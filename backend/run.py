"""
run.py — Belege → DATEV-Buchungsstapel.

Zusammenführung von drei Ständen:
  - Live (Sparkasse, Flatex-Einzelbelege, comdirect, v2-Dispatcher)
  - nie deploytes Paket (IBKR, EZB-Kurse, Flatex-Jahresmodus, v3/v4)
  - Kontenmatrix Fassung 3 (beide Kontenrahmen, vier Instrumentenklassen,
    Fondskategorien, gleitender Durchschnitt, zwei Stapel)

Öffentliche Schnittstelle bleibt kompatibel:
    main(pfad, output_dir, skr, bank, mandant)         → dict
    main_multi(pfade, output_dir, skr, bank, mandant)  → dict

Neu sind die Schlüsselwortargumente `vermoegensart`, `bewertung` und
`depot_overrides`, die aus den Mandantenstammdaten kommen.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from konten import Kontenmatrix, KontenKontext
from modelle import NormBeleg, Vorabpauschale, normalisiere, round2
from klassifizierung import Klassifikator, IsinTabelle
from bewertung import bewerte_belege, GLEITENDER_DURCHSCHNITT, FIFO
from booking_engine_v5 import belege_zu_buchungen_v5, BuchungsErgebnis
from datev_writer import buchungen_zu_csv, schreibe_review_csv
import einrichtungsblatt

BASIS = Path(__file__).parent
KONTEN_YAML = BASIS / "config" / "konten.yaml"
CONFIG_JSON = BASIS / "config.json"


# ───────────────────────────────────────────────────────────────────────────
# Erkennung
# ───────────────────────────────────────────────────────────────────────────
def detect_bank(file_path: str) -> str:
    p = file_path.lower()

    if p.endswith((".xlsx", ".xlsm", ".xls")):
        from parser_comdirect import is_comdirect_xlsx
        return "comdirect" if is_comdirect_xlsx(file_path) else "unknown"

    if p.endswith(".csv"):
        try:
            from parser_flatex_kontoumsaetze import ist_flatex_kontoumsaetze
            if ist_flatex_kontoumsaetze(file_path):
                return "flatex_kontoumsaetze"
        except ImportError:
            pass
        from parser_ibkr import is_ibkr_csv
        return "ibkr" if is_ibkr_csv(file_path) else "unknown"

    if p.endswith(".pdf"):
        try:
            from parser_flatex_ertraegnis import ist_ertraegnisaufstellung
            if ist_ertraegnisaufstellung(file_path):
                return "flatex_ertraegnis"
        except ImportError:
            pass
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            text = (pdf.pages[0].extract_text() or "") if pdf.pages else ""
        if "flatexDEGIRO" in text or "flatex.de" in text:
            return "flatex_einzelbeleg"
        if "Sparkasse" in text or "S-DirektInvest" in text or "Stadtsparkasse" in text:
            return "sparkasse"
        if "comdirect" in text.lower():
            return "comdirect_pdf"
    return "unknown"


def get_parser(bank: str):
    if bank == "sparkasse":
        import parser as p
        return p
    if bank == "flatex_einzelbeleg":
        raise ValueError(
            "Flatex-Einzelbelege werden nicht mehr verarbeitet. In den "
            "Einzelabrechnungen rechnet die Bank den Anschaffungswert aus dem "
            "bereits teilfreigestellten Gewinn zurück; bei Fonds weicht er "
            "dadurch um dreistellige Beträge ab. Bitte stattdessen die "
            "Erträgnisaufstellung (PDF) zusammen mit den Kontoumsätzen (CSV, "
            "je Unterdepot eine Datei) hochladen.")
    if bank == "comdirect":
        import parser_comdirect as p
        return p
    if bank == "ibkr":
        import parser_ibkr as p
        return p
    if bank == "comdirect_pdf":
        raise ValueError(
            "Der comdirect-Finanzreport als PDF wird nicht unterstützt. "
            "Bitte den XLSX-Export aus dem Webportal hochladen.")
    raise ValueError(f"Unbekannte oder nicht unterstützte Quelle: {bank}")


# ───────────────────────────────────────────────────────────────────────────
# Konfiguration
# ───────────────────────────────────────────────────────────────────────────
def lade_config(skr: str = "SKR04", vermoegensart: str = "UV",
                mandant_nr: str = "", bewertung: str = FIFO
                ) -> Tuple[dict, Kontenmatrix, KontenKontext]:
    roh = json.loads(CONFIG_JSON.read_text(encoding="utf-8"))
    matrix = Kontenmatrix.laden(KONTEN_YAML)

    vor = roh.get("mandant_vorgaben", {})
    ctx = KontenKontext(
        kontenrahmen=(skr or vor.get("kontenrahmen", "SKR04")).upper(),
        vermoegensart=(vermoegensart or vor.get("vermoegensart", "UV")).upper(),
        depot=1,
        sachkontenlaenge=int(roh["datev_header"].get("sachkontenlaenge", 4)),
    )

    if ctx.sachkontenlaenge != 4:
        raise ValueError(
            f"Sachkontenlänge {ctx.sachkontenlaenge} wird nicht unterstützt. "
            "Die Kontenmatrix ist auf vierstellige Sachkonten ausgelegt. Bei "
            "längeren Sachkonten sind alle Nummern in config/konten.yaml "
            "entsprechend zu erweitern.")

    header = dict(roh["datev_header"])
    header["mandant_nr"] = mandant_nr or header.get("mandant_nr", "")
    header["sachkontenrahmen"] = "03" if ctx.kontenrahmen == "SKR03" else "04"

    config = {
        "datev_header": header,
        "buchungstexte": roh["buchungstexte"],
        "options": roh.get("options", {}),
        "bewertung": bewertung or vor.get("bewertung", FIFO),
    }
    return config, matrix, ctx


# ───────────────────────────────────────────────────────────────────────────
# Verarbeitung
# ───────────────────────────────────────────────────────────────────────────
def verarbeite(rohbelege: List, matrix: Kontenmatrix, ctx: KontenKontext,
               config: dict, isin_tabelle: IsinTabelle,
               depot_index_je_beleg=None,
               vorabpauschalen: Optional[List[Vorabpauschale]] = None
               ) -> Tuple[BuchungsErgebnis, List[NormBeleg], object, Klassifikator]:
    """Die vier Stufen: normalisieren, klassifizieren, bewerten, buchen."""
    normalisiert: List[NormBeleg] = []
    for b in rohbelege:
        idx = depot_index_je_beleg(b) if depot_index_je_beleg else 1
        normalisiert.append(normalisiere(b, depot_index=idx))

    klassifikator = Klassifikator(matrix, isin_tabelle)
    klassifikator.klassifiziere_alle(normalisiert)

    bewerter = bewerte_belege(normalisiert, config["bewertung"])

    # #AK-PRÜFEN# nach der Bewertung nachziehen
    marker_ak = matrix.marker("ak_pruefen")
    marker_lot = matrix.marker("lot_pruefen")
    for nb in normalisiert:
        if nb.buchwert_unvollstaendig and marker_ak not in nb.marker:
            nb.marker.append(marker_ak)
        # Beim Durchschnittsverfahren ist die Tranchenzuordnung ohne Belang.
        if config["bewertung"] == GLEITENDER_DURCHSCHNITT and marker_lot in nb.marker:
            nb.marker.remove(marker_lot)

    erg = belege_zu_buchungen_v5(
        normalisiert, matrix, ctx, config["buchungstexte"],
        config.get("options"), vorabpauschalen)
    return erg, normalisiert, bewerter, klassifikator


# ───────────────────────────────────────────────────────────────────────────
# Ausgabe
# ───────────────────────────────────────────────────────────────────────────
def build_filenames(out: Path, mandant: str, tag: date) -> Dict[str, Path]:
    d = tag.strftime("%Y%m%d")
    pre = f"{mandant.strip()}_" if mandant.strip() else ""
    return {
        "stapel": out / f"{pre}Buchungsstapel_{d}.csv",
        "stapel_steuer": out / f"{pre}Buchungsstapel_Steuerrecht_{d}.csv",
        "plausi": out / f"{pre}Plausi_{d}.csv",
        "protokoll": out / f"{pre}Protokoll_{d}.txt",
        "einrichtung": out / f"{pre}Kontenblatt_Kanzlei_{d}.pdf",
        "vorabpauschale": out / f"{pre}Vorabpauschalen_{d}.csv",
        "isin": out / f"{pre}ISIN-Zuordnung_{d}.csv",
    }


def schreibe_vorabpauschalen(pfad: Path, vp: List[Vorabpauschale],
                             ibkr_im_lauf: bool) -> None:
    import csv
    with open(pfad, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["ISIN", "Bezeichnung", "Jahr", "Fondskategorie",
                    "Vorabpauschale EUR", "Einbehaltene Steuer EUR", "Depot"])
        for v in sorted(vp, key=lambda x: (x.isin, x.jahr)):
            w.writerow([v.isin, v.bezeichnung, v.jahr, v.kategorie or "",
                        str(round2(v.betrag)).replace(".", ","),
                        str(round2(v.steuer)).replace(".", ","), v.depot or ""])
        w.writerow([])
        w.writerow(["Hinweis", "Der Ausgleichsposten ist über die Jahre "
                    "fortzuschreiben. Beim Verkauf ist er aufzulösen."])
        if ibkr_im_lauf:
            w.writerow(["Achtung", "Für Depots bei Interactive Brokers weist "
                        "das Tool keine Vorabpauschale aus. IBKR Ireland ist "
                        "keine deutsche Abzugsstelle; die Vorabpauschale ist "
                        "selbst zu ermitteln."])


def schreibe_isin_liste(pfad: Path, klassifikator: Klassifikator) -> None:
    import csv
    with open(pfad, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["ISIN", "Bezeichnung", "Klasse", "Fondskategorie",
                    "Quelle", "Nachpflegen"])
        offen = {e.isin for e in klassifikator.tabelle.offene()}
        for isin, e in sorted(klassifikator.tabelle._d.items()):
            w.writerow([isin, e.bezeichnung, e.klasse or "", e.fondskategorie or "",
                        e.quelle, "JA" if isin in offen else ""])


# ───────────────────────────────────────────────────────────────────────────
# Einstiegspunkte
# ───────────────────────────────────────────────────────────────────────────
def main(pfad: str, output_dir: str = "./out", skr: str = "SKR04",
         bank: Optional[str] = "1801", mandant: str = "",
         vermoegensart: str = "UV", bewertung: str = FIFO,
         isin_tabelle_pfad: Optional[str] = None) -> dict:
    return main_multi([pfad], output_dir, skr, bank, mandant,
                      vermoegensart=vermoegensart, bewertung=bewertung,
                      isin_tabelle_pfad=isin_tabelle_pfad)


def main_multi(file_paths: List[str], output_dir: str = "./out",
               skr: str = "SKR04", bank: Optional[str] = "1801",
               mandant: str = "", vermoegensart: str = "UV",
               bewertung: str = FIFO,
               depot_overrides: Optional[Dict[str, int]] = None,
               isin_tabelle_pfad: Optional[str] = None) -> dict:
    """Verarbeitet eine oder mehrere Dateien.

    Mehrere Dateien bedeuten entweder den Flatex-Jahresmodus
    (1 Erträgnisaufstellung + n Kontoumsätze) oder mehrere Einzelbelege
    desselben Mandanten.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    config, matrix, ctx = lade_config(skr, vermoegensart, mandant, bewertung)

    isin_pfad = Path(isin_tabelle_pfad) if isin_tabelle_pfad else \
        out / f"isin_{mandant or 'default'}.json"
    isin_tabelle = IsinTabelle.laden(isin_pfad)

    # Das Verrechnungskonto des Depots ist ein eigenes Bankkonto neben dem
    # laufenden Geschäftskonto. Es kommt deshalb aus der Oberfläche und nicht
    # aus der Matrix; deren Wert dient nur als Vorschlag.
    verrechnungskonto = str(bank) if bank else matrix.bank(ctx)
    matrix.setze_bank_override(1, verrechnungskonto)
    vorgabe = matrix._rahmen(ctx)["bank"]["konten"][0]
    protokoll_hinweis_bank = (
        f"Verrechnungskonto {verrechnungskonto} "
        + ("(Standardkonto des Kontenrahmens)"
           if str(vorgabe) == verrechnungskonto
           else f"— abweichend vom Standardkonto {vorgabe}."))

    quellen = {p: detect_bank(p) for p in file_paths}
    unbekannt = [p for p, b in quellen.items() if b == "unknown"]
    if unbekannt:
        raise ValueError(
            "Quelle nicht erkannt: " + ", ".join(Path(p).name for p in unbekannt) +
            ". Unterstützt: Sparkasse (PDF), flatexDEGIRO (PDF, "
            "Erträgnisaufstellung, Kontoumsätze CSV), comdirect (XLSX), "
            "Interactive Brokers (CSV).")

    rohbelege: List = []
    ignoriert: List = []
    vorabpauschalen: List[Vorabpauschale] = []
    depot_map: Dict[str, int] = {}
    protokoll_extra: List[str] = [protokoll_hinweis_bank] if protokoll_hinweis_bank else []
    ibkr_im_lauf = any(b == "ibkr" for b in quellen.values())

    jahresmodus = ("flatex_ertraegnis" in quellen.values()
                   or "flatex_kontoumsaetze" in quellen.values())

    if jahresmodus:
        from flatex_jahr import verarbeite_jahresmodus
        pdfs = [p for p, b in quellen.items() if b == "flatex_ertraegnis"]
        csvs = [p for p, b in quellen.items() if b == "flatex_kontoumsaetze"]
        erg_jahr = verarbeite_jahresmodus(pdfs[0] if pdfs else None, csvs)
        rohbelege.extend(erg_jahr.belege)
        ignoriert.extend(erg_jahr.ignoriert)
        protokoll_extra.append(erg_jahr.protokoll())
        # Depotnamen auf 1-basierte Indizes abbilden; die Kontenvergabe
        # übernimmt die Matrix, nicht mehr die DepotRegistry.
        namen = sorted({b.depot for b in erg_jahr.belege if getattr(b, "depot", None)})
        depot_map = {n: i + 1 for i, n in enumerate(namen)}
        if depot_overrides:
            depot_map.update(depot_overrides)
        for v in getattr(erg_jahr, "vorabpauschalen", []):
            vorabpauschalen.append(Vorabpauschale(
                isin=getattr(v, "isin", ""), bezeichnung=getattr(v, "bezeichnung", ""),
                jahr=getattr(v, "jahr", None) or date.today().year,
                betrag=Decimal(str(getattr(v, "betrag", 0))),
                steuer=Decimal(str(getattr(v, "steuer", 0))),
                datum=getattr(v, "datum", None), depot=getattr(v, "depot", None)))
    else:
        for pfad, bankname in quellen.items():
            modul = get_parser(bankname)
            leser = getattr(modul, "parse_pdf", None) or getattr(modul, "parse_csv")
            belege, ign = leser(pfad)
            rohbelege.extend(belege)
            ignoriert.extend(ign)

    if not rohbelege:
        raise ValueError("Keine buchbaren Belege gefunden.")

    def depot_index(b) -> int:
        return depot_map.get(getattr(b, "depot", None), 1)

    erg, normalisiert, bewerter, klassifikator = verarbeite(
        rohbelege, matrix, ctx, config, isin_tabelle,
        depot_index_je_beleg=depot_index if depot_map else None,
        vorabpauschalen=vorabpauschalen)

    datum_von = min(nb.schlusstag for nb in normalisiert)
    datum_bis = max(nb.schlusstag for nb in normalisiert)

    tag = datetime.now().date()
    f = build_filenames(out, mandant, tag)

    # Das Belegdatum trägt in DATEV nur Tag und Monat; das Jahr kommt aus dem
    # Kopfsatz. Ein Stapel über den Jahreswechsel wäre deshalb für einen Teil
    # der Buchungen falsch datiert. Wir schreiben stattdessen je
    # Wirtschaftsjahr eine eigene Datei.
    stapel_dateien = _schreibe_stapel(f["stapel"], erg.hauptstapel, config)

    steuer_dateien: List[str] = []
    if erg.steuerstapel:
        zweck = config["datev_header"].get("rechnungslegungszweck_steuerrecht")
        if zweck is None:
            protokoll_extra.append(
                "Der Steuerstapel wurde NICHT geschrieben: in config.json ist "
                "'rechnungslegungszweck_steuerrecht' nicht gesetzt.")
        else:
            cfg_steuer = dict(config)
            cfg_steuer["datev_header"] = dict(config["datev_header"])
            cfg_steuer["datev_header"]["rechnungslegungszweck"] = zweck
            cfg_steuer["datev_header"]["stapel_bezeichnung_template"] = \
                "WP-Steuerrecht {datum_von}-{datum_bis}"
            steuer_dateien = _schreibe_stapel(f["stapel_steuer"],
                                              erg.steuerstapel, cfg_steuer)
    steuer_geschrieben = bool(steuer_dateien)
    if len(stapel_dateien) > 1:
        protokoll_extra.append(
            f"Der Zeitraum umfasst {len(stapel_dateien)} Wirtschaftsjahre. Es "
            f"wurde je Jahr ein eigener Stapel geschrieben, weil DATEV das "
            f"Jahr aus dem Kopfsatz ableitet und das Belegdatum nur Tag und "
            f"Monat trägt.")

    schreibe_review_csv(rohbelege, ignoriert, str(f["plausi"]))
    klassen = sorted({nb.klasse for nb in normalisiert if nb.klasse})
    n_depots = max(1, len({nb.depot_index for nb in normalisiert}))
    n_konten = einrichtungsblatt.schreibe_pdf(
        f["einrichtung"], matrix, ctx, klassen, mandant, verrechnungskonto,
        n_depots)
    if vorabpauschalen or ibkr_im_lauf:
        schreibe_vorabpauschalen(f["vorabpauschale"], vorabpauschalen, ibkr_im_lauf)
    schreibe_isin_liste(f["isin"], klassifikator)
    klassifikator.tabelle.speichern(isin_pfad)

    _schreibe_protokoll(f["protokoll"], file_paths, quellen, config, ctx,
                        erg, normalisiert, ignoriert, bewerter, klassifikator,
                        datum_von, datum_bis, protokoll_extra, n_konten,
                        steuer_geschrieben)

    return {
        "stapel": stapel_dateien[0] if stapel_dateien else None,
        "stapel_dateien": stapel_dateien,
        "stapel_steuer": steuer_dateien[0] if steuer_dateien else None,
        "stapel_steuer_dateien": steuer_dateien,
        "plausi": str(f["plausi"]),
        "protokoll": str(f["protokoll"]),
        "kontenblatt_kanzlei": str(f["einrichtung"]),
        "verrechnungskonto": verrechnungskonto,
        "isin_liste": str(f["isin"]),
        "quellen": {Path(k).name: v for k, v in quellen.items()},
        "kontenrahmen": ctx.kontenrahmen,
        "vermoegensart": ctx.vermoegensart,
        "bewertung": config["bewertung"],
        "n_belege": len(normalisiert),
        "n_buchungen": len(erg.hauptstapel),
        "n_buchungen_steuer": len(erg.steuerstapel),
        "n_ignoriert": len(ignoriert),
        "n_ungebucht": len(erg.ungebucht),
        "n_konten_anzulegen": n_konten,
        "datum_von": str(datum_von),
        "datum_bis": str(datum_bis),
    }


def _schreibe_stapel(basis: Path, buchungen, config: dict) -> List[str]:
    """Schreibt je Wirtschaftsjahr eine DTVF-Datei. Bei nur einem Jahr bleibt
    der Dateiname unverändert, damit bestehende Aufrufer nichts merken."""
    if not buchungen:
        return []
    jahre = sorted({b.belegdatum.year for b in buchungen})
    geschrieben: List[str] = []
    for jahr in jahre:
        teil = [b for b in buchungen if b.belegdatum.year == jahr]
        von = min(b.belegdatum for b in teil)
        bis = max(b.belegdatum for b in teil)
        cfg = dict(config)
        cfg["datev_header"] = dict(config["datev_header"])
        cfg["datev_header"]["wj_beginn"] = date(jahr, 1, 1).strftime("%Y%m%d")
        pfad = basis if len(jahre) == 1 else \
            basis.with_name(f"{basis.stem}_{jahr}{basis.suffix}")
        pfad.write_bytes(buchungen_zu_csv(teil, cfg, von, bis))
        geschrieben.append(str(pfad))
    return geschrieben


def _schreibe_protokoll(pfad, file_paths, quellen, config, ctx, erg,
                        normalisiert, ignoriert, bewerter, klassifikator,
                        datum_von, datum_bis, extra, n_konten,
                        steuer_geschrieben) -> None:
    from collections import Counter
    with open(pfad, "w", encoding="utf-8") as f:
        f.write("Wertstapel — Verarbeitungsprotokoll\n" + "=" * 66 + "\n\n")
        for p, b in quellen.items():
            f.write(f"Quelle:        {Path(p).name}  ({b})\n")
        f.write(f"Erzeugt am:    {datetime.now().isoformat(timespec='seconds')}\n")
        f.write(f"Kontenrahmen:  {ctx.kontenrahmen}\n")
        f.write(f"Vermögensart:  {'Umlaufvermögen' if ctx.vermoegensart == 'UV' else 'Anlagevermögen'}\n")
        f.write(f"Bewertung:     {config['bewertung']}\n")
        f.write(f"Mandant-Nr.:   {config['datev_header'].get('mandant_nr') or '—'}\n")
        f.write(f"Zeitraum:      {datum_von} bis {datum_bis}\n\n")

        f.write(f"Belege verarbeitet:   {len(normalisiert)}\n")
        f.write(f"Buchungen Hauptstapel:{len(erg.hauptstapel):>5}\n")
        f.write(f"Buchungen Steuerstapel:{len(erg.steuerstapel):>4}"
                f"{'' if steuer_geschrieben else '  (nicht geschrieben)'}\n")
        f.write(f"Seiten ignoriert:     {len(ignoriert)}\n")
        f.write(f"Konten anzulegen:     {n_konten}  (siehe Einrichtungsblatt)\n\n")

        klassen = Counter(nb.klasse or "—" for nb in normalisiert)
        f.write("Instrumentenklassen:\n")
        for k, n in sorted(klassen.items()):
            f.write(f"  {k:24} {n:4}\n")

        kats = Counter(nb.fondskategorie for nb in normalisiert if nb.fondskategorie)
        if kats:
            f.write("\nFondskategorien:\n")
            for k, n in sorted(kats.items()):
                f.write(f"  {k:24} {n:4}\n")

        offen = klassifikator.tabelle.offene()
        if offen:
            f.write(f"\nNACHPFLEGEN — {len(offen)} ISIN ohne eindeutige Zuordnung:\n")
            for e in offen:
                f.write(f"  {e.isin}  {e.bezeichnung[:40]:40} "
                        f"Klasse={e.klasse or '?'}  Kategorie={e.fondskategorie or '?'}\n")
            f.write("  Nach der Klärung im Frontend hinterlegen; ab dem "
                    "Folgejahr wird dann richtig gebucht.\n")

        markiert = [nb for nb in normalisiert if nb.marker]
        if markiert:
            f.write(f"\nMarkierte Belege: {len(markiert)}\n")
            zaehler = Counter(m for nb in markiert for m in nb.marker)
            for m, n in sorted(zaehler.items(), key=lambda x: -x[1]):
                f.write(f"  {m:16} {n:4}\n")

        if erg.ungebucht:
            f.write(f"\nNICHT GEBUCHT — {len(erg.ungebucht)} Vorgang/Vorgänge:\n")
            for u in erg.ungebucht:
                f.write(f"  [{u.typ}] {u.isin or '—'} {u.bezeichnung[:34]:34} "
                        f"{u.betrag} EUR\n      Grund: {u.grund}\n")
                if u.empfehlung:
                    f.write(f"      → {u.empfehlung}\n")

        warn = [nb for nb in normalisiert if nb.warnings]
        if warn:
            f.write(f"\nHinweise zu {len(warn)} Beleg(en):\n")
            for nb in warn:
                for w in nb.warnings:
                    f.write(f"  {nb.auftragsnummer}: {w}\n")

        f.write("\n" + bewerter.protokoll() + "\n")
        for h in erg.hinweise:
            f.write(f"\nHINWEIS: {h}\n")
        for e in extra:
            f.write("\n" + e + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Wertstapel — DATEV-Buchungsstapel erzeugen")
    ap.add_argument("dateien", nargs="+")
    ap.add_argument("--out", default="./out")
    ap.add_argument("--skr", default="SKR04", choices=["SKR03", "SKR04"])
    ap.add_argument("--vermoegensart", default="UV", choices=["UV", "AV"])
    ap.add_argument("--bewertung", default=FIFO,
                    choices=[FIFO, GLEITENDER_DURCHSCHNITT])
    ap.add_argument("--mandant", default="")
    args = ap.parse_args()
    print(json.dumps(main_multi(args.dateien, args.out, args.skr, None,
                                args.mandant, args.vermoegensart, args.bewertung),
                     indent=2, ensure_ascii=False))

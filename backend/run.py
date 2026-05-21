"""
run.py — PDF → DATEV-Buchungsstapel

Erkennt automatisch die Bank (Sparkasse oder Flatex) anhand des PDF-Inhalts
und nutzt den passenden Parser.
"""
import argparse, json, sys
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path

import pdfplumber

from booking_engine import belege_zu_buchungen, belege_zu_buchungen_alle_typen
from datev_writer import buchungen_zu_csv, schreibe_review_csv, _fmt_decimal


def detect_bank(pdf_path: str) -> str:
    """Erkennt die Bank anhand der ersten PDF-Seite."""
    with pdfplumber.open(pdf_path) as pdf:
        text = (pdf.pages[0].extract_text() or "") if pdf.pages else ""
    if "flatexDEGIRO" in text or "flatex.de" in text:
        return "flatex"
    if "Sparkasse" in text or "S-DirektInvest" in text or "Stadtsparkasse" in text:
        return "sparkasse"
    return "unknown"


def get_parser(bank: str):
    """Liefert das passende Parser-Modul."""
    if bank == "sparkasse":
        import parser as p
        return p
    if bank == "flatex":
        import parser_flatex as p
        # Booking-Engine erwartet Beleg/Tranche aus dem 'parser' Modul
        import parser as sparkasse_p
        sparkasse_p.Beleg = p.Beleg
        sparkasse_p.Tranche = p.Tranche
        return p
    raise ValueError(f"Unbekannte Bank: {bank}")


def resolve_config(skr="SKR04", bank=None, mandant_nr=""):
    config_path = Path(__file__).parent / "config.json"
    with open(config_path, encoding="utf-8") as f:
        raw = json.load(f)

    preset_key = skr.upper() if skr.upper() in raw.get("presets", {}) else "SKR04"
    preset = raw["presets"][preset_key].copy()
    if bank:
        preset["bank"] = {"nr": bank, "name": f"Bank ({bank})"}

    return {
        "konten": preset,
        "buchungstexte": raw["buchungstexte"],
        "options": raw["options"],
        "datev_header": {
            "berater_nr": raw["datev_header"].get("berater_nr", ""),
            "mandant_nr": mandant_nr or raw["datev_header"].get("mandant_nr", ""),
            "sachkontenlaenge": 4,
            "sachkontenrahmen": preset["sachkontenrahmen"],
            "diktatkuerzel": raw["datev_header"].get("diktatkuerzel", "XX"),
            "buchungstyp": 1, "rechnungslegungszweck": 0,
            "festschreibung": 0, "waehrung": "EUR",
            "exportiert_von": "wertstapel",
            "stapel_bezeichnung_template": "WP-Stapel {datum_von}-{datum_bis}",
            "wj_beginn": "",
        },
    }


def build_filenames(out, mandant, export_date):
    d = export_date.strftime("%Y%m%d")
    pre = f"{mandant.strip()}_" if mandant.strip() else ""
    return {
        "stapel":    out / f"{pre}Buchungsstapel_{d}.csv",
        "plausi":    out / f"{pre}Plausi_{d}.csv",
        "protokoll": out / f"{pre}Protokoll_{d}.txt",
    }


def main(pdf_path, output_dir="./out", skr="SKR04", bank="1801", mandant=""):
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)

    detected_bank = detect_bank(pdf_path)
    if detected_bank == "unknown":
        raise ValueError("Bank konnte nicht erkannt werden. "
                         "Unterstützt: Sparkasse, flatexDEGIRO.")
    parser_module = get_parser(detected_bank)

    config = resolve_config(skr=skr, bank=bank, mandant_nr=mandant)
    belege, ignored = parser_module.parse_pdf(pdf_path)

    # Alle Belegtypen werden gebucht — DIVIDENDE/FONDSERTRAG mit Marker (#DIV#, #FONDS#)
    unsupported = []  # Nichts mehr manuell ausgeschlossen

    all_belege = belege + unsupported
    if all_belege:
        datum_von = min(b.schlusstag for b in all_belege)
        datum_bis = max(b.schlusstag for b in all_belege)
    else:
        datum_von = datum_bis = datetime.now().date()
    config["datev_header"]["wj_beginn"] = date(datum_von.year, 1, 1).strftime("%Y%m%d")

    buchungen = belege_zu_buchungen_alle_typen(belege, config)

    export_date = datetime.now().date()
    fnames = build_filenames(out, mandant, export_date)

    csv_bytes = buchungen_zu_csv(buchungen, config, datum_von, datum_bis)
    fnames["stapel"].write_bytes(csv_bytes)
    schreibe_review_csv(belege, ignored, str(fnames["plausi"]))

    fails = [b for b in belege if not b.plausi_ok]
    with open(fnames["protokoll"], "w", encoding="utf-8") as f:
        f.write("Wertstapel — Verarbeitungsprotokoll\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Quelldatei:    {pdf_path}\n")
        f.write(f"Erkannte Bank: {detected_bank}\n")
        f.write(f"Erzeugt am:    {datetime.now().isoformat(timespec='seconds')}\n")
        f.write(f"Kontenrahmen:  {skr}\nBankkonto:     {bank}\n")
        f.write(f"Mandant-Nr.:   {mandant or '—'}\n")
        f.write(f"Datumsbereich: {datum_von} bis {datum_bis}\n\n")
        f.write(f"Belege gebucht:    {len(belege)}\n")
        f.write(f"Buchungen erzeugt: {len(buchungen)}\n")
        f.write(f"Seiten ignoriert:  {len(ignored)}\n")

        if unsupported:
            f.write(f"\n⚠️  NICHT GEBUCHT — Belegtypen noch nicht unterstützt:\n")
            for b in unsupported:
                f.write(f"  {b.typ}: {b.wertpapierbezeichnung} ({b.isin}), "
                        f"Endbetrag {b.ausmachender_betrag} EUR\n")
                if b.typ == "DIVIDENDE" and b.quellensteuer_eur:
                    f.write(f"     → Quellensteuer EUR: {b.quellensteuer_eur:.2f}\n")
                if b.typ == "FONDSERTRAG" and b.teilfrei_satz:
                    f.write(f"     → Teilfreist.-Satz: {b.teilfrei_satz}% "
                            f"(GmbH-Korrektur ggf. erforderlich)\n")
            f.write("\n     Diese Belege müssen manuell vom Steuerberater gebucht werden.\n")

        if fails:
            f.write(f"\n⚠️  PLAUSI-PROBLEME bei {len(fails)} Beleg(en):\n")
            for b in fails:
                f.write(f"  {b.auftragsnummer}: {' | '.join(b.warnings)}\n")
        else:
            f.write(f"\n✓ Alle Plausibilitätsprüfungen bestanden.\n")

    return {
        "stapel": str(fnames["stapel"]), "plausi": str(fnames["plausi"]),
        "protokoll": str(fnames["protokoll"]), "bank": detected_bank,
        "n_belege": len(belege), "n_buchungen": len(buchungen),
        "n_ignored": len(ignored), "n_unsupported": len(unsupported),
        "plausi_ok": len(fails) == 0 if belege else True,
        "datum_von": str(datum_von), "datum_bis": str(datum_bis),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("output_dir", nargs="?", default="./out")
    ap.add_argument("--skr", default="SKR04")
    ap.add_argument("--bank", default="1801")
    ap.add_argument("--mandant", default="")
    args = ap.parse_args()
    print(json.dumps(main(args.pdf, args.output_dir, args.skr, args.bank, args.mandant),
                     indent=2, ensure_ascii=False))

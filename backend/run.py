"""
run.py — PDF → DATEV-Buchungsstapel

Aufruf (standalone):
    python run.py <pdf_pfad> [output_dir]
        [--skr SKR04]
        [--bank 1801]
        [--mandant 31385]

Aufruf (aus FastAPI):
    result = main(pdf_path, output_dir, skr="SKR04", bank="1801", mandant="31385")

Erzeugte Dateien (Beispiel mit Mandant 31385, Datum 20260429):
  31385_Buchungsstapel_20260429.csv
  31385_Plausi_20260429.csv
  31385_Protokoll_20260429.txt
"""
import argparse
import json
import sys
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path

from parser import parse_pdf
from booking_engine import belege_zu_buchungen
from datev_writer import buchungen_zu_csv, schreibe_review_csv, _fmt_decimal


# ── Config-Preset auflösen ────────────────────────────────────────────────────
def resolve_config(skr: str = "SKR04", bank: str | None = None,
                   mandant_nr: str = "") -> dict:
    """Lädt config.json und löst das gewählte Preset auf."""
    config_path = Path(__file__).parent / "config.json"
    with open(config_path, encoding="utf-8") as f:
        raw = json.load(f)

    # Preset wählen (SKR04 ist default)
    preset_key = skr.upper() if skr.upper() in raw.get("presets", {}) else "SKR04"
    preset = raw["presets"][preset_key].copy()

    # Bankkonto überschreiben wenn angegeben
    if bank:
        preset["bank"] = {"nr": bank, "name": f"Bank ({bank})"}

    return {
        "konten":       preset,
        "buchungstexte": raw["buchungstexte"],
        "options":       raw["options"],
        "datev_header": {
            "berater_nr":           raw["datev_header"].get("berater_nr", ""),
            "mandant_nr":           mandant_nr or raw["datev_header"].get("mandant_nr", ""),
            "sachkontenlaenge":     4,
            "sachkontenrahmen":     preset["sachkontenrahmen"],
            "diktatkuerzel":        raw["datev_header"].get("diktatkuerzel", "XX"),
            "buchungstyp":          1,
            "rechnungslegungszweck":0,
            "festschreibung":       0,
            "waehrung":             "EUR",
            "exportiert_von":       "wertstapel",
            "stapel_bezeichnung_template": "WP-Stapel {datum_von}-{datum_bis}",
            # WJ-Beginn wird unten aus den Belegen abgeleitet
            "wj_beginn":            "",
        },
    }


# ── Dateinamen mit optionalem Mandant-Prefix ──────────────────────────────────
def build_filenames(out: Path, mandant: str, export_date: date) -> dict:
    d = export_date.strftime("%Y%m%d")
    pre = f"{mandant.strip()}_" if mandant.strip() else ""
    return {
        "stapel":    out / f"{pre}Buchungsstapel_{d}.csv",
        "plausi":    out / f"{pre}Plausi_{d}.csv",
        "protokoll": out / f"{pre}Protokoll_{d}.txt",
    }


# ── Hauptfunktion ─────────────────────────────────────────────────────────────
def main(
    pdf_path: str,
    output_dir: str = "./out",
    skr: str = "SKR04",
    bank: str = "1801",
    mandant: str = "",
) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Config
    config = resolve_config(skr=skr, bank=bank, mandant_nr=mandant)

    # PDF parsen
    belege, ignored = parse_pdf(pdf_path)

    # WJ-Beginn automatisch aus frühestem Belegdatum ableiten
    if belege:
        datum_von = min(b.schlusstag for b in belege)
        datum_bis = max(b.schlusstag for b in belege)
        wj_beginn = date(datum_von.year, 1, 1).strftime("%Y%m%d")
    else:
        datum_von = datum_bis = datetime.now().date()
        wj_beginn = date(datum_von.year, 1, 1).strftime("%Y%m%d")

    config["datev_header"]["wj_beginn"] = wj_beginn

    # Buchungen erzeugen
    buchungen = belege_zu_buchungen(belege, config)

    # Dateinamen
    export_date = datetime.now().date()
    fnames = build_filenames(out, mandant, export_date)

    # DATEV-CSV schreiben
    csv_bytes = buchungen_zu_csv(buchungen, config, datum_von, datum_bis)
    fnames["stapel"].write_bytes(csv_bytes)

    # Plausi-CSV schreiben
    schreibe_review_csv(belege, ignored, str(fnames["plausi"]))

    # Log schreiben
    with open(fnames["protokoll"], "w", encoding="utf-8") as f:
        f.write("Wertstapel — Verarbeitungsprotokoll\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Quelldatei:    {pdf_path}\n")
        f.write(f"Erzeugt am:    {datetime.now().isoformat(timespec='seconds')}\n")
        f.write(f"Kontenrahmen:  {skr}\n")
        f.write(f"Bankkonto:     {bank}\n")
        f.write(f"Mandant-Nr.:   {mandant or '—'}\n")
        f.write(f"WJ-Beginn:     {wj_beginn[:4]}-01-01 (automatisch aus Belegen)\n")
        f.write(f"Datumsbereich: {datum_von} bis {datum_bis}\n\n")

        f.write(f"Belege erkannt:    {len(belege)}\n")
        f.write(f"Buchungen erzeugt: {len(buchungen)}\n")
        f.write(f"Seiten ignoriert:  {len(ignored)}\n\n")

        n_kauf = sum(1 for b in belege if b.typ == "KAUF")
        n_vk   = sum(1 for b in belege if b.typ == "VERKAUF")
        f.write(f"Davon Käufe:    {n_kauf}\n")
        f.write(f"Davon Verkäufe: {n_vk}\n\n")

        # Summen
        ZERO = Decimal("0")
        sum_kv  = sum((b.kurswert for b in belege if b.typ == "KAUF"),    ZERO)
        sum_vv  = sum((b.kurswert for b in belege if b.typ == "VERKAUF"), ZERO)
        sum_geb = sum((b.gebuehren_summe for b in belege), ZERO)
        sum_g   = sum(
            (sum(t.erloes_ant - t.ak for t in b.tranchen if t.ist_gewinn)
             if b.tranchen else ZERO for b in belege), ZERO)
        sum_v   = sum(
            (sum(t.ak - t.erloes_ant for t in b.tranchen if not t.ist_gewinn)
             if b.tranchen else ZERO for b in belege), ZERO)

        f.write("Summen (EUR):\n")
        f.write(f"  Kurswerte Kauf:       {_fmt_decimal(sum_kv)}\n")
        f.write(f"  Kurswerte Verkauf:    {_fmt_decimal(sum_vv)}\n")
        f.write(f"  Gebühren gesamt:      {_fmt_decimal(sum_geb)}\n")
        f.write(f"  Veräußerungsgewinne:  {_fmt_decimal(sum_g)}\n")
        f.write(f"  Veräußerungsverluste: {_fmt_decimal(sum_v)}\n")
        f.write(f"  Netto-Steuerergebnis: {_fmt_decimal(sum_g - sum_v)}\n\n")

        # Plausi
        fails = [b for b in belege if not b.plausi_ok]
        if fails:
            f.write(f"⚠️  PLAUSI-PROBLEME bei {len(fails)} Beleg(en):\n")
            for b in fails:
                f.write(f"  Seite {b.seite}: {' | '.join(b.warnings)}\n")
        else:
            f.write("✅ Alle Plausibilitätsprüfungen bestanden.\n")

        f.write(f"\nIgnorierte Seiten ({len(ignored)}):\n")
        for ig in ignored:
            f.write(f"  Seite {ig.seite:3d} [{ig.typ}]: {ig.grund}\n")

    return {
        "stapel":      str(fnames["stapel"]),
        "plausi":      str(fnames["plausi"]),
        "protokoll":   str(fnames["protokoll"]),
        "n_belege":    len(belege),
        "n_buchungen": len(buchungen),
        "n_ignored":   len(ignored),
        "plausi_ok":   len(fails) == 0 if belege else True,
        "datum_von":   str(datum_von),
        "datum_bis":   str(datum_bis),
    }


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="PDF → DATEV-Buchungsstapel")
    ap.add_argument("pdf",        help="Pfad zur PDF-Datei")
    ap.add_argument("output_dir", nargs="?", default="./out",
                    help="Ausgabeverzeichnis (default: ./out)")
    ap.add_argument("--skr",     default="SKR04", help="SKR03 oder SKR04")
    ap.add_argument("--bank",    default="1801",  help="Bankkonto-Nummer")
    ap.add_argument("--mandant", default="",      help="Mandantennummer (optional)")

    args = ap.parse_args()
    result = main(args.pdf, args.output_dir,
                  skr=args.skr, bank=args.bank, mandant=args.mandant)
    print(json.dumps(result, indent=2, ensure_ascii=False))

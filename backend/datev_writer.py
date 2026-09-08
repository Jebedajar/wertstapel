"""
datev_writer.py — Schreibt eine DTVF-Buchungsstapel-CSV gemäß DATEV-Format-Definition v7.00.

Encoding: Windows-1252 (cp1252)
Zeilentrenner: CRLF
Spaltentrenner: ;
Dezimaltrenner: , (Komma)
Textfelder: ohne Anführungszeichen, außer wenn Sonderzeichen enthalten

Das Format hat 126 Spalten in der Datenzeile (Stand: Format-Version 13).
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List
import csv
import io

from modelle import Buchung


# Reihenfolge der 126 Datenspalten gemäß DATEV-DTVF v7.00 / Format-Version 13
DATEV_COLUMNS = [
    "Umsatz (ohne Soll/Haben-Kz)", "Soll/Haben-Kennzeichen", "WKZ Umsatz", "Kurs",
    "Basis-Umsatz", "WKZ Basis-Umsatz", "Konto", "Gegenkonto (ohne BU-Schlüssel)",
    "BU-Schlüssel", "Belegdatum", "Belegfeld 1", "Belegfeld 2", "Skonto",
    "Buchungstext", "Postensperre", "Diverse Adressnummer", "Geschäftspartnerbank",
    "Sachverhalt", "Zinssperre", "Beleglink",
    "Beleginfo - Art 1", "Beleginfo - Inhalt 1",
    "Beleginfo - Art 2", "Beleginfo - Inhalt 2",
    "Beleginfo - Art 3", "Beleginfo - Inhalt 3",
    "Beleginfo - Art 4", "Beleginfo - Inhalt 4",
    "Beleginfo - Art 5", "Beleginfo - Inhalt 5",
    "Beleginfo - Art 6", "Beleginfo - Inhalt 6",
    "Beleginfo - Art 7", "Beleginfo - Inhalt 7",
    "Beleginfo - Art 8", "Beleginfo - Inhalt 8",
    "KOST1 - Kostenstelle", "KOST2 - Kostenstelle", "Kost-Menge",
    "EU-Land u. UStID (Bestimmung)", "EU-Steuersatz (Bestimmung)",
    "Abw. Versteuerungsart", "Sachverhalt L+L", "Funktionsergänzung L+L",
    "BU 49 Hauptfunktionstyp", "BU 49 Hauptfunktionsnummer", "BU 49 Funktionsergänzung",
    "Zusatzinformation - Art 1", "Zusatzinformation- Inhalt 1",
    "Zusatzinformation - Art 2", "Zusatzinformation- Inhalt 2",
    "Zusatzinformation - Art 3", "Zusatzinformation- Inhalt 3",
    "Zusatzinformation - Art 4", "Zusatzinformation- Inhalt 4",
    "Zusatzinformation - Art 5", "Zusatzinformation- Inhalt 5",
    "Zusatzinformation - Art 6", "Zusatzinformation- Inhalt 6",
    "Zusatzinformation - Art 7", "Zusatzinformation- Inhalt 7",
    "Zusatzinformation - Art 8", "Zusatzinformation- Inhalt 8",
    "Zusatzinformation - Art 9", "Zusatzinformation- Inhalt 9",
    "Zusatzinformation - Art 10", "Zusatzinformation- Inhalt 10",
    "Zusatzinformation - Art 11", "Zusatzinformation- Inhalt 11",
    "Zusatzinformation - Art 12", "Zusatzinformation- Inhalt 12",
    "Zusatzinformation - Art 13", "Zusatzinformation- Inhalt 13",
    "Zusatzinformation - Art 14", "Zusatzinformation- Inhalt 14",
    "Zusatzinformation - Art 15", "Zusatzinformation- Inhalt 15",
    "Zusatzinformation - Art 16", "Zusatzinformation- Inhalt 16",
    "Zusatzinformation - Art 17", "Zusatzinformation- Inhalt 17",
    "Zusatzinformation - Art 18", "Zusatzinformation- Inhalt 18",
    "Zusatzinformation - Art 19", "Zusatzinformation- Inhalt 19",
    "Zusatzinformation - Art 20", "Zusatzinformation- Inhalt 20",
    "Stück", "Gewicht", "Zahlweise", "Forderungsart",
    "Veranlagungsjahr", "Zugeordnete Fälligkeit", "Skontotyp", "Auftragsnummer",
    "Buchungstyp (Anzahlungen)", "USt-Schlüssel (Anzahlungen)",
    "EU-Land (Anzahlungen)", "Sachverhalt L+L (Anzahlungen)",
    "EU-Steuersatz (Anzahlungen)", "Erlöskonto (Anzahlungen)",
    "Herkunft-Kz", "Buchungs GUID", "KOST-Datum", "SEPA-Mandatsreferenz",
    "Skontosperre", "Gesellschaftername", "Beteiligtennummer",
    "Identifikationsnummer", "Zeichnernummer", "Postensperre bis",
    "Bezeichnung SoBil-Sachverhalt", "Kennzeichen SoBil-Buchung",
    "Festschreibung", "Leistungsdatum", "Datum Zuord. Steuerperiode",
    "Fälligkeit", "Generalumkehr (GU)", "Steuersatz", "Land",
    "Abrechnungsreferenz", "BVV-Position",
    "EU-Land u. UStID (Ursprung)", "EU-Steuersatz (Ursprung)",
    "Abw. Skontokonto",
]
assert len(DATEV_COLUMNS) == 125, f"Erwartet 125 Spalten, sind {len(DATEV_COLUMNS)}"
N_COLS = 125

# Spalten-Indizes (0-basiert), nach Spaltennamen aus DATEV_COLUMNS
COL = {name: idx for idx, name in enumerate(DATEV_COLUMNS)}


def _fmt_stueck(d: Decimal) -> str:
    """Stück als ganze Zahl ohne Exponentialschreibweise."""
    if d == 0:
        return ""
    # Wenn ganzzahlig, ohne Komma; sonst mit Komma
    if d == d.to_integral_value():
        return str(int(d))
    return f"{d}".replace(".", ",")


def _fmt_decimal(d: Decimal) -> str:
    """1234.56 -> '1234,56' (deutsches Format, kein Tausendertrenner)."""
    # Auf 2 Nachkommastellen runden
    q = d.quantize(Decimal("0.01"))
    s = f"{q}".replace(".", ",")
    return s


def _fmt_kurs(d: Decimal) -> str:
    """Kursfeld: max. 4 Nachkommastellen."""
    if d == 0:
        return ""
    q = d.quantize(Decimal("0.0001")).normalize()
    s = f"{q}".replace(".", ",")
    if "," not in s:
        s += ",00"
    return s


def _fmt_belegdatum(d: date) -> str:
    """Belegdatum DATEV: TTMM (kein Jahr — kommt aus dem Header)."""
    return d.strftime("%d%m")


def _build_header_line(config: dict, datum_von: date, datum_bis: date) -> str:
    """Erzeugt die erste Header-Zeile (Format-Identifikation)."""
    h = config["datev_header"]
    now = datetime.now()
    erzeugt_am = now.strftime("%Y%m%d%H%M%S") + "000"

    bezeichnung = h["stapel_bezeichnung_template"].format(
        datum_von=datum_von.strftime("%Y%m%d"),
        datum_bis=datum_bis.strftime("%Y%m%d"),
    )

    fields = [
        "DTVF",                              # 1  Format-Kennzeichen
        "700",                               # 2  Versionsnummer
        "21",                                # 3  Format-Kategorie (21 = Buchungsstapel)
        "Buchungsstapel",                    # 4  Format-Name
        "13",                                # 5  Format-Version
        erzeugt_am,                          # 6  Erzeugt am
        "",                                  # 7  Imported (leer beim Export)
        "RE",                                # 8  Herkunft (RE = Rechnungswesen)
        h.get("exportiert_von", "claude"),   # 9  Exportiert von
        "",                                  # 10 Importiert von
        str(h["berater_nr"]),                # 11 Berater
        str(h["mandant_nr"]),                # 12 Mandant
        str(h["wj_beginn"]),                 # 13 WJ-Beginn (YYYYMMDD)
        str(h["sachkontenlaenge"]),          # 14 Sachkontenlänge
        datum_von.strftime("%Y%m%d"),        # 15 Datum von
        datum_bis.strftime("%Y%m%d"),        # 16 Datum bis
        bezeichnung,                         # 17 Bezeichnung
        h.get("diktatkuerzel", ""),          # 18 Diktatkürzel
        str(h.get("buchungstyp", 1)),        # 19 Buchungstyp
        str(h.get("rechnungslegungszweck", 0)),  # 20
        str(h.get("festschreibung", 0)),     # 21 Festschreibung
        h.get("waehrung", "EUR"),            # 22 WKZ
        "",                                  # 23 Reserviert
        "",                                  # 24 Derivatkennzeichen
        "",                                  # 25 Reserviert
        "",                                  # 26 Reserviert
        h.get("sachkontenrahmen", "04"),     # 27 Sachkontenrahmen (04=SKR04)
        # 28+: weitere Felder, alle leer
    ]
    # Auffüllen auf N_COLS Felder, damit die Zeile die gleiche Spaltenzahl hat
    # wie die Datenzeilen (so macht es auch die Steuerberater-Beispiel-CSV)
    while len(fields) < N_COLS:
        fields.append("")
    return ";".join(fields)


def buchungen_zu_csv(buchungen: List[Buchung], config: dict, datum_von: date, datum_bis: date) -> bytes:
    """Erzeugt die DTVF-CSV als Bytes (windows-1252, CRLF)."""
    output = io.StringIO()
    writer = csv.writer(
        output, delimiter=";", quotechar='"',
        quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n"
    )

    # Zeile 1: Header (Format-Identifikation)
    output.write(_build_header_line(config, datum_von, datum_bis))
    output.write("\r\n")

    # Zeile 2: Spaltennamen
    writer.writerow(DATEV_COLUMNS)

    # Datenzeilen
    h = config["datev_header"]
    festschreibung = str(h.get("festschreibung", 0))

    for b in buchungen:
        row = [""] * N_COLS

        row[COL["Umsatz (ohne Soll/Haben-Kz)"]] = _fmt_decimal(b.umsatz)
        row[COL["Soll/Haben-Kennzeichen"]] = b.soll_haben
        row[COL["WKZ Umsatz"]] = "EUR"
        if b.kurs:
            row[COL["Kurs"]] = _fmt_kurs(b.kurs)
        row[COL["Konto"]] = b.konto
        row[COL["Gegenkonto (ohne BU-Schlüssel)"]] = b.gegenkonto
        row[COL["Belegdatum"]] = _fmt_belegdatum(b.belegdatum)
        row[COL["Belegfeld 1"]] = b.belegfeld_1
        row[COL["Belegfeld 2"]] = b.belegfeld_2
        row[COL["Buchungstext"]] = b.buchungstext[:60]

        # Beleginfo-Felder: ISIN, WKN, Stück, Kurs, Quell-Seite, Kategorie
        if b.isin:
            row[COL["Beleginfo - Art 1"]] = "ISIN"
            row[COL["Beleginfo - Inhalt 1"]] = b.isin
        if b.wkn:
            row[COL["Beleginfo - Art 2"]] = "WKN"
            row[COL["Beleginfo - Inhalt 2"]] = b.wkn
        if b.stueck:
            row[COL["Beleginfo - Art 3"]] = "Stueck"
            row[COL["Beleginfo - Inhalt 3"]] = _fmt_stueck(b.stueck)
        if b.kurs:
            row[COL["Beleginfo - Art 4"]] = "Kurs"
            row[COL["Beleginfo - Inhalt 4"]] = _fmt_kurs(b.kurs)
        if b.kategorie:
            row[COL["Beleginfo - Art 5"]] = "Kategorie"
            row[COL["Beleginfo - Inhalt 5"]] = b.kategorie
        if b.quell_seite:
            row[COL["Beleginfo - Art 6"]] = "Quellseite"
            row[COL["Beleginfo - Inhalt 6"]] = str(b.quell_seite)

        if b.stueck:
            row[COL["Stück"]] = _fmt_stueck(b.stueck)
        row[COL["Herkunft-Kz"]] = "RE"
        row[COL["Festschreibung"]] = festschreibung

        writer.writerow(row)

    return output.getvalue().encode("cp1252", errors="replace")


def schreibe_review_csv(belege, ignored, path: str) -> None:
    """Schreibt ein Review-CSV mit allen Belegen und ignorierten Seiten."""
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow([
            "Seite", "Status", "Typ", "Auftragsnr", "Datum", "ISIN", "WKN",
            "Bezeichnung", "Stueck", "Kurswert", "Gebuehren", "Tranchen",
            "Ausmachend", "Teilfrei", "PlausiOK", "Warnung",
        ])
        for b in belege:
            tranchen_info = " | ".join(
                f"AK={_fmt_decimal(t.ak)} Erloes={_fmt_decimal(t.erloes_ant)} ({'G' if t.ist_gewinn else 'V'})"
                for t in b.tranchen
            )
            w.writerow([
                b.seite, "OK" if b.plausi_ok else "PLAUSI-FAIL", b.typ,
                b.auftragsnummer, b.schlusstag.strftime("%d.%m.%Y"),
                b.isin, b.wkn or "", b.wertpapierbezeichnung,
                _fmt_stueck(b.stueck),
                _fmt_decimal(b.kurswert),
                _fmt_decimal(b.gebuehren_summe),
                tranchen_info,
                _fmt_decimal(b.ausmachender_betrag),
                "JA" if b.teilfreistellung else "NEIN",
                "JA" if b.plausi_ok else "NEIN",
                " | ".join(b.warnings),
            ])
        for ig in ignored:
            w.writerow([ig.seite, "IGNORIERT", ig.typ] + [""] * 12 + [ig.grund])

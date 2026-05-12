"""
parser.py — Extraktion aus Stadtsparkasse-Wertpapierabrechnungen.

Verarbeitet:
  - Wertpapier Abrechnung Kauf
  - Wertpapier Abrechnung Verkauf
  - Wertpapier Abrechnung Rücknahme Investmentfonds (wird als VERKAUF behandelt)

Seite 2 (Berücksichtigte Anschaffungsgeschäfte) wird automatisch der
vorangehenden Seite 1 zugeordnet und liefert Tranchendaten.
"""
import re
from dataclasses import dataclass, field
from typing import Optional, List, Literal
from decimal import Decimal, ROUND_HALF_UP
from datetime import date

import pdfplumber


@dataclass
class Tranche:
    """Eine Anschaffungstranche aus Seite 2 der Abrechnung."""
    stueck: Decimal
    ak: Decimal          # Anschaffungskosten / Buchwert (positiv)
    erloes_ant: Decimal  # anteiliger Netto-Erlös (nach Provision) — positiv
    ist_gewinn: bool     # True=Gewinn, False=Verlust


@dataclass
class Beleg:
    """Eine geparste Wertpapierabrechnung (Kauf oder Verkauf)."""
    typ: Literal["KAUF", "VERKAUF"]
    seite: int
    auftragsnummer: str
    rechnungsnummer: Optional[str]
    datum_dokument: date
    schlusstag: date
    isin: str
    wkn: Optional[str]
    wertpapierbezeichnung: str
    stueck: Decimal
    ausfuehrungskurs: Optional[Decimal]
    kurswert: Decimal
    gebuehren_summe: Decimal
    ausmachender_betrag: Decimal
    tranchen: List[Tranche] = field(default_factory=list)
    teilfreistellung: bool = False
    plausi_ok: bool = True
    plausi_diff: Decimal = Decimal("0")
    warnings: List[str] = field(default_factory=list)


@dataclass
class IgnoredPage:
    seite: int
    typ: str
    grund: str


def _parse_decimal(s: str) -> Decimal:
    s = re.sub(r"[^0-9,]", "", s.replace(".", ""))
    if "," in s:
        s = s.replace(",", ".")
    return Decimal(s) if s else Decimal("0")


def _parse_date(s: str) -> date:
    d, m, y = s.strip().split(".")
    return date(int(y), int(m), int(d))


# Regex — alle auf normalisiertem Text (Zeilenumbrüche → Leerzeichen)
RE_AUFTRAGSNR   = re.compile(r"Auftragsnummer\s+(\S+)")
RE_DATUM_DOK    = re.compile(r"\bDatum\s+(\d{2}\.\d{2}\.\d{4})")
RE_RECHNUNGSNR  = re.compile(r"Rechnungsnummer\s+(\S+)")
RE_SCHLUSSTAG   = re.compile(r"Schlusstag[-/]?-?Zeit\s+(\d{2}\.\d{2}\.\d{4})")
RE_AUSFKURS     = re.compile(r"Ausführungskurs\s+([\d.,]+)\s*EUR")
RE_NOMINAL      = re.compile(
    r"Stück\s+([\d.,]+)\s+(.+?)\s+([A-Z]{2}[A-Z0-9]{9}\d)\s*(?:\(([A-Z0-9]+)\))?",
    re.DOTALL,
)
RE_KURSWERT     = re.compile(r"Kurswert\s+([\d.,]+)-?\s*EUR")
RE_PROVISION    = re.compile(r"Provision[^\n]*?([\d.,]+)-\s*EUR")
RE_ABWICKLUNG   = re.compile(r"Abwicklungskosten\s+(?:Börse\s+)?([\d.,]+)-\s*EUR")
RE_TRANSAKTION  = re.compile(r"Transaktionsentgelt\s+(?:Börse\s+)?([\d.,]+)-\s*EUR")
RE_FREMDE       = re.compile(r"Fremde Auslagen\s+([\d.,]+)-?\s*EUR")
RE_LIEFERGEBUEHR= re.compile(r"Übertragungs-/Liefergebühr\s+([\d.,]+)-?\s*EUR")
RE_AUSMACHEND   = re.compile(r"Ausmachender Betrag\s+([\d.,]+)[-+]?\s*EUR")
RE_TEILFREI_FLAG= re.compile(r"Teilfreistellung", re.IGNORECASE)

# Tranche-Zeilen auf Seite 2
RE_TRANCHE_ROW  = re.compile(
    r"(?:Kauf|Einbuchung|Verkauf)\s+"   # Geschäftsart
    r"\S+\s+"                            # Original-Auftragsnr.
    r"\d{2}\.\d{2}\.\d{4}\s+"           # Ausführungstag
    r"Stück\s+"                          # Einheit
    r"([\d.,]+)\s+"                      # Stück
    r"([\d.,]+)-\s+"                     # AS-Kosten (immer negativ)
    r"([\d.,]+)\s+"                      # Erlös ant.
    r"(?:[\d.,]+-?\s+)?"                 # Teilfreistellung (optional, überspringen)
    r"([\d.,]+)(-?)\s*\(?D?\)?",         # Ergebnis + Vorzeichen-Flag
)


def _classify(text_flat: str) -> str:
    if "Wertpapier Abrechnung Kauf" in text_flat:
        return "ABRECHNUNG_KAUF"
    if "Wertpapier Abrechnung Rücknahme Investmentfonds" in text_flat:
        return "ABRECHNUNG_RUECKNAHME"
    if "Wertpapier Abrechnung Verkauf" in text_flat:
        return "ABRECHNUNG_VERKAUF"
    if "Auftragsbestätigung" in text_flat:
        return "AUFTRAGSBESTAETIGUNG"
    if "Ausführungsanzeige" in text_flat:
        return "AUSFUEHRUNGSANZEIGE"
    if "Änderungsbestätigung" in text_flat:
        return "AENDERUNGSBESTAETIGUNG"
    if "Streichungsbestätigung" in text_flat:
        return "STREICHUNGSBESTAETIGUNG"
    if "Berücksichtigte Anschaffungsgeschäfte" in text_flat or "ant. Ergebnis" in text_flat:
        return "SEITE_2"
    if "Seite 2 von 2" in text_flat:
        return "SEITE_2_KAUF_MISCH"
    if "Verlustschwellenreport" in text_flat or "MiFID II" in text_flat:
        return "VERLUSTSCHWELLENREPORT"
    return "UNBEKANNT"


def _extract_tranchen(text_flat: str) -> List[Tranche]:
    tranchen = []
    for m in RE_TRANCHE_ROW.finditer(text_flat):
        stueck     = _parse_decimal(m.group(1))
        ak         = _parse_decimal(m.group(2))
        erloes_ant = _parse_decimal(m.group(3))
        verlust_flag = m.group(5) == "-"
        ist_gewinn = not verlust_flag
        tranchen.append(Tranche(stueck=stueck, ak=ak, erloes_ant=erloes_ant, ist_gewinn=ist_gewinn))
    return tranchen


def _extract_beleg(text_flat: str, seite_nr: int, typ: Literal["KAUF", "VERKAUF"]) -> Beleg:
    def req(pattern, label):
        m = pattern.search(text_flat)
        if not m:
            raise ValueError(f"Seite {seite_nr}: '{label}' nicht gefunden")
        return m

    auftragsnr = req(RE_AUFTRAGSNR, "Auftragsnummer").group(1)
    datum_dok  = _parse_date(req(RE_DATUM_DOK, "Datum").group(1))
    rnr_m      = RE_RECHNUNGSNR.search(text_flat)
    rechnungsnr = rnr_m.group(1) if rnr_m else None

    schluss_m = RE_SCHLUSSTAG.search(text_flat)
    schlusstag = _parse_date(schluss_m.group(1)) if schluss_m else datum_dok

    nom_m = req(RE_NOMINAL, "Nominale/ISIN")
    stueck = _parse_decimal(nom_m.group(1))
    bezeichnung = re.sub(r"\s+", " ", nom_m.group(2)).strip()
    isin = nom_m.group(3)
    wkn  = nom_m.group(4)

    kurs_m = RE_AUSFKURS.search(text_flat)
    kurs   = _parse_decimal(kurs_m.group(1)) if kurs_m else None

    kurswert = _parse_decimal(req(RE_KURSWERT, "Kurswert").group(1))

    gebuehren = Decimal("0")
    for label, rg in [
        ("Provision", RE_PROVISION),
        ("Abwicklungskosten", RE_ABWICKLUNG),
        ("Transaktionsentgelt", RE_TRANSAKTION),
        ("Fremde Auslagen", RE_FREMDE),
        ("Übertragungs-/Liefergebühr", RE_LIEFERGEBUEHR),
    ]:
        m = rg.search(text_flat)
        if m:
            gebuehren += _parse_decimal(m.group(1))

    ausmachend = _parse_decimal(req(RE_AUSMACHEND, "Ausmachender Betrag").group(1))

    teilfrei = bool(RE_TEILFREI_FLAG.search(text_flat))

    # Plausi
    if typ == "KAUF":
        erwartet = kurswert + gebuehren
    else:
        erwartet = kurswert - gebuehren
    diff = abs(ausmachend - erwartet)

    b = Beleg(
        typ=typ,
        seite=seite_nr,
        auftragsnummer=auftragsnr,
        rechnungsnummer=rechnungsnr,
        datum_dokument=datum_dok,
        schlusstag=schlusstag,
        isin=isin,
        wkn=wkn,
        wertpapierbezeichnung=bezeichnung,
        stueck=stueck,
        ausfuehrungskurs=kurs,
        kurswert=kurswert,
        gebuehren_summe=gebuehren,
        ausmachender_betrag=ausmachend,
        teilfreistellung=teilfrei,
        plausi_diff=diff,
    )
    if diff > Decimal("0.05"):
        b.plausi_ok = False
        b.warnings.append(f"Plausi-Diff {diff:.2f} EUR (erwartet {erwartet:.2f}, Beleg {ausmachend:.2f})")

    return b


def parse_pdf(pdf_path: str) -> tuple[list[Beleg], list[IgnoredPage]]:
    """Liest PDF und gibt (belege, ignored) zurück."""
    belege: list[Beleg] = []
    ignored: list[IgnoredPage] = []
    pending_beleg: Optional[Beleg] = None  # wartet auf Seite 2

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            raw  = page.extract_text() or ""
            text = raw.replace("\n", " ").replace("  ", " ")
            doctype = _classify(text)

            if doctype == "SEITE_2" and pending_beleg is not None:
                # Tranchendaten an letzten VERKAUF anhängen
                tranchen = _extract_tranchen(text)
                if tranchen:
                    pending_beleg.tranchen = tranchen
                # Jetzt einbuchen
                belege.append(pending_beleg)
                pending_beleg = None
                ignored.append(IgnoredPage(i, "SEITE_2", "Tranchendaten — an vorangehende Abrechnung gehängt"))
                continue

            # Vorherigen pending VERKAUF ohne Seite 2 noch speichern
            if pending_beleg is not None:
                pending_beleg.warnings.append("Keine Seite 2 gefunden — AK wird aus Seite-1-Daten berechnet")
                belege.append(pending_beleg)
                pending_beleg = None

            if doctype == "ABRECHNUNG_KAUF":
                try:
                    b = _extract_beleg(text, i, "KAUF")
                    belege.append(b)
                except Exception as e:
                    ignored.append(IgnoredPage(i, "PARSE_ERROR_KAUF", str(e)))

            elif doctype in ("ABRECHNUNG_VERKAUF", "ABRECHNUNG_RUECKNAHME"):
                try:
                    b = _extract_beleg(text, i, "VERKAUF")
                    if doctype == "ABRECHNUNG_RUECKNAHME":
                        b.warnings.append("Rücknahme Investmentfonds — als Verkauf behandelt")
                    pending_beleg = b  # Seite 2 abwarten
                except Exception as e:
                    ignored.append(IgnoredPage(i, "PARSE_ERROR_VERKAUF", str(e)))

            elif doctype == "SEITE_2":
                ignored.append(IgnoredPage(i, "SEITE_2_VERWAIST", "Seite 2 ohne vorangehende Abrechnung — übersprungen"))

            elif doctype == "AUFTRAGSBESTAETIGUNG":
                ignored.append(IgnoredPage(i, doctype, "Auftragsbestätigung — kein Geldfluss"))
            elif doctype == "AUSFUEHRUNGSANZEIGE":
                ignored.append(IgnoredPage(i, doctype, "Ausführungsanzeige — Abrechnung folgt separat"))
            elif doctype == "AENDERUNGSBESTAETIGUNG":
                ignored.append(IgnoredPage(i, doctype, "Änderungsbestätigung — kein Geldfluss"))
            elif doctype == "STREICHUNGSBESTAETIGUNG":
                ignored.append(IgnoredPage(i, doctype, "Streichungsbestätigung — kein Geldfluss"))
            elif doctype == "SEITE_2_KAUF_MISCH":
                ignored.append(IgnoredPage(i, doctype, "Seite 2 Mischkursabrechnung (Teilfüllungsdetails) — kein Geldfluss"))
            elif doctype == "VERLUSTSCHWELLENREPORT":
                ignored.append(IgnoredPage(i, doctype, "MiFID II Verlustschwellenreport — kein Geldfluss"))
            else:
                ignored.append(IgnoredPage(i, "UNBEKANNT", f"Belegtyp nicht erkannt (Snippet: {text[:80]!r})"))

    # Letzter pending falls PDF mit Verkauf ohne Seite 2 endet
    if pending_beleg is not None:
        pending_beleg.warnings.append("Keine Seite 2 — AK aus Seite-1-Daten")
        belege.append(pending_beleg)

    return belege, ignored

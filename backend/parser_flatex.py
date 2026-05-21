"""
parser_flatex.py — Extraktion aus flatexDEGIRO-Bank-Abrechnungen.

Verarbeitet:
  - Sammelabrechnung Wertpapierkauf/-verkauf
  - Dividendengutschrift (in-/ausländische Wertpapiere)
  - Ertragsmitteilung ausschüttender/teilthesaurierender Fonds

Unterschiede zur Sparkasse:
  - Key-Value-Layout statt Tabelle ("Kurs : 1.225,40 EUR")
  - Mehrere Belege in einer Sammelabrechnung möglich
  - Keine separaten Anschaffungstranchen — nur Gesamt-Gewinn/Verlust
    → Wir bauen eine synthetische Single-Tranche aus dem G/V-Wert
  - Zusätzliche Belegtypen DIVIDENDE und FONDSERTRAG
"""

import re
from dataclasses import dataclass, field
from typing import Optional, List, Literal
from decimal import Decimal
from datetime import date

import pdfplumber


# ── Dataclasses (kompatibel zu Sparkasse-Parser) ─────────────────
@dataclass
class Tranche:
    stueck: Decimal
    ak: Decimal
    erloes_ant: Decimal
    ist_gewinn: bool


@dataclass
class Beleg:
    typ: Literal["KAUF", "VERKAUF", "DIVIDENDE", "FONDSERTRAG"]
    seite: int
    auftragsnummer: str
    rechnungsnummer: Optional[str]
    datum_dokument: date
    schlusstag: date  # bei Dividende = Zahlungstag, bei Fonds = Valuta
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
    # Erweiterungen für Dividende/Fondsertrag
    teilfrei_satz: Optional[Decimal] = None   # z.B. 30.00 für 30%
    teilfrei_betrag: Optional[Decimal] = None # in EUR
    quellensteuer_eur: Optional[Decimal] = None
    kapitalertragsteuer: Optional[Decimal] = None
    soli: Optional[Decimal] = None
    devisenkurs: Optional[Decimal] = None


@dataclass
class IgnoredPage:
    seite: int
    typ: str
    grund: str


# ── Helper ────────────────────────────────────────────────────────
def _dec(s: str) -> Decimal:
    """Parst '1.225,4000' oder '-2.001,00' zu Decimal."""
    s = s.strip().replace(".", "").replace(",", ".")
    return Decimal(s) if s else Decimal("0")


def _ddmmyyyy(s: str) -> date:
    d, m, y = s.strip().split(".")
    return date(int(y), int(m), int(d))


def _find(text: str, pattern: str, default=None):
    m = re.search(pattern, text)
    return m.group(1) if m else default


def _dec_or_none(text: str, pattern: str) -> Optional[Decimal]:
    v = _find(text, pattern)
    return _dec(v) if v else None


# ── Bank-Erkennung ────────────────────────────────────────────────
def is_flatex_pdf(text: str) -> bool:
    return ("flatexDEGIRO" in text or
            "flatex.de" in text or
            "BIWBDE33XXX" in text)


# ── Hauptfunktion ─────────────────────────────────────────────────
def parse_pdf(pdf_path: str) -> tuple[list[Beleg], list[IgnoredPage]]:
    """Extrahiert alle Belege aus einem Flatex-PDF."""
    with pdfplumber.open(pdf_path) as pdf:
        full_text = "\n".join((p.extract_text() or "") for p in pdf.pages)
        n_pages = len(pdf.pages)

    # Dokument-Datum (für Rechnungsdatum / Belegdatum)
    dok_datum_str = _find(full_text, r"Frankfurt,\s+(\d{2}\.\d{2}\.\d{4})")
    dok_datum = _ddmmyyyy(dok_datum_str) if dok_datum_str else date.today()

    belege: list[Beleg] = []
    ignored: list[IgnoredPage] = []

    # Routing nach Belegtyp
    if "Sammelabrechnung" in full_text or "Wertpapierabrechnung" in full_text:
        belege.extend(_parse_kaeufe_verkaeufe(full_text, dok_datum))

    elif "Dividendengutschrift" in full_text:
        b = _parse_dividende(full_text, dok_datum)
        if b: belege.append(b)
        else: ignored.append(IgnoredPage(1, "DIVIDENDE", "Parsing fehlgeschlagen"))

    elif "Ertragsmitteilung" in full_text:
        b = _parse_fondsertrag(full_text, dok_datum)
        if b: belege.append(b)
        else: ignored.append(IgnoredPage(1, "FONDSERTRAG", "Parsing fehlgeschlagen"))

    else:
        ignored.append(IgnoredPage(
            seite=1, typ="UNBEKANNT",
            grund="Belegtyp nicht erkannt (weder Sammelabrechnung noch Dividende noch Ertragsmitteilung)"
        ))

    return belege, ignored


# ── Verkauf / Kauf parsen ─────────────────────────────────────────
RE_BELEG_HEADER = re.compile(
    r"Nr\.(\d+(?:/\d+)?)\s+(Verkauf|Kauf)\s+(.+?)\s+"
    r"\(([A-Z]{2}[A-Z0-9]{9}\d)/([A-Z0-9]+)\)"
)


def _parse_kaeufe_verkaeufe(text: str, dok_datum: date) -> list[Beleg]:
    """Findet alle Beleg-Blöcke (Nr.X/Y) und parst sie einzeln."""
    belege = []
    matches = list(RE_BELEG_HEADER.finditer(text))

    for i, m in enumerate(matches):
        block_start = m.start()
        block_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[block_start:block_end]

        auftragsnr = m.group(1)
        typ = m.group(2).upper()
        bezeichnung = m.group(3).strip()
        isin = m.group(4)
        wkn = m.group(5)

        stueck = (_dec_or_none(block, r"davon ausgef\.\s*:\s*([\d.,]+)\s*St\.")
                  or _dec_or_none(block, r"Ordervolumen\s*:\s*([\d.,]+)\s*St\.")
                  or Decimal("0"))

        kurs = _dec_or_none(block, r"Kurs\s*:\s*([\d.,]+)\s*EUR")
        kurswert = _dec_or_none(block, r"Kurswert\s*:\s*([\d.,]+)\s*EUR") or Decimal("0")
        provision = _dec_or_none(block, r"Provision\s*:\s*([\d.,]+)\s*EUR") or Decimal("0")
        fremde_spesen = _dec_or_none(block, r"\*?Fremde Spesen\s*:\s*([\d.,]+)\s*EUR") or Decimal("0")
        endbetrag = _dec_or_none(block, r"Endbetrag\s*:\s*([\d.,]+)\s*EUR") or Decimal("0")

        # Gewinn/Verlust kann negativ sein
        gv_match = re.search(r"Gewinn/Verlust:?\s*(-?[\d.,]+)\s*EUR", block)
        gewinn_verlust = _dec(gv_match.group(1)) if gv_match else None

        schlusstag_str = _find(block, r"Schlusstag\s*:\s*(\d{2}\.\d{2}\.\d{4})")
        schlusstag = _ddmmyyyy(schlusstag_str) if schlusstag_str else dok_datum

        gebuehren_summe = provision + fremde_spesen

        # Tranchen für Verkauf aus G/V ableiten (synthetische Single-Tranche)
        # erloes_ant = anteiliger Netto-Erlös NACH Gebührenabzug (= Endbetrag bei Single-Tranche)
        # AK = Kurswert - Gewinn  (G/V negativ → höhere AK)
        tranchen = []
        if typ == "VERKAUF" and gewinn_verlust is not None and kurswert:
            ak = kurswert - gewinn_verlust
            tranchen = [Tranche(
                stueck=stueck,
                ak=ak,
                erloes_ant=endbetrag if endbetrag else (kurswert - gebuehren_summe),
                ist_gewinn=gewinn_verlust > 0,
            )]

        # Plausibilität: Endbetrag = Kurswert ± Gebühren (bei Verkauf: Kurswert - Gebühren)
        warnings = []
        plausi_ok = True
        plausi_diff = Decimal("0")
        if endbetrag and kurswert:
            expected = (kurswert - gebuehren_summe) if typ == "VERKAUF" else (kurswert + gebuehren_summe)
            plausi_diff = abs(endbetrag - expected)
            if plausi_diff > Decimal("0.05"):
                plausi_ok = False
                warnings.append(f"Endbetrag-Abweichung: erwartet {expected}, ist {endbetrag}")

        belege.append(Beleg(
            typ=typ,
            seite=0,
            auftragsnummer=auftragsnr,
            rechnungsnummer=None,
            datum_dokument=dok_datum,
            schlusstag=schlusstag,
            isin=isin,
            wkn=wkn,
            wertpapierbezeichnung=bezeichnung,
            stueck=stueck,
            ausfuehrungskurs=kurs,
            kurswert=kurswert,
            gebuehren_summe=gebuehren_summe,
            ausmachender_betrag=endbetrag,
            tranchen=tranchen,
            teilfreistellung=False,
            plausi_ok=plausi_ok,
            plausi_diff=plausi_diff,
            warnings=warnings,
        ))

    return belege


# ── Dividende parsen ──────────────────────────────────────────────
def _parse_dividende(text: str, dok_datum: date) -> Optional[Beleg]:
    """Parst eine Dividendengutschrift (in- oder ausländisch)."""

    # Header: "Nr.XXXXX  WP-NAME (ISIN/WKN)"
    header = re.search(
        r"Nr\.(\d+)\s+(.+?)\s+\(([A-Z]{2}[A-Z0-9]{9}\d)/([A-Z0-9]+)\)",
        text,
    )
    if not header:
        return None

    auftragsnr = header.group(1)
    bezeichnung = header.group(2).strip()
    isin = header.group(3)
    wkn = header.group(4)

    stueck = _dec_or_none(text, r"St\.\s*:\s*([\d.,]+)") or Decimal("0")
    brutto_pro_st = _dec_or_none(text, r"pro Stück\s*:\s*([\d.,]+)\s*(?:USD|EUR)")
    bruttodividende_str = _find(text, r"Bruttodividende\s*:\s*([\d.,]+)\s*(?:USD|EUR)")
    bruttodividende = _dec(bruttodividende_str) if bruttodividende_str else Decimal("0")

    bemessung_eur = _dec_or_none(text, r"Bemessungs.{0,15}grundlage\s*:\s*([\d.,]+)\s*EUR") or Decimal("0")
    devisenkurs = _dec_or_none(text, r"Devisenkurs\s*:\s*([\d.,]+)")

    quellenst_usd = _dec_or_none(text, r"Gez\.\s*Quellenst\.\s*:\s*([\d.,]+)\s*USD")
    quellenst_eur = (quellenst_usd / devisenkurs) if quellenst_usd and devisenkurs else None

    endbetrag = _dec_or_none(text, r"Endbetrag\s*:\s*([\d.,]+)\s*EUR") or Decimal("0")

    kapest = _dec_or_none(text, r"Kapitalertragsteuer\s*:\s*([\d.,]+)\s*EUR") or Decimal("0")
    soli = _dec_or_none(text, r"Solidaritätszuschlag\s*:\s*([\d.,]+)\s*EUR") or Decimal("0")

    zahlungstag_str = _find(text, r"Zahlungstag\s*:\s*(\d{2}\.\d{2}\.\d{4})")
    valuta_str = _find(text, r"Valuta\s*:\s*(\d{2}\.\d{2}\.\d{4})")
    schlusstag = _ddmmyyyy(zahlungstag_str or valuta_str) if (zahlungstag_str or valuta_str) else dok_datum

    return Beleg(
        typ="DIVIDENDE",
        seite=0,
        auftragsnummer=auftragsnr,
        rechnungsnummer=None,
        datum_dokument=dok_datum,
        schlusstag=schlusstag,
        isin=isin,
        wkn=wkn,
        wertpapierbezeichnung=bezeichnung,
        stueck=stueck,
        ausfuehrungskurs=brutto_pro_st,
        kurswert=bemessung_eur,           # Bemessungsgrundlage in EUR = "Bruttodividende EUR netto US-QSt"
        gebuehren_summe=Decimal("0"),
        ausmachender_betrag=endbetrag,
        tranchen=[],
        teilfreistellung=False,
        devisenkurs=devisenkurs,
        quellensteuer_eur=quellenst_eur,
        kapitalertragsteuer=kapest,
        soli=soli,
    )


# ── Fondsertrag parsen ────────────────────────────────────────────
def _parse_fondsertrag(text: str, dok_datum: date) -> Optional[Beleg]:
    """Parst eine Fonds-Ertragsmitteilung (mit Teilfreistellung)."""
    header = re.search(
        r"Nr\.(\d+)\s+(.+?)\s+\(([A-Z]{2}[A-Z0-9]{9}\d)/([A-Z0-9]+)\)",
        text,
    )
    if not header:
        return None

    auftragsnr = header.group(1)
    bezeichnung = header.group(2).strip()
    isin = header.group(3)
    wkn = header.group(4)

    stueck = _dec_or_none(text, r"St\.\s*:\s*([\d.,]+)") or Decimal("0")
    brutto_pro_st = _dec_or_none(text, r"pro Stück\s*:\s*([\d.,]+)\s*(?:USD|EUR)")
    bruttoausschuettung_str = _find(text, r"Bruttoausschüttung\s*:\s*([\d.,]+)\s*(?:USD|EUR)")
    bruttoausschuettung = _dec(bruttoausschuettung_str) if bruttoausschuettung_str else Decimal("0")

    bemessung_eur = _dec_or_none(text, r"Bemessungsgrundlage\s*:\s*([\d.,]+)\s*EUR") or Decimal("0")
    devisenkurs = _dec_or_none(text, r"Devisenkurs\s*:\s*([\d.,]+)")

    teilfrei_satz = _dec_or_none(text, r"Teilfreist\.-satz:\s*([\d.,]+)\s*%")
    teilfrei_betrag = _dec_or_none(text, r"Teilfreistellung\s*:\s*([\d.,]+)\s*EUR")

    einbeh_steuer = _dec_or_none(text, r"\*Einbeh\.\s*Steuer\s*:\s*([\d.,]+)\s*EUR") or Decimal("0")
    kapest = _dec_or_none(text, r"Kapitalertragsteuer\s*:\s*([\d.,]+)\s*EUR") or Decimal("0")
    soli = _dec_or_none(text, r"Solidaritätszuschlag\s*:\s*([\d.,]+)\s*EUR") or Decimal("0")

    endbetrag = _dec_or_none(text, r"Endbetrag\s*:\s*([\d.,]+)\s*EUR") or Decimal("0")
    valuta_str = _find(text, r"Valuta\s*:\s*(\d{2}\.\d{2}\.\d{4})")
    schlusstag = _ddmmyyyy(valuta_str) if valuta_str else dok_datum

    warnings = []
    if teilfrei_satz == Decimal("30"):
        warnings.append("Teilfreist.-Satz 30% (Privatanleger) — für GmbH gilt 80% (Aktienfonds)")

    return Beleg(
        typ="FONDSERTRAG",
        seite=0,
        auftragsnummer=auftragsnr,
        rechnungsnummer=None,
        datum_dokument=dok_datum,
        schlusstag=schlusstag,
        isin=isin,
        wkn=wkn,
        wertpapierbezeichnung=bezeichnung,
        stueck=stueck,
        ausfuehrungskurs=brutto_pro_st,
        kurswert=bemessung_eur,
        gebuehren_summe=Decimal("0"),
        ausmachender_betrag=endbetrag,
        tranchen=[],
        teilfreistellung=teilfrei_satz is not None and teilfrei_satz > 0,
        teilfrei_satz=teilfrei_satz,
        teilfrei_betrag=teilfrei_betrag,
        kapitalertragsteuer=kapest,
        soli=soli,
        devisenkurs=devisenkurs,
        warnings=warnings,
    )

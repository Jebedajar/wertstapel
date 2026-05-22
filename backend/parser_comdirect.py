"""
parser_comdirect.py — Parser für comdirect XLSX-Transaktionsexporte.

Quelldatei: vom Kunden aus der comdirect-Web-Oberfläche heruntergeladenes XLSX
            mit allen Trades eines Zeitraums.

Besonderheiten:
  - Comdirect liefert keine Gewinn/Verlust-Werte pro Trade
  - AK werden via FIFO aus den im XLSX enthaltenen Käufen berechnet
  - Bei Verkäufen von Positionen die vor dem XLSX-Zeitraum gekauft wurden
    fehlt die AK — Marker #AK-PRÜFEN# im Buchungstext, Buchung trotzdem
    erstellt aber mit AK=0 für den unbekannten Teil
  - Finanztransaktionssteuer (Spalte "Transaktionssteuer(n) EUR") wird als
    eigener Beleg vom Typ FTT erzeugt und separat gebucht (SKR04 6305)
  - Verwahrentgelt und Zinsgutschrift sind im XLSX NICHT enthalten —
    diese stehen nur im Finanzreport-PDF (separates Dokument)
"""

import re
from dataclasses import dataclass, field
from typing import Optional, List, Literal, Dict, Tuple
from decimal import Decimal
from datetime import date
import pandas as pd


# ── Beleg/Tranche kompatibel zu Sparkasse/Flatex ─────────────────
@dataclass
class Tranche:
    stueck: Decimal
    ak: Decimal
    erloes_ant: Decimal
    ist_gewinn: bool


@dataclass
class Beleg:
    typ: Literal["KAUF", "VERKAUF", "FTT"]
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
    ak_unvollstaendig: bool = False
    devisenkurs: Optional[Decimal] = None
    teilfrei_satz: Optional[Decimal] = None
    teilfrei_betrag: Optional[Decimal] = None
    quellensteuer_eur: Optional[Decimal] = None
    kapitalertragsteuer: Optional[Decimal] = None
    soli: Optional[Decimal] = None


@dataclass
class IgnoredPage:
    seite: int
    typ: str
    grund: str


# ── Helper ─────────────────────────────────────────────────────────
def _dec(x) -> Decimal:
    """Wandelt beliebigen Excel-Wert in Decimal."""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return Decimal("0")
    if isinstance(x, str):
        x = x.strip().replace(".", "").replace(",", ".")
        if not x:
            return Decimal("0")
    return Decimal(str(x))


def _parse_date(x) -> date:
    """Comdirect XLSX hat manchmal Strings, manchmal Timestamps."""
    if isinstance(x, str):
        d, m, y = x.split(".")
        return date(int(y), int(m), int(d))
    return x.date() if hasattr(x, "date") else x


# ── Bank-Erkennung ─────────────────────────────────────────────────
def is_comdirect_xlsx(xlsx_path: str) -> bool:
    """Erkennt Comdirect-XLSX anhand der Spaltenstruktur."""
    try:
        df = pd.read_excel(xlsx_path, nrows=1)
        cols = [str(c).lower() for c in df.columns]
        return ("abrechnungstag" in cols and "geschäftsart" in cols
                and "kundenendbetrag eur" in cols)
    except Exception:
        return False


# ── Hauptfunktion ───────────────────────────────────────────────────
def parse_xlsx(xlsx_path: str) -> tuple[list[Beleg], list[IgnoredPage]]:
    """
    Liest Comdirect-XLSX, sortiert nach Datum, baut FIFO-Inventory auf
    und erzeugt Belege mit korrekten Tranchen für Verkäufe.
    """
    df = pd.read_excel(xlsx_path)
    df.columns = [str(c).strip() for c in df.columns]

    COL_ABR    = "Abrechnungstag"
    COL_AUSF   = "Datum Ausführung"
    COL_WKN    = "WKN"
    COL_ISIN   = "ISIN"
    COL_BEZ    = "Bezeichnung"
    COL_TYP    = "Geschäftsart"
    COL_STUECK = "Stücke/Nom."
    COL_KURS   = "Kurs"
    COL_KW     = "Kurswert EUR"
    COL_KEB    = "Kundenendbetrag EUR"
    COL_ENT    = "Entgelt (Summe eigen und fremd) EUR"
    COL_FTT    = "Transaktionssteuer(n) EUR"
    COL_ORDER  = "Ordernummer"
    COL_DEV    = "Devisenkurs"

    df = df.sort_values(by=COL_ABR).reset_index(drop=True)

    # FIFO-Inventory: dict[isin] → list of (stueck_remaining, ak_pro_stueck)
    inventory: Dict[str, List[Tuple[Decimal, Decimal]]] = {}

    belege: List[Beleg] = []
    ignored: List[IgnoredPage] = []

    for idx, row in df.iterrows():
        isin    = str(row[COL_ISIN]).strip()
        wkn     = str(row[COL_WKN]).strip() if not pd.isna(row[COL_WKN]) else ""
        bez     = str(row[COL_BEZ]).strip() if not pd.isna(row[COL_BEZ]) else f"({wkn})"
        typ_str = str(row[COL_TYP]).strip().upper()
        stueck  = _dec(row[COL_STUECK])
        kurs    = _dec(row[COL_KURS])
        kurswert = _dec(row[COL_KW])
        endbetrag = _dec(row[COL_KEB])
        entgelt  = abs(_dec(row[COL_ENT]))
        ftt_eur  = abs(_dec(row[COL_FTT]))
        order_nr = str(row[COL_ORDER]).strip() if not pd.isna(row[COL_ORDER]) else f"COM{idx:06d}"
        dev_kurs = _dec(row[COL_DEV]) if COL_DEV in df.columns and not pd.isna(row[COL_DEV]) else None
        schlusstag = _parse_date(row[COL_ABR])

        if typ_str == "KAUF":
            abs_kurswert = abs(kurswert)
            abs_endbetrag = abs(endbetrag)

            belege.append(Beleg(
                typ="KAUF",
                seite=idx + 2,
                auftragsnummer=order_nr,
                rechnungsnummer=None,
                datum_dokument=schlusstag,
                schlusstag=schlusstag,
                isin=isin,
                wkn=wkn,
                wertpapierbezeichnung=bez,
                stueck=stueck,
                ausfuehrungskurs=kurs,
                kurswert=abs_kurswert,
                gebuehren_summe=entgelt,
                ausmachender_betrag=abs_endbetrag,
                devisenkurs=dev_kurs,
            ))

            ak_pro_stueck = abs_endbetrag / stueck if stueck > 0 else Decimal("0")
            inventory.setdefault(isin, []).append((stueck, ak_pro_stueck))

        elif typ_str == "VERKAUF":
            tranchen = []
            remaining = stueck
            ak_unvollstaendig = False

            inv_lots = inventory.get(isin, [])
            while remaining > 0 and inv_lots:
                lot_stueck, lot_ak_pst = inv_lots[0]
                if lot_stueck <= remaining:
                    tranchen.append((lot_stueck, lot_ak_pst))
                    remaining -= lot_stueck
                    inv_lots.pop(0)
                else:
                    tranchen.append((remaining, lot_ak_pst))
                    inv_lots[0] = (lot_stueck - remaining, lot_ak_pst)
                    remaining = Decimal("0")

            if remaining > 0:
                ak_unvollstaendig = True
                tranchen.append((remaining, Decimal("0")))

            erloes_brutto = kurswert
            erloes_netto  = endbetrag
            ergebnis_tranchen: List[Tranche] = []
            for tr_stueck, tr_ak_pst in tranchen:
                anteil = tr_stueck / stueck if stueck > 0 else Decimal("0")
                tr_erloes_brutto = (erloes_brutto * anteil).quantize(Decimal("0.01"))
                tr_ak_ges = (tr_ak_pst * tr_stueck).quantize(Decimal("0.01"))
                ist_gewinn = tr_erloes_brutto > tr_ak_ges

                ergebnis_tranchen.append(Tranche(
                    stueck=tr_stueck,
                    ak=tr_ak_ges,
                    erloes_ant=tr_erloes_brutto,
                    ist_gewinn=ist_gewinn,
                ))

            warnings = []
            if ak_unvollstaendig:
                warnings.append(
                    f"#AK-PRÜFEN# {remaining} Stück ohne historische AK "
                    f"(Altbestand vor XLSX-Zeitraum) — AK=0 angesetzt"
                )

            belege.append(Beleg(
                typ="VERKAUF",
                seite=idx + 2,
                auftragsnummer=order_nr,
                rechnungsnummer=None,
                datum_dokument=schlusstag,
                schlusstag=schlusstag,
                isin=isin,
                wkn=wkn,
                wertpapierbezeichnung=bez,
                stueck=stueck,
                ausfuehrungskurs=kurs,
                kurswert=kurswert,
                gebuehren_summe=entgelt,
                ausmachender_betrag=endbetrag,
                tranchen=ergebnis_tranchen,
                ak_unvollstaendig=ak_unvollstaendig,
                warnings=warnings,
                devisenkurs=dev_kurs,
            ))

        else:
            ignored.append(IgnoredPage(
                seite=idx + 2,
                typ="UNBEKANNTER_GESCHAEFTSTYP",
                grund=f"Geschäftsart '{typ_str}' nicht erkannt (erwartet: Kauf/Verkauf)",
            ))
            continue

        if ftt_eur > Decimal("0.01"):
            belege.append(Beleg(
                typ="FTT",
                seite=idx + 2,
                auftragsnummer=order_nr,
                rechnungsnummer=None,
                datum_dokument=schlusstag,
                schlusstag=schlusstag,
                isin=isin,
                wkn=wkn,
                wertpapierbezeichnung=bez,
                stueck=Decimal("0"),
                ausfuehrungskurs=None,
                kurswert=ftt_eur,
                gebuehren_summe=Decimal("0"),
                ausmachender_betrag=ftt_eur,
            ))

    return belege, ignored


# ── Wrapper damit es mit run.py kompatibel ist ─────────────────────
def parse_pdf(path: str):
    """Kompatibilitäts-Alias — Comdirect liefert XLSX, nicht PDF."""
    return parse_xlsx(path)

"""
parser_ibkr.py — Parser für Interactive Brokers Activity Statements (CSV).

Quelldatei: IBKR → Reports & Statements → Statements → Activity, Format CSV,
            Sprache English, Sections: Trades, Dividends, Withholding Tax,
            Fees, Interest, Corporate Actions, Financial Instrument Information.

Besonderheiten gegenüber den anderen Parsern:
  - Multi-Section-Format: jede Zeile beginnt mit dem Section-Namen
  - Pro Section mehrere Header möglich (Stocks / Forex haben andere Spalten)
  - Trades enthalten keine ISIN → Mapping über Financial Instrument Information
    (Spalte "Security ID"); Symbole können Aliase haben ("SSACz, ISAC")
  - IBKR liefert Basis und Realized P/L pro Order → keine eigene FIFO-Rechnung
  - Kein Lot-Detail im Standard-Statement → gemischte Gewinn/Verlust-Verkäufe
    werden netto gebucht und mit #LOT-PRÜFEN# markiert
  - IBKR Ireland ist keine deutsche Abzugsstelle: keine KapESt, kein Soli,
    keine Teilfreistellung → alle Fondsanteile bekommen #TF#
  - Fremdwährung wird über EZB-Referenzkurse (fx_rates.py) in EUR umgerechnet
"""

import csv
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Literal, Dict

from fx_rates import FxRates, FxRateUnavailable


# ── Dataclasses (kompatibel zu den übrigen Parsern) ───────────────────────
@dataclass
class Tranche:
    stueck: Decimal
    ak: Decimal
    erloes_ant: Decimal
    ist_gewinn: bool


@dataclass
class Beleg:
    typ: Literal["KAUF", "VERKAUF", "DIVIDENDE", "FONDSERTRAG",
                 "ZINSGUTSCHRIFT", "ZINSAUFWAND", "GEBUEHR", "FX", "UNBEKANNT"]
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
    # IBKR-spezifisch
    waehrung: str = "EUR"
    devisenkurs: Optional[Decimal] = None
    fx_hinweis: str = ""
    lot_unvollstaendig: bool = False      # → #LOT-PRÜFEN#
    instrument_typ: str = ""              # COMMON / ETF / ADR / FUND
    quellensteuer_eur: Optional[Decimal] = None
    kapitalertragsteuer: Optional[Decimal] = None
    soli: Optional[Decimal] = None
    teilfrei_satz: Optional[Decimal] = None
    teilfrei_betrag: Optional[Decimal] = None


@dataclass
class IgnoredPage:
    seite: int
    typ: str
    grund: str


# ── Helper ────────────────────────────────────────────────────────────────
def _dec(x) -> Decimal:
    """IBKR nutzt US-Format: 1,234.56 → Decimal."""
    if x is None:
        return Decimal("0")
    s = str(x).strip().replace(",", "")
    if not s or s in ("--", "-"):
        return Decimal("0")
    try:
        return Decimal(s)
    except Exception:
        return Decimal("0")


def _parse_dt(s: str) -> Optional[date]:
    """IBKR: '2024-07-05, 09:31:12' oder '2024-07-05'."""
    if not s:
        return None
    s = str(s).strip().split(",")[0].strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


RE_ISIN = re.compile(r"\b([A-Z]{2}[A-Z0-9]{9}\d)\b")


def _isin_aus_text(text: str) -> Optional[str]:
    """Dividenden-Descriptions enthalten die ISIN in Klammern."""
    m = RE_ISIN.search(str(text or ""))
    return m.group(1) if m else None


def is_ibkr_csv(path: str) -> bool:
    """Erkennt IBKR-Statements an der ersten Zeile."""
    try:
        with open(path, encoding="utf-8-sig", errors="ignore") as f:
            head = f.read(4000)
        return ("Statement,Header" in head or "Statement,Data" in head) and \
               ("Interactive Brokers" in head or "BrokerName" in head or
                "Financial Instrument Information" in head or "Trades,Header" in head)
    except Exception:
        return False


# ── Section-Reader ────────────────────────────────────────────────────────
def _read_sections(path: str) -> Dict[str, List[dict]]:
    """
    Liest die CSV in ein Dict {section: [row_dict, ...]}.
    Pro Section können mehrere Header auftreten (Stocks/Forex) —
    jeder Header gilt für die folgenden Data-Zeilen.
    """
    out: Dict[str, List[dict]] = {}
    current_hdr: Dict[str, list] = {}

    with open(path, encoding="utf-8-sig", newline="") as f:
        for raw in csv.reader(f):
            if not raw or len(raw) < 2:
                continue
            section, kind = raw[0], raw[1]

            if kind == "Header":
                current_hdr[section] = raw
                continue
            if kind != "Data":
                continue          # SubTotal / Total / Notes überspringen

            hdr = current_hdr.get(section)
            if not hdr:
                continue
            row = dict(zip(hdr, raw))
            row["_raw"] = raw
            out.setdefault(section, []).append(row)

    return out


def _instrument_map(sections) -> Dict[str, dict]:
    """Symbol → {isin, typ, description}. Aliase werden aufgesplittet."""
    m: Dict[str, dict] = {}
    for r in sections.get("Financial Instrument Information", []):
        isin = (r.get("Security ID") or "").strip()
        typ  = (r.get("Type") or "").strip().upper()
        desc = (r.get("Description") or "").strip()
        for sym in str(r.get("Symbol") or "").split(","):
            sym = sym.strip()
            if sym:
                m[sym] = {"isin": isin, "typ": typ, "description": desc}
    return m


def _ist_fonds(instrument_typ: str) -> bool:
    """ETF/Fonds → Teilfreistellung nach InvStG prüfen."""
    return instrument_typ in ("ETF", "FUND", "CLOSED-END FUND", "MUTUAL FUND")


# ── Hauptfunktion ─────────────────────────────────────────────────────────
def parse_csv(path: str, fx: Optional[FxRates] = None
              ) -> tuple[list[Beleg], list[IgnoredPage]]:
    sections = _read_sections(path)
    instr    = _instrument_map(sections)
    fx       = fx or FxRates()

    belege:  List[Beleg]      = []
    ignored: List[IgnoredPage] = []

    # Zeitraum + Währungen ermitteln, dann EZB-Kurse einmalig vorladen
    alle_daten, alle_whg = [], set()
    for sec in ("Trades", "Dividends", "Withholding Tax", "Fees", "Interest"):
        for r in sections.get(sec, []):
            d = _parse_dt(r.get("Date/Time") or r.get("Date") or "")
            if d:
                alle_daten.append(d)
            w = (r.get("Currency") or "").strip().upper()
            if w and w not in ("EUR", "TOTAL", "BASE CURRENCY SUMMARY"):
                alle_whg.add(w)
    if alle_daten:
        von, bis = min(alle_daten), max(alle_daten)
        for w in alle_whg:
            try:
                fx.ensure_range(w, von, bis)
            except Exception as e:
                ignored.append(IgnoredPage(0, "FX",
                    f"EZB-Kurse für {w} nicht abrufbar: {e}"))

    belege += _parse_trades(sections, instr, fx, ignored)
    belege += _parse_dividends(sections, instr, fx, ignored)
    belege += _parse_interest(sections, fx, ignored)
    belege += _parse_fees(sections, fx, ignored)

    for sec in ("Corporate Actions",):
        for i, r in enumerate(sections.get(sec, [])):
            ignored.append(IgnoredPage(
                seite=i + 1, typ="CORPORATE_ACTION",
                grund=f"{(r.get('Description') or '')[:110]} — manuell zu beurteilen"))

    return belege, ignored


# ── Trades ────────────────────────────────────────────────────────────────
def _parse_trades(sections, instr, fx, ignored) -> List[Beleg]:
    belege = []
    for i, r in enumerate(sections.get("Trades", [])):
        if (r.get("DataDiscriminator") or "").strip() != "Order":
            continue

        asset = (r.get("Asset Category") or "").strip()
        whg   = (r.get("Currency") or "EUR").strip().upper()
        sym   = (r.get("Symbol") or "").strip()
        tag   = _parse_dt(r.get("Date/Time"))
        qty   = _dec(r.get("Quantity"))

        if asset == "Forex":
            ignored.append(IgnoredPage(
                seite=i + 1, typ="FOREX",
                grund=f"Devisenumwandlung {sym} {qty} — Buchung abhängig von "
                      f"Fremdwährungskonto-Entscheidung"))
            continue

        if asset != "Stocks" or tag is None or qty == 0:
            ignored.append(IgnoredPage(
                seite=i + 1, typ=f"TRADE_{asset.upper() or 'UNBEKANNT'}",
                grund=f"Assetklasse '{asset}' wird nicht automatisch gebucht"))
            continue

        info  = instr.get(sym, {})
        isin  = info.get("isin", "")
        ityp  = info.get("typ", "")
        bez   = info.get("description", sym)

        proceeds = _dec(r.get("Proceeds"))       # Verkauf positiv, Kauf negativ
        comm     = abs(_dec(r.get("Comm/Fee")))
        basis    = _dec(r.get("Basis"))
        realized = _dec(r.get("Realized P/L"))
        kurs     = _dec(r.get("T. Price"))

        # → EUR umrechnen
        warn, fx_hinweis, devkurs = [], "", None
        try:
            if whg != "EUR":
                devkurs, _ = fx.get_rate(whg, tag)
                fx_hinweis = fx.rate_info(whg, tag)
            # ruft to_eur, das seinerseits get_rate nutzt
            proceeds_e = fx.to_eur(proceeds, whg, tag)
            comm_e     = fx.to_eur(comm,     whg, tag)
            basis_e    = fx.to_eur(basis,    whg, tag)
            realized_e = fx.to_eur(realized, whg, tag)
            kurs_e     = fx.to_eur(kurs,     whg, tag) if kurs else None
        except FxRateUnavailable as e:
            warn.append(f"FX-Umrechnung fehlgeschlagen: {e}")
            proceeds_e, comm_e, basis_e, realized_e, kurs_e = (
                proceeds, comm, basis, realized, kurs or None)

        if _ist_fonds(ityp):
            warn.append("Fondsanteil — Teilfreistellung nach InvStG prüfen "
                        "(IBKR liefert keinen TF-Satz)")

        if qty > 0:
            # ── Kauf ────────────────────────────────────────────────────
            belege.append(Beleg(
                typ="KAUF", seite=i + 1, auftragsnummer=f"IB{i+1:05d}",
                rechnungsnummer=None, datum_dokument=tag, schlusstag=tag,
                isin=isin, wkn=None, wertpapierbezeichnung=bez,
                stueck=qty, ausfuehrungskurs=kurs_e,
                kurswert=abs(proceeds_e), gebuehren_summe=comm_e,
                ausmachender_betrag=abs(proceeds_e) + comm_e,
                waehrung=whg, devisenkurs=devkurs, fx_hinweis=fx_hinweis,
                instrument_typ=ityp, teilfreistellung=_ist_fonds(ityp),
                warnings=warn,
            ))
            continue

        # ── Verkauf ─────────────────────────────────────────────────────
        stueck = abs(qty)
        ak     = abs(basis_e)
        # Nur Order-Ebene verfügbar → eine Netto-Tranche, Marker setzen
        tranchen = [Tranche(stueck=stueck, ak=ak,
                            erloes_ant=proceeds_e, ist_gewinn=realized_e > 0)]
        warn.append("#LOT-PRÜFEN# Nur Order-Ebene im Statement — bei Verkäufen "
                    "aus mehreren Tranchen ist keine Aufteilung in Gewinn- und "
                    "Verlustanteile möglich")

        # Plausibilität: Proceeds − Comm − |Basis| = Realized P/L
        diff = abs((proceeds_e - comm_e - ak) - realized_e)
        ok   = diff <= Decimal("0.05")
        if not ok:
            warn.append(f"Abweichung Realized P/L: erwartet "
                        f"{proceeds_e - comm_e - ak}, ist {realized_e} (Δ {diff})")

        belege.append(Beleg(
            typ="VERKAUF", seite=i + 1, auftragsnummer=f"IB{i+1:05d}",
            rechnungsnummer=None, datum_dokument=tag, schlusstag=tag,
            isin=isin, wkn=None, wertpapierbezeichnung=bez,
            stueck=stueck, ausfuehrungskurs=kurs_e,
            kurswert=proceeds_e, gebuehren_summe=comm_e,
            ausmachender_betrag=proceeds_e - comm_e,
            tranchen=tranchen, lot_unvollstaendig=True,
            waehrung=whg, devisenkurs=devkurs, fx_hinweis=fx_hinweis,
            instrument_typ=ityp, teilfreistellung=_ist_fonds(ityp),
            plausi_ok=ok, plausi_diff=diff, warnings=warn,
        ))

    return belege


# ── Dividenden + Quellensteuer ────────────────────────────────────────────
def _parse_dividends(sections, instr, fx, ignored) -> List[Beleg]:
    # Quellensteuer nach (isin, datum) indexieren; Beträge sind negativ
    qst: Dict[tuple, Decimal] = {}
    for r in sections.get("Withholding Tax", []):
        tag  = _parse_dt(r.get("Date"))
        isin = _isin_aus_text(r.get("Description"))
        whg  = (r.get("Currency") or "EUR").strip().upper()
        if not tag or not isin or whg in ("TOTAL",):
            continue
        try:
            betrag = fx.to_eur(abs(_dec(r.get("Amount"))), whg, tag)
        except FxRateUnavailable:
            betrag = abs(_dec(r.get("Amount")))
        qst[(isin, tag)] = qst.get((isin, tag), Decimal("0")) + betrag

    belege = []
    isin_typ = {v["isin"]: v["typ"] for v in instr.values() if v.get("isin")}
    isin_bez = {v["isin"]: v["description"] for v in instr.values() if v.get("isin")}

    for i, r in enumerate(sections.get("Dividends", [])):
        whg  = (r.get("Currency") or "EUR").strip().upper()
        if whg in ("TOTAL",) or whg.startswith("BASE"):
            continue
        tag  = _parse_dt(r.get("Date"))
        desc = r.get("Description") or ""
        isin = _isin_aus_text(desc)
        if not tag or not isin:
            ignored.append(IgnoredPage(i + 1, "DIVIDENDE",
                                       f"ISIN/Datum nicht erkennbar: {desc[:80]}"))
            continue

        warn, fx_hinweis, devkurs = [], "", None
        try:
            if whg != "EUR":
                devkurs, _ = fx.get_rate(whg, tag)
                fx_hinweis = fx.rate_info(whg, tag)
            netto_e = fx.to_eur(_dec(r.get("Amount")), whg, tag)
        except FxRateUnavailable as e:
            warn.append(f"FX-Umrechnung fehlgeschlagen: {e}")
            netto_e = _dec(r.get("Amount"))

        quellenst = qst.get((isin, tag), Decimal("0"))
        ityp      = isin_typ.get(isin, "")
        bez       = isin_bez.get(isin, desc[:40])
        fonds     = _ist_fonds(ityp)

        warn.append("IBKR ist keine deutsche Abzugsstelle — keine KapESt/Soli "
                    "einbehalten, §8b bzw. InvStG-Einordnung erforderlich")
        if fonds:
            warn.append("Fondsausschüttung — Teilfreistellungssatz für GmbH prüfen")

        belege.append(Beleg(
            typ="FONDSERTRAG" if fonds else "DIVIDENDE",
            seite=i + 1, auftragsnummer=f"IBDIV{i+1:04d}",
            rechnungsnummer=None, datum_dokument=tag, schlusstag=tag,
            isin=isin, wkn=None, wertpapierbezeichnung=bez,
            stueck=Decimal("0"), ausfuehrungskurs=None,
            kurswert=netto_e + quellenst,
            gebuehren_summe=Decimal("0"), ausmachender_betrag=netto_e,
            quellensteuer_eur=quellenst or None,
            kapitalertragsteuer=Decimal("0"), soli=Decimal("0"),
            waehrung=whg, devisenkurs=devkurs, fx_hinweis=fx_hinweis,
            instrument_typ=ityp, teilfreistellung=fonds, warnings=warn,
        ))

    return belege


# ── Zinsen ────────────────────────────────────────────────────────────────
def _parse_interest(sections, fx, ignored) -> List[Beleg]:
    belege = []
    for i, r in enumerate(sections.get("Interest", [])):
        whg = (r.get("Currency") or "EUR").strip().upper()
        if whg in ("TOTAL",) or whg.startswith("BASE"):
            continue
        tag = _parse_dt(r.get("Date"))
        if not tag:
            continue
        betrag = _dec(r.get("Amount"))
        try:
            betrag_e = fx.to_eur(abs(betrag), whg, tag)
            fx_hinweis = fx.rate_info(whg, tag) if whg != "EUR" else ""
        except FxRateUnavailable:
            betrag_e, fx_hinweis = abs(betrag), ""

        belege.append(Beleg(
            typ="ZINSGUTSCHRIFT" if betrag > 0 else "ZINSAUFWAND",
            seite=i + 1, auftragsnummer=f"IBINT{i+1:04d}",
            rechnungsnummer=None, datum_dokument=tag, schlusstag=tag,
            isin="", wkn=None,
            wertpapierbezeichnung=(r.get("Description") or "Zinsen")[:40],
            stueck=Decimal("0"), ausfuehrungskurs=None,
            kurswert=betrag_e, gebuehren_summe=Decimal("0"),
            ausmachender_betrag=betrag_e,
            waehrung=whg, fx_hinweis=fx_hinweis,
        ))
    return belege


# ── Gebühren ──────────────────────────────────────────────────────────────
def _parse_fees(sections, fx, ignored) -> List[Beleg]:
    belege = []
    for i, r in enumerate(sections.get("Fees", [])):
        whg = (r.get("Currency") or "EUR").strip().upper()
        if whg in ("TOTAL",) or whg.startswith("BASE"):
            continue
        tag = _parse_dt(r.get("Date"))
        betrag = _dec(r.get("Amount"))
        if not tag or betrag == 0:
            continue
        try:
            betrag_e = fx.to_eur(abs(betrag), whg, tag)
        except FxRateUnavailable:
            betrag_e = abs(betrag)

        belege.append(Beleg(
            typ="GEBUEHR", seite=i + 1, auftragsnummer=f"IBFEE{i+1:04d}",
            rechnungsnummer=None, datum_dokument=tag, schlusstag=tag,
            isin="", wkn=None,
            wertpapierbezeichnung=(r.get("Description") or "Gebuehr")[:40],
            stueck=Decimal("0"), ausfuehrungskurs=None,
            kurswert=betrag_e, gebuehren_summe=Decimal("0"),
            ausmachender_betrag=betrag_e, waehrung=whg,
        ))
    return belege


# ── Alias für run.py ──────────────────────────────────────────────────────
def parse_pdf(path: str):
    return parse_csv(path)

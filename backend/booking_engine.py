"""
booking_engine.py — Buchwertabgang-Methode nach DATEV-Dokument 5300857.

KAUF  (1 Buchung):
  1510 an 1801 = Ausmachender Betrag (Kurswert + alle Gebühren aktiviert)

VERKAUF pro Tranche (3 Buchungen):
  Bei GEWINN:
    1801 an 4906  = anteiliger Brutto-Erlös
    6857 an 1801  = anteilige Provision
    4904 an 1510  = Buchwert / AK der Tranche

  Bei VERLUST:
    1801 an 6906  = anteiliger Brutto-Erlös
    6858 an 1801  = anteilige Provision
    6904 an 1510  = Buchwert / AK der Tranche

Teilfreistellung: kein extra Buchungssatz — nur " [Teilfreistellung]" im Text.

Mischabrechnung: Pro Tranche getrennt, Provision proportional aufgeteilt.
"""
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from typing import List, Optional

from parser import Beleg, Tranche


TWO  = Decimal("0.01")


@dataclass
class Buchung:
    umsatz: Decimal
    soll_haben: str        # "S" = Soll, "H" = Haben
    konto: str
    gegenkonto: str
    belegdatum: date
    belegfeld_1: str
    belegfeld_2: str = ""
    buchungstext: str = ""
    isin: str = ""
    wkn: str = ""
    stueck: Decimal = Decimal("0")
    kurs: Decimal = Decimal("0")
    kategorie: str = ""
    quell_seite: int = 0


def _kuerzen(s: str, n: int) -> str:
    return s if len(s) <= n else s[:n-1].rstrip() + "…"


def _fmt_stueck(d: Decimal) -> str:
    if d == d.to_integral_value():
        return str(int(d))
    return str(d)


def _round2(d: Decimal) -> Decimal:
    return d.quantize(TWO, rounding=ROUND_HALF_UP)


def _fallback_tranchen(b: Beleg) -> List[Tranche]:
    """Berechnet AK aus Seite-1-Daten wenn keine Seite-2-Tranchen vorhanden."""
    b.plausi_ok = False
    b.warnings.append("Tranchendaten fehlen — Buchung mit AK=0 erstellt, MANUELL KORRIGIEREN!")
    return [Tranche(stueck=b.stueck, ak=Decimal("0"), erloes_ant=b.ausmachender_betrag, ist_gewinn=True)]


def belege_zu_buchungen(belege: List[Beleg], config: dict) -> List[Buchung]:
    buchungen: List[Buchung] = []
    K  = config["konten"]
    T  = config["buchungstexte"]
    OPT= config.get("options", {})
    bez_max = OPT.get("kuerze_bezeichnung_auf", 30)

    konto_bank   = K["bank"]["nr"]
    konto_wp     = K["wertpapiere_uv"]["nr"]

    for b in belege:
        bez = _kuerzen(b.wertpapierbezeichnung, bez_max)
        ak_marker = "#AK-PRÜFEN# " if getattr(b, "ak_unvollstaendig", False) else ""
        teilfrei_str = ak_marker + ("#TF# " if b.teilfreistellung else "")
        ctx = dict(anzahl=_fmt_stueck(b.stueck), bezeichnung=bez,
                   isin=b.isin, auftragsnr=b.auftragsnummer, teilfrei=teilfrei_str)

        if b.typ == "KAUF":
            buchungen.append(Buchung(
                umsatz=b.ausmachender_betrag,
                soll_haben="S",
                konto=konto_wp,
                gegenkonto=konto_bank,
                belegdatum=b.schlusstag,
                belegfeld_1=b.auftragsnummer,
                belegfeld_2=b.rechnungsnummer or "",
                buchungstext=T["kauf"].format(**ctx)[:60],
                isin=b.isin, wkn=b.wkn or "",
                stueck=b.stueck, kurs=b.ausfuehrungskurs or Decimal("0"),
                kategorie="Kurswert+Gebühren",
                quell_seite=b.seite,
            ))

        elif b.typ == "VERKAUF":
            tranchen = b.tranchen if b.tranchen else _fallback_tranchen(b)

            summe_erloes = sum(t.erloes_ant for t in tranchen)
            prov_ges = b.gebuehren_summe

            for t in tranchen:
                ist_gewinn = t.ist_gewinn

                if summe_erloes > 0:
                    prov_ant = _round2(prov_ges * t.erloes_ant / summe_erloes)
                else:
                    prov_ant = _round2(prov_ges / len(tranchen))

                brutto_erloes = _round2(t.erloes_ant + prov_ant)

                konto_erloes  = K["erloese_gewinn"]["nr"]  if ist_gewinn else K["verluste_erloes"]["nr"]
                konto_abgang  = K["abgang_gewinn"]["nr"]   if ist_gewinn else K["abgang_verlust"]["nr"]
                konto_prov    = K["gebuehren_vk_gewinn"]["nr"] if ist_gewinn else K["gebuehren_vk_verlust"]["nr"]

                buchungen.append(Buchung(
                    umsatz=brutto_erloes,
                    soll_haben="S",
                    konto=konto_bank,
                    gegenkonto=konto_erloes,
                    belegdatum=b.schlusstag,
                    belegfeld_1=b.auftragsnummer,
                    belegfeld_2=b.rechnungsnummer or "",
                    buchungstext=T["verkauf_erloes"].format(**ctx)[:60],
                    isin=b.isin, wkn=b.wkn or "",
                    stueck=t.stueck, kurs=b.ausfuehrungskurs or Decimal("0"),
                    kategorie="Erlös" + (" (Gewinn)" if ist_gewinn else " (Verlust)"),
                    quell_seite=b.seite,
                ))

                if prov_ant > 0:
                    buchungen.append(Buchung(
                        umsatz=prov_ant,
                        soll_haben="S",
                        konto=konto_prov,
                        gegenkonto=konto_bank,
                        belegdatum=b.schlusstag,
                        belegfeld_1=b.auftragsnummer,
                        belegfeld_2=b.rechnungsnummer or "",
                        buchungstext=T["verkauf_gebuehren"].format(**ctx)[:60],
                        isin=b.isin, wkn=b.wkn or "",
                        stueck=t.stueck,
                        kategorie="Gebühren" + (" (6857)" if ist_gewinn else " (6858)"),
                        quell_seite=b.seite,
                    ))

                if t.ak > 0:
                    buchungen.append(Buchung(
                        umsatz=t.ak,
                        soll_haben="S",
                        konto=konto_abgang,
                        gegenkonto=konto_wp,
                        belegdatum=b.schlusstag,
                        belegfeld_1=b.auftragsnummer,
                        belegfeld_2=b.rechnungsnummer or "",
                        buchungstext=T["verkauf_abgang"].format(**ctx)[:60],
                        isin=b.isin, wkn=b.wkn or "",
                        stueck=t.stueck,
                        kategorie="Buchwertabgang" + (" (4904)" if ist_gewinn else " (6904)"),
                        quell_seite=b.seite,
                    ))

    return buchungen


# ─────────────────────────────────────────────────────────────────────────────
# Flatex-Erweiterung: DIVIDENDE + FONDSERTRAG
# ─────────────────────────────────────────────────────────────────────────────

def _buchungen_dividende(b, config: dict) -> List[Buchung]:
    """
    SKR04-Buchungen für ausländische Dividenden.
    Marker #DIV# signalisiert dem Steuerberater: §8b-Einordnung prüfen.

    1801 Soll – 7700 Haben : Endbetrag (Nettodividende)
    1780 Soll – 7700 Haben : Quellensteuer EUR (anrechenbar)
    """
    K = config["konten"]
    opts = config.get("options", {})
    bez = _kuerzen(b.wertpapierbezeichnung, opts.get("kuerze_bezeichnung_auf", 30))

    endbetrag  = b.ausmachender_betrag
    quellenst  = getattr(b, "quellensteuer_eur", None) or Decimal("0")
    buchungen: List[Buchung] = []

    buchungen.append(Buchung(
        umsatz        = endbetrag,
        soll_haben    = "S",
        konto         = K["bank"]["nr"],
        gegenkonto    = "7700",
        belegdatum    = b.schlusstag,
        belegfeld_1   = b.auftragsnummer,
        belegfeld_2   = "",
        buchungstext  = f"#DIV# Dividende {bez} ({b.isin})"[:60],
        isin          = b.isin,
        wkn           = b.wkn or "",
        stueck        = b.stueck,
        kategorie     = "Dividende Bank",
        quell_seite   = b.seite,
    ))

    if quellenst > Decimal("0"):
        buchungen.append(Buchung(
            umsatz        = quellenst,
            soll_haben    = "S",
            konto         = "1780",
            gegenkonto    = "7700",
            belegdatum    = b.schlusstag,
            belegfeld_1   = b.auftragsnummer,
            belegfeld_2   = "",
            buchungstext  = f"#DIV# Quellensteuer {b.isin}"[:60],
            isin          = b.isin,
            wkn           = b.wkn or "",
            stueck        = Decimal("0"),
            kategorie     = "Dividende Quellensteuer",
            quell_seite   = b.seite,
        ))

    return buchungen


def _buchungen_fondsertrag(b, config: dict) -> List[Buchung]:
    """
    SKR04-Buchungen für Fonds-Ausschüttungen.
    Marker #FONDS# + TF-Satz signalisiert Steuerberater: ggf. auf 80% (GmbH, Aktienfonds) korrigieren.

    1801 Soll – 7810 Haben : Endbetrag (nach Steuerabzug)
    1780 Soll – 7810 Haben : KapESt + Soli (einbehalten, anrechenbar)
    """
    K = config["konten"]
    opts = config.get("options", {})
    bez = _kuerzen(b.wertpapierbezeichnung, opts.get("kuerze_bezeichnung_auf", 30))

    endbetrag   = b.ausmachender_betrag
    kapest      = getattr(b, "kapitalertragsteuer", None) or Decimal("0")
    soli        = getattr(b, "soli", None) or Decimal("0")
    steuer_ges  = kapest + soli
    tf_satz     = getattr(b, "teilfrei_satz", None)
    tf_hinweis  = f" TF={tf_satz}%" if tf_satz else ""

    buchungen: List[Buchung] = []

    buchungen.append(Buchung(
        umsatz        = endbetrag,
        soll_haben    = "S",
        konto         = K["bank"]["nr"],
        gegenkonto    = "7810",
        belegdatum    = b.schlusstag,
        belegfeld_1   = b.auftragsnummer,
        belegfeld_2   = "",
        buchungstext  = f"#FONDS# Ausschuettung {bez} ({b.isin}){tf_hinweis}"[:60],
        isin          = b.isin,
        wkn           = b.wkn or "",
        stueck        = b.stueck,
        kategorie     = f"Fondsertrag{tf_hinweis}",
        quell_seite   = b.seite,
    ))

    if steuer_ges > Decimal("0"):
        buchungen.append(Buchung(
            umsatz        = steuer_ges,
            soll_haben    = "S",
            konto         = "1780",
            gegenkonto    = "7810",
            belegdatum    = b.schlusstag,
            belegfeld_1   = b.auftragsnummer,
            belegfeld_2   = "",
            buchungstext  = f"#FONDS# KapESt+Soli {b.isin}"[:60],
            isin          = b.isin,
            wkn           = b.wkn or "",
            stueck        = Decimal("0"),
            kategorie     = "Fondsertrag Steuer",
            quell_seite   = b.seite,
        ))

    return buchungen


def belege_zu_buchungen_alle_typen(belege: list, config: dict) -> List[Buchung]:
    """
    Erweiterter Dispatcher für alle Belegtypen.
    KAUF/VERKAUF → bestehende Engine
    DIVIDENDE    → _buchungen_dividende
    FONDSERTRAG  → _buchungen_fondsertrag
    """
    alle: List[Buchung] = []
    kauf_vk = [b for b in belege if b.typ in ("KAUF", "VERKAUF")]
    if kauf_vk:
        alle.extend(belege_zu_buchungen(kauf_vk, config))
    for b in belege:
        if b.typ == "DIVIDENDE":
            alle.extend(_buchungen_dividende(b, config))
        elif b.typ == "FONDSERTRAG":
            alle.extend(_buchungen_fondsertrag(b, config))
    return alle


# ─────────────────────────────────────────────────────────────────────────────
# Erweiterung Runde 2: Verwahrentgelt, Zinsgutschrift, Finanztransaktionssteuer
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class UngebuchterBeleg:
    """
    Erkannter Vorgang der NICHT automatisch gebucht wurde.
    Erscheint im Protokoll mit Buchungsempfehlung für den Steuerberater.
    """
    typ: str
    datum: date
    betrag: Decimal
    grund: str
    empfehlung: str = ""
    isin: str = ""
    bezeichnung: str = ""
    rohtext: str = ""


def _buchungen_verwahrentgelt(b, config: dict) -> List[Buchung]:
    """SKR04: 6860 (Nebenkosten Geldverkehr) an 1801 (Bank)."""
    K = config["konten"]
    bez = _kuerzen(b.wertpapierbezeichnung or "Verwahrentgelt", 30)
    return [Buchung(
        umsatz=b.ausmachender_betrag, soll_haben="S",
        konto="6860", gegenkonto=K["bank"]["nr"],
        belegdatum=b.schlusstag, belegfeld_1=b.auftragsnummer, belegfeld_2="",
        buchungstext=f"Verwahrentgelt {bez}"[:60],
        isin=b.isin or "", wkn=b.wkn or "",
        stueck=b.stueck or Decimal("0"),
        kategorie="Verwahrentgelt", quell_seite=b.seite,
    )]


def _buchungen_zinsgutschrift(b, config: dict) -> List[Buchung]:
    """SKR04: 1801 (Bank) an 7100 (Zinserträge); +1780 für KapESt/Soli."""
    K = config["konten"]
    bez = _kuerzen(b.wertpapierbezeichnung, 30)
    kapest = getattr(b, "kapitalertragsteuer", None) or Decimal("0")
    soli = getattr(b, "soli", None) or Decimal("0")
    steuer_ges = kapest + soli

    buchungen = [Buchung(
        umsatz=b.ausmachender_betrag, soll_haben="S",
        konto=K["bank"]["nr"], gegenkonto="7100",
        belegdatum=b.schlusstag, belegfeld_1=b.auftragsnummer, belegfeld_2="",
        buchungstext=f"Zinsgutschrift {bez} ({b.isin})"[:60],
        isin=b.isin, wkn=b.wkn or "", stueck=b.stueck,
        kategorie="Zinsgutschrift", quell_seite=b.seite,
    )]
    if steuer_ges > Decimal("0"):
        buchungen.append(Buchung(
            umsatz=steuer_ges, soll_haben="S",
            konto="1780", gegenkonto="7100",
            belegdatum=b.schlusstag, belegfeld_1=b.auftragsnummer, belegfeld_2="",
            buchungstext=f"KapESt+Soli Zins {b.isin}"[:60],
            isin=b.isin, wkn=b.wkn or "", stueck=Decimal("0"),
            kategorie="Zinsgutschrift Steuer", quell_seite=b.seite,
        ))
    return buchungen


def _buchungen_ftt(b, config: dict) -> List[Buchung]:
    """SKR04: 6305 (Sonstige Steuern) an 1801 (Bank) — Finanztransaktionssteuer."""
    K = config["konten"]
    bez = _kuerzen(b.wertpapierbezeichnung, 30)
    return [Buchung(
        umsatz=b.ausmachender_betrag, soll_haben="S",
        konto="6305", gegenkonto=K["bank"]["nr"],
        belegdatum=b.schlusstag, belegfeld_1=b.auftragsnummer, belegfeld_2="",
        buchungstext=f"FTT {bez} ({b.isin})"[:60],
        isin=b.isin or "", wkn=b.wkn or "", stueck=Decimal("0"),
        kategorie="Finanztransaktionssteuer", quell_seite=b.seite,
    )]


def belege_zu_buchungen_v2(belege, config):
    """Voller Dispatcher inkl. aller Typen. Returns (buchungen, ungebucht_liste)."""
    alle, ungebucht = [], []
    kauf_vk = [b for b in belege if b.typ in ("KAUF", "VERKAUF")]
    if kauf_vk:
        alle.extend(belege_zu_buchungen(kauf_vk, config))

    for b in belege:
        if b.typ in ("KAUF", "VERKAUF"):
            continue
        if b.typ == "DIVIDENDE":
            alle.extend(_buchungen_dividende(b, config))
        elif b.typ == "FONDSERTRAG":
            alle.extend(_buchungen_fondsertrag(b, config))
        elif b.typ == "VERWAHRENTGELT":
            alle.extend(_buchungen_verwahrentgelt(b, config))
        elif b.typ == "ZINSGUTSCHRIFT":
            alle.extend(_buchungen_zinsgutschrift(b, config))
        elif b.typ == "FTT":
            alle.extend(_buchungen_ftt(b, config))
        else:
            ungebucht.append(UngebuchterBeleg(
                typ=b.typ, datum=b.schlusstag, betrag=b.ausmachender_betrag,
                grund=f"Belegtyp '{b.typ}' wird nicht automatisch gebucht",
                empfehlung="Manuelle Prüfung durch Steuerberater erforderlich",
                isin=b.isin or "", bezeichnung=b.wertpapierbezeichnung or "",
            ))
    return alle, ungebucht

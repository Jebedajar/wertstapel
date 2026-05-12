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
    # Für Simple-Fälle (1 Tranche)
    # AK = Ausmachender Betrag ∓ Veräußerungsgewinn/-verlust
    # aber wir haben dieses Info auf Seite 1 nur als Gesamtwert.
    # Hier wird vereinfacht: gesamter Erlös = Ausmachender Betrag (netto nach Provision)
    # Gewinn/Verlust nicht bekannt ohne Seite 2 → Warnung bereits gesetzt.
    # Wir liefern EINE Tranche mit AK=0, damit der Buchungssatz erstellt werden kann,
    # aber als Plausi-Warnung.
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
        teilfrei_str = " [Teilfreistellung]" if b.teilfreistellung else ""
        ctx = dict(anzahl=_fmt_stueck(b.stueck), bezeichnung=bez,
                   isin=b.isin, auftragsnr=b.auftragsnummer, teilfrei=teilfrei_str)

        if b.typ == "KAUF":
            # ─── KAUF: 1 Buchung, Ausmachender Betrag auf 1510 ───────────────
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
            # ─── VERKAUF: Pro Tranche 3 Buchungen ────────────────────────────
            tranchen = b.tranchen if b.tranchen else _fallback_tranchen(b)

            # Ausmachender Betrag = Summe der Netto-Erlöse der Tranchen
            summe_erloes = sum(t.erloes_ant for t in tranchen)
            # Provision gesamt
            prov_ges = b.gebuehren_summe

            for t in tranchen:
                ist_gewinn = t.ist_gewinn

                # Proportionale Provision
                if summe_erloes > 0:
                    prov_ant = _round2(prov_ges * t.erloes_ant / summe_erloes)
                else:
                    prov_ant = _round2(prov_ges / len(tranchen))

                # Brutto-Erlös der Tranche = netto + anteilige Provision
                brutto_erloes = _round2(t.erloes_ant + prov_ant)

                # Konten je nach Gewinn/Verlust
                konto_erloes  = K["erloese_gewinn"]["nr"]  if ist_gewinn else K["verluste_erloes"]["nr"]
                konto_abgang  = K["abgang_gewinn"]["nr"]   if ist_gewinn else K["abgang_verlust"]["nr"]
                konto_prov    = K["gebuehren_vk_gewinn"]["nr"] if ist_gewinn else K["gebuehren_vk_verlust"]["nr"]

                # Buchung 1: Bank an Erlöskonto = Brutto-Erlös
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

                # Buchung 2: Provisionskonto an Bank = anteilige Provision
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

                # Buchung 3: Abgangskonto an WP = Buchwert
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

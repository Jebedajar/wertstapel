"""
modelle.py — Einheitliches Datenmodell für alle Parser und die Buchungsengine.

Bisher definierte jeder Parser eigene Dataclasses `Beleg` und `Tranche`, und
`run.get_parser` patchte zur Laufzeit `sparkasse_parser.Beleg = p.Beleg`, weil
`booking_engine` mit `from parser import Beleg` importierte. Das entfällt.

Die Parser dürfen ihre eigenen Dataclasses vorerst behalten — `normalisiere()`
liest sie über getattr und ergänzt die neuen Felder. So lässt sich der Umbau
schrittweise machen, ohne alle sechs Parser gleichzeitig anzufassen.

Neu gegenüber allen Vorgängerständen:
  - klasse           Instrumentenklasse (aktie | fonds | anleihe | derivat_verbrieft)
  - fondskategorie   bei Fonds die Kategorie für die Teilfreistellung
  - depot_index      1-basiert, ersetzt die Kontovergabe der DepotRegistry
  - marker           Liste, wird erst nach der Buchungserzeugung injiziert
  - buchwert         von bewertung.py gesetzter Abgangswert
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Any

TWO = Decimal("0.01")


def round2(d: Decimal) -> Decimal:
    return Decimal(d).quantize(TWO, rounding=ROUND_HALF_UP)


def kuerzen(s: str, n: int) -> str:
    s = s or ""
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def fmt_stueck(d: Decimal) -> str:
    d = Decimal(d or 0)
    return str(int(d)) if d == d.to_integral_value() else str(d)


# ───────────────────────────────────────────────────────────────────────────
# Buchung — bisher in booking_engine.py definiert.
# datev_writer.py muss seinen Import auf `from modelle import Buchung` ändern.
# ───────────────────────────────────────────────────────────────────────────
@dataclass
class Buchung:
    umsatz: Decimal
    soll_haben: str            # "S" = Soll, "H" = Haben
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
    stapel: str = "handelsrecht"    # "handelsrecht" | "steuerrecht"


@dataclass
class Tranche:
    stueck: Decimal
    ak: Decimal
    erloes_ant: Decimal
    ist_gewinn: bool


@dataclass
class UngebuchterBeleg:
    """Erkannter, aber bewusst nicht gebuchter Vorgang. Kein stiller Fehler."""
    typ: str
    datum: Optional[date] = None
    betrag: Optional[Decimal] = None
    grund: str = ""
    empfehlung: str = ""
    isin: str = ""
    bezeichnung: str = ""
    depot: Optional[str] = None
    seite: int = 0


@dataclass
class Vorabpauschale:
    """Fiktiver Ertrag nach § 18 InvStG. Wird im Steuerstapel gebucht."""
    isin: str
    bezeichnung: str
    jahr: int
    betrag: Decimal
    steuer: Decimal = Decimal("0")
    datum: Optional[date] = None
    depot: Optional[str] = None
    kategorie: Optional[str] = None


@dataclass
class NormBeleg:
    """Vereinheitlichter Beleg. Hält eine Referenz auf das Original,
    damit parserspezifische Zusatzfelder erreichbar bleiben."""
    quelle: Any                       # der ursprüngliche Beleg des Parsers
    typ: str
    seite: int
    auftragsnummer: str
    rechnungsnummer: Optional[str]
    schlusstag: date
    isin: str
    wkn: str
    bezeichnung: str
    stueck: Decimal
    ausfuehrungskurs: Optional[Decimal]
    kurswert: Decimal
    gebuehren_summe: Decimal
    ausmachender_betrag: Decimal
    tranchen: List[Tranche] = field(default_factory=list)

    # Steuern und Erträge
    kapitalertragsteuer: Decimal = Decimal("0")
    soli: Decimal = Decimal("0")
    quellensteuer_eur: Decimal = Decimal("0")
    teilfrei_satz: Optional[Decimal] = None
    stueckzinsen: Decimal = Decimal("0")

    # Neu
    klasse: Optional[str] = None
    fondskategorie: Optional[str] = None
    depot_index: int = 1
    depot_name: Optional[str] = None
    marker: List[str] = field(default_factory=list)
    buchwert: Optional[Decimal] = None
    buchwert_unvollstaendig: bool = False
    warnings: List[str] = field(default_factory=list)
    waehrung: str = "EUR"

    @property
    def ist_gewinn(self) -> bool:
        if self.buchwert is None:
            return True
        return self.erloes_brutto > self.buchwert

    @property
    def erloes_brutto(self) -> Decimal:
        """Verkaufserlös vor Abzug der Veräußerungskosten."""
        return self.kurswert if self.kurswert else self.ausmachender_betrag + self.gebuehren_summe

    @property
    def ergebnis(self) -> Decimal:
        """Abgangsergebnis vor Kosten. Nur sinnvoll bei Verkäufen."""
        return round2(self.erloes_brutto - (self.buchwert or Decimal("0")))


def _d(wert, vorgabe="0") -> Decimal:
    if wert is None:
        return Decimal(vorgabe)
    return Decimal(str(wert))


def normalisiere(beleg: Any, depot_index: int = 1) -> NormBeleg:
    """Übersetzt einen beliebigen Parser-Beleg in das einheitliche Modell."""
    g = lambda name, vorgabe=None: getattr(beleg, name, vorgabe)

    tranchen = []
    for t in (g("tranchen", []) or []):
        tranchen.append(Tranche(
            stueck=_d(getattr(t, "stueck", 0)),
            ak=_d(getattr(t, "ak", 0)),
            erloes_ant=_d(getattr(t, "erloes_ant", 0)),
            ist_gewinn=bool(getattr(t, "ist_gewinn", True)),
        ))

    nb = NormBeleg(
        quelle=beleg,
        typ=g("typ", "UNBEKANNT"),
        seite=int(g("seite", 0) or 0),
        auftragsnummer=str(g("auftragsnummer", "") or ""),
        rechnungsnummer=g("rechnungsnummer"),
        schlusstag=g("schlusstag") or g("datum_dokument") or date.today(),
        isin=str(g("isin", "") or ""),
        wkn=str(g("wkn", "") or ""),
        bezeichnung=str(g("wertpapierbezeichnung", "") or ""),
        stueck=_d(g("stueck", 0)),
        ausfuehrungskurs=g("ausfuehrungskurs"),
        kurswert=_d(g("kurswert", 0)),
        gebuehren_summe=_d(g("gebuehren_summe", 0)),
        ausmachender_betrag=_d(g("ausmachender_betrag", 0)),
        tranchen=tranchen,
        kapitalertragsteuer=_d(g("kapitalertragsteuer", 0)),
        soli=_d(g("soli", 0)),
        quellensteuer_eur=_d(g("quellensteuer_eur", 0)),
        teilfrei_satz=g("teilfrei_satz"),
        stueckzinsen=_d(g("stueckzinsen", 0)),
        depot_index=depot_index,
        depot_name=g("depot"),
        marker=list(g("marker", []) or []),
        warnings=list(g("warnings", []) or []),
        waehrung=str(g("waehrung", "EUR") or "EUR"),
    )

    # Marker, die die Altparser als Flags statt als Liste führen
    if g("ak_unvollstaendig", False):
        nb.marker.append("#AK-PRÜFEN#")
        nb.buchwert_unvollstaendig = True
    if g("lot_unvollstaendig", False):
        nb.marker.append("#LOT-PRÜFEN#")

    # Der Flatex-Einzelbelegparser rechnet den Anschaffungswert aus dem
    # bereits teilfreigestellten Gewinn/Verlust zurück. Bei Fonds ist das
    # Ergebnis um dreistellige Beträge falsch — deshalb hier immer markieren.
    if nb.typ == "VERKAUF" and type(beleg).__module__ == "parser_flatex":
        nb.marker.append("#AK-PRÜFEN#")
        nb.warnings.append(
            "Anschaffungswert aus Gewinn/Verlust zurückgerechnet — bei Fonds "
            "hat die Bank die Teilfreistellung bereits gegengerechnet")

    # Doppelte Marker entfernen, Reihenfolge erhalten
    gesehen, sauber = set(), []
    for m in nb.marker:
        if m not in gesehen:
            gesehen.add(m)
            sauber.append(m)
    nb.marker = sauber
    return nb

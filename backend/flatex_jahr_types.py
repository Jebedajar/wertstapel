"""
flatex_jahr_types.py — Gemeinsame Dataclasses für den Flatex-Jahresmodus
(Erträgnisaufstellung PDF + Kontoumsätze CSV).

Strukturell kompatibel zu den Beleg/Tranche-Definitionen der bestehenden
Parser (parser.py, parser_flatex.py, parser_comdirect.py, parser_ibkr.py).

NEU gegenüber den Einzelbeleg-Parsern:
  - Beleg.depot          : Name des Unterdepots (z. B. "Low Risk Depot")
  - Beleg.depot_quelle   : wie die Zuordnung zustande kam (Audit-Trail)
  - Beleg.veraeusserungskosten / anschaffungskosten_gesamt
    → getrennte Kostenseiten, siehe Docstring in parser_flatex_ertraegnis

Alle bestehenden Felder bleiben unverändert, damit booking_engine die
Belege ohne Sonderbehandlung verarbeiten kann.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from datetime import date
from typing import Optional, List, Literal


BelegTyp = Literal[
    "KAUF",
    "VERKAUF",
    "DIVIDENDE",
    "FONDSERTRAG",
    "VERWAHRENTGELT",
    "ZINSGUTSCHRIFT",
    "ZINSAUFWAND",
    "VORABPAUSCHALE_STEUER",
    "KAPITALMASSNAHME",
    "DEPOTUEBERTRAG",
]


@dataclass
class Tranche:
    """Eine Anschaffungstranche. Im Jahresmodus meist synthetisch (1 Stück-Block),
    da die Erträgnisaufstellung den A-Wert bereits aggregiert liefert."""
    stueck: Decimal
    ak: Decimal            # Buchwert / Anschaffungskosten (positiv)
    erloes_ant: Decimal    # anteiliger Netto-Erlös (positiv)
    ist_gewinn: bool


@dataclass
class Beleg:
    typ: BelegTyp
    seite: int
    auftragsnummer: str                 # = Transaktions-Nr. (TA-Nr.)
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

    # Erweiterungen der Einzelbeleg-Parser (kompatibel gehalten)
    teilfrei_satz: Optional[Decimal] = None
    teilfrei_betrag: Optional[Decimal] = None
    quellensteuer_eur: Optional[Decimal] = None
    kapitalertragsteuer: Optional[Decimal] = None
    soli: Optional[Decimal] = None
    devisenkurs: Optional[Decimal] = None
    ak_unvollstaendig: bool = False

    # ── NEU: Marker ─────────────────────────────────────────────
    # Bewusst NICHT in wertpapierbezeichnung: booking_engine kürzt die
    # Bezeichnung auf `options.kuerze_bezeichnung_auf` (Default 30 Zeichen)
    # und würde Marker zerstören. Sie werden erst nach der Buchungserzeugung
    # in den Buchungstext injiziert — analog zu #LOT-PRÜFEN# in v3.
    marker: List[str] = field(default_factory=list)

    # ── NEU: Multi-Depot ────────────────────────────────────────
    depot: Optional[str] = None
    depot_quelle: Optional[str] = None   # "csv-direkt" | "ta-exakt" |
                                         # "ta-fenster" | "ta-fenster+betrag" |
                                         # "isin-eindeutig" | "einzeldepot" |
                                         # "unbestimmt"

    # ── NEU: getrennte Kostenseiten (Jahresmodus) ───────────────
    veraeusserungskosten: Optional[Decimal] = None
    anschaffungskosten_gesamt: Optional[Decimal] = None

    # Rohwerte der Erträgnisaufstellung (für Protokoll/Nachvollziehbarkeit)
    roh_a_wert: Optional[Decimal] = None
    roh_v_wert: Optional[Decimal] = None
    roh_kosten: Optional[Decimal] = None
    roh_bruttoertrag: Optional[Decimal] = None

    # Storno-Verkettung
    storniert_von: Optional[str] = None   # TA-Nr. des Storno-Satzes
    storniert_ta: Optional[str] = None    # bei Storno: welche TA-Nr. storniert wird


@dataclass
class IgnoredPage:
    seite: int
    typ: str
    grund: str


@dataclass
class UngebuchterBeleg:
    """Erkannter, aber nicht automatisch buchbarer Vorgang.
    Erscheint explizit im Protokoll — kein stiller Fehler."""
    seite: int
    typ: str
    isin: Optional[str]
    bezeichnung: str
    betrag: Optional[Decimal]
    grund: str
    depot: Optional[str] = None

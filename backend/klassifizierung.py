"""
klassifizierung.py — Bestimmt für jeden Beleg die Instrumentenklasse und,
bei Fonds, die Kategorie für die Teilfreistellung.

Grundregel: Es wird nie geraten. Wo die Zuordnung unsicher ist, wird sie
markiert und — bei Fonds — auf ein eigenes Sammelkonto gebucht, damit die
Kanzlei am Saldo sieht, wie groß der offene Punkt ist.

Drei Stufen:
  1. Mandanten-ISIN-Tabelle (manuelle Einträge haben immer Vorrang)
  2. Belegmerkmale — bei Fonds vor allem der von der Bank angewandte
     Teilfreistellungssatz, der die Kategorie eindeutig verrät
  3. Sonst: aktie mit Marker #KLASSE# bzw. Kategorie unbestimmt mit #TF?#
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from decimal import Decimal
from pathlib import Path
from typing import Dict, Optional, Tuple, List

AKTIE = "aktie"
FONDS = "fonds"
ANLEIHE = "anleihe"
DERIVAT = "derivat_verbrieft"

# Echte Optionen und Futures bildet das Tool bewusst nicht ab.
NICHT_ABBILDBAR = "nicht_abbildbar"

_FONDS_WORTE = re.compile(
    r"\b(etf|ucits|fonds?|fund|index|sicav|investmentanteil|"
    r"lyxor|ishares|xtrackers|amundi|vanguard|spdr|invesco)\b", re.I)
_ANLEIHE_WORTE = re.compile(
    r"\b(anleihe|bond|obligation|schuldverschr|note|bundesobl|"
    r"floater|treasury|senior|nachrang)\b", re.I)
_DERIVAT_WORTE = re.compile(
    r"\b(turbo|faktor|optionsschein|zertifikat|discount|bonus|"
    r"knock.?out|mini.?long|mini.?short|call|put)\b", re.I)
_NICHT_ABBILDBAR_WORTE = re.compile(
    r"\b(future|stillhalter|cfd|kontrakt|margin)\b", re.I)
_ADR_WORTE = re.compile(r"\b(adr|american depositary|depositary receipt)\b", re.I)

# Anleihen werden in Nominal gehandelt: Kurs um 100, Bezeichnung mit
# Kupon und Fälligkeit ("3,5% 15.02.2030").
_KUPON = re.compile(r"\d+[,.]\d+\s*%")


@dataclass
class IsinEintrag:
    isin: str
    bezeichnung: str = ""
    klasse: Optional[str] = None
    fondskategorie: Optional[str] = None
    quelle: str = "heuristik"          # "manuell" | "bank" | "heuristik"


class IsinTabelle:
    """Mandantenbezogene Zuordnung ISIN → Klasse und Fondskategorie.

    Wird bei jedem Lauf ergänzt, sobald eine Bankquelle etwas Eindeutiges
    liefert. Manuelle Einträge werden nie überschrieben.
    """

    def __init__(self, eintraege: Optional[Dict[str, IsinEintrag]] = None):
        self._d: Dict[str, IsinEintrag] = eintraege or {}

    @classmethod
    def laden(cls, pfad: Path) -> "IsinTabelle":
        p = Path(pfad)
        if not p.exists():
            return cls()
        roh = json.loads(p.read_text(encoding="utf-8"))
        return cls({k: IsinEintrag(**v) for k, v in roh.items()})

    def speichern(self, pfad: Path) -> None:
        p = Path(pfad)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({k: asdict(v) for k, v in sorted(self._d.items())},
                                indent=2, ensure_ascii=False), encoding="utf-8")

    def get(self, isin: str) -> Optional[IsinEintrag]:
        return self._d.get(isin)

    def merken(self, isin: str, bezeichnung: str, klasse: Optional[str],
               kategorie: Optional[str], quelle: str) -> None:
        if not isin:
            return
        alt = self._d.get(isin)
        if alt and alt.quelle == "manuell":
            return                       # manuell schlägt alles
        if alt and alt.quelle == "bank" and quelle == "heuristik":
            return                       # Bank schlägt Heuristik
        self._d[isin] = IsinEintrag(
            isin=isin, bezeichnung=bezeichnung or (alt.bezeichnung if alt else ""),
            klasse=klasse or (alt.klasse if alt else None),
            fondskategorie=kategorie or (alt.fondskategorie if alt else None),
            quelle=quelle,
        )

    def offene(self) -> List[IsinEintrag]:
        """Einträge, bei denen Klasse oder Kategorie unklar geblieben ist —
        Vorschlagsliste für die Pflegemaske im Frontend."""
        return [e for e in self._d.values()
                if e.klasse is None
                or (e.klasse == FONDS and e.fondskategorie in (None, "unbestimmt"))]

    def __len__(self) -> int:
        return len(self._d)


class Klassifikator:
    def __init__(self, matrix, tabelle: Optional[IsinTabelle] = None):
        self.matrix = matrix
        self.tabelle = tabelle or IsinTabelle()

    # ── Instrumentenklasse ────────────────────────────────────────────────
    def _klasse_aus_beleg(self, nb) -> Tuple[Optional[str], bool]:
        """Rückgabe: (klasse, sicher)."""
        text = f"{nb.bezeichnung} {getattr(nb.quelle, 'wertpapierbezeichnung', '')}"

        if _ADR_WORTE.search(text):
            # American Depositary Receipts verbriefen Aktien und werden nach
            # BMF vom 24.05.2013 wie Aktien behandelt.
            return AKTIE, True
        if _NICHT_ABBILDBAR_WORTE.search(text):
            return NICHT_ABBILDBAR, True
        if _DERIVAT_WORTE.search(text):
            return DERIVAT, True
        if nb.teilfrei_satz is not None or nb.typ == "FONDSERTRAG":
            return FONDS, True
        if _FONDS_WORTE.search(text):
            return FONDS, True
        if _ANLEIHE_WORTE.search(text) or nb.stueckzinsen:
            return ANLEIHE, True
        if _KUPON.search(text):
            return ANLEIHE, False
        if nb.typ == "DIVIDENDE":
            return AKTIE, True
        return None, False

    # ── Fondskategorie ────────────────────────────────────────────────────
    def _kategorie_aus_beleg(self, nb) -> Tuple[Optional[str], str]:
        """Rückgabe: (kategorie, quelle)."""
        kat = self.matrix.kategorie_aus_banksatz(nb.teilfrei_satz)
        if kat:
            return kat, "bank"
        return None, "heuristik"

    # ── Hauptfunktion ─────────────────────────────────────────────────────
    # Belegtypen ohne Wertpapierbezug — für sie ist die Klasse ohne Bedeutung.
    OHNE_KLASSE = {"VERWAHRENTGELT", "GEBUEHR", "ZINSGUTSCHRIFT", "ZINSAUFWAND",
                   "VORABPAUSCHALE_STEUER", "DEPOTUEBERTRAG"}

    def klassifiziere_alle(self, belege) -> None:
        """Zwei Durchläufe. Der erste sammelt alles, was eindeutig aus
        Bankdaten hervorgeht — vor allem den Teilfreistellungssatz. Der zweite
        wendet das auf alle Belege derselben ISIN an, auch auf frühere Käufe,
        bei denen der Satz noch nicht bekannt war."""
        for nb in belege:
            if nb.typ in self.OHNE_KLASSE:
                continue
            kat = self.matrix.kategorie_aus_banksatz(nb.teilfrei_satz)
            if kat and nb.isin:
                self.tabelle.merken(nb.isin, nb.bezeichnung, FONDS, kat, "bank")
        for nb in belege:
            self.klassifiziere(nb)

    def klassifiziere(self, nb) -> None:
        """Setzt klasse, fondskategorie und Marker am Beleg."""
        if nb.typ in self.OHNE_KLASSE:
            return
        if nb.typ == "DIVIDENDE":
            nb.marker.append(self.matrix.marker("dividende"))
        eintrag = self.tabelle.get(nb.isin) if nb.isin else None

        klasse = eintrag.klasse if eintrag and eintrag.klasse else None
        sicher = klasse is not None
        if klasse is None:
            klasse, sicher = self._klasse_aus_beleg(nb)

        if klasse is None:
            klasse, sicher = AKTIE, False

        nb.klasse = klasse
        if not sicher and klasse != NICHT_ABBILDBAR:
            nb.marker.append(self.matrix.marker("klasse"))
            nb.warnings.append(
                f"Instrumentenklasse nicht sicher erkannt — als '{klasse}' gebucht")

        if _ADR_WORTE.search(nb.bezeichnung or ""):
            nb.marker.append(self.matrix.marker("adr"))
            nb.warnings.append(
                "ADR — nach überwiegender Auffassung wie eine Aktie unter "
                "§ 8b KStG; höchstrichterlich nicht entschieden")

        if klasse == FONDS:
            kat = (eintrag.fondskategorie
                   if eintrag and eintrag.fondskategorie not in (None, "unbestimmt")
                   else None)
            quelle = "manuell" if (eintrag and eintrag.quelle == "manuell" and kat) else None
            if kat is None:
                kat, quelle = self._kategorie_aus_beleg(nb)
            if kat is None:
                kat, quelle = "unbestimmt", "heuristik"
            nb.fondskategorie = kat
            nb.marker.append(self.matrix.tf_marker(kat))
            if kat == "unbestimmt":
                nb.warnings.append(
                    "Fondskategorie nicht ermittelbar — Buchung auf dem Konto "
                    "'Kategorie unbestimmt'. Bei Interactive Brokers ist das der "
                    "Normalfall, weil dort keine Teilfreistellung ausgewiesen wird.")
            self.tabelle.merken(nb.isin, nb.bezeichnung, FONDS, kat,
                                quelle or "heuristik")
        elif nb.isin:
            self.tabelle.merken(nb.isin, nb.bezeichnung, klasse, None,
                                "bank" if sicher else "heuristik")

        if klasse == NICHT_ABBILDBAR:
            nb.warnings.append(
                "Termingeschäft ohne Verbriefung (Option, Future, CFD) — wird "
                "nicht gebucht")

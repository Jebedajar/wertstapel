"""
depot_registry.py — Generische Verwaltung beliebig vieler Unterdepots.

Hintergrund
-----------
Flatex erlaubt mehrere Unterdepots unter einer Kundennummer. Jedes Unterdepot
hat ein eigenes Verrechnungskonto (eigene IBAN, eigenes `Auftraggeberkonto`
in den Kontoumsätzen). Damit Bank- und ggf. Bestandskonten am Jahresende
auseinandergehalten werden können, braucht jedes Unterdepot eigene
Sachkonten im Kontenrahmen.

Diese Registry ist bewusst NICHT auf zwei Depots festgelegt — sie vergibt
Konten für 1..n Depots und funktioniert auch im Einzeldepot-Fall
(dann wird schlicht das Basiskonto verwendet, exakt wie bisher).

Vergabestrategie
----------------
1. Explizite Zuordnung (`overrides`) hat immer Vorrang. Das ist der Weg für
   Mandanten, deren Steuerberater 1801 bereits anderweitig belegt hat.
2. Ohne Override wird deterministisch vergeben: Depots werden nach einem
   stabilen Schlüssel sortiert (Kontonummer, nicht Anzeigename — der Name
   kann vom Kunden umbenannt werden) und erhalten fortlaufend
   basis, basis+1, basis+2, ...

Determinismus ist hier kritisch: Zwei Exporte desselben Mandanten müssen
dieselben Konten liefern, sonst kollidiert der zweite Import in DATEV mit
dem ersten.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Iterable


# Standard-Basiskonten SKR04. Bewusst als Konstanten, nicht hart im Code.
DEFAULT_BASIS = {
    "bank": 1801,        # Verrechnungs-/Bankkonto je Unterdepot
    "bestand": 1510,     # Wertpapiere UV je Unterdepot (optional, s. u.)
}

# Wenn False, teilen sich alle Depots EIN Bestandskonto (1510).
# Wenn True, bekommt jedes Depot ein eigenes (1510, 1511, ...).
#
# Standard: True. Begründung: Flatex liefert je Unterdepot einen eigenen
# Jahresdepotauszug. Nur mit getrennten Bestandskonten lässt sich der
# Buchbestand am Stichtag gegen den jeweiligen Auszug abstimmen.
#
# ACHTUNG: Ob 1511 ff. im Kontenplan des Mandanten frei sind, ist NICHT
# geprüft — die Vergabe läuft schlicht ab basis_bestand aufwärts. Die
# konkreten Nummern gehören einmalig von der Steuerberaterin bestätigt und
# danach als `overrides` fixiert, damit Folgeexporte stabil bleiben.
SPLIT_BESTANDSKONTO = True


@dataclass
class Depot:
    """Ein Unterdepot."""
    schluessel: str                 # stabil: Auftraggeberkonto/Kontonummer
    name: str                       # Anzeigename ("Low Risk Depot")
    bank_konto: int = 0
    bestand_konto: int = 0
    index: int = 0                  # 0-basierte Reihenfolge

    @property
    def kurz(self) -> str:
        """Kurzform für den Buchungstext (DATEV: 60 Zeichen gesamt!)."""
        return self.name.replace(" Depot", "").replace(" ", "")[:12]


class DepotRegistry:
    """Sammelt Depots und vergibt deterministisch Sachkonten."""

    def __init__(
        self,
        basis_bank: int = DEFAULT_BASIS["bank"],
        basis_bestand: int = DEFAULT_BASIS["bestand"],
        split_bestand: bool = SPLIT_BESTANDSKONTO,
        overrides: Optional[Dict[str, Dict[str, int]]] = None,
    ):
        """
        overrides: {depot_schluessel: {"bank": 1801, "bestand": 1510}}
                   Teilangaben erlaubt — fehlende Werte werden vergeben.
        """
        self.basis_bank = basis_bank
        self.basis_bestand = basis_bestand
        self.split_bestand = split_bestand
        self.overrides = overrides or {}
        self._depots: Dict[str, Depot] = {}
        self._finalisiert = False

    # ── Erfassung ───────────────────────────────────────────────
    def erfasse(self, schluessel: str, name: str) -> None:
        """Meldet ein Depot an. Mehrfachaufrufe sind unschädlich."""
        if self._finalisiert:
            raise RuntimeError(
                "Registry bereits finalisiert — erst alle Depots erfassen, "
                "dann finalisieren()."
            )
        schluessel = (schluessel or "").strip()
        name = (name or "").strip()
        if not schluessel:
            # Fallback: Name als Schlüssel, wenn keine Kontonummer vorliegt
            schluessel = name or "UNBEKANNT"
        if schluessel not in self._depots:
            self._depots[schluessel] = Depot(schluessel=schluessel, name=name or schluessel)
        elif name and self._depots[schluessel].name != name:
            # Name kann sich zwischen Exporten ändern — Schlüssel bleibt stabil
            self._depots[schluessel].name = name

    def erfasse_viele(self, paare: Iterable[tuple]) -> None:
        for schluessel, name in paare:
            self.erfasse(schluessel, name)

    # ── Kontenvergabe ───────────────────────────────────────────
    def finalisieren(self) -> None:
        """Vergibt die Konten. Muss nach der Erfassung und vor dem
        ersten Zugriff aufgerufen werden."""
        if self._finalisiert:
            return
        # Stabile Sortierung über den Schlüssel (nicht den Anzeigenamen!)
        geordnet = sorted(self._depots.values(), key=lambda d: d.schluessel)
        naechste_bank = self.basis_bank
        naechster_bestand = self.basis_bestand
        vergeben_bank = {
            ov["bank"] for ov in self.overrides.values() if "bank" in ov
        }
        vergeben_bestand = {
            ov["bestand"] for ov in self.overrides.values() if "bestand" in ov
        }

        for i, d in enumerate(geordnet):
            d.index = i
            ov = self.overrides.get(d.schluessel, {})

            if "bank" in ov:
                d.bank_konto = ov["bank"]
            else:
                while naechste_bank in vergeben_bank:
                    naechste_bank += 1
                d.bank_konto = naechste_bank
                vergeben_bank.add(naechste_bank)
                naechste_bank += 1

            if "bestand" in ov:
                d.bestand_konto = ov["bestand"]
            elif self.split_bestand:
                while naechster_bestand in vergeben_bestand:
                    naechster_bestand += 1
                d.bestand_konto = naechster_bestand
                vergeben_bestand.add(naechster_bestand)
                naechster_bestand += 1
            else:
                d.bestand_konto = self.basis_bestand

        self._finalisiert = True

    # ── Zugriff ─────────────────────────────────────────────────
    @property
    def anzahl(self) -> int:
        return len(self._depots)

    @property
    def ist_multidepot(self) -> bool:
        return len(self._depots) > 1

    def alle(self) -> List[Depot]:
        self.finalisieren()
        return sorted(self._depots.values(), key=lambda d: d.index)

    def by_name(self, name: str) -> Optional[Depot]:
        self.finalisieren()
        for d in self._depots.values():
            if d.name == name:
                return d
        return None

    def by_schluessel(self, schluessel: str) -> Optional[Depot]:
        self.finalisieren()
        return self._depots.get(schluessel)

    def bank_konto(self, depot_name: Optional[str]) -> int:
        """Bankkonto für einen Depotnamen. Fällt auf das Basiskonto zurück,
        wenn kein/kein passendes Depot bekannt ist (Einzeldepot-Verhalten)."""
        self.finalisieren()
        if depot_name:
            d = self.by_name(depot_name)
            if d:
                return d.bank_konto
        return self.basis_bank

    def bestand_konto(self, depot_name: Optional[str]) -> int:
        self.finalisieren()
        if depot_name:
            d = self.by_name(depot_name)
            if d:
                return d.bestand_konto
        return self.basis_bestand

    # ── Protokoll ───────────────────────────────────────────────
    def protokoll(self) -> str:
        self.finalisieren()
        if not self._depots:
            return "Keine Depots erfasst."
        zeilen = ["Erkannte Depots und Kontenzuordnung:"]
        for d in self.alle():
            zeilen.append(
                f"  [{d.index}] {d.name} (Konto {d.schluessel}) "
                f"→ Bank {d.bank_konto}, Bestand {d.bestand_konto}"
            )
        if not self.split_bestand and self.ist_multidepot:
            zeilen.append(
                "  Hinweis: gemeinsames Bestandskonto "
                f"{self.basis_bestand} für alle Depots "
                "(SPLIT_BESTANDSKONTO=False) — Bestandsabstimmung je Depot "
                "am Stichtag ist damit nicht möglich."
            )
        elif self.split_bestand and self.ist_multidepot:
            nicht_bestaetigt = [
                d for d in self.alle()
                if "bestand" not in self.overrides.get(d.schluessel, {})
                and d.bestand_konto != self.basis_bestand
            ]
            if nicht_bestaetigt:
                zeilen.append(
                    "  PRÜFEN: automatisch vergebene Bestandskonten "
                    + ", ".join(str(d.bestand_konto) for d in nicht_bestaetigt)
                    + " — Verfügbarkeit im Kontenplan durch Steuerberater "
                    "bestätigen und als Override fixieren."
                )
        return "\n".join(zeilen)

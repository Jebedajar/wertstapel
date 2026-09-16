"""
depot_registry.py — Stabile Identifikation und Reihenfolge mehrerer
Unterdepots.

Frühere Fassung dieses Moduls vergab hier auch Bank- und Bestandskonten
(basis_bank, basis_bestand, SPLIT_BESTANDSKONTO). Das ist seit der
Kontenmatrix (config/konten.yaml) obsolet — Kontonummern kommen
ausschließlich von dort, abhängig von Kontenrahmen, Vermögensart und
Instrumentenklasse. Ein einzelnes "Bestandskonto je Depot" konnte das
ohnehin nicht mehr abbilden: ein Depot hat, je nach Instrument, bis zu
vier verschiedene Bestandskonten (Aktie, Fonds, Anleihe, Derivat).

Was hier bleibt und weiterhin gebraucht wird: die stabile Zuordnung
Depotname → Index. Sortiert wird nach dem Auftraggeberkonto (schluessel),
nicht nach dem Anzeigenamen — der Name kann vom Kunden jederzeit
umbenannt werden, die Kontonummer nicht. Ohne diese Stabilität würde ein
umbenanntes Depot beim nächsten Export auf einen anderen Index und damit
auf ein anderes Bankkonto rutschen und mit dem Vorjahr kollidieren.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Iterable


@dataclass
class Depot:
    """Ein Unterdepot."""
    schluessel: str                 # stabil: Auftraggeberkonto/Kontonummer
    name: str                       # Anzeigename ("Low Risk Depot")
    index: int = 0                  # 0-basiert, stabil über schluessel-Sortierung

    @property
    def kurz(self) -> str:
        """Kurzform für den Buchungstext (DATEV: 60 Zeichen gesamt!)."""
        return self.name.replace(" Depot", "").replace(" ", "")[:12]


class DepotRegistry:
    """Sammelt Depots und weist ihnen eine stabile, deterministische
    Reihenfolge zu. Vergibt seit Fassung 3 KEINE Kontonummern mehr —
    siehe Moduldocstring."""

    def __init__(self):
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
            # Fallback: Name als Schlüssel, wenn keine Kontonummer vorliegt.
            # Dann ist die Reihenfolge nicht stabil gegen Umbenennung —
            # das ist der bestmögliche Fall ohne echte Kontonummer.
            schluessel = name or "UNBEKANNT"
        if schluessel not in self._depots:
            self._depots[schluessel] = Depot(schluessel=schluessel, name=name or schluessel)
        elif name and self._depots[schluessel].name != name:
            # Name kann sich zwischen Exporten ändern — Schlüssel bleibt stabil.
            self._depots[schluessel].name = name

    def erfasse_viele(self, paare: Iterable[tuple]) -> None:
        for schluessel, name in paare:
            self.erfasse(schluessel, name)

    # ── Reihenfolge ─────────────────────────────────────────────
    def finalisieren(self) -> None:
        """Vergibt die stabile Reihenfolge. Muss nach der Erfassung und vor
        dem ersten Zugriff aufgerufen werden."""
        if self._finalisiert:
            return
        # Stabile Sortierung über den Schlüssel (Kontonummer), NICHT den
        # Anzeigenamen — der kann sich zwischen zwei Exporten ändern, ohne
        # dass sich am Depot selbst etwas geändert hat.
        geordnet = sorted(self._depots.values(), key=lambda d: d.schluessel)
        for i, d in enumerate(geordnet):
            d.index = i
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

    def depot_index(self, depot_name: Optional[str]) -> int:
        """1-basierter Index für die Kontenmatrix (KontenKontext.depot).

        Diese Nummerierung, nicht eine eigene Sortierung über die im Lauf
        vorkommenden Namen, ist der einzige Ort, an dem Depotname auf
        Kontenmatrix-Index abgebildet werden sollte — hier ist die
        Stabilität sichergestellt. Unbekannter oder fehlender Name → 1
        (Einzeldepot-Verhalten).
        """
        self.finalisieren()
        if depot_name:
            d = self.by_name(depot_name)
            if d:
                return d.index + 1
        return 1

    # ── Protokoll ───────────────────────────────────────────────
    def protokoll(self) -> str:
        """Nennt nur Depotidentität und Reihenfolge. Welche Bank- und
        Bestandskonten tatsächlich verwendet wurden, stammt aus der
        Kontenmatrix und steht im Kontenblatt bzw. im Protokollkopf von
        run.py — nicht hier, damit nie zwei Quellen widersprüchliche
        Kontonummern behaupten."""
        self.finalisieren()
        if not self._depots:
            return "Keine Depots erfasst."
        zeilen = ["Erkannte Depots (Reihenfolge stabil nach Kontonummer, "
                 "nicht nach Anzeigename):"]
        for d in self.alle():
            zeilen.append(f"  Depot {d.index + 1}: {d.name} (Konto {d.schluessel})")
        if len(self._depots) > 5:
            zeilen.append(
                "  ACHTUNG: mehr als 5 Depots erkannt. Die Kontenmatrix hält "
                "für die Instrumentenklassen Bestand nur 5 Depotplätze vor "
                "(config/konten.yaml). Weitere Nummern müssen dort ergänzt "
                "werden, bevor dieser Mandant korrekt gebucht werden kann.")
        return "\n".join(zeilen)

"""
bewertung.py — Ermittlung des Buchwerts beim Abgang.

Bisher steckte die FIFO-Logik im comdirect-Parser (Inventory-Dict in
`parse_xlsx`) und der IBKR-Parser konnte mangels Closed-Lot-Detail gar nicht
zuordnen. Beides wandert hierher, damit alle Banken dieselbe Methode nutzen
und die Methode pro Mandant wählbar ist.

Vorgabe ist der gleitende Durchschnitt (§ 240 Abs. 4 HGB). Anders als ein
Jahresdurchschnitt steht er zu jedem Zeitpunkt fest und eignet sich damit für
unterjährige Buchungen. FIFO bleibt wählbar, weil die Banken selbst so rechnen.
Die gewählte Methode ist nach § 252 Abs. 1 Nr. 6 HGB beizubehalten und wird
deshalb am Mandanten gespeichert, nicht pro Export gewählt.

Wichtig: Liefert die Bank den Anschaffungswert selbst (Sparkasse Seite 2,
Flatex-Erträgnisaufstellung mit A-Wert), wird dieser übernommen und hier gar
nicht gerechnet — siehe `uebernimm_banktranchen`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from modelle import round2

GLEITENDER_DURCHSCHNITT = "gleitender_durchschnitt"
FIFO = "fifo"


@dataclass
class _Lot:
    stueck: Decimal
    ak_je_stueck: Decimal


@dataclass
class _Position:
    stueck: Decimal = Decimal("0")
    wert: Decimal = Decimal("0")           # Summe der Anschaffungskosten
    lots: List[_Lot] = field(default_factory=list)

    @property
    def schnitt(self) -> Decimal:
        if self.stueck <= 0:
            return Decimal("0")
        return self.wert / self.stueck


class Bewerter:
    """Führt Bestände je ISIN und liefert den Buchwert beim Abgang."""

    def __init__(self, methode: str = GLEITENDER_DURCHSCHNITT):
        if methode not in (GLEITENDER_DURCHSCHNITT, FIFO):
            raise ValueError(f"Unbekannte Bewertungsmethode: {methode}")
        self.methode = methode
        self._pos: Dict[str, _Position] = {}

    # ── Bestandsaufbau ────────────────────────────────────────────────────
    def anfangsbestand(self, isin: str, stueck: Decimal, wert: Decimal) -> None:
        """Vortrag aus dem Vorjahr. Ohne ihn sind Verkäufe von Altbeständen
        nicht bewertbar und bekommen #AK-PRÜFEN#."""
        self.zugang(isin, stueck, wert)

    def zugang(self, isin: str, stueck: Decimal, wert: Decimal) -> None:
        """wert = ausmachender Betrag inklusive Gebühren und Transaktionssteuer."""
        stueck, wert = Decimal(stueck), Decimal(wert)
        if stueck <= 0:
            return
        p = self._pos.setdefault(isin, _Position())
        p.stueck += stueck
        p.wert += wert
        if self.methode == FIFO:
            p.lots.append(_Lot(stueck=stueck, ak_je_stueck=wert / stueck))

    # ── Abgang ────────────────────────────────────────────────────────────
    def abgang(self, isin: str, stueck: Decimal) -> Tuple[Decimal, bool]:
        """Rückgabe: (buchwert, unvollstaendig).

        `unvollstaendig` bedeutet: für einen Teil der verkauften Stücke war
        kein Anschaffungswert bekannt. Der fehlende Teil wird mit 0 bewertet
        und der Beleg mit #AK-PRÜFEN# markiert — nicht stillschweigend als
        Gewinn gebucht.
        """
        stueck = Decimal(stueck)
        p = self._pos.get(isin)
        if p is None or p.stueck <= 0 or stueck <= 0:
            return Decimal("0"), True

        gedeckt = min(stueck, p.stueck)
        unvollstaendig = gedeckt < stueck

        if self.methode == GLEITENDER_DURCHSCHNITT:
            buchwert = round2(p.schnitt * gedeckt)
            p.wert -= buchwert
            p.stueck -= gedeckt
            if p.stueck <= 0:
                p.stueck = Decimal("0")
                p.wert = Decimal("0")
            return buchwert, unvollstaendig

        # FIFO
        rest = gedeckt
        buchwert = Decimal("0")
        while rest > 0 and p.lots:
            lot = p.lots[0]
            nimm = min(rest, lot.stueck)
            buchwert += lot.ak_je_stueck * nimm
            lot.stueck -= nimm
            rest -= nimm
            if lot.stueck <= 0:
                p.lots.pop(0)
        buchwert = round2(buchwert)
        p.stueck -= gedeckt
        p.wert -= buchwert
        return buchwert, unvollstaendig

    # ── Bankwerte übernehmen ──────────────────────────────────────────────
    def uebernimm_banktranchen(self, isin: str, tranchen) -> Optional[Decimal]:
        """Nutzt den von der Bank gelieferten Anschaffungswert und hält den
        eigenen Bestand synchron. Rückgabe: Buchwert, oder None wenn keine
        brauchbaren Tranchen vorliegen."""
        if not tranchen:
            return None
        buchwert = round2(sum(Decimal(t.ak) for t in tranchen))
        stueck = sum(Decimal(t.stueck) for t in tranchen)
        if buchwert <= 0:
            return None
        p = self._pos.get(isin)
        if p is not None:
            p.stueck = max(Decimal("0"), p.stueck - stueck)
            p.wert = max(Decimal("0"), p.wert - buchwert)
            if self.methode == FIFO:
                rest = stueck
                while rest > 0 and p.lots:
                    lot = p.lots[0]
                    nimm = min(rest, lot.stueck)
                    lot.stueck -= nimm
                    rest -= nimm
                    if lot.stueck <= 0:
                        p.lots.pop(0)
        return buchwert

    # ── Auswertung ────────────────────────────────────────────────────────
    def bestaende(self) -> Dict[str, Tuple[Decimal, Decimal]]:
        """{isin: (stueck, buchwert)} — Grundlage für den Bestandsnachweis."""
        return {i: (p.stueck, round2(p.wert))
                for i, p in self._pos.items() if p.stueck > 0}

    def protokoll(self) -> str:
        z = [f"Bewertungsmethode: "
             f"{'gleitender Durchschnitt' if self.methode == GLEITENDER_DURCHSCHNITT else 'FIFO'}"]
        best = self.bestaende()
        if best:
            z.append("Bestand am Ende des Zeitraums:")
            for isin, (st, wert) in sorted(best.items()):
                z.append(f"  {isin}  {st} Stück  Buchwert {wert} EUR")
        return "\n".join(z)


def bewerte_belege(belege, methode: str = GLEITENDER_DURCHSCHNITT,
                   anfangsbestaende: Optional[Dict[str, Tuple[Decimal, Decimal]]] = None
                   ) -> Bewerter:
    """Läuft chronologisch durch die Belege, baut Bestände auf und setzt
    `buchwert` sowie `buchwert_unvollstaendig` an jedem Verkauf.

    Die Belege müssen normalisiert (modelle.NormBeleg) und nach Datum
    sortiert sein.
    """
    bew = Bewerter(methode)
    for isin, (stueck, wert) in (anfangsbestaende or {}).items():
        bew.anfangsbestand(isin, stueck, wert)

    for nb in sorted(belege, key=lambda b: (b.schlusstag, b.auftragsnummer)):
        if nb.typ == "KAUF":
            bew.zugang(nb.isin, nb.stueck, nb.ausmachender_betrag)
        elif nb.typ in ("VERKAUF", "KAPITALMASSNAHME"):
            bank_wert = bew.uebernimm_banktranchen(nb.isin, nb.tranchen)
            if bank_wert is not None:
                nb.buchwert = bank_wert
                nb.buchwert_unvollstaendig = False
            else:
                nb.buchwert, nb.buchwert_unvollstaendig = bew.abgang(nb.isin, nb.stueck)
                if nb.buchwert_unvollstaendig:
                    nb.warnings.append(
                        "Anschaffungskosten für einen Teil der verkauften Stücke "
                        "nicht bekannt (Altbestand vor dem Exportzeitraum)")
    return bew

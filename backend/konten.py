"""
konten.py — Zugriff auf die Kontenmatrix aus config/konten.yaml.

Einzige Quelle für Kontonummern. Im übrigen Code darf keine Kontonummer
mehr als Literal stehen.

Verwendung:

    from konten import Kontenmatrix, KontenKontext

    matrix = Kontenmatrix.laden()
    ctx = KontenKontext(kontenrahmen="SKR04", vermoegensart="UV", depot=1)

    matrix.bank(ctx)                                  -> "1800"
    matrix.bestand("aktie", ctx)                      -> "1510"
    matrix.erfolg("aktie", "erloes_gewinn", ctx)      -> "4906"
    matrix.fonds("abgang_gewinn", "aktienfonds", ctx) -> "4950"
    matrix.gemeinsam("kapest", ctx)                   -> "7630"

Jede unbekannte Kombination wirft KontoNichtDefiniert. Es gibt bewusst
keinen Vorgabewert — eine falsche Buchung ist schlimmer als ein Abbruch.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any
from decimal import Decimal

import yaml


VORGABE_PFAD = Path(__file__).parent / "config" / "konten.yaml"


class KontoNichtDefiniert(KeyError):
    """Für die angefragte Kombination ist in konten.yaml kein Konto hinterlegt."""


@dataclass(frozen=True)
class KontenKontext:
    kontenrahmen: str        # "SKR03" | "SKR04"
    vermoegensart: str       # "UV" | "AV"
    depot: int = 1           # 1-basiert
    sachkontenlaenge: int = 4

    def __post_init__(self):
        if self.kontenrahmen not in ("SKR03", "SKR04"):
            raise ValueError(f"Unbekannter Kontenrahmen: {self.kontenrahmen}")
        if self.vermoegensart not in ("UV", "AV"):
            raise ValueError(f"Unbekannte Vermögensart: {self.vermoegensart}")
        if self.depot < 1:
            raise ValueError("Depotnummer ist 1-basiert")


@dataclass
class AnzulegendesKonto:
    nummer: str
    bezeichnung: str
    zweck: str


class Kontenmatrix:
    def __init__(self, daten: Dict[str, Any]):
        self._d = daten
        self._bank_overrides: Dict[int, str] = {}

    def setze_bank_override(self, depot: int, konto: str) -> None:
        """Überschreibt das Bankkonto eines Depots — für Mandanten, deren
        Kanzlei das Standardkonto anderweitig belegt hat. Wird im Protokoll
        ausgewiesen, damit die Abweichung nicht unbemerkt bleibt."""
        self._bank_overrides[int(depot)] = str(konto)

    @property
    def bank_overrides(self) -> Dict[int, str]:
        return dict(self._bank_overrides)

    # ── Laden ────────────────────────────────────────────────────────────
    @classmethod
    def laden(cls, pfad: Optional[Path] = None) -> "Kontenmatrix":
        p = Path(pfad) if pfad else VORGABE_PFAD
        with open(p, encoding="utf-8") as f:
            daten = yaml.safe_load(f)
        if daten.get("version") != 3:
            raise ValueError(
                f"konten.yaml hat Version {daten.get('version')}, erwartet 3. "
                "Prüfe, ob die Datei zur Codeversion passt."
            )
        return cls(daten)

    # ── Formatierung ─────────────────────────────────────────────────────
    @staticmethod
    def _fmt(nummer: Any, laenge: int) -> str:
        """981 -> '0981'. Kontonummern stehen in der YAML als Zahl."""
        return str(nummer).zfill(laenge)

    def _rahmen(self, ctx: KontenKontext) -> Dict[str, Any]:
        return self._d[ctx.kontenrahmen]

    # ── Zugriffe ─────────────────────────────────────────────────────────
    def bank(self, ctx: KontenKontext) -> str:
        if ctx.depot in self._bank_overrides:
            return self._bank_overrides[ctx.depot]
        konten = self._rahmen(ctx)["bank"]["konten"]
        if ctx.depot > len(konten):
            raise KontoNichtDefiniert(
                f"{ctx.kontenrahmen}: nur {len(konten)} Bankkonten hinterlegt, "
                f"Depot {ctx.depot} angefragt"
            )
        return self._fmt(konten[ctx.depot - 1], ctx.sachkontenlaenge)

    def bestand(self, klasse: str, ctx: KontenKontext) -> str:
        knoten = self._rahmen(ctx)[ctx.vermoegensart]["bestand"]
        if klasse not in knoten:
            raise KontoNichtDefiniert(
                f"{ctx.kontenrahmen}/{ctx.vermoegensart}: kein Bestandskonto "
                f"für Klasse '{klasse}'"
            )
        eintrag = knoten[klasse]
        if "konto" in eintrag:                      # AV: ein Konto, kein Depotsplit
            return self._fmt(eintrag["konto"], ctx.sachkontenlaenge)
        konten = eintrag["konten"]
        if ctx.depot > len(konten):
            raise KontoNichtDefiniert(
                f"{ctx.kontenrahmen}/{ctx.vermoegensart}/{klasse}: nur "
                f"{len(konten)} Depots hinterlegt, Depot {ctx.depot} angefragt. "
                "Weitere Nummern in konten.yaml ergänzen."
            )
        return self._fmt(konten[ctx.depot - 1], ctx.sachkontenlaenge)

    def erfolg(self, klasse: str, zweck: str, ctx: KontenKontext) -> str:
        knoten = self._rahmen(ctx)[ctx.vermoegensart]
        if klasse not in knoten or zweck not in knoten[klasse]:
            raise KontoNichtDefiniert(
                f"{ctx.kontenrahmen}/{ctx.vermoegensart}/{klasse}: kein Konto "
                f"für Zweck '{zweck}'"
            )
        return self._fmt(knoten[klasse][zweck]["konto"], ctx.sachkontenlaenge)

    def fonds(self, zweck: str, kategorie: str, ctx: KontenKontext) -> str:
        """Zwecke mit Kategoriesplit: ausschuettung, abgang_gewinn, abgang_verlust."""
        knoten = self._rahmen(ctx)[ctx.vermoegensart].get("fonds")
        if not knoten or zweck not in knoten:
            raise KontoNichtDefiniert(
                f"{ctx.kontenrahmen}/{ctx.vermoegensart}/fonds: kein Zweck '{zweck}'"
            )
        eintrag = knoten[zweck]
        if "konto" in eintrag:                      # Zweck ohne Kategoriesplit
            return self._fmt(eintrag["konto"], ctx.sachkontenlaenge)
        kat = kategorie or "unbestimmt"
        if kat == "immobilienfonds_ausland":        # eigener TF-Satz, gleiches Konto
            kat = "immobilienfonds"
        if kat not in eintrag:
            raise KontoNichtDefiniert(
                f"{ctx.kontenrahmen}/fonds/{zweck}: keine Kategorie '{kat}'"
            )
        return self._fmt(eintrag[kat]["konto"], ctx.sachkontenlaenge)

    def methode(self, klasse: str, ctx: KontenKontext) -> str:
        """'brutto' (Erlös und Buchwert getrennt) oder 'netto' (Abgangsergebnis)."""
        return self._rahmen(ctx)[ctx.vermoegensart][klasse].get("methode", "netto")

    def gemeinsam(self, zweck: str, ctx: KontenKontext) -> str:
        knoten = self._rahmen(ctx)["gemeinsam"]
        if zweck not in knoten:
            raise KontoNichtDefiniert(
                f"{ctx.kontenrahmen}/gemeinsam: kein Konto für '{zweck}'"
            )
        return self._fmt(knoten[zweck]["konto"], ctx.sachkontenlaenge)

    # ── Fondskategorie und Marker ────────────────────────────────────────
    def kategorie_aus_banksatz(self, satz: Optional[Decimal]) -> Optional[str]:
        """Leitet die Fondskategorie aus dem von der Bank angewandten
        Privatanleger-Teilfreistellungssatz ab. None, wenn nicht ableitbar."""
        if satz is None:
            return None
        try:
            key = int(Decimal(str(satz)))
        except Exception:
            return None
        return self._d["kategorie_aus_banksatz"].get(key)

    def tf_marker(self, kategorie: Optional[str]) -> str:
        return self._d["marker"]["teilfreistellung"].get(kategorie or "unbestimmt",
                                                         self._d["marker"]["teilfreistellung"]["unbestimmt"])

    def tf_satz(self, kategorie: Optional[str]) -> Optional[int]:
        return self._d["teilfreistellung_koerperschaft"].get(kategorie or "unbestimmt")

    def marker(self, name: str) -> str:
        return self._d["marker"][name]

    @property
    def buchungstext_max(self) -> int:
        return int(self._d.get("buchungstext_max_laenge", 60))

    @property
    def entfallene_konten(self) -> Dict[str, str]:
        """Für den Selbsttest: diese Nummern dürfen im Code nicht mehr vorkommen."""
        return {str(k): v for k, v in self._d.get("entfallen", {}).items()}

    # ── Einrichtungsblatt ────────────────────────────────────────────────
    def bezeichnung(self, schluessel: str) -> str:
        return self._d.get("bezeichnungen", {}).get(schluessel, schluessel)

    def anzulegende_konten(self, ctx: KontenKontext,
                           klassen: Optional[List[str]] = None,
                           depots: int = 1) -> List[AnzulegendesKonto]:
        """Konten mit status 'anzulegen' für die gewählte Kombination.
        `depots` begrenzt die Bestandskonten auf die tatsächlich genutzten
        Depots — wer ein Depot hat, soll keine fünf Konten anlegen."""
        klassen = klassen or self._d["instrumentenklassen"]
        treffer: List[AnzulegendesKonto] = []
        wurzel = self._rahmen(ctx)[ctx.vermoegensart]

        for klasse, eintrag in wurzel.get("bestand", {}).items():
            if klasse not in klassen:
                continue
            label = self.bezeichnung(f"bestand/{klasse}")
            if "konten" in eintrag:
                stat = eintrag.get("status")
                stat = stat if isinstance(stat, list) else [stat] * len(eintrag["konten"])
                for i, nr in enumerate(eintrag["konten"][:max(depots, 1)]):
                    if stat[i] == "anzulegen":
                        zusatz = f", Depot {i + 1}" if depots > 1 else ""
                        treffer.append(AnzulegendesKonto(
                            self._fmt(nr, ctx.sachkontenlaenge),
                            label + zusatz, "Bestandskonto"))
            elif eintrag.get("status") == "anzulegen":
                treffer.append(AnzulegendesKonto(
                    self._fmt(eintrag["konto"], ctx.sachkontenlaenge),
                    label, "Bestandskonto"))

        for klasse in klassen:
            zweig = wurzel.get(klasse)
            if not isinstance(zweig, dict):
                continue
            for zweck, eintrag in zweig.items():
                if zweck in ("status", "methode") or not isinstance(eintrag, dict):
                    continue
                if "konto" in eintrag:
                    if eintrag.get("status") == "anzulegen":
                        treffer.append(AnzulegendesKonto(
                            self._fmt(eintrag["konto"], ctx.sachkontenlaenge),
                            self.bezeichnung(f"{klasse}/{zweck}"), "Erfolgskonto"))
                else:
                    for kat, unter in eintrag.items():
                        if not isinstance(unter, dict) or "konto" not in unter:
                            continue
                        if unter.get("status") == "anzulegen":
                            treffer.append(AnzulegendesKonto(
                                self._fmt(unter["konto"], ctx.sachkontenlaenge),
                                self.bezeichnung(f"{klasse}/{zweck}/{kat}"),
                                "Erfolgskonto"))

        gesehen, sauber = set(), []
        for k in sorted(treffer, key=lambda x: x.nummer):
            if k.nummer not in gesehen:
                gesehen.add(k.nummer)
                sauber.append(k)
        return sauber

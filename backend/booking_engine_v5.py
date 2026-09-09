"""
booking_engine_v5.py — Buchungserzeugung auf Basis der Kontenmatrix.

Löst die Dispatcher v1 bis v4 ab. Die alten Funktionen bleiben im Repository,
werden aber nicht mehr aufgerufen; nach einer erfolgreichen Vergleichsphase
können sie entfernt werden.

Was neu ist gegenüber v4
------------------------
  1. Sämtliche Konten kommen aus konten.yaml. Keine Nummer steht mehr im Code.
     Damit ist der SKR-03-Export erstmals vollständig richtig — bisher liefen
     Dividende, Fondsertrag, Steuern, Verwahrentgelt und FTT immer auf
     SKR-04-Nummern, unabhängig vom gewählten Kontenrahmen.
  2. Vier Instrumentenklassen mit eigenen Konten. § 8b KStG gilt nur für Aktien.
  3. Fondskonten je Kategorie, weil die Teilfreistellung je Kategorie abweicht
     und der Buchungsstapel sie nicht transportieren kann.
  4. Zwei Stapel: Handelsrecht und "nur Steuerrecht" (Vorabpauschale).
  5. Finanztransaktionssteuer wird aktiviert statt auf ein eigenes Konto
     gebucht.
  6. Gezahlte Stückzinsen werden als antizipativer Posten abgegrenzt.
  7. Fehlende Anschaffungswerte führen nicht mehr zu einer Buchung auf der
     Gewinnseite, sondern zu einem ungebuchten Beleg.

Korrigierte Konten gegenüber dem Live-Stand
-------------------------------------------
  7700 → Dividendenkonto der Matrix (7700 ist Gewinnvortrag, Eigenkapital)
  7810 → Fondskonto je Kategorie     (7810 liegt im Aufwandsbereich)
  1780 → 7630 / 7633 bzw. 2213 / 2216 (1780 ist LZB-Guthaben)
  6860 → 6879 / 4971                 (6860 ist nicht abziehbare Vorsteuer)
  6305 → entfällt, FTT wird aktiviert (6305 ist Raumkosten)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from konten import Kontenmatrix, KontenKontext, KontoNichtDefiniert
from modelle import (Buchung, NormBeleg, UngebuchterBeleg, Vorabpauschale,
                     kuerzen, fmt_stueck, round2)

NULL = Decimal("0")

# Reihenfolge = Priorität. Vordere Marker zeigen auf Fehler in der Buchung
# selbst, hintere nur auf steuerliche Nacharbeit.
MARKER_PRIO = [
    "#DEPOT-PRÜFEN#", "#AK-PRÜFEN#", "#KLASSE#", "#LOT-PRÜFEN#",
    "#TF?#", "#TF80#", "#TF60#", "#TF40#", "#TF0#",
    "#ADR#", "#DIV#", "#CHECK#", "#VORABP#",
]


@dataclass
class BuchungsErgebnis:
    hauptstapel: List[Buchung] = field(default_factory=list)
    steuerstapel: List[Buchung] = field(default_factory=list)
    ungebucht: List[UngebuchterBeleg] = field(default_factory=list)
    hinweise: List[str] = field(default_factory=list)
    vorabpauschalen: List[Vorabpauschale] = field(default_factory=list)

    @property
    def alle(self) -> List[Buchung]:
        return self.hauptstapel + self.steuerstapel


class Buchungsengine:
    def __init__(self, matrix: Kontenmatrix, ctx: KontenKontext,
                 texte: Dict[str, str], options: Optional[dict] = None):
        self.m = matrix
        self.ctx = ctx
        self.t = texte
        self.o = options or {}
        self.bez_max = int(self.o.get("kuerze_bezeichnung_auf", 30))
        self.text_max = matrix.buchungstext_max

    # ── Hilfen ────────────────────────────────────────────────────────────
    def _ctx(self, nb: NormBeleg) -> KontenKontext:
        if nb.depot_index == self.ctx.depot:
            return self.ctx
        return KontenKontext(self.ctx.kontenrahmen, self.ctx.vermoegensart,
                             nb.depot_index, self.ctx.sachkontenlaenge)

    def _text(self, schluessel: str, nb: NormBeleg, **extra) -> str:
        vorlage = self.t.get(schluessel, "{marker}" + schluessel)
        return vorlage.format(
            marker="",                       # wird später injiziert
            anzahl=fmt_stueck(nb.stueck),
            bezeichnung=kuerzen(nb.bezeichnung, self.bez_max),
            isin=nb.isin,
            auftragsnr=nb.auftragsnummer,
            jahr=nb.schlusstag.year,
            **extra,
        ).strip()[: self.text_max]

    def _b(self, nb: NormBeleg, betrag: Decimal, konto: str, gegenkonto: str,
           text: str, kategorie: str, stapel: str = "handelsrecht",
           stueck: Optional[Decimal] = None) -> Buchung:
        return Buchung(
            umsatz=round2(betrag), soll_haben="S",
            konto=konto, gegenkonto=gegenkonto,
            belegdatum=nb.schlusstag,
            belegfeld_1=nb.auftragsnummer,
            belegfeld_2=nb.rechnungsnummer or "",
            buchungstext=text[: self.text_max],
            isin=nb.isin, wkn=nb.wkn,
            stueck=nb.stueck if stueck is None else stueck,
            kurs=nb.ausfuehrungskurs or NULL,
            kategorie=kategorie, quell_seite=nb.seite, stapel=stapel,
        )

    def _bank(self, nb: NormBeleg) -> str:
        return self.m.bank(self._ctx(nb))

    def _bestand(self, nb: NormBeleg) -> str:
        return self.m.bestand(nb.klasse, self._ctx(nb))

    def _fonds(self, zweck: str, nb: NormBeleg) -> str:
        return self.m.fonds(zweck, nb.fondskategorie, self._ctx(nb))

    def _gem(self, zweck: str, nb: NormBeleg) -> str:
        return self.m.gemeinsam(zweck, self._ctx(nb))

    # ── Kauf ──────────────────────────────────────────────────────────────
    def kauf(self, nb: NormBeleg) -> List[Buchung]:
        """Ein Satz: Bestand an Bank über den ausmachenden Betrag.

        Gebühren und Finanztransaktionssteuer sind darin enthalten und damit
        aktiviert — genau das war die Festlegung der Steuerberaterin zur FTT.
        """
        return [self._b(nb, nb.ausmachender_betrag, self._bestand(nb), self._bank(nb),
                        self._text("kauf", nb), "Kurswert+Nebenkosten")]

    # ── Verkauf ───────────────────────────────────────────────────────────
    def verkauf(self, nb: NormBeleg) -> Tuple[List[Buchung], List[UngebuchterBeleg]]:
        # Ein Buchwert von 0 bei gleichzeitig unvollständiger Bewertung ist
        # kein Buchwert, sondern eine Wissenslücke. Würden wir buchen, bliebe
        # das Bestandskonto ungemindert und der gesamte Erlös erschiene als
        # Gewinn — der Stapel sähe vollständig aus und wäre es nicht.
        if nb.buchwert is None or (nb.buchwert <= NULL and nb.buchwert_unvollstaendig):
            return [], [UngebuchterBeleg(
                typ="VERKAUF", datum=nb.schlusstag, betrag=nb.ausmachender_betrag,
                isin=nb.isin, bezeichnung=nb.bezeichnung, seite=nb.seite,
                grund="Kein Anschaffungswert ermittelbar (Altbestand vor dem "
                      "Exportzeitraum)",
                empfehlung="Buchwert aus der Vorjahresbilanz ergänzen und "
                           "manuell buchen. Eine Buchung mit Buchwert 0 würde "
                           "den gesamten Erlös als Gewinn ausweisen und das "
                           "Bestandskonto ungemindert lassen.")]

        methode = self.m.methode(nb.klasse, self._ctx(nb))
        if methode == "brutto":
            return self._verkauf_brutto(nb), []
        return self._verkauf_netto(nb), []

    def _verkauf_brutto(self, nb: NormBeleg) -> List[Buchung]:
        """Aktien, § 8b KStG. Erlös und Buchwert getrennt, weil DATEV dafür
        eigene, für die Körperschaftsteuer gekennzeichnete Konten vorsieht."""
        c = self._ctx(nb)
        gewinn = nb.ist_gewinn
        k_erloes = self.m.erfolg(nb.klasse, "erloes_gewinn" if gewinn else "erloes_verlust", c)
        k_abgang = self.m.erfolg(nb.klasse, "buchwert_gewinn" if gewinn else "buchwert_verlust", c)
        k_kosten = self.m.erfolg(nb.klasse, "kosten_gewinn" if gewinn else "kosten_verlust", c)

        buchungen = [
            self._b(nb, nb.erloes_brutto, self._bank(nb), k_erloes,
                    self._text("verkauf_erloes", nb),
                    "Erlös " + ("(Gewinn)" if gewinn else "(Verlust)")),
            self._b(nb, nb.buchwert, k_abgang, self._bestand(nb),
                    self._text("verkauf_abgang", nb), "Buchwertabgang"),
        ]
        if nb.gebuehren_summe > NULL:
            buchungen.append(self._b(nb, nb.gebuehren_summe, k_kosten, self._bank(nb),
                                     self._text("verkauf_gebuehren", nb),
                                     "Veräußerungskosten"))
        return buchungen

    def _verkauf_netto(self, nb: NormBeleg) -> List[Buchung]:
        """Fonds, Anleihen, verbriefte Derivate. Der Buchwert läuft direkt
        gegen den Bestand, auf dem Erfolgskonto steht das Abgangsergebnis."""
        c = self._ctx(nb)
        gewinn = nb.ist_gewinn
        ergebnis = abs(nb.ergebnis)
        bestand = self._bestand(nb)
        bank = self._bank(nb)

        if nb.klasse == "fonds":
            k_ergebnis = self._fonds("abgang_gewinn" if gewinn else "abgang_verlust", nb)
            k_kosten = self._fonds("veraeusserungskosten", nb)
        else:
            k_ergebnis = self.m.erfolg(nb.klasse, "abgang_gewinn" if gewinn else "abgang_verlust", c)
            k_kosten = None

        buchungen: List[Buchung] = []
        if gewinn:
            # Bank an Bestand über den Buchwert, Bank an Ergebnis über den Gewinn
            if nb.buchwert > NULL:
                buchungen.append(self._b(nb, nb.buchwert, bank, bestand,
                                         self._text("verkauf_abgang", nb), "Buchwertabgang"))
            if ergebnis > NULL:
                buchungen.append(self._b(nb, ergebnis, bank, k_ergebnis,
                                         self._text("verkauf_ergebnis", nb),
                                         "Abgangsergebnis (Gewinn)"))
        else:
            # Bank an Bestand über den Erlös, Verlustkonto an Bestand über den Verlust
            if nb.erloes_brutto > NULL:
                buchungen.append(self._b(nb, nb.erloes_brutto, bank, bestand,
                                         self._text("verkauf_abgang", nb), "Erlösanteil"))
            if ergebnis > NULL:
                buchungen.append(self._b(nb, ergebnis, k_ergebnis, bestand,
                                         self._text("verkauf_ergebnis", nb),
                                         "Abgangsergebnis (Verlust)"))

        if nb.gebuehren_summe > NULL:
            if k_kosten:
                buchungen.append(self._b(nb, nb.gebuehren_summe, k_kosten, bank,
                                         self._text("verkauf_gebuehren", nb),
                                         "Veräußerungskosten"))
            else:
                # Anleihen und Derivate haben kein eigenes Kostenkonto —
                # die Kosten mindern das Abgangsergebnis.
                buchungen.append(self._b(nb, nb.gebuehren_summe, k_ergebnis, bank,
                                         self._text("verkauf_gebuehren", nb),
                                         "Veräußerungskosten im Ergebnis"))
        return buchungen

    # ── Erträge ───────────────────────────────────────────────────────────
    def _ertrag(self, nb: NormBeleg, ertragskonto: str, text_key: str,
                steuer_key: str) -> List[Buchung]:
        bank = self._bank(nb)
        buchungen = [self._b(nb, nb.ausmachender_betrag, bank, ertragskonto,
                             self._text(text_key, nb), "Ertrag netto")]

        steuer = nb.kapitalertragsteuer + nb.soli
        if steuer > NULL:
            # KapESt und SolZ liegen in der Matrix auf getrennten Konten.
            if nb.kapitalertragsteuer > NULL:
                buchungen.append(self._b(nb, nb.kapitalertragsteuer,
                                         self._gem("kapest", nb), ertragskonto,
                                         self._text(steuer_key, nb), "KapESt",
                                         stueck=NULL))
            if nb.soli > NULL:
                buchungen.append(self._b(nb, nb.soli, self._gem("solz", nb), ertragskonto,
                                         self._text(steuer_key, nb), "SolZ", stueck=NULL))
            if nb.kapitalertragsteuer == NULL and nb.soli == NULL:
                buchungen.append(self._b(nb, steuer, self._gem("kapest", nb), ertragskonto,
                                         self._text(steuer_key, nb),
                                         "KapESt+SolZ", stueck=NULL))

        if nb.quellensteuer_eur > NULL:
            buchungen.append(self._b(
                nb, nb.quellensteuer_eur, self._gem("quellensteuer_anrechenbar", nb),
                ertragskonto, self._text("dividende_quellensteuer", nb),
                "Anrechenbare Quellensteuer", stueck=NULL))
        return buchungen

    def dividende(self, nb: NormBeleg) -> List[Buchung]:
        # Der Marker #DIV# wird in der Klassifizierung gesetzt, nicht hier —
        # die Engine darf die Belege nicht verändern, sonst verdoppeln sich
        # Marker bei einem zweiten Lauf (z. B. Vergleich SKR03/SKR04).
        konto = self.m.erfolg("aktie", "dividende", self._ctx(nb))
        return self._ertrag(nb, konto, "dividende", "dividende_steuer")

    def ausschuettung(self, nb: NormBeleg) -> List[Buchung]:
        konto = self._fonds("ausschuettung", nb)
        return self._ertrag(nb, konto, "ausschuettung", "ausschuettung_steuer")

    def kupon(self, nb: NormBeleg) -> List[Buchung]:
        """Kupon einer Anleihe. Zuerst werden die beim Kauf aktivierten
        Stückzinsen aufgelöst, der Rest ist Zinsertrag."""
        c = self._ctx(nb)
        bank = self._bank(nb)
        k_zins = self.m.erfolg("anleihe", "zinsertrag", c)
        k_stueck = self.m.erfolg("anleihe", "stueckzinsen_aktiv", c)
        buchungen: List[Buchung] = []

        offen = nb.stueckzinsen
        rest = nb.ausmachender_betrag
        if offen > NULL:
            aufloesung = min(offen, rest)
            buchungen.append(self._b(nb, aufloesung, bank, k_stueck,
                                     self._text("stueckzinsen_aufloesung", nb),
                                     "Auflösung Stückzinsen", stueck=NULL))
            rest -= aufloesung
        if rest > NULL:
            buchungen.append(self._b(nb, rest, bank, k_zins,
                                     self._text("kupon", nb), "Zinsertrag"))
        buchungen.extend(self._ertrag_steuern(nb, k_zins))
        return buchungen

    def _ertrag_steuern(self, nb: NormBeleg, ertragskonto: str) -> List[Buchung]:
        out = []
        if nb.kapitalertragsteuer > NULL:
            out.append(self._b(nb, nb.kapitalertragsteuer, self._gem("kapest", nb),
                               ertragskonto, self._text("dividende_steuer", nb),
                               "KapESt", stueck=NULL))
        if nb.soli > NULL:
            out.append(self._b(nb, nb.soli, self._gem("solz", nb), ertragskonto,
                               self._text("dividende_steuer", nb), "SolZ", stueck=NULL))
        return out

    def stueckzinsen_kauf(self, nb: NormBeleg) -> List[Buchung]:
        """Beim Anleihenkauf gezahlte Stückzinsen werden aktiviert, nicht
        sofort gegen den Zinsertrag gebucht. Ohne Abgrenzung wandert der
        Zinsertrag über den Bilanzstichtag ins falsche Jahr."""
        if nb.stueckzinsen <= NULL:
            return []
        k = self.m.erfolg("anleihe", "stueckzinsen_aktiv", self._ctx(nb))
        return [self._b(nb, nb.stueckzinsen, k, self._bank(nb),
                        self._text("stueckzinsen_gezahlt", nb),
                        "Gezahlte Stückzinsen", stueck=NULL)]

    # ── Laufende Posten ───────────────────────────────────────────────────
    def einfach(self, nb: NormBeleg, zweck: str, text_key: str,
                richtung: str = "aufwand") -> List[Buchung]:
        konto = self._gem(zweck, nb)
        bank = self._bank(nb)
        text = self.t.get(text_key, text_key).format(
            marker="", bezeichnung=kuerzen(nb.bezeichnung, 40), isin=nb.isin).strip()
        if richtung == "aufwand":
            return [self._b(nb, nb.ausmachender_betrag, konto, bank, text, zweck,
                            stueck=NULL)]
        buchungen = [self._b(nb, nb.ausmachender_betrag, bank, konto, text, zweck,
                             stueck=NULL)]
        buchungen.extend(self._ertrag_steuern(nb, konto))
        return buchungen

    # ── Vorabpauschale ────────────────────────────────────────────────────
    def vorabpauschale_bildung(self, v: Vorabpauschale, depot_index: int = 1) -> List[Buchung]:
        """Steuerstapel: aktiver Ausgleichsposten an Ertrag.
        Handelsrechtlich ist die Vorabpauschale kein Geschäftsvorfall."""
        c = KontenKontext(self.ctx.kontenrahmen, self.ctx.vermoegensart,
                          depot_index, self.ctx.sachkontenlaenge)
        ap = self.m.fonds("ausgleichsposten_aktiv", None, c)
        ertrag = self.m.fonds("vorabpauschale_ertrag", None, c)
        text = self.t.get("vorabpauschale_bildung", "Vorabpauschale {jahr} {isin}").format(
            marker="", jahr=v.jahr, isin=v.isin,
            bezeichnung=kuerzen(v.bezeichnung, 20)).strip()
        return [Buchung(
            umsatz=round2(v.betrag), soll_haben="S", konto=ap, gegenkonto=ertrag,
            belegdatum=v.datum or date(v.jahr, 12, 31),
            belegfeld_1=f"VP{v.jahr}", belegfeld_2="",
            buchungstext=text[: self.text_max], isin=v.isin, wkn="",
            stueck=NULL, kategorie="Vorabpauschale Bildung",
            stapel="steuerrecht",
        )]

    def vorabpauschale_steuer(self, nb: NormBeleg) -> List[Buchung]:
        """Hauptstapel: der tatsächliche Steuerabfluss. Bisher lief er auf
        1780 — das ist im SKR 04 das LZB-Guthaben."""
        return [self._b(nb, nb.ausmachender_betrag, self._gem("kapest", nb),
                        self._bank(nb),
                        self._text("vorabpauschale_bildung", nb),
                        "Vorabpauschale Steuerabfluss", stueck=NULL)]


# ───────────────────────────────────────────────────────────────────────────
# Dispatcher
# ───────────────────────────────────────────────────────────────────────────
def belege_zu_buchungen_v5(
    belege: List[NormBeleg],
    matrix: Kontenmatrix,
    ctx: KontenKontext,
    texte: Dict[str, str],
    options: Optional[dict] = None,
    vorabpauschalen: Optional[List[Vorabpauschale]] = None,
) -> BuchungsErgebnis:
    """Erwartet normalisierte, klassifizierte und bewertete Belege."""
    eng = Buchungsengine(matrix, ctx, texte, options)
    erg = BuchungsErgebnis(vorabpauschalen=list(vorabpauschalen or []))

    for nb in sorted(belege, key=lambda b: (b.schlusstag, b.auftragsnummer)):
        try:
            erg.hauptstapel.extend(_eine_gruppe(eng, nb, erg))
        except KontoNichtDefiniert as e:
            erg.ungebucht.append(UngebuchterBeleg(
                typ=nb.typ, datum=nb.schlusstag, betrag=nb.ausmachender_betrag,
                isin=nb.isin, bezeichnung=nb.bezeichnung, seite=nb.seite,
                grund=f"Kein Konto hinterlegt: {e}",
                empfehlung="Kontonummer in config/konten.yaml ergänzen"))

    for v in erg.vorabpauschalen:
        if v.betrag and v.betrag > NULL:
            erg.steuerstapel.extend(eng.vorabpauschale_bildung(v))

    verworfen = _injiziere_marker(erg.alle, belege)
    if verworfen:
        erg.hinweise.append(
            f"{len(verworfen)} Marker wegen des DATEV-Zeichenlimits nicht im "
            f"Buchungstext: " + "; ".join(verworfen[:10]))

    _pruefe_summen(erg)
    return erg


def _eine_gruppe(eng: Buchungsengine, nb: NormBeleg,
                 erg: BuchungsErgebnis) -> List[Buchung]:
    t = nb.typ

    if nb.klasse == "nicht_abbildbar":
        erg.ungebucht.append(UngebuchterBeleg(
            typ=t, datum=nb.schlusstag, betrag=nb.ausmachender_betrag,
            isin=nb.isin, bezeichnung=nb.bezeichnung, seite=nb.seite,
            grund="Option, Future oder CFD",
            empfehlung="Stillhalterprämien laufen über sonstige "
                       "Verbindlichkeiten, Margin über sonstige "
                       "Vermögensgegenstände, zum Stichtag ggf. "
                       "Drohverlustrückstellung. Manuell erfassen."))
        return []

    if t == "KAUF":
        out = eng.kauf(nb)
        out.extend(eng.stueckzinsen_kauf(nb))
        return out

    if t in ("VERKAUF", "KAPITALMASSNAHME"):
        buchungen, ungebucht = eng.verkauf(nb)
        erg.ungebucht.extend(ungebucht)
        return buchungen

    if t == "DIVIDENDE":
        return eng.dividende(nb)

    if t == "FONDSERTRAG":
        return eng.ausschuettung(nb)

    if t == "KUPON":
        return eng.kupon(nb)

    if t == "VERWAHRENTGELT":
        return eng.einfach(nb, "verwahrentgelt", "verwahrentgelt")

    if t == "GEBUEHR":
        return eng.einfach(nb, "nebenkosten_geldverkehr", "nebenkosten")

    if t == "ZINSGUTSCHRIFT":
        return eng.einfach(nb, "zinsertrag_sonstige", "zinsgutschrift", "ertrag")

    if t == "ZINSAUFWAND":
        return eng.einfach(nb, "zinsaufwand", "zinsaufwand")

    if t == "VORABPAUSCHALE_STEUER":
        return eng.vorabpauschale_steuer(nb)

    if t == "FTT":
        # Die Finanztransaktionssteuer ist aktivierungspflichtig und im
        # ausmachenden Betrag des Kaufs bereits enthalten. Ein eigener Beleg
        # würde sie ein zweites Mal erfassen.
        erg.hinweise.append(
            f"FTT-Beleg {nb.auftragsnummer} ({nb.isin}) übersprungen — die "
            f"Steuer ist als Anschaffungsnebenkosten im Kauf enthalten.")
        return []

    erg.ungebucht.append(UngebuchterBeleg(
        typ=t, datum=nb.schlusstag, betrag=nb.ausmachender_betrag,
        isin=nb.isin, bezeichnung=nb.bezeichnung, seite=nb.seite,
        grund=f"Belegtyp '{t}' wird nicht automatisch gebucht",
        empfehlung="Manuelle Prüfung durch die Kanzlei"))
    return []


def _injiziere_marker(buchungen: List[Buchung], belege: List[NormBeleg]) -> List[str]:
    """Setzt die Marker als Präfix in den Buchungstext.

    Marker dürfen nicht in der Wertpapierbezeichnung stehen, weil die auf
    `kuerze_bezeichnung_auf` gekürzt wird und der Marker dabei verloren ginge.
    """
    je_auftrag: Dict[str, List[str]] = {}
    for nb in belege:
        if nb.marker:
            je_auftrag.setdefault(nb.auftragsnummer, []).extend(nb.marker)

    verworfen: List[str] = []
    for bk in buchungen:
        mk = je_auftrag.get(bk.belegfeld_1)
        if not mk:
            continue
        offen = []
        for m in mk:
            if m not in bk.buchungstext and m not in offen:
                offen.append(m)
        offen.sort(key=lambda m: MARKER_PRIO.index(m) if m in MARKER_PRIO else 99)

        # Marker haben Vorrang vor dem Wertpapiernamen. Passt beides nicht in
        # die 60 Zeichen, wird der Text gekürzt, nicht der Marker verworfen —
        # ein weggefallenes #AK-PRÜFEN# ist genau der stille Fehler, den die
        # Marker verhindern sollen. Erst wenn die Marker allein das Limit
        # sprengen, fällt der letzte weg.
        while offen and len(" ".join(offen)) > 60:
            verworfen.append(f"{bk.belegfeld_1}: {offen[-1]} (Zeichenlimit)")
            offen.pop()
        if offen:
            praefix = " ".join(offen)
            rest = 60 - len(praefix) - 1
            text = bk.buchungstext[:rest].rstrip() if rest > 0 else ""
            bk.buchungstext = f"{praefix} {text}".strip()[:60]
    return verworfen


def _pruefe_summen(erg: BuchungsErgebnis) -> None:
    """Jede Buchung ist einseitig mit Konto und Gegenkonto erfasst, deshalb
    gleicht sich der Stapel je Definition aus. Geprüft wird stattdessen, ob
    Beträge plausibel sind — Nullbuchungen und negative Umsätze deuten auf
    einen Parserfehler hin."""
    for name, stapel in (("Hauptstapel", erg.hauptstapel),
                         ("Steuerstapel", erg.steuerstapel)):
        null = [b for b in stapel if b.umsatz == NULL]
        negativ = [b for b in stapel if b.umsatz < NULL]
        if null:
            erg.hinweise.append(
                f"{name}: {len(null)} Buchung(en) mit Betrag 0 — entfernt.")
            stapel[:] = [b for b in stapel if b.umsatz != NULL]
        if negativ:
            erg.hinweise.append(
                f"{name}: {len(negativ)} Buchung(en) mit negativem Betrag. "
                f"DATEV erwartet positive Umsätze mit Soll/Haben-Kennzeichen — "
                f"bitte den zugrunde liegenden Beleg prüfen.")

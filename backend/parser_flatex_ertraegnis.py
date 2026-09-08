"""
parser_flatex_ertraegnis.py — Parser für die Flatex "Erträgnisaufstellung"
(Jahresdokument, PDF).

Warum ein eigener Parser
------------------------
Die Erträgnisaufstellung liefert den A-Wert (Anschaffungswert) roh und
korrekt. In den Einzelabrechnungen muss der A-Wert bei Fonds/ETFs aus dem
bereits mit 30 % Teilfreistellung verrechneten G/V zurückgerechnet werden —
das erzeugt Fehler von mehreren hundert Euro je Position. Verifizierte
Formel der Bank:

    Bruttoertrag = (V-Wert − A-Wert − Kosten) × (1 − TF_Bank)

Für die GmbH gilt bei Aktienfonds 80 % TF, nicht 30 %. Wir ignorieren den
Bruttoertrag der Bank deshalb vollständig und rechnen selbst aus
A-Wert / V-Wert / Kosten.

Layout
------
Entgegen der ursprünglichen Annahme ist das Dokument NICHT zeichenweise
festbreitig — `pdftotext -layout` liefert je nach Zeileninhalt
unterschiedliches Spacing. Verlässlich ist dagegen das Koordinatenraster:
6 rechtsbündige Wertspalten, jede mit einem konstanten "EUR"-Anker.
Der Zahlenwert steht immer unmittelbar links davon.

    Spalte:      0      1      2      3      4      5
    EUR x1:    161    277    394    510    626    749

    Zeile 1:  TA-Nr./Art | ISIN | WP-Bezeichnung |        Stücke/Nominale
    Zeile 2:  Datum K | Datum V/Z | A-Wert(2) | V-Wert(3) |     Kosten(5)
    Zeile 3:  Bruttoertrag(0) KapE-Inland(1) TEV_I(2) REIT_I(3) Zins*(4) Zins**(5)
    Zeile 4:  Termin.(0) KapE-Ausland(1) TEV_A(2) REIT_A(3) Fonds*(4) Fonds**(5)
    Zeile 5:  EBG(0) §27KStG(1) KapE-VG(2) TEV_VG(3) KESt(4) SolZ(5)

Das Raster wird beim Einlesen gegen die Kopfzeile validiert, damit ein
Layoutwechsel der Bank sofort auffällt statt still falsch zu parsen.
"""

import re
from dataclasses import dataclass
from decimal import Decimal
from datetime import date
from typing import List, Tuple, Optional, Dict

import pdfplumber

from flatex_jahr_types import Beleg, Tranche, IgnoredPage, UngebuchterBeleg
from depot_registry import DepotRegistry


# ── Rasterkonstanten ────────────────────────────────────────────
EUR_ANKER = [161.0, 277.0, 394.0, 510.0, 626.0, 749.0]
ANKER_TOLERANZ = 6.0
ZEILEN_JE_SATZ = 5

ISIN_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}\d$")

# ── Vorabpauschale ──────────────────────────────────────────────
# Bewusst NICHT als Ertrag gebucht und auch NICHT gewinnmindernd verrechnet.
#
# Handelsrechtlich sind Anschaffungskosten in § 255 HGB abschließend definiert
# (Kaufpreis + Anschaffungsnebenkosten). Die Vorabpauschale ist eine
# Steuerzahlung, keine Nebenkosten — sie darf die AK nicht erhöhen. Die
# Gewinnminderung nach § 17 InvStG ist eine rein steuerliche Korrektur und
# gehört in die Überleitungsrechnung, nicht in den laufenden Buchungsstapel.
#
# Gebucht wird deshalb nur der tatsächliche Steuerabfluss (1780 an Bank) aus
# den Kontoumsätzen. Betroffene Verkäufe erhalten stattdessen den Marker
# #VORABP#, und das Protokoll weist die Beträge je ISIN aus, damit der
# Steuerberater sie in der Steuererklärung berücksichtigen kann.
#
# OFFEN (Frage an die Steuerberaterin): Über Jahre kumulierte Vorabpauschalen.
# Ein Verkauf in 2027 müsste die Vorabpauschalen aus 2025 und 2026 mindern —
# das Jahresdokument 2027 kennt diese aber nicht. Ohne mandantenbezogene
# Historie ist das aus einem Einzeljahr grundsätzlich nicht ableitbar.


@dataclass
class Vorabpauschale:
    """Eine Vorabpauschale aus der Erträgnisaufstellung."""
    isin: str
    bezeichnung: str
    datum: Optional[date]
    betrag: Decimal          # fiktiver Ertrag (mindert § 17 InvStG den VG)
    kest: Decimal
    solz: Decimal
    depot: Optional[str]
    tanr: str

    @property
    def steuer(self) -> Decimal:
        return self.kest + self.solz
TANR_RE = re.compile(r"^(\d{9,12})/(.*)$")
BETRAG_RE = re.compile(r"^-?[\d.]*\d,\d{2}$")
DATUM_RE = re.compile(r"^\d{2}\.\d{2}\.\d{4}$")

# Termingeschäfte i. S. § 15 Abs. 4 S. 3 EStG (Verlustverrechnungsbeschränkung)
TERMIN_RE = re.compile(
    r"\b(TURBO[CL]?|MINIL|FAKTL|KO\b|CALL|PUT|DISCOUNT|BONUS)\b", re.IGNORECASE
)


# ── Helper ──────────────────────────────────────────────────────
def _dec(s: str) -> Optional[Decimal]:
    s = (s or "").strip().replace(".", "").replace(",", ".")
    if not s:
        return None
    try:
        return Decimal(s)
    except Exception:
        return None


def _ddmmyyyy(s: str) -> Optional[date]:
    if not DATUM_RE.match(s or ""):
        return None
    d, m, y = s.split(".")
    return date(int(y), int(m), int(d))


def _spalte(x1: float) -> Optional[int]:
    for i, anker in enumerate(EUR_ANKER):
        if abs(x1 - anker) < ANKER_TOLERANZ:
            return i
    return None


def ist_ertraegnisaufstellung(pdf_pfad: str) -> bool:
    """Erkennung für den Dispatcher in run.py."""
    try:
        with pdfplumber.open(pdf_pfad) as pdf:
            txt = (pdf.pages[0].extract_text() or "")
            return "ERTRÄGNISAUFSTELLUNG" in txt.upper() and "flatex" in txt.lower()
    except Exception:
        return False


# ── Zeilenauswertung ────────────────────────────────────────────
def _werte_der_zeile(worte: List[dict]) -> Dict[int, Optional[Decimal]]:
    """Liest die 6 Wertspalten einer Zeile über die EUR-Anker aus.
    Leere Spalten (nur 'EUR') liefern None."""
    werte: Dict[int, Optional[Decimal]] = {}
    for j, w in enumerate(worte):
        if w["text"] != "EUR":
            continue
        spalte = _spalte(w["x1"])
        if spalte is None:
            continue
        wert = None
        if j > 0:
            vor = worte[j - 1]
            if BETRAG_RE.match(vor["text"]) and vor["x1"] < w["x0"]:
                wert = _dec(vor["text"])
        werte[spalte] = wert
    return werte


def _zeilen(page) -> List[Tuple[float, List[dict]]]:
    gruppen: Dict[float, List[dict]] = {}
    for w in page.extract_words():
        gruppen.setdefault(round(w["top"], 0), []).append(w)
    return [(t, sorted(v, key=lambda x: x["x0"])) for t, v in sorted(gruppen.items())]


def _kopf_pruefen(zeilen) -> bool:
    """Validiert das Raster gegen die Spaltenüberschriften."""
    for _, worte in zeilen:
        texte = [w["text"] for w in worte]
        if "Transaktions-Nr./-art" in texte and "ISIN" in texte:
            return True
    return False


# ── Rohsatz aus dem PDF ─────────────────────────────────────────
class _Rohsatz:
    __slots__ = ("seite", "tanr", "art", "isin", "wp", "stueck", "datum_k",
                 "datum_vz", "a_wert", "v_wert", "kosten", "bruttoertrag",
                 "kap_inland", "kap_ausland", "kap_vg", "fonds2", "kest",
                 "solz", "storno_ta", "datum_k_diverse", "ertr_27")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))


def _lies_rohsaetze(pdf_pfad: str) -> Tuple[List[_Rohsatz], List[IgnoredPage]]:
    rohe: List[_Rohsatz] = []
    ignoriert: List[IgnoredPage] = []

    with pdfplumber.open(pdf_pfad) as pdf:
        for seite_nr, page in enumerate(pdf.pages, start=1):
            zeilen = _zeilen(page)
            hat_kopf = _kopf_pruefen(zeilen)

            i = 0
            gefunden_auf_seite = 0
            while i < len(zeilen):
                worte = zeilen[i][1]
                if not worte:
                    i += 1
                    continue
                m = TANR_RE.match(worte[0]["text"])
                if not m:
                    i += 1
                    continue
                if not hat_kopf:
                    ignoriert.append(IgnoredPage(
                        seite_nr, "LAYOUT",
                        "Datensatz ohne gültige Spaltenüberschrift gefunden — "
                        "Layout der Bank möglicherweise geändert"))
                    break
                if i + ZEILEN_JE_SATZ > len(zeilen):
                    ignoriert.append(IgnoredPage(
                        seite_nr, "ABGESCHNITTEN",
                        f"Datensatz {m.group(1)} unvollständig (Seitenende)"))
                    break

                block = [zeilen[i + k][1] for k in range(ZEILEN_JE_SATZ)]
                rohe.append(_baue_rohsatz(seite_nr, m, block))
                gefunden_auf_seite += 1
                i += ZEILEN_JE_SATZ

            if gefunden_auf_seite == 0 and hat_kopf:
                ignoriert.append(IgnoredPage(
                    seite_nr, "LEER", "Seite mit Kopf, aber ohne Datensätze"))

    return rohe, ignoriert


def _baue_rohsatz(seite_nr: int, m, block) -> _Rohsatz:
    kopf = block[0]
    tanr, rest_art = m.group(1), m.group(2)

    # ISIN in der Kopfzeile finden
    isin, isin_idx = None, None
    for j, w in enumerate(kopf):
        if ISIN_RE.match(w["text"]):
            isin, isin_idx = w["text"], j
            break

    # Art = Text zwischen TA-Nr. und ISIN
    art_teile = [rest_art] + [w["text"] for w in kopf[1:isin_idx]] \
        if isin_idx else [rest_art]
    art = " ".join(t for t in art_teile if t).strip()

    # Storno-Verkettung: "Storno 4100720642 Verkauf"
    storno_ta = None
    sm = re.match(r"Storno\s+(\d{9,12})", art)
    if sm:
        storno_ta = sm.group(1)

    # WP-Bezeichnung + Stück/Nominale
    wp_worte, stueck = [], None
    if isin_idx is not None:
        rest = kopf[isin_idx + 1:]
        st_idx = None
        for j, w in enumerate(rest):
            if w["text"] == "St." and j > 0:
                stueck = _dec(rest[j - 1]["text"])
                st_idx = j - 1
                break
        if st_idx is None and rest and BETRAG_RE.match(rest[-1]["text"]):
            # Nominale ohne "St."-Einheit (z. B. bei Dividenden)
            stueck = _dec(rest[-1]["text"])
            st_idx = len(rest) - 1
        wp_worte = [w["text"] for w in (rest[:st_idx] if st_idx is not None else rest)]

    # Zeile 2: Daten + A/V/Kosten
    z2 = block[1]
    datum_tokens = [w["text"] for w in z2
                    if DATUM_RE.match(w["text"]) or w["text"] == "Diverse"]
    datum_k = datum_vz = None
    diverse = False
    if len(datum_tokens) >= 2:
        datum_k = datum_tokens[0]
        datum_vz = datum_tokens[-1]
    elif len(datum_tokens) == 1:
        datum_vz = datum_tokens[0]
    if datum_k == "Diverse":
        diverse, datum_k = True, None

    v2 = _werte_der_zeile(z2)
    v3 = _werte_der_zeile(block[2])
    v4 = _werte_der_zeile(block[3])
    v5 = _werte_der_zeile(block[4])

    return _Rohsatz(
        seite=seite_nr, tanr=tanr, art=art, isin=isin,
        wp=" ".join(wp_worte).strip(), stueck=stueck,
        datum_k=_ddmmyyyy(datum_k) if datum_k else None,
        datum_vz=_ddmmyyyy(datum_vz) if datum_vz else None,
        datum_k_diverse=diverse,
        a_wert=v2.get(2), v_wert=v2.get(3), kosten=v2.get(5),
        bruttoertrag=v3.get(0), kap_inland=v3.get(1),
        kap_ausland=v4.get(1), fonds2=v4.get(5),
        kap_vg=v5.get(2), kest=v5.get(4), solz=v5.get(5),
        ertr_27=v5.get(1),
        storno_ta=storno_ta,
    )


# ── Depot-Resolver ──────────────────────────────────────────────
TA_FENSTER = 15   # empirisch: Offsets +6..+11 bei Verkäufen, 0 bei Erträgen
CENT = Decimal("0.02")


def _loese_depot(
    roh: _Rohsatz,
    ta_index: Dict[int, dict],
    isin_depots: Dict[str, set],
    registry: DepotRegistry,
) -> Tuple[Optional[str], str]:
    """
    Ordnet einen PDF-Datensatz einem Unterdepot zu.

    Kette (erste greifende Regel gewinnt):
      1. einzeldepot        — nur ein Depot vorhanden, Zuordnung trivial
      2. ta-exakt           — TA-Nr. steht 1:1 in den Kontoumsätzen
                              (gilt für Dividenden, Ausschüttungen,
                               Vorabpauschalen)
      3. ta-fenster         — nächsthöhere TA-Nr. im Fenster, eindeutig
                              (gilt für Verkäufe: Offset +6..+11)
      4. ta-fenster+betrag  — mehrere Kandidaten, aber genau einer passt
                              betragsmäßig zum V-Wert
      5. isin-eindeutig     — ISIN kommt nur in einem Depot vor
      6. unbestimmt         — Marker #DEPOT-PRÜFEN#
    """
    ta = int(roh.tanr)

    if not registry.ist_multidepot:
        # Nur EIN Depot bekannt — die Zuordnung ist trivial, aber nur dann
        # belastbar, wenn der Vorgang auch wirklich in dessen Kontoumsätzen
        # auftaucht. Fehlt er dort, liegt der Verdacht nahe, dass der Kunde
        # den Export eines weiteren Unterdepots vergessen hat. Dann würde eine
        # stille Zuordnung den Vorgang ins falsche Depot buchen.
        einziges = registry.alle()
        name = einziges[0].name if einziges else None
        if not ta_index:
            return name, "einzeldepot"          # gar keine CSV — separat gewarnt
        bekannt = ta in ta_index or any(
            0 < k - ta <= TA_FENSTER for k in ta_index)
        return name, ("einzeldepot" if bekannt else "einzeldepot-ohne-beleg")

    # 2 — exakter Treffer
    treffer = ta_index.get(ta)
    if treffer:
        return treffer["depot"], "ta-exakt"

    # 3/4 — Fenster nach oben
    kandidaten = [v for k, v in ta_index.items() if 0 < k - ta <= TA_FENSTER]
    if roh.isin:
        nach_isin = [c for c in kandidaten if c["isin"] == roh.isin]
        if nach_isin:
            kandidaten = nach_isin

    if kandidaten:
        depots = {c["depot"] for c in kandidaten}
        if len(depots) == 1:
            return kandidaten[0]["depot"], "ta-fenster"

        # mehrdeutig → über den Betrag entscheiden
        if roh.v_wert is not None:
            passend = [c for c in kandidaten
                       if abs(abs(c["betrag"]) - abs(roh.v_wert)) <= CENT]
            if len({c["depot"] for c in passend}) == 1:
                return passend[0]["depot"], "ta-fenster+betrag"

    # 5 — ISIN-Eindeutigkeit
    if roh.isin:
        depots = isin_depots.get(roh.isin, set())
        if len(depots) == 1:
            return next(iter(depots)), "isin-eindeutig"

    return None, "unbestimmt"


# ── Hauptfunktion ───────────────────────────────────────────────
def parse_pdf(
    pdf_pfad: str,
    ta_index: Optional[Dict[int, dict]] = None,
    registry: Optional[DepotRegistry] = None,
) -> Tuple[List[Beleg], List[UngebuchterBeleg], List[IgnoredPage],
           Dict[str, str], List["Vorabpauschale"]]:
    """
    Parst die Erträgnisaufstellung.

    ta_index/registry stammen aus parser_flatex_kontoumsaetze.parse_csvs().
    Ohne sie ist keine Depot-Zuordnung und keine korrekte AK-Ableitung
    möglich — beides wird dann mit Markern gekennzeichnet.

    Rückgabe: (belege, ungebucht, ignoriert, isin_namen, vorabpauschalen)
    """
    ta_index = ta_index or {}
    registry = registry or DepotRegistry()
    if not registry.anzahl:
        registry.erfasse("", "")   # Einzeldepot-Fallback

    rohe, ignoriert = _lies_rohsaetze(pdf_pfad)

    # ISIN → Depots (für Fallback 5) und ISIN → Name (für CSV-Belege)
    isin_depots: Dict[str, set] = {}
    for eintrag in ta_index.values():
        if eintrag["isin"]:
            isin_depots.setdefault(eintrag["isin"], set()).add(eintrag["depot"])
    isin_namen: Dict[str, str] = {
        r.isin: r.wp for r in rohe if r.isin and r.wp
    }

    # Stornierte Sätze ermitteln: Storno hebt Original auf, beide entfallen
    storniert = {r.storno_ta for r in rohe if r.storno_ta}
    storno_saetze = {r.tanr for r in rohe if r.storno_ta}

    belege: List[Beleg] = []
    ungebucht: List[UngebuchterBeleg] = []

    # Durchlauf 1 — Vorabpauschalen sammeln. Muss vor den Verkäufen laufen,
    # damit betroffene Verkäufe den Marker #VORABP# erhalten können.
    vorabpauschalen: List[Vorabpauschale] = []
    for roh in rohe:
        if not (roh.art or "").lower().startswith("vorabpauschale"):
            continue
        if roh.tanr in storniert or roh.tanr in storno_saetze:
            continue
        depot, _ = _loese_depot(roh, ta_index, isin_depots, registry)
        vorabpauschalen.append(Vorabpauschale(
            isin=roh.isin or "", bezeichnung=roh.wp or "",
            datum=roh.datum_vz, betrag=roh.bruttoertrag or Decimal("0"),
            kest=roh.kest or Decimal("0"), solz=roh.solz or Decimal("0"),
            depot=depot, tanr=roh.tanr))

    # Durchlauf 2 — buchbare Vorgänge
    for roh in rohe:
        if roh.tanr in storniert or roh.tanr in storno_saetze:
            ungebucht.append(UngebuchterBeleg(
                seite=roh.seite, typ="STORNO", isin=roh.isin,
                bezeichnung=roh.wp or "", betrag=roh.v_wert,
                grund=f"Storno-Paar (TA {roh.tanr}) — hebt sich auf, "
                      "Ersatzbuchung wird separat erfasst"))
            continue

        depot, quelle = _loese_depot(roh, ta_index, isin_depots, registry)
        art = (roh.art or "").lower()

        if art.startswith("verkauf"):
            belege.append(_verkauf(roh, depot, quelle, ta_index, vorabp=vorabpauschalen))

        elif art.startswith("kapitalmaßnahme") or art.startswith("kapitalmassnahme"):
            if roh.a_wert is not None:
                # Knock-out / vorzeitige Fälligkeit → wie Verkauf
                belege.append(_verkauf(roh, depot, quelle, ta_index,
                                       typ="KAPITALMASSNAHME",
                                       vorabp=vorabpauschalen))
            elif roh.ertr_27 is not None:
                # Einlagenrückgewähr aus dem steuerlichen Einlagekonto
                # (§ 27 KStG). Erfolgsneutral: mindert die Anschaffungskosten
                # der Beteiligung, ist KEIN Ertrag. Ohne Kenntnis des
                # Buchwerts der betroffenen Position nicht automatisch
                # buchbar — bewusst als ungebucht ausgewiesen statt still
                # als Fondsertrag zu verbuchen.
                ungebucht.append(UngebuchterBeleg(
                    seite=roh.seite, typ="EINLAGENRUECKGEWAEHR",
                    isin=roh.isin, bezeichnung=roh.wp or "",
                    betrag=roh.ertr_27, depot=depot,
                    grund="Ertrag nach § 27 KStG (Einlagenrückgewähr) — "
                          "erfolgsneutral, mindert die Anschaffungskosten. "
                          "Manuell gegen das Bestandskonto buchen."))
            else:
                belege.append(_ertrag(roh, depot, quelle, "FONDSERTRAG"))

        elif art.startswith("dividende"):
            belege.append(_ertrag(roh, depot, quelle, "DIVIDENDE"))

        elif art.startswith("vorabpauschale"):
            # Bereits in Durchlauf 1 erfasst. Gebucht wird nur der tatsächliche
            # Steuerabfluss aus den Kontoumsätzen (1780 an Bank) — hier kein
            # Beleg, siehe Modulkopf.
            continue

        else:
            ungebucht.append(UngebuchterBeleg(
                seite=roh.seite, typ=(roh.art or "UNBEKANNT")[:30],
                isin=roh.isin, bezeichnung=roh.wp or "",
                betrag=roh.bruttoertrag, depot=depot,
                grund="Vorgangsart der Erträgnisaufstellung nicht automatisch "
                      "buchbar — manuelle Einordnung erforderlich"))

    return belege, ungebucht, ignoriert, isin_namen, vorabpauschalen


# ── Belegkonstruktion ───────────────────────────────────────────
DATEV_TEXT_MAX = 60

# Reihenfolge = Priorität. Bei Platzmangel fallen die hinteren zuerst weg,
# weil die vorderen auf Fehler in der Buchung selbst hinweisen, die hinteren
# nur auf steuerliche Nacharbeit.
MARKER_PRIO = ["#DEPOT-PRÜFEN#", "#AK-PRÜFEN#", "#TERMIN#", "#TF#", "#VORABP#"]


def _marker(roh: _Rohsatz, quelle: str, extra: List[str]) -> List[str]:
    """Marker als PRÄFIX (DATEV-Buchungstext ist auf 60 Zeichen begrenzt —
    ein Suffix würde als erstes abgeschnitten)."""
    marker = list(extra)
    if quelle in ("unbestimmt", "einzeldepot-ohne-beleg"):
        marker.append("#DEPOT-PRÜFEN#")
    if roh.wp and TERMIN_RE.search(roh.wp):
        marker.append("#TERMIN#")   # § 15 Abs. 4 S. 3 EStG, nicht § 8b KStG
    # doppelte entfernen, nach Priorität sortieren
    eindeutig = list(dict.fromkeys(marker))
    return sorted(eindeutig,
                  key=lambda m: MARKER_PRIO.index(m) if m in MARKER_PRIO else 99)


def _buchungstext(marker: List[str], name: str, warnings: List[str]) -> str:
    """Baut den Buchungstext und hält die DATEV-Grenze von 60 Zeichen ein.

    Marker haben Vorrang vor dem Wertpapiernamen — ein abgeschnittener Name
    ist unschön, ein verlorener Marker verdeckt einen Prüfhinweis. Reicht der
    Platz auch für die Marker nicht, werden die nachrangigen verworfen und
    das in den Warnungen des Belegs protokolliert.
    """
    name = (name or "").strip()
    behalten = list(marker)
    while behalten and len(" ".join(behalten)) + 4 > DATEV_TEXT_MAX:
        entfernt = behalten.pop()
        warnings.append(
            f"Marker {entfernt} wegen DATEV-Zeichenlimit nicht im "
            "Buchungstext — siehe Protokoll")
    prefix = " ".join(behalten)
    rest = DATEV_TEXT_MAX - len(prefix) - (1 if prefix else 0)
    if len(name) > rest:
        name = name[:max(rest - 1, 0)].rstrip() + "…"
    return (f"{prefix} {name}".strip() if prefix else name)


def _verkauf(roh, depot, quelle, ta_index, typ="VERKAUF", vorabp=None) -> Beleg:
    """
    Kostenzuordnung
    ---------------
    Die Spalte "Kosten" der Erträgnisaufstellung enthält die Summe aus
    Anschaffungsneben- UND Veräußerungskosten. Für den Buchwertabgang muss
    getrennt werden, weil beim Kauf der volle Betrag auf 1510 aktiviert wurde:

        Veräußerungskosten = V-Wert − |Betrag der Verkaufszeile in der CSV|
        AK (Buchwert)      = A-Wert + Kosten − Veräußerungskosten

    Verifiziert an ZALANDO (DE000ZAL1111): A 623,60 + 15,80 − 7,90 = 631,50
    = exakt der Kaufbetrag der CSV-Zeile. Ohne CSV ist diese Trennung nicht
    möglich → Marker #AK-PRÜFEN#.
    """
    extra: List[str] = []
    v_wert = roh.v_wert or Decimal("0")
    a_wert = roh.a_wert or Decimal("0")
    kosten = roh.kosten or Decimal("0")

    verk_kosten = None
    ta = int(roh.tanr)
    for k, v in ta_index.items():
        if 0 < k - ta <= TA_FENSTER and v["art"] in ("VERKAUF", "KAPITALMASSNAHME") \
                and (not roh.isin or v["isin"] == roh.isin):
            verk_kosten = v_wert - abs(v["betrag"])
            break

    ak_unvollstaendig = False
    if verk_kosten is None or verk_kosten < 0:
        verk_kosten = kosten
        ak_gesamt = a_wert
        ak_unvollstaendig = True
        extra.append("#AK-PRÜFEN#")
    else:
        ak_gesamt = a_wert + kosten - verk_kosten

    netto_erloes = v_wert - verk_kosten
    ist_gewinn = netto_erloes >= ak_gesamt

    if roh.fonds2 is not None or (roh.wp and "ETF" in roh.wp.upper()):
        extra.append("#TF#")

    # #VORABP# — auf diese ISIN wurde im selben Zeitraum Vorabpauschale
    # versteuert. Mindert steuerlich den Veräußerungsgewinn (§ 17 InvStG),
    # wird aber bewusst nicht gebucht (siehe Modulkopf).
    vorabp_treffer = []
    for v in (vorabp or []):
        if not roh.isin or v.isin != roh.isin:
            continue
        if v.depot and depot and v.depot != depot:
            continue
        if v.datum and roh.datum_vz and v.datum > roh.datum_vz:
            continue   # Vorabpauschale nach dem Verkauf — nicht anrechenbar
        vorabp_treffer.append(v)
    if vorabp_treffer:
        extra.append("#VORABP#")

    b = Beleg(
        typ=typ, seite=roh.seite, auftragsnummer=roh.tanr, rechnungsnummer=None,
        datum_dokument=roh.datum_vz or date.today(),
        schlusstag=roh.datum_vz or date.today(),
        isin=roh.isin or "", wkn=None,
        wertpapierbezeichnung="",   # unten gesetzt, s. _buchungstext()
        stueck=roh.stueck or Decimal("0"),
        ausfuehrungskurs=None,
        kurswert=v_wert,
        gebuehren_summe=verk_kosten,
        ausmachender_betrag=netto_erloes,
        tranchen=[Tranche(stueck=roh.stueck or Decimal("0"), ak=ak_gesamt,
                          erloes_ant=netto_erloes, ist_gewinn=ist_gewinn)],
        depot=depot, depot_quelle=quelle,
        veraeusserungskosten=verk_kosten,
        anschaffungskosten_gesamt=ak_gesamt,
        roh_a_wert=roh.a_wert, roh_v_wert=roh.v_wert,
        roh_kosten=roh.kosten, roh_bruttoertrag=roh.bruttoertrag,
        ak_unvollstaendig=ak_unvollstaendig,
        storniert_von=None,
    )
    b.marker = _marker(roh, quelle, extra)
    b.wertpapierbezeichnung = (roh.wp or "").strip()
    if roh.datum_k_diverse:
        b.warnings.append("Kaufdatum 'Diverse' — Position aus mehreren Tranchen")
    if ak_unvollstaendig:
        b.warnings.append(
            "Veräußerungskosten nicht aus Kontoumsätzen ableitbar — "
            "AK entspricht ungetrenntem A-Wert")
    if quelle == "unbestimmt":
        b.warnings.append("Unterdepot nicht eindeutig zuordenbar")
    elif quelle == "einzeldepot-ohne-beleg":
        b.warnings.append(
            "Vorgang fehlt in den Kontoumsätzen des einzigen bekannten Depots "
            "— fehlt der Export eines weiteren Unterdepots?")
    if vorabp_treffer:
        summe = sum(v.betrag for v in vorabp_treffer)
        b.warnings.append(
            f"Vorabpauschale {summe} EUR auf diese ISIN versteuert — mindert "
            "steuerlich den Veräußerungsgewinn (§ 17 InvStG), nicht gebucht")
    return b


def _ertrag(roh, depot, quelle, typ) -> Beleg:
    """Dividende / Fondsausschüttung. Brutto und KESt/SolZ stehen getrennt
    im Dokument, deshalb hier vollständig buchbar."""
    extra = ["#DIV#"] if typ == "DIVIDENDE" else ["#FONDS#"]
    brutto = roh.bruttoertrag or Decimal("0")
    kest = roh.kest or Decimal("0")
    solz = roh.solz or Decimal("0")

    b = Beleg(
        typ=typ, seite=roh.seite, auftragsnummer=roh.tanr, rechnungsnummer=None,
        datum_dokument=roh.datum_vz or date.today(),
        schlusstag=roh.datum_vz or date.today(),
        isin=roh.isin or "", wkn=None,
        wertpapierbezeichnung="",   # unten gesetzt, s. _buchungstext()
        stueck=roh.stueck or Decimal("0"),
        ausfuehrungskurs=None,
        kurswert=brutto, gebuehren_summe=Decimal("0"),
        ausmachender_betrag=brutto - kest - solz,
        kapitalertragsteuer=kest or None, soli=solz or None,
        depot=depot, depot_quelle=quelle,
        roh_bruttoertrag=roh.bruttoertrag,
    )
    b.marker = _marker(roh, quelle, extra)
    b.wertpapierbezeichnung = (roh.wp or "").strip()
    if roh.kap_ausland is not None or (roh.art or "").lower().endswith("ausland"):
        b.warnings.append("Auslandsertrag — Quellensteueranrechnung prüfen")
    if quelle == "unbestimmt":
        b.warnings.append("Unterdepot nicht eindeutig zuordenbar")
    return b

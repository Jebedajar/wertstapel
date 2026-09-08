"""
parser_flatex_kontoumsaetze.py — Parser für Flatex "Kontoumsätze" CSV-Exporte.

Die Erträgnisaufstellung enthält KEINE Käufe. Diese Lücke schließen die
Kontoumsätze. Zusätzlich liefert die CSV:
  - Verwahrentgelt (Xetra Gold)
  - Zinsabschluss (Guthaben-/Sollzinsen)
  - Vorabpauschale (tatsächlicher Steuerabfluss)
  - Depotüberträge zwischen den Unterdepots
  - und — entscheidend — die Depot-Zuordnung je TA-Nr.

Pro Unterdepot wird eine eigene CSV exportiert. Der Parser nimmt deshalb
eine LISTE von Dateien entgegen.

Format (ISO-8859-1, Semikolon-getrennt):
    Buchtag;Valuta;BIC / BLZ;IBAN / Kontonummer;Buchungsinformationen;
    TA-Nr.;Betrag;;Auftraggeberkonto;Konto

Wichtig: Spalte `Konto` ist der Anzeigename des Unterdepots, `Auftraggeberkonto`
die stabile Kontonummer. Für die Registry wird die Kontonummer als Schlüssel
verwendet, weil der Anzeigename vom Kunden umbenannt werden kann.
"""

import csv
import re
from decimal import Decimal
from datetime import date
from typing import List, Tuple, Optional, Dict

from flatex_jahr_types import Beleg, Tranche, UngebuchterBeleg
from depot_registry import DepotRegistry


ENCODING = "iso-8859-1"
ISIN_RE = re.compile(r"\b([A-Z]{2}[A-Z0-9]{9}\d)\b")

ERWARTETE_SPALTEN = {
    "Buchtag", "Valuta", "Buchungsinformationen", "TA-Nr.",
    "Betrag", "Auftraggeberkonto", "Konto",
}


# ── Helper ──────────────────────────────────────────────────────
def _dec(s: str) -> Decimal:
    s = (s or "").strip().replace(".", "").replace(",", ".")
    if not s:
        return Decimal("0")
    try:
        return Decimal(s)
    except Exception:
        return Decimal("0")


def _ddmmyyyy(s: str) -> Optional[date]:
    s = (s or "").strip()
    if not re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", s):
        return None
    d, m, y = s.split(".")
    return date(int(y), int(m), int(d))


def _isin(text: str) -> Optional[str]:
    m = ISIN_RE.search(text or "")
    return m.group(1) if m else None


def ist_flatex_kontoumsaetze(pfad: str) -> bool:
    """Erkennung für den Dispatcher in run.py."""
    try:
        with open(pfad, encoding=ENCODING) as f:
            kopf = f.readline()
    except Exception:
        return False
    felder = {x.strip() for x in kopf.split(";")}
    return ERWARTETE_SPALTEN.issubset(felder)


# ── Klassifikation einer Umsatzzeile ────────────────────────────
def _klassifiziere(info: str, betrag: Decimal) -> str:
    t = info.lower()
    if t.startswith("storno"):
        return "STORNO"
    if "ausführung order kauf" in t:
        return "KAUF"
    if "ausführung order verkauf" in t:
        return "VERKAUF"
    if "verwahrentgelt" in t:
        return "VERWAHRENTGELT"
    if "zinsabschluss" in t:
        return "ZINS"
    if "vorabpauschale" in t:
        return "VORABPAUSCHALE_STEUER"
    if "dividendenzahlung" in t or "erträgnisausschüttung" in t:
        return "ERTRAG"
    if "opt.-recht" in t or "vorz. ko" in t:
        return "KAPITALMASSNAHME"
    if not info.strip():
        return "UEBERTRAG"
    return "SONSTIGE"


# ── Hauptfunktion ───────────────────────────────────────────────
def parse_csvs(
    pfade: List[str],
    registry: Optional[DepotRegistry] = None,
) -> Tuple[List[Beleg], List[UngebuchterBeleg], DepotRegistry, Dict[int, dict]]:
    """
    Liest 1..n Kontoumsätze-CSVs.

    Rückgabe:
      belege     — buchbare Belege (KAUF, VERWAHRENTGELT, ZINS*, VORABPAUSCHALE)
      ungebucht  — erkannt, aber nicht automatisch buchbar
      registry   — befüllte DepotRegistry
      ta_index   — {TA-Nr: {...}} Nachschlagetabelle für den PDF-Resolver.
                   Diese ist der eigentliche Schlüssel zur Depot-Zuordnung
                   der Erträgnisaufstellung.

    Erträge (Dividende/Ausschüttung) werden hier NICHT gebucht — sie stehen
    mit Brutto/KESt/SolZ-Aufteilung in der Erträgnisaufstellung und würden
    sonst doppelt erfasst. Sie landen aber im ta_index.
    """
    registry = registry or DepotRegistry()
    belege: List[Beleg] = []
    ungebucht: List[UngebuchterBeleg] = []
    ta_index: Dict[int, dict] = {}

    for pfad in pfade:
        with open(pfad, encoding=ENCODING, newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for zeile_nr, row in enumerate(reader, start=2):
                info = (row.get("Buchungsinformationen") or "").strip()
                ta_roh = (row.get("TA-Nr.") or "").strip()
                if not ta_roh.isdigit():
                    continue
                ta = int(ta_roh)
                betrag = _dec(row.get("Betrag"))
                depot_name = (row.get("Konto") or "").strip()
                depot_key = (row.get("Auftraggeberkonto") or "").strip()
                buchtag = _ddmmyyyy(row.get("Buchtag"))
                valuta = _ddmmyyyy(row.get("Valuta")) or buchtag
                isin = _isin(info)
                art = _klassifiziere(info, betrag)

                registry.erfasse(depot_key, depot_name)

                ta_index[ta] = dict(
                    ta=ta, art=art, isin=isin, betrag=betrag,
                    depot=depot_name, depot_key=depot_key,
                    buchtag=buchtag, valuta=valuta, info=info,
                )

                # ── Buchbare Vorgänge ───────────────────────────
                if art == "KAUF":
                    belege.append(_kauf_beleg(
                        ta, isin, info, betrag, valuta or buchtag,
                        depot_name, zeile_nr))

                elif art == "VERWAHRENTGELT":
                    # booking_engine stellt "Verwahrentgelt " bereits voran —
                    # hier nur den konkretisierenden Teil liefern, sonst
                    # entsteht "Verwahrentgelt Verwahrentgelt".
                    belege.append(_einfach_beleg(
                        "VERWAHRENTGELT", ta, isin, info, betrag,
                        valuta or buchtag, depot_name, zeile_nr,
                        _detail(info, "Verwahrentgelt", depot_name)))

                elif art == "ZINS":
                    if betrag == 0:
                        continue  # Nullzeile, kein Buchungsstoff
                    typ = "ZINSGUTSCHRIFT" if betrag > 0 else "ZINSAUFWAND"
                    belege.append(_einfach_beleg(
                        typ, ta, isin, info, betrag, valuta or buchtag,
                        depot_name, zeile_nr,
                        _detail(info, "Zinsabschluss", depot_name)))

                elif art == "VORABPAUSCHALE_STEUER":
                    # Konsens: nur den tatsächlichen Steuerabfluss buchen
                    # (1780 an Bank), keinen fiktiven Ertrag.
                    belege.append(_einfach_beleg(
                        "VORABPAUSCHALE_STEUER", ta, isin, info, betrag,
                        valuta or buchtag, depot_name, zeile_nr,
                        "Vorabpauschale Steuer"))

                # ── Bewusst nicht hier gebucht ──────────────────
                elif art in ("VERKAUF", "ERTRAG", "KAPITALMASSNAHME", "STORNO"):
                    # Kommen vollständig (inkl. A-Wert / KESt / SolZ) aus der
                    # Erträgnisaufstellung. Hier nur als Index-Eintrag.
                    continue

                elif art == "UEBERTRAG":
                    ungebucht.append(UngebuchterBeleg(
                        seite=zeile_nr, typ="DEPOTUEBERTRAG", isin=None,
                        bezeichnung=f"Übertrag {row.get('IBAN / Kontonummer','')}".strip(),
                        betrag=betrag, depot=depot_name,
                        grund="Geldübertrag zwischen Konten — Gegenkonto manuell "
                              "zuordnen (ggf. Depot-zu-Depot-Umbuchung)"))

                else:
                    ungebucht.append(UngebuchterBeleg(
                        seite=zeile_nr, typ="SONSTIGE", isin=isin,
                        bezeichnung=info[:60], betrag=betrag, depot=depot_name,
                        grund="Umsatzart aus Kontoumsätzen nicht zuordenbar"))

    return belege, ungebucht, registry, ta_index


# ── Beleg-Konstruktoren ─────────────────────────────────────────
def _kauf_beleg(ta, isin, info, betrag, dat, depot, zeile) -> Beleg:
    """Kauf aus den Kontoumsätzen.

    Achtung: Die CSV liefert NUR den Endbetrag (inkl. aller Gebühren) und die
    ISIN — weder Stückzahl noch Kurs. Für die Buchung 1510 an Bank ist das
    ausreichend (Buchwertabgang-Methode aktiviert ohnehin den vollen Betrag),
    der Buchungstext bleibt aber ohne Stückangabe. Wer Stück+Kurs im Text
    braucht, muss zusätzlich den Depotumsätze-CSV-Export liefern.
    """
    b = Beleg(
        typ="KAUF", seite=zeile, auftragsnummer=str(ta), rechnungsnummer=None,
        datum_dokument=dat, schlusstag=dat, isin=isin or "",
        wkn=None, wertpapierbezeichnung=_wp_name(info, isin),
        stueck=Decimal("0"), ausfuehrungskurs=None,
        kurswert=abs(betrag), gebuehren_summe=Decimal("0"),
        ausmachender_betrag=abs(betrag), depot=depot, depot_quelle="csv-direkt",
    )
    if not isin:
        b.warnings.append("Kauf ohne erkennbare ISIN im Buchungstext")
    b.warnings.append("Stück/Kurs nicht in Kontoumsätzen enthalten")
    return b


def _einfach_beleg(typ, ta, isin, info, betrag, dat, depot, zeile, label) -> Beleg:
    return Beleg(
        typ=typ, seite=zeile, auftragsnummer=str(ta), rechnungsnummer=None,
        datum_dokument=dat, schlusstag=dat, isin=isin or "",
        wkn=None, wertpapierbezeichnung=label,
        stueck=Decimal("0"), ausfuehrungskurs=None,
        kurswert=abs(betrag), gebuehren_summe=Decimal("0"),
        ausmachender_betrag=abs(betrag), depot=depot, depot_quelle="csv-direkt",
    )


def _detail(info: str, praefix_der_engine: str, depot: Optional[str]) -> str:
    """Liefert den konkretisierenden Teil des Buchungstexts.

    booking_engine baut Texte als f"{Label} {bezeichnung}". Würde hier erneut
    das Label stehen, entstünde "Verwahrentgelt Verwahrentgelt". Wir geben
    deshalb den Rest der Buchungsinformation zurück — und bei mehreren
    Depots zusätzlich das Depotkürzel, weil sonst identische Zeilen
    verschiedener Unterdepots im Stapel ununterscheidbar wären.
    """
    rest = (info or "").strip()
    for prefix in (praefix_der_engine, "Zinsabschluss", "Verwahrentgelt"):
        if rest.lower().startswith(prefix.lower()):
            rest = rest[len(prefix):].strip(" -:")
            break
    teile = [t for t in (rest, depot) if t]
    return " ".join(teile)[:40] if teile else ""


def _wp_name(info: str, isin: Optional[str]) -> str:
    """Aus 'Ausführung ORDER Kauf US67066G1040 291524333' wird kein Name —
    die CSV enthält keine WP-Bezeichnung. Wir geben die ISIN zurück und
    lassen den Namen später aus der Erträgnisaufstellung nachtragen."""
    return isin or info[:40]


def namen_aus_ertraegnis_nachtragen(
    belege: List[Beleg], isin_namen: Dict[str, str]
) -> int:
    """Ergänzt WP-Bezeichnungen in CSV-Belegen aus dem PDF-Namensindex.
    Rückgabe: Anzahl ergänzter Belege."""
    n = 0
    for b in belege:
        if b.isin and b.isin in isin_namen and b.wertpapierbezeichnung == b.isin:
            b.wertpapierbezeichnung = isin_namen[b.isin]
            n += 1
    return n

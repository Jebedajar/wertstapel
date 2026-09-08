"""
fx_rates.py — EZB-Referenzkurse (Devisenkassamittelkurs) mit SQLite-Cache.

Quelle: EZB Data Portal, https://data-api.ecb.europa.eu
  Serie:  D.<WHG>.EUR.SP00.A   (täglich, Fremdwährung je 1 EUR, Kassakurs)
  Kein API-Key, kein Rate-Limit, Historie ab 1999.

Rechtsgrundlage: §256a HGB — Umrechnung zum Devisenkassamittelkurs.
Der EZB-Referenzkurs ist dafür die gängige Bezugsgröße.

Verwendung:
    from fx_rates import FxRates
    fx = FxRates()
    fx.ensure_range("USD", date(2024,1,1), date(2024,12,31))
    eur = fx.to_eur(Decimal("213.32"), "USD", date(2024,7,5))
"""

import os
import sqlite3
import csv
import io
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

import requests

DB_PATH  = os.getenv("DB_PATH", "/var/www/wertstapel/data/wertstapel.db")
ECB_BASE = "https://data-api.ecb.europa.eu/service/data/EXR"
TIMEOUT  = 20

# Maximale Rückwärtssuche wenn der Tag kein TARGET-Handelstag ist
MAX_LOOKBACK_DAYS = 10


class FxRateUnavailable(Exception):
    """Kein Kurs für Währung/Datum ermittelbar."""


class FxRates:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        self._init_table()

    # ── Schema ────────────────────────────────────────────────────────────
    def _init_table(self):
        with sqlite3.connect(self.db_path) as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS fx_rates (
                    waehrung TEXT NOT NULL,
                    datum    TEXT NOT NULL,
                    kurs     TEXT NOT NULL,        -- Fremdwährung je 1 EUR
                    quelle   TEXT NOT NULL DEFAULT 'ECB',
                    PRIMARY KEY (waehrung, datum)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_fx_datum ON fx_rates(datum)")

    # ── Abruf von der EZB ─────────────────────────────────────────────────
    def fetch_from_ecb(self, waehrung: str, von: date, bis: date) -> int:
        """
        Lädt Tageskurse von der EZB und schreibt sie in den Cache.
        Gibt die Anzahl neu gespeicherter Zeilen zurück.
        """
        waehrung = waehrung.upper()
        if waehrung == "EUR":
            return 0

        url = f"{ECB_BASE}/D.{waehrung}.EUR.SP00.A"
        params = {
            "format":      "csvdata",
            "startPeriod": von.isoformat(),
            "endPeriod":   bis.isoformat(),
        }
        try:
            resp = requests.get(url, params=params, timeout=TIMEOUT)
            resp.raise_for_status()
        except requests.RequestException as e:
            raise FxRateUnavailable(
                f"EZB-Abruf für {waehrung} fehlgeschlagen: {e}") from e

        rows = []
        for rec in csv.DictReader(io.StringIO(resp.text)):
            tp  = (rec.get("TIME_PERIOD") or "").strip()
            val = (rec.get("OBS_VALUE") or "").strip()
            if not tp or not val:
                continue
            try:
                Decimal(val)
            except Exception:
                continue          # z.B. "NaN" an Feiertagen
            rows.append((waehrung, tp, val, "ECB"))

        if rows:
            with sqlite3.connect(self.db_path) as db:
                db.executemany(
                    "INSERT OR REPLACE INTO fx_rates (waehrung, datum, kurs, quelle) "
                    "VALUES (?, ?, ?, ?)", rows
                )
        return len(rows)

    def ensure_range(self, waehrung: str, von: date, bis: date) -> None:
        """
        Stellt sicher dass der Zeitraum im Cache liegt.
        Lädt nur nach wenn Lücken bestehen.
        Puffer von 14 Tagen vor `von` für Feiertags-Rückwärtssuche.
        """
        waehrung = waehrung.upper()
        if waehrung == "EUR":
            return

        von_puffer = von - timedelta(days=14)
        with sqlite3.connect(self.db_path) as db:
            row = db.execute(
                "SELECT COUNT(*), MIN(datum), MAX(datum) FROM fx_rates "
                "WHERE waehrung = ? AND datum BETWEEN ? AND ?",
                (waehrung, von_puffer.isoformat(), bis.isoformat())
            ).fetchone()

        n, dmin, dmax = row
        # Grobe Heuristik: ~5 Handelstage je 7 Kalendertage
        erwartet = int((bis - von_puffer).days * 5 / 7 * 0.8)
        vollstaendig = (
            n >= max(erwartet, 1)
            and dmin is not None and dmin <= (von_puffer + timedelta(days=7)).isoformat()
            and dmax is not None and dmax >= (bis - timedelta(days=7)).isoformat()
        )
        if not vollstaendig:
            try:
                self.fetch_from_ecb(waehrung, von_puffer, bis)
            except FxRateUnavailable:
                pass   # Aufrufer meldet fehlende Kurse über get_rate

    # ── Kursabfrage ───────────────────────────────────────────────────────
    def get_rate(self, waehrung: str, tag: date,
                 auto_fetch: bool = True) -> tuple[Decimal, date]:
        """
        Liefert (kurs, tatsaechliches_kursdatum).
        Kurs = Einheiten Fremdwährung je 1 EUR.
        Ist `tag` kein TARGET-Handelstag, wird bis zu MAX_LOOKBACK_DAYS
        rückwärts gesucht (gängige Praxis: letzter veröffentlichter Kurs).
        """
        waehrung = waehrung.upper()
        if waehrung == "EUR":
            return Decimal("1"), tag

        with sqlite3.connect(self.db_path) as db:
            row = db.execute(
                "SELECT kurs, datum FROM fx_rates "
                "WHERE waehrung = ? AND datum <= ? AND datum >= ? "
                "ORDER BY datum DESC LIMIT 1",
                (waehrung, tag.isoformat(),
                 (tag - timedelta(days=MAX_LOOKBACK_DAYS)).isoformat())
            ).fetchone()

        if row:
            return Decimal(row[0]), date.fromisoformat(row[1])

        if auto_fetch:
            try:
                self.fetch_from_ecb(waehrung, tag - timedelta(days=30), tag)
            except FxRateUnavailable:
                pass
            return self.get_rate(waehrung, tag, auto_fetch=False)

        raise FxRateUnavailable(
            f"Kein EZB-Kurs für {waehrung} am {tag} (auch nicht in den "
            f"{MAX_LOOKBACK_DAYS} Tagen davor)."
        )

    def to_eur(self, betrag, waehrung: str, tag: date) -> Decimal:
        """Rechnet einen Fremdwährungsbetrag in EUR um (2 Nachkommastellen)."""
        betrag = Decimal(str(betrag))
        if waehrung.upper() == "EUR":
            return betrag.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        kurs, _ = self.get_rate(waehrung, tag)
        return (betrag / kurs).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def rate_info(self, waehrung: str, tag: date) -> str:
        """Kurztext für Protokoll/Buchungstext, z.B. 'USD/EUR 1,0836 (05.07.2024)'."""
        if waehrung.upper() == "EUR":
            return "EUR"
        try:
            kurs, kursdatum = self.get_rate(waehrung, tag)
        except FxRateUnavailable:
            return f"{waehrung.upper()}/EUR — Kurs nicht verfügbar"
        return (f"{waehrung.upper()}/EUR {kurs:.4f} "
                f"({kursdatum.strftime('%d.%m.%Y')})")


# ── CLI: Cache vorbefüllen ────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    waehrungen = sys.argv[1].split(",") if len(sys.argv) > 1 else ["USD", "GBP", "CHF", "JPY"]
    jahr_von   = int(sys.argv[2]) if len(sys.argv) > 2 else date.today().year - 3
    fx = FxRates()
    for w in waehrungen:
        n = fx.fetch_from_ecb(w.strip().upper(), date(jahr_von, 1, 1), date.today())
        print(f"{w.strip().upper()}: {n} Kurse gespeichert")

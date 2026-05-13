"""
db_setup.py — Datenbank-Schema anlegen

Ausführen nach dem ersten Deploy:
  python3 db_setup.py

Oder aus FastAPI main.py beim Start aufrufen:
  from db_setup import init_db
  init_db()
"""

import os, sqlite3
from pathlib import Path

DB_PATH = os.getenv("DB_PATH", "/var/www/wertstapel/data/wertstapel.db")


def init_db():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as db:
        db.executescript("""
        -- Nutzer
        CREATE TABLE IF NOT EXISTS users (
            email       TEXT PRIMARY KEY,
            credits     INTEGER NOT NULL DEFAULT 0,
            flat_until  TEXT,           -- ISO-Date, z.B. "2027-05-13"
            created_at  TEXT NOT NULL
        );

        -- Jobs (PDF-Verarbeitungen)
        CREATE TABLE IF NOT EXISTS jobs (
            id              TEXT PRIMARY KEY,  -- UUID
            user_email      TEXT,
            plan_id         TEXT,
            status          TEXT NOT NULL DEFAULT 'awaiting_payment',
            pdf_path        TEXT,
            output_dir      TEXT,
            created_at      TEXT NOT NULL,
            FOREIGN KEY (user_email) REFERENCES users(email)
        );

        -- Sessions (1-Jahr-Cookie)
        CREATE TABLE IF NOT EXISTS sessions (
            token       TEXT PRIMARY KEY,
            email       TEXT NOT NULL,
            expires_at  TEXT NOT NULL,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        -- Magic-Link-Tokens (15 Minuten)
        CREATE TABLE IF NOT EXISTS magic_tokens (
            email       TEXT PRIMARY KEY,
            token       TEXT NOT NULL,
            expires_at  TEXT NOT NULL
        );

        -- Admin-Log (manuelle Credit-Einbuchungen)
        CREATE TABLE IF NOT EXISTS admin_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            action      TEXT NOT NULL,
            email       TEXT NOT NULL,
            amount      INTEGER,
            note        TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        -- Indizes
        CREATE INDEX IF NOT EXISTS idx_sessions_email      ON sessions(email);
        CREATE INDEX IF NOT EXISTS idx_sessions_expires    ON sessions(expires_at);
        CREATE INDEX IF NOT EXISTS idx_jobs_user_email     ON jobs(user_email);
        CREATE INDEX IF NOT EXISTS idx_jobs_status         ON jobs(status);
        """)
    print(f"DB initialisiert: {DB_PATH}")


if __name__ == "__main__":
    init_db()

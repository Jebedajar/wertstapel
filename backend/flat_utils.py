import os, sqlite3
from datetime import date, timedelta

DB_PATH = os.getenv("DB_PATH", "/var/www/wertstapel/backend/wertstapel.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def apply_flat_purchase(email: str, months: int = 12) -> dict:
    today = date.today()
    days  = months * 30

    with get_db() as db:
        row = db.execute(
            "SELECT flat_until FROM users WHERE email = ?", (email,)
        ).fetchone()

        if row and row["flat_until"]:
            existing = date.fromisoformat(row["flat_until"])
            base     = existing if existing > today else today
            extended = existing > today
        else:
            base     = today
            extended = False

        new_until = (base + timedelta(days=days)).isoformat()

        db.execute("""
            INSERT INTO users (email, credits, flat_until, reminder_sent, created_at)
            VALUES (?, 0, ?, 0, ?)
            ON CONFLICT(email) DO UPDATE SET
                flat_until    = excluded.flat_until,
                reminder_sent = 0
        """, (email, new_until, today.isoformat()))

    return {"email": email, "flat_until": new_until, "extended": extended}


def apply_credits_purchase(email: str, credits: int) -> dict:
    today = date.today()
    with get_db() as db:
        db.execute("""
            INSERT INTO users (email, credits, flat_until, reminder_sent, created_at)
            VALUES (?, ?, NULL, 0, ?)
            ON CONFLICT(email) DO UPDATE SET credits = credits + excluded.credits
        """, (email, credits, today.isoformat()))
        row = db.execute(
            "SELECT credits FROM users WHERE email = ?", (email,)
        ).fetchone()
    return {"email": email, "credits": row["credits"] if row else credits}


def get_expiring_flats(days_ahead: int = 30) -> list:
    target = (date.today() + timedelta(days=days_ahead)).isoformat()
    with get_db() as db:
        rows = db.execute("""
            SELECT email, flat_until FROM users
            WHERE flat_until = ? AND reminder_sent = 0
        """, (target,)).fetchall()
    return [dict(r) for r in rows]


def mark_reminder_sent(email: str) -> None:
    with get_db() as db:
        db.execute("UPDATE users SET reminder_sent = 1 WHERE email = ?", (email,))

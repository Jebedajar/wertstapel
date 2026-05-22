"""
export_routes.py — Direkter Export-Start für eingeloggte Nutzer mit Guthaben.

Einzubinden in main.py:
    from export_routes import router as export_router
    app.include_router(export_router)
"""

import os, sqlite3, uuid
from datetime import date, datetime
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from auth import get_session_user

router = APIRouter()
DB_PATH = os.getenv("DB_PATH", "/var/www/wertstapel/backend/wertstapel.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class ExportStartRequest(BaseModel):
    skr:     str = "SKR04"
    bank:    str = "1801"
    mandant: str = ""


@router.post("/api/export/start")
async def export_start(body: ExportStartRequest, request: Request):
    """
    Startet einen Export direkt aus dem Guthaben — ohne Stripe.
    Wird nur aufgerufen wenn der Nutzer eingeloggt ist und Credits hat.

    Ablauf:
    1. Session prüfen
    2. Guthaben prüfen (Credits > 0 oder Flat gültig)
    3. Credits um 1 reduzieren (bei Flat: keine Reduktion)
    4. Job-ID anlegen
    5. Job-ID zurückgeben — Frontend startet Verarbeitung
    """
    user = get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Nicht angemeldet")

    email      = user["email"]
    credits    = user["credits"]
    flat_until = user["flat_until"]

    flat_valid = (
        flat_until is not None and
        date.fromisoformat(flat_until) >= date.today()
    )

    if credits <= 0 and not flat_valid:
        raise HTTPException(
            status_code=402,
            detail="Kein Guthaben. Bitte ein Paket erwerben."
        )

    job_id = str(uuid.uuid4())

    with get_db() as db:
        if not flat_valid:
            db.execute(
                "UPDATE users SET credits = credits - 1 WHERE email = ?",
                (email,)
            )

        db.execute(
            """INSERT INTO jobs
               (id, user_email, plan_id, status, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (
                job_id,
                email,
                "flat" if flat_valid else "credits",
                "processing",
                datetime.utcnow().isoformat(),
            )
        )

    return {
        "ok":      True,
        "job_id":  job_id,
        "skr":     body.skr,
        "bank":    body.bank,
        "mandant": body.mandant,
    }


@router.get("/api/export/status/{job_id}")
async def export_status(job_id: str, request: Request):
    """Gibt den aktuellen Status eines Jobs zurück."""
    user = get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Nicht angemeldet")

    with get_db() as db:
        row = db.execute(
            "SELECT status, output_dir FROM jobs WHERE id = ? AND user_email = ?",
            (job_id, user["email"])
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Job nicht gefunden")

    return {"job_id": job_id, "status": row["status"], "output_dir": row["output_dir"]}

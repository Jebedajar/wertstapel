"""
export_routes.py — Direkter Export-Start für eingeloggte Nutzer mit Guthaben.
"""

import os, sqlite3, uuid
from datetime import date, datetime
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Form, BackgroundTasks

from auth import get_session_user

router = APIRouter()
DB_PATH = os.getenv("DB_PATH", "/var/www/wertstapel/backend/wertstapel.db")
UPLOAD_DIR = Path("/tmp/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@router.post("/api/export/start")
async def export_start(
    background_tasks: BackgroundTasks,
    request:  Request,
    file:     UploadFile = File(...),
    skr:      str = Form("SKR04"),
    bank:     str = Form("1801"),
    mandant:  str = Form(""),
):
    """
    Startet einen Export direkt aus dem Guthaben — ohne Stripe.
    Nimmt Datei-Upload entgegen, prüft Guthaben, legt Job an und startet Verarbeitung.
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

    allowed_ext = {".pdf", ".xlsx", ".xls", ".csv"}
    file_ext = Path(file.filename or "").suffix.lower()
    if not file_ext or file_ext not in allowed_ext:
        raise HTTPException(400, "Nur PDF-, XLSX-, XLS- oder CSV-Dateien erlaubt")

    content = await file.read()
    if len(content) > 100 * 1024 * 1024:
        raise HTTPException(400, "Datei zu groß (max. 100 MB)")

    job_id   = str(uuid.uuid4())
    pdf_path = UPLOAD_DIR / f"{job_id}{file_ext}"
    pdf_path.write_bytes(content)

    with get_db() as db:
        if not flat_valid:
            db.execute(
                "UPDATE users SET credits = credits - 1 WHERE email = ?",
                (email,)
            )

        db.execute(
            """INSERT INTO jobs
               (id, user_email, plan_id, status, pdf_path, skr, bank, mandant, created_at)
               VALUES (?, ?, ?, 'paid', ?, ?, ?, ?, ?)""",
            (
                job_id,
                email,
                "flat" if flat_valid else "credits",
                str(pdf_path),
                skr,
                bank,
                mandant,
                datetime.utcnow().isoformat(),
            )
        )

    from main import process_job
    background_tasks.add_task(process_job, job_id)

    return {"ok": True, "job_id": job_id}


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

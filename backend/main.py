import os
import sys
import uuid
import sqlite3
import secrets
from pathlib import Path
from datetime import datetime, timedelta, date
from contextlib import contextmanager

import stripe
from fastapi import (
    FastAPI, UploadFile, File, Form, HTTPException,
    Request, BackgroundTasks, Depends
)
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

STRIPE_SECRET_KEY     = os.environ["STRIPE_SECRET_KEY"]
STRIPE_WEBHOOK_SECRET = os.environ["STRIPE_WEBHOOK_SECRET"]
STRIPE_PRICE_SINGLE   = os.environ["STRIPE_PRICE_SINGLE"]
STRIPE_PRICE_FIVE     = os.environ["STRIPE_PRICE_FIVE"]
STRIPE_PRICE_TWENTY   = os.environ["STRIPE_PRICE_TWENTY"]
STRIPE_PRICE_FLAT     = os.environ["STRIPE_PRICE_FLAT"]
ADMIN_PASSWORD        = os.environ["ADMIN_PASSWORD"]
APP_URL               = os.environ.get("APP_URL", "https://wertstapel.de")
AGB_VERSION           = "2026-05-18-v1"

stripe.api_key = STRIPE_SECRET_KEY

from emails import send_email, send_flat_expiry_reminder
from flat_utils import apply_flat_purchase, apply_credits_purchase

UPLOAD_DIR = Path("/tmp/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

DB_PATH = Path("/var/www/wertstapel/backend/wertstapel.db")

PLAN_MAP = {
    "single": {"price_id": STRIPE_PRICE_SINGLE, "credits": 1,  "type": "credits", "months": 0},
    "five":   {"price_id": STRIPE_PRICE_FIVE,   "credits": 5,  "type": "credits", "months": 0},
    "twenty": {"price_id": STRIPE_PRICE_TWENTY, "credits": 20, "type": "credits", "months": 0},
    "flat":   {"price_id": STRIPE_PRICE_FLAT,   "credits": 0,  "type": "flat",    "months": 12},
}

from auth import router as auth_router

app = FastAPI(title="Wertstapel API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://wertstapel.de", "https://www.wertstapel.de", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

security = HTTPBasic()


@contextmanager
def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                credits INTEGER DEFAULT 0,
                flat_until DATE,
                reminder_sent INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                user_email TEXT NOT NULL,
                plan_id TEXT,
                status TEXT DEFAULT 'awaiting_payment',
                pdf_path TEXT,
                output_dir TEXT,
                skr TEXT DEFAULT 'SKR04',
                bank TEXT DEFAULT '1801',
                mandant TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS magic_tokens (
                email      TEXT NOT NULL,
                token      TEXT PRIMARY KEY,
                expires_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token      TEXT PRIMARY KEY,
                email      TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
        """)
        for col, default in [
            ("skr",         "'SKR04'"),
            ("bank",        "'1801'"),
            ("mandant",     "''"),
            ("consent_at",  "NULL"),
            ("consent_ip",  "NULL"),
            ("agb_version", "NULL"),
        ]:
            try:
                conn.execute(f"ALTER TABLE jobs ADD COLUMN {col} TEXT DEFAULT {default}")
            except Exception:
                pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN reminder_sent INTEGER NOT NULL DEFAULT 0")
        except Exception:
            pass


init_db()


def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct = secrets.compare_digest(credentials.password.encode(), ADMIN_PASSWORD.encode())
    if not correct:
        raise HTTPException(status_code=401, detail="Unauthorized",
                            headers={"WWW-Authenticate": "Basic"})
    return credentials.username


def _send_done_email(email: str, job_id: str):
    try:
        send_email(
            to=email,
            subject="Ihr Buchungsstapel ist fertig — Wertstapel",
            html_body=f"""
            <p style="font-weight:700;font-size:16px;margin-bottom:8px">Ihr Buchungsstapel ist fertig.</p>
            <p style="color:#5E6B82;font-size:14px;margin-bottom:28px">
              Ihr DATEV-Buchungsstapel wurde erfolgreich erstellt.<br>
              Der Download-Link ist 24 Stunden gültig.
            </p>
            <a href="{APP_URL}/success?job_id={job_id}"
               style="display:inline-block;padding:13px 28px;background:#0B1220;color:#fff;
                      text-decoration:none;border-radius:8px;font-weight:600;font-size:14px">
              Jetzt herunterladen →
            </a>
            """,
        )
    except Exception as e:
        print(f"Email failed for {email}: {e}")


def process_job(job_id: str):
    from run import main as run_main

    output_dir = f"/tmp/uploads/{job_id}_out"

    with get_db() as conn:
        conn.execute("UPDATE jobs SET status='processing' WHERE id=?", (job_id,))

    try:
        with get_db() as conn:
            row = conn.execute(
                "SELECT pdf_path, user_email, skr, bank, mandant FROM jobs WHERE id=?", (job_id,)
            ).fetchone()

        if not row or not row["pdf_path"]:
            raise ValueError("PDF path not found")

        run_main(
            row["pdf_path"],
            output_dir,
            skr=row["skr"] or "SKR04",
            bank=row["bank"] or "1801",
            mandant=row["mandant"] or "",
        )

        with get_db() as conn:
            conn.execute(
                "UPDATE jobs SET status='done', output_dir=? WHERE id=?",
                (output_dir, job_id),
            )

        _send_done_email(row["user_email"], job_id)

    except Exception as e:
        print(f"Job {job_id} failed: {e}")
        with get_db() as conn:
            conn.execute("UPDATE jobs SET status='error' WHERE id=?", (job_id,))


@app.post("/api/upload")
async def upload_pdf(
    request:  Request,
    file:     UploadFile = File(...),
    email:    str = Form(...),
    plan:     str = Form("single"),
    skr:      str = Form("SKR04"),
    bank:     str = Form("1801"),
    mandant:  str = Form(""),
    consent:  str = Form("false"),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Nur PDF-Dateien erlaubt")

    content = await file.read()
    if len(content) > 100 * 1024 * 1024:
        raise HTTPException(400, "Datei zu groß (max. 100 MB)")

    plan_cfg = PLAN_MAP.get(plan)
    if not plan_cfg:
        raise HTTPException(400, "Ungültiger Plan")
    if consent != "true":
        raise HTTPException(400, "Bitte AGB, AVV und Datenschutzerklärung akzeptieren")

    job_id      = str(uuid.uuid4())
    consent_at  = datetime.utcnow().isoformat()
    consent_ip  = (request.headers.get("x-real-ip") or request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else ""))
    pdf_path = UPLOAD_DIR / f"{job_id}.pdf"
    pdf_path.write_bytes(content)

    with get_db() as conn:
        conn.execute("INSERT OR IGNORE INTO users (email) VALUES (?)", (email,))
        conn.execute(
            "INSERT INTO jobs (id, user_email, plan_id, status, pdf_path, skr, bank, mandant, consent_at, consent_ip, agb_version) VALUES (?, ?, ?, 'awaiting_payment', ?, ?, ?, ?, ?, ?, ?)",
            (job_id, email, plan_cfg["price_id"], str(pdf_path), skr, bank, mandant, consent_at, consent_ip, AGB_VERSION),
        )

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{"price": plan_cfg["price_id"], "quantity": 1}],
        mode="payment",
        success_url=f"{APP_URL}/success?job_id={job_id}",
        cancel_url=f"{APP_URL}/?cancelled=1",
        customer_email=email,
        metadata={
            "job_id":  job_id,
            "email":   email,
            "type":    plan_cfg["type"],
            "credits": str(plan_cfg["credits"]),
            "months":  str(plan_cfg["months"]),
        },
    )

    return {"job_id": job_id, "checkout_url": session.url}


@app.post("/api/webhook/stripe")
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks):
    payload    = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(400, "Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        meta    = session.get("metadata", {})

        job_id    = meta.get("job_id")
        email     = meta.get("email")
        plan_type = meta.get("type", "credits")
        credits   = int(meta.get("credits", "0"))
        months    = int(meta.get("months", "0"))

        if not job_id or not email:
            return {"ok": False, "reason": "missing metadata"}

        if plan_type == "flat":
            apply_flat_purchase(email, months if months > 0 else 12)
        else:
            apply_credits_purchase(email, credits)

        with get_db() as conn:
            conn.execute("UPDATE jobs SET status='paid' WHERE id=?", (job_id,))

        background_tasks.add_task(process_job, job_id)

    return {"ok": True}


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    with get_db() as conn:
        row = conn.execute(
            "SELECT status, output_dir FROM jobs WHERE id=?", (job_id,)
        ).fetchone()

    if not row:
        raise HTTPException(404, "Job nicht gefunden")

    result: dict = {"status": row["status"]}

    if row["status"] == "done" and row["output_dir"]:
        out = Path(row["output_dir"])
        result["files"] = [f.name for f in out.iterdir() if f.is_file()] if out.exists() else []

    return result


@app.get("/api/download/{job_id}/{filename}")
async def download_file(job_id: str, filename: str):
    if "/" in filename or ".." in filename:
        raise HTTPException(400, "Ungültiger Dateiname")

    with get_db() as conn:
        row = conn.execute(
            "SELECT status, output_dir FROM jobs WHERE id=?", (job_id,)
        ).fetchone()

    if not row:
        raise HTTPException(404, "Job nicht gefunden")
    if row["status"] != "done":
        raise HTTPException(403, "Datei noch nicht verfügbar")

    file_path = Path(row["output_dir"]) / filename
    if not file_path.exists():
        raise HTTPException(404, "Datei nicht gefunden")

    return FileResponse(str(file_path), filename=filename, media_type="application/octet-stream")


@app.post("/api/admin/credits")
async def admin_add_credits(request: Request, admin: str = Depends(verify_admin)):
    body    = await request.json()
    email   = body.get("email")
    credits = int(body.get("credits", 0))

    if not email:
        raise HTTPException(400, "E-Mail erforderlich")

    with get_db() as conn:
        conn.execute(
            """INSERT INTO users (email, credits) VALUES (?, ?)
               ON CONFLICT(email) DO UPDATE SET credits=credits+excluded.credits""",
            (email, credits),
        )
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()

    return {"email": email, "credits": user["credits"]}


@app.get("/api/health")
async def health():
    return {"ok": True}

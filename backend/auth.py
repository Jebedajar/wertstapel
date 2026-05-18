"""
auth.py — Magic Link Auth + Session Management
Wird von main.py importiert und als Router eingebunden.

Endpunkte:
  POST /api/auth/magic-link   → Token erzeugen + Mail versenden
  GET  /api/auth/verify       → Token prüfen + Cookie setzen
  GET  /api/auth/me           → Aktuellen User aus Cookie lesen
  POST /api/auth/logout       → Cookie löschen
"""

import os, secrets, sqlite3
from datetime import datetime, timedelta, date
from fastapi import APIRouter, Request, Response, HTTPException
from pydantic import BaseModel, EmailStr
import resend

router = APIRouter()

DB_PATH   = os.getenv("DB_PATH", "/var/www/wertstapel/backend/wertstapel.db")
BASE_URL  = os.getenv("BASE_URL", "https://wertstapel.de")
RESEND_KEY = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL = os.getenv("RESEND_FROM", "wertstapel@spark-innovation.de")
COOKIE_MAX_AGE = 60 * 60 * 24 * 365  # 1 Jahr in Sekunden

resend.api_key = RESEND_KEY


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_session_user(request: Request) -> dict | None:
    """Liest Session-Token aus Cookie und gibt User-Daten zurück."""
    token = request.cookies.get("ws_session")
    if not token:
        return None
    with get_db() as db:
        row = db.execute(
            "SELECT u.email, u.credits, u.flat_until "
            "FROM sessions s JOIN users u ON s.email = u.email "
            "WHERE s.token = ? AND s.expires_at > ?",
            (token, datetime.utcnow().isoformat())
        ).fetchone()
    return dict(row) if row else None


class MagicLinkRequest(BaseModel):
    email: str


@router.post("/api/auth/magic-link")
async def request_magic_link(body: MagicLinkRequest):
    """Erzeugt einen Magic-Link-Token und schickt ihn per E-Mail."""
    email = body.email.lower().strip()

    # Token erzeugen (32 Bytes = 64 Hex-Zeichen)
    token     = secrets.token_hex(32)
    expires   = (datetime.utcnow() + timedelta(minutes=15)).isoformat()

    with get_db() as db:
        # User anlegen falls nicht vorhanden
        db.execute(
            "INSERT OR IGNORE INTO users (email, credits, created_at) VALUES (?, 0, ?)",
            (email, datetime.utcnow().isoformat())
        )
        # Alten Token löschen, neuen speichern
        db.execute("DELETE FROM magic_tokens WHERE email = ?", (email,))
        db.execute(
            "INSERT INTO magic_tokens (email, token, expires_at) VALUES (?, ?, ?)",
            (email, token, expires)
        )

    login_url = f"{BASE_URL}/api/auth/verify?token={token}"

    resend.Emails.send({
        "from": FROM_EMAIL,
        "to": email,
        "subject": "Ihr Wertstapel Login-Link",
        "html": f"""
        <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:40px 20px">
          <p style="font-weight:700;font-size:16px;margin-bottom:8px">Wertstapel — Login</p>
          <p style="color:#5E6B82;font-size:14px;margin-bottom:28px">
            Klicken Sie auf den Button um sich anzumelden.<br>
            Der Link ist 15 Minuten gültig.
          </p>
          <a href="{login_url}"
             style="display:inline-block;padding:13px 28px;background:#0B1220;color:#fff;
                    text-decoration:none;border-radius:8px;font-weight:600;font-size:14px">
            Jetzt anmelden →
          </a>
          <p style="color:#97A1B5;font-size:12px;margin-top:24px">
            Falls Sie diesen Link nicht angefordert haben, ignorieren Sie diese E-Mail.
          </p>
        </div>
        """,
    })

    return {"ok": True}


@router.get("/api/auth/verify")
async def verify_magic_link(token: str, response: Response):
    """Prüft Magic-Link-Token und setzt Session-Cookie."""
    with get_db() as db:
        row = db.execute(
            "SELECT email FROM magic_tokens WHERE token = ? AND expires_at > ?",
            (token, datetime.utcnow().isoformat())
        ).fetchone()

        if not row:
            raise HTTPException(status_code=400, detail="Link ungültig oder abgelaufen.")

        email = row["email"]

        # Token löschen (einmalig verwendbar)
        db.execute("DELETE FROM magic_tokens WHERE token = ?", (token,))

        # Session anlegen
        session_token = secrets.token_hex(32)
        session_exp   = (datetime.utcnow() + timedelta(days=365)).isoformat()
        db.execute(
            "INSERT INTO sessions (token, email, expires_at) VALUES (?, ?, ?)",
            (session_token, email, session_exp)
        )

    # Cookie setzen: 1 Jahr, HttpOnly, Secure, SameSite=Lax
    response = Response(status_code=302, headers={"Location": "/"})
    response.set_cookie(
        key="ws_session",
        value=session_token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )
    return response


@router.get("/api/auth/me")
async def get_me(request: Request):
    """Gibt aktuellen User zurück oder 401."""
    user = get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Nicht angemeldet")
    return user


@router.post("/api/auth/logout")
async def logout(response: Response):
    """Löscht Session-Cookie."""
    response = Response(content='{"ok":true}', media_type="application/json")
    response.delete_cookie("ws_session", path="/")
    return response

@router.post("/api/auth/post-purchase/{job_id}")
async def post_purchase_login(job_id: str, response: Response):
    """Auto-login after successful Stripe checkout using the job's email."""
    with get_db() as db:
        row = db.execute(
            "SELECT user_email FROM jobs WHERE id = ? AND status IN ('paid', 'processing', 'done')",
            (job_id,)
        ).fetchone()

    if not row:
        raise HTTPException(404, "Job nicht gefunden")

    email = row["user_email"]

    session_token = secrets.token_hex(32)
    session_exp   = (datetime.utcnow() + timedelta(days=365)).isoformat()

    with get_db() as db:
        db.execute(
            "INSERT OR IGNORE INTO users (email, credits, created_at) VALUES (?, 0, ?)",
            (email, datetime.utcnow().isoformat())
        )
        db.execute(
            "INSERT INTO sessions (token, email, expires_at) VALUES (?, ?, ?)",
            (session_token, email, session_exp)
        )

    response.set_cookie(
        key="ws_session",
        value=session_token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )
    return {"ok": True, "email": email}

import os
import requests
from datetime import date

BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
FROM_EMAIL    = os.getenv("FROM_EMAIL", "info@wertstapel.de")
FROM_NAME     = "Wertstapel"
APP_URL       = os.getenv("APP_URL", "https://wertstapel.de")

_FOOTER_HTML = """
<div style="margin-top:40px;padding-top:20px;border-top:1px solid #e4e2db;
            font-size:11px;color:#97A1B5;line-height:1.7;font-family:sans-serif">
  <strong style="color:#5E6B82">Wertstapel.de</strong><br>
  ein Angebot der Spark Innovation GmbH<br>
  Lenneper Str. 32 &middot; 40591 Düsseldorf<br>
  Geschäftsführer: Martin Ferfers<br>
  HRB 83993 &middot; Amtsgericht Düsseldorf<br>
  USt-ID: DE318933806<br>
  <a href="https://wertstapel.de/datenschutz" style="color:#97A1B5">Datenschutz</a>
  &nbsp;&middot;&nbsp;
  <a href="https://wertstapel.de/impressum" style="color:#97A1B5">Impressum</a>
</div>
"""


def send_email(to: str, subject: str, html_body: str) -> None:
    html = f"""
    <div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:40px 20px">
      {html_body}
      {_FOOTER_HTML}
    </div>
    """
    resp = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        json={
            "sender":      {"name": FROM_NAME, "email": FROM_EMAIL},
            "to":          [{"email": to}],
            "subject":     subject,
            "htmlContent": html,
        },
        headers={
            "api-key":      BREVO_API_KEY,
            "Content-Type": "application/json",
        },
        timeout=15,
    )
    if not resp.ok:
        raise RuntimeError(f"Brevo error {resp.status_code}: {resp.text}")


def send_flat_expiry_reminder(to: str, flat_until: str) -> None:
    try:
        d = date.fromisoformat(flat_until)
        datum_de = d.strftime("%d.%m.%Y")
    except Exception:
        datum_de = flat_until

    send_email(
        to=to,
        subject="Ihre Wertstapel-Jahresflat läuft in 30 Tagen ab",
        html_body=f"""
        <p style="font-weight:700;font-size:16px;margin-bottom:8px">Ihre Jahresflat läuft bald ab.</p>
        <p style="color:#5E6B82;font-size:14px;margin-bottom:20px">
          Ihre Jahresflat ist noch bis zum <strong style="color:#0B1220">{datum_de}</strong> gültig —
          das sind noch 30 Tage.
        </p>
        <p style="color:#5E6B82;font-size:14px;margin-bottom:28px">
          Wenn Sie jetzt verlängern, wird die neue Laufzeit an Ihren bestehenden Zeitraum angehängt —
          kein Tag geht verloren.
        </p>
        <a href="{APP_URL}/#pricing"
           style="display:inline-block;padding:13px 28px;background:#0B1220;color:#fff;
                  text-decoration:none;border-radius:8px;font-weight:600;font-size:14px">
          Jahresflat verlängern →
        </a>
        """,
    )

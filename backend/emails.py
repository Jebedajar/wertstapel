import os
import requests

BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
FROM_EMAIL    = os.getenv("FROM_EMAIL", "info@wertstapel.de")
FROM_NAME     = "Wertstapel"

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

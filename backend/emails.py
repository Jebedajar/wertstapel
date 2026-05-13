"""
emails.py — E-Mail-Vorlagen für Wertstapel

Verwendung:
  from emails import send_purchase_confirmation, send_download_links
"""

import os
import resend

resend.api_key = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL    = os.getenv("RESEND_FROM", "wertstapel@spark-innovation.de")
BASE_URL      = os.getenv("BASE_URL", "https://wertstapel.de")


def send_purchase_confirmation(email: str, plan_label: str, credits: int,
                                is_flat: bool = False, flat_until: str = ""):
    """
    Kaufbestätigung nach Stripe-Zahlung.
    Informiert über Guthaben und erklärt wie es abgerufen wird.
    """
    if is_flat:
        credits_line = "eine Jahresflat"
        credits_note = f"Ihr Flat läuft bis {flat_until}."
    else:
        credits_line = f"{credits} {'Export' if credits == 1 else 'Exporte'}"
        credits_note = f"Ihr Guthaben: {credits} {'Export' if credits == 1 else 'Exporte'} verbleibend."

    resend.Emails.send({
        "from": FROM_EMAIL,
        "to":   email,
        "subject": f"Ihr Wertstapel-Paket ist bereit",
        "html": f"""
        <div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:40px 20px;color:#0B1220">
          <p style="font-weight:700;font-size:15px;margin-bottom:4px">WERTSTAPEL</p>
          <p style="color:#5E6B82;font-size:12px;margin-bottom:32px;letter-spacing:.04em;text-transform:uppercase">
            Buchungsstapel für Wertpapierabrechnungen
          </p>

          <p style="font-size:16px;margin-bottom:8px">Vielen Dank für Ihren Kauf.</p>
          <p style="font-size:15px;color:#1F2937;margin-bottom:28px">
            Sie haben {credits_line} erworben.<br>
            Ihre Exporte sind unter dieser E-Mail-Adresse gespeichert
            und jederzeit abrufbar unter wertstapel.de
          </p>

          <div style="background:#F7F8FB;border-radius:12px;padding:22px 24px;margin-bottom:28px">
            <p style="font-weight:700;font-size:13px;margin-bottom:14px;color:#0B1220">
              So nutzen Sie Ihr Export-Guthaben:
            </p>
            <p style="font-size:14px;color:#1F2937;margin-bottom:8px;display:flex;align-items:flex-start;gap:10px">
              <span style="color:#2563EB;font-weight:700">→</span>
              <span><a href="{BASE_URL}" style="color:#2563EB;font-weight:600">wertstapel.de</a> aufrufen</span>
            </p>
            <p style="font-size:14px;color:#1F2937;margin-bottom:8px;display:flex;align-items:flex-start;gap:10px">
              <span style="color:#2563EB;font-weight:700">→</span>
              <span>Ausreichendes „Guthaben" in der Navigation prüfen<br>
              <span style="color:#5E6B82;font-size:13px">ODER „Login" klicken</span></span>
            </p>
            <p style="font-size:14px;color:#1F2937;display:flex;align-items:flex-start;gap:10px">
              <span style="color:#2563EB;font-weight:700">→</span>
              <span>PDF hochladen</span>
            </p>
          </div>

          <p style="color:#97A1B5;font-size:12px;margin-bottom:6px">{credits_note}</p>
          <p style="color:#97A1B5;font-size:12px">
            Bei Fragen: <a href="mailto:hallo@wertstapel.de" style="color:#5E6B82">hallo@wertstapel.de</a>
          </p>
        </div>
        """,
    })


def send_download_links(email: str, job_id: str, filenames: dict,
                        n_belege: int, n_buchungen: int, plausi_ok: bool,
                        credits_remaining: int):
    """
    Download-Links nach erfolgreichem Export.
    Wird als Backup verschickt falls Browser-Session unterbrochen wurde.
    """
    dl_base = f"{BASE_URL}/api/download/{job_id}"

    plausi_badge = (
        '<span style="color:#166534;background:#DCFCE7;padding:2px 8px;border-radius:4px;font-size:12px">✓ Alle Plausibilitätsprüfungen bestanden</span>'
        if plausi_ok else
        '<span style="color:#92400E;background:#FEF3C7;padding:2px 8px;border-radius:4px;font-size:12px">⚠ Bitte Plausibilitätsbericht prüfen</span>'
    )

    resend.Emails.send({
        "from": FROM_EMAIL,
        "to":   email,
        "subject": "Ihr DATEV-Buchungsstapel ist fertig",
        "html": f"""
        <div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:40px 20px;color:#0B1220">
          <p style="font-weight:700;font-size:15px;margin-bottom:4px">WERTSTAPEL</p>
          <p style="color:#5E6B82;font-size:12px;margin-bottom:32px;letter-spacing:.04em;text-transform:uppercase">
            Export erfolgreich
          </p>

          <p style="font-size:14px;color:#5E6B82;margin-bottom:6px">
            {n_belege} Belege · {n_buchungen} Buchungssätze
          </p>
          <p style="margin-bottom:20px">{plausi_badge}</p>

          <div style="background:#F7F8FB;border-radius:12px;padding:20px 22px;margin-bottom:24px">
            {_file_row(dl_base, filenames['stapel'],    'DATEV-Buchungsstapel', 'DATEV-Import')}
            {_file_row(dl_base, filenames['plausi'],    'Plausibilitätsbericht', 'Vor dem Import prüfen')}
            {_file_row(dl_base, filenames['protokoll'], 'Verarbeitungsprotokoll', 'Audit-Trail')}
          </div>

          <p style="color:#97A1B5;font-size:12px;margin-bottom:6px">
            Download-Links sind 24 Stunden gültig.
          </p>
          {'<p style="color:#97A1B5;font-size:12px">Verbleibendes Guthaben: ' + str(credits_remaining) + ' Exporte</p>' if credits_remaining >= 0 else ''}
        </div>
        """,
    })


def _file_row(base: str, filename: str, title: str, label: str) -> str:
    return f"""
    <div style="border-bottom:1px solid #E6EAF2;padding:10px 0;display:flex;justify-content:space-between;align-items:center">
      <div>
        <div style="font-family:monospace;font-size:12px;color:#0B1220">{filename}</div>
        <div style="font-size:11px;color:#5E6B82;margin-top:2px">{label}</div>
      </div>
      <a href="{base}/{filename}"
         style="font-size:13px;font-weight:600;color:#2563EB;text-decoration:none">
        ↓ Download
      </a>
    </div>
    """

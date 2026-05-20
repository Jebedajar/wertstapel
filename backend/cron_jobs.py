"""
cron_jobs.py — täglich um 09:00 Uhr ausführen

Cron-Eintrag:
  0 9 * * * /usr/bin/python3 /var/www/wertstapel/backend/cron_jobs.py >> /var/log/wertstapel-cron.log 2>&1
"""

import sys, os
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from flat_utils import get_expiring_flats, mark_reminder_sent
from emails    import send_flat_expiry_reminder


def run():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] Cron-Job gestartet")

    expiring = get_expiring_flats(days_ahead=30)
    print(f"[{now}] {len(expiring)} ablaufende Flat(s) gefunden")

    for user in expiring:
        email      = user["email"]
        flat_until = user["flat_until"]
        try:
            send_flat_expiry_reminder(email, flat_until)
            mark_reminder_sent(email)
            print(f"[{now}] Reminder gesendet an {email} (läuft ab: {flat_until})")
        except Exception as e:
            print(f"[{now}] FEHLER für {email}: {e}")

    print(f"[{now}] Cron-Job abgeschlossen")


if __name__ == "__main__":
    run()

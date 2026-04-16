"""
Morning Report - Sendet eine E-Mail mit allen generierten Websites
"""

import json
import os
import smtplib
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
REPORT_TO = os.environ.get("REPORT_TO", GMAIL_USER)

CATEGORY_EMOJIS = {
    "Friseur": "✂️",
    "Handwerker": "🔧",
    "Restaurant": "🍽️",
    "Kosmetikstudio": "💅",
    "Physiotherapie": "💪",
    "Sonstiges": "🏢",
}

def build_html_report(businesses: list) -> str:
    date_str = datetime.now().strftime("%d.%m.%Y")

    deployed = [b for b in businesses if b.get("netlify_deployed")]
    failed = [b for b in businesses if not b.get("netlify_deployed")]

    # Group by category
    by_category = {}
    for b in deployed:
        cat = b.get("category", "Sonstiges")
        by_category.setdefault(cat, []).append(b)

    rows_html = ""
    for cat, items in sorted(by_category.items()):
        emoji = CATEGORY_EMOJIS.get(cat, "🏢")
        for b in items:
            name = b.get("name", "—")
            address = b.get("address", "—")
            phone = b.get("phone", "—") or "—"
            rating = b.get("rating", "")
            reviews = b.get("reviews", "")
            url = b.get("netlify_url", "")
            maps_url = b.get("maps_url", "")

            rating_str = f"⭐ {rating} ({reviews})" if rating else "—"

            rows_html += f"""
            <tr>
                <td style="padding:12px 16px; border-bottom:1px solid #f0f0f0;">
                    <strong>{emoji} {name}</strong><br>
                    <small style="color:#666;">{address}</small>
                </td>
                <td style="padding:12px 16px; border-bottom:1px solid #f0f0f0; color:#666;">{cat}</td>
                <td style="padding:12px 16px; border-bottom:1px solid #f0f0f0; color:#666;">{phone}</td>
                <td style="padding:12px 16px; border-bottom:1px solid #f0f0f0; color:#666;">{rating_str}</td>
                <td style="padding:12px 16px; border-bottom:1px solid #f0f0f0;">
                    <a href="{url}" style="background:#0070f3;color:white;padding:6px 14px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:600;">Website ansehen</a>
                    {"<br><br>" if maps_url else ""}
                    {f'<a href="{maps_url}" style="color:#0070f3;font-size:12px;">Google Maps</a>' if maps_url else ""}
                </td>
            </tr>"""

    failed_html = ""
    if failed:
        failed_html = f"""
        <div style="margin-top:32px;padding:16px;background:#fff3cd;border-radius:8px;border:1px solid #ffc107;">
            <strong>⚠️ {len(failed)} Betriebe konnten nicht verarbeitet werden:</strong><br>
            {", ".join(b.get("name", "?") for b in failed)}
        </div>"""

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:900px;margin:0 auto;padding:32px 16px;color:#1a1a1a;background:#f8f9fa;">

  <div style="background:linear-gradient(135deg,#0070f3,#00a8ff);border-radius:16px;padding:32px;margin-bottom:32px;color:white;">
    <h1 style="margin:0 0 8px;font-size:28px;">🌅 Guten Morgen!</h1>
    <p style="margin:0;opacity:0.9;font-size:16px;">Dein nächtlicher Website-Agent hat {len(deployed)} neue Websites für Betriebe in Erftstadt erstellt.</p>
    <p style="margin:8px 0 0;opacity:0.7;font-size:14px;">{date_str} • Erftstadt, NRW</p>
  </div>

  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:32px;">
    <div style="background:white;border-radius:12px;padding:20px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
      <div style="font-size:32px;font-weight:700;color:#0070f3;">{len(deployed)}</div>
      <div style="color:#666;font-size:14px;">Websites erstellt</div>
    </div>
    <div style="background:white;border-radius:12px;padding:20px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
      <div style="font-size:32px;font-weight:700;color:#00b894;">{len(by_category)}</div>
      <div style="color:#666;font-size:14px;">Kategorien</div>
    </div>
    <div style="background:white;border-radius:12px;padding:20px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
      <div style="font-size:32px;font-weight:700;color:#e17055;">{len(failed)}</div>
      <div style="color:#666;font-size:14px;">Fehlgeschlagen</div>
    </div>
  </div>

  <div style="background:white;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
    <table style="width:100%;border-collapse:collapse;">
      <thead>
        <tr style="background:#f8f9fa;">
          <th style="padding:12px 16px;text-align:left;font-size:13px;color:#666;font-weight:600;border-bottom:2px solid #eee;">Betrieb</th>
          <th style="padding:12px 16px;text-align:left;font-size:13px;color:#666;font-weight:600;border-bottom:2px solid #eee;">Kategorie</th>
          <th style="padding:12px 16px;text-align:left;font-size:13px;color:#666;font-weight:600;border-bottom:2px solid #eee;">Telefon</th>
          <th style="padding:12px 16px;text-align:left;font-size:13px;color:#666;font-weight:600;border-bottom:2px solid #eee;">Bewertung</th>
          <th style="padding:12px 16px;text-align:left;font-size:13px;color:#666;font-weight:600;border-bottom:2px solid #eee;">Aktionen</th>
        </tr>
      </thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>
  </div>

  {failed_html}

  <p style="text-align:center;color:#aaa;font-size:13px;margin-top:32px;">
    Generiert von deinem Local Web Agent • Läuft täglich um 2:00 Uhr
  </p>

</body>
</html>"""

def send_report(manifest_path: str = "generated_sites/manifest.json"):
    with open(manifest_path, "r", encoding="utf-8") as f:
        businesses = json.load(f)

    deployed_count = len([b for b in businesses if b.get("netlify_deployed")])
    date_str = datetime.now().strftime("%d.%m.%Y")

    subject = f"🌅 {deployed_count} neue Websites für Erftstadt – {date_str}"
    html_body = build_html_report(businesses)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = REPORT_TO
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, REPORT_TO, msg.as_string())
        logger.info(f"✓ Report sent to {REPORT_TO}")
    except Exception as e:
        logger.error(f"✗ Failed to send email: {e}")
        raise

if __name__ == "__main__":
    send_report()

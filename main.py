"""
Main Orchestrator - Führt den kompletten Workflow aus:
1. Scraping (Google Maps → Betriebe ohne Website)
2. Website-Generierung (Claude API)
3. Netlify-Deployment
4. E-Mail-Report
"""

import logging
import sys
import os
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("agent.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

def check_env():
    required = ["GEMINI_API_KEY", "NETLIFY_TOKEN", "GMAIL_USER", "GMAIL_APP_PASSWORD"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        logger.error(f"Missing environment variables: {', '.join(missing)}")
        sys.exit(1)
    logger.info("✓ All environment variables present")

def run_scraper():
    logger.info("\n" + "="*50)
    logger.info("STEP 1: Scraping Google Maps for Erftstadt")
    logger.info("="*50)
    from scraper import scrape_all
    import json
    businesses = scrape_all()
    with open("businesses_no_website.json", "w", encoding="utf-8") as f:
        json.dump([b.__dict__ if hasattr(b, '__dict__') else b for b in businesses], f, ensure_ascii=False, indent=2)
    logger.info(f"✓ Found {len(businesses)} businesses without website")
    return len(businesses)

def run_generator():
    logger.info("\n" + "="*50)
    logger.info("STEP 2: Generating websites with Claude AI")
    logger.info("="*50)
    from generator import generate_all_websites
    results = generate_all_websites()
    generated = len([r for r in results if r.get("website_generated")])
    logger.info(f"✓ Generated {generated} websites")
    return generated

def run_deployer():
    logger.info("\n" + "="*50)
    logger.info("STEP 3: Deploying to Netlify")
    logger.info("="*50)
    from deployer import deploy_all_sites
    results = deploy_all_sites()
    deployed = len([r for r in results if r.get("netlify_deployed")])
    logger.info(f"✓ Deployed {deployed} sites")
    return deployed

def run_reporter():
    logger.info("\n" + "="*50)
    logger.info("STEP 4: Sending morning report email")
    logger.info("="*50)
    from reporter import send_report
    send_report()
    logger.info("✓ Report sent!")

def main():
    logger.info("🚀 Local Web Agent starting...")
    logger.info("Location: Erftstadt, NRW, Germany")

    check_env()

    try:
        count = run_scraper()
        if count == 0:
            logger.warning("No businesses found without websites. Sending empty report.")

        run_generator()
        run_deployer()
        run_reporter()

        logger.info("\n" + "="*50)
        logger.info("✅ All done! Check your email for the morning report.")
        logger.info("="*50)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        # Try to send error report
        try:
            import smtplib
            from email.mime.text import MIMEText
            msg = MIMEText(f"Der Local Web Agent ist mit einem Fehler abgestürzt:\n\n{e}")
            msg["Subject"] = "❌ Local Web Agent - Fehler aufgetreten"
            msg["From"] = os.environ["GMAIL_USER"]
            msg["To"] = os.environ.get("REPORT_TO", os.environ["GMAIL_USER"])
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
                s.login(os.environ["GMAIL_USER"], os.environ["GMAIL_APP_PASSWORD"])
                s.sendmail(msg["From"], msg["To"], msg.as_string())
        except Exception:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()

"""
Netlify Deployer - Lädt generierte Websites auf Netlify hoch
Jeder Betrieb bekommt seine eigene Netlify-Subdomain
"""

import json
import os
import time
import logging
import requests
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

NETLIFY_TOKEN = os.environ["NETLIFY_TOKEN"]
HEADERS = {
    "Authorization": f"Bearer {NETLIFY_TOKEN}",
    "Content-Type": "application/json",
}

def create_site(site_name: str) -> dict:
    """Erstellt eine neue Netlify-Site"""
    response = requests.post(
        "https://api.netlify.com/api/v1/sites",
        headers=HEADERS,
        json={"name": site_name}
    )
    if response.status_code in (200, 201):
        return response.json()
    elif response.status_code == 422:
        # Name already taken, try with suffix
        import random
        new_name = f"{site_name}-{random.randint(100, 999)}"
        return create_site(new_name)
    else:
        raise Exception(f"Failed to create site: {response.status_code} {response.text}")

def deploy_html(site_id: str, html_content: str) -> dict:
    """Deployed HTML direkt zu einer Netlify-Site"""
    import hashlib
    import zipfile
    import io

    # Create zip with index.html
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("index.html", html_content)
    zip_buffer.seek(0)

    response = requests.post(
        f"https://api.netlify.com/api/v1/sites/{site_id}/deploys",
        headers={
            "Authorization": f"Bearer {NETLIFY_TOKEN}",
            "Content-Type": "application/zip",
        },
        data=zip_buffer.getvalue()
    )

    if response.status_code in (200, 201):
        return response.json()
    else:
        raise Exception(f"Deploy failed: {response.status_code} {response.text}")

def wait_for_deploy(deploy_id: str, timeout: int = 120) -> bool:
    """Wartet bis der Deploy fertig ist"""
    start = time.time()
    while time.time() - start < timeout:
        response = requests.get(
            f"https://api.netlify.com/api/v1/deploys/{deploy_id}",
            headers=HEADERS
        )
        if response.status_code == 200:
            state = response.json().get("state")
            if state == "ready":
                return True
            elif state in ("error", "failed"):
                return False
        time.sleep(3)
    return False

def deploy_all_sites(sites_dir: str = "generated_sites") -> list:
    """Deployed alle generierten Websites zu Netlify"""

    manifest_path = Path(sites_dir) / "manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        businesses = json.load(f)

    deployed = []

    for business in businesses:
        if not business.get("website_generated"):
            continue

        name = business.get("name", "betrieb")
        filename = business.get("website_file")

        if not filename:
            continue

        html_path = Path(sites_dir) / filename
        if not html_path.exists():
            logger.warning(f"HTML file not found: {html_path}")
            continue

        # Create URL-friendly site name
        site_name = f"erftstadt-{filename.replace('.html', '').replace('_', '-')}"
        # Netlify site names max 63 chars
        site_name = site_name[:63].rstrip('-')

        logger.info(f"Deploying: {name} → {site_name}.netlify.app")

        try:
            # Create site
            site = create_site(site_name)
            site_id = site["id"]
            actual_name = site.get("name", site_name)

            # Read HTML
            with open(html_path, "r", encoding="utf-8") as f:
                html = f.read()

            # Deploy
            deploy = deploy_html(site_id, html)
            deploy_id = deploy.get("id")

            # Wait for deploy
            if deploy_id:
                success = wait_for_deploy(deploy_id)
            else:
                success = True  # Sometimes deploy is immediate

            url = f"https://{actual_name}.netlify.app"
            admin_url = f"https://app.netlify.com/sites/{actual_name}"

            business["netlify_url"] = url
            business["netlify_admin"] = admin_url
            business["netlify_deployed"] = success

            deployed.append(business)

            if success:
                logger.info(f"  ✓ Live: {url}")
            else:
                logger.warning(f"  ⚠ Deploy pending: {url}")

            time.sleep(1)  # Rate limiting

        except Exception as e:
            logger.error(f"  ✗ Failed to deploy {name}: {e}")
            business["netlify_deployed"] = False
            business["netlify_error"] = str(e)
            deployed.append(business)

    # Update manifest with deploy info
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(businesses, f, ensure_ascii=False, indent=2)

    successful = [d for d in deployed if d.get("netlify_deployed")]
    logger.info(f"\n✓ Deployed {len(successful)}/{len(deployed)} sites to Netlify")

    return deployed

if __name__ == "__main__":
    results = deploy_all_sites()
    for r in results:
        if r.get("netlify_url"):
            print(f"{r['name']}: {r['netlify_url']}")

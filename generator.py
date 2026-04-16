"""
Website Generator - Erstellt automatisch Websites für Betriebe ohne Website
Nutzt die Google Gemini API (kostenlos) für individuelle, professionelle Website-Generierung
"""

import json
import os
import re
import logging
from pathlib import Path
from typing import Optional
import google.generativeai as genai

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

CATEGORY_STYLES = {
    "Friseur": {
        "colors": "schwarz, gold, weiß",
        "vibe": "elegant, modern, stylish",
        "emoji": "✂️",
    },
    "Handwerker": {
        "colors": "dunkelblau, orange, grau",
        "vibe": "solide, vertrauenswürdig, professionell",
        "emoji": "🔧",
    },
    "Restaurant": {
        "colors": "warmes Rot, cremeweiß, holzbraun",
        "vibe": "einladend, gemütlich, appetitlich",
        "emoji": "🍽️",
    },
    "Kosmetikstudio": {
        "colors": "rose, gold, weiß",
        "vibe": "luxuriös, feminin, gepflegt",
        "emoji": "💅",
    },
    "Physiotherapie": {
        "colors": "hellblau, grün, weiß",
        "vibe": "gesund, beruhigend, vertrauenswürdig",
        "emoji": "💪",
    },
    "Sonstiges": {
        "colors": "dunkelgrau, blau, weiß",
        "vibe": "professionell, klar, modern",
        "emoji": "🏢",
    },
}

def generate_website(business: dict) -> Optional[str]:
    """Generiert eine vollständige HTML-Website für einen Betrieb"""

    category = business.get("category", "Sonstiges")
    style = CATEGORY_STYLES.get(category, CATEGORY_STYLES["Sonstiges"])

    name = business.get("name", "Unbekannter Betrieb")
    address = business.get("address", "Erftstadt")
    phone = business.get("phone", "")
    rating = business.get("rating", "")
    reviews = business.get("reviews", "")
    hours = business.get("hours", "")
    maps_url = business.get("maps_url", "")

    prompt = f"""Du bist ein erstklassiger Webdesigner. Erstelle eine vollständige, professionelle Single-Page-Website als reinen HTML-Code für diesen lokalen Betrieb aus Erftstadt, Deutschland.

BETRIEB:
- Name: {name}
- Kategorie: {category} {style['emoji']}
- Adresse: {address}
- Telefon: {phone if phone else 'nicht bekannt'}
- Bewertung: {rating if rating else 'keine'} Sterne ({reviews if reviews else '0'} Bewertungen)
- Öffnungszeiten: {hours if hours else 'auf Anfrage'}
- Google Maps: {maps_url if maps_url else ''}

DESIGN-ANFORDERUNGEN:
- Farbpalette: {style['colors']}
- Stil: {style['vibe']}
- Vollständig responsiv (Mobile-First)
- Moderne CSS-Animationen und Hover-Effekte
- Google Fonts einbinden (passend zum Stil)
- Keine externen Bibliotheken außer Google Fonts
- Hero-Section mit dem Betriebsnamen
- Über-uns-Sektion (kreativ erfunden, aber glaubwürdig und lokal)
- Leistungen/Angebote-Sektion
- Kontakt-Sektion mit Adresse, Telefon, Öffnungszeiten
- Google Maps Embed oder Link
- Footer
- Sehr hohe Design-Qualität - KEINE generischen Templates
- Jede Website soll einzigartig aussehen

WICHTIG:
- Gib NUR den kompletten HTML-Code zurück, nichts anderes
- Keine Markdown-Backticks, kein Kommentar davor oder danach
- Starte direkt mit <!DOCTYPE html>
- Alles in einer einzigen HTML-Datei (CSS und JS inline)
- Texte auf Deutsch
- Mach die Website so überzeugend, dass der Betrieb sie wirklich nutzen würde"""

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(max_output_tokens=8000)
        )

        html = response.text.strip()

        # Clean up if markdown backticks slipped through
        if html.startswith("```"):
            html = re.sub(r'^```[a-z]*\n?', '', html)
            html = re.sub(r'\n?```$', '', html)

        if not html.startswith("<!DOCTYPE") and not html.startswith("<html"):
            logger.warning(f"Unexpected output for {name}, trying to extract HTML...")
            match = re.search(r'<!DOCTYPE html>.*</html>', html, re.DOTALL | re.IGNORECASE)
            if match:
                html = match.group(0)
            else:
                return None

        return html

    except Exception as e:
        logger.error(f"Error generating website for {name}: {e}")
        return None

def slug(name: str) -> str:
    """Erstellt einen URL-freundlichen Slug aus dem Namen"""
    s = name.lower()
    s = re.sub(r'[äöüß]', lambda m: {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss'}[m.group()], s)
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = s.strip('-')
    return s[:50]

def generate_all_websites(input_file: str = "businesses_no_website.json", output_dir: str = "generated_sites"):
    """Generiert Websites für alle Betriebe ohne Website"""

    Path(output_dir).mkdir(exist_ok=True)

    with open(input_file, "r", encoding="utf-8") as f:
        businesses = json.load(f)

    logger.info(f"Generating websites for {len(businesses)} businesses...")

    results = []

    for i, business in enumerate(businesses):
        name = business.get("name", f"business_{i}")
        logger.info(f"[{i+1}/{len(businesses)}] Generating website for: {name}")

        html = generate_website(business)

        if html:
            filename = f"{slug(name)}.html"
            filepath = Path(output_dir) / filename

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html)

            business["website_file"] = filename
            business["website_generated"] = True
            results.append(business)
            logger.info(f"  ✓ Saved: {filename}")
        else:
            business["website_generated"] = False
            results.append(business)
            logger.warning(f"  ✗ Failed: {name}")

    # Save results manifest
    with open(f"{output_dir}/manifest.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    successful = [r for r in results if r.get("website_generated")]
    logger.info(f"\n✓ Generated {len(successful)}/{len(businesses)} websites")

    return results

if __name__ == "__main__":
    results = generate_all_websites()
    print(f"\nDone! Generated {len([r for r in results if r.get('website_generated')])} websites")

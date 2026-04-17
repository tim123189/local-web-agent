"""
Google Maps Scraper - Findet lokale Betriebe ohne Website in Erftstadt
"""

import time
import json
import random
import logging
from dataclasses import dataclass, asdict
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SEARCH_QUERIES = [
    "Friseur Erftstadt",
    "Frisörsalon Erftstadt",
    "Handwerker Erftstadt",
    "Elektriker Erftstadt",
    "Klempner Erftstadt",
    "Maler Erftstadt",
    "Restaurant Erftstadt",
    "Gaststätte Erftstadt",
    "Kosmetikstudio Erftstadt",
    "Kosmetik Erftstadt",
    "Physiotherapie Erftstadt",
    "Physiotherapeut Erftstadt",
]

@dataclass
class Business:
    name: str
    category: str
    address: str
    phone: Optional[str]
    rating: Optional[str]
    reviews: Optional[str]
    hours: Optional[str]
    has_website: bool
    maps_url: Optional[str]
    description: Optional[str] = None

def get_category(query: str) -> str:
    if "friseur" in query.lower() or "frisör" in query.lower():
        return "Friseur"
    elif "handwerker" in query.lower() or "elektriker" in query.lower() or "klempner" in query.lower() or "maler" in query.lower():
        return "Handwerker"
    elif "restaurant" in query.lower() or "gaststätte" in query.lower():
        return "Restaurant"
    elif "kosmetik" in query.lower():
        return "Kosmetikstudio"
    elif "physiotherap" in query.lower():
        return "Physiotherapie"
    return "Sonstiges"

def create_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=de-DE")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def accept_cookies(driver: webdriver.Chrome):
    try:
        wait = WebDriverWait(driver, 5)
        buttons = driver.find_elements(By.XPATH, "//button[contains(., 'Alle ablehnen') or contains(., 'Akzeptieren') or contains(., 'Accept')]")
        for btn in buttons:
            if "ablehnen" in btn.text.lower() or "reject" in btn.text.lower():
                btn.click()
                return
        if buttons:
            buttons[0].click()
    except Exception:
        pass

def scrape_business_details(driver: webdriver.Chrome, listing, category: str) -> Optional[Business]:
    try:
        # Click on listing
        listing.click()
        time.sleep(random.uniform(2, 3))

        wait = WebDriverWait(driver, 10)

        # Name
        try:
            name = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1.DUwDvf, h1.fontHeadlineLarge"))).text.strip()
        except TimeoutException:
            return None

        if not name:
            return None

        # Check for website
        has_website = False
        try:
            website_elements = driver.find_elements(By.XPATH, "//a[@data-item-id='authority' or contains(@aria-label, 'Website') or contains(@aria-label, 'website')]")
            if website_elements:
                has_website = True
        except Exception:
            pass

        # Also check via button text
        try:
            web_buttons = driver.find_elements(By.XPATH, "//a[contains(@href, 'http') and not(contains(@href, 'google')) and not(contains(@href, 'maps'))]")
            data_btns = driver.find_elements(By.CSS_SELECTOR, "[data-item-id='authority']")
            if data_btns:
                has_website = True
        except Exception:
            pass

        # Address
        address = ""
        try:
            addr_el = driver.find_elements(By.CSS_SELECTOR, "[data-item-id='address'], [aria-label*='Adresse'], button[data-tooltip='Adresse kopieren']")
            if addr_el:
                address = addr_el[0].text.strip()
            if not address:
                addr_els = driver.find_elements(By.XPATH, "//button[@data-item-id='address']//div[contains(@class,'fontBodyMedium')]")
                if addr_els:
                    address = addr_els[0].text.strip()
        except Exception:
            pass

        # Phone
        phone = None
        try:
            phone_els = driver.find_elements(By.CSS_SELECTOR, "[data-item-id*='phone'], [aria-label*='Telefon'], [data-tooltip*='Nummer']")
            if phone_els:
                phone = phone_els[0].text.strip()
        except Exception:
            pass

        # Rating
        rating = None
        reviews = None
        try:
            rating_el = driver.find_elements(By.CSS_SELECTOR, "div.fontDisplayLarge, span.ceNzKf")
            if rating_el:
                rating = rating_el[0].text.strip()
            reviews_el = driver.find_elements(By.CSS_SELECTOR, "span.RDApEe, button[aria-label*='Rezension']")
            if reviews_el:
                reviews = reviews_el[0].text.strip().replace("(", "").replace(")", "")
        except Exception:
            pass

        # Hours
        hours = None
        try:
            hours_els = driver.find_elements(By.CSS_SELECTOR, "[aria-label*='Öffnungszeiten'], [data-item-id='oh']")
            if hours_els:
                hours = hours_els[0].get_attribute("aria-label") or hours_els[0].text.strip()
        except Exception:
            pass

        # Current URL
        maps_url = driver.current_url

        return Business(
            name=name,
            category=category,
            address=address,
            phone=phone,
            rating=rating,
            reviews=reviews,
            hours=hours,
            has_website=has_website,
            maps_url=maps_url,
        )

    except Exception as e:
        logger.error(f"Error scraping business details: {e}")
        return None

def scrape_query(driver: webdriver.Chrome, query: str, max_results: int = 20) -> list[Business]:
    businesses = []
    category = get_category(query)

    try:
        url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
        driver.get(url)
        time.sleep(random.uniform(3, 5))
        accept_cookies(driver)
        time.sleep(2)

        wait = WebDriverWait(driver, 15)

        # Wait for results
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='feed']")))
        except TimeoutException:
            logger.warning(f"No results feed found for: {query}")
            return businesses

        # Scroll to load more results
        feed = driver.find_element(By.CSS_SELECTOR, "div[role='feed']")
        for _ in range(3):
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", feed)
            time.sleep(random.uniform(2, 3))

        # Get all listings
        listings = driver.find_elements(By.CSS_SELECTOR, "div[role='feed'] a.hfpxzc, div[role='feed'] div.Nv2PK")
        logger.info(f"Found {len(listings)} listings for '{query}'")

        seen_names = set()

        for i, listing in enumerate(listings[:max_results]):
            try:
                business = scrape_business_details(driver, listing, category)
                if business and business.name not in seen_names:
                    seen_names.add(business.name)
                    businesses.append(business)
                    logger.info(f"  [{i+1}] {business.name} - Website: {business.has_website}")

                # Go back to results
                driver.back()
                time.sleep(random.uniform(2, 3))

                # Re-find feed and listings after back navigation
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='feed']")))
                    listings = driver.find_elements(By.CSS_SELECTOR, "div[role='feed'] a.hfpxzc, div[role='feed'] div.Nv2PK")
                except TimeoutException:
                    break

            except Exception as e:
                logger.error(f"Error processing listing {i}: {e}")
                try:
                    driver.back()
                    time.sleep(2)
                    listings = driver.find_elements(By.CSS_SELECTOR, "div[role='feed'] a.hfpxzc, div[role='feed'] div.Nv2PK")
                except Exception:
                    break

    except Exception as e:
        logger.error(f"Error scraping query '{query}': {e}")

    return businesses

def scrape_all() -> list[Business]:
    driver = create_driver()
    all_businesses = []
    seen_names = set()

    try:
        for query in SEARCH_QUERIES:
            logger.info(f"\n=== Searching: {query} ===")
            businesses = scrape_query(driver, query, max_results=15)

            for b in businesses:
                if b.name not in seen_names:
                    seen_names.add(b.name)
                    all_businesses.append(b)

            time.sleep(random.uniform(3, 6))

    finally:
        driver.quit()

    # Filter: only businesses WITHOUT website
    no_website = [b for b in all_businesses if not b.has_website]
    logger.info(f"\n=== Results ===")
    logger.info(f"Total found: {len(all_businesses)}")
    logger.info(f"Without website: {len(no_website)}")

    return no_website

if __name__ == "__main__":
    businesses = scrape_all()

    with open("businesses_no_website.json", "w", encoding="utf-8") as f:
        json.dump([asdict(b) for b in businesses], f, ensure_ascii=False, indent=2)

    logger.info(f"\nSaved {len(businesses)} businesses to businesses_no_website.json")

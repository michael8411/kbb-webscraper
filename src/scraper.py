# scraper.py

import os
import re
import time
import random
import logging
import pip_system_certs.wrapt_requests
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup, Tag
from pydantic import BaseModel, Field, ValidationError, field_validator

from utils import (
    create_session,
    get_proxy,
    get_user_agent,
    get_cached_or_request,
    test_proxy,
    setup_logging,
    config,
)

from data_processing import load_existing_data, compare_and_update_data, save_data

logger = logging.getLogger(__name__)

# ==========================================
# 1. Pydantic Data Model (The Blueprint)
# ==========================================


class Vehicle(BaseModel):
    """
    Defines the strict schema for a vehicle.
    Pydantic will automatically validate types (int, float, str)
    and ensure optional fields are handled correctly.
    """

    kbb_id: Optional[str] = Field(default=None, description="The unique KBB URL path")
    name: Optional[str] = None
    year: Optional[int] = None
    make: Optional[str] = None
    model: Optional[str] = None
    category: Optional[str] = None

    # Metrics
    price_reference: Optional[int] = Field(default=None, ge=0)  # Must be >= 0
    mpg_combined: Optional[int] = Field(default=None, ge=0)
    rating_expert: Optional[float] = Field(default=None, ge=0, le=5)  # 0.0 to 5.0
    rating_consumer: Optional[float] = Field(default=None, ge=0, le=5)

    description: Optional[str] = None

    # Custom Validator: Ensure kbb_id starts with a slash if present
    @field_validator("kbb_id")
    @classmethod
    def validate_kbb_id(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.startswith("/"):
            # We can fix it automatically or raise an error. Let's fix it.
            return f"/{v}"
        return v


# ==========================================
# 2. Parsing Helper Functions
# ==========================================


def clean_price(price: Any) -> Optional[int]:
    """Extracts integer price from string (e.g., '$25,000' -> 25000)."""
    if not price or str(price).lower() in ["none", "null", "n/a"]:
        return None
    clean_str = re.sub(r"[^\d]", "", str(price))
    try:
        return int(clean_str)
    except ValueError:
        return None


def clean_rating(rating: Any) -> Optional[float]:
    """Extracts float rating from string (e.g., '4.8' -> 4.8)."""
    if not rating or str(rating).lower() in ["none", "null", "n/a"]:
        return None
    try:
        return float(str(rating).strip())
    except ValueError:
        return None


def clean_mpg(mpg: Any) -> Optional[int]:
    """Extracts integer MPG from string (e.g., '30 MPG' -> 30)."""
    if not mpg or str(mpg).lower() in ["none", "null", "n/a"]:
        return None
    match = re.search(r"(\d+)", str(mpg))
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


# ==========================================
# 3. HTML Extraction Helpers
# ==========================================


def get_vehicle_header_info(card: Tag) -> Dict[str, Any]:
    """Extracts core identity info: Name, Year, Make, Model, Category, KBB_ID."""
    info = {}

    # 1. KBB Link (Primary ID)
    details_link = card.find("a", class_=re.compile(r"e1uau9z02"))
    if not details_link:
        details_link = card.find("a", class_=re.compile(r"ewtqiv30"))

    if details_link and details_link.has_attr("href"):
        info["kbb_id"] = details_link["href"].strip()
    else:
        raw_id = card.get("id", "unknown")
        logger.warning(f"No details link found for card {raw_id}")
        info["kbb_id"] = None

    # 2. Vehicle Name
    name_tag = card.find("h2", class_=re.compile(r"argo-heading"))
    if not name_tag:
        name_tag = card.find("a", class_=re.compile(r"css-[a-z0-9]+ ewtqiv30"))

    raw_name = name_tag.text.strip() if name_tag else None
    info["name"] = raw_name

    # 3. Parse Year, Make, Model
    year, make, model = None, None, None
    if raw_name:
        parts = raw_name.split()
        if len(parts) > 1:
            if parts[0].isdigit() and len(parts[0]) == 4:
                year = parts.pop(0)
            elif parts[-1].isdigit() and len(parts[-1]) == 4:
                year = parts.pop(-1)

            if parts:
                make = parts[0]
                model = " ".join(parts[1:])

    info["year"] = int(year) if year else None
    info["make"] = make
    info["model"] = model

    # 4. Category
    cat_div = card.find("div", class_=re.compile(r"e19qstch21"))
    info["category"] = cat_div.text.strip() if cat_div else None

    return info


def find_metric_value(card: Tag, label_text: str) -> Optional[str]:
    """Finds a value associated with a specific label by traversing up the DOM."""
    label = card.find("div", string=label_text)
    if not label:
        return None

    flex_container = label.find_parent("div", direction="horizontal")
    if not flex_container:
        curr = label
        for _ in range(3):
            if curr.parent:
                curr = curr.parent
                if "direction" in curr.attrs or len(list(curr.children)) > 1:
                    flex_container = curr
                    break

    if flex_container:
        value_div = flex_container.find("div", class_=re.compile(r"e151py7u1"))
        if not value_div:
            for child in flex_container.find_all("div", recursive=False):
                text = child.get_text()
                if (
                    any(x in text for x in ["$", "MPG"])
                    and text != label_text
                    and any(c.isdigit() for c in text)
                ):
                    value_div = child
                    break
        return value_div.text.strip() if value_div else None
    return None


def get_ratings(card: Tag) -> Dict[str, Optional[float]]:
    """Extracts ratings."""
    ratings = {"rating_expert": None, "rating_consumer": None}
    for r_type in ["Expert", "Consumer"]:
        label = card.find("div", string=r_type)
        if label and label.parent:
            score_div = label.parent.find("div", class_=re.compile(r"css-[a-z0-9]+"))
            if score_div:
                clean_txt = score_div.text.strip()
                if clean_txt.replace(".", "").isdigit():
                    key = f"rating_{r_type.lower()}"
                    ratings[key] = clean_rating(clean_txt)
    return ratings


# ==========================================
# 3. Main Extraction Orchestrator (With Pydantic)
# ==========================================


def extract_vehicle_data(card: BeautifulSoup) -> Optional[Dict[str, Any]]:
    """
    Extracts data, validates it using the Vehicle Pydantic model,
    and returns a clean dictionary. Returns None if validation fails.
    """
    # 1. Gather Raw Data
    data = get_vehicle_header_info(card)

    # 2. Pricing
    raw_price = find_metric_value(card, "Starting Price")
    if not raw_price:
        price_label = card.find("div", string="Starting Price")
        if price_label:
            parent = price_label.find_parent("div", direction="horizontal")
            if parent:
                for child in parent.find_all("div"):
                    if "$" in child.get_text():
                        raw_price = child.get_text().strip()
                        break
    data["price_reference"] = clean_price(raw_price)

    # 3. MPG
    raw_mpg = find_metric_value(card, "Combined Fuel Economy")
    data["mpg_combined"] = clean_mpg(raw_mpg)

    # 4. Ratings
    ratings = get_ratings(card)
    data.update(ratings)

    # 5. Description
    desc_div = card.find("div", class_=re.compile(r"e19qstch18"))
    if desc_div:
        desc_span = desc_div.find("span")
        data["description"] = (
            desc_span.text.strip() if desc_span else desc_div.text.strip()
        )
    else:
        data["description"] = None

    # --- PYDANTIC VALIDATION STEP ---
    try:
        # This line attempts to fit the raw data into our strict Vehicle blueprint
        vehicle = Vehicle(**data)

        # If successful, we convert it back to a clean dictionary
        # exclude_none=False ensures we keep nulls for the database
        return vehicle.model_dump()

    except ValidationError as e:
        # If data is bad (e.g. price is "Two Thousand"), this catches it!
        error_id = data.get("kbb_id") or data.get("name") or "Unknown"
        logger.error(f"❌ DATA VALIDATION FAILED for {error_id}: {e}")
        return None


# ==========================================
# 4. Main Scraper Loop
# ==========================================


def scrape_kbb_car_finder():
    base_url = config.get("BaseURL")
    data_file_path = config.get("DataFilePath")
    max_retries = int(config.get("MaxRetries", 5))
    backoff_factor = float(config.get("BackoffFactor", 0.5))

    session = create_session()
    proxy_url = get_proxy()
    proxies = {"http": proxy_url, "https": proxy_url}

    headers = {
        "User-Agent": get_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": base_url,
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    all_vehicle_data = load_existing_data(data_file_path)
    stats = {"updated": 0, "added": 0, "removed": 0}
    total_start_time = time.time()
    page = 1

    while True:
        page_start_time = time.time()
        url = f"{base_url}page-{page}/" if page > 1 else base_url
        logger.info(f"Scraping page {page}...")

        content = None
        for i in range(max_retries):
            try:
                content = get_cached_or_request(url, session, headers, proxies)
                if content:
                    break
            except Exception as e:
                sleep_time = backoff_factor * (2**i) + random.uniform(0, 1)
                logger.warning(
                    f"Error on page {page} (Attempt {i+1}): {e}. Retrying in {sleep_time:.2f}s"
                )
                time.sleep(sleep_time)

        if not content:
            logger.error(
                f"Failed to retrieve page {page} after {max_retries} attempts."
            )
            break

        soup = BeautifulSoup(content, "html.parser")
        vehicle_cards = soup.find_all("div", id=re.compile(r"^vehicle_card_\d+"))

        if not vehicle_cards:
            logger.info(f"No vehicle cards found on page {page}. Stopping.")
            if soup.find("div", class_="g-recaptcha"):
                logger.critical("CAPTCHA detected! Aborting.")
            break

        page_data = {}
        for card in vehicle_cards:
            try:
                # v_data is now guaranteed to be a valid dictionary conforming to our Schema
                # or None if validation failed
                v_data = extract_vehicle_data(card)

                if v_data:
                    # Determine Key for JSON
                    primary_id = v_data.get("kbb_id")

                    if not primary_id:
                        primary_id = card.get("id", "unknown_card")

                    unique_key = f"page_{page}_{primary_id}"
                    page_data[unique_key] = v_data

            except Exception as e:
                logger.error(f"Error processing card on page {page}: {e}")
                continue

        # Data Persistence
        updated, added, removed = compare_and_update_data(
            all_vehicle_data, page_data, page
        )

        stats["updated"] += len(updated)
        stats["added"] += len(added)
        stats["removed"] += len(removed)

        logger.info(
            f"Page {page} Results: {len(updated)} Updated, {len(added)} Added, {len(removed)} Removed"
        )

        os.makedirs(os.path.dirname(data_file_path), exist_ok=True)
        save_data(data_file_path, all_vehicle_data)

        duration = time.time() - page_start_time
        logger.info(f"Processed page {page} in {duration:.2f}s")

        delay = random.uniform(20, 60)
        logger.info(f"Sleeping {delay:.2f}s before next page...")
        time.sleep(delay)

        page += 1

    # Final Summary
    total_duration = time.time() - total_start_time
    logger.info("=" * 50)
    logger.info(f"Scraping Completed in {total_duration:.2f}s")
    logger.info(f"Total Vehicles in DB: {len(all_vehicle_data)}")
    logger.info(
        f"Session Stats: {stats['added']} Added | {stats['updated']} Updated | {stats['removed']} Removed"
    )
    logger.info("=" * 50)


if __name__ == "__main__":
    setup_logging()
    test_proxy()
    scrape_kbb_car_finder()

# scraper.py

import os
import time
import random
import logging
from typing import Dict, Any
from bs4 import BeautifulSoup

from utils import (
    create_session,
    get_proxy,
    get_user_agent,
    get_cached_or_request,
    test_proxy,
    setup_logging,
    config  # Access the configuration
)

from data_processing import (
    load_existing_data,
    compare_and_update_data,
    save_data
)

logger = logging.getLogger(__name__)

def extract_vehicle_data(card: BeautifulSoup) -> Dict[str, Any]:
    data = {}

    data['id'] = card.get('id', '').strip()

    # Extract vehicle name from <a> tag with specific class
    name_tag = card.find('a', class_='css-z66djy ewtqiv30')
    data['name'] = name_tag.text.strip() if name_tag else 'N/A'

    # Try to extract year, make, and model from 'name'
    name_parts = data['name'].split()
    year = None
    if name_parts:
        # Check if first or last part is a 4-digit year
        if name_parts[0].isdigit() and len(name_parts[0]) == 4:
            # Year is at the beginning
            year = name_parts.pop(0)
        elif name_parts[-1].isdigit() and len(name_parts[-1]) == 4:
            # Year is at the end
            year = name_parts.pop(-1)
        else:
            year = 'N/A'

    data['year'] = year if year else 'N/A'
    data['make'] = name_parts[0] if name_parts else 'N/A'
    data['model'] = ' '.join(name_parts[1:]) if len(name_parts) > 1 else 'N/A'

    # Extract category
    category_div = card.find('div', class_='css-3oc9y8 e19qstch20')
    data['category'] = category_div.text.strip() if category_div else 'N/A'

    # Verify name from <h2> tag
    name_h2 = card.find('h2', class_='css-iqcfy5 e148eed12')
    data['name_verification'] = name_h2.text.strip() if name_h2 else 'N/A'

    # Extract starting price
    price_label = card.find('div', class_='css-tpw6mp e1ma5l2g3', string='Starting Price')
    if price_label:
        price_div = price_label.find_previous('div', class_='css-fpbjth e151py7u1')
        data['starting_price'] = price_div.text.strip() if price_div else 'N/A'
    else:
        data['starting_price'] = 'N/A'

    # Extract fuel economy
    fuel_economy_label = card.find('div', class_='css-tpw6mp e1ma5l2g3', string='Combined Fuel Economy')
    if fuel_economy_label:
        fuel_economy_div = fuel_economy_label.find_previous('div', class_='css-fpbjth e151py7u1')
        data['fuel_economy'] = fuel_economy_div.text.strip() if fuel_economy_div else 'N/A'
    else:
        data['fuel_economy'] = 'N/A'

    # Initialize ratings
    data['expert_rating'] = 'N/A'
    data['consumer_rating'] = 'N/A'

    # Extract ratings
    ratings_div = card.find('div', class_='css-1ouitaz ex4y58i1')
    if ratings_div:
        # Expert Rating
        expert_divs = ratings_div.find_all('div', class_='css-hryd08')
        for div in expert_divs:
            text = div.get_text(strip=True)
            if 'Expert' in text:
                expert_rating_span = div.find('span', class_='css-1rttn8x')
                data['expert_rating'] = expert_rating_span.text.strip() if expert_rating_span else 'N/A'
                break
        else:
            data['expert_rating'] = 'N/A'

        # Consumer Rating
        consumer_div = ratings_div.find('div', class_='css-1p1bpqh')
        if consumer_div:
            consumer_rating_div = consumer_div.find('div', class_='css-1c7qqqr')
            data['consumer_rating'] = consumer_rating_div.text.strip() if consumer_rating_div else 'N/A'
    else:
        data['expert_rating'] = 'N/A'
        data['consumer_rating'] = 'N/A'

    # Extract description
    desc_div = card.find('div', class_='css-1bclrc1 e19qstch17')
    if desc_div:
        desc_span = desc_div.find('span')
        data['description'] = desc_span.text.strip() if desc_span else 'N/A'
    else:
        data['description'] = 'N/A'

    return data

def scrape_kbb_car_finder():
    """
    Scrape vehicle data from KBB Car Finder.

    This function scrapes vehicle data from the KBB Car Finder website, handling pagination
    dynamically until no more vehicle cards are found. It implements exception handling,
    retries with exponential backoff, and logs performance metrics.
    """
    base_url = config.get('BaseURL')
    data_file_path = config.get('DataFilePath')

    session = create_session()
    proxy_url = get_proxy()
    proxies = {'http': proxy_url, 'https': proxy_url}

    headers = {
        'User-Agent': get_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': base_url,
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    # Load existing data
    all_vehicle_data = load_existing_data(data_file_path)

    # Initialize cumulative counters
    total_updated = 0
    total_added = 0
    total_removed = 0

    # Start performance timing
    total_start_time = time.time()

    page = 1
    max_retries = int(config.get('MaxRetries', 5))
    backoff_factor = float(config.get('BackoffFactor', 0.5))

    while True:
        page_start_time = time.time()
        url = f"{base_url}page-{page}/" if page > 1 else base_url
        logger.info(f"Scraping page {page}")

        # Implement retries with exponential backoff
        retry_count = 0
        while retry_count < max_retries:
            try:
                content = get_cached_or_request(url, session, headers, proxies)
                if not content:
                    raise Exception("No content retrieved.")
                break
            except Exception as e:
                retry_count += 1
                sleep_time = backoff_factor * (2 ** (retry_count - 1)) + random.uniform(0, 1)
                logger.warning(f"Error retrieving page {page}: {e}. Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
        else:
            logger.error(f"Failed to retrieve page {page} after {max_retries} attempts.")
            break  # Exit the loop if content can't be retrieved

        soup = BeautifulSoup(content, 'html.parser')

        # Adjust the selectors to match the actual HTML structure
        vehicle_card_sets = soup.find_all('div', class_='css-1tzioz7 eds0yfe0')  # Update class names if needed
        vehicle_cards = []
        for card_set in vehicle_card_sets:
            cards = card_set.find_all('div', class_='ewtqiv33 css-dkiyok e11el9oi0')  # Update class names if needed
            vehicle_cards.extend(cards)

        if not vehicle_cards:
            logger.info(f"No vehicle cards found on page {page}. Stopping.")
            break  # Exit the loop when no vehicles are found

        page_vehicle_data = {}
        for card in vehicle_cards:
            try:
                vehicle_data = extract_vehicle_data(card)
                unique_id = f"page_{page}_{vehicle_data['id']}"
                page_vehicle_data[unique_id] = vehicle_data
            except Exception as e:
                logger.error(f"Error extracting data from card on page {page}: {e}")
                continue  # Skip to the next card

        updated, added, removed = compare_and_update_data(
            all_vehicle_data, page_vehicle_data, page
        )

        # Update cumulative counts
        total_updated += len(updated)
        total_added += len(added)
        total_removed += len(removed)

        logger.info(f"Page {page}: {len(updated)} updated, {len(added)} added, {len(removed)} removed")

        # Create the data directory if it doesn't exist
        os.makedirs(os.path.dirname(data_file_path), exist_ok=True)

        # Save data after each page
        save_data(data_file_path, all_vehicle_data)

        # Log performance metrics for the page
        page_duration = time.time() - page_start_time
        logger.info(f"Processed page {page} in {page_duration:.2f} seconds")

        # Implement intelligent rate limiting
        delay = random.uniform(20, 60)
        logger.info(f"Waiting for {delay:.2f} seconds before the next page")
        time.sleep(delay)

        page += 1  # Increment page number

    # Log total scraping time
    total_duration = time.time() - total_start_time
    logger.info(f"Scraping completed in {total_duration:.2f} seconds. Total vehicles scraped: {len(all_vehicle_data)}")
    logger.info(f"Total updated: {total_updated}, Total added: {total_added}, Total removed: {total_removed}")

if __name__ == "__main__":
    setup_logging()
    test_proxy()  # Test the proxy connection first
    scrape_kbb_car_finder()

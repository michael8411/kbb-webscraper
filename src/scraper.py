import os
import json
import time
import random
import logging
import hashlib
from bs4 import BeautifulSoup

from utils import (
    create_session,
    get_proxy,
    get_user_agent,
    get_cached_or_request,
    test_proxy
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def scrape_kbb_car_finder():
    base_url = "https://www.kbb.com/car-finder/"
    session = create_session()
    proxy_url = get_proxy()
    proxies = {'http': proxy_url, 'https': proxy_url}
    
    all_vehicle_data = {}
    
    for page in range(1, 331):  # Pages 1 to 330
        url = f"{base_url}page-{page}/" if page > 1 else base_url
        
        headers = {
            'User-Agent': get_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': base_url,
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        logger.info(f"Scraping page {page} of 330")
        content = get_cached_or_request(url, session, headers, proxies)
        if not content:
            logger.warning(f"Skipping page {page} due to retrieval failure")
            continue
        
        soup = BeautifulSoup(content, 'html.parser')
        
        vehicle_card_sets = soup.find_all('div', class_='css-1tzioz7 eds0yfe0')
        
        page_vehicle_data = {}
        for card_set in vehicle_card_sets:
            vehicle_cards = card_set.find_all('div', class_='ewtqiv33 css-dkiyok e11el9oi0')
            
            for card in vehicle_cards:
                vehicle_data = extract_vehicle_data(card)
                unique_id = f"page_{page}_{vehicle_data['id']}"
                page_vehicle_data[unique_id] = vehicle_data
        
        all_vehicle_data.update(page_vehicle_data)
        logger.info(f"Scraped {len(page_vehicle_data)} vehicles from page {page}")
        
        # Create the data directory if it doesn't exist 
        os.makedirs('data', exist_ok=True)
        
        # Save data after each page
        with open('data/kbb_vehicle_data.json', 'w') as f:
            json.dump(all_vehicle_data, f, indent=2)
        
        # Implement intelligent rate limiting
        delay = random.uniform(20, 60)
        logger.info(f"Waiting for {delay:.2f} seconds before the next page")
        time.sleep(delay)
    
    logger.info(f"Scraping completed. Total vehicles scraped: {len(all_vehicle_data)}")

def extract_vehicle_data(card):
    data = {}
    
    data['id'] = card.get('id', '')
    data['name'] = card.get('alt', '')
    
    make_model = data['name'].split(' ', 1)
    data['make'] = make_model[0] if len(make_model) > 0 else ''
    data['model'] = make_model[1] if len(make_model) > 1 else ''
    data['year'] = data['model'].split()[-1] if data['model'] else ''
    
    category_div = card.find('div', class_='css-3oc9y8 e19qstch20')
    data['category'] = category_div.text.strip() if category_div else 'N/A'
    
    name_h2 = card.find('h2', class_='css-iqcfy5 e148eed12')
    data['name_verification'] = name_h2.text.strip() if name_h2 else 'N/A'
    
    # Extract starting price
    price_div = card.find('div', class_='css-15j21fj e19qstch15')
    if price_div:
        price = price_div.find('div', class_='css-fpbjth e151py7u1')
        data['starting_price'] = price.text.strip() if price else 'N/A'
    else:
        data['starting_price'] = 'N/A'
    
    # Extract fuel economy and ratings
    meta_div = card.find('div', class_='css-14q4cew e19qstch18')
    if meta_div:
        # Extract fuel economy
        fuel_economy_div = meta_div.find('div', string='Combined Fuel Economy')
        if fuel_economy_div:
            fuel_economy = fuel_economy_div.find_previous('div', class_='css-fpbjth e151py7u1')
            data['fuel_economy'] = fuel_economy.text.strip() if fuel_economy else 'N/A'
        else:
            data['fuel_economy'] = 'N/A'
        
        # Extract expert and consumer ratings
        ratings_div = meta_div.find('div', class_='css-1ouitaz ex4y58i1')
        if ratings_div:
            rating_divs = ratings_div.find_all('div', class_='css-1p1bpqh')
            for rating_div in rating_divs:
                rating_type = rating_div.find('div', class_='css-hryd08').text.strip()
                rating_value = rating_div.find('div', class_='css-1c7qqqr').text.strip()
                if rating_type == 'Expert':
                    data['expert_rating'] = rating_value
                elif rating_type == 'Consumer':
                    data['consumer_rating'] = rating_value
            
            # Ensure ratings are set
            data.setdefault('expert_rating', 'N/A')
            data.setdefault('consumer_rating', 'N/A')
        else:
            data['expert_rating'] = 'N/A'
            data['consumer_rating'] = 'N/A'
    else:
        data['fuel_economy'] = 'N/A'
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

if __name__ == "__main__":
    test_proxy()  # Test the proxy connection first
    scrape_kbb_car_finder()

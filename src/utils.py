import requests
import logging
import hashlib
import os
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from fake_useragent import UserAgent
from cachetools import TTLCache


# Set up logging (assumes logging is configured in the main script)
logger = logging.getLogger(__name__)

# Set up caching
cache = TTLCache(maxsize=100, ttl=3600)  # Cache for 1 hour


def create_session():
    """Create a requests session with retry logic."""
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=0.1,
        status_forcelist=[500, 502, 503, 504]
    )
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session

# Load enviornment variables from .env file
load_dotenv()

def get_proxy():
    """Retrieve BrightData proxy configuration from .env"""
    username = os.getenv('BRIGHTDATA_USERNAME')
    password = os.getenv('BRIGHTDATA_PASSWORD')
    host = os.getenv('BRIGHTDATA_HOST')
    port = os.getenv('BRIGHTDATA_PORT')
    return f'http://{username}:{password}@{host}:{port}'

def get_user_agent():
    """Generate a random user agent string."""
    ua = UserAgent()
    return ua.random

def get_cached_or_request(url, session, headers, proxies):
    """Retrieve content from cache or make an HTTP GET request."""
    cache_key = hashlib.md5(url.encode()).hexdigest()
    if cache_key in cache:
        logger.info(f"Using cached data for {url}")
        return cache[cache_key]

    try:
        response = session.get(url, headers=headers, proxies=proxies, timeout=30)
        response.raise_for_status()
        cache[cache_key] = response.text
        logger.info(f"Successfully retrieved {url}")
        return response.text
    except requests.RequestException as e:
        logger.error(f"Failed to retrieve the page {url}: {e}")
        return None

def test_proxy():
    """Test the proxy connection."""
    session = create_session()
    proxy_url = get_proxy()
    proxies = {'http': proxy_url, 'https': proxy_url}

    try:
        response = session.get('https://geo.brdtest.com/mygeo.json', proxies=proxies)
        logger.info(f"Proxy test successful: {response.text}")
    except requests.RequestException as e:
        logger.error(f"Error testing proxy: {e}")
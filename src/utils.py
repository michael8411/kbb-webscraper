# utils.py

import os
import sys
import pip_system_certs.wrapt_requests
import logging
import hashlib
import requests
import random
import time
import configparser
from typing import Optional
from cachetools import TTLCache
from fake_useragent import UserAgent
from requests.adapters import HTTPAdapter, Retry
from dotenv import load_dotenv
import pip_system_certs.wrapt_requests

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))


def load_config(config_file="config.ini") -> configparser.SectionProxy:
    """
    Load configuration from an INI file.

    Args:
        config_file (str): The path to the configuration file.

    Returns:
        configparser.SectionProxy: The configuration parameters.
    """
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), config_file)
    config.read(config_path)
    if "DEFAULT" not in config:
        logger.error(f"DEFAULT section missing in config file: {config_path}")
        sys.exit(1)
    return config["DEFAULT"]


# Load configuration
config = load_config()


def setup_logging(log_dir="logs", max_logs=5, log_level=logging.INFO):
    """
    Set up logging configuration.

    Args:
        log_dir (str): Directory to store log files.
        max_logs (int): Maximum number of log files to keep.
        log_level (int): Logging level.
    """
    logger = logging.getLogger()
    logger.setLevel(log_level)

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_files = [f for f in os.listdir(log_dir) if f.startswith("scraper")]
    if len(log_files) >= max_logs:
        oldest_log = sorted(log_files)[0]
        os.remove(os.path.join(log_dir, oldest_log))

    log_filename = os.path.join(log_dir, f"scraper_{int(time.time())}.log")
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(log_level)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def get_proxy() -> Optional[str]:
    """
    Retrieve proxy configuration from environment variables.

    Returns:
        Optional[str]: Proxy URL if all credentials are provided, else None.
    """
    username = os.getenv("PROXY_USERNAME")
    password = os.getenv("PROXY_PASSWORD")
    host = os.getenv("PROXY_HOST")
    port = os.getenv("PROXY_PORT")

    if username and password and host and port:
        return f"http://{username}:{password}@{host}:{port}"
    else:
        logger.warning(
            "Proxy credentials not fully provided. Proceeding without proxy."
        )
        return None


def create_session() -> requests.Session:
    """
    Create a requests session with retry strategy.

    Returns:
        requests.Session: Configured requests session.
    """
    session = requests.Session()
    retries = Retry(
        total=int(config.get("MaxRetries", 5)),
        backoff_factor=float(config.get("BackoffFactor", 0.5)),
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def get_user_agent() -> str:
    """
    Get a random User-Agent string.

    Returns:
        str: Random User-Agent string.
    """
    try:
        ua = UserAgent()
        return ua.random
    except Exception as e:
        logger.warning(f"Error getting user agent: {e}")
        return "Mozilla/5.0"


def test_proxy():
    """
    Test the proxy configuration by making a simple request.
    """
    proxy_url = get_proxy()
    if proxy_url:
        proxies = {"http": proxy_url, "https": proxy_url}
        try:
            response = requests.get(
                "https://www.google.com", proxies=proxies, timeout=10
            )
            if response.status_code == 200:
                logger.info("Proxy is working.")
            else:
                logger.warning(
                    f"Proxy test failed with status code {response.status_code}."
                )
        except Exception as e:
            logger.error(f"Proxy test failed: {e}")
    else:
        logger.info("No proxy configured.")


# Initialize cache with TTL of 24 hours
cache = TTLCache(maxsize=1000, ttl=86400)


def get_cached_or_request(
    url: str,
    session: requests.Session,
    headers: dict,
    proxies: dict,
    max_retries: int = 5,
) -> Optional[str]:
    """
    Retrieve content from cache or make an HTTP GET request with retries.

    Args:
        url (str): URL to retrieve.
        session (requests.Session): Session object for making requests.
        headers (dict): Headers to include in the request.
        proxies (dict): Proxies to use for the request.
        max_retries (int): Maximum number of retries.

    Returns:
        Optional[str]: The content retrieved from the URL or None if failed.
    """
    cache_key = hashlib.md5(url.encode()).hexdigest()
    if cache_key in cache:
        logger.info(f"Using cached data for {url}")
        return cache[cache_key]

    retry_count = 0
    backoff_factor = float(config.get("BackoffFactor", 0.5))
    while retry_count < max_retries:
        try:
            response = session.get(
                url, headers=headers, proxies=proxies, timeout=30, verify=False
            )
            response.raise_for_status()
            cache[cache_key] = response.text
            logger.info(f"Successfully retrieved {url}")
            return response.text
        except requests.RequestException as e:
            retry_count += 1
            sleep_time = backoff_factor * (2 ** (retry_count - 1)) + random.uniform(
                0, 1
            )
            logger.warning(
                f"Request failed ({retry_count}/{max_retries}) for {url}: {e}. Retrying in {sleep_time:.2f} seconds..."
            )
            time.sleep(sleep_time)
    logger.error(f"Failed to retrieve the page {url} after {max_retries} attempts.")
    return None

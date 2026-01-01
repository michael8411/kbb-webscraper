import os
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

_supabase_client = None


def get_supabase_client() -> Client:
    """
    Singleton pattern to get the supabase client.
    """
    global _supabase_client
    if _supabase_client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        if not url or not key:
            logger.error("SUPABASE_URL or SUPABASE_KEY is not set")
            raise ValueError("SUPABASE_URL or SUPABASE_KEY is not set")

        _supabase_client = create_client(url, key)
    return _supabase_client


def close_supabase_client():
    """
    Close the supabase client.
    """
    global _supabase_client
    if _supabase_client:
        _supabase_client.close()
        _supabase_client = None

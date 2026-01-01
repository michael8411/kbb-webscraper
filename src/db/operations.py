import logging
import re
from typing import Dict, Any, Optional
from .supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


def parse_price(price_str: str) -> Optional[float]:
    """Converts '$32,315' to 32315.0"""
    if not price_str or not isinstance(price_str, str) or price_str == "N/A":
        return None
    clean_str = price_str.replace("$", "").replace(",", "").strip()
    try:
        return float(clean_str)
    except ValueError:
        return None


def parse_mpg(mpg_str: str) -> Optional[int]:
    """Converts '30 MPG' to 30"""
    if not mpg_str or not isinstance(mpg_str, str) or mpg_str == "N/A":
        return None
    # Extract first number found
    import re

    match = re.search(r"\d+", mpg_str)
    if match:
        return int(match.group())
    return None


def parse_rating(rating_str: str) -> Optional[float]:
    """Converts '4.8' to 4.8"""
    if not rating_str or rating_str == "N/A":
        return None
    try:
        return float(rating_str)
    except ValueError:
        return None


def upsert_vehicle_batch(vehicles_data: Dict[str, Any]) -> int:
    """Upserts a batch of vehicles into the database."""
    supabase = get_supabase_client()

    records_to_upsert = []

    for unique_id, data in vehicles_data.items():
        # Critical Check: Ensure kbb_id is present
        # Supabase will reject rows with null kbb_id because it is the unique constraint/primary key
        # If scraper extraction failed to get URL, we try fallback to ID, otherwise skip
        kbb_id = data.get("kbb_id")
        if not kbb_id:
            # Try fallback to scraper's 'id' field if available (e.g. vehicle_card_123)
            fallback_id = data.get("id")
            if fallback_id:
                kbb_id = f"card_{fallback_id}"
            else:
                logger.warning(
                    f"Skipping vehicle '{data.get('name')}' - Missing kbb_id and no fallback ID."
                )
                continue

        record = {
            "kbb_id": kbb_id,  # Use the validated ID
            "name": data.get("name"),
            "year": data.get("year"),
            "make": data.get("make"),
            "model": data.get("model"),
            "category": data.get("category"),
            "price_reference": data.get("price_reference"),
            "mpg_combined": data.get("mpg_combined"),
            "rating_expert": data.get("rating_expert"),
            "rating_consumer": data.get("rating_consumer"),
            "description": data.get("description"),
            "updated_at": "now()",
        }
        records_to_upsert.append(record)

    if not records_to_upsert:
        return 0

    try:
        response = (
            supabase.table("vehicles")
            .upsert(records_to_upsert, on_conflict="kbb_id")
            .execute()
        )
        count = len(records_to_upsert)
        logger.info(f"Successfully upserted {count} vehicles to supabase")
        return count
    except Exception as e:
        logger.error(f"Error upserting vehicles to supabase: {e}")
        return 0

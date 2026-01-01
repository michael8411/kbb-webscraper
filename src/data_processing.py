# data_processing.py

import json
import logging
from typing import Dict, Any, Tuple, List

logger = logging.getLogger(__name__)


def load_existing_data(file_path: str) -> Dict[str, Any]:
    """
    Load existing data from a JSON file.

    Args:
        file_path (str): The path to the JSON file containing existing data.

    Returns:
        Dict[str, Any]: A dictionary containing the loaded data.
    """
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            logger.info(f"Loaded existing data from {file_path}")
            logger.debug(f"Loaded data contains {len(data)} entries")
            return data
    except FileNotFoundError:
        logger.info(f"No existing data found at {file_path}. Starting fresh.")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {file_path}: {e}. Starting fresh.")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error loading data from {file_path}: {e}")
        return {}


def compare_and_update_data(
    all_data: Dict[str, Any], new_page_data: Dict[str, Any], page_number: int
) -> Tuple[List[str], List[str], List[str]]:
    """
    Compare new data with existing data and update intelligently.

    Args:
        all_data (Dict[str, Any]): The complete dataset containing all entries.
        new_page_data (Dict[str, Any]): The new data extracted from the current page.
        page_number (int): The page number being processed.

    Returns:
        Tuple[List[str], List[str], List[str]]:
            - updated (List[str]): List of keys for entries that were updated.
            - added (List[str]): List of keys for entries that were added.
            - removed (List[str]): List of keys for entries that were removed.
    """
    updated = []
    added = []
    removed = []

    # Identify existing entries for this page
    existing_page_keys = [
        key for key in all_data if key.startswith(f"page_{page_number}_")
    ]

    # Check for updated or new entries
    for key, new_entry in new_page_data.items():
        if key in all_data:
            if all_data[key] != new_entry:
                all_data[key] = new_entry
                updated.append(key)
        else:
            all_data[key] = new_entry
            added.append(key)

    # Identify removed entries
    for key in existing_page_keys:
        if key not in new_page_data:
            del all_data[key]
            removed.append(key)

    # Log detailed changes at the debug level
    if updated:
        logger.debug(f"Updated entries on page {page_number}: {updated}")
    if added:
        logger.debug(f"Added entries on page {page_number}: {added}")
    if removed:
        logger.debug(f"Removed entries on page {page_number}: {removed}")

    return updated, added, removed


def save_data(file_path: str, data: Dict[str, Any]) -> None:
    """
    Save data to a JSON file.

    Args:
        file_path (str): The path to the JSON file where data will be saved.
        data (Dict[str, Any]): The data to be saved.
    """
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Data saved to {file_path}")
        logger.debug(f"Saved data contains {len(data)} entries")
    except (IOError, TypeError, json.JSONEncodeError) as e:
        logger.error(f"Failed to save data to {file_path}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error saving data to {file_path}: {e}")

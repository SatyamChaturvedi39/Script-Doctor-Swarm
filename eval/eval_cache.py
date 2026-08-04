"""
Evaluation Cache Manager.

Stores and retrieves intermediate evaluation results in `eval/results/eval_cache.json`.
Allows skipping previously completed test cases to save API quota and resume interrupted runs.
"""

from __future__ import annotations

import json
import logging
import os

logger = logging.getLogger("script_doctor.eval.cache")

CACHE_FILE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "results", "eval_cache.json"
)


def load_cache() -> dict:
    """Load the current eval cache from disk."""
    if os.path.exists(CACHE_FILE_PATH):
        try:
            with open(CACHE_FILE_PATH, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Could not read eval_cache.json: %s", e)
    return {}


def save_cache(cache_data: dict) -> None:
    """Persist cache data to disk."""
    os.makedirs(os.path.dirname(CACHE_FILE_PATH), exist_ok=True)
    with open(CACHE_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, indent=2)


def get_cached_result(cache_key: str, force: bool = False) -> dict | None:
    """
    Retrieve a cached test case result if it exists and contains no errors.
    Returns None if force=True or if the key is missing/failed.
    """
    if force:
        return None
    cache = load_cache()
    result = cache.get(cache_key)
    if result and isinstance(result, dict) and "error" not in result:
        return result
    return None


def set_cached_result(cache_key: str, data: dict) -> None:
    """Cache a successful test case result immediately to disk."""
    if isinstance(data, dict) and "error" in data:
        return  # Do not cache failed runs
    cache = load_cache()
    cache[cache_key] = data
    save_cache(cache)
    logger.info("[CACHE SAVED] %s stored to eval_cache.json", cache_key)


def clear_cache() -> None:
    """Remove the eval_cache.json file."""
    if os.path.exists(CACHE_FILE_PATH):
        try:
            os.remove(CACHE_FILE_PATH)
            logger.info("[CACHE CLEARED] Removed eval_cache.json")
        except Exception as e:
            logger.warning("Failed to clear cache file: %s", e)

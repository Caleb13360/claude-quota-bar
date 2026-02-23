#!/usr/bin/env python3
"""
Reads cached usage data scraped by scrape_usage.sh.
Kicks off a background scrape when the cache is stale.
"""

import json
import os
import subprocess
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.parent
CACHE_PATH = SCRIPT_DIR / "data" / "usage_cache.json"
SCRAPE_SCRIPT = SCRIPT_DIR / "scrape_usage.sh"
CACHE_MAX_AGE = 30  # seconds


def _load_cache() -> dict | None:
    """Load cached usage data."""
    try:
        if CACHE_PATH.exists():
            with open(CACHE_PATH, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return None


def _trigger_scrape():
    """Kick off the scrape script in the background."""
    try:
        subprocess.Popen(
            ['bash', str(SCRAPE_SCRIPT)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception:
        pass


def get_usage() -> dict | None:
    """Get usage data from cache. Trigger background refresh if stale."""
    data = _load_cache()

    if data:
        age = time.time() - data.get('scraped_at', 0)
        if age > CACHE_MAX_AGE:
            _trigger_scrape()
        return data
    else:
        # No cache at all — trigger scrape, return None for now
        _trigger_scrape()
        return None

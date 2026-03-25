"""Cache curated results to avoid re-running Claude unnecessarily."""

import json
import logging
from datetime import datetime
from pathlib import Path

from src.config import DATA_DIR

logger = logging.getLogger(__name__)

CURATED_DIR: Path = DATA_DIR / "curated"


def _ensure_dir() -> None:
    CURATED_DIR.mkdir(parents=True, exist_ok=True)


def _today_path() -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    return CURATED_DIR / f"curated_{today}.json"


def save_curated(data: list[dict]) -> Path:
    """Save curated results to a date-stamped JSON file.

    Returns the path of the saved file.
    """
    _ensure_dir()
    filepath = _today_path()
    filepath.write_text(json.dumps(data, indent=2))
    logger.info(f"Cached curated results to {filepath}")
    return filepath


def load_curated(force: bool = False) -> list[dict] | None:
    """Load today's cached curated results.

    Returns None if:
    - force=True (bypass cache)
    - No cache file exists for today
    """
    if force:
        return None

    filepath = _today_path()
    if not filepath.exists():
        return None

    try:
        data = json.loads(filepath.read_text())
        logger.info(f"Loaded cached curation from {filepath}")
        return data
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to load cache: {e}")
        return None

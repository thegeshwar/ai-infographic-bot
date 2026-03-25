"""Session persistence for Playwright browser state.

Saves and loads cookies/localStorage per platform so that repeated logins
are avoided.  Sessions are stored as JSON in data/sessions/<platform>.json.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Optional

from src.config import DATA_DIR

logger = logging.getLogger(__name__)

DEFAULT_SESSIONS_DIR = DATA_DIR / "sessions"


def _sessions_dir(sessions_dir: Optional[Path] = None) -> Path:
    d = sessions_dir or DEFAULT_SESSIONS_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_session(
    platform: str,
    state: dict[str, Any],
    *,
    sessions_dir: Optional[Path] = None,
) -> Path:
    """Persist Playwright storage state for *platform*.

    Parameters
    ----------
    platform:
        e.g. "twitter", "linkedin", "instagram"
    state:
        The dict returned by ``browser_context.storage_state()``.
    sessions_dir:
        Override the default directory (useful for tests).

    Returns
    -------
    Path to the saved JSON file.
    """
    d = _sessions_dir(sessions_dir)
    filepath = d / f"{platform}.json"
    payload = {
        "saved_at": time.time(),
        "state": state,
    }
    filepath.write_text(json.dumps(payload, indent=2))
    logger.info("Saved session for %s → %s", platform, filepath)
    return filepath


def load_session(
    platform: str,
    *,
    sessions_dir: Optional[Path] = None,
) -> Optional[dict[str, Any]]:
    """Load a previously saved session, or return None if absent."""
    d = _sessions_dir(sessions_dir)
    filepath = d / f"{platform}.json"
    if not filepath.exists():
        return None
    try:
        data = json.loads(filepath.read_text())
        return data["state"]
    except (json.JSONDecodeError, KeyError) as exc:
        logger.warning("Corrupt session file for %s: %s", platform, exc)
        return None


def is_session_expired(
    platform: str,
    *,
    max_age_hours: float = 24,
    sessions_dir: Optional[Path] = None,
) -> bool:
    """Return True if the session file is missing or older than *max_age_hours*."""
    d = _sessions_dir(sessions_dir)
    filepath = d / f"{platform}.json"
    if not filepath.exists():
        return True
    try:
        data = json.loads(filepath.read_text())
        saved_at = data["saved_at"]
        age_hours = (time.time() - saved_at) / 3600
        return age_hours > max_age_hours
    except (json.JSONDecodeError, KeyError):
        return True

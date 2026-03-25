"""History tracking — prevents re-posting of already-published stories."""

import json
from datetime import datetime
from pathlib import Path

# Default history file location
_DEFAULT_HISTORY = Path(__file__).parent.parent / "data" / "history.json"


def _load(history_file: Path) -> list[dict]:
    """Load history entries from JSON file."""
    if not history_file.exists():
        return []
    try:
        return json.loads(history_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _save(entries: list[dict], history_file: Path) -> None:
    """Save history entries to JSON file."""
    history_file.parent.mkdir(parents=True, exist_ok=True)
    history_file.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def is_posted(url: str, history_file: Path = _DEFAULT_HISTORY) -> bool:
    """Check if a story URL has already been posted.

    Args:
        url: The story URL to check.
        history_file: Path to history JSON file.

    Returns:
        True if the URL exists in posting history.
    """
    entries = _load(history_file)
    return any(entry["url"] == url for entry in entries)


def record_post(
    story: dict,
    platform: str,
    image_path: str,
    history_file: Path = _DEFAULT_HISTORY,
) -> None:
    """Record a successful post to history.

    Args:
        story: Story dict with at least 'url' and 'headline' keys.
        platform: Platform name (e.g. 'twitter', 'linkedin').
        image_path: Path to the generated infographic image.
        history_file: Path to history JSON file.
    """
    entries = _load(history_file)
    entries.append(
        {
            "url": story["url"],
            "title": story["headline"],
            "platform": platform,
            "image_path": str(image_path),
            "timestamp": datetime.now().isoformat(),
        }
    )
    _save(entries, history_file)


def get_history(history_file: Path = _DEFAULT_HISTORY) -> list[dict]:
    """Return all history entries.

    Args:
        history_file: Path to history JSON file.

    Returns:
        List of history entry dicts.
    """
    return _load(history_file)

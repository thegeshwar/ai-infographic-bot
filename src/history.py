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


def is_posted(identifier: str, history_file: Path = _DEFAULT_HISTORY) -> bool:
    """Check if a story has already been posted.

    Args:
        identifier: Story identifier (original_title or URL) to check.
        history_file: Path to history JSON file.

    Returns:
        True if the identifier exists in posting history.
    """
    if not identifier:
        return False
    entries = _load(history_file)
    return any(
        entry.get("url") == identifier or entry.get("title") == identifier
        for entry in entries
    )


def record_post(
    story: dict,
    platform: str,
    image_path: str,
    history_file: Path = _DEFAULT_HISTORY,
    key: str = "url",
) -> None:
    """Record a successful post to history.

    Args:
        story: Story dict (curated format with 'headline', 'original_title', etc.).
        platform: Platform name (e.g. 'twitter', 'linkedin').
        image_path: Path to the generated infographic image.
        history_file: Path to history JSON file.
        key: Which story field to use as the URL identifier.
    """
    entries = _load(history_file)
    entries.append(
        {
            "url": story.get(key, story.get("headline", "")),
            "title": story.get("headline", ""),
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

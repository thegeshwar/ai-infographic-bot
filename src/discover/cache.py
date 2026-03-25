"""File-based cache with TTL and rate limiting for news fetching."""

from __future__ import annotations

import json
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .scraper import Story


class CacheManager:
    """Simple file-based JSON cache with per-source TTL and rate limiting.

    Cached files are stored as ``<cache_dir>/<source_key>.json`` with structure:
    ``{"fetched_at": <epoch>, "stories": [...]}``.
    """

    def __init__(
        self,
        cache_dir: Path | str = "data/cache",
        ttl_seconds: int = 3600,
        min_fetch_interval: int = 300,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds
        self.min_fetch_interval = min_fetch_interval

    def _path(self, source_key: str) -> Path:
        safe = source_key.replace(" ", "_").replace("/", "_")
        return self.cache_dir / f"{safe}.json"

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def write(self, source_key: str, stories: list[Story]) -> None:
        """Persist stories to a JSON cache file."""
        payload = {
            "fetched_at": time.time(),
            "stories": [_story_to_dict(s) for s in stories],
        }
        self._path(source_key).write_text(json.dumps(payload, default=str))

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def read(self, source_key: str) -> list[Story] | None:
        """Read cached stories if they exist and are not expired.

        Returns ``None`` if the cache file is missing or expired.
        """
        path = self._path(source_key)
        if not path.exists():
            return None

        data = json.loads(path.read_text())
        fetched_at = data.get("fetched_at", 0)
        if time.time() - fetched_at > self.ttl_seconds:
            return None

        # Lazy import to avoid circular dependency at module level
        from .scraper import Story  # noqa: F811

        return [
            Story(
                title=d["title"],
                url=d["url"],
                summary=d["summary"],
                source=d["source"],
                published=_parse_dt(d.get("published")),
                tags=d.get("tags", []),
            )
            for d in data.get("stories", [])
        ]

    # ------------------------------------------------------------------
    # Rate limiting
    # ------------------------------------------------------------------

    def should_fetch(self, source_key: str) -> bool:
        """Return True if enough time has elapsed since the last fetch."""
        path = self._path(source_key)
        if not path.exists():
            return True
        data = json.loads(path.read_text())
        elapsed = time.time() - data.get("fetched_at", 0)
        return elapsed >= self.min_fetch_interval


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _story_to_dict(story: Story) -> dict:
    from .scraper import Story as _S  # noqa: F811
    return {
        "title": story.title,
        "url": story.url,
        "summary": story.summary,
        "source": story.source,
        "published": story.published.isoformat() if story.published else None,
        "tags": story.tags,
    }


def _parse_dt(val: str | None) -> datetime | None:
    if not val or val == "None":
        return None
    try:
        return datetime.fromisoformat(val)
    except (ValueError, TypeError):
        return None

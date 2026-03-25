"""Multi-source news scraper for AI/ML content."""

import logging
from dataclasses import dataclass, field
from datetime import datetime

import feedparser
import httpx

from .sources import SOURCES, Source

logger = logging.getLogger(__name__)


@dataclass
class Story:
    title: str
    url: str
    summary: str
    source: str
    published: datetime | None = None
    tags: list[str] = field(default_factory=list)


def _fetch_rss(source: Source) -> list[Story]:
    """Fetch stories from an RSS feed."""
    stories = []
    try:
        resp = httpx.get(source.url, timeout=15, follow_redirects=True)
        feed = feedparser.parse(resp.text)
        for entry in feed.entries[:20]:
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])
            stories.append(Story(
                title=entry.get("title", ""),
                url=entry.get("link", ""),
                summary=entry.get("summary", "")[:500],
                source=source.name,
                published=published,
            ))
    except Exception as e:
        logger.warning(f"Failed to fetch {source.name}: {e}")
    return stories


def discover_stories() -> list[Story]:
    """Discover stories from all configured sources."""
    all_stories = []
    for source in SOURCES:
        if source.source_type == "rss":
            all_stories.extend(_fetch_rss(source))
        else:
            logger.info(f"Skipping unsupported source type: {source.source_type}")
    logger.info(f"Discovered {len(all_stories)} stories from {len(SOURCES)} sources")
    return all_stories

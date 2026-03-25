"""Multi-source news scraper for AI/ML content."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urljoin

import feedparser
import httpx
from bs4 import BeautifulSoup

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


# ---------------------------------------------------------------------------
# RSS
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# NewsAPI
# ---------------------------------------------------------------------------

def _fetch_newsapi(source: Source, api_key: str) -> list[Story]:
    """Fetch AI/ML articles from NewsAPI.

    Queries the ``/v2/everything`` endpoint with AI-related keywords.
    """
    stories: list[Story] = []
    if not api_key:
        logger.info("NEWSAPI_KEY not configured, skipping NewsAPI source")
        return stories

    try:
        resp = httpx.get(
            source.url,
            params={
                "q": "artificial intelligence OR machine learning OR LLM",
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 20,
                "apiKey": api_key,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        for article in data.get("articles", []):
            published = None
            pub_str = article.get("publishedAt")
            if pub_str:
                try:
                    published = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    pass

            stories.append(Story(
                title=article.get("title", ""),
                url=article.get("url", ""),
                summary=(article.get("description") or "")[:500],
                source=source.name,
                published=published,
            ))
    except Exception as e:
        logger.warning(f"Failed to fetch NewsAPI: {e}")

    return stories


# ---------------------------------------------------------------------------
# Web scraping fallback
# ---------------------------------------------------------------------------

def _fetch_scrape(source: Source) -> list[Story]:
    """Scrape article links from a web page using httpx + BeautifulSoup.

    Looks for ``<article>`` elements containing ``<h2>`` headings with links,
    which is a common pattern on news sites.
    """
    stories: list[Story] = []
    try:
        resp = httpx.get(
            source.url,
            timeout=15,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; AIInfoBot/1.0)"},
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for article in soup.find_all("article")[:20]:
            heading = article.find(["h2", "h3"])
            if not heading:
                continue
            link = heading.find("a", href=True)
            if not link:
                continue

            title = link.get_text(strip=True)
            href = link["href"]
            url = urljoin(source.url, href)

            summary_el = article.find("p")
            summary = summary_el.get_text(strip=True)[:500] if summary_el else ""

            if title and url:
                stories.append(Story(
                    title=title,
                    url=url,
                    summary=summary,
                    source=source.name,
                ))
    except Exception as e:
        logger.warning(f"Failed to scrape {source.name}: {e}")

    return stories


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def discover_stories() -> list[Story]:
    """Discover stories from all configured sources."""
    from src.config import NEWSAPI_KEY  # lazy to avoid circular at import time

    all_stories: list[Story] = []
    for source in SOURCES:
        if source.source_type == "rss":
            all_stories.extend(_fetch_rss(source))
        elif source.source_type == "api":
            all_stories.extend(_fetch_newsapi(source, api_key=NEWSAPI_KEY))
        elif source.source_type == "scrape":
            all_stories.extend(_fetch_scrape(source))
        else:
            logger.info(f"Skipping unsupported source type: {source.source_type}")

    logger.info(f"Discovered {len(all_stories)} stories from {len(SOURCES)} sources")
    return all_stories

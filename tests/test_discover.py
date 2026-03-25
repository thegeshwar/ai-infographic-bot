"""Comprehensive tests for the discover module."""

import json
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.discover.scraper import Story, _fetch_rss, _fetch_newsapi, _fetch_scrape
from src.discover.sources import SOURCES, Source
from src.discover.dedup import deduplicate
from src.discover.cache import CacheManager


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

SAMPLE_RSS_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item>
      <title>New GPT-5 Model Released</title>
      <link>https://example.com/gpt5</link>
      <description>OpenAI releases GPT-5 with improved reasoning.</description>
      <pubDate>Mon, 24 Mar 2025 12:00:00 GMT</pubDate>
    </item>
    <item>
      <title>LLM Benchmarks Updated</title>
      <link>https://example.com/benchmarks</link>
      <description>New benchmarks for evaluating large language models.</description>
      <pubDate>Sun, 23 Mar 2025 10:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""

SAMPLE_NEWSAPI_RESPONSE = {
    "status": "ok",
    "totalResults": 2,
    "articles": [
        {
            "title": "AI Startup Raises $100M",
            "url": "https://news.example.com/ai-startup",
            "description": "A new AI startup has raised $100M in Series B funding.",
            "source": {"name": "TechNews"},
            "publishedAt": "2025-03-24T14:30:00Z",
        },
        {
            "title": "Machine Learning in Healthcare",
            "url": "https://news.example.com/ml-healthcare",
            "description": "How ML is transforming diagnostics.",
            "source": {"name": "HealthTech"},
            "publishedAt": "2025-03-23T09:00:00Z",
        },
    ],
}

SAMPLE_HTML_PAGE = """\
<html>
<head><title>AI News Site</title></head>
<body>
  <article>
    <h2><a href="https://ainews.example.com/story1">Breakthrough in Reinforcement Learning</a></h2>
    <p>Researchers achieve new SOTA on Atari benchmarks.</p>
  </article>
  <article>
    <h2><a href="https://ainews.example.com/story2">New Transformer Architecture</a></h2>
    <p>A novel attention mechanism reduces compute by 40%.</p>
  </article>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Source definitions
# ---------------------------------------------------------------------------

def test_sources_defined():
    assert len(SOURCES) > 0
    for source in SOURCES:
        assert source.name
        assert source.url
        assert source.source_type in ("rss", "api", "scrape")


def test_sources_include_all_types():
    """Sources should include rss, api, and scrape types."""
    types = {s.source_type for s in SOURCES}
    assert "rss" in types
    assert "api" in types
    assert "scrape" in types


# ---------------------------------------------------------------------------
# RSS parsing
# ---------------------------------------------------------------------------

@patch("src.discover.scraper.httpx.get")
def test_fetch_rss_parses_entries(mock_get):
    mock_resp = MagicMock()
    mock_resp.text = SAMPLE_RSS_XML
    mock_get.return_value = mock_resp

    source = Source("TestFeed", "https://example.com/feed", "rss")
    stories = _fetch_rss(source)

    assert len(stories) == 2
    assert stories[0].title == "New GPT-5 Model Released"
    assert stories[0].url == "https://example.com/gpt5"
    assert stories[0].source == "TestFeed"
    assert stories[0].published is not None
    assert isinstance(stories[0].published, datetime)


@patch("src.discover.scraper.httpx.get")
def test_fetch_rss_handles_failure(mock_get):
    mock_get.side_effect = Exception("Connection error")
    source = Source("BadFeed", "https://bad.example.com/feed", "rss")
    stories = _fetch_rss(source)
    assert stories == []


# ---------------------------------------------------------------------------
# NewsAPI parsing
# ---------------------------------------------------------------------------

@patch("src.discover.scraper.httpx.get")
def test_fetch_newsapi_parses_articles(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = SAMPLE_NEWSAPI_RESPONSE
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    source = Source("NewsAPI AI", "https://newsapi.org/v2/everything", "api")
    stories = _fetch_newsapi(source, api_key="fake-key")

    assert len(stories) == 2
    assert stories[0].title == "AI Startup Raises $100M"
    assert stories[0].url == "https://news.example.com/ai-startup"
    assert stories[0].source == "NewsAPI AI"
    assert stories[0].published is not None


@patch("src.discover.scraper.httpx.get")
def test_fetch_newsapi_handles_failure(mock_get):
    mock_get.side_effect = Exception("API error")
    source = Source("NewsAPI AI", "https://newsapi.org/v2/everything", "api")
    stories = _fetch_newsapi(source, api_key="fake-key")
    assert stories == []


@patch("src.discover.scraper.httpx.get")
def test_fetch_newsapi_handles_empty_response(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"status": "ok", "totalResults": 0, "articles": []}
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    source = Source("NewsAPI AI", "https://newsapi.org/v2/everything", "api")
    stories = _fetch_newsapi(source, api_key="fake-key")
    assert stories == []


# ---------------------------------------------------------------------------
# Web scraping
# ---------------------------------------------------------------------------

@patch("src.discover.scraper.httpx.get")
def test_fetch_scrape_extracts_articles(mock_get):
    mock_resp = MagicMock()
    mock_resp.text = SAMPLE_HTML_PAGE
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    source = Source("AI News Site", "https://ainews.example.com", "scrape")
    stories = _fetch_scrape(source)

    assert len(stories) >= 2
    assert stories[0].title == "Breakthrough in Reinforcement Learning"
    assert stories[0].url == "https://ainews.example.com/story1"
    assert stories[0].source == "AI News Site"


@patch("src.discover.scraper.httpx.get")
def test_fetch_scrape_handles_failure(mock_get):
    mock_get.side_effect = Exception("Connection refused")
    source = Source("Bad Site", "https://bad.example.com", "scrape")
    stories = _fetch_scrape(source)
    assert stories == []


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def _make_story(title: str, url: str, source: str = "Test") -> Story:
    return Story(title=title, url=url, summary="", source=source)


def test_dedup_exact_url():
    """Exact duplicate URLs should be removed."""
    stories = [
        _make_story("Story A", "https://example.com/a"),
        _make_story("Story A copy", "https://example.com/a"),
        _make_story("Story B", "https://example.com/b"),
    ]
    result = deduplicate(stories)
    assert len(result) == 2
    urls = [s.url for s in result]
    assert "https://example.com/a" in urls
    assert "https://example.com/b" in urls


def test_dedup_similar_titles():
    """Stories with very similar titles but different URLs should be deduplicated."""
    stories = [
        _make_story("OpenAI Releases New GPT-5 Model", "https://a.com/1"),
        _make_story("OpenAI Releases New GPT-5 Model Today", "https://b.com/2"),
        _make_story("Completely Different Story About Robotics", "https://c.com/3"),
    ]
    result = deduplicate(stories)
    assert len(result) == 2
    titles = [s.title for s in result]
    assert "Completely Different Story About Robotics" in titles


def test_dedup_keeps_different_stories():
    """Distinct stories should all be kept."""
    stories = [
        _make_story("AI in Healthcare", "https://a.com/1"),
        _make_story("Quantum Computing Breakthrough", "https://b.com/2"),
        _make_story("New Robotics Framework Released", "https://c.com/3"),
    ]
    result = deduplicate(stories)
    assert len(result) == 3


def test_dedup_empty_list():
    assert deduplicate([]) == []


def test_dedup_single_story():
    stories = [_make_story("Only Story", "https://a.com/1")]
    assert len(deduplicate(stories)) == 1


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

def test_cache_write_and_read(tmp_path):
    cm = CacheManager(cache_dir=tmp_path, ttl_seconds=3600)
    stories = [
        _make_story("Cached Story", "https://example.com/cached"),
    ]
    cm.write("test_source", stories)
    loaded = cm.read("test_source")
    assert loaded is not None
    assert len(loaded) == 1
    assert loaded[0].title == "Cached Story"


def test_cache_expiry(tmp_path):
    cm = CacheManager(cache_dir=tmp_path, ttl_seconds=1)
    stories = [_make_story("Expiring", "https://example.com/expire")]
    cm.write("expire_src", stories)

    # Immediately should be valid
    assert cm.read("expire_src") is not None

    # After TTL expires, should return None
    time.sleep(1.1)
    assert cm.read("expire_src") is None


def test_cache_miss(tmp_path):
    cm = CacheManager(cache_dir=tmp_path, ttl_seconds=3600)
    assert cm.read("nonexistent") is None


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

def test_rate_limit_blocks_recent_fetch(tmp_path):
    cm = CacheManager(cache_dir=tmp_path, ttl_seconds=3600, min_fetch_interval=60)
    stories = [_make_story("Rate limited", "https://example.com/rl")]
    cm.write("rl_source", stories)

    # Should be rate-limited (fetched just now)
    assert cm.should_fetch("rl_source") is False


def test_rate_limit_allows_after_interval(tmp_path):
    cm = CacheManager(cache_dir=tmp_path, ttl_seconds=3600, min_fetch_interval=1)
    stories = [_make_story("Old", "https://example.com/old")]
    cm.write("old_source", stories)

    time.sleep(1.1)
    assert cm.should_fetch("old_source") is True


def test_rate_limit_allows_new_source(tmp_path):
    cm = CacheManager(cache_dir=tmp_path, ttl_seconds=3600, min_fetch_interval=60)
    assert cm.should_fetch("brand_new_source") is True

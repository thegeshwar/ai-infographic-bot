"""Basic tests for the discover module."""

from src.discover.sources import SOURCES


def test_sources_defined():
    assert len(SOURCES) > 0
    for source in SOURCES:
        assert source.name
        assert source.url
        assert source.source_type in ("rss", "api", "scrape")

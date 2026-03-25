"""Deduplication of news stories by URL and title similarity."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .scraper import Story


def _tokenize(text: str) -> set[str]:
    """Lowercase and split text into a set of word tokens."""
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _title_similarity(a: str, b: str) -> float:
    """Compute token overlap ratio between two titles (Jaccard-ish)."""
    tokens_a = _tokenize(a)
    tokens_b = _tokenize(b)
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


def deduplicate(stories: list[Story], similarity_threshold: float = 0.75) -> list[Story]:
    """Remove duplicate stories by exact URL match and title similarity.

    First pass: keep only the first occurrence of each URL.
    Second pass: among remaining stories, remove those whose title is too
    similar to an already-kept story.
    """
    if not stories:
        return []

    # Pass 1: exact URL dedup (keep first seen)
    seen_urls: set[str] = set()
    url_deduped: list[Story] = []
    for story in stories:
        normalized = story.url.rstrip("/")
        if normalized not in seen_urls:
            seen_urls.add(normalized)
            url_deduped.append(story)

    # Pass 2: title similarity dedup
    kept: list[Story] = []
    for story in url_deduped:
        is_dup = False
        for existing in kept:
            if _title_similarity(story.title, existing.title) >= similarity_threshold:
                is_dup = True
                break
        if not is_dup:
            kept.append(story)

    return kept

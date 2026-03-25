"""Rank and curate stories using Claude for intelligent selection."""

import json
import logging

import anthropic

from src.config import ANTHROPIC_API_KEY, MAX_STORIES
from src.discover.scraper import Story

logger = logging.getLogger(__name__)

CURATION_PROMPT = """You are a news curator for an AI/ML infographic account.
Given these stories, select the top {max_stories} most interesting and impactful ones.
For each selected story, provide:
- A concise headline (max 10 words)
- 3 key bullet points (max 15 words each)
- A category: one of [breakthrough, product, research, industry, policy]

Return JSON array with objects: {{"headline": str, "bullets": [str], "category": str, "original_title": str}}

Stories:
{stories}"""


def curate_stories(stories: list[Story]) -> list[dict]:
    """Use Claude to rank and curate top stories."""
    if not stories:
        logger.warning("No stories to curate")
        return []

    if not ANTHROPIC_API_KEY:
        logger.warning("No ANTHROPIC_API_KEY — falling back to simple curation")
        return _simple_curate(stories)

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    stories_text = "\n".join(
        f"- [{s.source}] {s.title}: {s.summary[:200]}" for s in stories
    )

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{
                "role": "user",
                "content": CURATION_PROMPT.format(
                    max_stories=MAX_STORIES, stories=stories_text
                ),
            }],
        )
        text = message.content[0].text
        # Extract JSON from response
        start = text.index("[")
        end = text.rindex("]") + 1
        curated = json.loads(text[start:end])
        logger.info(f"Curated {len(curated)} stories")
        return curated[:MAX_STORIES]
    except Exception as e:
        logger.error(f"Claude curation failed: {e}")
        return _simple_curate(stories)


def _simple_curate(stories: list[Story]) -> list[dict]:
    """Fallback curation without LLM — just pick the first N stories."""
    return [
        {
            "headline": s.title[:60],
            "bullets": [s.summary[:80]],
            "category": "industry",
            "original_title": s.title,
        }
        for s in stories[:MAX_STORIES]
    ]

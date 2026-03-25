"""Rank and curate stories using Claude for intelligent selection."""

import json
import logging

import anthropic

from src.config import ANTHROPIC_API_KEY, MAX_STORIES
from src.curate.cache import load_curated, save_curated
from src.curate.scorer import sort_stories_by_score
from src.discover.scraper import Story

logger = logging.getLogger(__name__)

CURATION_PROMPT = """You are an expert news curator for a popular AI/ML infographic social media account.
Your audience is technical but busy — they want the most important stories distilled clearly.

From the stories below (pre-ranked by relevance), select the top {max_stories} that best combine:
1. **Recency** — prefer stories from the last 24-48 hours
2. **Impact** — breakthroughs, major launches, or policy shifts that affect many people
3. **Novelty** — genuinely new information, not incremental updates or rehashed announcements
4. **Diversity** — avoid picking multiple stories about the same topic or company

For each selected story, provide:
- **headline**: A punchy, specific headline (max 10 words). Avoid vague words like "new", "big", "major". Name the company/model/technique.
- **bullets**: Exactly 3 key bullet points (max 15 words each). Each bullet should convey a distinct fact — not restate the headline.
- **category**: One of [breakthrough, product, research, industry, policy]
- **original_title**: The original title of the story you selected (copy exactly)

Return ONLY a JSON array. No markdown, no explanation.
Format: [{{"headline": str, "bullets": [str, str, str], "category": str, "original_title": str}}]

Stories (ranked by relevance score, best first):
{stories}"""


def curate_stories(stories: list[Story], force: bool = False) -> list[dict]:
    """Use Claude to rank and curate top stories.

    Args:
        stories: List of discovered stories to curate.
        force: If True, bypass the cache and re-run curation.

    Returns:
        List of curated story dicts.
    """
    if not stories:
        logger.warning("No stories to curate")
        return []

    # Check cache first
    cached = load_curated(force=force)
    if cached is not None:
        logger.info("Using cached curation results")
        return cached

    # Pre-sort stories by credibility + relevance score
    sorted_stories = sort_stories_by_score(stories)
    ranked_stories = [s for s, _ in sorted_stories]

    if not ANTHROPIC_API_KEY:
        logger.warning("No ANTHROPIC_API_KEY — falling back to simple curation")
        result = _simple_curate(ranked_stories)
        save_curated(result)
        return result

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    stories_text = "\n".join(
        f"- [{s.source}] {s.title}: {s.summary[:200]}" for s in ranked_stories
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
        result = curated[:MAX_STORIES]
        logger.info(f"Curated {len(result)} stories")
        save_curated(result)
        return result
    except Exception as e:
        logger.error(f"Claude curation failed: {e}")
        result = _simple_curate(ranked_stories)
        save_curated(result)
        return result


def _simple_curate(stories: list[Story]) -> list[dict]:
    """Fallback curation without LLM — just pick the first N stories."""
    return [
        {
            "headline": s.title[:60],
            "bullets": [
                s.summary[:80] if s.summary else "Details pending",
                f"Source: {s.source}",
                f"Published: {s.published.strftime('%b %d') if s.published else 'Recent'}",
            ],
            "category": "industry",
            "original_title": s.title,
        }
        for s in stories[:MAX_STORIES]
    ]

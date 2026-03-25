"""Source credibility scoring and story ranking."""

from datetime import datetime, timezone

from src.discover.scraper import Story

# Credibility weights for known sources (0.0 to 1.0)
SOURCE_WEIGHTS: dict[str, float] = {
    "ArXiv AI": 0.95,
    "MIT Tech Review AI": 0.90,
    "TechCrunch AI": 0.80,
    "The Verge AI": 0.75,
    "Hacker News AI": 0.70,
}

DEFAULT_WEIGHT = 0.40

# Keywords that indicate high relevance to AI/ML audience
RELEVANCE_KEYWORDS = [
    "llm", "gpt", "transformer", "diffusion", "neural", "deep learning",
    "machine learning", "reinforcement learning", "benchmark", "open source",
    "model", "training", "inference", "reasoning", "agent", "multimodal",
    "breakthrough", "sota", "state-of-the-art", "foundation model",
    "fine-tuning", "rlhf", "alignment", "safety",
]


def _keyword_score(text: str) -> float:
    """Return a keyword relevance score between 0.0 and 1.0."""
    text_lower = text.lower()
    matches = sum(1 for kw in RELEVANCE_KEYWORDS if kw in text_lower)
    # Normalize: cap at 5 keyword matches for max score
    return min(matches / 5.0, 1.0)


def _recency_score(published: datetime | None) -> float:
    """Return a recency score between 0.0 and 1.0. More recent = higher."""
    if published is None:
        return 0.5  # neutral if unknown
    # Ensure both sides are tz-aware or tz-naive for safe subtraction
    now = datetime.now(timezone.utc)
    if published.tzinfo is None:
        now = datetime.now()
    age_hours = (now - published).total_seconds() / 3600
    if age_hours < 0:
        age_hours = 0
    # Stories less than 6 hours old get full score, decays over 7 days
    if age_hours <= 6:
        return 1.0
    elif age_hours >= 168:  # 7 days
        return 0.1
    else:
        return max(0.1, 1.0 - (age_hours - 6) / 162)


def score_story(story: Story) -> float:
    """Score a story based on source credibility, keyword relevance, and recency.

    Returns a float score (higher is better).
    Weights: source=40%, keywords=35%, recency=25%
    """
    source_w = SOURCE_WEIGHTS.get(story.source, DEFAULT_WEIGHT)
    keyword_w = _keyword_score(f"{story.title} {story.summary}")
    recency_w = _recency_score(story.published)

    score = (source_w * 0.40) + (keyword_w * 0.35) + (recency_w * 0.25)
    return round(score, 4)


def sort_stories_by_score(stories: list[Story]) -> list[tuple[Story, float]]:
    """Sort stories by score descending. Returns list of (story, score) tuples."""
    if not stories:
        return []
    scored = [(s, score_story(s)) for s in stories]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored

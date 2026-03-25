"""News source definitions for AI/ML content."""

from dataclasses import dataclass


@dataclass
class Source:
    name: str
    url: str
    source_type: str  # "rss", "api", "scrape"


SOURCES = [
    # RSS feeds
    Source("Hacker News AI", "https://hnrss.org/newest?q=AI+OR+LLM+OR+machine+learning&points=50", "rss"),
    Source("ArXiv AI", "https://rss.arxiv.org/rss/cs.AI", "rss"),
    Source("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/", "rss"),
    Source("MIT Tech Review AI", "https://www.technologyreview.com/feed/", "rss"),
    Source("The Verge AI", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "rss"),

    # NewsAPI (requires NEWSAPI_KEY)
    Source("NewsAPI AI", "https://newsapi.org/v2/everything", "api"),

    # Web scrape targets
    Source("VentureBeat AI", "https://venturebeat.com/category/ai/", "scrape"),
    Source("AI News", "https://www.artificialintelligence-news.com/", "scrape"),
]

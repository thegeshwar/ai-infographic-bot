# AI Infographic Bot

Fully automated daily pipeline that discovers trending AI/ML news, generates infographic images, and posts to social media.

## Architecture

Python monolith with Playwright for browser automation, running on macOS.

### Pipeline Stages

1. **Discover** — Scrape trending AI/ML news from multiple sources
2. **Curate** — Rank and select top stories, extract key facts
3. **Generate** — Create infographic images from curated content
4. **Post** — Publish to social media platforms via Playwright

## Project Structure

```
ai-infographic-bot/
├── src/
│   ├── __init__.py
│   ├── config.py          # Settings and env vars
│   ├── pipeline.py         # Main orchestrator
│   ├── discover/           # News scraping
│   │   ├── __init__.py
│   │   ├── scraper.py      # Multi-source scraper
│   │   └── sources.py      # Source definitions
│   ├── curate/             # Content curation
│   │   ├── __init__.py
│   │   └── ranker.py       # Story ranking and selection
│   ├── generate/           # Image generation
│   │   ├── __init__.py
│   │   ├── renderer.py     # Infographic renderer
│   │   └── templates.py    # Visual templates
│   └── post/               # Social media posting
│       ├── __init__.py
│       └── publisher.py    # Playwright-based publisher
├── data/                   # Runtime data (gitignored)
├── output/                 # Generated images (gitignored)
├── tests/
├── requirements.txt
├── .env.example
├── .gitignore
└── run.py                  # CLI entrypoint
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env  # Configure your API keys
```

## Usage

```bash
python run.py              # Run full pipeline
python run.py discover     # Run only news discovery
python run.py generate     # Run only image generation
python run.py post         # Run only posting
```

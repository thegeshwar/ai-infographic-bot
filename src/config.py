import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / os.getenv("OUTPUT_DIR", "output")

DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# News sources
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")

# LLM
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Social media
TWITTER_USERNAME = os.getenv("TWITTER_USERNAME", "")
TWITTER_PASSWORD = os.getenv("TWITTER_PASSWORD", "")
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL", "")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD", "")

# Pipeline
MAX_STORIES = int(os.getenv("MAX_STORIES", "5"))
SCHEDULE_HOUR = int(os.getenv("SCHEDULE_HOUR", "8"))

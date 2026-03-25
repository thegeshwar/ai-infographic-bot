import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / os.getenv("OUTPUT_DIR", "output")
GALLERY_DIR = ROOT_DIR / "gallery"
SCHEDULE_HOUR = int(os.getenv("SCHEDULE_HOUR", "8"))

DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

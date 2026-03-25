"""Font loading for macOS."""
from functools import lru_cache
from PIL import ImageFont

_FONT_PATH = "/System/Library/Fonts/Helvetica.ttc"
_BOLD_INDEX = 1
_REGULAR_INDEX = 0


@lru_cache(maxsize=32)
def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load Helvetica at the given size. Falls back to Pillow default."""
    try:
        index = _BOLD_INDEX if bold else _REGULAR_INDEX
        return ImageFont.truetype(_FONT_PATH, size, index=index)
    except OSError:
        return ImageFont.load_default(size=size)

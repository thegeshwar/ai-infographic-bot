"""Infographic image renderer using Pillow."""

import logging
import textwrap
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src.config import OUTPUT_DIR
from .templates import (
    CATEGORY_COLORS,
    CATEGORY_ICONS,
    FONTS,
    get_template,
    get_output_format,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Font helper
# ---------------------------------------------------------------------------

def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Get a font, falling back to default if custom fonts unavailable."""
    try:
        if bold:
            return ImageFont.truetype(
                "/System/Library/Fonts/Helvetica.ttc", size, index=1
            )
        return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)
    except OSError:
        return ImageFont.load_default(size=size)


# ---------------------------------------------------------------------------
# Drawing utilities
# ---------------------------------------------------------------------------

def _draw_gradient(width: int, height: int, start_hex: str, end_hex: str) -> Image.Image:
    """Create a top-to-bottom linear gradient image."""
    img = Image.new("RGB", (width, height))

    def _hex_to_rgb(h: str):
        h = h.lstrip("#")
        return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))

    r1, g1, b1 = _hex_to_rgb(start_hex)
    r2, g2, b2 = _hex_to_rgb(end_hex)

    draw = ImageDraw.Draw(img)
    for y in range(height):
        t = y / max(height - 1, 1)
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        draw.line([(0, y), (width - 1, y)], fill=(r, g, b))

    return img


def _wrap_text(text: str, max_chars: int = 40) -> list[str]:
    """Wrap *text* into lines of at most *max_chars* characters."""
    if not text:
        return [""]
    return textwrap.wrap(text, width=max_chars) or [""]


# ---------------------------------------------------------------------------
# Main renderer
# ---------------------------------------------------------------------------

def generate_infographic(
    curated_stories: list[dict],
    *,
    template: str = "dark",
    format: str = "instagram",
) -> Path:
    """Generate an infographic image from curated stories.

    Parameters
    ----------
    curated_stories:
        List of story dicts with keys ``headline``, ``category``, ``bullets``.
    template:
        Visual style — one of ``dark``, ``light``, ``gradient``, ``minimal``.
    format:
        Output dimensions — one of ``instagram``, ``twitter``, ``linkedin``.
    """
    tmpl = get_template(template)
    fmt = get_output_format(format)
    width, height = fmt["width"], fmt["height"]
    margin = tmpl["margin"]
    content_width = width - 2 * margin

    # -- background --------------------------------------------------------
    if "gradient_start" in tmpl and "gradient_end" in tmpl:
        img = _draw_gradient(width, height, tmpl["gradient_start"], tmpl["gradient_end"])
    else:
        img = Image.new("RGB", (width, height), tmpl["background"])

    draw = ImageDraw.Draw(img)

    # -- header ------------------------------------------------------------
    title_font = _get_font(FONTS["title"]["size"], bold=True)
    date_font = _get_font(FONTS["date"]["size"])
    today = datetime.now().strftime("%B %d, %Y")

    draw.text((margin, 40), "AI/ML Daily Digest", font=title_font, fill=tmpl["text_primary"])
    draw.text((margin, 100), today, font=date_font, fill=tmpl["text_muted"])

    # divider
    draw.line(
        [(margin, 145), (width - margin, 145)],
        fill=tmpl["accent"],
        width=2,
    )

    # -- story cards -------------------------------------------------------
    y = 165
    headline_font = _get_font(FONTS["headline"]["size"], bold=True)
    bullet_font = _get_font(FONTS["bullet"]["size"])
    tag_font = _get_font(FONTS["tag"]["size"], bold=True)

    # Estimate chars that fit in content width (~0.55 * font_size per char)
    headline_max_chars = max(20, int(content_width / (FONTS["headline"]["size"] * 0.55)))
    bullet_max_chars = max(20, int((content_width - 30) / (FONTS["bullet"]["size"] * 0.50)))

    for idx, story in enumerate(curated_stories, 1):
        if y > height - 80:
            break  # no room for more cards

        cat = story.get("category", "industry")
        colors = CATEGORY_COLORS.get(cat, CATEGORY_COLORS["industry"])
        icon = CATEGORY_ICONS.get(cat, "")

        # Card background
        card_top = y
        # Pre-calculate card height
        headline_lines = _wrap_text(story["headline"], max_chars=headline_max_chars)
        bullet_lines_all: list[list[str]] = []
        for bullet in story.get("bullets", [])[:3]:
            bullet_lines_all.append(_wrap_text(bullet, max_chars=bullet_max_chars))

        card_h = (
            tmpl["card_padding"]       # top padding
            + 30                       # tag
            + 10                       # gap
            + len(headline_lines) * 38 # headline lines
            + 10                       # gap
            + sum(len(bl) * 30 for bl in bullet_lines_all)
            + tmpl["card_padding"]     # bottom padding
        )

        # Draw rounded card background
        draw.rounded_rectangle(
            [(margin - 10, card_top), (width - margin + 10, card_top + card_h)],
            radius=tmpl["card_radius"],
            fill=tmpl["card_bg"],
        )

        cy = card_top + tmpl["card_padding"]

        # Number + category tag
        tag_text = f"{icon} {cat.upper()}"
        tag_w = len(tag_text) * 9 + 24
        draw.rounded_rectangle(
            [(margin + 5, cy), (margin + 5 + tag_w, cy + 26)],
            radius=4,
            fill=colors["primary"],
        )
        draw.text((margin + 17, cy + 4), tag_text, font=tag_font, fill="#FFFFFF")

        # Story number badge
        num_x = width - margin - 30
        draw.rounded_rectangle(
            [(num_x, cy), (num_x + 28, cy + 26)],
            radius=4,
            fill=colors["accent"],
        )
        draw.text(
            (num_x + 8, cy + 4),
            str(idx),
            font=tag_font,
            fill=tmpl["text_primary"],
        )
        cy += 36

        # Headline (wrapped)
        for line in headline_lines:
            draw.text((margin + 15, cy), line, font=headline_font, fill=tmpl["text_primary"])
            cy += 38

        cy += 6

        # Bullets (wrapped)
        for bl_lines in bullet_lines_all:
            first = True
            for line in bl_lines:
                prefix = "\u2022 " if first else "  "
                draw.text(
                    (margin + 25, cy),
                    f"{prefix}{line}",
                    font=bullet_font,
                    fill=tmpl["text_secondary"],
                )
                cy += 30
                first = False

        y = card_top + card_h + 14  # gap between cards

    # -- footer ------------------------------------------------------------
    footer_font = _get_font(FONTS["footer"]["size"])
    wm_font = _get_font(FONTS["watermark"]["size"])

    hashtags = "#AI #MachineLearning #DailyDigest"
    draw.text(
        (margin, height - 60),
        hashtags,
        font=footer_font,
        fill=tmpl["text_muted"],
    )
    draw.text(
        (margin, height - 35),
        "Generated by AI Infographic Bot",
        font=wm_font,
        fill=tmpl["text_muted"],
    )

    # -- save --------------------------------------------------------------
    output_path = OUTPUT_DIR / f"infographic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    img.save(output_path, "PNG")
    logger.info("Saved infographic to %s", output_path)
    return output_path

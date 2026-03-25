"""Single-story infographic rendering engine.

Produces 1080x1350 PNG images optimized for LinkedIn.
"""
from __future__ import annotations

import re
import textwrap
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src.render.fonts import load_font
from src.render.model import StoryContent
from src.render.templates import get_template

WIDTH = 1080
HEIGHT = 1350
MARGIN = 60
CONTENT_WIDTH = WIDTH - 2 * MARGIN


def _parse_color(color_str: str) -> tuple[int, int, int]:
    """Parse a hex or rgba() color string to an RGB tuple."""
    if color_str.startswith("#"):
        h = color_str.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    m = re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", color_str)
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return (128, 128, 128)


def _parse_color_alpha(color_str: str) -> tuple[int, int, int, int]:
    """Parse color string to RGBA tuple."""
    if color_str.startswith("#"):
        rgb = _parse_color(color_str)
        return (*rgb, 255)
    m = re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)", color_str)
    if m:
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        a = int(float(m.group(4)) * 255) if m.group(4) else 255
        return (r, g, b, a)
    return (128, 128, 128, 255)


def _wrap_text(text: str, font_size: int, max_width: int) -> list[str]:
    """Wrap text to fit within max_width pixels."""
    chars_per_line = max(10, int(max_width / (font_size * 0.55)))
    return textwrap.wrap(text, width=chars_per_line)


def _draw_gradient_bg(img: Image.Image, colors: list[str]) -> None:
    """Draw a top-to-bottom linear gradient."""
    draw = ImageDraw.Draw(img)
    c1 = _parse_color(colors[0])
    c2 = _parse_color(colors[1])
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(c1[0] + (c2[0] - c1[0]) * ratio)
        g = int(c1[1] + (c2[1] - c1[1]) * ratio)
        b = int(c1[2] + (c2[2] - c1[2]) * ratio)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))


def _draw_rounded_rect(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    radius: int,
    fill: tuple | None = None,
    outline: tuple | None = None,
    width: int = 1,
) -> None:
    """Draw a rounded rectangle."""
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def _blend_rgba_on_bg(rgba: tuple[int, int, int, int], bg: tuple[int, int, int]) -> tuple[int, int, int]:
    """Blend an RGBA color onto an opaque RGB background."""
    a = rgba[3] / 255.0
    return (
        int(rgba[0] * a + bg[0] * (1 - a)),
        int(rgba[1] * a + bg[1] * (1 - a)),
        int(rgba[2] * a + bg[2] * (1 - a)),
    )


def render_story(
    story: StoryContent,
    template: str = "dark-glassmorphism",
    output_dir: Path | None = None,
) -> Path:
    """Render a single-story infographic and save as PNG.

    Returns the path to the saved image.
    """
    tmpl = get_template(template)
    if output_dir is None:
        output_dir = Path("output")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create canvas
    img = Image.new("RGB", (WIDTH, HEIGHT))

    # Background
    bg = tmpl["bg"]
    if isinstance(bg, list):
        _draw_gradient_bg(img, bg)
        bg_rgb = _parse_color(bg[0])  # approximate for blending
    else:
        bg_rgb = _parse_color(bg)
        img.paste(bg_rgb, (0, 0, WIDTH, HEIGHT))

    draw = ImageDraw.Draw(img)
    y = 0

    # --- Tricolor accent bar ---
    tricolor = tmpl.get("tricolor_accent")
    if tricolor:
        bar_h = 4
        third = WIDTH // 3
        for i, color_str in enumerate(tricolor):
            c = _parse_color(color_str)
            x0 = i * third
            x1 = (i + 1) * third if i < 2 else WIDTH
            draw.rectangle([x0, 0, x1, bar_h], fill=c)
        y = bar_h + 8
    else:
        y = 20

    # --- Grid pattern ---
    if tmpl.get("grid_pattern"):
        overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        grid_draw = ImageDraw.Draw(overlay)
        grid_color = (128, 128, 128, 18)
        for gx in range(0, WIDTH, 30):
            grid_draw.line([(gx, 0), (gx, HEIGHT)], fill=grid_color, width=1)
        for gy in range(0, HEIGHT, 30):
            grid_draw.line([(0, gy), (WIDTH, gy)], fill=grid_color, width=1)
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img)

    # --- Logo + brand (company templates) ---
    if tmpl.get("logo"):
        logo_size = 40
        logo_x = MARGIN
        logo_y = y + 10
        accent_rgb = _parse_color(tmpl["accent_line"])
        _draw_rounded_rect(
            draw,
            (logo_x, logo_y, logo_x + logo_size, logo_y + logo_size),
            radius=8,
            fill=accent_rgb,
        )
        cu_font = load_font(20, bold=True)
        draw.text(
            (logo_x + logo_size // 2, logo_y + logo_size // 2),
            "Cu",
            fill=(255, 255, 255),
            font=cu_font,
            anchor="mm",
        )
        brand_font = load_font(22, bold=True)
        draw.text(
            (logo_x + logo_size + 12, logo_y + logo_size // 2),
            "CU CIRCUITS",
            fill=_parse_color(tmpl["text_primary"]),
            font=brand_font,
            anchor="lm",
        )
        y = logo_y + logo_size + 20
    else:
        y += 20

    # --- Hook text ---
    hook_font = load_font(40, bold=True)
    hook_color = _parse_color(tmpl["hook_color"])
    hook_lines = _wrap_text(story.hook, 40, CONTENT_WIDTH)
    for line in hook_lines:
        draw.text((MARGIN, y), f"\u201c{line}\u201d" if line == hook_lines[0] and len(hook_lines) == 1 else
                  (f"\u201c{line}" if line == hook_lines[0] else
                   (f"{line}\u201d" if line == hook_lines[-1] else line)),
                  fill=hook_color, font=hook_font)
        y += 50
    y += 10

    # --- Accent line ---
    accent_rgb = _parse_color(tmpl["accent_line"])
    draw.line([(MARGIN, y), (WIDTH - MARGIN, y)], fill=accent_rgb, width=2)
    y += 20

    # --- Headline ---
    headline_font = load_font(48, bold=True)
    headline_color = _parse_color(tmpl["text_primary"])
    headline_text = story.headline.upper()
    headline_lines = _wrap_text(headline_text, 48, CONTENT_WIDTH)
    for line in headline_lines:
        draw.text((MARGIN, y), line, fill=headline_color, font=headline_font)
        y += 58
    y += 10

    # --- Date + Source ---
    date_str = datetime.now().strftime("%B %d, %Y")
    meta_text = f"{date_str} \u00b7 {story.source}"
    meta_font = load_font(20)
    draw.text((MARGIN, y), meta_text, fill=_parse_color(tmpl["text_muted"]), font=meta_font)
    y += 36

    # --- Story card ---
    card_padding = 24
    card_x0 = MARGIN
    card_x1 = WIDTH - MARGIN
    card_inner_width = CONTENT_WIDTH - 2 * card_padding

    # Pre-calculate card height
    body_font = load_font(22)
    all_body_lines: list[list[str]] = []
    for para in story.body:
        wrapped = _wrap_text(para, 22, card_inner_width)
        all_body_lines.append(wrapped)

    total_body_lines = sum(len(lines) for lines in all_body_lines)
    line_height = 30
    para_gap = 16
    card_text_height = total_body_lines * line_height + (len(all_body_lines) - 1) * para_gap
    card_height = card_text_height + 2 * card_padding

    card_y0 = y
    card_y1 = y + card_height
    card_radius = tmpl.get("card_radius", 12)

    # Card background - blend rgba onto background
    card_bg_rgba = _parse_color_alpha(tmpl["card_bg"])
    card_bg_blended = _blend_rgba_on_bg(card_bg_rgba, bg_rgb)

    card_border_rgba = _parse_color_alpha(tmpl["card_border"])
    card_border_blended = _blend_rgba_on_bg(card_border_rgba, bg_rgb)

    _draw_rounded_rect(
        draw,
        (card_x0, card_y0, card_x1, card_y1),
        radius=card_radius,
        fill=card_bg_blended,
        outline=card_border_blended,
        width=1,
    )

    # Draw body text inside card
    text_y = card_y0 + card_padding
    text_secondary = _parse_color(tmpl["text_secondary"])
    for para_lines in all_body_lines:
        for line in para_lines:
            draw.text((card_x0 + card_padding, text_y), line, fill=text_secondary, font=body_font)
            text_y += line_height
        text_y += para_gap

    y = card_y1 + 20

    # --- Insight box ---
    insight_padding = 20
    insight_inner_width = CONTENT_WIDTH - 2 * insight_padding - 8  # 8 for left border
    insight_font = load_font(22)
    insight_header_font = load_font(18, bold=True)
    insight_lines = _wrap_text(story.insight, 22, insight_inner_width)
    insight_header_height = 28
    insight_text_height = len(insight_lines) * 30
    insight_height = insight_header_height + insight_text_height + 2 * insight_padding

    insight_y0 = y
    insight_y1 = y + insight_height

    # Insight background
    insight_bg_rgba = _parse_color_alpha(tmpl["insight_bg"])
    insight_bg_blended = _blend_rgba_on_bg(insight_bg_rgba, bg_rgb)

    _draw_rounded_rect(
        draw,
        (MARGIN, insight_y0, WIDTH - MARGIN, insight_y1),
        radius=card_radius,
        fill=insight_bg_blended,
    )

    # Left accent border
    draw.rectangle(
        [MARGIN, insight_y0 + 4, MARGIN + 4, insight_y1 - 4],
        fill=accent_rgb,
    )

    # Insight header
    insight_text_x = MARGIN + insight_padding + 4
    iy = insight_y0 + insight_padding
    draw.text((insight_text_x, iy), "\U0001f4a1 KEY INSIGHT", fill=accent_rgb, font=insight_header_font)
    iy += insight_header_height

    # Insight text
    text_primary = _parse_color(tmpl["text_primary"])
    for line in insight_lines:
        draw.text((insight_text_x, iy), line, fill=text_primary, font=insight_font)
        iy += 30

    y = insight_y1 + 20

    # --- Hashtags ---
    hashtag_font = load_font(18)
    hashtag_text = " ".join(story.hashtags)
    hashtag_color = _parse_color(tmpl["text_muted"])
    hashtag_lines = _wrap_text(hashtag_text, 18, CONTENT_WIDTH)
    for line in hashtag_lines:
        draw.text((MARGIN, y), line, fill=hashtag_color, font=hashtag_font)
        y += 26
    y += 10

    # --- Footer ---
    draw.line([(MARGIN, y), (WIDTH - MARGIN, y)], fill=accent_rgb, width=1)
    y += 12
    footer_font = load_font(14)
    footer_text = f"{tmpl['footer_text']} \u00b7 Generated by AI Infographic Bot"
    draw.text((MARGIN, y), footer_text, fill=_parse_color(tmpl["text_muted"]), font=footer_font)

    # Save
    filename = f"infographic_{datetime.now():%Y%m%d_%H%M%S}.png"
    out_path = output_dir / filename
    img.save(str(out_path), "PNG")
    return out_path

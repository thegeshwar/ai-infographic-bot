"""HTML-to-PNG infographic renderer using Playwright.

Claude writes custom HTML/CSS for each infographic. This engine
screenshots it to a 1080x1350 PNG optimized for LinkedIn.
"""
from __future__ import annotations

import asyncio
import tempfile
from datetime import datetime
from pathlib import Path

from src.render.model import StoryContent

WIDTH = 1080
HEIGHT = 1350


def _wrap_html(html: str) -> str:
    """Wrap the infographic HTML in a page with correct viewport sizing."""
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ width: {WIDTH}px; height: {HEIGHT}px; overflow: hidden; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif; }}
</style>
</head>
<body>
{html}
</body>
</html>"""


async def _screenshot(html: str, output_path: Path) -> None:
    """Launch Playwright, render HTML, screenshot to PNG."""
    from playwright.async_api import async_playwright

    full_html = _wrap_html(html)

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
        f.write(full_html)
        tmp_path = f.name

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                viewport={"width": WIDTH, "height": HEIGHT},
                device_scale_factor=2,  # Retina quality
            )
            await page.goto(f"file://{tmp_path}", wait_until="networkidle")
            await page.screenshot(path=str(output_path), type="png")
            await browser.close()
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def render_story(
    story: StoryContent,
    output_dir: Path | str | None = None,
) -> Path:
    """Render a story's HTML to a 1080x1350 PNG.

    The story.html field must contain the full infographic HTML/CSS.
    """
    if not story.html:
        raise ValueError("StoryContent.html is empty. Claude must design the HTML first.")

    if output_dir is None:
        from src.config import OUTPUT_DIR
        output_dir = OUTPUT_DIR

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    slug = story.headline[:40].lower().replace(" ", "-").replace("'", "")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    output_path = output_dir / f"{slug}_{datetime.now():%Y%m%d_%H%M%S}.png"

    asyncio.run(_screenshot(story.html, output_path))
    return output_path

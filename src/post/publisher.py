"""Social media publisher using Playwright for browser automation."""

import logging
from pathlib import Path

from playwright.async_api import async_playwright

from src.config import (
    TWITTER_USERNAME,
    TWITTER_PASSWORD,
    LINKEDIN_EMAIL,
    LINKEDIN_PASSWORD,
)

logger = logging.getLogger(__name__)


async def post_to_twitter(image_path: Path, caption: str) -> bool:
    """Post an infographic to Twitter/X using Playwright."""
    if not TWITTER_USERNAME or not TWITTER_PASSWORD:
        logger.warning("Twitter credentials not configured — skipping")
        return False

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            ctx = await browser.new_context()
            page = await ctx.new_page()

            # Login
            await page.goto("https://x.com/login")
            await page.fill('input[autocomplete="username"]', TWITTER_USERNAME)
            await page.click('text=Next')
            await page.fill('input[type="password"]', TWITTER_PASSWORD)
            await page.click('text=Log in')
            await page.wait_for_url("**/home", timeout=30000)

            # Compose tweet
            await page.click('[data-testid="tweetTextarea_0"]')
            await page.keyboard.type(caption)

            # Attach image
            file_input = await page.query_selector('input[type="file"]')
            if file_input:
                await file_input.set_input_files(str(image_path))

            # Post
            await page.click('[data-testid="tweetButton"]')
            await page.wait_for_timeout(3000)

            await browser.close()
            logger.info("Posted to Twitter successfully")
            return True
    except Exception as e:
        logger.error(f"Twitter posting failed: {e}")
        return False


async def post_to_linkedin(image_path: Path, caption: str) -> bool:
    """Post an infographic to LinkedIn using Playwright."""
    if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
        logger.warning("LinkedIn credentials not configured — skipping")
        return False

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            ctx = await browser.new_context()
            page = await ctx.new_page()

            # Login
            await page.goto("https://www.linkedin.com/login")
            await page.fill('#username', LINKEDIN_EMAIL)
            await page.fill('#password', LINKEDIN_PASSWORD)
            await page.click('[type="submit"]')
            await page.wait_for_url("**/feed/**", timeout=30000)

            # Start post
            await page.click('button:has-text("Start a post")')
            await page.wait_for_timeout(1000)

            # Type caption
            editor = await page.wait_for_selector('[role="textbox"]')
            await editor.type(caption)

            # Attach image
            await page.click('button[aria-label*="Add media"]')
            file_input = await page.wait_for_selector('input[type="file"]')
            await file_input.set_input_files(str(image_path))
            await page.wait_for_timeout(3000)
            done_btn = await page.query_selector('button:has-text("Done")')
            if done_btn:
                await done_btn.click()

            # Post
            await page.click('button:has-text("Post")')
            await page.wait_for_timeout(3000)

            await browser.close()
            logger.info("Posted to LinkedIn successfully")
            return True
    except Exception as e:
        logger.error(f"LinkedIn posting failed: {e}")
        return False

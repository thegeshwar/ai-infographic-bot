"""Social media publisher using Playwright for browser automation.

Supports Twitter/X, LinkedIn, and Instagram.  Each poster integrates:
- Session persistence (avoids repeated logins)
- Retry with exponential backoff
- 2FA / CAPTCHA detection with manual-input pause
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, Page, BrowserContext

from src.config import (
    TWITTER_USERNAME,
    TWITTER_PASSWORD,
    LINKEDIN_EMAIL,
    LINKEDIN_PASSWORD,
    INSTAGRAM_USERNAME,
    INSTAGRAM_PASSWORD,
)
from src.post.session import load_session, save_session
from src.post.retry import with_retry

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 2FA / CAPTCHA helpers
# ---------------------------------------------------------------------------

# CSS selectors that indicate a 2FA or CAPTCHA challenge.
_2FA_SELECTORS = [
    'input[name="verificationCode"]',
    'input[name="challenge_response"]',
    '[data-testid="ocfEnterTextTextInput"]',
    'input[id="approvals_code"]',
    'input[aria-label*="verification"]',
    'input[aria-label*="security code"]',
]

_CAPTCHA_SELECTORS = [
    'iframe[src*="captcha"]',
    'iframe[src*="recaptcha"]',
    'iframe[src*="hcaptcha"]',
    '[class*="captcha"]',
    '#captcha',
]


async def detect_2fa(page: Page) -> bool:
    """Return True if the page contains a 2FA / verification prompt."""
    for sel in _2FA_SELECTORS:
        el = await page.query_selector(sel)
        if el:
            return True
    return False


async def detect_captcha(page: Page) -> bool:
    """Return True if the page contains a CAPTCHA challenge."""
    for sel in _CAPTCHA_SELECTORS:
        el = await page.query_selector(sel)
        if el:
            return True
    return False


async def wait_for_manual_input(
    page: Page,
    *,
    challenge_type: str = "2fa",
    timeout_seconds: float = 300,
    poll_interval: float = 3,
) -> None:
    """Pause execution and wait for the user to solve a challenge manually.

    Polls every *poll_interval* seconds.  If the challenge element is still
    present after *timeout_seconds*, raises ``TimeoutError``.
    """
    detector = detect_2fa if challenge_type == "2fa" else detect_captcha
    label = "2FA" if challenge_type == "2fa" else "CAPTCHA"

    logger.warning(
        "%s detected — please complete the challenge in the browser. "
        "Waiting up to %.0f seconds ...",
        label, timeout_seconds,
    )
    print(f"\n*** {label} DETECTED — complete the challenge in the browser window ***\n")

    elapsed = 0.0
    while elapsed < timeout_seconds:
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval
        if not await detector(page):
            logger.info("%s resolved after %.0f seconds", label, elapsed)
            return

    raise TimeoutError(f"{label} was not resolved within {timeout_seconds}s")


# ---------------------------------------------------------------------------
# Shared Playwright helpers
# ---------------------------------------------------------------------------

async def _create_context(
    pw,
    platform: str,
    headless: bool = False,
) -> tuple:
    """Launch browser and create a context, restoring session if available.

    Returns (browser, context, page, used_saved_session: bool).
    """
    browser = await pw.chromium.launch(headless=headless)

    saved = load_session(platform)
    if saved:
        ctx = await browser.new_context(storage_state=saved)
        logger.info("Restored saved session for %s", platform)
        used_saved = True
    else:
        ctx = await browser.new_context()
        used_saved = False

    page = await ctx.new_page()
    return browser, ctx, page, used_saved


async def _handle_challenges(page: Page) -> None:
    """Check for 2FA / CAPTCHA after a login attempt and wait if needed."""
    if await detect_2fa(page):
        await wait_for_manual_input(page, challenge_type="2fa")
    if await detect_captcha(page):
        await wait_for_manual_input(page, challenge_type="captcha")


async def _save_and_close(ctx: BrowserContext, browser, platform: str) -> None:
    """Persist session state and close the browser."""
    state = await ctx.storage_state()
    save_session(platform, state)
    await browser.close()


# ---------------------------------------------------------------------------
# Twitter / X
# ---------------------------------------------------------------------------

@with_retry(max_attempts=3)
async def post_to_twitter(image_path: Path, caption: str) -> bool:
    """Post an infographic to Twitter/X using Playwright."""
    if not TWITTER_USERNAME or not TWITTER_PASSWORD:
        logger.warning("Twitter credentials not configured — skipping")
        return False

    try:
        async with async_playwright() as p:
            browser, ctx, page, had_session = await _create_context(p, "twitter")

            # Login (skip if we restored a valid session)
            await page.goto("https://x.com/home" if had_session else "https://x.com/login")

            if not had_session:
                await page.fill('input[autocomplete="username"]', TWITTER_USERNAME)
                await page.click("text=Next")
                await page.fill('input[type="password"]', TWITTER_PASSWORD)
                await page.click("text=Log in")
                await page.wait_for_url("**/home", timeout=30000)
                await _handle_challenges(page)

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

            await _save_and_close(ctx, browser, "twitter")
            logger.info("Posted to Twitter successfully")
            return True
    except Exception as e:
        logger.error("Twitter posting failed: %s", e)
        return False


# ---------------------------------------------------------------------------
# LinkedIn
# ---------------------------------------------------------------------------

@with_retry(max_attempts=3)
async def post_to_linkedin(image_path: Path, caption: str) -> bool:
    """Post an infographic to LinkedIn using Playwright."""
    if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
        logger.warning("LinkedIn credentials not configured — skipping")
        return False

    try:
        async with async_playwright() as p:
            browser, ctx, page, had_session = await _create_context(p, "linkedin")

            await page.goto(
                "https://www.linkedin.com/feed/" if had_session
                else "https://www.linkedin.com/login"
            )

            if not had_session:
                await page.fill("#username", LINKEDIN_EMAIL)
                await page.fill("#password", LINKEDIN_PASSWORD)
                await page.click('[type="submit"]')
                await page.wait_for_url("**/feed/**", timeout=30000)
                await _handle_challenges(page)

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

            await _save_and_close(ctx, browser, "linkedin")
            logger.info("Posted to LinkedIn successfully")
            return True
    except Exception as e:
        logger.error("LinkedIn posting failed: %s", e)
        return False


# ---------------------------------------------------------------------------
# Instagram
# ---------------------------------------------------------------------------

@with_retry(max_attempts=3)
async def post_to_instagram(image_path: Path, caption: str) -> bool:
    """Post an infographic to Instagram using Playwright.

    Uses Instagram's web interface to create a new post with an image and
    caption (including hashtags).
    """
    if not INSTAGRAM_USERNAME or not INSTAGRAM_PASSWORD:
        logger.warning("Instagram credentials not configured — skipping")
        return False

    try:
        async with async_playwright() as p:
            browser, ctx, page, had_session = await _create_context(p, "instagram")

            await page.goto(
                "https://www.instagram.com/"
                if had_session
                else "https://www.instagram.com/accounts/login/"
            )

            if not had_session:
                await page.fill('input[name="username"]', INSTAGRAM_USERNAME)
                await page.fill('input[name="password"]', INSTAGRAM_PASSWORD)
                await page.click('button[type="submit"]')
                await page.wait_for_url("**/instagram.com/**", timeout=30000)
                await _handle_challenges(page)

                # Dismiss "Save login info" and "Turn on notifications" dialogs
                for dismiss_text in ("Not Now", "Not now"):
                    btn = await page.query_selector(f'button:has-text("{dismiss_text}")')
                    if btn:
                        await btn.click()
                        await page.wait_for_timeout(1000)

            # Open "new post" dialog — try SVG icon first, fall back to button
            new_post = await page.query_selector('svg[aria-label="New post"]')
            if new_post:
                await new_post.click()
            else:
                create_btn = await page.query_selector('[aria-label="New post"]')
                if create_btn:
                    await create_btn.click()
            await page.wait_for_timeout(1000)

            # Upload image
            file_input = await page.wait_for_selector('input[type="file"]')
            await file_input.set_input_files(str(image_path))
            await page.wait_for_timeout(2000)

            # Click through the creation flow: Next → Next → Share
            for step_text in ("Next", "Next"):
                btn = await page.query_selector(f'button:has-text("{step_text}")')
                if btn:
                    await btn.click()
                    await page.wait_for_timeout(1000)

            # Write caption
            caption_area = await page.query_selector('textarea[aria-label="Write a caption..."]')
            if not caption_area:
                caption_area = await page.query_selector('[role="textbox"]')
            if caption_area:
                await caption_area.click()
                await page.keyboard.type(caption)

            # Share
            share_btn = await page.query_selector('button:has-text("Share")')
            if share_btn:
                await share_btn.click()
                await page.wait_for_timeout(5000)

            await _save_and_close(ctx, browser, "instagram")
            logger.info("Posted to Instagram successfully")
            return True
    except Exception as e:
        logger.error("Instagram posting failed: %s", e)
        return False

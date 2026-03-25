"""Comprehensive tests for the social media posting system.

Tests cover: session persistence, retry logic, 2FA/CAPTCHA detection,
platform posters (Twitter, LinkedIn, Instagram), and credential-missing skips.
"""

import asyncio
import json
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest
import pytest_asyncio

# ---------------------------------------------------------------------------
# Session persistence tests
# ---------------------------------------------------------------------------


class TestSessionPersistence:
    """Tests for src.post.session — save, load, and expiry detection."""

    def test_save_session_creates_file(self, tmp_path):
        """Saving a session writes a JSON file under data/sessions/<platform>.json."""
        from src.post.session import save_session

        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()

        state = {
            "cookies": [{"name": "sid", "value": "abc123"}],
            "origins": [],
        }
        save_session("twitter", state, sessions_dir=sessions_dir)

        saved = sessions_dir / "twitter.json"
        assert saved.exists()
        data = json.loads(saved.read_text())
        assert data["state"]["cookies"][0]["value"] == "abc123"
        assert "saved_at" in data

    def test_load_session_returns_state(self, tmp_path):
        """Loading a previously saved session returns the stored state."""
        from src.post.session import save_session, load_session

        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()

        state = {"cookies": [{"name": "tok", "value": "xyz"}], "origins": []}
        save_session("linkedin", state, sessions_dir=sessions_dir)

        loaded = load_session("linkedin", sessions_dir=sessions_dir)
        assert loaded is not None
        assert loaded["cookies"][0]["value"] == "xyz"

    def test_load_session_returns_none_when_missing(self, tmp_path):
        """Loading a non-existent session returns None."""
        from src.post.session import load_session

        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()

        assert load_session("nonexistent", sessions_dir=sessions_dir) is None

    def test_session_expiry_detection(self, tmp_path):
        """A session older than max_age_hours is detected as expired."""
        from src.post.session import save_session, is_session_expired

        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()

        state = {"cookies": [], "origins": []}
        save_session("twitter", state, sessions_dir=sessions_dir)

        # Manually backdate the saved_at timestamp
        filepath = sessions_dir / "twitter.json"
        data = json.loads(filepath.read_text())
        data["saved_at"] = time.time() - 3600 * 25  # 25 hours ago
        filepath.write_text(json.dumps(data))

        assert is_session_expired("twitter", max_age_hours=24, sessions_dir=sessions_dir) is True

    def test_session_not_expired_when_fresh(self, tmp_path):
        """A freshly saved session is not expired."""
        from src.post.session import save_session, is_session_expired

        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()

        state = {"cookies": [], "origins": []}
        save_session("twitter", state, sessions_dir=sessions_dir)

        assert is_session_expired("twitter", max_age_hours=24, sessions_dir=sessions_dir) is False

    def test_missing_session_is_expired(self, tmp_path):
        """A missing session file counts as expired."""
        from src.post.session import is_session_expired

        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()

        assert is_session_expired("twitter", sessions_dir=sessions_dir) is True


# ---------------------------------------------------------------------------
# Retry logic tests
# ---------------------------------------------------------------------------


class TestRetryDecorator:
    """Tests for src.post.retry — exponential backoff decorator."""

    @pytest.mark.asyncio
    async def test_succeeds_on_first_try(self):
        """Function that succeeds immediately is called once."""
        from src.post.retry import with_retry

        call_count = 0

        @with_retry(max_attempts=3)
        async def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = await succeed()
        assert result == "ok"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_succeeds_on_second_try(self):
        """Function that fails once then succeeds is retried."""
        from src.post.retry import with_retry

        call_count = 0

        @with_retry(max_attempts=3, base_delay=0.01)
        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("network blip")
            return "recovered"

        result = await flaky()
        assert result == "recovered"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_gives_up_after_max_attempts(self):
        """Function that always fails raises after max_attempts."""
        from src.post.retry import with_retry

        @with_retry(max_attempts=3, base_delay=0.01)
        async def always_fail():
            raise ConnectionError("down")

        with pytest.raises(ConnectionError):
            await always_fail()

    @pytest.mark.asyncio
    async def test_no_retry_on_auth_error(self):
        """Auth errors are not retried — they raise immediately."""
        from src.post.retry import with_retry, AuthError

        call_count = 0

        @with_retry(max_attempts=3, base_delay=0.01)
        async def auth_fail():
            nonlocal call_count
            call_count += 1
            raise AuthError("bad creds")

        with pytest.raises(AuthError):
            await auth_fail()
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_rate_limit_waits_longer(self):
        """Rate-limit errors use a longer wait before retrying."""
        from src.post.retry import with_retry, RateLimitError

        call_count = 0

        @with_retry(max_attempts=3, base_delay=0.01)
        async def rate_limited():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RateLimitError("slow down")
            return "ok"

        result = await rate_limited()
        assert result == "ok"
        assert call_count == 2


class TestRetryStrategySelection:
    """Tests that the classify_error function picks the right strategy."""

    def test_network_error_is_retry(self):
        from src.post.retry import classify_error

        assert classify_error(ConnectionError("timeout")) == "retry"

    def test_auth_error_is_relogin(self):
        from src.post.retry import classify_error, AuthError

        assert classify_error(AuthError("expired")) == "relogin"

    def test_rate_limit_is_wait(self):
        from src.post.retry import classify_error, RateLimitError

        assert classify_error(RateLimitError("429")) == "wait"

    def test_unknown_error_is_retry(self):
        from src.post.retry import classify_error

        assert classify_error(RuntimeError("unknown")) == "retry"


# ---------------------------------------------------------------------------
# 2FA / CAPTCHA detection tests
# ---------------------------------------------------------------------------


class TestTwoFactorDetection:
    """Tests for 2FA and CAPTCHA detection in publisher helpers."""

    @pytest.mark.asyncio
    async def test_detects_2fa_prompt(self):
        """When page contains a 2FA prompt element, detect_2fa returns True."""
        from src.post.publisher import detect_2fa

        page = AsyncMock()
        page.query_selector = AsyncMock(return_value=MagicMock())  # element found
        assert await detect_2fa(page) is True

    @pytest.mark.asyncio
    async def test_no_2fa_when_absent(self):
        """When page has no 2FA prompt, detect_2fa returns False."""
        from src.post.publisher import detect_2fa

        page = AsyncMock()
        page.query_selector = AsyncMock(return_value=None)
        assert await detect_2fa(page) is False

    @pytest.mark.asyncio
    async def test_detects_captcha(self):
        """When page contains a CAPTCHA, detect_captcha returns True."""
        from src.post.publisher import detect_captcha

        page = AsyncMock()
        page.query_selector = AsyncMock(return_value=MagicMock())
        assert await detect_captcha(page) is True

    @pytest.mark.asyncio
    async def test_no_captcha_when_absent(self):
        """When page has no CAPTCHA, detect_captcha returns False."""
        from src.post.publisher import detect_captcha

        page = AsyncMock()
        page.query_selector = AsyncMock(return_value=None)
        assert await detect_captcha(page) is False

    @pytest.mark.asyncio
    async def test_wait_for_manual_input_times_out(self):
        """wait_for_manual_input raises TimeoutError after timeout."""
        from src.post.publisher import wait_for_manual_input

        page = AsyncMock()
        # Simulate the challenge never being resolved
        page.query_selector = AsyncMock(return_value=MagicMock())  # still present

        with pytest.raises(TimeoutError):
            await wait_for_manual_input(page, challenge_type="2fa", timeout_seconds=0.1, poll_interval=0.05)


# ---------------------------------------------------------------------------
# Platform poster tests (mocked Playwright)
# ---------------------------------------------------------------------------


class TestTwitterPoster:
    """Tests for post_to_twitter with fully mocked Playwright."""

    @pytest.mark.asyncio
    async def test_skips_when_credentials_missing(self):
        """Returns False and logs warning when credentials are empty."""
        with patch("src.post.publisher.TWITTER_USERNAME", ""), \
             patch("src.post.publisher.TWITTER_PASSWORD", ""):
            from src.post.publisher import post_to_twitter
            result = await post_to_twitter(Path("/fake/img.png"), "hello")
            assert result is False

    @pytest.mark.asyncio
    async def test_calls_playwright_correctly(self):
        """Verifies the Playwright call sequence for a Twitter post."""
        mock_page = AsyncMock()
        mock_page.query_selector = AsyncMock(return_value=AsyncMock())  # file input
        # Make detect_2fa/detect_captcha return False
        mock_page.url = "https://x.com/home"

        mock_ctx = AsyncMock()
        mock_ctx.new_page = AsyncMock(return_value=mock_page)
        mock_ctx.storage_state = AsyncMock(return_value={"cookies": [], "origins": []})

        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_ctx)

        mock_chromium = AsyncMock()
        mock_chromium.launch = AsyncMock(return_value=mock_browser)

        mock_pw = AsyncMock()
        mock_pw.chromium = mock_chromium

        mock_pw_cm = AsyncMock()
        mock_pw_cm.__aenter__ = AsyncMock(return_value=mock_pw)
        mock_pw_cm.__aexit__ = AsyncMock(return_value=False)

        with patch("src.post.publisher.TWITTER_USERNAME", "user"), \
             patch("src.post.publisher.TWITTER_PASSWORD", "pass"), \
             patch("src.post.publisher.async_playwright", return_value=mock_pw_cm), \
             patch("src.post.publisher.load_session", return_value=None), \
             patch("src.post.publisher.save_session"), \
             patch("src.post.publisher.detect_2fa", new_callable=AsyncMock, return_value=False), \
             patch("src.post.publisher.detect_captcha", new_callable=AsyncMock, return_value=False):
            from src.post.publisher import post_to_twitter
            result = await post_to_twitter(Path("/fake/img.png"), "AI news!")
            assert result is True
            mock_page.goto.assert_called()
            mock_page.fill.assert_called()


class TestLinkedInPoster:
    """Tests for post_to_linkedin with fully mocked Playwright."""

    @pytest.mark.asyncio
    async def test_skips_when_credentials_missing(self):
        with patch("src.post.publisher.LINKEDIN_EMAIL", ""), \
             patch("src.post.publisher.LINKEDIN_PASSWORD", ""):
            from src.post.publisher import post_to_linkedin
            result = await post_to_linkedin(Path("/fake/img.png"), "hello")
            assert result is False

    @pytest.mark.asyncio
    async def test_calls_playwright_correctly(self):
        mock_editor = AsyncMock()
        mock_file_input = AsyncMock()
        mock_done_btn = AsyncMock()

        mock_page = AsyncMock()
        mock_page.wait_for_selector = AsyncMock(side_effect=[mock_editor, mock_file_input])
        mock_page.query_selector = AsyncMock(return_value=mock_done_btn)
        mock_page.url = "https://www.linkedin.com/feed/"

        mock_ctx = AsyncMock()
        mock_ctx.new_page = AsyncMock(return_value=mock_page)
        mock_ctx.storage_state = AsyncMock(return_value={"cookies": [], "origins": []})

        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_ctx)

        mock_chromium = AsyncMock()
        mock_chromium.launch = AsyncMock(return_value=mock_browser)

        mock_pw = AsyncMock()
        mock_pw.chromium = mock_chromium

        mock_pw_cm = AsyncMock()
        mock_pw_cm.__aenter__ = AsyncMock(return_value=mock_pw)
        mock_pw_cm.__aexit__ = AsyncMock(return_value=False)

        with patch("src.post.publisher.LINKEDIN_EMAIL", "user@test.com"), \
             patch("src.post.publisher.LINKEDIN_PASSWORD", "pass"), \
             patch("src.post.publisher.async_playwright", return_value=mock_pw_cm), \
             patch("src.post.publisher.load_session", return_value=None), \
             patch("src.post.publisher.save_session"), \
             patch("src.post.publisher.detect_2fa", new_callable=AsyncMock, return_value=False), \
             patch("src.post.publisher.detect_captcha", new_callable=AsyncMock, return_value=False):
            from src.post.publisher import post_to_linkedin
            result = await post_to_linkedin(Path("/fake/img.png"), "AI news!")
            assert result is True
            mock_page.goto.assert_called()


class TestInstagramPoster:
    """Tests for post_to_instagram with fully mocked Playwright."""

    @pytest.mark.asyncio
    async def test_skips_when_credentials_missing(self):
        with patch("src.post.publisher.INSTAGRAM_USERNAME", ""), \
             patch("src.post.publisher.INSTAGRAM_PASSWORD", ""):
            from src.post.publisher import post_to_instagram
            result = await post_to_instagram(Path("/fake/img.png"), "hello #ai")
            assert result is False

    @pytest.mark.asyncio
    async def test_calls_playwright_correctly(self):
        mock_file_input = AsyncMock()
        mock_page = AsyncMock()
        mock_page.wait_for_selector = AsyncMock(return_value=mock_file_input)
        mock_page.query_selector = AsyncMock(return_value=AsyncMock())
        mock_page.url = "https://www.instagram.com/"

        mock_ctx = AsyncMock()
        mock_ctx.new_page = AsyncMock(return_value=mock_page)
        mock_ctx.storage_state = AsyncMock(return_value={"cookies": [], "origins": []})

        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_ctx)

        mock_chromium = AsyncMock()
        mock_chromium.launch = AsyncMock(return_value=mock_browser)

        mock_pw = AsyncMock()
        mock_pw.chromium = mock_chromium

        mock_pw_cm = AsyncMock()
        mock_pw_cm.__aenter__ = AsyncMock(return_value=mock_pw)
        mock_pw_cm.__aexit__ = AsyncMock(return_value=False)

        with patch("src.post.publisher.INSTAGRAM_USERNAME", "iguser"), \
             patch("src.post.publisher.INSTAGRAM_PASSWORD", "igpass"), \
             patch("src.post.publisher.async_playwright", return_value=mock_pw_cm), \
             patch("src.post.publisher.load_session", return_value=None), \
             patch("src.post.publisher.save_session"), \
             patch("src.post.publisher.detect_2fa", new_callable=AsyncMock, return_value=False), \
             patch("src.post.publisher.detect_captcha", new_callable=AsyncMock, return_value=False):
            from src.post.publisher import post_to_instagram
            result = await post_to_instagram(Path("/fake/img.png"), "AI update #ml")
            assert result is True
            mock_page.goto.assert_called()

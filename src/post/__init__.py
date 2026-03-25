"""Social media posting package.

Public API:
    post_to_twitter   — post infographic to Twitter/X
    post_to_linkedin  — post infographic to LinkedIn
    post_to_instagram — post infographic to Instagram
    save_session / load_session / is_session_expired — session helpers
    with_retry / AuthError / RateLimitError — retry helpers
"""

from .publisher import (
    post_to_twitter,
    post_to_linkedin,
    post_to_instagram,
    detect_2fa,
    detect_captcha,
    wait_for_manual_input,
)
from .session import save_session, load_session, is_session_expired
from .retry import with_retry, AuthError, RateLimitError, classify_error

__all__ = [
    "post_to_twitter",
    "post_to_linkedin",
    "post_to_instagram",
    "detect_2fa",
    "detect_captcha",
    "wait_for_manual_input",
    "save_session",
    "load_session",
    "is_session_expired",
    "with_retry",
    "AuthError",
    "RateLimitError",
    "classify_error",
]

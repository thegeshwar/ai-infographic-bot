"""Retry logic with exponential backoff and error classification.

Provides a ``@with_retry`` decorator for async functions and custom exception
types for auth and rate-limit failures.
"""

import asyncio
import functools
import logging
from typing import Callable

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom error types
# ---------------------------------------------------------------------------

class AuthError(Exception):
    """Raised when authentication fails (bad creds, expired token, etc.)."""


class RateLimitError(Exception):
    """Raised when the platform returns a rate-limit / 429 response."""


# ---------------------------------------------------------------------------
# Error classification
# ---------------------------------------------------------------------------

def classify_error(exc: Exception) -> str:
    """Return a strategy string for the given exception.

    Returns
    -------
    "relogin" — caller should re-authenticate, do not retry blindly.
    "wait"    — rate-limited; wait longer then retry.
    "retry"   — transient / unknown; retry with normal backoff.
    """
    if isinstance(exc, AuthError):
        return "relogin"
    if isinstance(exc, RateLimitError):
        return "wait"
    return "retry"


# ---------------------------------------------------------------------------
# Decorator
# ---------------------------------------------------------------------------

def with_retry(
    max_attempts: int = 3,
    base_delay: float = 2.0,
    rate_limit_multiplier: float = 5.0,
) -> Callable:
    """Decorator that retries an async function with exponential backoff.

    Parameters
    ----------
    max_attempts:
        Total number of attempts (including the first call).
    base_delay:
        Seconds to wait after the first failure; doubled each attempt.
    rate_limit_multiplier:
        Extra multiplier applied to the delay for ``RateLimitError``.

    Behaviour by error type
    -----------------------
    * ``AuthError``      — raised immediately, no retry.
    * ``RateLimitError`` — retried with a longer delay.
    * Other exceptions   — retried with normal exponential backoff.
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            last_exc: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await fn(*args, **kwargs)
                except AuthError:
                    # Auth errors are not retryable
                    raise
                except RateLimitError as exc:
                    last_exc = exc
                    if attempt == max_attempts:
                        raise
                    delay = base_delay * (2 ** (attempt - 1)) * rate_limit_multiplier
                    logger.warning(
                        "Rate limited on attempt %d/%d — waiting %.1fs",
                        attempt, max_attempts, delay,
                    )
                    await asyncio.sleep(delay)
                except Exception as exc:
                    last_exc = exc
                    if attempt == max_attempts:
                        raise
                    delay = base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        "Attempt %d/%d failed (%s) — retrying in %.1fs",
                        attempt, max_attempts, exc, delay,
                    )
                    await asyncio.sleep(delay)
            # Should not reach here, but just in case
            raise last_exc  # type: ignore[misc]

        return wrapper

    return decorator

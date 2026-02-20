"""SignalOps exception hierarchy and retry utilities."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ── Exception Hierarchy ──


class SignalOpsError(Exception):
    """Base exception for all signalops errors."""


class APIError(SignalOpsError):
    """Raised when an external API call fails."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable


class RateLimitError(APIError):
    """Raised when an API rate limit is hit (HTTP 429)."""

    def __init__(self, message: str, retry_after: float = 60.0) -> None:
        super().__init__(message, status_code=429, retryable=True)
        self.retry_after = retry_after


class AuthenticationError(APIError):
    """Raised when API authentication fails (HTTP 401/403)."""

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message, status_code=401, retryable=False)


class StreamTierError(APIError):
    """Raised when Filtered Stream access requires a higher API tier."""

    def __init__(self, message: str = "Filtered Stream requires X API Pro tier") -> None:
        super().__init__(message, status_code=403, retryable=False)


class ConfigError(SignalOpsError):
    """Raised when project configuration is invalid or missing."""


# ── Retry Utility ──


def retry_with_backoff(
    fn: Callable[[], T],
    *,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_exceptions: tuple[type[Exception], ...] = (APIError,),
) -> T:
    """Execute *fn* with exponential backoff on retryable exceptions.

    Non-retryable ``APIError`` instances propagate immediately.
    After exhausting retries the last error is re-raised.
    """
    last_error: Exception | None = None

    for attempt in range(max_retries):
        try:
            return fn()
        except retryable_exceptions as exc:
            last_error = exc

            # Non-retryable API errors should not be retried
            if isinstance(exc, APIError) and not exc.retryable:
                raise

            delay = min(base_delay * (2**attempt), max_delay)

            # Honour retry-after from rate limit errors
            if isinstance(exc, RateLimitError):
                delay = max(delay, exc.retry_after)

            if attempt < max_retries - 1:
                logger.warning(
                    "Attempt %d/%d failed: %s — retrying in %.1fs",
                    attempt + 1,
                    max_retries,
                    exc,
                    delay,
                )
                time.sleep(delay)
            else:
                logger.error(
                    "Attempt %d/%d failed: %s — no retries left",
                    attempt + 1,
                    max_retries,
                    exc,
                )

    assert last_error is not None  # noqa: S101
    raise last_error

"""Sliding window rate limiter with jitter for API compliance."""

from __future__ import annotations

import random
import time
from collections import deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from signalops.storage.cache import CacheBackend


class RateLimiter:
    """Token-bucket-style rate limiter using a sliding window of timestamps.

    Optionally accepts a CacheBackend for persisting state across process restarts.
    """

    def __init__(
        self,
        max_requests: int,
        window_seconds: int,
        jitter_range: float = 0.2,
        cache: CacheBackend | None = None,
        cache_key: str = "ratelimit:default",
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.jitter_range = jitter_range
        self._cache = cache
        self._cache_key = cache_key
        self._timestamps: deque[float] = deque()
        # State that can be overridden by API response headers
        self._header_remaining: int | None = None
        self._header_reset_at: float | None = None
        # Restore state from cache if available
        self._restore_from_cache()

    def acquire(self) -> float:
        """Try to acquire a rate limit token.

        Returns 0.0 if allowed immediately, or the number of seconds to wait.
        """
        now = time.monotonic()

        # If we have header-based info and it says we're out of tokens
        if self._header_remaining is not None and self._header_remaining <= 0:
            if self._header_reset_at is not None:
                wall_now = time.time()
                wait = max(0.0, self._header_reset_at - wall_now)
                if wait > 0:
                    return self._add_jitter(wait)
            # Reset header state after using it
            self._header_remaining = None
            self._header_reset_at = None

        # Purge timestamps outside the window
        cutoff = now - self.window_seconds
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()

        if len(self._timestamps) < self.max_requests:
            self._timestamps.append(now)
            return 0.0

        # Window is full — calculate wait time until oldest entry expires
        oldest = self._timestamps[0]
        wait = (oldest + self.window_seconds) - now
        return self._add_jitter(max(0.0, wait))

    def update_from_headers(self, headers: dict[str, str]) -> None:
        """Update rate limit state from X API response headers."""
        remaining = headers.get("x-rate-limit-remaining")
        reset = headers.get("x-rate-limit-reset")

        if remaining is not None:
            self._header_remaining = int(remaining)
        if reset is not None:
            self._header_reset_at = float(reset)

        self._persist_to_cache()

    @property
    def tokens(self) -> int:
        """Return remaining requests in current window."""
        if self._header_remaining is not None:
            return self._header_remaining

        now = time.monotonic()
        cutoff = now - self.window_seconds
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()

        return max(0, self.max_requests - len(self._timestamps))

    def _add_jitter(self, wait_time: float) -> float:
        """Add randomized jitter to a wait time."""
        if wait_time <= 0 or self.jitter_range <= 0:
            return wait_time
        jitter = wait_time * self.jitter_range
        return wait_time + random.uniform(-jitter, jitter)

    def _persist_to_cache(self) -> None:
        """Save header-based rate limit state to cache for cross-process persistence."""
        if self._cache is None:
            return
        import json

        state = {
            "header_remaining": self._header_remaining,
            "header_reset_at": self._header_reset_at,
        }
        self._cache.set(self._cache_key, json.dumps(state), ttl=self.window_seconds)

    def _restore_from_cache(self) -> None:
        """Restore rate limit state from cache on startup."""
        if self._cache is None:
            return
        import json

        raw = self._cache.get(self._cache_key)
        if raw is None:
            return
        try:
            state = json.loads(raw)
            self._header_remaining = state.get("header_remaining")
            self._header_reset_at = state.get("header_reset_at")
        except (json.JSONDecodeError, TypeError):
            pass  # Corrupted cache entry — ignore

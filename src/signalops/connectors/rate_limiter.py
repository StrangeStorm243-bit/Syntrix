"""Sliding window rate limiter with jitter for API compliance."""

import random
import time
from collections import deque


class RateLimiter:
    """Token-bucket-style rate limiter using a sliding window of timestamps."""

    def __init__(
        self,
        max_requests: int,
        window_seconds: int,
        jitter_range: float = 0.2,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.jitter_range = jitter_range
        self._timestamps: deque[float] = deque()
        # State that can be overridden by API response headers
        self._header_remaining: int | None = None
        self._header_reset_at: float | None = None

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

    def update_from_headers(self, headers: dict) -> None:
        """Update rate limit state from X API response headers."""
        remaining = headers.get("x-rate-limit-remaining")
        reset = headers.get("x-rate-limit-reset")

        if remaining is not None:
            self._header_remaining = int(remaining)
        if reset is not None:
            self._header_reset_at = float(reset)

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

"""Tests for the sliding window rate limiter."""

import time

from signalops.connectors.rate_limiter import RateLimiter
from signalops.storage.cache import InMemoryCache


class TestWithinLimit:
    def test_allows_all_within_limit(self):
        rl = RateLimiter(max_requests=10, window_seconds=900)
        for _ in range(10):
            assert rl.acquire() == 0.0

    def test_single_request(self):
        rl = RateLimiter(max_requests=1, window_seconds=900)
        assert rl.acquire() == 0.0


class TestOverLimit:
    def test_blocks_when_over_limit(self):
        rl = RateLimiter(max_requests=2, window_seconds=900, jitter_range=0.0)
        rl.acquire()
        rl.acquire()
        wait = rl.acquire()
        assert wait > 0

    def test_wait_time_is_reasonable(self):
        rl = RateLimiter(max_requests=2, window_seconds=60, jitter_range=0.0)
        rl.acquire()
        rl.acquire()
        wait = rl.acquire()
        # Should need to wait up to window_seconds
        assert 0 < wait <= 60


class TestTokensProperty:
    def test_full_tokens(self):
        rl = RateLimiter(max_requests=10, window_seconds=900)
        assert rl.tokens == 10

    def test_tokens_decrease(self):
        rl = RateLimiter(max_requests=10, window_seconds=900)
        rl.acquire()
        rl.acquire()
        assert rl.tokens == 8

    def test_tokens_at_zero(self):
        rl = RateLimiter(max_requests=2, window_seconds=900)
        rl.acquire()
        rl.acquire()
        assert rl.tokens == 0


class TestHeaderUpdates:
    def test_update_remaining(self):
        rl = RateLimiter(max_requests=300, window_seconds=900)
        rl.update_from_headers({"x-rate-limit-remaining": "5"})
        assert rl.tokens == 5

    def test_update_remaining_and_reset(self):
        rl = RateLimiter(max_requests=300, window_seconds=900)
        future = str(int(time.time()) + 60)
        rl.update_from_headers(
            {
                "x-rate-limit-remaining": "0",
                "x-rate-limit-reset": future,
            }
        )
        # Should block because remaining is 0
        wait = rl.acquire()
        assert wait > 0

    def test_partial_headers(self):
        rl = RateLimiter(max_requests=300, window_seconds=900)
        rl.update_from_headers({"x-rate-limit-remaining": "50"})
        assert rl.tokens == 50


class TestJitter:
    def test_jitter_varies_wait_times(self):
        """Multiple calls should produce different wait times due to jitter."""
        waits = set()
        for _ in range(20):
            rl = RateLimiter(max_requests=1, window_seconds=60, jitter_range=0.2)
            rl.acquire()
            wait = rl.acquire()
            waits.add(round(wait, 4))
        # With jitter, we should get at least a few different values
        assert len(waits) > 1

    def test_zero_jitter_is_consistent(self):
        rl = RateLimiter(max_requests=1, window_seconds=60, jitter_range=0.0)
        rl.acquire()
        w1 = rl.acquire()
        # Reset and try again
        rl2 = RateLimiter(max_requests=1, window_seconds=60, jitter_range=0.0)
        rl2.acquire()
        w2 = rl2.acquire()
        # Both should be very close (within timing precision)
        assert abs(w1 - w2) < 1.0

    def test_jitter_within_range(self):
        """Wait times should be within ±jitter_range of base wait."""
        rl = RateLimiter(max_requests=1, window_seconds=100, jitter_range=0.2)
        rl.acquire()
        waits = [rl._add_jitter(10.0) for _ in range(100)]
        for w in waits:
            assert 8.0 <= w <= 12.0  # 10 ± 20%


class TestCachePersistence:
    def test_persist_header_state_to_cache(self) -> None:
        cache = InMemoryCache()
        rl = RateLimiter(max_requests=300, window_seconds=900, cache=cache)
        future = str(int(time.time()) + 60)
        rl.update_from_headers({"x-rate-limit-remaining": "5", "x-rate-limit-reset": future})
        # Cache should have the state
        assert cache.exists("ratelimit:default")

    def test_restore_header_state_from_cache(self) -> None:
        cache = InMemoryCache()
        # First limiter persists state
        rl1 = RateLimiter(max_requests=300, window_seconds=900, cache=cache)
        future = str(int(time.time()) + 60)
        rl1.update_from_headers({"x-rate-limit-remaining": "5", "x-rate-limit-reset": future})
        # Second limiter restores from cache
        rl2 = RateLimiter(max_requests=300, window_seconds=900, cache=cache)
        assert rl2.tokens == 5

    def test_no_cache_no_error(self) -> None:
        """Rate limiter works fine without cache."""
        rl = RateLimiter(max_requests=10, window_seconds=900, cache=None)
        assert rl.acquire() == 0.0

    def test_custom_cache_key(self) -> None:
        cache = InMemoryCache()
        rl = RateLimiter(
            max_requests=300, window_seconds=900, cache=cache, cache_key="ratelimit:x-search"
        )
        rl.update_from_headers({"x-rate-limit-remaining": "3"})
        assert cache.exists("ratelimit:x-search")
        assert not cache.exists("ratelimit:default")

"""Tests for the cache system: InMemoryCache, RedisCache (mocked), and helper functions."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

from signalops.config.schema import RedisConfig
from signalops.storage.cache import (
    InMemoryCache,
    RedisCache,
    cache_search_results,
    get_cache,
    get_cached_search,
    is_duplicate,
    mark_seen,
)


class TestInMemoryCache:
    def test_get_set(self) -> None:
        cache = InMemoryCache()
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_missing_key(self) -> None:
        cache = InMemoryCache()
        assert cache.get("nonexistent") is None

    def test_exists(self) -> None:
        cache = InMemoryCache()
        assert cache.exists("key1") is False
        cache.set("key1", "value1")
        assert cache.exists("key1") is True

    def test_delete(self) -> None:
        cache = InMemoryCache()
        cache.set("key1", "value1")
        assert cache.delete("key1") is True
        assert cache.get("key1") is None

    def test_delete_missing_key(self) -> None:
        cache = InMemoryCache()
        assert cache.delete("nonexistent") is False

    def test_ttl_expiry(self) -> None:
        cache = InMemoryCache()
        cache.set("key1", "value1", ttl=1)
        assert cache.get("key1") == "value1"

        # Simulate time passing by manipulating the store directly
        key_value, _ = cache._store["key1"]
        cache._store["key1"] = (key_value, time.monotonic() - 1)

        assert cache.get("key1") is None
        assert cache.exists("key1") is False

    def test_no_ttl_persists(self) -> None:
        cache = InMemoryCache()
        cache.set("key1", "value1")  # No TTL
        assert cache.get("key1") == "value1"

    def test_overwrite_value(self) -> None:
        cache = InMemoryCache()
        cache.set("key1", "old")
        cache.set("key1", "new")
        assert cache.get("key1") == "new"

    def test_cleanup_expired(self) -> None:
        cache = InMemoryCache()
        cache.set("keep", "yes")
        cache.set("expire", "no", ttl=1)

        # Expire the entry
        key_value, _ = cache._store["expire"]
        cache._store["expire"] = (key_value, time.monotonic() - 1)

        cache._cleanup_expired()
        assert "keep" in cache._store
        assert "expire" not in cache._store


class TestRedisCache:
    def test_get_set(self) -> None:
        mock_redis = MagicMock()
        mock_redis.get.return_value = "value1"

        cache = RedisCache()
        cache._client = mock_redis

        cache.set("key1", "value1")
        mock_redis.set.assert_called_once_with("key1", "value1")

        result = cache.get("key1")
        assert result == "value1"

    def test_set_with_ttl(self) -> None:
        mock_redis = MagicMock()
        cache = RedisCache()
        cache._client = mock_redis

        cache.set("key1", "value1", ttl=300)
        mock_redis.setex.assert_called_once_with("key1", 300, "value1")

    def test_exists(self) -> None:
        mock_redis = MagicMock()
        mock_redis.exists.return_value = 1
        cache = RedisCache()
        cache._client = mock_redis

        assert cache.exists("key1") is True
        mock_redis.exists.assert_called_once_with("key1")

    def test_delete(self) -> None:
        mock_redis = MagicMock()
        mock_redis.delete.return_value = 1
        cache = RedisCache()
        cache._client = mock_redis

        assert cache.delete("key1") is True
        mock_redis.delete.assert_called_once_with("key1")

    def test_lazy_connection(self) -> None:
        cache = RedisCache(url="redis://localhost:6379/0")
        assert cache._client is None

        mock_redis = MagicMock()
        with patch("redis.from_url", return_value=mock_redis):
            cache._connect()

        assert cache._client is mock_redis


class TestGetCacheFactory:
    def test_disabled_returns_in_memory(self) -> None:
        config = RedisConfig(enabled=False)
        cache = get_cache(config)
        assert isinstance(cache, InMemoryCache)

    def test_enabled_but_unavailable_returns_in_memory(self) -> None:
        config = RedisConfig(enabled=True, url="redis://nonexistent:6379/0")
        with patch("signalops.storage.cache.RedisCache") as mock_cls:
            instance = MagicMock()
            instance._connect.return_value.ping.side_effect = ConnectionError("no redis")
            mock_cls.return_value = instance
            cache = get_cache(config)
        assert isinstance(cache, InMemoryCache)

    def test_enabled_and_available_returns_redis(self) -> None:
        config = RedisConfig(enabled=True, url="redis://localhost:6379/0")
        with patch("signalops.storage.cache.RedisCache") as mock_cls:
            instance = MagicMock(spec=RedisCache)
            instance._connect.return_value.ping.return_value = True
            mock_cls.return_value = instance
            cache = get_cache(config)
        # Should return the RedisCache mock instance
        assert cache is instance


class TestDedupHelpers:
    def test_mark_seen_and_check(self) -> None:
        cache = InMemoryCache()
        assert is_duplicate(cache, "x", "12345", "spectra") is False
        mark_seen(cache, "x", "12345", "spectra")
        assert is_duplicate(cache, "x", "12345", "spectra") is True

    def test_different_projects_not_duplicate(self) -> None:
        cache = InMemoryCache()
        mark_seen(cache, "x", "12345", "spectra")
        assert is_duplicate(cache, "x", "12345", "salesense") is False

    def test_different_platforms_not_duplicate(self) -> None:
        cache = InMemoryCache()
        mark_seen(cache, "x", "12345", "spectra")
        assert is_duplicate(cache, "linkedin", "12345", "spectra") is False

    def test_dedup_with_ttl(self) -> None:
        cache = InMemoryCache()
        mark_seen(cache, "x", "12345", "spectra", ttl=1)

        # Expire the entry
        for key in list(cache._store.keys()):
            val, _ = cache._store[key]
            cache._store[key] = (val, time.monotonic() - 1)

        assert is_duplicate(cache, "x", "12345", "spectra") is False


class TestSearchCacheHelpers:
    def test_cache_and_retrieve(self) -> None:
        cache = InMemoryCache()
        results = [{"id": "1", "text": "hello"}, {"id": "2", "text": "world"}]
        cache_search_results(cache, "test query", results)

        cached = get_cached_search(cache, "test query")
        assert cached == results

    def test_cache_miss(self) -> None:
        cache = InMemoryCache()
        assert get_cached_search(cache, "unknown query") is None

    def test_different_queries_different_keys(self) -> None:
        cache = InMemoryCache()
        results_a = [{"id": "1"}]
        results_b = [{"id": "2"}]
        cache_search_results(cache, "query a", results_a)
        cache_search_results(cache, "query b", results_b)

        assert get_cached_search(cache, "query a") == results_a
        assert get_cached_search(cache, "query b") == results_b

    def test_cache_with_ttl(self) -> None:
        cache = InMemoryCache()
        results = [{"id": "1"}]
        cache_search_results(cache, "test", results, ttl=1)

        # Expire the entry
        for key in list(cache._store.keys()):
            val, _ = cache._store[key]
            cache._store[key] = (val, time.monotonic() - 1)

        assert get_cached_search(cache, "test") is None

    def test_serialization_round_trip(self) -> None:
        cache = InMemoryCache()
        results = [
            {"id": "1", "metrics": {"likes": 5, "views": 100}},
            {"id": "2", "nested": {"deep": True}},
        ]
        cache_search_results(cache, "complex", results)
        cached = get_cached_search(cache, "complex")
        assert cached == results

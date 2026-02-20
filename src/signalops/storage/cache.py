"""Cache backends for deduplication and search result caching.

Redis is optional — falls back to in-memory cache if unavailable.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from signalops.config.schema import RedisConfig

logger = logging.getLogger(__name__)


class CacheBackend(ABC):
    """Abstract cache backend. All implementations must handle errors gracefully."""

    @abstractmethod
    def get(self, key: str) -> str | None:
        """Get a value by key. Returns None if not found or expired."""

    @abstractmethod
    def set(self, key: str, value: str, ttl: int | None = None) -> None:
        """Set a key-value pair with optional TTL in seconds."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a key exists and is not expired."""

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a key. Returns True if the key existed."""


class InMemoryCache(CacheBackend):
    """Dict-based cache with TTL support. Used as fallback when Redis is unavailable."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[str, float | None]] = {}

    def get(self, key: str) -> str | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at is not None and time.monotonic() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: str, ttl: int | None = None) -> None:
        expires_at = time.monotonic() + ttl if ttl is not None else None
        self._store[key] = (value, expires_at)

    def exists(self, key: str) -> bool:
        return self.get(key) is not None

    def delete(self, key: str) -> bool:
        return self._store.pop(key, None) is not None

    def _cleanup_expired(self) -> None:
        """Remove all expired entries. Called periodically if needed."""
        now = time.monotonic()
        expired = [k for k, (_, exp) in self._store.items() if exp is not None and now > exp]
        for k in expired:
            del self._store[k]


class RedisCache(CacheBackend):
    """Redis-backed cache. Connects lazily on first operation."""

    def __init__(self, url: str = "redis://localhost:6379/0") -> None:
        self._url = url
        self._client: Any = None

    def _connect(self) -> Any:
        if self._client is None:
            import redis

            self._client = redis.from_url(self._url, decode_responses=True)
        return self._client

    def get(self, key: str) -> str | None:
        return self._connect().get(key)  # type: ignore[no-any-return]

    def set(self, key: str, value: str, ttl: int | None = None) -> None:
        client = self._connect()
        if ttl is not None:
            client.setex(key, ttl, value)
        else:
            client.set(key, value)

    def exists(self, key: str) -> bool:
        return bool(self._connect().exists(key))

    def delete(self, key: str) -> bool:
        return bool(self._connect().delete(key))


def get_cache(config: RedisConfig) -> CacheBackend:
    """Factory: return RedisCache if enabled and connectable, else InMemoryCache."""
    if not config.enabled:
        logger.debug("Redis disabled in config, using in-memory cache")
        return InMemoryCache()

    try:
        cache = RedisCache(url=config.url)
        # Test connectivity with a ping
        cache._connect().ping()
        logger.info("Connected to Redis at %s", config.url)
        return cache
    except Exception:
        logger.warning(
            "Redis unavailable at %s, falling back to in-memory cache",
            config.url,
        )
        return InMemoryCache()


# ── Dedup helpers ──


def _dedup_key(platform: str, platform_id: str, project_id: str) -> str:
    """Build a cache key for deduplication."""
    return f"dedup:{project_id}:{platform}:{platform_id}"


def is_duplicate(cache: CacheBackend, platform: str, platform_id: str, project_id: str) -> bool:
    """Check if a post has already been seen."""
    return cache.exists(_dedup_key(platform, platform_id, project_id))


def mark_seen(
    cache: CacheBackend,
    platform: str,
    platform_id: str,
    project_id: str,
    ttl: int = 86400,
) -> None:
    """Mark a post as seen in the cache."""
    cache.set(_dedup_key(platform, platform_id, project_id), "1", ttl=ttl)


# ── Search cache helpers ──


def _search_cache_key(query: str) -> str:
    """Build a cache key for a search query."""
    query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
    return f"search:{query_hash}"


def cache_search_results(
    cache: CacheBackend,
    query: str,
    results: list[dict[str, Any]],
    ttl: int = 1800,
) -> None:
    """Cache search results for a query."""
    cache.set(_search_cache_key(query), json.dumps(results), ttl=ttl)


def get_cached_search(cache: CacheBackend, query: str) -> list[dict[str, Any]] | None:
    """Get cached search results. Returns None on cache miss."""
    raw = cache.get(_search_cache_key(query))
    if raw is None:
        return None
    return json.loads(raw)  # type: ignore[no-any-return]

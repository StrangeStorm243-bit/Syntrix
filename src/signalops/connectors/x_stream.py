"""Filtered Stream connector for X API v2 (requires Pro tier).

Provides real-time tweet collection via the Filtered Stream endpoint.
Uses httpx streaming to receive tweets as they match configured rules.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import httpx

from signalops.exceptions import StreamTierError as StreamTierError  # re-export

from .base import RawPost
from .rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

BASE_URL = "https://api.x.com/2"
STREAM_URL = f"{BASE_URL}/tweets/search/stream"
RULES_URL = f"{BASE_URL}/tweets/search/stream/rules"

# Backoff constants
INITIAL_BACKOFF = 1.0
MAX_BACKOFF = 60.0
BACKOFF_MULTIPLIER = 2.0


class StreamConnector:
    """Filtered Stream connector for real-time tweet collection.

    Requires X API Pro tier ($5K/month). Falls back gracefully with
    a clear error if the tier check fails.
    """

    def __init__(
        self,
        bearer_token: str,
        rate_limiter: RateLimiter | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.bearer_token = bearer_token
        self.rate_limiter = rate_limiter
        self._client = httpx.Client(
            base_url=BASE_URL,
            headers={
                "Authorization": f"Bearer {bearer_token}",
                "User-Agent": "SignalOps/0.2.0",
            },
            timeout=timeout,
        )

    def check_tier(self) -> bool:
        """Verify Pro tier access by attempting to read stream rules.

        Raises StreamTierError if not available.
        """
        try:
            response = self._client.get("/tweets/search/stream/rules")
            if response.status_code == 403:
                raise StreamTierError(
                    "Filtered Stream requires X API Pro tier ($5K/month). "
                    "Current access level does not include this endpoint."
                )
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                raise StreamTierError(
                    "Filtered Stream requires X API Pro tier ($5K/month). "
                    "Current access level does not include this endpoint."
                ) from e
            raise

    def add_rules(self, rules: list[str]) -> list[str]:
        """Add stream filter rules. Returns rule IDs.

        Each rule is a string query (same syntax as search endpoint).
        """
        if not rules:
            return []

        payload = {"add": [{"value": rule} for rule in rules]}
        response = self._client.post(
            "/tweets/search/stream/rules",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

        rule_ids: list[str] = []
        for rule in data.get("data", []):
            rule_ids.append(rule["id"])

        errors = data.get("errors", [])
        if errors:
            logger.warning("Some rules had errors: %s", errors)

        return rule_ids

    def delete_rules(self, rule_ids: list[str]) -> None:
        """Delete stream filter rules by ID."""
        if not rule_ids:
            return

        payload = {"delete": {"ids": rule_ids}}
        response = self._client.post(
            "/tweets/search/stream/rules",
            json=payload,
        )
        response.raise_for_status()

    def get_rules(self) -> list[dict[str, str]]:
        """Get all current stream rules."""
        response = self._client.get("/tweets/search/stream/rules")
        response.raise_for_status()
        data = response.json()
        return [{"id": r["id"], "value": r["value"]} for r in data.get("data", [])]

    def stream(
        self,
        callback: Callable[[RawPost], None],
        backfill_minutes: int = 5,
        max_reconnects: int = 10,
    ) -> None:
        """Connect to Filtered Stream and process tweets in real-time.

        Calls callback for each parsed tweet. Includes automatic
        reconnection with exponential backoff on disconnects.

        Args:
            callback: Called with each RawPost as it arrives.
            backfill_minutes: Request tweets from this many minutes ago on connect.
            max_reconnects: Maximum reconnection attempts before giving up.
        """
        backoff = INITIAL_BACKOFF
        reconnects = 0

        while reconnects < max_reconnects:
            try:
                self._stream_once(callback, backfill_minutes)
                # Clean return — stream ended normally, stop reconnecting
                logger.info("Stream ended cleanly")
                return
            except httpx.ReadTimeout:
                logger.info("Stream read timeout, reconnecting...")
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    retry_after = int(e.response.headers.get("retry-after", "60"))
                    logger.warning("Stream rate limited, waiting %ds", retry_after)
                    time.sleep(retry_after)
                    continue
                logger.error("Stream HTTP error %d: %s", e.response.status_code, e)
                raise
            except (httpx.ConnectError, httpx.RemoteProtocolError):
                logger.warning(
                    "Stream disconnected, reconnecting in %.1fs (attempt %d/%d)",
                    backoff,
                    reconnects + 1,
                    max_reconnects,
                )

            time.sleep(backoff)
            backoff = min(backoff * BACKOFF_MULTIPLIER, MAX_BACKOFF)
            reconnects += 1

        logger.error("Max reconnection attempts (%d) reached, stopping stream", max_reconnects)

    def _stream_once(
        self,
        callback: Callable[[RawPost], None],
        backfill_minutes: int,
    ) -> None:
        """Single stream connection attempt."""
        params: dict[str, Any] = {
            "tweet.fields": "author_id,created_at,public_metrics,entities,conversation_id,lang",
            "user.fields": "id,username,name,public_metrics,verified",
            "expansions": "author_id",
        }
        if backfill_minutes > 0:
            params["backfill_minutes"] = backfill_minutes

        with self._client.stream(
            "GET",
            "/tweets/search/stream",
            params=params,
        ) as response:
            response.raise_for_status()

            for line in response.iter_lines():
                if not line.strip():
                    continue  # heartbeat

                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse stream line: %s", line[:100])
                    continue

                post = self._parse_stream_tweet(data)
                if post:
                    callback(post)

    def _parse_stream_tweet(self, data: dict[str, Any]) -> RawPost | None:
        """Parse a single streamed tweet into a RawPost."""
        tweet = data.get("data")
        if not tweet:
            return None

        # Build user lookup from includes
        users: dict[str, dict[str, Any]] = {}
        for user in data.get("includes", {}).get("users", []):
            users[user["id"]] = user

        author_id = tweet.get("author_id", "")
        user = users.get(author_id, {})

        created_str = tweet.get("created_at", "")
        try:
            created_at = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            created_at = datetime.now(UTC)

        metrics = tweet.get("public_metrics", {})
        entities = tweet.get("entities", {})

        return RawPost(
            platform="x",
            platform_id=tweet["id"],
            author_id=author_id,
            author_username=user.get("username", ""),
            author_display_name=user.get("name", ""),
            author_followers=user.get("public_metrics", {}).get("followers_count", 0),
            author_verified=user.get("verified", False),
            text=tweet.get("text", ""),
            created_at=created_at,
            language=tweet.get("lang"),
            reply_to_id=None,
            conversation_id=tweet.get("conversation_id"),
            metrics={
                "likes": metrics.get("like_count", 0),
                "retweets": metrics.get("retweet_count", 0),
                "replies": metrics.get("reply_count", 0),
                "views": metrics.get("impression_count", 0),
            },
            entities={
                "urls": [u.get("expanded_url", u.get("url", "")) for u in entities.get("urls", [])],
                "mentions": [m.get("username", "") for m in entities.get("mentions", [])],
                "hashtags": [h.get("tag", "") for h in entities.get("hashtags", [])],
            },
            raw_json=tweet,
        )

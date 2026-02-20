"""X API v2 connector implementation."""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

import httpx

from signalops.exceptions import (
    APIError,
    AuthenticationError,
    RateLimitError,
    retry_with_backoff,
)

from .base import Connector, RawPost
from .rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

BASE_URL = "https://api.x.com/2"

# Fields to request from the X API
TWEET_FIELDS = (
    "author_id,created_at,public_metrics,entities,"
    "conversation_id,lang,in_reply_to_user_id,referenced_tweets"
)
USER_FIELDS = "id,username,name,public_metrics,verified,description"
EXPANSIONS = "author_id"


class XConnector(Connector):
    """Connector for X (Twitter) API v2."""

    def __init__(
        self,
        bearer_token: str,
        user_token: str | None = None,
        rate_limiter: RateLimiter | None = None,
        timeout: float = 30.0,
    ):
        self.bearer_token = bearer_token
        self.user_token = user_token
        self.rate_limiter = rate_limiter
        self.timeout = timeout
        self._client = httpx.Client(
            base_url=BASE_URL,
            headers={
                "Authorization": f"Bearer {bearer_token}",
                "User-Agent": "SignalOps/0.2.0",
            },
            timeout=timeout,
        )

    def search(
        self,
        query: str,
        since_id: str | None = None,
        max_results: int = 100,
    ) -> list[RawPost]:
        """Search for recent tweets matching query."""

        def _do_search() -> list[RawPost]:
            self._wait_for_rate_limit()

            params: dict[str, Any] = {
                "query": query,
                "max_results": min(max_results, 100),
                "tweet.fields": TWEET_FIELDS,
                "user.fields": USER_FIELDS,
                "expansions": EXPANSIONS,
            }
            if since_id:
                params["since_id"] = since_id

            response = self._client.get("/tweets/search/recent", params=params)
            self._update_rate_limits(response)
            self._raise_for_status(response)

            data = response.json()
            if "data" not in data:
                return []

            # Build user lookup from includes
            users: dict[str, Any] = {}
            for user in data.get("includes", {}).get("users", []):
                users[user["id"]] = user

            posts: list[RawPost] = []
            for tweet in data["data"]:
                post = self._parse_tweet(tweet, users)
                if post:
                    posts.append(post)

            return posts

        return retry_with_backoff(_do_search, max_retries=3, base_delay=2.0)

    def get_user(self, user_id: str) -> dict[str, Any]:
        """Fetch user profile by ID."""

        def _do_get_user() -> dict[str, Any]:
            self._wait_for_rate_limit()

            response = self._client.get(
                f"/users/{user_id}",
                params={"user.fields": USER_FIELDS},
            )
            self._update_rate_limits(response)
            self._raise_for_status(response)
            data: dict[str, Any] = response.json().get("data", {})
            return data

        return retry_with_backoff(_do_get_user, max_retries=3, base_delay=2.0)

    def post_reply(self, in_reply_to_id: str, text: str) -> str:
        """Post a reply tweet. Requires user OAuth token."""
        if not self.user_token:
            raise RuntimeError("User OAuth token required for posting replies")

        def _do_post_reply() -> str:
            self._wait_for_rate_limit()

            headers = {
                "Authorization": f"Bearer {self.user_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "text": text,
                "reply": {"in_reply_to_tweet_id": in_reply_to_id},
            }

            response = self._client.post("/tweets", json=payload, headers=headers)
            self._update_rate_limits(response)
            self._raise_for_status(response)

            result: dict[str, Any] = response.json()
            post_id: str = result["data"]["id"]
            return post_id

        return retry_with_backoff(_do_post_reply, max_retries=3, base_delay=2.0)

    def get_tweet_metrics(self, tweet_ids: list[str]) -> dict[str, dict[str, int]]:
        """Fetch current engagement metrics for tweets.

        Used by outcome tracker to check if sent replies got engagement.
        Batches up to 100 IDs per request.
        """
        if not tweet_ids:
            return {}

        result: dict[str, dict[str, int]] = {}

        for i in range(0, len(tweet_ids), 100):
            batch = tweet_ids[i : i + 100]

            def _do_fetch_batch() -> dict[str, Any]:
                self._wait_for_rate_limit()

                response = self._client.get(
                    "/tweets",
                    params={
                        "ids": ",".join(batch),
                        "tweet.fields": "public_metrics",
                    },
                )
                self._update_rate_limits(response)
                self._raise_for_status(response)
                data: dict[str, Any] = response.json()
                return data

            try:
                data = retry_with_backoff(_do_fetch_batch, max_retries=3, base_delay=2.0)
            except RateLimitError:
                logger.warning("Rate limited during metrics fetch, returning partial results")
                break

            for tweet in data.get("data", []):
                metrics = tweet.get("public_metrics", {})
                result[tweet["id"]] = {
                    "likes": metrics.get("like_count", 0),
                    "retweets": metrics.get("retweet_count", 0),
                    "replies": metrics.get("reply_count", 0),
                    "views": metrics.get("impression_count", 0),
                }

            # Track deleted/unavailable tweets from errors
            for error in data.get("errors", []):
                tweet_id = error.get("resource_id", error.get("value", ""))
                if tweet_id and tweet_id not in result:
                    result[tweet_id] = {"likes": 0, "retweets": 0, "replies": 0, "views": 0}

        return result

    def health_check(self) -> bool:
        """Verify API connectivity and auth."""
        try:
            response = self._client.get(
                "/tweets/search/recent",
                params={"query": "test", "max_results": 10},
            )
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    def _raise_for_status(self, response: httpx.Response) -> None:
        """Map HTTP status codes to typed exceptions."""
        status = response.status_code
        if 200 <= status < 300:
            return

        url = str(response.url)
        if status == 429:
            retry_after = float(response.headers.get("retry-after", "60"))
            raise RateLimitError(f"Rate limited on {url}", retry_after=retry_after)
        if status in (401, 403):
            raise AuthenticationError(f"Auth failed ({status}) on {url}")
        if status >= 500:
            raise APIError(
                f"Server error {status} on {url}",
                status_code=status,
                retryable=True,
            )
        # Other 4xx — client error, not retryable
        raise APIError(
            f"Client error {status} on {url}",
            status_code=status,
            retryable=False,
        )

    def _parse_tweet(self, tweet: dict[str, Any], users: dict[str, Any]) -> RawPost | None:
        """Parse a single X API v2 tweet into a RawPost."""
        author_id = tweet.get("author_id", "")
        user = users.get(author_id, {})

        # Parse created_at timestamp
        created_str = tweet.get("created_at", "")
        try:
            created_at = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            created_at = datetime.now(UTC)

        metrics = tweet.get("public_metrics", {})
        entities = tweet.get("entities", {})

        # Check for reply_to
        reply_to_id = None
        for ref in tweet.get("referenced_tweets", []):
            if ref.get("type") == "replied_to":
                reply_to_id = ref.get("id")
                break

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
            reply_to_id=reply_to_id,
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

    def _wait_for_rate_limit(self) -> None:
        """Block if rate limiter says we need to wait."""
        if self.rate_limiter is None:
            return
        wait = self.rate_limiter.acquire()
        if wait > 0:
            logger.info("Rate limit: waiting %.1f seconds", wait)
            time.sleep(wait)

    def _update_rate_limits(self, response: httpx.Response) -> None:
        """Update rate limiter from response headers."""
        if self.rate_limiter is None:
            return
        headers = {
            "x-rate-limit-remaining": response.headers.get("x-rate-limit-remaining"),
            "x-rate-limit-reset": response.headers.get("x-rate-limit-reset"),
        }
        # Only update if headers are present
        if any(v is not None for v in headers.values()):
            self.rate_limiter.update_from_headers(
                {k: v for k, v in headers.items() if v is not None}
            )

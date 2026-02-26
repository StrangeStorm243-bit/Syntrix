"""Twitter connector using twikit (internal API, no API key needed)."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from signalops.connectors.base import Connector, RawPost

logger = logging.getLogger(__name__)


class TwikitConnector(Connector):
    """Connector using twikit to access Twitter's internal GraphQL API.

    Requires Twitter username and password. No API key needed.
    Uses session cookies for authentication (cached to avoid repeated logins).
    """

    def __init__(
        self,
        username: str,
        password: str,
        email: str | None = None,
        cookie_path: str | None = None,
    ) -> None:
        self._username = username
        self._password = password
        self._email = email
        self._cookie_path = cookie_path or ".twikit_cookies.json"
        self._client: Any = None
        self._logged_in = False

    def _ensure_client(self) -> Any:
        """Lazy-initialize twikit client and login."""
        if self._client is not None and self._logged_in:
            return self._client

        from twikit import Client

        self._client = Client("en-US")

        # Try loading saved cookies first
        try:
            self._client.load_cookies(self._cookie_path)
            self._logged_in = True
            logger.info("Loaded saved twikit session cookies")
            return self._client
        except Exception:  # noqa: BLE001
            pass

        # Login with credentials
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(
                self._client.login(
                    auth_info_1=self._username,
                    auth_info_2=self._email or self._username,
                    password=self._password,
                )
            )
            self._client.save_cookies(self._cookie_path)
            self._logged_in = True
            logger.info("Logged in to Twitter via twikit")
        finally:
            loop.close()

        return self._client

    def search(
        self,
        query: str,
        since_id: str | None = None,
        max_results: int = 100,
    ) -> list[RawPost]:
        """Search tweets using twikit."""
        client = self._ensure_client()
        loop = asyncio.new_event_loop()
        try:
            search_query = query
            if since_id:
                search_query = f"{query} since_id:{since_id}"
            tweets = loop.run_until_complete(
                client.search_tweet(search_query, product="Latest", count=max_results)
            )
        finally:
            loop.close()

        results: list[RawPost] = []
        for tweet in tweets:
            try:
                raw_post = self._tweet_to_raw_post(tweet)
                results.append(raw_post)
            except Exception:  # noqa: BLE001
                logger.warning("Failed to parse tweet %s", getattr(tweet, "id", "?"))
                continue

        return results

    def get_user(self, user_id: str) -> dict[str, Any]:
        """Get user profile by ID."""
        client = self._ensure_client()
        loop = asyncio.new_event_loop()
        try:
            user = loop.run_until_complete(client.get_user_by_id(user_id))
        finally:
            loop.close()
        return {
            "id": user.id,
            "username": user.screen_name,
            "display_name": user.name,
            "followers": user.followers_count,
            "verified": user.verified,
        }

    def post_reply(self, in_reply_to_id: str, text: str) -> str:
        """Post a reply to a tweet."""
        client = self._ensure_client()
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                client.create_tweet(text=text, reply_to=in_reply_to_id)
            )
        finally:
            loop.close()
        return str(result.id)

    def like(self, post_id: str) -> bool:
        """Like a tweet."""
        client = self._ensure_client()
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(client.favorite_tweet(post_id))
            return True
        except Exception:  # noqa: BLE001
            logger.warning("Failed to like tweet %s", post_id)
            return False
        finally:
            loop.close()

    def follow(self, user_id: str) -> bool:
        """Follow a user."""
        client = self._ensure_client()
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(client.follow_user(user_id))
            return True
        except Exception:  # noqa: BLE001
            logger.warning("Failed to follow user %s", user_id)
            return False
        finally:
            loop.close()

    def health_check(self) -> bool:
        """Check if we have a valid session."""
        return self._logged_in

    @staticmethod
    def _tweet_to_raw_post(tweet: Any) -> RawPost:
        """Convert a twikit Tweet object to a RawPost."""
        user = tweet.user
        created_at: datetime
        if isinstance(tweet.created_at, str):
            created_at = datetime.strptime(tweet.created_at, "%a %b %d %H:%M:%S %z %Y")
        else:
            created_at = tweet.created_at

        if created_at.tzinfo is not None:
            created_at = created_at.astimezone(UTC)
        else:
            created_at = created_at.replace(tzinfo=UTC)

        return RawPost(
            platform="x",
            platform_id=str(tweet.id),
            author_id=str(user.id),
            author_username=user.screen_name,
            author_display_name=user.name,
            author_followers=getattr(user, "followers_count", 0),
            author_verified=getattr(user, "verified", False),
            text=tweet.text,
            created_at=created_at,
            language=getattr(tweet, "lang", "en"),
            reply_to_id=getattr(tweet, "reply_to", None),
            conversation_id=getattr(tweet, "conversation_id", None),
            metrics={
                "likes": getattr(tweet, "favorite_count", 0),
                "retweets": getattr(tweet, "retweet_count", 0),
                "replies": getattr(tweet, "reply_count", 0),
                "views": getattr(tweet, "view_count", 0),
            },
            entities={
                "hashtags": [h.get("text", "") for h in (getattr(tweet, "hashtags", None) or [])],
                "mentions": [
                    m.get("screen_name", "") for m in (getattr(tweet, "mentions", None) or [])
                ],
                "urls": [u.get("expanded_url", "") for u in (getattr(tweet, "urls", None) or [])],
            },
            raw_json={"twikit_id": str(tweet.id)},
        )

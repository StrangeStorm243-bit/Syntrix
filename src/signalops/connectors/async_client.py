"""Async HTTP client wrapper for concurrent API calls."""

from __future__ import annotations

from typing import Any

import httpx


class AsyncXClient:
    """Async wrapper around X API v2 for concurrent search queries."""

    def __init__(
        self,
        bearer_token: str,
        base_url: str = "https://api.twitter.com/2",
        timeout: float = 30.0,
    ) -> None:
        self._bearer_token = bearer_token
        self._base_url = base_url
        self._timeout = timeout

    async def search_recent(
        self,
        query: str,
        max_results: int = 100,
        since_id: str | None = None,
        tweet_fields: str = "created_at,public_metrics,entities,lang,conversation_id",
        user_fields: str = "name,username,public_metrics,verified,description",
        expansions: str = "author_id",
    ) -> dict[str, Any]:
        """Search recent tweets. Returns raw API response dict."""
        params: dict[str, str | int] = {
            "query": query,
            "max_results": max_results,
            "tweet.fields": tweet_fields,
            "user.fields": user_fields,
            "expansions": expansions,
        }
        if since_id:
            params["since_id"] = since_id

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(
                f"{self._base_url}/tweets/search/recent",
                params=params,
                headers={"Authorization": f"Bearer {self._bearer_token}"},
            )
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]

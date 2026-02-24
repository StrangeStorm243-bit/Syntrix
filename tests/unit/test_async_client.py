"""Tests for async X API client."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from signalops.connectors.async_client import AsyncXClient


@pytest.mark.asyncio
async def test_search_recent_basic() -> None:
    """Basic search returns parsed JSON."""
    mock_response = {
        "data": [{"id": "123", "text": "hello"}],
        "includes": {"users": [{"id": "u1", "username": "test"}]},
    }
    with respx.mock:
        respx.get("https://api.twitter.com/2/tweets/search/recent").mock(
            return_value=Response(200, json=mock_response)
        )
        client = AsyncXClient(bearer_token="test-token")
        result = await client.search_recent(query="test query")

    assert result["data"][0]["id"] == "123"
    assert len(result["includes"]["users"]) == 1


@pytest.mark.asyncio
async def test_search_recent_with_since_id() -> None:
    """since_id is passed as query parameter."""
    with respx.mock:
        route = respx.get("https://api.twitter.com/2/tweets/search/recent").mock(
            return_value=Response(200, json={"data": []})
        )
        client = AsyncXClient(bearer_token="test-token")
        await client.search_recent(query="test", since_id="999")

    assert route.called
    request = route.calls[0].request
    assert "since_id=999" in str(request.url)


@pytest.mark.asyncio
async def test_search_recent_auth_header() -> None:
    """Bearer token is sent in Authorization header."""
    with respx.mock:
        route = respx.get("https://api.twitter.com/2/tweets/search/recent").mock(
            return_value=Response(200, json={"data": []})
        )
        client = AsyncXClient(bearer_token="my-secret-token")
        await client.search_recent(query="test")

    request = route.calls[0].request
    assert request.headers["authorization"] == "Bearer my-secret-token"


@pytest.mark.asyncio
async def test_search_recent_raises_on_error() -> None:
    """HTTP errors are raised."""
    with respx.mock:
        respx.get("https://api.twitter.com/2/tweets/search/recent").mock(
            return_value=Response(429, json={"detail": "Too Many Requests"})
        )
        client = AsyncXClient(bearer_token="test-token")
        with pytest.raises(Exception):
            await client.search_recent(query="test")

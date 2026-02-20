"""Tests for XConnector retry and error mapping logic."""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest
import respx

from signalops.connectors.x_api import XConnector
from signalops.exceptions import APIError, AuthenticationError, RateLimitError


@pytest.fixture
def connector() -> XConnector:
    return XConnector(bearer_token="test-token")


class TestRaiseForStatus:
    def test_200_passes(self, connector: XConnector) -> None:
        response = httpx.Response(200, request=httpx.Request("GET", "http://test"))
        connector._raise_for_status(response)  # should not raise

    def test_429_raises_rate_limit(self, connector: XConnector) -> None:
        response = httpx.Response(
            429,
            headers={"retry-after": "30"},
            request=httpx.Request("GET", "http://test"),
        )
        with pytest.raises(RateLimitError) as exc_info:
            connector._raise_for_status(response)
        assert exc_info.value.retry_after == 30.0
        assert exc_info.value.retryable is True

    def test_401_raises_auth_error(self, connector: XConnector) -> None:
        response = httpx.Response(401, request=httpx.Request("GET", "http://test"))
        with pytest.raises(AuthenticationError):
            connector._raise_for_status(response)

    def test_403_raises_auth_error(self, connector: XConnector) -> None:
        response = httpx.Response(403, request=httpx.Request("GET", "http://test"))
        with pytest.raises(AuthenticationError):
            connector._raise_for_status(response)

    def test_500_raises_retryable(self, connector: XConnector) -> None:
        response = httpx.Response(500, request=httpx.Request("GET", "http://test"))
        with pytest.raises(APIError) as exc_info:
            connector._raise_for_status(response)
        assert exc_info.value.retryable is True
        assert exc_info.value.status_code == 500

    def test_400_raises_non_retryable(self, connector: XConnector) -> None:
        response = httpx.Response(400, request=httpx.Request("GET", "http://test"))
        with pytest.raises(APIError) as exc_info:
            connector._raise_for_status(response)
        assert exc_info.value.retryable is False


class TestSearchRetry:
    @patch("signalops.exceptions.time.sleep")
    @respx.mock
    def test_retries_on_500_then_succeeds(self, mock_sleep: object, connector: XConnector) -> None:
        route = respx.get("https://api.x.com/2/tweets/search/recent")
        route.side_effect = [
            httpx.Response(500, request=httpx.Request("GET", "http://test")),
            httpx.Response(
                200,
                json={"data": [], "meta": {"result_count": 0}},
                request=httpx.Request("GET", "http://test"),
            ),
        ]

        result = connector.search("test query")
        assert result == []
        assert route.call_count == 2

    @patch("signalops.exceptions.time.sleep")
    @respx.mock
    def test_raises_auth_error_no_retry(self, mock_sleep: object, connector: XConnector) -> None:
        route = respx.get("https://api.x.com/2/tweets/search/recent")
        route.side_effect = [
            httpx.Response(401, request=httpx.Request("GET", "http://test")),
        ]

        with pytest.raises(AuthenticationError):
            connector.search("test query")
        assert route.call_count == 1


class TestPostReplyRetry:
    @patch("signalops.exceptions.time.sleep")
    @respx.mock
    def test_retries_on_502(self, mock_sleep: object) -> None:
        conn = XConnector(bearer_token="test", user_token="user-tok")

        route = respx.post("https://api.x.com/2/tweets")
        route.side_effect = [
            httpx.Response(502, request=httpx.Request("POST", "http://test")),
            httpx.Response(
                200,
                json={"data": {"id": "12345"}},
                request=httpx.Request("POST", "http://test"),
            ),
        ]

        result = conn.post_reply("orig-123", "Hello!")
        assert result == "12345"
        assert route.call_count == 2

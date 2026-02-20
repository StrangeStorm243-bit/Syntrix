"""Tests for XConnector.get_tweet_metrics() engagement polling."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from signalops.connectors.x_api import XConnector


@pytest.fixture
def connector() -> XConnector:
    """XConnector with a fake bearer token and no rate limiter."""
    return XConnector(bearer_token="test-bearer-token")


def _mock_response(
    data: list[dict] | None = None,
    errors: list[dict] | None = None,
    status_code: int = 200,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    """Build a fake httpx.Response for tweet lookup."""
    body: dict = {}
    if data is not None:
        body["data"] = data
    if errors is not None:
        body["errors"] = errors
    resp = httpx.Response(
        status_code=status_code,
        json=body,
        headers=headers or {},
        request=httpx.Request("GET", "https://api.x.com/2/tweets"),
    )
    return resp


class TestSingleTweet:
    def test_single_tweet_metrics(self, connector: XConnector) -> None:
        resp = _mock_response(
            data=[
                {
                    "id": "111",
                    "public_metrics": {
                        "like_count": 10,
                        "retweet_count": 3,
                        "reply_count": 2,
                        "impression_count": 500,
                    },
                }
            ]
        )
        with patch.object(connector._client, "get", return_value=resp):
            result = connector.get_tweet_metrics(["111"])

        assert result == {"111": {"likes": 10, "retweets": 3, "replies": 2, "views": 500}}

    def test_empty_list_returns_empty(self, connector: XConnector) -> None:
        result = connector.get_tweet_metrics([])
        assert result == {}


class TestBatching:
    def test_batches_over_100_ids(self, connector: XConnector) -> None:
        """IDs > 100 should split into multiple requests."""
        ids = [str(i) for i in range(150)]

        batch1_data = [
            {
                "id": str(i),
                "public_metrics": {
                    "like_count": 1,
                    "retweet_count": 0,
                    "reply_count": 0,
                    "impression_count": 10,
                },
            }
            for i in range(100)
        ]
        batch2_data = [
            {
                "id": str(i),
                "public_metrics": {
                    "like_count": 2,
                    "retweet_count": 0,
                    "reply_count": 0,
                    "impression_count": 20,
                },
            }
            for i in range(100, 150)
        ]

        call_count = 0

        def mock_get(url: str, params: dict | None = None, **kwargs: object) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _mock_response(data=batch1_data)
            return _mock_response(data=batch2_data)

        with patch.object(connector._client, "get", side_effect=mock_get):
            result = connector.get_tweet_metrics(ids)

        assert call_count == 2
        assert len(result) == 150
        # First batch has likes=1, second has likes=2
        assert result["0"]["likes"] == 1
        assert result["100"]["likes"] == 2

    def test_exactly_100_ids_single_request(self, connector: XConnector) -> None:
        ids = [str(i) for i in range(100)]
        data = [
            {
                "id": str(i),
                "public_metrics": {
                    "like_count": 1,
                    "retweet_count": 0,
                    "reply_count": 0,
                    "impression_count": 0,
                },
            }
            for i in range(100)
        ]
        resp = _mock_response(data=data)
        with patch.object(connector._client, "get", return_value=resp):
            result = connector.get_tweet_metrics(ids)
        assert len(result) == 100


class TestDeletedTweets:
    def test_deleted_tweets_return_zeros(self, connector: XConnector) -> None:
        resp = _mock_response(
            data=[
                {
                    "id": "111",
                    "public_metrics": {
                        "like_count": 5,
                        "retweet_count": 1,
                        "reply_count": 0,
                        "impression_count": 100,
                    },
                },
            ],
            errors=[
                {
                    "resource_id": "222",
                    "detail": "Not found",
                    "type": "https://api.twitter.com/2/problems/resource-not-found",
                },
            ],
        )
        with patch.object(connector._client, "get", return_value=resp):
            result = connector.get_tweet_metrics(["111", "222"])

        assert result["111"]["likes"] == 5
        assert result["222"] == {"likes": 0, "retweets": 0, "replies": 0, "views": 0}

    def test_all_deleted(self, connector: XConnector) -> None:
        resp = _mock_response(
            errors=[
                {"resource_id": "111", "detail": "Not found"},
                {"resource_id": "222", "detail": "Not found"},
            ],
        )
        with patch.object(connector._client, "get", return_value=resp):
            result = connector.get_tweet_metrics(["111", "222"])

        assert len(result) == 2
        assert all(m["likes"] == 0 for m in result.values())


class TestRateLimit:
    def test_rate_limit_returns_partial(self, connector: XConnector) -> None:
        """On 429, return whatever we have so far."""
        ids = [str(i) for i in range(200)]

        call_count = 0

        def mock_get(url: str, params: dict | None = None, **kwargs: object) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _mock_response(
                    data=[
                        {
                            "id": str(i),
                            "public_metrics": {
                                "like_count": 1,
                                "retweet_count": 0,
                                "reply_count": 0,
                                "impression_count": 0,
                            },
                        }
                        for i in range(100)
                    ]
                )
            # Second batch hits rate limit
            return _mock_response(status_code=429)

        with patch.object(connector._client, "get", side_effect=mock_get):
            result = connector.get_tweet_metrics(ids)

        # Should have first batch only
        assert len(result) == 100
        assert call_count == 2

    def test_respects_rate_limiter(self) -> None:
        """Rate limiter acquire() should be called before each request."""
        rl = MagicMock()
        rl.acquire.return_value = 0.0
        connector = XConnector(bearer_token="test", rate_limiter=rl)

        resp = _mock_response(
            data=[
                {
                    "id": "1",
                    "public_metrics": {
                        "like_count": 0,
                        "retweet_count": 0,
                        "reply_count": 0,
                        "impression_count": 0,
                    },
                }
            ]
        )
        with patch.object(connector._client, "get", return_value=resp):
            connector.get_tweet_metrics(["1"])

        rl.acquire.assert_called()


class TestErrorHandling:
    def test_api_error_raises(self, connector: XConnector) -> None:
        resp = _mock_response(status_code=500)
        with patch.object(connector._client, "get", return_value=resp):
            with pytest.raises(httpx.HTTPStatusError):
                connector.get_tweet_metrics(["111"])

    def test_missing_public_metrics_defaults_to_zero(self, connector: XConnector) -> None:
        """If a tweet has no public_metrics, default to zeros."""
        resp = _mock_response(data=[{"id": "111"}])
        with patch.object(connector._client, "get", return_value=resp):
            result = connector.get_tweet_metrics(["111"])

        assert result["111"] == {"likes": 0, "retweets": 0, "replies": 0, "views": 0}

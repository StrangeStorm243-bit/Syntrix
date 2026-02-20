"""Tests for the Filtered Stream connector."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from signalops.connectors.x_stream import (
    StreamConnector,
    StreamTierError,
)


@pytest.fixture
def connector() -> StreamConnector:
    return StreamConnector(bearer_token="test-bearer-token")


def _mock_response(
    data: dict | list | None = None,
    status_code: int = 200,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    body = data if data is not None else {}
    return httpx.Response(
        status_code=status_code,
        json=body,
        headers=headers or {},
        request=httpx.Request("GET", "https://api.x.com/2/tweets/search/stream"),
    )


def _make_stream_line(
    tweet_id: str = "111",
    text: str = "Hello world",
    author_id: str = "user_1",
) -> str:
    """Build a JSON line as the stream would emit."""
    return json.dumps(
        {
            "data": {
                "id": tweet_id,
                "text": text,
                "author_id": author_id,
                "created_at": "2026-02-20T12:00:00.000Z",
                "public_metrics": {
                    "like_count": 5,
                    "retweet_count": 1,
                    "reply_count": 0,
                    "impression_count": 100,
                },
                "entities": {},
                "conversation_id": tweet_id,
                "lang": "en",
            },
            "includes": {
                "users": [
                    {
                        "id": author_id,
                        "username": "testuser",
                        "name": "Test User",
                        "public_metrics": {"followers_count": 500},
                        "verified": False,
                    }
                ]
            },
        }
    )


class TestCheckTier:
    def test_pro_tier_returns_true(self, connector: StreamConnector) -> None:
        resp = _mock_response(data={"data": []})
        with patch.object(connector._client, "get", return_value=resp):
            assert connector.check_tier() is True

    def test_non_pro_tier_raises(self, connector: StreamConnector) -> None:
        resp = _mock_response(status_code=403)
        with patch.object(connector._client, "get", return_value=resp):
            with pytest.raises(StreamTierError, match="Pro tier"):
                connector.check_tier()


class TestRuleManagement:
    def test_add_rules(self, connector: StreamConnector) -> None:
        resp = _mock_response(
            data={
                "data": [
                    {"id": "rule_1", "value": "python"},
                    {"id": "rule_2", "value": "rust"},
                ]
            }
        )
        with patch.object(connector._client, "post", return_value=resp):
            ids = connector.add_rules(["python", "rust"])
        assert ids == ["rule_1", "rule_2"]

    def test_add_empty_rules(self, connector: StreamConnector) -> None:
        ids = connector.add_rules([])
        assert ids == []

    def test_delete_rules(self, connector: StreamConnector) -> None:
        resp = _mock_response(data={"meta": {"summary": {"deleted": 2}}})
        with patch.object(connector._client, "post", return_value=resp):
            connector.delete_rules(["rule_1", "rule_2"])

    def test_delete_empty_rules(self, connector: StreamConnector) -> None:
        # Should not make any request
        connector.delete_rules([])

    def test_get_rules(self, connector: StreamConnector) -> None:
        resp = _mock_response(
            data={
                "data": [
                    {"id": "rule_1", "value": "python"},
                    {"id": "rule_2", "value": "rust"},
                ]
            }
        )
        with patch.object(connector._client, "get", return_value=resp):
            rules = connector.get_rules()
        assert len(rules) == 2
        assert rules[0] == {"id": "rule_1", "value": "python"}

    def test_get_rules_empty(self, connector: StreamConnector) -> None:
        resp = _mock_response(data={})
        with patch.object(connector._client, "get", return_value=resp):
            rules = connector.get_rules()
        assert rules == []


class TestStreamParsing:
    def test_parse_stream_tweet(self, connector: StreamConnector) -> None:
        line = _make_stream_line(tweet_id="t1", text="Hello")
        data = json.loads(line)
        post = connector._parse_stream_tweet(data)
        assert post is not None
        assert post.platform_id == "t1"
        assert post.text == "Hello"
        assert post.platform == "x"
        assert post.author_username == "testuser"
        assert post.metrics["likes"] == 5

    def test_parse_empty_data(self, connector: StreamConnector) -> None:
        post = connector._parse_stream_tweet({})
        assert post is None

    def test_parse_missing_includes(self, connector: StreamConnector) -> None:
        data = {
            "data": {
                "id": "t1",
                "text": "no user info",
                "author_id": "unknown",
                "created_at": "2026-02-20T12:00:00.000Z",
                "public_metrics": {},
                "entities": {},
            }
        }
        post = connector._parse_stream_tweet(data)
        assert post is not None
        assert post.author_username == ""


class TestStreamOnce:
    def test_processes_lines(self, connector: StreamConnector) -> None:
        """_stream_once should parse JSON lines and call callback."""
        posts_received: list[str] = []

        def callback(post: object) -> None:
            posts_received.append(getattr(post, "platform_id", ""))

        lines = [
            _make_stream_line("t1"),
            "",  # heartbeat
            _make_stream_line("t2"),
        ]

        # Build a mock streaming response
        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_stream)
        mock_stream.__exit__ = MagicMock(return_value=False)
        mock_stream.raise_for_status = MagicMock()
        mock_stream.iter_lines = MagicMock(return_value=iter(lines))

        with patch.object(connector._client, "stream", return_value=mock_stream):
            connector._stream_once(callback, backfill_minutes=5)

        assert posts_received == ["t1", "t2"]

    def test_skips_malformed_json(self, connector: StreamConnector) -> None:
        posts_received: list[str] = []

        def callback(post: object) -> None:
            posts_received.append(getattr(post, "platform_id", ""))

        lines = [
            "not valid json",
            _make_stream_line("t1"),
        ]

        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_stream)
        mock_stream.__exit__ = MagicMock(return_value=False)
        mock_stream.raise_for_status = MagicMock()
        mock_stream.iter_lines = MagicMock(return_value=iter(lines))

        with patch.object(connector._client, "stream", return_value=mock_stream):
            connector._stream_once(callback, backfill_minutes=0)

        assert posts_received == ["t1"]


class TestBackoff:
    def test_reconnects_on_disconnect(self, connector: StreamConnector) -> None:
        """Stream should reconnect on connection errors."""
        call_count = 0

        def mock_stream_once(callback: object, backfill_minutes: int) -> None:
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise httpx.ConnectError("Connection reset")
            # Third call succeeds (no exception, clean return)

        with (
            patch.object(connector, "_stream_once", side_effect=mock_stream_once),
            patch("signalops.connectors.x_stream.time.sleep"),
        ):
            connector.stream(callback=lambda p: None, max_reconnects=5)

        assert call_count == 3

    def test_stops_after_max_reconnects(self, connector: StreamConnector) -> None:
        def mock_stream_once(callback: object, backfill_minutes: int) -> None:
            raise httpx.ConnectError("Connection refused")

        with (
            patch.object(connector, "_stream_once", side_effect=mock_stream_once),
            patch("signalops.connectors.x_stream.time.sleep"),
        ):
            connector.stream(callback=lambda p: None, max_reconnects=3)

        # Should have attempted 3 times then stopped (no error raised)

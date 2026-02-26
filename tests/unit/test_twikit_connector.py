"""Tests for TwikitConnector and twikit factory integration."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from signalops.connectors.base import Platform
from signalops.connectors.factory import ConnectorFactory
from signalops.connectors.twikit_connector import TwikitConnector


class TestTwikitConnector:
    """Test TwikitConnector search, reply, like, follow."""

    def test_search_returns_raw_posts(self) -> None:
        """search() should return list of RawPost from twikit results."""
        connector = TwikitConnector(
            username="test_user",
            password="test_pass",
        )
        mock_tweet = MagicMock()
        mock_tweet.id = "123456"
        mock_tweet.user.id = "user1"
        mock_tweet.user.name = "Test User"
        mock_tweet.user.screen_name = "testuser"
        mock_tweet.user.followers_count = 500
        mock_tweet.user.verified = False
        mock_tweet.text = "Need a better code review tool"
        mock_tweet.created_at = "Mon Feb 25 10:00:00 +0000 2026"
        mock_tweet.lang = "en"
        mock_tweet.reply_to = None
        mock_tweet.conversation_id = None
        mock_tweet.favorite_count = 5
        mock_tweet.retweet_count = 2
        mock_tweet.reply_count = 1
        mock_tweet.view_count = 800
        mock_tweet.hashtags = []
        mock_tweet.mentions = []
        mock_tweet.urls = []

        # Mock _ensure_client and client.search_tweet
        mock_client = MagicMock()
        mock_client.search_tweet = AsyncMock(return_value=[mock_tweet])
        connector._client = mock_client
        connector._logged_in = True

        results = connector.search("code review")
        assert len(results) == 1
        assert results[0].platform == "x"
        assert results[0].platform_id == "123456"
        assert results[0].author_username == "testuser"
        assert results[0].author_followers == 500
        assert results[0].text == "Need a better code review tool"

    def test_search_with_since_id(self) -> None:
        """search() appends since_id to query."""
        connector = TwikitConnector(username="test", password="pass")
        mock_client = MagicMock()
        mock_client.search_tweet = AsyncMock(return_value=[])
        connector._client = mock_client
        connector._logged_in = True

        connector.search("test query", since_id="99999")
        call_args = mock_client.search_tweet.call_args
        assert "since_id:99999" in call_args[0][0]

    def test_post_reply(self) -> None:
        """post_reply() creates a tweet and returns its ID."""
        connector = TwikitConnector(username="test", password="pass")
        mock_result = MagicMock()
        mock_result.id = "new_tweet_789"
        mock_client = MagicMock()
        mock_client.create_tweet = AsyncMock(return_value=mock_result)
        connector._client = mock_client
        connector._logged_in = True

        reply_id = connector.post_reply("original_123", "Great tweet!")
        assert reply_id == "new_tweet_789"
        mock_client.create_tweet.assert_called_once_with(
            text="Great tweet!", reply_to="original_123"
        )

    def test_like(self) -> None:
        """like() calls favorite_tweet and returns True."""
        connector = TwikitConnector(username="test", password="pass")
        mock_client = MagicMock()
        mock_client.favorite_tweet = AsyncMock(return_value=None)
        connector._client = mock_client
        connector._logged_in = True

        assert connector.like("tweet_123") is True
        mock_client.favorite_tweet.assert_called_once_with("tweet_123")

    def test_like_failure_returns_false(self) -> None:
        """like() returns False on failure."""
        connector = TwikitConnector(username="test", password="pass")
        mock_client = MagicMock()
        mock_client.favorite_tweet = AsyncMock(side_effect=Exception("API error"))
        connector._client = mock_client
        connector._logged_in = True

        assert connector.like("tweet_123") is False

    def test_follow(self) -> None:
        """follow() calls follow_user and returns True."""
        connector = TwikitConnector(username="test", password="pass")
        mock_client = MagicMock()
        mock_client.follow_user = AsyncMock(return_value=None)
        connector._client = mock_client
        connector._logged_in = True

        assert connector.follow("user_456") is True
        mock_client.follow_user.assert_called_once_with("user_456")

    def test_follow_failure_returns_false(self) -> None:
        """follow() returns False on failure."""
        connector = TwikitConnector(username="test", password="pass")
        mock_client = MagicMock()
        mock_client.follow_user = AsyncMock(side_effect=Exception("API error"))
        connector._client = mock_client
        connector._logged_in = True

        assert connector.follow("user_456") is False

    def test_get_user(self) -> None:
        """get_user() fetches user profile by ID."""
        connector = TwikitConnector(username="test", password="pass")
        mock_user = MagicMock()
        mock_user.id = "user1"
        mock_user.screen_name = "testuser"
        mock_user.name = "Test User"
        mock_user.followers_count = 1000
        mock_user.verified = True
        mock_client = MagicMock()
        mock_client.get_user_by_id = AsyncMock(return_value=mock_user)
        connector._client = mock_client
        connector._logged_in = True

        result = connector.get_user("user1")
        assert result["id"] == "user1"
        assert result["username"] == "testuser"
        assert result["followers"] == 1000
        assert result["verified"] is True

    def test_health_check_with_valid_session(self) -> None:
        """health_check() returns True when logged in."""
        connector = TwikitConnector(username="test", password="pass")
        connector._logged_in = True
        assert connector.health_check() is True

    def test_health_check_without_session(self) -> None:
        """health_check() returns False when not logged in."""
        connector = TwikitConnector(username="test", password="pass")
        assert connector.health_check() is False

    def test_tweet_to_raw_post_with_datetime_object(self) -> None:
        """_tweet_to_raw_post handles datetime objects."""
        TwikitConnector(username="test", password="pass")
        mock_tweet = MagicMock()
        mock_tweet.id = "111"
        mock_tweet.user.id = "u1"
        mock_tweet.user.screen_name = "user1"
        mock_tweet.user.name = "User One"
        mock_tweet.user.followers_count = 100
        mock_tweet.user.verified = False
        mock_tweet.text = "Hello world"
        mock_tweet.created_at = datetime(2026, 2, 25, tzinfo=UTC)
        mock_tweet.lang = "en"
        mock_tweet.reply_to = None
        mock_tweet.conversation_id = None
        mock_tweet.favorite_count = 0
        mock_tweet.retweet_count = 0
        mock_tweet.reply_count = 0
        mock_tweet.view_count = 0
        mock_tweet.hashtags = None
        mock_tweet.mentions = None
        mock_tweet.urls = None

        raw_post = TwikitConnector._tweet_to_raw_post(mock_tweet)
        assert raw_post.platform_id == "111"
        assert raw_post.created_at.year == 2026

    def test_ensure_client_cookie_load(self) -> None:
        """_ensure_client tries cookies first before login."""
        connector = TwikitConnector(username="test", password="pass")
        with patch.dict("sys.modules", {"twikit": MagicMock()}):
            import sys

            mock_client_cls = MagicMock()
            mock_instance = MagicMock()
            mock_client_cls.return_value = mock_instance
            mock_instance.load_cookies.return_value = None  # Success
            sys.modules["twikit"].Client = mock_client_cls

            connector._ensure_client()
            assert connector._logged_in is True
            mock_instance.load_cookies.assert_called_once()

    def test_ensure_client_login_on_cookie_fail(self) -> None:
        """_ensure_client falls back to login when cookies fail."""
        connector = TwikitConnector(username="test", password="pass", email="test@example.com")
        with patch.dict("sys.modules", {"twikit": MagicMock()}):
            import sys

            mock_client_cls = MagicMock()
            mock_instance = MagicMock()
            mock_client_cls.return_value = mock_instance
            mock_instance.load_cookies.side_effect = Exception("No cookies")
            mock_instance.login = AsyncMock(return_value=None)
            sys.modules["twikit"].Client = mock_client_cls

            connector._ensure_client()
            assert connector._logged_in is True
            mock_instance.login.assert_called_once_with(
                auth_info_1="test",
                auth_info_2="test@example.com",
                password="pass",
            )
            mock_instance.save_cookies.assert_called_once()


class TestTwikitFactory:
    """Test ConnectorFactory twikit preference."""

    def setup_method(self) -> None:
        ConnectorFactory.clear_cache()

    def test_factory_prefers_twikit_when_credentials_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Factory returns TwikitConnector when TWIKIT_USERNAME/PASSWORD are set."""
        monkeypatch.setenv("TWIKIT_USERNAME", "myuser")
        monkeypatch.setenv("TWIKIT_PASSWORD", "mypass")
        connector = ConnectorFactory.create(Platform.X)
        assert isinstance(connector, TwikitConnector)

    def test_factory_falls_back_to_x_api(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Factory returns XConnector when twikit credentials not set."""
        monkeypatch.delenv("TWIKIT_USERNAME", raising=False)
        monkeypatch.delenv("TWIKIT_PASSWORD", raising=False)
        monkeypatch.setenv("X_BEARER_TOKEN", "test-token")
        connector = ConnectorFactory.create(Platform.X)
        from signalops.connectors.x_api import XConnector

        assert isinstance(connector, XConnector)

    def test_factory_twikit_with_optional_email(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Factory passes email and cookie_path from env."""
        monkeypatch.setenv("TWIKIT_USERNAME", "myuser")
        monkeypatch.setenv("TWIKIT_PASSWORD", "mypass")
        monkeypatch.setenv("TWIKIT_EMAIL", "my@email.com")
        monkeypatch.setenv("TWIKIT_COOKIE_PATH", "/tmp/cookies.json")
        connector = ConnectorFactory.create(Platform.X)
        assert isinstance(connector, TwikitConnector)
        assert connector._email == "my@email.com"  # type: ignore[attr-defined]
        assert connector._cookie_path == "/tmp/cookies.json"  # type: ignore[attr-defined]

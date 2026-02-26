"""Contract tests for the Connector interface.

Any connector implementation should pass these tests.
"""

from __future__ import annotations

import pytest

from signalops.connectors.base import Connector


class ConnectorContractTests:
    """Mixin for connector contract tests. Subclass and set self.connector."""

    connector: Connector

    def test_search_returns_list(self) -> None:
        """search() must return a list."""
        result = self.connector.search("test query")
        assert isinstance(result, list)

    def test_search_with_max_results(self) -> None:
        """search() respects max_results parameter."""
        result = self.connector.search("test", max_results=5)
        assert len(result) <= 5

    def test_get_user_returns_dict(self) -> None:
        """get_user() must return a dict."""
        result = self.connector.get_user("test_id")
        assert isinstance(result, dict)

    def test_health_check_returns_bool(self) -> None:
        """health_check() must return a boolean."""
        result = self.connector.health_check()
        assert isinstance(result, bool)


class TestLinkedInConnectorContract(ConnectorContractTests):
    """Run contract tests against LinkedIn stubbed connector."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        from signalops.connectors.linkedin import LinkedInConnector

        self.connector = LinkedInConnector()  # Stubbed mode

    def test_search_returns_empty_when_stubbed(self) -> None:
        """Stubbed connector returns empty list, not error."""
        result = self.connector.search("test")
        assert result == []

    def test_get_user_returns_stubbed_data(self) -> None:
        """Stubbed connector returns placeholder user data."""
        result = self.connector.get_user("urn:li:person:123")
        assert result["_stubbed"] is True
        assert result["platform"] == "linkedin"

    def test_post_reply_raises_not_implemented(self) -> None:
        """LinkedIn post_reply always raises — read-only platform."""
        with pytest.raises(NotImplementedError, match="read-only"):
            self.connector.post_reply("urn:li:share:123", "test reply")

    def test_like_raises_not_implemented(self) -> None:
        """LinkedIn like always raises — read-only platform."""
        with pytest.raises(NotImplementedError, match="read-only"):
            self.connector.like("urn:li:share:123")

    def test_follow_raises_not_implemented(self) -> None:
        """LinkedIn follow always raises — read-only platform."""
        with pytest.raises(NotImplementedError, match="read-only"):
            self.connector.follow("urn:li:person:123")

    def test_health_check_returns_false_when_stubbed(self) -> None:
        """Stubbed connector reports unhealthy."""
        assert self.connector.health_check() is False


class TestLinkedInToRawPost:
    """Tests for LinkedInConnector.to_raw_post conversion."""

    def test_converts_linkedin_post_to_raw_post(self) -> None:
        from signalops.connectors.linkedin import LinkedInConnector, LinkedInPost

        connector = LinkedInConnector()
        linkedin_post = LinkedInPost(
            urn="urn:li:share:123456",
            author_urn="urn:li:person:789",
            author_name="Jane Doe",
            author_headline="CTO at TechCo",
            author_connections=500,
            author_is_premium=True,
            text="Excited about our new code review automation!",
            post_type="post",
            published_at="2026-02-20T10:00:00Z",
            reactions=42,
            comments=8,
            shares=5,
            impressions=1200,
        )

        raw = connector.to_raw_post(linkedin_post)

        assert raw.platform == "linkedin"
        assert raw.platform_id == "urn:li:share:123456"
        assert raw.author_id == "urn:li:person:789"
        assert raw.author_username == "jane-doe"
        assert raw.author_display_name == "Jane Doe"
        assert raw.author_followers == 500
        assert raw.author_verified is True
        assert raw.metrics["likes"] == 42
        assert raw.metrics["replies"] == 8
        assert raw.metrics["retweets"] == 5
        assert raw.metrics["views"] == 1200

    def test_handles_none_impressions(self) -> None:
        from signalops.connectors.linkedin import LinkedInConnector, LinkedInPost

        connector = LinkedInConnector()
        linkedin_post = LinkedInPost(
            urn="urn:li:share:999",
            author_urn="urn:li:person:111",
            author_name="John Smith",
            author_headline="Engineer",
            author_connections=100,
            author_is_premium=False,
            text="Test post",
            post_type="post",
            published_at="2026-02-20T10:00:00Z",
            reactions=0,
            comments=0,
            shares=0,
            impressions=None,
        )

        raw = connector.to_raw_post(linkedin_post)
        assert raw.metrics["views"] == 0

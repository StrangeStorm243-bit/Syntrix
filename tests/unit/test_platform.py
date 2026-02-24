"""Tests for Platform enum and validation."""

from __future__ import annotations

import pytest

from signalops.connectors.base import Platform


class TestPlatform:
    def test_from_string_valid(self) -> None:
        assert Platform.from_string("x") == Platform.X
        assert Platform.from_string("linkedin") == Platform.LINKEDIN
        assert Platform.from_string("socialdata") == Platform.SOCIALDATA

    def test_from_string_case_insensitive(self) -> None:
        assert Platform.from_string("X") == Platform.X
        assert Platform.from_string("LinkedIn") == Platform.LINKEDIN
        assert Platform.from_string("SOCIALDATA") == Platform.SOCIALDATA

    def test_from_string_invalid(self) -> None:
        with pytest.raises(ValueError, match="Unknown platform"):
            Platform.from_string("tiktok")

    def test_from_string_empty(self) -> None:
        with pytest.raises(ValueError, match="Unknown platform"):
            Platform.from_string("")

    def test_all_platforms_have_lowercase_values(self) -> None:
        """Every platform has a lowercase string value."""
        for p in Platform:
            assert p.value == p.value.lower()

    def test_platform_values_are_unique(self) -> None:
        """No duplicate values."""
        values = [p.value for p in Platform]
        assert len(values) == len(set(values))


class TestRawPostPlatformValidation:
    def test_valid_platform_accepted(self) -> None:
        from datetime import UTC, datetime

        from signalops.connectors.base import RawPost

        post = RawPost(
            platform="x",
            platform_id="123",
            author_id="456",
            author_username="test",
            author_display_name="Test",
            author_followers=100,
            author_verified=False,
            text="hello",
            created_at=datetime.now(UTC),
            language="en",
            reply_to_id=None,
            conversation_id=None,
        )
        assert post.platform == "x"

    def test_invalid_platform_rejected(self) -> None:
        from datetime import UTC, datetime

        from signalops.connectors.base import RawPost

        with pytest.raises(ValueError, match="Unknown platform"):
            RawPost(
                platform="tiktok",
                platform_id="123",
                author_id="456",
                author_username="test",
                author_display_name="Test",
                author_followers=100,
                author_verified=False,
                text="hello",
                created_at=datetime.now(UTC),
                language="en",
                reply_to_id=None,
                conversation_id=None,
            )

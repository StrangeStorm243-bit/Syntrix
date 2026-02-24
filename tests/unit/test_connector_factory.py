"""Tests for ConnectorFactory."""

from __future__ import annotations

import pytest

from signalops.connectors.base import Platform
from signalops.connectors.factory import ConnectorFactory


class TestConnectorFactory:
    def setup_method(self) -> None:
        ConnectorFactory.clear_cache()

    def test_create_x_connector(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Factory creates XConnector when bearer token is available."""
        monkeypatch.setenv("X_BEARER_TOKEN", "test-token")
        connector = ConnectorFactory.create(Platform.X)
        from signalops.connectors.x_api import XConnector

        assert isinstance(connector, XConnector)

    def test_create_x_without_token_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Factory raises when X bearer token is missing."""
        monkeypatch.delenv("X_BEARER_TOKEN", raising=False)
        with pytest.raises(ValueError, match="X_BEARER_TOKEN"):
            ConnectorFactory.create(Platform.X)

    def test_create_linkedin_connector(self) -> None:
        """Factory creates LinkedInConnector (stubbed mode)."""
        connector = ConnectorFactory.create(Platform.LINKEDIN)
        from signalops.connectors.linkedin import LinkedInConnector

        assert isinstance(connector, LinkedInConnector)

    def test_create_from_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Factory accepts string platform names."""
        monkeypatch.setenv("X_BEARER_TOKEN", "test-token")
        connector = ConnectorFactory.create("x")
        assert connector is not None

    def test_create_unknown_platform_raises(self) -> None:
        """Factory raises for unknown platforms."""
        with pytest.raises(ValueError, match="Unknown platform"):
            ConnectorFactory.create("tiktok")

    def test_cache_returns_same_instance(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Factory caches connector instances."""
        monkeypatch.setenv("X_BEARER_TOKEN", "test-token")
        c1 = ConnectorFactory.create(Platform.X)
        c2 = ConnectorFactory.create(Platform.X)
        assert c1 is c2

    def test_clear_cache(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """clear_cache removes cached instances."""
        monkeypatch.setenv("X_BEARER_TOKEN", "test-token")
        c1 = ConnectorFactory.create(Platform.X)
        ConnectorFactory.clear_cache()
        c2 = ConnectorFactory.create(Platform.X)
        assert c1 is not c2

    def test_create_all_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """create_all with default platforms config returns X only (linkedin disabled)."""
        monkeypatch.setenv("X_BEARER_TOKEN", "test-token")
        from signalops.config.schema import (
            PersonaConfig,
            ProjectConfig,
            QueryConfig,
            RelevanceRubric,
        )

        config = ProjectConfig(
            project_id="test",
            project_name="Test",
            description="Test project",
            queries=[QueryConfig(text="test", label="test")],
            relevance=RelevanceRubric(
                system_prompt="test",
                positive_signals=["test"],
                negative_signals=["test"],
            ),
            persona=PersonaConfig(
                name="Test",
                role="tester",
                tone="helpful",
                voice_notes="Be helpful.",
                example_reply="Sure!",
            ),
        )
        connectors = ConnectorFactory.create_all(config)
        assert Platform.X in connectors
        # LinkedIn disabled by default so only X + linkedin(disabled) = just X
        assert Platform.LINKEDIN not in connectors

    def test_socialdata_not_implemented(self) -> None:
        """SocialData connector raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            ConnectorFactory.create(Platform.SOCIALDATA)

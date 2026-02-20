"""Tests for the notification CLI commands."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner
from rich.console import Console

from signalops.cli.notify import notify_group
from signalops.config.schema import (
    NotificationConfig,
    PersonaConfig,
    ProjectConfig,
    QueryConfig,
    RelevanceRubric,
)


def _make_config(
    notifications: NotificationConfig | None = None,
) -> ProjectConfig:
    """Build a ProjectConfig with given notification settings."""
    return ProjectConfig(
        project_id="test-project",
        project_name="Test Project",
        description="Test",
        queries=[QueryConfig(text="test", label="test")],
        relevance=RelevanceRubric(
            system_prompt="test",
            positive_signals=["need"],
            negative_signals=["spam"],
        ),
        persona=PersonaConfig(
            name="Bot",
            role="tester",
            tone="helpful",
            voice_notes="Be brief.",
            example_reply="Hi!",
        ),
        notifications=notifications or NotificationConfig(),
    )


def _invoke(args: list[str], config: ProjectConfig) -> object:
    """Run a CLI command with mocked config loading."""
    runner = CliRunner()
    with patch("signalops.cli.notify.load_active_config", return_value=config):
        return runner.invoke(
            notify_group,
            args,
            obj={"console": Console(width=120), "format": "table"},
        )


class TestNotifyTest:
    def test_no_webhooks_shows_warning(self) -> None:
        config = _make_config(NotificationConfig(enabled=False))
        result = _invoke(["test"], config)
        assert result.exit_code == 0  # type: ignore[union-attr]
        assert "No webhooks" in result.output  # type: ignore[union-attr]

    def test_with_mocked_notifier_success(self) -> None:
        config = _make_config(
            NotificationConfig(
                enabled=True,
                discord_webhook="https://discord.com/api/webhooks/test",
            )
        )
        mock_notifier = MagicMock()
        mock_notifier.send.return_value = True

        with patch(
            "signalops.cli.notify.get_notifiers",
            return_value=[mock_notifier],
        ):
            result = _invoke(["test"], config)

        assert result.exit_code == 0  # type: ignore[union-attr]
        assert "sent" in result.output  # type: ignore[union-attr]
        mock_notifier.send.assert_called_once()

    def test_with_mocked_notifier_failure(self) -> None:
        config = _make_config(
            NotificationConfig(
                enabled=True,
                discord_webhook="https://discord.com/api/webhooks/test",
            )
        )
        mock_notifier = MagicMock()
        mock_notifier.send.return_value = False

        with patch(
            "signalops.cli.notify.get_notifiers",
            return_value=[mock_notifier],
        ):
            result = _invoke(["test"], config)

        assert result.exit_code == 0  # type: ignore[union-attr]
        assert "failed" in result.output  # type: ignore[union-attr]


class TestNotifyStatus:
    def test_status_shows_configuration(self) -> None:
        config = _make_config(
            NotificationConfig(
                enabled=True,
                min_score_to_notify=75,
                discord_webhook="https://discord.com/api/webhooks/test123",
            )
        )
        result = _invoke(["status"], config)
        assert result.exit_code == 0  # type: ignore[union-attr]
        output = result.output  # type: ignore[union-attr]
        assert "True" in output  # enabled
        assert "75" in output  # min_score_to_notify

    def test_status_unreachable_webhook(self) -> None:
        config = _make_config(
            NotificationConfig(
                enabled=True,
                discord_webhook="https://discord.com/api/webhooks/test",
            )
        )
        mock_notifier = MagicMock()
        mock_notifier.health_check.return_value = False

        with patch(
            "signalops.cli.notify.get_notifiers",
            return_value=[mock_notifier],
        ):
            result = _invoke(["status"], config)

        assert result.exit_code == 0  # type: ignore[union-attr]
        assert "unreachable" in result.output  # type: ignore[union-attr]

    def test_status_no_webhooks(self) -> None:
        config = _make_config(NotificationConfig(enabled=True))
        result = _invoke(["status"], config)
        assert result.exit_code == 0  # type: ignore[union-attr]
        assert "No active webhooks" in result.output  # type: ignore[union-attr]

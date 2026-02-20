"""Tests for the notification system (Discord, Slack, factory, dispatch)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from signalops.config.schema import NotificationConfig, ProjectConfig
from signalops.notifications.base import (
    NotificationPayload,
    Notifier,
    get_notifiers,
    notify_high_scores,
)
from signalops.notifications.discord import DiscordNotifier
from signalops.notifications.slack import SlackNotifier

# ── Payload tests ──


class TestNotificationPayload:
    def test_auto_timestamp(self) -> None:
        payload = NotificationPayload(project_name="test", lead_count=3)
        assert payload.timestamp  # auto-filled
        assert "T" in payload.timestamp  # ISO format

    def test_explicit_timestamp(self) -> None:
        payload = NotificationPayload(
            project_name="test", lead_count=1, timestamp="2026-01-01T00:00:00Z"
        )
        assert payload.timestamp == "2026-01-01T00:00:00Z"


# ── Discord tests ──


class TestDiscordNotifier:
    def test_send_success(self) -> None:
        notifier = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/test")
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_resp.text = ""

        with patch("httpx.post", return_value=mock_resp) as mock_post:
            result = notifier.send("Test Title", "Test message", {"Lead 1": "info"})

        assert result is True
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1]["json"]
        assert "embeds" in payload
        embed = payload["embeds"][0]
        assert embed["title"] == "Test Title"
        assert embed["description"] == "Test message"
        assert len(embed["fields"]) == 1

    def test_send_failure_status(self) -> None:
        notifier = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/test")
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.text = "Bad Request"

        with patch("httpx.post", return_value=mock_resp):
            result = notifier.send("Title", "Msg")

        assert result is False

    def test_send_exception_returns_false(self) -> None:
        notifier = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/test")

        with patch("httpx.post", side_effect=ConnectionError("unreachable")):
            result = notifier.send("Title", "Msg")

        assert result is False

    def test_embed_color(self) -> None:
        embed = DiscordNotifier._build_embed("Title", "Msg")
        assert embed["color"] == 0x00FF00
        assert embed["footer"]["text"] == "SignalOps Notification"

    def test_embed_fields(self) -> None:
        embed = DiscordNotifier._build_embed("Title", "Msg", {"Lead 1": "@user — score 85"})
        assert len(embed["fields"]) == 1
        assert embed["fields"][0]["name"] == "Lead 1"
        assert embed["fields"][0]["inline"] is True

    def test_health_check_success(self) -> None:
        notifier = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/test")
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch("httpx.get", return_value=mock_resp):
            assert notifier.health_check() is True

    def test_health_check_failure(self) -> None:
        notifier = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/test")

        with patch("httpx.get", side_effect=ConnectionError("down")):
            assert notifier.health_check() is False


# ── Slack tests ──


class TestSlackNotifier:
    def test_send_success(self) -> None:
        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "ok"

        with patch("httpx.post", return_value=mock_resp) as mock_post:
            result = notifier.send("Test Title", "Test message", {"Lead 1": "info"})

        assert result is True
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1]["json"]
        assert "blocks" in payload
        blocks = payload["blocks"]
        # Header block
        assert blocks[0]["type"] == "header"
        assert blocks[0]["text"]["text"] == "Test Title"

    def test_send_failure(self) -> None:
        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "server_error"

        with patch("httpx.post", return_value=mock_resp):
            result = notifier.send("Title", "Msg")

        assert result is False

    def test_send_exception_returns_false(self) -> None:
        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")

        with patch("httpx.post", side_effect=ConnectionError("unreachable")):
            result = notifier.send("Title", "Msg")

        assert result is False

    def test_blocks_structure_with_fields(self) -> None:
        blocks = SlackNotifier._build_blocks("Title", "Msg", {"Lead 1": "@user — score 85"})
        types = [b["type"] for b in blocks]
        assert types[0] == "header"
        assert "section" in types
        assert "divider" in types
        assert types[-1] == "context"

    def test_blocks_structure_without_fields(self) -> None:
        blocks = SlackNotifier._build_blocks("Title", "Msg")
        types = [b["type"] for b in blocks]
        assert types[0] == "header"
        assert "section" in types
        assert types[-1] == "context"

    def test_health_check_success(self) -> None:
        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch("httpx.post", return_value=mock_resp):
            assert notifier.health_check() is True

    def test_health_check_failure(self) -> None:
        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")

        with patch("httpx.post", side_effect=ConnectionError("down")):
            assert notifier.health_check() is False


# ── Factory tests ──


class TestGetNotifiers:
    def test_both_configured(self) -> None:
        config = NotificationConfig(
            enabled=True,
            discord_webhook="https://discord.com/api/webhooks/123",
            slack_webhook="https://hooks.slack.com/456",
        )
        notifiers = get_notifiers(config)
        assert len(notifiers) == 2
        assert isinstance(notifiers[0], DiscordNotifier)
        assert isinstance(notifiers[1], SlackNotifier)

    def test_discord_only(self) -> None:
        config = NotificationConfig(
            enabled=True,
            discord_webhook="https://discord.com/api/webhooks/123",
        )
        notifiers = get_notifiers(config)
        assert len(notifiers) == 1
        assert isinstance(notifiers[0], DiscordNotifier)

    def test_slack_only(self) -> None:
        config = NotificationConfig(
            enabled=True,
            slack_webhook="https://hooks.slack.com/456",
        )
        notifiers = get_notifiers(config)
        assert len(notifiers) == 1
        assert isinstance(notifiers[0], SlackNotifier)

    def test_disabled_returns_empty(self) -> None:
        config = NotificationConfig(
            enabled=False,
            discord_webhook="https://discord.com/api/webhooks/123",
        )
        notifiers = get_notifiers(config)
        assert notifiers == []

    def test_no_webhooks_returns_empty(self) -> None:
        config = NotificationConfig(enabled=True)
        notifiers = get_notifiers(config)
        assert notifiers == []


# ── notify_high_scores tests ──


class TestNotifyHighScores:
    @pytest.fixture()
    def project_config(self, sample_project_config: ProjectConfig) -> ProjectConfig:
        sample_project_config.notifications = NotificationConfig(
            enabled=True,
            min_score_to_notify=70,
            discord_webhook="https://discord.com/api/webhooks/test",
        )
        return sample_project_config

    def test_scores_above_threshold(self, project_config: ProjectConfig) -> None:
        scores = [
            {"author": "user1", "score": 85, "text_preview": "Need help with X"},
            {"author": "user2", "score": 60, "text_preview": "Random tweet"},
            {"author": "user3", "score": 75, "text_preview": "Looking for tools"},
        ]
        mock_notifier = MagicMock(spec=Notifier)
        mock_notifier.send.return_value = True

        result = notify_high_scores(scores, project_config, [mock_notifier])

        assert result["notified"] == 1
        assert result["failed"] == 0
        assert result["skipped"] == 1  # user2 below threshold
        mock_notifier.send.assert_called_once()

    def test_no_scores_above_threshold(self, project_config: ProjectConfig) -> None:
        scores = [
            {"author": "user1", "score": 50, "text_preview": "Low score"},
        ]
        mock_notifier = MagicMock(spec=Notifier)

        result = notify_high_scores(scores, project_config, [mock_notifier])

        assert result["notified"] == 0
        assert result["skipped"] == 1
        mock_notifier.send.assert_not_called()

    def test_notifier_failure(self, project_config: ProjectConfig) -> None:
        scores = [{"author": "user1", "score": 90, "text_preview": "Help"}]
        mock_notifier = MagicMock(spec=Notifier)
        mock_notifier.send.return_value = False

        result = notify_high_scores(scores, project_config, [mock_notifier])

        assert result["notified"] == 0
        assert result["failed"] == 1

    def test_notifier_exception(self, project_config: ProjectConfig) -> None:
        scores = [{"author": "user1", "score": 90, "text_preview": "Help"}]
        mock_notifier = MagicMock(spec=Notifier)
        mock_notifier.send.side_effect = RuntimeError("boom")

        result = notify_high_scores(scores, project_config, [mock_notifier])

        assert result["notified"] == 0
        assert result["failed"] == 1

    def test_empty_scores(self, project_config: ProjectConfig) -> None:
        mock_notifier = MagicMock(spec=Notifier)

        result = notify_high_scores([], project_config, [mock_notifier])

        assert result["notified"] == 0
        assert result["skipped"] == 0
        mock_notifier.send.assert_not_called()

    def test_multiple_notifiers(self, project_config: ProjectConfig) -> None:
        scores = [{"author": "user1", "score": 90, "text_preview": "Help"}]
        notifier1 = MagicMock(spec=Notifier)
        notifier1.send.return_value = True
        notifier2 = MagicMock(spec=Notifier)
        notifier2.send.return_value = True

        result = notify_high_scores(scores, project_config, [notifier1, notifier2])

        assert result["notified"] == 2
        assert result["failed"] == 0

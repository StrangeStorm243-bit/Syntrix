"""Tests for orchestrator notification hook."""

from __future__ import annotations

from unittest.mock import MagicMock

from signalops.config.schema import NotificationConfig
from signalops.notifications.base import Notifier
from signalops.pipeline.orchestrator import PipelineOrchestrator
from signalops.storage.database import Score


def _make_orchestrator(
    db_session,  # type: ignore[no-untyped-def]
    notifiers: list[Notifier] | None = None,
) -> PipelineOrchestrator:
    """Build a PipelineOrchestrator with mocked deps."""
    connector = MagicMock()
    judge = MagicMock()
    draft_gen = MagicMock()
    return PipelineOrchestrator(
        db_session=db_session,
        connector=connector,
        judge=judge,
        draft_generator=draft_gen,
        notifiers=notifiers,
    )


class TestOrchestratorNotifications:
    def test_notifications_fire_above_threshold(
        self,
        db_session,  # type: ignore[no-untyped-def]
        sample_project_config,  # type: ignore[no-untyped-def]
        sample_project_in_db,  # type: ignore[no-untyped-def]
    ) -> None:
        """Notifications fire when scores exceed min_score_to_notify."""
        sample_project_config.notifications = NotificationConfig(
            enabled=True,
            min_score_to_notify=70,
            discord_webhook="https://discord.com/api/webhooks/test",
        )

        # Insert high-score data
        db_session.add(
            Score(
                normalized_post_id=1,
                project_id="test-project",
                total_score=85.0,
                components={"relevance": 0.9},
                scoring_version="v1",
            )
        )
        db_session.commit()

        mock_notifier = MagicMock(spec=Notifier)
        mock_notifier.send.return_value = True

        orch = _make_orchestrator(db_session, notifiers=[mock_notifier])
        result = orch._run_notify(sample_project_config, dry_run=False)

        assert result["notified"] == 1
        assert result["failed"] == 0
        mock_notifier.send.assert_called_once()

    def test_notifications_skip_when_disabled(
        self,
        db_session,  # type: ignore[no-untyped-def]
        sample_project_config,  # type: ignore[no-untyped-def]
    ) -> None:
        """Notifications skip when config.notifications.enabled = False."""
        sample_project_config.notifications = NotificationConfig(enabled=False)

        mock_notifier = MagicMock(spec=Notifier)
        orch = _make_orchestrator(db_session, notifiers=[mock_notifier])
        result = orch._run_notify(sample_project_config, dry_run=False)

        assert result["skipped"] is True
        mock_notifier.send.assert_not_called()

    def test_notifications_skip_when_no_notifiers(
        self,
        db_session,  # type: ignore[no-untyped-def]
        sample_project_config,  # type: ignore[no-untyped-def]
    ) -> None:
        """Notifications skip when no notifiers are provided."""
        sample_project_config.notifications = NotificationConfig(enabled=True)

        orch = _make_orchestrator(db_session, notifiers=[])
        result = orch._run_notify(sample_project_config, dry_run=False)

        assert result["skipped"] is True

    def test_notification_failure_doesnt_crash(
        self,
        db_session,  # type: ignore[no-untyped-def]
        sample_project_config,  # type: ignore[no-untyped-def]
        sample_project_in_db,  # type: ignore[no-untyped-def]
    ) -> None:
        """Notification failure doesn't crash the pipeline."""
        sample_project_config.notifications = NotificationConfig(
            enabled=True,
            min_score_to_notify=70,
        )

        # Insert data
        db_session.add(
            Score(
                normalized_post_id=1,
                project_id="test-project",
                total_score=90.0,
                components={"relevance": 0.9},
                scoring_version="v1",
            )
        )
        db_session.commit()

        mock_notifier = MagicMock(spec=Notifier)
        mock_notifier.send.side_effect = RuntimeError("webhook exploded")

        orch = _make_orchestrator(db_session, notifiers=[mock_notifier])
        # Should not raise
        result = orch._run_notify(sample_project_config, dry_run=False)

        assert result["failed"] == 1
        assert result["notified"] == 0

    def test_default_no_notifiers(
        self,
        db_session,  # type: ignore[no-untyped-def]
    ) -> None:
        """Default orchestrator has empty notifiers list."""
        orch = PipelineOrchestrator(
            db_session=db_session,
            connector=MagicMock(),
            judge=MagicMock(),
            draft_generator=MagicMock(),
        )
        assert orch.notifiers == []

"""Integration tests for rate limit compliance across the pipeline."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from signalops.config.schema import (
    PersonaConfig,
    ProjectConfig,
    QueryConfig,
    RelevanceRubric,
)
from signalops.exceptions import AuthenticationError, RateLimitError
from signalops.pipeline.sender import SenderStage
from signalops.storage.database import (
    Draft,
    DraftStatus,
    NormalizedPost,
    Project,
    RawPost,
)


def _make_config(
    *,
    max_per_hour: int = 100,
    max_per_day: int = 100,
    max_per_month: int = 0,
) -> ProjectConfig:
    return ProjectConfig(
        project_id="test-project",
        project_name="Test",
        description="Test",
        queries=[QueryConfig(text="test", label="test")],
        relevance=RelevanceRubric(
            system_prompt="test",
            positive_signals=["good"],
            negative_signals=["bad"],
        ),
        persona=PersonaConfig(
            name="Bot",
            role="test",
            tone="test",
            voice_notes="test",
            example_reply="test",
        ),
        rate_limits={
            "max_replies_per_hour": max_per_hour,
            "max_replies_per_day": max_per_day,
            "max_replies_per_month": max_per_month,
        },
    )


def _seed_approved_drafts(
    session: Session,
    count: int,
    project_id: str = "test-project",
) -> list[Draft]:
    """Create N approved drafts with associated raw + normalized posts."""
    drafts: list[Draft] = []
    for i in range(count):
        raw = RawPost(
            project_id=project_id,
            platform="x",
            platform_id=f"raw-{i}",
            query_used="test",
            raw_json={"id": f"raw-{i}", "text": f"post {i}"},
        )
        session.add(raw)
        session.flush()

        norm = NormalizedPost(
            raw_post_id=raw.id,
            project_id=project_id,
            platform="x",
            platform_id=f"norm-{i}",
            author_id=f"author-{i}",
            author_username=f"user{i}",
            text_original=f"post {i}",
            text_cleaned=f"post {i}",
            created_at=datetime.now(UTC),
        )
        session.add(norm)
        session.flush()

        draft = Draft(
            normalized_post_id=norm.id,
            project_id=project_id,
            text_generated=f"reply {i}",
            model_id="test-model",
            status=DraftStatus.APPROVED,
        )
        session.add(draft)
        session.flush()
        drafts.append(draft)

    session.commit()
    return drafts


def _seed_sent_drafts(
    session: Session,
    count: int,
    sent_at: datetime,
    project_id: str = "test-project",
) -> None:
    """Create N already-sent drafts at a specific time."""
    for i in range(count):
        raw = RawPost(
            project_id=project_id,
            platform="x",
            platform_id=f"sent-raw-{i}-{sent_at.isoformat()}",
            query_used="test",
            raw_json={"id": f"sent-raw-{i}"},
        )
        session.add(raw)
        session.flush()

        norm = NormalizedPost(
            raw_post_id=raw.id,
            project_id=project_id,
            platform="x",
            platform_id=f"sent-norm-{i}-{sent_at.isoformat()}",
            author_id=f"sent-author-{i}",
            author_username=f"sent-user{i}",
            text_original=f"sent post {i}",
            text_cleaned=f"sent post {i}",
            created_at=datetime.now(UTC),
        )
        session.add(norm)
        session.flush()

        draft = Draft(
            normalized_post_id=norm.id,
            project_id=project_id,
            text_generated=f"sent reply {i}",
            model_id="test-model",
            status=DraftStatus.SENT,
            sent_at=sent_at,
            sent_post_id=f"sent-id-{i}",
        )
        session.add(draft)

    session.commit()


@pytest.fixture
def _project_in_db(db_session: Session) -> str:
    project = Project(
        id="test-project",
        name="Test",
        config_path="test.yaml",
        config_hash="abc",
    )
    db_session.add(project)
    db_session.commit()
    return "test-project"


class TestSenderHourlyLimit:
    def test_respects_hourly_limit(self, db_session: Session, _project_in_db: str) -> None:
        """With 6 drafts and limit=5, only 5 should be sent."""
        config = _make_config(max_per_hour=5)
        _seed_approved_drafts(db_session, 6)

        connector = MagicMock()
        connector.post_reply.return_value = "reply-id"

        sender = SenderStage(connector, db_session)
        result = sender.run("test-project", config)

        assert result["sent_count"] == 5
        assert result["skipped_rate_limit"] >= 1


class TestSenderDailyLimit:
    def test_respects_daily_limit(self, db_session: Session, _project_in_db: str) -> None:
        """With 5 already sent today and limit=5, none should be sent."""
        config = _make_config(max_per_day=5)
        _seed_sent_drafts(db_session, 5, sent_at=datetime.now(UTC) - timedelta(minutes=30))
        _seed_approved_drafts(db_session, 3)

        connector = MagicMock()
        sender = SenderStage(connector, db_session)
        result = sender.run("test-project", config)

        assert result["sent_count"] == 0
        assert "Daily limit" in result.get("rate_limit_reason", "")


class TestSenderMonthlyLimit:
    def test_respects_monthly_limit(self, db_session: Session, _project_in_db: str) -> None:
        """Monthly cap should block sends when reached."""
        config = _make_config(max_per_month=10)
        _seed_sent_drafts(db_session, 10, sent_at=datetime.now(UTC) - timedelta(days=15))
        _seed_approved_drafts(db_session, 3)

        connector = MagicMock()
        sender = SenderStage(connector, db_session)
        result = sender.run("test-project", config)

        assert result["sent_count"] == 0
        assert "Monthly limit" in result.get("rate_limit_reason", "")

    def test_monthly_limit_zero_means_disabled(
        self, db_session: Session, _project_in_db: str
    ) -> None:
        """max_per_month=0 should not block."""
        config = _make_config(max_per_month=0)
        _seed_approved_drafts(db_session, 2)

        connector = MagicMock()
        connector.post_reply.return_value = "reply-id"

        sender = SenderStage(connector, db_session)
        result = sender.run("test-project", config)

        assert result["sent_count"] == 2


class TestSenderErrorHandling:
    def test_stops_on_rate_limit_error(self, db_session: Session, _project_in_db: str) -> None:
        """If connector raises RateLimitError, sender should stop sending."""
        config = _make_config()
        _seed_approved_drafts(db_session, 3)

        connector = MagicMock()
        connector.post_reply.side_effect = [
            "reply-1",
            RateLimitError("rate limited", retry_after=60),
            "reply-3",  # should never be called
        ]

        sender = SenderStage(connector, db_session)
        result = sender.run("test-project", config)

        assert result["sent_count"] == 1
        assert result["skipped_rate_limit"] >= 1

    def test_stops_on_auth_error(self, db_session: Session, _project_in_db: str) -> None:
        """If connector raises AuthenticationError, sender should stop."""
        config = _make_config()
        _seed_approved_drafts(db_session, 3)

        connector = MagicMock()
        connector.post_reply.side_effect = [
            "reply-1",
            AuthenticationError("invalid token"),
            "reply-3",  # should never be called
        ]

        sender = SenderStage(connector, db_session)
        result = sender.run("test-project", config)

        assert result["sent_count"] == 1
        assert result["failed_count"] == 1
        # Only 2 calls — stops after auth error
        assert connector.post_reply.call_count == 2

"""End-to-end pipeline integration tests with mocked external APIs."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from signalops.connectors.base import Connector, RawPost
from signalops.storage.database import (
    Draft,
    DraftStatus,
    NormalizedPost,
)


@pytest.fixture
def mock_connector():
    """Returns a mock Connector that returns fake tweets."""
    connector = MagicMock(spec=Connector)
    connector.search.return_value = [
        RawPost(
            platform="x",
            platform_id="123456",
            author_id="789",
            author_username="testuser",
            author_display_name="Test User",
            author_followers=1000,
            author_verified=False,
            text="Looking for a good code review tool. Anyone recommend?",
            created_at=datetime.now(UTC),
            language="en",
            reply_to_id=None,
            conversation_id="123456",
            metrics={"likes": 5, "retweets": 1, "replies": 2, "views": 500},
            entities={"urls": [], "mentions": [], "hashtags": []},
            raw_json={"id": "123456", "text": "Looking for a good code review tool."},
        ),
        RawPost(
            platform="x",
            platform_id="654321",
            author_id="321",
            author_username="devjane",
            author_display_name="Jane Developer",
            author_followers=5000,
            author_verified=True,
            text="Anyone know a tool that helps with automated PR reviews?",
            created_at=datetime.now(UTC),
            language="en",
            reply_to_id=None,
            conversation_id="654321",
            metrics={"likes": 12, "retweets": 3, "replies": 4, "views": 1200},
            entities={"urls": [], "mentions": [], "hashtags": ["#devtools"]},
            raw_json={"id": "654321", "text": "Anyone know a tool for automated PR reviews?"},
        ),
    ]
    connector.post_reply.return_value = "reply-999"
    connector.health_check.return_value = True
    return connector


def test_sender_dry_run(db_session, sample_project_in_db, mock_connector, sample_project_config):
    """Test that sender stage respects dry_run flag."""
    from signalops.pipeline.sender import SenderStage

    # Create a normalized post and approved draft
    post = NormalizedPost(
        raw_post_id=1,
        project_id="test-project",
        platform="x",
        platform_id="123",
        author_id="456",
        author_username="testuser",
        author_display_name="Test",
        author_followers=1000,
        author_verified=False,
        text_original="Test tweet",
        text_cleaned="Test tweet",
        created_at=datetime.now(UTC),
        likes=5,
        retweets=1,
        replies=2,
        views=500,
    )
    db_session.add(post)
    db_session.flush()

    draft = Draft(
        normalized_post_id=post.id,
        project_id="test-project",
        text_generated="Great question! Check out our tool.",
        model_id="claude-sonnet-4-6",
        status=DraftStatus.APPROVED,
        approved_at=datetime.now(UTC),
    )
    db_session.add(draft)
    db_session.commit()

    # Create a RawPost row (required by FK)
    from signalops.storage.database import RawPost as RawPostDB

    raw_post = RawPostDB(
        id=1,
        project_id="test-project",
        platform="x",
        platform_id="123",
        raw_json={"text": "test"},
    )
    db_session.add(raw_post)
    db_session.commit()

    sender = SenderStage(connector=mock_connector, db_session=db_session)
    result = sender.run(
        project_id="test-project",
        config=sample_project_config,
        dry_run=True,
    )

    assert result["dry_run"] is True
    assert result["sent_count"] == 1
    # Connector should NOT have been called in dry run
    mock_connector.post_reply.assert_not_called()
    # Draft status should still be APPROVED (not SENT)
    db_session.refresh(draft)
    assert draft.status == DraftStatus.APPROVED


def test_sender_rate_limit_check(
    db_session,
    sample_project_in_db,
    mock_connector,
    sample_project_config,
):
    """Test sender respects rate limits."""
    from signalops.pipeline.sender import SenderStage

    sender = SenderStage(connector=mock_connector, db_session=db_session)

    # With no sent drafts, rate limit should be OK
    is_allowed, reason = sender._check_rate_limits("test-project", sample_project_config)
    assert is_allowed is True
    assert reason == ""


def test_orchestrator_instantiation(db_session, mock_connector):
    """Test that PipelineOrchestrator can be instantiated."""
    from unittest.mock import MagicMock

    from signalops.pipeline.orchestrator import PipelineOrchestrator

    judge = MagicMock()
    draft_gen = MagicMock()

    orchestrator = PipelineOrchestrator(
        db_session=db_session,
        connector=mock_connector,
        judge=judge,
        draft_generator=draft_gen,
    )

    assert orchestrator.session is db_session
    assert orchestrator.connector is mock_connector


def test_exporter_empty_db(db_session, sample_project_in_db):
    """Test exporter with no data returns empty results."""
    import os
    import tempfile

    from signalops.training.exporter import TrainingDataExporter

    exporter = TrainingDataExporter(db_session=db_session)

    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w") as f:
        output_path = f.name

    try:
        result = exporter.export_judgments(
            project_id="test-project",
            format="openai",
            output=output_path,
        )
        assert result["records"] == 0

        result = exporter.export_draft_preferences(
            project_id="test-project",
            output=output_path,
        )
        assert result["records"] == 0
    finally:
        os.unlink(output_path)


def test_queue_approve_and_reject(db_session, sample_project_in_db):
    """Test draft approval and rejection flow."""
    post = NormalizedPost(
        raw_post_id=1,
        project_id="test-project",
        platform="x",
        platform_id="t1",
        author_id="a1",
        author_username="user1",
        author_display_name="User One",
        author_followers=500,
        author_verified=False,
        text_original="Need help",
        text_cleaned="Need help",
        created_at=datetime.now(UTC),
    )
    db_session.add(post)
    db_session.flush()

    # Create RawPost (for FK)
    from signalops.storage.database import RawPost as RawPostDB

    raw = RawPostDB(id=1, project_id="test-project", platform="x", platform_id="t1", raw_json={})
    db_session.add(raw)

    draft1 = Draft(
        normalized_post_id=post.id,
        project_id="test-project",
        text_generated="Here to help!",
        model_id="test-model",
        status=DraftStatus.PENDING,
    )
    draft2 = Draft(
        normalized_post_id=post.id,
        project_id="test-project",
        text_generated="We can assist!",
        model_id="test-model",
        status=DraftStatus.PENDING,
    )
    db_session.add_all([draft1, draft2])
    db_session.commit()

    # Approve draft1
    draft1.status = DraftStatus.APPROVED
    draft1.approved_at = datetime.now(UTC)
    db_session.commit()

    db_session.refresh(draft1)
    assert draft1.status == DraftStatus.APPROVED

    # Reject draft2
    draft2.status = DraftStatus.REJECTED
    db_session.commit()

    db_session.refresh(draft2)
    assert draft2.status == DraftStatus.REJECTED

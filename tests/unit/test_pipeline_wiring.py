"""Tests for pipeline run and queue send wiring."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from signalops.api.app import create_app
from signalops.storage.database import (
    Base,
    Draft,
    DraftStatus,
    NormalizedPost,
    Project,
    RawPost,
    get_engine,
    get_session,
)


@pytest.fixture()
def db_url() -> Iterator[str]:
    """Create a temp-file SQLite database URL."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    url = f"sqlite:///{db_path}"
    engine = get_engine(url)
    Base.metadata.create_all(engine)
    engine.dispose()
    yield url
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture()
def client(db_url: str) -> Iterator[TestClient]:
    """Create a test client."""
    with patch.dict(os.environ, {"SIGNALOPS_DB_URL": db_url}):
        app = create_app()
        with TestClient(app) as c:
            yield c


@pytest.fixture()
def seeded_db(db_url: str) -> str:
    """Seed the database with a project, posts, and drafts."""
    engine = get_engine(db_url)
    session = get_session(engine)

    project = Project(id="test-proj", name="Test", config_path="projects/spectra.yaml")
    project.is_active = True  # type: ignore[assignment]
    session.add(project)
    session.flush()

    raw = RawPost(
        platform="x",
        platform_id="tweet_123",
        project_id="test-proj",
        query_used="test",
        raw_json={"text": "Need better code review"},
    )
    session.add(raw)
    session.flush()

    post = NormalizedPost(
        raw_post_id=raw.id,
        project_id="test-proj",
        platform="x",
        platform_id="tweet_123",
        author_id="user1",
        author_username="testuser",
        author_display_name="Test User",
        author_followers=500,
        author_verified=False,
        text_original="Need better code review",
        text_cleaned="need better code review",
        created_at=datetime.now(UTC),
    )
    session.add(post)
    session.flush()

    draft = Draft(
        normalized_post_id=post.id,
        project_id="test-proj",
        text_generated="Have you tried Spectra?",
        model_id="test-model",
        status=DraftStatus.APPROVED,
        approved_at=datetime.now(UTC),
    )
    session.add(draft)
    session.commit()
    session.close()
    engine.dispose()
    return db_url


class TestPipelineRun:
    """Test that /api/pipeline/run triggers the orchestrator."""

    def test_pipeline_run_returns_started(self, seeded_db: str) -> None:
        """POST /api/pipeline/run returns started status."""
        with patch.dict(os.environ, {"SIGNALOPS_DB_URL": seeded_db}):
            app = create_app()
            with TestClient(app) as client:
                resp = client.post("/api/pipeline/run")
                assert resp.status_code == 200
                data = resp.json()
                assert data["status"] == "started"
                assert data["project_id"] == "test-proj"

    def test_pipeline_run_no_project_returns_404(self, db_url: str) -> None:
        """POST /api/pipeline/run with no project returns 404."""
        with patch.dict(os.environ, {"SIGNALOPS_DB_URL": db_url}):
            app = create_app()
            with TestClient(app) as client:
                resp = client.post("/api/pipeline/run")
                assert resp.status_code == 404


class TestQueueSend:
    """Test that /api/queue/send wires to connector."""

    def test_send_with_connector(self, seeded_db: str) -> None:
        """POST /api/queue/send actually calls connector.post_reply."""
        mock_connector = MagicMock()
        mock_connector.post_reply.return_value = "reply_tweet_999"

        with patch.dict(os.environ, {"SIGNALOPS_DB_URL": seeded_db}):
            with patch(
                "signalops.connectors.factory.ConnectorFactory"
            ) as MockFactory:
                mock_factory_instance = MagicMock()
                mock_factory_instance.create.return_value = mock_connector
                MockFactory.return_value = mock_factory_instance

                app = create_app()
                with TestClient(app) as client:
                    resp = client.post("/api/queue/send")
                    assert resp.status_code == 200
                    data = resp.json()
                    assert data["sent_count"] >= 1
                    assert data["failed_count"] == 0

                    # Verify connector was called
                    mock_connector.post_reply.assert_called()

    def test_send_without_connector_dry_run(self, seeded_db: str) -> None:
        """POST /api/queue/send marks as sent even without connector."""
        with patch.dict(os.environ, {"SIGNALOPS_DB_URL": seeded_db}):
            with patch(
                "signalops.connectors.factory.ConnectorFactory"
            ) as MockFactory:
                mock_factory_instance = MagicMock()
                mock_factory_instance.create.side_effect = ValueError("No token")
                MockFactory.return_value = mock_factory_instance

                app = create_app()
                with TestClient(app) as client:
                    resp = client.post("/api/queue/send")
                    assert resp.status_code == 200
                    data = resp.json()
                    assert data["sent_count"] >= 1

    def test_send_empty_queue(self, db_url: str) -> None:
        """POST /api/queue/send with no approved drafts."""
        with patch.dict(os.environ, {"SIGNALOPS_DB_URL": db_url}):
            app = create_app()
            with TestClient(app) as client:
                resp = client.post("/api/queue/send")
                assert resp.status_code == 200
                data = resp.json()
                assert data["sent_count"] == 0


class TestAuthOptional:
    """Test that API key is optional when not configured."""

    def test_projects_accessible_without_key(self, client: TestClient) -> None:
        """GET /api/projects works without API key when not configured."""
        resp = client.get("/api/projects")
        assert resp.status_code == 200

    def test_pipeline_accessible_without_key(self, db_url: str) -> None:
        """POST /api/pipeline/run accessible without API key."""
        # Seed a project first
        engine = get_engine(db_url)
        session = get_session(engine)
        project = Project(
            id="test", name="Test", config_path="projects/spectra.yaml"
        )
        project.is_active = True  # type: ignore[assignment]
        session.add(project)
        session.commit()
        session.close()
        engine.dispose()

        with patch.dict(os.environ, {"SIGNALOPS_DB_URL": db_url}):
            app = create_app()
            with TestClient(app) as client:
                resp = client.post("/api/pipeline/run")
                assert resp.status_code == 200

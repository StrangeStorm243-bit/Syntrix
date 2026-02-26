"""Tests for setup and sequence API routes."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from signalops.storage.database import (
    Enrollment,
    EnrollmentStatus,
    NormalizedPost,
    Project,
    RawPost,
    Sequence,
    SequenceStep,
    init_db,
)


def _create_test_app() -> tuple[FastAPI, Any]:
    """Create a minimal FastAPI app with setup + sequences routes."""
    from signalops.api.routes.sequences import router as sequences_router
    from signalops.api.routes.setup import router as setup_router

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    init_db(engine)

    app = FastAPI()
    app.state.engine = engine
    app.include_router(setup_router)
    app.include_router(sequences_router)

    return app, engine


class TestSetupStatus:
    """Tests for GET /api/setup/status."""

    def setup_method(self) -> None:
        self.app, self.engine = _create_test_app()
        self.client = TestClient(self.app)

    def teardown_method(self) -> None:
        self.engine.dispose()

    def test_status_returns_incomplete_when_no_project(self) -> None:
        """Returns is_complete=False when no project exists."""
        resp = self.client.get("/api/setup/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_complete"] is False
        assert data["project_id"] is None

    def test_status_returns_complete_when_project_exists(self) -> None:
        """Returns is_complete=True when a project exists."""
        session = Session(self.engine)
        project = Project(id="test", name="Test", config_path="t.yaml")
        session.add(project)
        session.commit()
        session.close()

        resp = self.client.get("/api/setup/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_complete"] is True
        assert data["project_id"] == "test"
        assert data["project_name"] == "Test"


class TestTestConnection:
    """Tests for POST /api/setup/test-connection."""

    def setup_method(self) -> None:
        self.app, self.engine = _create_test_app()
        self.client = TestClient(self.app)

    def teardown_method(self) -> None:
        self.engine.dispose()

    @patch("signalops.api.routes.setup.TwikitConnector", create=True)
    def test_successful_connection(self, mock_cls: MagicMock) -> None:
        """Returns success=True when connector health check passes."""
        mock_instance = MagicMock()
        mock_instance.health_check.return_value = True
        mock_cls.return_value = mock_instance

        resp = self.client.post(
            "/api/setup/test-connection",
            json={"username": "testuser", "password": "testpass"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["username"] == "testuser"

    @patch("signalops.api.routes.setup.TwikitConnector", create=True)
    def test_failed_connection(self, mock_cls: MagicMock) -> None:
        """Returns success=False when connector raises."""
        mock_cls.side_effect = Exception("Login failed")

        resp = self.client.post(
            "/api/setup/test-connection",
            json={"username": "bad", "password": "bad"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert "Login failed" in data["message"]


class TestCompleteSetup:
    """Tests for POST /api/setup."""

    def setup_method(self) -> None:
        self.app, self.engine = _create_test_app()
        self.client = TestClient(self.app)

    def teardown_method(self) -> None:
        self.engine.dispose()
        # Clean up generated YAML files
        import glob

        for f in glob.glob("projects/test-*.yaml"):
            try:
                os.remove(f)
            except OSError:
                pass

    @patch("signalops.api.routes.setup.SequenceEngine")
    def test_complete_setup_creates_project(self, mock_engine_cls: MagicMock) -> None:
        """POST /api/setup creates a project in the database."""
        mock_engine_instance = MagicMock()
        mock_engine_instance.create_default_sequences.return_value = []
        mock_engine_cls.return_value = mock_engine_instance

        resp = self.client.post(
            "/api/setup",
            json={
                "project_name": "Test Project",
                "product_url": "https://example.com",
                "description": "A test product",
                "problem_statement": "Testing is hard",
                "role_keywords": ["developers"],
                "tweet_topics": ["testing tools"],
                "twitter_username": "testuser",
                "twitter_password": "testpass",
                "persona_name": "Alex",
                "persona_role": "Developer Advocate",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_complete"] is True
        assert data["project_id"] == "test-project"
        assert data["project_name"] == "Test Project"

    @patch("signalops.api.routes.setup.SequenceEngine")
    def test_complete_setup_creates_yaml_file(self, mock_engine_cls: MagicMock) -> None:
        """POST /api/setup generates a project YAML file."""
        mock_engine_instance = MagicMock()
        mock_engine_instance.create_default_sequences.return_value = []
        mock_engine_cls.return_value = mock_engine_instance

        self.client.post(
            "/api/setup",
            json={
                "project_name": "Test YAML",
                "product_url": "https://example.com",
                "description": "A test product",
                "problem_statement": "Testing is hard",
                "role_keywords": ["developers"],
                "tweet_topics": ["testing"],
                "twitter_username": "testuser",
                "twitter_password": "testpass",
                "persona_name": "Alex",
                "persona_role": "Developer Advocate",
            },
        )
        config_path = "projects/test-yaml.yaml"
        assert os.path.exists(config_path)

    @patch("signalops.api.routes.setup.SequenceEngine")
    def test_setup_status_complete_after_setup(self, mock_engine_cls: MagicMock) -> None:
        """After POST /api/setup, GET /api/setup/status returns is_complete=True."""
        mock_engine_instance = MagicMock()
        mock_engine_instance.create_default_sequences.return_value = []
        mock_engine_cls.return_value = mock_engine_instance

        self.client.post(
            "/api/setup",
            json={
                "project_name": "Test Status",
                "product_url": "https://example.com",
                "description": "A test product",
                "problem_statement": "Testing is hard",
                "role_keywords": ["developers"],
                "tweet_topics": ["testing"],
                "twitter_username": "testuser",
                "twitter_password": "testpass",
                "persona_name": "Alex",
                "persona_role": "Developer Advocate",
            },
        )
        resp = self.client.get("/api/setup/status")
        assert resp.json()["is_complete"] is True


class TestListSequences:
    """Tests for GET /api/sequences."""

    def setup_method(self) -> None:
        self.app, self.engine = _create_test_app()
        self.client = TestClient(self.app)

        # Seed project and sequences
        session = Session(self.engine)
        proj = Project(id="test", name="Test", config_path="t.yaml", is_active=True)
        session.add(proj)
        session.flush()

        seq = Sequence(project_id="test", name="Gentle Touch")
        session.add(seq)
        session.flush()

        step = SequenceStep(
            sequence_id=seq.id,
            step_order=1,
            action_type="like",
            delay_hours=0,
        )
        session.add(step)
        session.commit()
        self.seq_id = seq.id
        session.close()

    def teardown_method(self) -> None:
        self.engine.dispose()

    def test_list_sequences_returns_sequences(self) -> None:
        """GET /api/sequences returns sequences for active project."""
        resp = self.client.get("/api/sequences")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "Gentle Touch"
        assert len(data[0]["steps"]) == 1
        assert data[0]["enrolled_count"] == 0
        assert data[0]["completed_count"] == 0

    def test_list_sequences_with_enrollments(self) -> None:
        """Sequences include enrollment counts."""
        session = Session(self.engine)
        # Add a raw + normalized post for enrollment FK
        raw = RawPost(project_id="test", platform="x", platform_id="tw1", raw_json={})
        session.add(raw)
        session.flush()
        norm = NormalizedPost(
            raw_post_id=raw.id,
            project_id="test",
            platform="x",
            platform_id="tw1",
            author_id="u1",
            author_username="testuser",
            text_original="Test",
            text_cleaned="Test",
            created_at=datetime.now(UTC),
        )
        session.add(norm)
        session.flush()

        enrollment = Enrollment(
            normalized_post_id=norm.id,
            sequence_id=self.seq_id,
            project_id="test",
            status=EnrollmentStatus.ACTIVE,
        )
        session.add(enrollment)
        session.commit()
        session.close()

        resp = self.client.get("/api/sequences")
        data = resp.json()
        assert data[0]["enrolled_count"] == 1


class TestListEnrollments:
    """Tests for GET /api/sequences/{id}/enrollments."""

    def setup_method(self) -> None:
        self.app, self.engine = _create_test_app()
        self.client = TestClient(self.app)

        # Seed data
        session = Session(self.engine)
        proj = Project(id="test", name="Test", config_path="t.yaml", is_active=True)
        session.add(proj)

        seq = Sequence(project_id="test", name="Test Seq")
        session.add(seq)
        session.flush()
        self.seq_id = seq.id

        raw = RawPost(project_id="test", platform="x", platform_id="tw1", raw_json={})
        session.add(raw)
        session.flush()
        norm = NormalizedPost(
            raw_post_id=raw.id,
            project_id="test",
            platform="x",
            platform_id="tw1",
            author_id="u1",
            author_username="testuser",
            text_original="Test",
            text_cleaned="Test",
            created_at=datetime.now(UTC),
        )
        session.add(norm)
        session.flush()

        enrollment = Enrollment(
            normalized_post_id=norm.id,
            sequence_id=seq.id,
            project_id="test",
            status=EnrollmentStatus.ACTIVE,
        )
        session.add(enrollment)
        session.commit()
        session.close()

    def teardown_method(self) -> None:
        self.engine.dispose()

    def test_list_enrollments_returns_enrollments(self) -> None:
        """GET /api/sequences/{id}/enrollments returns enrollment list."""
        resp = self.client.get(f"/api/sequences/{self.seq_id}/enrollments")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["status"] == "active"

    def test_list_enrollments_empty_for_unknown_sequence(self) -> None:
        """Returns empty list for sequence with no enrollments."""
        resp = self.client.get("/api/sequences/9999/enrollments")
        assert resp.status_code == 200
        assert resp.json() == []

"""Integration tests for API routes with seeded test data."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator
from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from signalops.api.app import create_app
from signalops.storage.database import (
    Base,
    Draft,
    DraftStatus,
    Judgment,
    JudgmentLabel,
    NormalizedPost,
    Project,
    RawPost,
    Score,
    get_engine,
    get_session,
)

API_KEY = "test-key-123"


@pytest.fixture()
def client() -> Iterator[TestClient]:
    """Create a test client with seeded data in a temp-file SQLite DB.

    We patch SIGNALOPS_DB_URL so the app lifespan creates its engine
    against the same DB file where we've seeded test data.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db_url = f"sqlite:///{db_path}"

    # Create tables and seed data in the temp DB
    engine = get_engine(db_url)
    Base.metadata.create_all(engine)
    session = get_session(engine)

    project = Project(
        id="spectra",
        name="Spectra",
        config_path="projects/spectra.yaml",
        is_active=True,
    )
    session.add(project)

    raw = RawPost(
        project_id="spectra",
        platform="x",
        platform_id="tweet_1",
        raw_json={"text": "hello"},
    )
    session.add(raw)
    session.flush()

    post = NormalizedPost(
        raw_post_id=raw.id,
        project_id="spectra",
        platform="x",
        platform_id="tweet_1",
        author_id="user_1",
        author_username="alice",
        author_display_name="Alice",
        author_followers=500,
        author_verified=True,
        text_original="Looking for a CRM tool",
        text_cleaned="looking for a crm tool",
        language="en",
        created_at=datetime(2026, 1, 15, tzinfo=UTC),
    )
    session.add(post)
    session.flush()

    judgment = Judgment(
        normalized_post_id=post.id,
        project_id="spectra",
        label=JudgmentLabel.RELEVANT,
        confidence=0.95,
        reasoning="Strong buying signal",
        model_id="claude-sonnet-4-6",
    )
    session.add(judgment)

    score = Score(
        normalized_post_id=post.id,
        project_id="spectra",
        total_score=82.5,
        components={"relevance": 0.95, "authority": 0.7},
        scoring_version="v1",
    )
    session.add(score)

    draft = Draft(
        normalized_post_id=post.id,
        project_id="spectra",
        text_generated="Hey! Have you checked out Spectra?",
        model_id="claude-sonnet-4-6",
        status=DraftStatus.PENDING,
    )
    session.add(draft)
    session.commit()
    session.close()
    engine.dispose()

    with patch.dict(os.environ, {"SIGNALOPS_DB_URL": db_url}):
        app = create_app()
        with TestClient(app) as c:
            yield c

    # Clean up temp file
    try:
        os.unlink(db_path)
    except OSError:
        pass


def _headers() -> dict[str, str]:
    return {"X-API-Key": API_KEY}


class TestProjects:
    @patch.dict(os.environ, {"SIGNALOPS_API_KEY": API_KEY})
    def test_list_projects(self, client: TestClient) -> None:
        resp = client.get("/api/projects", headers=_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == "spectra"

    @patch.dict(os.environ, {"SIGNALOPS_API_KEY": API_KEY})
    def test_get_project(self, client: TestClient) -> None:
        resp = client.get("/api/projects/spectra", headers=_headers())
        assert resp.status_code == 200
        assert resp.json()["name"] == "Spectra"

    @patch.dict(os.environ, {"SIGNALOPS_API_KEY": API_KEY})
    def test_get_nonexistent_project(self, client: TestClient) -> None:
        resp = client.get("/api/projects/nope", headers=_headers())
        assert resp.status_code == 404


class TestLeads:
    @patch.dict(os.environ, {"SIGNALOPS_API_KEY": API_KEY})
    def test_list_leads(self, client: TestClient) -> None:
        resp = client.get("/api/leads", headers=_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["author_username"] == "alice"

    @patch.dict(os.environ, {"SIGNALOPS_API_KEY": API_KEY})
    def test_list_leads_with_label_filter(self, client: TestClient) -> None:
        resp = client.get("/api/leads?label=relevant", headers=_headers())
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    @patch.dict(os.environ, {"SIGNALOPS_API_KEY": API_KEY})
    def test_list_leads_with_score_filter(self, client: TestClient) -> None:
        resp = client.get("/api/leads?min_score=80", headers=_headers())
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    @patch.dict(os.environ, {"SIGNALOPS_API_KEY": API_KEY})
    def test_top_leads(self, client: TestClient) -> None:
        resp = client.get("/api/leads/top", headers=_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["score"] == 82.5

    @patch.dict(os.environ, {"SIGNALOPS_API_KEY": API_KEY})
    def test_get_lead_detail(self, client: TestClient) -> None:
        resp = client.get("/api/leads", headers=_headers())
        lead_id = resp.json()["items"][0]["id"]
        resp = client.get(f"/api/leads/{lead_id}", headers=_headers())
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["judgment_reasoning"] == "Strong buying signal"
        assert detail["score"] == 82.5


class TestQueue:
    @patch.dict(os.environ, {"SIGNALOPS_API_KEY": API_KEY})
    def test_list_queue(self, client: TestClient) -> None:
        resp = client.get("/api/queue", headers=_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "pending"

    @patch.dict(os.environ, {"SIGNALOPS_API_KEY": API_KEY})
    def test_approve_draft(self, client: TestClient) -> None:
        resp = client.get("/api/queue", headers=_headers())
        draft_id = resp.json()["items"][0]["id"]
        resp = client.post(f"/api/queue/{draft_id}/approve", headers=_headers())
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"

    @patch.dict(os.environ, {"SIGNALOPS_API_KEY": API_KEY})
    def test_edit_draft(self, client: TestClient) -> None:
        resp = client.get("/api/queue", headers=_headers())
        draft_id = resp.json()["items"][0]["id"]
        resp = client.post(
            f"/api/queue/{draft_id}/edit",
            headers=_headers(),
            json={"text": "Updated reply text"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "edited"
        assert resp.json()["text_final"] == "Updated reply text"

    @patch.dict(os.environ, {"SIGNALOPS_API_KEY": API_KEY})
    def test_reject_draft(self, client: TestClient) -> None:
        resp = client.get("/api/queue", headers=_headers())
        draft_id = resp.json()["items"][0]["id"]
        resp = client.post(
            f"/api/queue/{draft_id}/reject",
            headers=_headers(),
            json={"reason": "off-topic"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "rejected"


class TestStats:
    @patch.dict(os.environ, {"SIGNALOPS_API_KEY": API_KEY})
    def test_pipeline_stats(self, client: TestClient) -> None:
        resp = client.get("/api/stats", headers=_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert data["collected"] >= 1
        assert data["judged"] >= 1
        assert data["scored"] >= 1

    @patch.dict(os.environ, {"SIGNALOPS_API_KEY": API_KEY})
    def test_stats_timeline(self, client: TestClient) -> None:
        resp = client.get("/api/stats/timeline", headers=_headers())
        assert resp.status_code == 200

    @patch.dict(os.environ, {"SIGNALOPS_API_KEY": API_KEY})
    def test_outcomes(self, client: TestClient) -> None:
        resp = client.get("/api/stats/outcomes", headers=_headers())
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestAnalytics:
    @patch.dict(os.environ, {"SIGNALOPS_API_KEY": API_KEY})
    def test_score_distribution(self, client: TestClient) -> None:
        resp = client.get("/api/analytics/score-distribution", headers=_headers())
        assert resp.status_code == 200

    @patch.dict(os.environ, {"SIGNALOPS_API_KEY": API_KEY})
    def test_conversion_funnel(self, client: TestClient) -> None:
        resp = client.get("/api/analytics/conversion-funnel", headers=_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 6
        assert data[0]["stage"] == "Collected"

    @patch.dict(os.environ, {"SIGNALOPS_API_KEY": API_KEY})
    def test_judge_accuracy(self, client: TestClient) -> None:
        resp = client.get("/api/analytics/judge-accuracy", headers=_headers())
        assert resp.status_code == 200


class TestExperiments:
    @patch.dict(os.environ, {"SIGNALOPS_API_KEY": API_KEY})
    def test_list_experiments_empty(self, client: TestClient) -> None:
        resp = client.get("/api/experiments", headers=_headers())
        assert resp.status_code == 200
        assert resp.json() == []

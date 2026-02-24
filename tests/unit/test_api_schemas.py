"""Tests for API Pydantic response schemas."""

from __future__ import annotations

from datetime import datetime

from signalops.api.schemas import (
    DraftResponse,
    LeadResponse,
    PaginatedResponse,
    PipelineStatsResponse,
    ProjectResponse,
    ScoreDistributionBucket,
)


class TestPaginatedResponse:
    def test_pages_calculation(self) -> None:
        resp: PaginatedResponse[int] = PaginatedResponse(
            items=[1, 2, 3], total=25, page=1, page_size=10
        )
        assert resp.pages == 3

    def test_pages_exact_division(self) -> None:
        resp: PaginatedResponse[int] = PaginatedResponse(items=[], total=20, page=1, page_size=10)
        assert resp.pages == 2

    def test_pages_zero_total(self) -> None:
        resp: PaginatedResponse[int] = PaginatedResponse(items=[], total=0, page=1, page_size=10)
        assert resp.pages == 0

    def test_pages_zero_page_size(self) -> None:
        resp: PaginatedResponse[int] = PaginatedResponse(items=[], total=10, page=1, page_size=0)
        assert resp.pages == 0

    def test_single_page(self) -> None:
        resp: PaginatedResponse[int] = PaginatedResponse(items=[1], total=1, page=1, page_size=20)
        assert resp.pages == 1


class TestLeadResponse:
    def test_serializes_with_nulls(self) -> None:
        lead = LeadResponse(
            id=1,
            platform="x",
            platform_id="123",
            author_username=None,
            author_display_name=None,
            author_followers=0,
            author_verified=False,
            text_original="hello",
            text_cleaned="hello",
            created_at=datetime(2026, 1, 1),
        )
        data = lead.model_dump()
        assert data["score"] is None
        assert data["judgment_label"] is None
        assert data["draft_status"] is None

    def test_serializes_with_all_fields(self) -> None:
        lead = LeadResponse(
            id=1,
            platform="x",
            platform_id="123",
            author_username="alice",
            author_display_name="Alice",
            author_followers=500,
            author_verified=True,
            text_original="hello",
            text_cleaned="hello",
            created_at=datetime(2026, 1, 1),
            score=85.5,
            judgment_label="relevant",
            judgment_confidence=0.92,
            draft_status="pending",
        )
        data = lead.model_dump()
        assert data["score"] == 85.5
        assert data["judgment_label"] == "relevant"


class TestProjectResponse:
    def test_serializes(self) -> None:
        proj = ProjectResponse(
            id="spectra",
            name="Spectra",
            config_path="projects/spectra.yaml",
            is_active=True,
            created_at=None,
            updated_at=None,
        )
        data = proj.model_dump()
        assert data["id"] == "spectra"
        assert data["is_active"] is True


class TestDraftResponse:
    def test_serializes(self) -> None:
        draft = DraftResponse(
            id=1,
            normalized_post_id=10,
            project_id="spectra",
            text_generated="Hey!",
            text_final=None,
            tone="helpful",
            template_used=None,
            model_id="claude-sonnet-4-6",
            status="pending",
            created_at=None,
            approved_at=None,
            sent_at=None,
        )
        data = draft.model_dump()
        assert data["status"] == "pending"
        assert data["text_final"] is None


class TestPipelineStats:
    def test_serializes(self) -> None:
        stats = PipelineStatsResponse(
            collected=100,
            judged=80,
            relevant=50,
            scored=50,
            drafted=30,
            approved=20,
            sent=10,
            outcomes=5,
        )
        data = stats.model_dump()
        assert data["collected"] == 100
        assert data["outcomes"] == 5


class TestScoreDistributionBucket:
    def test_serializes(self) -> None:
        bucket = ScoreDistributionBucket(bucket_min=0.0, bucket_max=10.0, count=5)
        data = bucket.model_dump()
        assert data["bucket_min"] == 0.0
        assert data["count"] == 5

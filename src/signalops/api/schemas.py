"""Pydantic response models for the SignalOps REST API."""

from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, computed_field

T = TypeVar("T")


# ── Pagination ──


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list wrapper."""

    items: list[T]
    total: int
    page: int
    page_size: int

    @computed_field  # type: ignore[prop-decorator]
    @property
    def pages(self) -> int:
        if self.page_size <= 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size


# ── Projects ──


class ProjectResponse(BaseModel):
    id: str
    name: str
    config_path: str
    is_active: bool | None
    created_at: datetime | None
    updated_at: datetime | None


class ProjectConfigResponse(BaseModel):
    """Sanitized project config (no secrets)."""

    project_id: str
    project_name: str
    description: str
    queries: list[dict[str, object]]
    scoring: dict[str, object]
    persona: dict[str, object]


# ── Leads ──


class LeadResponse(BaseModel):
    id: int
    platform: str
    platform_id: str
    author_username: str | None
    author_display_name: str | None
    author_followers: int
    author_verified: bool
    text_original: str
    text_cleaned: str
    created_at: datetime
    score: float | None = None
    judgment_label: str | None = None
    judgment_confidence: float | None = None
    draft_status: str | None = None


class LeadDetailResponse(LeadResponse):
    """Extended lead with full judgment, score, and draft info."""

    judgment_reasoning: str | None = None
    score_components: dict[str, object] | None = None
    draft_text: str | None = None
    draft_id: int | None = None


# ── Queue / Drafts ──


class DraftResponse(BaseModel):
    id: int
    normalized_post_id: int
    project_id: str
    text_generated: str
    text_final: str | None
    tone: str | None
    template_used: str | None
    model_id: str
    status: str
    created_at: datetime | None
    approved_at: datetime | None
    sent_at: datetime | None

    # Embedded lead context
    author_username: str | None = None
    author_display_name: str | None = None
    text_original: str | None = None
    score: float | None = None


class DraftEditRequest(BaseModel):
    text: str


class DraftRejectRequest(BaseModel):
    reason: str = ""


# ── Stats ──


class PipelineStatsResponse(BaseModel):
    collected: int
    judged: int
    relevant: int
    scored: int
    drafted: int
    approved: int
    sent: int
    outcomes: int


class TimelineBucket(BaseModel):
    period: str  # "2026-02-24", "2026-W09", etc.
    collected: int = 0
    judged: int = 0
    drafted: int = 0
    sent: int = 0


class OutcomeBreakdown(BaseModel):
    outcome_type: str
    count: int


# ── Analytics ──


class ScoreDistributionBucket(BaseModel):
    bucket_min: float
    bucket_max: float
    count: int


class QueryPerformanceRow(BaseModel):
    query_label: str
    total_leads: int
    avg_score: float
    relevant_pct: float


class ConversionFunnelStep(BaseModel):
    stage: str
    count: int


# ── Experiments ──


class ExperimentResponse(BaseModel):
    id: int
    experiment_id: str
    project_id: str | None
    primary_model: str
    canary_model: str
    canary_pct: float
    status: str
    started_at: datetime | None
    ended_at: datetime | None


class ExperimentResultsResponse(BaseModel):
    experiment_id: str
    primary_count: int
    canary_count: int
    primary_avg_latency_ms: float | None
    canary_avg_latency_ms: float | None


class ExperimentCreateRequest(BaseModel):
    experiment_id: str
    project_id: str | None = None
    primary_model: str
    canary_model: str
    canary_pct: float = 0.1


class SendPreviewItem(BaseModel):
    draft_id: int
    normalized_post_id: int
    text_final: str
    author_username: str | None
    platform: str
    platform_id: str


class SendResult(BaseModel):
    sent_count: int
    failed_count: int
    draft_ids: list[int]


class PersonaEffectivenessRow(BaseModel):
    tone: str
    template_used: str | None
    total_drafts: int
    approved_count: int
    rejected_count: int
    approval_rate: float

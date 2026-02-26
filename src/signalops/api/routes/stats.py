"""Pipeline statistics endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import ColumnElement, func
from sqlalchemy.orm import Session

from signalops.api.auth import require_api_key
from signalops.api.deps import get_db
from signalops.api.schemas import (
    OutcomeBreakdown,
    PipelineStatsResponse,
    TimelineBucket,
)
from signalops.storage.database import (
    Draft,
    DraftStatus,
    Judgment,
    JudgmentLabel,
    NormalizedPost,
    Outcome,
    RawPost,
    Score,
)

router = APIRouter()


@router.get("", response_model=PipelineStatsResponse)
def pipeline_stats(
    project_id: str | None = Query(None),
    db: Session = Depends(get_db),
    _api_key: str | None = Depends(require_api_key),
) -> PipelineStatsResponse:
    """Overall pipeline statistics."""

    def _count(model: type, extra_filter: ColumnElement[bool] | None = None) -> int:
        q = db.query(func.count()).select_from(model)
        if project_id and hasattr(model, "project_id"):
            q = q.filter(model.project_id == project_id)
        if extra_filter is not None:
            q = q.filter(extra_filter)
        result = q.scalar()
        return int(result) if result else 0

    return PipelineStatsResponse(
        collected=_count(RawPost),
        judged=_count(Judgment),
        relevant=_count(Judgment, Judgment.label == JudgmentLabel.RELEVANT),
        scored=_count(Score),
        drafted=_count(Draft),
        approved=_count(Draft, Draft.status == DraftStatus.APPROVED),
        sent=_count(Draft, Draft.status == DraftStatus.SENT),
        outcomes=_count(Outcome),
    )


@router.get("/timeline", response_model=list[TimelineBucket])
def stats_timeline(
    project_id: str | None = Query(None),
    granularity: str = Query("daily"),
    db: Session = Depends(get_db),
    _api_key: str | None = Depends(require_api_key),
) -> list[TimelineBucket]:
    """Stats over time in daily buckets."""
    # SQLite date formatting
    if granularity == "weekly":
        date_fmt = "%Y-W%W"
    elif granularity == "monthly":
        date_fmt = "%Y-%m"
    else:
        date_fmt = "%Y-%m-%d"

    # Collected per period
    collected_q = db.query(
        func.strftime(date_fmt, NormalizedPost.created_at).label("period"),
        func.count().label("cnt"),
    ).group_by("period")
    if project_id:
        collected_q = collected_q.filter(NormalizedPost.project_id == project_id)

    buckets: dict[str, TimelineBucket] = {}
    for row in collected_q.all():
        period = str(row.period) if row.period else "unknown"
        buckets[period] = TimelineBucket(period=period, collected=int(row.cnt))

    return sorted(buckets.values(), key=lambda b: b.period)


@router.get("/outcomes", response_model=list[OutcomeBreakdown])
def outcome_breakdown(
    project_id: str | None = Query(None),
    db: Session = Depends(get_db),
    _api_key: str | None = Depends(require_api_key),
) -> list[OutcomeBreakdown]:
    """Outcome type breakdown."""
    query = db.query(
        Outcome.outcome_type,
        func.count().label("cnt"),
    ).group_by(Outcome.outcome_type)
    if project_id:
        query = query.filter(Outcome.project_id == project_id)

    return [
        OutcomeBreakdown(
            outcome_type=(
                row.outcome_type.value
                if hasattr(row.outcome_type, "value")
                else str(row.outcome_type)
            ),
            count=int(row.cnt),
        )
        for row in query.all()
    ]

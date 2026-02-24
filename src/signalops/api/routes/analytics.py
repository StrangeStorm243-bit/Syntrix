"""Analytics endpoints for lead scoring and pipeline performance."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import ColumnElement, case, func
from sqlalchemy.orm import Session

from signalops.api.auth import require_api_key
from signalops.api.deps import get_db
from signalops.api.schemas import (
    ConversionFunnelStep,
    PersonaEffectivenessRow,
    QueryPerformanceRow,
    ScoreDistributionBucket,
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


@router.get("/score-distribution", response_model=list[ScoreDistributionBucket])
def score_distribution(
    project_id: str | None = Query(None),
    bucket_size: float = Query(10.0, gt=0),
    db: Session = Depends(get_db),
    _api_key: str = Depends(require_api_key),
) -> list[ScoreDistributionBucket]:
    """Histogram of lead scores."""
    query = db.query(Score.total_score)
    if project_id:
        query = query.filter(Score.project_id == project_id)

    scores = [float(row.total_score) for row in query.all()]
    if not scores:
        return []

    buckets: dict[float, int] = {}
    for s in scores:
        bucket_min = (s // bucket_size) * bucket_size
        buckets[bucket_min] = buckets.get(bucket_min, 0) + 1

    return sorted(
        [
            ScoreDistributionBucket(
                bucket_min=k,
                bucket_max=k + bucket_size,
                count=v,
            )
            for k, v in buckets.items()
        ],
        key=lambda b: b.bucket_min,
    )


@router.get("/judge-accuracy")
def judge_accuracy(
    project_id: str | None = Query(None),
    db: Session = Depends(get_db),
    _api_key: str = Depends(require_api_key),
) -> dict[str, object]:
    """Precision/recall from human corrections."""
    query = db.query(Judgment).filter(Judgment.human_label.isnot(None))
    if project_id:
        query = query.filter(Judgment.project_id == project_id)

    judgments = query.all()
    total = len(judgments)
    if total == 0:
        return {"total_corrections": 0, "agreement_rate": None}

    agreements = sum(1 for j in judgments if j.label == j.human_label)
    return {
        "total_corrections": total,
        "agreement_rate": round(agreements / total, 4),
    }


@router.get("/query-performance", response_model=list[QueryPerformanceRow])
def query_performance(
    project_id: str | None = Query(None),
    db: Session = Depends(get_db),
    _api_key: str = Depends(require_api_key),
) -> list[QueryPerformanceRow]:
    """Which queries produce the best leads."""
    query = (
        db.query(
            RawPost.query_used,
            func.count(RawPost.id).label("total"),
            func.avg(Score.total_score).label("avg_score"),
            func.sum(
                case(
                    (Judgment.label == JudgmentLabel.RELEVANT, 1),
                    else_=0,
                )
            ).label("relevant_count"),
        )
        .outerjoin(NormalizedPost, NormalizedPost.raw_post_id == RawPost.id)
        .outerjoin(Score, Score.normalized_post_id == NormalizedPost.id)
        .outerjoin(Judgment, Judgment.normalized_post_id == NormalizedPost.id)
        .group_by(RawPost.query_used)
    )

    if project_id:
        query = query.filter(RawPost.project_id == project_id)

    results: list[QueryPerformanceRow] = []
    for row in query.all():
        total = int(row.total) if row.total else 0
        relevant = int(row.relevant_count) if row.relevant_count else 0
        results.append(
            QueryPerformanceRow(
                query_label=str(row.query_used or "unknown"),
                total_leads=total,
                avg_score=round(float(row.avg_score or 0), 2),
                relevant_pct=round(relevant / total * 100, 1) if total > 0 else 0.0,
            )
        )
    return results


@router.get("/persona-effectiveness", response_model=list[PersonaEffectivenessRow])
def persona_effectiveness(
    project_id: str | None = Query(None),
    db: Session = Depends(get_db),
    _api_key: str = Depends(require_api_key),
) -> list[PersonaEffectivenessRow]:
    """Draft approval rates by persona (tone / template)."""
    query = db.query(
        Draft.tone,
        Draft.template_used,
        func.count(Draft.id).label("total"),
        func.sum(
            case(
                (Draft.status.in_([DraftStatus.APPROVED, DraftStatus.EDITED]), 1),
                else_=0,
            )
        ).label("approved"),
        func.sum(
            case(
                (Draft.status == DraftStatus.REJECTED, 1),
                else_=0,
            )
        ).label("rejected"),
    ).group_by(Draft.tone, Draft.template_used)

    if project_id:
        query = query.filter(Draft.project_id == project_id)

    results: list[PersonaEffectivenessRow] = []
    for row in query.all():
        total = int(row.total) if row.total else 0
        approved = int(row.approved) if row.approved else 0
        rejected = int(row.rejected) if row.rejected else 0
        results.append(
            PersonaEffectivenessRow(
                tone=str(row.tone or "default"),
                template_used=str(row.template_used) if row.template_used else None,
                total_drafts=total,
                approved_count=approved,
                rejected_count=rejected,
                approval_rate=round(approved / total * 100, 1) if total > 0 else 0.0,
            )
        )
    return results


@router.get("/conversion-funnel", response_model=list[ConversionFunnelStep])
def conversion_funnel(
    project_id: str | None = Query(None),
    db: Session = Depends(get_db),
    _api_key: str = Depends(require_api_key),
) -> list[ConversionFunnelStep]:
    """Pipeline conversion funnel: Collected -> Judged -> Scored -> Drafted -> Sent -> Outcome."""

    def _count(model: type, extra_filter: ColumnElement[bool] | None = None) -> int:
        q = db.query(func.count()).select_from(model)
        if project_id and hasattr(model, "project_id"):
            q = q.filter(model.project_id == project_id)
        if extra_filter is not None:
            q = q.filter(extra_filter)
        result = q.scalar()
        return int(result) if result else 0

    return [
        ConversionFunnelStep(stage="Collected", count=_count(RawPost)),
        ConversionFunnelStep(stage="Judged", count=_count(Judgment)),
        ConversionFunnelStep(stage="Scored", count=_count(Score)),
        ConversionFunnelStep(stage="Drafted", count=_count(Draft)),
        ConversionFunnelStep(stage="Sent", count=_count(Draft, Draft.status == DraftStatus.SENT)),
        ConversionFunnelStep(stage="Outcome", count=_count(Outcome)),
    ]

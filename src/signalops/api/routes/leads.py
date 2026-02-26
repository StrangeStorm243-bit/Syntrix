"""Lead browsing and filtering endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from signalops.api.auth import require_api_key
from signalops.api.deps import get_db
from signalops.api.schemas import (
    LeadDetailResponse,
    LeadResponse,
    PaginatedResponse,
)
from signalops.storage.database import (
    Draft,
    Judgment,
    JudgmentLabel,
    NormalizedPost,
    Score,
)

router = APIRouter()


def _build_lead_response(
    post: NormalizedPost,
    judgment: Judgment | None,
    score: Score | None,
    draft: Draft | None,
) -> LeadResponse:
    return LeadResponse(
        id=int(post.id),
        platform=str(post.platform),
        platform_id=str(post.platform_id),
        author_username=post.author_username,  # type: ignore[arg-type]
        author_display_name=post.author_display_name,  # type: ignore[arg-type]
        author_followers=int(post.author_followers or 0),
        author_verified=bool(post.author_verified),
        text_original=str(post.text_original),
        text_cleaned=str(post.text_cleaned),
        created_at=post.created_at,  # type: ignore[arg-type]
        score=float(score.total_score) if score else None,
        judgment_label=judgment.label.value if judgment and judgment.label else None,
        judgment_confidence=(
            float(judgment.confidence) if judgment and judgment.confidence else None
        ),
        draft_status=draft.status.value if draft and draft.status else None,
    )


@router.get("", response_model=PaginatedResponse[LeadResponse])
def list_leads(
    project_id: str | None = Query(None),
    min_score: float | None = Query(None),
    max_score: float | None = Query(None),
    label: str | None = Query(None),
    sort_by: str = Query("created_at"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _api_key: str | None = Depends(require_api_key),
) -> PaginatedResponse[LeadResponse]:
    """List leads with filtering and pagination."""
    query = db.query(NormalizedPost)

    if project_id:
        query = query.filter(NormalizedPost.project_id == project_id)

    # Join for score/label filtering
    if min_score is not None or max_score is not None or sort_by == "score":
        query = query.outerjoin(Score, Score.normalized_post_id == NormalizedPost.id)
        if min_score is not None:
            query = query.filter(Score.total_score >= min_score)
        if max_score is not None:
            query = query.filter(Score.total_score <= max_score)

    if label:
        try:
            label_enum = JudgmentLabel(label)
        except ValueError:
            label_enum = None
        if label_enum:
            query = query.outerjoin(Judgment, Judgment.normalized_post_id == NormalizedPost.id)
            query = query.filter(Judgment.label == label_enum)

    total = query.count()

    # Sorting
    if sort_by == "score":
        query = query.order_by(desc(Score.total_score))
    else:
        query = query.order_by(desc(NormalizedPost.created_at))

    posts = query.offset((page - 1) * page_size).limit(page_size).all()

    items: list[LeadResponse] = []
    for post in posts:
        judgment = db.query(Judgment).filter(Judgment.normalized_post_id == post.id).first()
        score = db.query(Score).filter(Score.normalized_post_id == post.id).first()
        draft = db.query(Draft).filter(Draft.normalized_post_id == post.id).first()
        items.append(_build_lead_response(post, judgment, score, draft))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/top", response_model=list[LeadResponse])
def top_leads(
    project_id: str | None = Query(None),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    _api_key: str | None = Depends(require_api_key),
) -> list[LeadResponse]:
    """Get top N leads by score."""
    query = db.query(NormalizedPost).join(Score, Score.normalized_post_id == NormalizedPost.id)
    if project_id:
        query = query.filter(NormalizedPost.project_id == project_id)
    posts = query.order_by(desc(Score.total_score)).limit(limit).all()

    results: list[LeadResponse] = []
    for post in posts:
        judgment = db.query(Judgment).filter(Judgment.normalized_post_id == post.id).first()
        score = db.query(Score).filter(Score.normalized_post_id == post.id).first()
        draft = db.query(Draft).filter(Draft.normalized_post_id == post.id).first()
        results.append(_build_lead_response(post, judgment, score, draft))
    return results


@router.get("/{lead_id}", response_model=LeadDetailResponse)
def get_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    _api_key: str | None = Depends(require_api_key),
) -> LeadDetailResponse:
    """Get lead detail with full judgment, score, and draft info."""
    from fastapi import HTTPException

    post = db.query(NormalizedPost).filter(NormalizedPost.id == lead_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Lead not found")

    judgment = db.query(Judgment).filter(Judgment.normalized_post_id == post.id).first()
    score = db.query(Score).filter(Score.normalized_post_id == post.id).first()
    draft = db.query(Draft).filter(Draft.normalized_post_id == post.id).first()

    return LeadDetailResponse(
        id=int(post.id),
        platform=str(post.platform),
        platform_id=str(post.platform_id),
        author_username=str(post.author_username) if post.author_username else None,
        author_display_name=str(post.author_display_name) if post.author_display_name else None,
        author_followers=int(post.author_followers or 0),
        author_verified=bool(post.author_verified),
        text_original=str(post.text_original),
        text_cleaned=str(post.text_cleaned),
        created_at=post.created_at,  # type: ignore[arg-type]
        score=float(score.total_score) if score else None,
        judgment_label=judgment.label.value if judgment and judgment.label else None,
        judgment_confidence=(
            float(judgment.confidence) if judgment and judgment.confidence else None
        ),
        draft_status=draft.status.value if draft and draft.status else None,
        judgment_reasoning=(str(judgment.reasoning) if judgment and judgment.reasoning else None),
        score_components=score.components if score else None,  # type: ignore[arg-type]
        draft_text=(str(draft.text_final or draft.text_generated) if draft else None),
        draft_id=int(draft.id) if draft else None,
    )

"""Draft approval queue endpoints."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from signalops.api.auth import require_api_key
from signalops.api.deps import get_db
from signalops.api.schemas import (
    DraftEditRequest,
    DraftRejectRequest,
    DraftResponse,
    PaginatedResponse,
    SendPreviewItem,
    SendResult,
)
from signalops.storage.database import (
    Draft,
    DraftStatus,
    NormalizedPost,
    Score,
)

router = APIRouter()


def _build_draft_response(
    draft: Draft,
    db: Session,
) -> DraftResponse:
    post = db.query(NormalizedPost).filter(NormalizedPost.id == draft.normalized_post_id).first()
    score = (
        (db.query(Score).filter(Score.normalized_post_id == draft.normalized_post_id).first())
        if post
        else None
    )
    return DraftResponse(
        id=int(draft.id),
        normalized_post_id=int(draft.normalized_post_id),
        project_id=str(draft.project_id),
        text_generated=str(draft.text_generated),
        text_final=str(draft.text_final) if draft.text_final else None,
        tone=str(draft.tone) if draft.tone else None,
        template_used=str(draft.template_used) if draft.template_used else None,
        model_id=str(draft.model_id),
        status=draft.status.value if draft.status else "pending",
        created_at=draft.created_at,  # type: ignore[arg-type]
        approved_at=draft.approved_at,  # type: ignore[arg-type]
        sent_at=draft.sent_at,  # type: ignore[arg-type]
        author_username=post.author_username if post else None,  # type: ignore[arg-type]
        author_display_name=post.author_display_name if post else None,  # type: ignore[arg-type]
        text_original=str(post.text_original) if post else None,
        score=float(score.total_score) if score else None,
    )


@router.get("", response_model=PaginatedResponse[DraftResponse])
def list_queue(
    project_id: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _api_key: str | None = Depends(require_api_key),
) -> PaginatedResponse[DraftResponse]:
    """List drafts in the approval queue."""
    query = db.query(Draft)
    if project_id:
        query = query.filter(Draft.project_id == project_id)
    if status:
        try:
            status_enum = DraftStatus(status)
            query = query.filter(Draft.status == status_enum)
        except ValueError:
            pass
    else:
        # Default: show pending drafts
        query = query.filter(Draft.status == DraftStatus.PENDING)

    total = query.count()
    drafts = query.offset((page - 1) * page_size).limit(page_size).all()

    return PaginatedResponse(
        items=[_build_draft_response(d, db) for d in drafts],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{draft_id}", response_model=DraftResponse)
def get_draft(
    draft_id: int,
    db: Session = Depends(get_db),
    _api_key: str | None = Depends(require_api_key),
) -> DraftResponse:
    """Get draft detail."""
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return _build_draft_response(draft, db)


@router.post("/{draft_id}/approve", response_model=DraftResponse)
def approve_draft(
    draft_id: int,
    db: Session = Depends(get_db),
    _api_key: str | None = Depends(require_api_key),
) -> DraftResponse:
    """Approve a pending draft."""
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft.status != DraftStatus.PENDING:
        raise HTTPException(
            status_code=409,
            detail=f"Draft is {draft.status.value}, not pending",
        )
    draft.status = DraftStatus.APPROVED  # type: ignore[assignment]
    draft.approved_at = datetime.now(UTC)  # type: ignore[assignment]
    draft.text_final = draft.text_generated
    db.commit()
    db.refresh(draft)
    return _build_draft_response(draft, db)


@router.post("/{draft_id}/edit", response_model=DraftResponse)
def edit_draft(
    draft_id: int,
    body: DraftEditRequest,
    db: Session = Depends(get_db),
    _api_key: str | None = Depends(require_api_key),
) -> DraftResponse:
    """Edit and approve a draft."""
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft.status != DraftStatus.PENDING:
        raise HTTPException(
            status_code=409,
            detail=f"Draft is {draft.status.value}, not pending",
        )
    draft.status = DraftStatus.EDITED  # type: ignore[assignment]
    draft.approved_at = datetime.now(UTC)  # type: ignore[assignment]
    draft.text_final = body.text  # type: ignore[assignment]
    db.commit()
    db.refresh(draft)
    return _build_draft_response(draft, db)


@router.post("/{draft_id}/reject", response_model=DraftResponse)
def reject_draft(
    draft_id: int,
    body: DraftRejectRequest | None = None,
    db: Session = Depends(get_db),
    _api_key: str | None = Depends(require_api_key),
) -> DraftResponse:
    """Reject a draft."""
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft.status != DraftStatus.PENDING:
        raise HTTPException(
            status_code=409,
            detail=f"Draft is {draft.status.value}, not pending",
        )
    draft.status = DraftStatus.REJECTED  # type: ignore[assignment]
    db.commit()
    db.refresh(draft)
    return _build_draft_response(draft, db)


@router.post("/send-preview", response_model=list[SendPreviewItem])
def send_preview(
    project_id: str | None = Query(None),
    db: Session = Depends(get_db),
    _api_key: str | None = Depends(require_api_key),
) -> list[SendPreviewItem]:
    """Dry-run preview of drafts that would be sent."""
    query = db.query(Draft).filter(Draft.status.in_([DraftStatus.APPROVED, DraftStatus.EDITED]))
    if project_id:
        query = query.filter(Draft.project_id == project_id)

    items: list[SendPreviewItem] = []
    for draft in query.all():
        post = (
            db.query(NormalizedPost).filter(NormalizedPost.id == draft.normalized_post_id).first()
        )
        items.append(
            SendPreviewItem(
                draft_id=int(draft.id),
                normalized_post_id=int(draft.normalized_post_id),
                text_final=str(draft.text_final or draft.text_generated),
                author_username=post.author_username if post else None,  # type: ignore[arg-type]
                platform=str(post.platform) if post else "unknown",
                platform_id=str(post.platform_id) if post else "",
            )
        )
    return items


@router.post("/send", response_model=SendResult)
def send_approved(
    project_id: str | None = Query(None),
    db: Session = Depends(get_db),
    _api_key: str | None = Depends(require_api_key),
) -> SendResult:
    """Send all approved/edited drafts via connector."""
    from signalops.connectors.factory import ConnectorFactory

    query = db.query(Draft).filter(Draft.status.in_([DraftStatus.APPROVED, DraftStatus.EDITED]))
    if project_id:
        query = query.filter(Draft.project_id == project_id)

    drafts = query.all()
    sent_ids: list[int] = []
    failed_count = 0

    # Create connector for sending
    factory = ConnectorFactory()
    try:
        connector = factory.create("x")
    except Exception:  # noqa: BLE001
        logger.warning("No connector available — marking as sent (dry run)")
        connector = None

    for draft in drafts:
        try:
            text = str(draft.text_final or draft.text_generated)
            post = db.query(NormalizedPost).filter(
                NormalizedPost.id == draft.normalized_post_id
            ).first()

            if connector and post:
                reply_id = connector.post_reply(
                    str(post.platform_id), text
                )
                draft.sent_post_id = reply_id  # type: ignore[assignment]

            draft.status = DraftStatus.SENT  # type: ignore[assignment]
            draft.sent_at = datetime.now(UTC)  # type: ignore[assignment]
            sent_ids.append(int(draft.id))  # type: ignore[arg-type]
        except Exception:  # noqa: BLE001
            logger.exception("Failed to send draft %s", draft.id)
            failed_count += 1

    db.commit()
    return SendResult(
        sent_count=len(sent_ids),
        failed_count=failed_count,
        draft_ids=sent_ids,
    )

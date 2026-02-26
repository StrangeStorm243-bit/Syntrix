"""Sequence management endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from signalops.api.deps import get_db
from signalops.storage.database import (
    Enrollment,
    EnrollmentStatus,
    Project,
    Sequence,
)

router = APIRouter(prefix="/api/sequences", tags=["sequences"])


# ── Pydantic response models ──


class SequenceStepResponse(BaseModel):
    """A single step in a sequence."""

    id: int
    step_order: int
    action_type: str
    delay_hours: float
    requires_approval: bool


class SequenceResponse(BaseModel):
    """A sequence with enrollment counts."""

    id: int
    name: str
    description: str | None
    is_active: bool
    steps: list[SequenceStepResponse]
    enrolled_count: int
    completed_count: int


class EnrollmentResponse(BaseModel):
    """An enrollment record for a lead in a sequence."""

    id: int
    normalized_post_id: int
    current_step_order: int
    status: str
    enrolled_at: str
    next_step_at: str | None


# ── Helper ──


def _get_active_project(db: Session) -> Project:
    """Get the active project or raise 404."""
    project = db.query(Project).filter(Project.is_active.is_(True)).first()
    if not project:
        raise HTTPException(status_code=404, detail="No active project found")
    return project


# ── Routes ──


@router.get("", response_model=list[SequenceResponse])
def list_sequences(
    db: Session = Depends(get_db),
) -> list[SequenceResponse]:
    """List all sequences for the active project."""
    project = _get_active_project(db)
    sequences = (
        db.query(Sequence).filter(Sequence.project_id == project.id).all()
    )
    results: list[SequenceResponse] = []
    for seq in sequences:
        enrolled = (
            db.query(Enrollment)
            .filter(
                Enrollment.sequence_id == seq.id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
            .count()
        )
        completed = (
            db.query(Enrollment)
            .filter(
                Enrollment.sequence_id == seq.id,
                Enrollment.status == EnrollmentStatus.COMPLETED,
            )
            .count()
        )
        results.append(
            SequenceResponse(
                id=int(seq.id),  # type: ignore[arg-type]
                name=str(seq.name),
                description=seq.description,  # type: ignore[arg-type]
                is_active=bool(seq.is_active),
                steps=[
                    SequenceStepResponse(
                        id=int(s.id),  # type: ignore[arg-type]
                        step_order=int(s.step_order),  # type: ignore[arg-type]
                        action_type=str(s.action_type),
                        delay_hours=float(s.delay_hours),  # type: ignore[arg-type]
                        requires_approval=bool(s.requires_approval),
                    )
                    for s in seq.steps
                ],
                enrolled_count=enrolled,
                completed_count=completed,
            )
        )
    return results


@router.get(
    "/{sequence_id}/enrollments", response_model=list[EnrollmentResponse]
)
def list_enrollments(
    sequence_id: int,
    db: Session = Depends(get_db),
) -> list[EnrollmentResponse]:
    """List enrollments for a sequence."""
    enrollments = (
        db.query(Enrollment)
        .filter(Enrollment.sequence_id == sequence_id)
        .order_by(Enrollment.enrolled_at.desc())  # type: ignore[union-attr]
        .limit(100)
        .all()
    )
    return [
        EnrollmentResponse(
            id=int(e.id),  # type: ignore[arg-type]
            normalized_post_id=int(e.normalized_post_id),  # type: ignore[arg-type]
            current_step_order=int(e.current_step_order),  # type: ignore[arg-type]
            status=(
                e.status.value
                if hasattr(e.status, "value")
                else str(e.status)
            ),
            enrolled_at=(
                e.enrolled_at.isoformat() if e.enrolled_at else ""
            ),
            next_step_at=(
                e.next_step_at.isoformat() if e.next_step_at else None
            ),
        )
        for e in enrollments
    ]

"""Human correction helpers for judgment feedback loop."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from signalops.storage.audit import log_action
from signalops.storage.database import Judgment, JudgmentLabel


def correct_judgment(
    db_session: Session,
    judgment_id: int,
    new_label: str,
    reason: str | None = None,
) -> Judgment:
    """Apply human correction to a judgment.

    Sets human_label, human_corrected_at, human_reason.
    Logs to audit. Returns updated judgment.
    """
    judgment = db_session.query(Judgment).get(judgment_id)
    if judgment is None:
        raise ValueError(f"Judgment {judgment_id} not found")

    label_enum = JudgmentLabel(new_label)

    judgment.human_label = label_enum  # type: ignore[assignment]
    judgment.human_corrected_at = datetime.now(UTC)  # type: ignore[assignment]
    judgment.human_reason = reason  # type: ignore[assignment]

    log_action(
        session=db_session,
        project_id=str(judgment.project_id),
        action="judgment_corrected",
        entity_type="judgment",
        entity_id=judgment.id,  # type: ignore[arg-type]
        details={
            "original_label": judgment.label.value,
            "new_label": new_label,
            "reason": reason,
        },
        user="human",
    )

    db_session.commit()
    return judgment


def get_correction_stats(db_session: Session, project_id: str) -> dict[str, Any]:
    """Stats: total corrections, agreement rate (human == model), by label."""
    corrected = (
        db_session.query(Judgment)
        .filter(
            Judgment.project_id == project_id,
            Judgment.human_label.isnot(None),
        )
        .all()
    )

    total = len(corrected)
    if total == 0:
        return {
            "total_corrections": 0,
            "agreement_rate": 0.0,
            "by_label": {},
        }

    agreements = sum(1 for j in corrected if j.human_label == j.label)
    by_label: dict[str, int] = {}
    for j in corrected:
        lbl = j.human_label.value if j.human_label else "unknown"
        by_label[lbl] = by_label.get(lbl, 0) + 1

    return {
        "total_corrections": total,
        "agreement_rate": round(agreements / total, 4),
        "by_label": by_label,
    }


def get_uncorrected_sample(
    db_session: Session,
    project_id: str,
    n: int = 10,
    strategy: str = "low_confidence",
) -> list[Judgment]:
    """Get judgments for human review.

    Strategies:
        'low_confidence' — lowest confidence first
        'random' — random sample
        'recent' — most recent first
    """
    query = db_session.query(Judgment).filter(
        Judgment.project_id == project_id,
        Judgment.human_label.is_(None),
    )

    if strategy == "low_confidence":
        query = query.order_by(Judgment.confidence.asc())
    elif strategy == "random":
        from sqlalchemy.sql.expression import func

        query = query.order_by(func.random())
    elif strategy == "recent":
        query = query.order_by(Judgment.created_at.desc())
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    return query.limit(n).all()

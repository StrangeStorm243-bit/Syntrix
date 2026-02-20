"""Append-only audit logger for all pipeline actions."""

from sqlalchemy.orm import Session

from .database import AuditLog


def log_action(
    session: Session,
    project_id: str,
    action: str,
    entity_type: str | None = None,
    entity_id: int | None = None,
    details: dict | None = None,
    user: str = "system",
) -> AuditLog:
    """Create an audit log entry and commit."""
    entry = AuditLog(
        project_id=project_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        user=user,
    )
    session.add(entry)
    session.commit()
    return entry


def get_recent_actions(
    session: Session, project_id: str, limit: int = 50
) -> list[AuditLog]:
    """Return most recent audit entries for a project."""
    return (
        session.query(AuditLog)
        .filter(AuditLog.project_id == project_id)
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
        .all()
    )

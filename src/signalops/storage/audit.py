"""Stub — real implementation on feat/data branch."""
from .database import AuditLog


def log_action(session, project_id, action, entity_type=None, entity_id=None, details=None, user="system"):
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


def get_recent_actions(session, project_id, limit=50):
    return (
        session.query(AuditLog)
        .filter(AuditLog.project_id == project_id)
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
        .all()
    )

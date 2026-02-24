"""FastAPI dependency injection for database sessions, config, and auth."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

from fastapi import Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from signalops.api.auth import require_api_key
from signalops.config.loader import load_project
from signalops.config.schema import ProjectConfig
from signalops.storage.database import Project, get_session


def get_db(request: Request) -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session scoped to the request."""
    engine = request.app.state.engine
    session = get_session(engine)
    try:
        yield session
    finally:
        session.close()


def get_current_project(
    project_id: str | None = Query(None),
    db: Session = Depends(get_db),
    _api_key: str = Depends(require_api_key),
) -> Project:
    """Resolve the active project from query param or fall back to the single active one."""
    if project_id:
        project = db.query(Project).filter(Project.id == project_id).first()
    else:
        project = db.query(Project).filter(Project.is_active.is_(True)).first()

    if not project:
        raise HTTPException(status_code=404, detail="No active project found")
    return project


def get_config(
    project: Project = Depends(get_current_project),
) -> ProjectConfig:
    """Load the ProjectConfig for the current project."""
    config_path: Any = project.config_path
    return load_project(str(config_path))

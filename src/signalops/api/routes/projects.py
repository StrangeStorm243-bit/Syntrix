"""Project management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from signalops.api.auth import require_api_key
from signalops.api.deps import get_db
from signalops.api.schemas import ProjectConfigResponse, ProjectResponse
from signalops.config.loader import load_project
from signalops.storage.database import Project

router = APIRouter()


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    db: Session = Depends(get_db),
    _api_key: str | None = Depends(require_api_key),
) -> list[ProjectResponse]:
    """List all projects."""
    projects = db.query(Project).all()
    return [
        ProjectResponse(
            id=str(p.id),
            name=str(p.name),
            config_path=str(p.config_path),
            is_active=bool(p.is_active) if p.is_active is not None else None,
            created_at=p.created_at,  # type: ignore[arg-type]
            updated_at=p.updated_at,  # type: ignore[arg-type]
        )
        for p in projects
    ]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    _api_key: str | None = Depends(require_api_key),
) -> ProjectResponse:
    """Get project details."""
    from fastapi import HTTPException

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse(
        id=str(project.id),
        name=str(project.name),
        config_path=str(project.config_path),
        is_active=bool(project.is_active) if project.is_active is not None else None,
        created_at=project.created_at,  # type: ignore[arg-type]
        updated_at=project.updated_at,  # type: ignore[arg-type]
    )


@router.get("/{project_id}/config", response_model=ProjectConfigResponse)
def get_project_config(
    project_id: str,
    db: Session = Depends(get_db),
    _api_key: str | None = Depends(require_api_key),
) -> ProjectConfigResponse:
    """Get sanitized project config (no secrets)."""
    from fastapi import HTTPException

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    cfg = load_project(str(project.config_path))
    return ProjectConfigResponse(
        project_id=cfg.project_id,
        project_name=cfg.project_name,
        description=cfg.description,
        queries=[q.model_dump() for q in cfg.queries],
        scoring=cfg.scoring.model_dump(),
        persona=cfg.persona.model_dump(),
    )


@router.post("/{project_id}/activate", response_model=ProjectResponse)
def activate_project(
    project_id: str,
    db: Session = Depends(get_db),
    _api_key: str | None = Depends(require_api_key),
) -> ProjectResponse:
    """Set a project as the active project (deactivates others)."""
    from fastapi import HTTPException

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Deactivate all, then activate target
    db.query(Project).update({Project.is_active: False})
    project.is_active = True  # type: ignore[assignment]
    db.commit()
    db.refresh(project)

    return ProjectResponse(
        id=str(project.id),
        name=str(project.name),
        config_path=str(project.config_path),
        is_active=bool(project.is_active) if project.is_active is not None else None,
        created_at=project.created_at,  # type: ignore[arg-type]
        updated_at=project.updated_at,  # type: ignore[arg-type]
    )

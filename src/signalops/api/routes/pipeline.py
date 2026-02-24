"""Pipeline execution endpoints with WebSocket progress."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from signalops.api.auth import require_api_key
from signalops.api.deps import get_db
from signalops.api.websocket import manager
from signalops.storage.database import Project

logger = logging.getLogger(__name__)

router = APIRouter()


async def _broadcast_progress(stage: str, progress: float, detail: str) -> None:
    """Broadcast pipeline progress to all WebSocket clients."""
    await manager.broadcast(
        {"type": "pipeline_progress", "stage": stage, "progress": progress, "detail": detail}
    )


def _run_pipeline_sync(project_id: str, db_url: str) -> None:
    """Run the pipeline synchronously in a background thread.

    Imports orchestrator lazily to avoid circular deps.
    This is a placeholder — the actual orchestrator integration
    will be wired during Phase 3 integration.
    """
    logger.info("Pipeline run started for project %s", project_id)
    # TODO: Wire to PipelineOrchestrator with progress_callback
    # The orchestrator will call _broadcast_progress at each stage
    logger.info("Pipeline run completed for project %s", project_id)


@router.post("/run")
async def run_pipeline(
    project_id: str | None = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    _api_key: str = Depends(require_api_key),
) -> dict[str, Any]:
    """Trigger a pipeline run in the background."""
    # Resolve project
    if project_id:
        project = db.query(Project).filter(Project.id == project_id).first()
    else:
        project = db.query(Project).filter(Project.is_active.is_(True)).first()

    if not project:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="No active project found")

    # Broadcast start
    await _broadcast_progress("starting", 0.0, f"Pipeline starting for {project.id}")

    # Get db_url from engine
    bind = db.get_bind()
    db_url = str(bind.url)  # type: ignore[union-attr]

    # Run in background
    background_tasks.add_task(_run_pipeline_sync, str(project.id), db_url)

    return {"status": "started", "project_id": str(project.id)}

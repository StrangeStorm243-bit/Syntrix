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
    """Run the pipeline synchronously in a background thread."""
    from signalops.config.loader import load_project
    from signalops.connectors.factory import ConnectorFactory
    from signalops.models.draft_model import LLMDraftGenerator
    from signalops.models.judge_model import LLMPromptJudge
    from signalops.models.llm_gateway import LLMGateway
    from signalops.pipeline.orchestrator import PipelineOrchestrator
    from signalops.storage.database import get_engine, get_session

    logger.info("Pipeline run started for project %s", project_id)
    engine = get_engine(db_url)
    session = get_session(engine)
    try:
        # Load config from project's yaml path
        project = session.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.error("Project %s not found in database", project_id)
            return
        config = load_project(str(project.config_path))

        # Create connector (prefers twikit if env vars set, else X API)
        factory = ConnectorFactory()
        connector = factory.create("x", config)

        # Create LLM judge and drafter
        gateway = LLMGateway()
        judge_model = getattr(config.llm, "judge_model", "claude-sonnet-4-6")
        draft_model = getattr(config.llm, "draft_model", "claude-sonnet-4-6")
        judge = LLMPromptJudge(gateway=gateway, model=judge_model)
        drafter = LLMDraftGenerator(gateway=gateway, model=draft_model)

        orchestrator = PipelineOrchestrator(
            db_session=session,
            connector=connector,
            judge=judge,
            draft_generator=drafter,
        )
        results = orchestrator.run_all(config)
        logger.info("Pipeline completed for %s: %s", project_id, results)
    except Exception:
        logger.exception("Pipeline run failed for project %s", project_id)
    finally:
        session.close()
        engine.dispose()


@router.post("/run")
async def run_pipeline(
    project_id: str | None = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    _api_key: str | None = Depends(require_api_key),
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

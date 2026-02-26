"""FastAPI application factory for the SignalOps web dashboard."""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from signalops.api.routes.analytics import router as analytics_router
from signalops.api.routes.experiments import router as experiments_router
from signalops.api.routes.leads import router as leads_router
from signalops.api.routes.pipeline import router as pipeline_router
from signalops.api.routes.projects import router as projects_router
from signalops.api.routes.queue import router as queue_router
from signalops.api.routes.sequences import router as sequences_router
from signalops.api.routes.setup import router as setup_router
from signalops.api.routes.stats import router as stats_router
from signalops.storage.database import get_engine, init_db

logger = logging.getLogger(__name__)


def _tick_sequences(db_url: str) -> None:
    """Execute due sequence steps (called by APScheduler)."""
    try:
        from signalops.connectors.factory import ConnectorFactory
        from signalops.pipeline.sequence_engine import SequenceEngine
        from signalops.storage.database import get_engine as _get_engine
        from signalops.storage.database import get_session

        engine = _get_engine(db_url)
        session = get_session(engine)
        factory = ConnectorFactory()
        connector = factory.create("x")
        seq_engine = SequenceEngine(session, connector)
        count = seq_engine.execute_due_steps()
        if count:
            logger.info("Executed %d sequence steps", count)
        session.close()
        engine.dispose()
    except Exception:  # noqa: BLE001
        logger.debug("Sequence tick skipped — no connector or no due steps")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize DB engine on startup, dispose on shutdown."""
    db_url = os.environ.get("SIGNALOPS_DB_URL", "sqlite:///signalops.db")
    app.state.engine = get_engine(db_url)
    init_db(app.state.engine)

    # Start APScheduler for periodic pipeline runs (optional)
    scheduler: Any = None
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore[import-untyped]

        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            _tick_sequences,
            "interval",
            seconds=30,
            args=[db_url],
            id="sequence_tick",
        )
        scheduler.start()
        app.state.scheduler = scheduler
        logger.info("APScheduler started — sequence tick every 30s")
    except ImportError:
        logger.info("APScheduler not installed — no background scheduling")

    yield

    if scheduler is not None:
        scheduler.shutdown()
    app.state.engine.dispose()


def create_app(db_url: str | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="SignalOps API",
        version="0.3.0",
        lifespan=lifespan,
    )

    # CORS — allow Vite dev server and configurable origins
    allowed_origins = os.environ.get("SIGNALOPS_CORS_ORIGINS", "http://localhost:5173").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # If db_url passed directly (e.g. tests), override on state
    if db_url:

        @asynccontextmanager
        async def _test_lifespan(app: FastAPI) -> AsyncIterator[None]:
            app.state.engine = get_engine(db_url)
            yield
            app.state.engine.dispose()

        app.router.lifespan_context = _test_lifespan

    # Register routers
    app.include_router(projects_router, prefix="/api/projects", tags=["projects"])
    app.include_router(leads_router, prefix="/api/leads", tags=["leads"])
    app.include_router(queue_router, prefix="/api/queue", tags=["queue"])
    app.include_router(stats_router, prefix="/api/stats", tags=["stats"])
    app.include_router(analytics_router, prefix="/api/analytics", tags=["analytics"])
    app.include_router(experiments_router, prefix="/api/experiments", tags=["experiments"])
    app.include_router(pipeline_router, prefix="/api/pipeline", tags=["pipeline"])
    app.include_router(setup_router)
    app.include_router(sequences_router)

    # WebSocket endpoint
    from signalops.api.websocket import websocket_endpoint

    app.websocket("/ws/pipeline")(websocket_endpoint)

    return app


def main() -> None:
    """Run the SignalOps API server (entry point for signalops-api command)."""
    import uvicorn

    host = os.environ.get("SIGNALOPS_API_HOST", "0.0.0.0")
    port = int(os.environ.get("SIGNALOPS_API_PORT", "8400"))
    uvicorn.run(
        "signalops.api.app:create_app",
        factory=True,
        host=host,
        port=port,
        reload=True,
    )

"""A/B experiment endpoints (reads from T2's tables, but API layer is T1)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from signalops.api.auth import require_api_key
from signalops.api.deps import get_db
from signalops.api.schemas import ExperimentResponse, ExperimentResultsResponse

router = APIRouter()

# NOTE: These endpoints will be fully functional after T2 merges the
# ab_experiments and ab_results tables. For now they return empty lists
# or 404, which is safe since the experiments feature requires T2's schema.


@router.get("", response_model=list[ExperimentResponse])
def list_experiments(
    project_id: str | None = Query(None),
    db: Session = Depends(get_db),
    _api_key: str = Depends(require_api_key),
) -> list[ExperimentResponse]:
    """List A/B experiments."""
    # Dynamically check if the table exists (safe for pre-T2 merge)
    from sqlalchemy import inspect as sa_inspect

    inspector = sa_inspect(db.get_bind())
    if "ab_experiments" not in inspector.get_table_names():
        return []

    from sqlalchemy import text

    rows = db.execute(text("SELECT * FROM ab_experiments ORDER BY started_at DESC"))
    results: list[ExperimentResponse] = []
    for row in rows:
        mapping = row._mapping
        if project_id and mapping.get("project_id") != project_id:
            continue
        results.append(
            ExperimentResponse(
                id=int(mapping["id"]),
                experiment_id=str(mapping["experiment_id"]),
                project_id=mapping.get("project_id"),
                primary_model=str(mapping["primary_model"]),
                canary_model=str(mapping["canary_model"]),
                canary_pct=float(mapping["canary_pct"]),
                status=str(mapping["status"]),
                started_at=mapping.get("started_at"),
                ended_at=mapping.get("ended_at"),
            )
        )
    return results


@router.get("/{experiment_id}", response_model=ExperimentResponse)
def get_experiment(
    experiment_id: str,
    db: Session = Depends(get_db),
    _api_key: str = Depends(require_api_key),
) -> ExperimentResponse:
    """Get experiment detail."""
    from fastapi import HTTPException
    from sqlalchemy import inspect as sa_inspect
    from sqlalchemy import text

    inspector = sa_inspect(db.get_bind())
    if "ab_experiments" not in inspector.get_table_names():
        raise HTTPException(status_code=404, detail="Experiments not available yet")

    row = db.execute(
        text("SELECT * FROM ab_experiments WHERE experiment_id = :eid"),
        {"eid": experiment_id},
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Experiment not found")
    mapping = row._mapping
    return ExperimentResponse(
        id=int(mapping["id"]),
        experiment_id=str(mapping["experiment_id"]),
        project_id=mapping.get("project_id"),
        primary_model=str(mapping["primary_model"]),
        canary_model=str(mapping["canary_model"]),
        canary_pct=float(mapping["canary_pct"]),
        status=str(mapping["status"]),
        started_at=mapping.get("started_at"),
        ended_at=mapping.get("ended_at"),
    )


@router.get("/{experiment_id}/results", response_model=ExperimentResultsResponse)
def get_experiment_results(
    experiment_id: str,
    db: Session = Depends(get_db),
    _api_key: str = Depends(require_api_key),
) -> ExperimentResultsResponse:
    """Statistical comparison of A/B experiment results."""
    from fastapi import HTTPException
    from sqlalchemy import inspect as sa_inspect
    from sqlalchemy import text

    inspector = sa_inspect(db.get_bind())
    if "ab_results" not in inspector.get_table_names():
        raise HTTPException(status_code=404, detail="Experiments not available yet")

    rows = db.execute(
        text(
            "SELECT model_used, COUNT(*) as cnt, AVG(latency_ms) as avg_lat "
            "FROM ab_results WHERE experiment_id = :eid GROUP BY model_used"
        ),
        {"eid": experiment_id},
    ).fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="No results for experiment")

    primary_count = 0
    canary_count = 0
    primary_lat: float | None = None
    canary_lat: float | None = None

    # First model alphabetically is primary, second is canary
    sorted_rows = sorted(rows, key=lambda r: str(r._mapping["model_used"]))
    if len(sorted_rows) >= 1:
        m = sorted_rows[0]._mapping
        primary_count = int(m["cnt"])
        primary_lat = float(m["avg_lat"]) if m["avg_lat"] else None
    if len(sorted_rows) >= 2:
        m = sorted_rows[1]._mapping
        canary_count = int(m["cnt"])
        canary_lat = float(m["avg_lat"]) if m["avg_lat"] else None

    return ExperimentResultsResponse(
        experiment_id=experiment_id,
        primary_count=primary_count,
        canary_count=canary_count,
        primary_avg_latency_ms=primary_lat,
        canary_avg_latency_ms=canary_lat,
    )

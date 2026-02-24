"""Optional Argilla export for DPO pairs and human corrections."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session


def export_to_argilla(
    db_session: Session,
    project_id: str,
    argilla_api_url: str = "http://localhost:6900",
    argilla_api_key: str = "",
    dataset_name: str | None = None,
) -> dict[str, Any]:
    """Push preference pairs to Argilla for annotation review.

    Requires: pip install signalops[argilla]
    """
    try:
        import argilla as rg
    except ImportError:
        return {"error": "argilla not installed. Run: pip install signalops[argilla]"}

    client = rg.Argilla(api_url=argilla_api_url, api_key=argilla_api_key)
    name = dataset_name or f"signalops-dpo-{project_id}"

    from signalops.storage.database import PreferencePair

    pairs = db_session.query(PreferencePair).filter(PreferencePair.project_id == project_id).all()

    records = [
        rg.Record(
            fields={
                "prompt": pair.prompt,
                "chosen": pair.chosen_text,
                "rejected": pair.rejected_text,
            },
            metadata={"source": pair.source, "draft_id": pair.draft_id},
        )
        for pair in pairs
    ]

    dataset = rg.Dataset(name=name, records=records)
    dataset.push_to_argilla(client)
    return {"records": len(records), "dataset": name}

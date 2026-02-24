"""Export commands for training data."""

from __future__ import annotations

import os
from datetime import UTC, datetime

import click

from signalops.cli.project import get_active_project


@click.group("export")
def export_group() -> None:
    """Export data for fine-tuning or analysis."""


@export_group.command("training-data")
@click.option(
    "--type",
    "data_type",
    type=click.Choice(["judgments", "drafts", "outcomes", "dpo"]),
    required=True,
)
@click.option(
    "--format",
    "data_format",
    type=click.Choice(["openai", "dpo"]),
    default="openai",
)
@click.option("--output", default=None, help="Output file path")
@click.option("--since", default=None, help="Only export after this date (YYYY-MM-DD)")
@click.option(
    "--min-confidence",
    default=None,
    type=float,
    help="Only export judgments with confidence >= this value",
)
@click.option(
    "--include-metadata",
    is_flag=True,
    default=False,
    help="Include export metadata in output",
)
@click.pass_context
def export_training_data(
    ctx: click.Context,
    data_type: str,
    data_format: str,
    output: str | None,
    since: str | None,
    min_confidence: float | None,
    include_metadata: bool,
) -> None:
    """Export training data as JSONL for fine-tuning."""
    from signalops.config.defaults import DEFAULT_DB_URL
    from signalops.storage.database import get_engine, get_session, init_db
    from signalops.training.exporter import TrainingDataExporter

    console = ctx.obj["console"]
    project_id = get_active_project(ctx)
    dry_run = ctx.obj["dry_run"]

    engine = get_engine(DEFAULT_DB_URL)
    init_db(engine)
    session = get_session(engine)

    exporter = TrainingDataExporter(db_session=session)

    since_dt: datetime | None = None
    if since:
        since_dt = datetime.strptime(since, "%Y-%m-%d").replace(tzinfo=UTC)

    if data_type == "judgments":
        default_output = output or "judgments.jsonl"
        if dry_run:
            console.print(f"[yellow][DRY RUN] Would export judgments to {default_output}")
            session.close()
            return
        result = exporter.export_judgments(
            project_id=project_id,
            format=data_format,
            output=default_output,
            since=since_dt,
            min_confidence=min_confidence,
            include_metadata=include_metadata,
        )
    elif data_type == "outcomes":
        default_output = output or "outcomes.jsonl"
        if dry_run:
            console.print(f"[yellow][DRY RUN] Would export outcomes to {default_output}")
            session.close()
            return
        result = exporter.export_outcomes(
            project_id=project_id,
            output=default_output,
        )
    elif data_type == "dpo":
        default_output = output or "preferences.jsonl"
        if dry_run:
            console.print(f"[yellow][DRY RUN] Would export DPO pairs to {default_output}")
            session.close()
            return
        from signalops.training.dpo import export_dpo_pairs

        result = export_dpo_pairs(session, project_id, default_output)
    else:
        default_output = output or "preferences.jsonl"
        if dry_run:
            console.print(f"[yellow][DRY RUN] Would export draft preferences to {default_output}")
            session.close()
            return
        result = exporter.export_draft_preferences(
            project_id=project_id,
            output=default_output,
        )

    file_size = os.path.getsize(result["output"])
    console.print(
        f"[green]Exported {result['records']} records to {result['output']} ({file_size:,} bytes)"
    )
    session.close()

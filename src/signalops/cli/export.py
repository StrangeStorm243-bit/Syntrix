"""Export commands for training data."""

import click

from signalops.cli.project import get_active_project, load_active_config


@click.group("export")
def export_group():
    """Export data for fine-tuning or analysis."""


@export_group.command("training-data")
@click.option("--type", "data_type", type=click.Choice(["judgments", "drafts"]), required=True)
@click.option("--format", "data_format", type=click.Choice(["openai", "dpo"]), default="openai")
@click.option("--output", default=None, help="Output file path")
@click.pass_context
def export_training_data(ctx, data_type, data_format, output):
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
        )
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

    console.print(
        f"[green]Exported {result['records']} records to {result['output']}"
    )
    session.close()

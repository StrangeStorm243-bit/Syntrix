"""A/B experiment CLI commands."""

from __future__ import annotations

import uuid

import click

from signalops.cli.project import get_active_project


@click.group("experiment")
def experiment_group() -> None:
    """Manage A/B test experiments."""


@experiment_group.command("create")
@click.option("--primary", required=True, help="Primary model ID")
@click.option("--canary", required=True, help="Canary model ID")
@click.option("--canary-pct", default=0.1, type=float, help="Canary traffic percentage (0-1)")
@click.option("--hypothesis", default=None, help="Experiment hypothesis")
@click.pass_context
def experiment_create(
    ctx: click.Context,
    primary: str,
    canary: str,
    canary_pct: float,
    hypothesis: str | None,
) -> None:
    """Create a new A/B test experiment."""
    from signalops.config.defaults import DEFAULT_DB_URL
    from signalops.storage.database import ABExperiment, get_engine, get_session, init_db

    console = ctx.obj["console"]
    project_id = get_active_project(ctx)

    engine = get_engine(DEFAULT_DB_URL)
    init_db(engine)
    session = get_session(engine)

    experiment_id = f"exp-{uuid.uuid4().hex[:8]}"
    experiment = ABExperiment(
        experiment_id=experiment_id,
        project_id=project_id,
        primary_model=primary,
        canary_model=canary,
        canary_pct=canary_pct,
        status="active",
        hypothesis=hypothesis,
    )
    session.add(experiment)
    session.commit()

    console.print(f"[green]Created experiment {experiment_id}")
    console.print(f"  Primary: {primary}")
    console.print(f"  Canary: {canary} ({canary_pct:.0%} traffic)")
    if hypothesis:
        console.print(f"  Hypothesis: {hypothesis}")
    session.close()


@experiment_group.command("list")
@click.pass_context
def experiment_list(ctx: click.Context) -> None:
    """List all experiments for the active project."""
    from rich.table import Table

    from signalops.config.defaults import DEFAULT_DB_URL
    from signalops.storage.database import ABExperiment, get_engine, get_session, init_db

    console = ctx.obj["console"]
    project_id = get_active_project(ctx)

    engine = get_engine(DEFAULT_DB_URL)
    init_db(engine)
    session = get_session(engine)

    experiments = (
        session.query(ABExperiment)
        .filter(ABExperiment.project_id == project_id)
        .order_by(ABExperiment.started_at.desc())
        .all()
    )

    if not experiments:
        console.print("[yellow]No experiments found.")
        session.close()
        return

    table = Table(title="A/B Experiments")
    table.add_column("ID")
    table.add_column("Primary")
    table.add_column("Canary")
    table.add_column("Traffic")
    table.add_column("Status")

    for exp in experiments:
        status_color = {"active": "green", "paused": "yellow", "completed": "dim"}.get(
            str(exp.status), "white"
        )
        table.add_row(
            str(exp.experiment_id),
            str(exp.primary_model),
            str(exp.canary_model),
            f"{float(exp.canary_pct):.0%}",
            f"[{status_color}]{exp.status}[/{status_color}]",
        )

    console.print(table)
    session.close()


@experiment_group.command("results")
@click.argument("experiment_id")
@click.pass_context
def experiment_results(ctx: click.Context, experiment_id: str) -> None:
    """Show results and statistical analysis for an experiment."""
    from rich.table import Table

    from signalops.config.defaults import DEFAULT_DB_URL
    from signalops.models.ab_analysis import analyze_experiment
    from signalops.storage.database import get_engine, get_session, init_db

    console = ctx.obj["console"]

    engine = get_engine(DEFAULT_DB_URL)
    init_db(engine)
    session = get_session(engine)

    results = analyze_experiment(session, experiment_id)

    console.print(f"\n[bold]Experiment: {results.experiment_id}[/bold]")
    console.print(f"Primary: {results.primary_model} ({results.primary_count} judgments)")
    console.print(f"Canary: {results.canary_model} ({results.canary_count} judgments)")

    table = Table(title="Metrics Comparison")
    table.add_column("Metric")
    table.add_column("Primary")
    table.add_column("Canary")

    for key in results.primary_metrics:
        p_val = results.primary_metrics[key]
        c_val = results.canary_metrics[key]
        if "pct" in key or "rate" in key:
            table.add_row(key, f"{p_val:.1%}", f"{c_val:.1%}")
        else:
            table.add_row(key, f"{p_val:.2f}", f"{c_val:.2f}")

    console.print(table)

    if results.p_value is not None:
        sig = "[green]Yes[/green]" if results.is_significant else "[yellow]No[/yellow]"
        console.print(f"\nChi-squared: {results.chi_squared:.4f}, p-value: {results.p_value:.4f}")
        console.print(f"Significant: {sig}")

    console.print(f"\n[bold]Recommendation:[/bold] {results.recommendation}")
    session.close()


@experiment_group.command("stop")
@click.argument("experiment_id")
@click.pass_context
def experiment_stop(ctx: click.Context, experiment_id: str) -> None:
    """Stop an active experiment."""
    from datetime import UTC, datetime

    from signalops.config.defaults import DEFAULT_DB_URL
    from signalops.storage.database import ABExperiment, get_engine, get_session, init_db

    console = ctx.obj["console"]

    engine = get_engine(DEFAULT_DB_URL)
    init_db(engine)
    session = get_session(engine)

    experiment = (
        session.query(ABExperiment).filter(ABExperiment.experiment_id == experiment_id).first()
    )
    if not experiment:
        raise click.UsageError(f"Experiment {experiment_id} not found")

    experiment.status = "completed"  # type: ignore[assignment]
    experiment.ended_at = datetime.now(UTC)  # type: ignore[assignment]
    session.commit()

    console.print(f"[green]Experiment {experiment_id} stopped.")
    session.close()

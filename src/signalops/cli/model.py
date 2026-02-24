"""Model registry CLI commands."""

from __future__ import annotations

import click

from signalops.cli.project import get_active_project  # noqa: F401


@click.group("model")
def model_group() -> None:
    """Manage the fine-tuned model registry."""


@model_group.command("register")
@click.option("--model-id", required=True, help="Model ID (e.g., ft:gpt-4o-mini:spectra-v1)")
@click.option("--provider", required=True, type=click.Choice(["openai", "anthropic"]))
@click.option("--type", "model_type", required=True, type=click.Choice(["judge", "drafter"]))
@click.option("--display-name", default=None, help="Human-friendly name")
@click.option("--base-model", default=None, help="Base model fine-tuned from")
@click.option("--version", default="v1", help="Model version")
@click.pass_context
def model_register(
    ctx: click.Context,
    model_id: str,
    provider: str,
    model_type: str,
    display_name: str | None,
    base_model: str | None,
    version: str,
) -> None:
    """Register a fine-tuned model."""
    from signalops.config.defaults import DEFAULT_DB_URL
    from signalops.storage.database import ModelRegistry, get_engine, get_session, init_db

    console = ctx.obj["console"]

    engine = get_engine(DEFAULT_DB_URL)
    init_db(engine)
    session = get_session(engine)

    model = ModelRegistry(
        model_id=model_id,
        provider=provider,
        model_type=model_type,
        display_name=display_name or model_id,
        base_model=base_model,
        version=version,
        is_active=True,
    )
    session.add(model)
    session.commit()

    console.print(f"[green]Registered model: {model_id}")
    console.print(f"  Provider: {provider}, Type: {model_type}, Version: {version}")
    session.close()


@model_group.command("list")
@click.option("--all", "show_all", is_flag=True, help="Show inactive models too")
@click.pass_context
def model_list(ctx: click.Context, show_all: bool) -> None:
    """List registered models."""
    from rich.table import Table

    from signalops.config.defaults import DEFAULT_DB_URL
    from signalops.storage.database import ModelRegistry, get_engine, get_session, init_db

    console = ctx.obj["console"]

    engine = get_engine(DEFAULT_DB_URL)
    init_db(engine)
    session = get_session(engine)

    query = session.query(ModelRegistry)
    if not show_all:
        query = query.filter(ModelRegistry.is_active == True)  # noqa: E712
    models = query.order_by(ModelRegistry.deployed_at.desc()).all()

    if not models:
        console.print("[yellow]No models registered.")
        session.close()
        return

    table = Table(title="Model Registry")
    table.add_column("Model ID", max_width=50)
    table.add_column("Provider")
    table.add_column("Type")
    table.add_column("Version")
    table.add_column("Active")

    for m in models:
        active = "[green]Yes[/green]" if m.is_active else "[dim]No[/dim]"
        table.add_row(str(m.model_id), str(m.provider), str(m.model_type), str(m.version), active)

    console.print(table)
    session.close()


@model_group.command("activate")
@click.argument("model_id")
@click.pass_context
def model_activate(ctx: click.Context, model_id: str) -> None:
    """Activate a registered model."""
    from signalops.config.defaults import DEFAULT_DB_URL
    from signalops.storage.database import ModelRegistry, get_engine, get_session, init_db

    console = ctx.obj["console"]

    engine = get_engine(DEFAULT_DB_URL)
    init_db(engine)
    session = get_session(engine)

    model = session.query(ModelRegistry).filter(ModelRegistry.model_id == model_id).first()
    if not model:
        raise click.UsageError(f"Model {model_id} not found")

    model.is_active = True  # type: ignore[assignment]
    session.commit()
    console.print(f"[green]Model {model_id} activated.")
    session.close()


@model_group.command("deactivate")
@click.argument("model_id")
@click.pass_context
def model_deactivate(ctx: click.Context, model_id: str) -> None:
    """Deactivate a registered model."""
    from signalops.config.defaults import DEFAULT_DB_URL
    from signalops.storage.database import ModelRegistry, get_engine, get_session, init_db

    console = ctx.obj["console"]

    engine = get_engine(DEFAULT_DB_URL)
    init_db(engine)
    session = get_session(engine)

    model = session.query(ModelRegistry).filter(ModelRegistry.model_id == model_id).first()
    if not model:
        raise click.UsageError(f"Model {model_id} not found")

    model.is_active = False  # type: ignore[assignment]
    session.commit()
    console.print(f"[yellow]Model {model_id} deactivated.")
    session.close()

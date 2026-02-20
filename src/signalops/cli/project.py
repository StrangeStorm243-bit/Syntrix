"""Project management CLI commands."""

from __future__ import annotations

from typing import Any

import click
from rich.table import Table

from signalops.config.defaults import DEFAULT_PROJECTS_DIR
from signalops.config.schema import ProjectConfig


@click.group("project")
def project_group() -> None:
    """Manage projects."""


@project_group.command("set")
@click.argument("name")
@click.pass_context
def project_set(ctx: click.Context, name: str) -> None:
    """Set the active project."""
    from signalops.config.loader import load_project, set_active_project

    config_path = DEFAULT_PROJECTS_DIR / f"{name}.yaml"
    if not config_path.exists():
        raise click.UsageError(f"Project config not found: {config_path}")

    # Validate by loading
    config = load_project(config_path)

    # Store active project
    set_active_project(name)

    console = ctx.obj["console"]
    console.print(f"[green]Active project: {name} ({len(config.queries)} queries configured)")


@project_group.command("list")
@click.pass_context
def project_list(ctx: click.Context) -> None:
    """List all available projects."""
    from signalops.config.loader import get_active_project, load_project

    console = ctx.obj["console"]

    projects_dir = DEFAULT_PROJECTS_DIR
    if not projects_dir.exists():
        console.print("[yellow]No projects directory found. Run: signalops project init")
        return

    yaml_files = sorted(projects_dir.glob("*.yaml"))
    if not yaml_files:
        console.print("[yellow]No project configs found in projects/")
        return

    active_name = get_active_project()

    table = Table(title="Projects")
    table.add_column("Active", justify="center", width=6)
    table.add_column("Name", style="bold")
    table.add_column("Description")
    table.add_column("Queries", justify="right")

    for yf in yaml_files:
        name = yf.stem
        try:
            config = load_project(yf)
            marker = "[green]*[/green]" if name == active_name else ""
            table.add_row(marker, config.project_name, config.description, str(len(config.queries)))
        except Exception as e:
            table.add_row("", name, f"[red]Error: {e}[/red]", "?")

    console.print(table)


@project_group.command("init")
@click.pass_context
def project_init(ctx: click.Context) -> None:
    """Create a new project interactively."""
    from rich.prompt import Prompt

    console = ctx.obj["console"]

    console.print("[bold]Create a new SignalOps project[/bold]\n")

    project_id = Prompt.ask("Project ID (slug)", default="my-project")
    project_name = Prompt.ask("Project name", default=project_id.replace("-", " ").title())
    description = Prompt.ask("Description")
    product_url = Prompt.ask("Product URL (optional)", default="")

    # Queries
    queries: list[dict[str, Any]] = []
    console.print("\n[bold]Search Queries[/bold] (enter empty text to stop)")
    while True:
        text = Prompt.ask("  Query text (X API syntax)", default="")
        if not text:
            if not queries:
                console.print("[red]At least one query is required.")
                continue
            break
        label = Prompt.ask("  Query label", default=f"query-{len(queries) + 1}")
        queries.append({"text": text, "label": label, "enabled": True, "max_results_per_run": 100})

    # Persona
    console.print("\n[bold]Bot Persona[/bold]")
    persona_name = Prompt.ask("  Persona name", default="Alex")
    persona_role = Prompt.ask("  Role", default="product specialist")
    persona_tone = Prompt.ask("  Tone", default="helpful")
    voice_notes = Prompt.ask("  Voice notes", default="Be concise and authentic.")
    example_reply = Prompt.ask("  Example reply")

    # Relevance rubric
    console.print("\n[bold]Relevance Rubric[/bold]")
    system_prompt = Prompt.ask(
        "  System prompt for judge",
        default=f"You are a relevance judge for {project_name}.",
    )
    pos = Prompt.ask("  Positive signals (comma-separated)")
    neg = Prompt.ask("  Negative signals (comma-separated)")

    import yaml

    config_dict = {
        "project_id": project_id,
        "project_name": project_name,
        "description": description,
        "product_url": product_url or None,
        "queries": queries,
        "icp": {
            "min_followers": 100,
            "languages": ["en"],
        },
        "relevance": {
            "system_prompt": system_prompt,
            "positive_signals": [s.strip() for s in pos.split(",") if s.strip()],
            "negative_signals": [s.strip() for s in neg.split(",") if s.strip()],
        },
        "scoring": {
            "relevance_judgment": 0.35,
            "author_authority": 0.25,
            "engagement_signals": 0.15,
            "recency": 0.15,
            "intent_strength": 0.10,
        },
        "persona": {
            "name": persona_name,
            "role": persona_role,
            "tone": persona_tone,
            "voice_notes": voice_notes,
            "example_reply": example_reply,
        },
        "rate_limits": {"max_replies_per_hour": 5, "max_replies_per_day": 20},
        "llm": {"judge_model": "claude-sonnet-4-6", "draft_model": "claude-sonnet-4-6"},
    }

    DEFAULT_PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = DEFAULT_PROJECTS_DIR / f"{project_id}.yaml"
    with open(output_path, "w") as f:
        yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)

    console.print(f"\n[green]Project created: {output_path}")
    console.print(f"Run: signalops project set {project_id}")


def get_active_project(ctx: click.Context) -> str:
    """Get the active project name from ctx override or ~/.signalops/active_project."""
    if ctx.obj.get("project"):
        return str(ctx.obj["project"])

    from signalops.config.loader import get_active_project as _get_active

    name = _get_active()
    if name is not None:
        return name
    raise click.UsageError("No active project. Run: signalops project set <name>")


def load_active_config(ctx: click.Context) -> ProjectConfig:
    """Load the active project's config."""
    from signalops.config.loader import load_project

    name = get_active_project(ctx)
    path = DEFAULT_PROJECTS_DIR / f"{name}.yaml"
    if not path.exists():
        raise click.UsageError(f"Project config not found: {path}")
    return load_project(path)

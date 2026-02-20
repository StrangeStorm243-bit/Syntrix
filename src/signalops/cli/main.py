"""SignalOps CLI — main entry point."""

from __future__ import annotations

import click
from dotenv import load_dotenv
from rich.console import Console

# Load .env on startup
load_dotenv()

console = Console()


@click.group()
@click.option("--project", "-p", default=None, help="Override active project")
@click.option("--dry-run", is_flag=True, default=False, help="Preview without side effects")
@click.option("--verbose", "-v", is_flag=True, default=False, help="Debug logging")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@click.pass_context
def cli(
    ctx: click.Context, project: str | None, dry_run: bool, verbose: bool, output_format: str
) -> None:
    """SignalOps — Agentic social lead finder + outreach workbench."""
    ctx.ensure_object(dict)
    ctx.obj["project"] = project
    ctx.obj["dry_run"] = dry_run
    ctx.obj["verbose"] = verbose
    ctx.obj["format"] = output_format
    ctx.obj["console"] = console

    if verbose:
        import logging

        logging.basicConfig(level=logging.DEBUG)


# Register sub-groups and commands (lazy-imported modules define their groups)
import signalops.cli.draft  # noqa: E402, F401 — registers draft command on run_group
import signalops.cli.judge  # noqa: E402, F401 — registers judge command on run_group
import signalops.cli.score  # noqa: E402, F401 — registers score command on run_group
import signalops.cli.send  # noqa: E402, F401 — registers send command on queue_group
from signalops.cli.approve import queue_group  # noqa: E402
from signalops.cli.collect import run_group  # noqa: E402
from signalops.cli.correct import correct_cmd  # noqa: E402
from signalops.cli.eval import eval_group  # noqa: E402
from signalops.cli.export import export_group  # noqa: E402
from signalops.cli.project import project_group  # noqa: E402
from signalops.cli.stats import stats_cmd  # noqa: E402

cli.add_command(project_group, "project")
cli.add_command(run_group, "run")
cli.add_command(queue_group, "queue")
cli.add_command(stats_cmd, "stats")
cli.add_command(export_group, "export")
cli.add_command(correct_cmd, "correct")
cli.add_command(eval_group, "eval")

if __name__ == "__main__":
    cli()

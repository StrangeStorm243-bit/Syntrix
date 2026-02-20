"""Human correction CLI commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from signalops.cli.project import get_active_project

if TYPE_CHECKING:
    from rich.console import Console
    from sqlalchemy.orm import Session


@click.command("correct")
@click.argument("judgment_id", required=False, type=int)
@click.option(
    "--label",
    type=click.Choice(["relevant", "irrelevant", "maybe"]),
    help="Corrected label",
)
@click.option("--reason", default=None, help="Reason for correction")
@click.option("--review", is_flag=True, default=False, help="Interactive review mode")
@click.option("--n", "count", default=10, type=int, help="Number to review")
@click.option(
    "--strategy",
    type=click.Choice(["low_confidence", "random", "recent"]),
    default="low_confidence",
    help="Sampling strategy for review mode",
)
@click.pass_context
def correct_cmd(
    ctx: click.Context,
    judgment_id: int | None,
    label: str | None,
    reason: str | None,
    review: bool,
    count: int,
    strategy: str,
) -> None:
    """Correct a judgment or interactively review judgments."""
    from signalops.config.defaults import DEFAULT_DB_URL
    from signalops.storage.database import get_engine, get_session, init_db

    console: Console = ctx.obj["console"]
    project_id = get_active_project(ctx)

    engine = get_engine(DEFAULT_DB_URL)
    init_db(engine)
    session = get_session(engine)

    try:
        if review:
            _interactive_review(session, project_id, count, strategy, console)
        elif judgment_id is not None and label is not None:
            _direct_correct(session, project_id, judgment_id, label, reason, console)
        else:
            raise click.UsageError("Provide <judgment_id> --label <label> or use --review")
    finally:
        session.close()


def _direct_correct(
    session: Session,
    project_id: str,
    judgment_id: int,
    label: str,
    reason: str | None,
    console: Console,
) -> None:
    """Apply a single correction."""
    from signalops.storage.database import Judgment, NormalizedPost
    from signalops.training.labeler import correct_judgment

    judgment = session.query(Judgment).get(judgment_id)
    if judgment is None:
        console.print(f"[red]Judgment {judgment_id} not found")
        return

    post = session.query(NormalizedPost).filter_by(id=judgment.normalized_post_id).first()

    console.print(f"\n[bold]Post:[/bold] {post.text_cleaned if post else '(unknown)'}")
    console.print(
        f"[bold]Model judgment:[/bold] {judgment.label.value} (confidence: {judgment.confidence})"
    )

    updated = correct_judgment(session, judgment_id, label, reason)
    console.print(
        f"\n[green]Corrected:[/green] {judgment.label.value} -> {updated.human_label.value}"
    )


def _interactive_review(
    session: Session,
    project_id: str,
    count: int,
    strategy: str,
    console: Console,
) -> None:
    """Interactive review mode."""
    from rich.prompt import Prompt

    from signalops.storage.database import NormalizedPost
    from signalops.training.labeler import correct_judgment, get_uncorrected_sample

    judgments = get_uncorrected_sample(session, project_id, n=count, strategy=strategy)

    if not judgments:
        console.print("[yellow]No uncorrected judgments found for review.")
        return

    console.print(f"[bold]Review mode:[/bold] {len(judgments)} judgments ({strategy})\n")

    corrected = 0
    skipped = 0
    agreed = 0

    for i, j in enumerate(judgments, 1):
        post = session.query(NormalizedPost).filter_by(id=j.normalized_post_id).first()

        console.print(f"\n--- [{i}/{len(judgments)}] ---")
        console.print(f"[bold]Post:[/bold] {post.text_cleaned if post else '(unknown)'}")
        if post and post.author_username:
            console.print(f"[bold]Author:[/bold] @{post.author_username}")
        console.print(f"[bold]Model:[/bold] {j.label.value} (confidence: {j.confidence})")

        choice = Prompt.ask(
            "Label",
            choices=["relevant", "irrelevant", "maybe", "skip"],
            default="skip",
        )

        if choice == "skip":
            skipped += 1
            continue

        reason_text = Prompt.ask("Reason (optional)", default="")
        correct_judgment(
            session,
            j.id,  # type: ignore[arg-type]
            choice,
            reason_text or None,
        )
        corrected += 1
        if choice == j.label.value:
            agreed += 1

    console.print("\n[bold]Session summary:[/bold]")
    console.print(f"  Corrected: {corrected}")
    console.print(f"  Skipped: {skipped}")
    if corrected > 0:
        console.print(f"  Agreement rate: {agreed / corrected:.0%}")

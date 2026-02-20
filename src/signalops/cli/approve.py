"""Draft approval queue CLI commands."""

import click

from signalops.cli.project import get_active_project


@click.group("queue")
def queue_group():
    """Manage the draft approval queue."""


@queue_group.command("list")
@click.pass_context
def queue_list(ctx):
    """Show pending drafts."""
    from signalops.config.defaults import DEFAULT_DB_URL
    from signalops.storage.database import (
        Draft,
        DraftStatus,
        NormalizedPost,
        Score,
        get_engine,
        get_session,
        init_db,
    )
    from rich.table import Table

    console = ctx.obj["console"]
    project_id = get_active_project(ctx)

    engine = get_engine(DEFAULT_DB_URL)
    init_db(engine)
    session = get_session(engine)

    drafts = (
        session.query(Draft, NormalizedPost, Score)
        .join(NormalizedPost, Draft.normalized_post_id == NormalizedPost.id)
        .outerjoin(Score, Score.normalized_post_id == NormalizedPost.id)
        .filter(Draft.project_id == project_id)
        .filter(Draft.status.in_([DraftStatus.PENDING, DraftStatus.APPROVED, DraftStatus.EDITED]))
        .order_by(Score.total_score.desc().nullslast())
        .all()
    )

    if not drafts:
        console.print("[yellow]No pending drafts found.")
        session.close()
        return

    table = Table(title="Draft Queue")
    table.add_column("ID", justify="right")
    table.add_column("Score", justify="right")
    table.add_column("Reply To")
    table.add_column("Draft", max_width=60)
    table.add_column("Status")

    for draft, post, score in drafts:
        score_val = f"{score.total_score:.0f}" if score else "—"
        text_preview = (draft.text_generated[:57] + "...") if len(draft.text_generated) > 60 else draft.text_generated
        status_color = {
            DraftStatus.PENDING: "yellow",
            DraftStatus.APPROVED: "green",
            DraftStatus.EDITED: "cyan",
        }.get(draft.status, "white")
        table.add_row(
            str(draft.id),
            score_val,
            f"@{post.author_username}",
            text_preview,
            f"[{status_color}]{draft.status.value}[/{status_color}]",
        )

    console.print(table)
    session.close()


@queue_group.command("approve")
@click.argument("draft_id", type=int)
@click.pass_context
def queue_approve(ctx, draft_id):
    """Approve a draft for sending."""
    from datetime import datetime, timezone

    from signalops.config.defaults import DEFAULT_DB_URL
    from signalops.storage.audit import log_action
    from signalops.storage.database import Draft, DraftStatus, get_engine, get_session, init_db

    console = ctx.obj["console"]
    project_id = get_active_project(ctx)

    engine = get_engine(DEFAULT_DB_URL)
    init_db(engine)
    session = get_session(engine)

    draft = session.query(Draft).filter_by(id=draft_id, project_id=project_id).first()
    if not draft:
        raise click.UsageError(f"Draft #{draft_id} not found in project {project_id}")

    draft.status = DraftStatus.APPROVED
    draft.approved_at = datetime.now(timezone.utc)
    session.commit()

    log_action(session, project_id, "approve_draft", "draft", draft_id)
    console.print(f"[green]Draft #{draft_id} approved.")
    session.close()


@queue_group.command("edit")
@click.argument("draft_id", type=int)
@click.pass_context
def queue_edit(ctx, draft_id):
    """Edit a draft then approve it."""
    from datetime import datetime, timezone

    from rich.prompt import Prompt

    from signalops.config.defaults import DEFAULT_DB_URL
    from signalops.storage.audit import log_action
    from signalops.storage.database import Draft, DraftStatus, get_engine, get_session, init_db

    console = ctx.obj["console"]
    project_id = get_active_project(ctx)

    engine = get_engine(DEFAULT_DB_URL)
    init_db(engine)
    session = get_session(engine)

    draft = session.query(Draft).filter_by(id=draft_id, project_id=project_id).first()
    if not draft:
        raise click.UsageError(f"Draft #{draft_id} not found in project {project_id}")

    console.print(f"[bold]Current draft:[/bold]\n{draft.text_generated}\n")
    new_text = Prompt.ask("New text (or press Enter to keep)")

    if new_text:
        draft.text_final = new_text
    else:
        draft.text_final = draft.text_generated

    draft.status = DraftStatus.EDITED
    draft.approved_at = datetime.now(timezone.utc)
    session.commit()

    log_action(
        session, project_id, "edit_draft", "draft", draft_id,
        details={"new_text": draft.text_final},
    )
    console.print(f"[green]Draft #{draft_id} edited and approved.")
    session.close()


@queue_group.command("reject")
@click.argument("draft_id", type=int)
@click.option("--reason", default=None, help="Rejection reason")
@click.pass_context
def queue_reject(ctx, draft_id, reason):
    """Reject a draft."""
    from signalops.config.defaults import DEFAULT_DB_URL
    from signalops.storage.audit import log_action
    from signalops.storage.database import Draft, DraftStatus, get_engine, get_session, init_db

    console = ctx.obj["console"]
    project_id = get_active_project(ctx)

    engine = get_engine(DEFAULT_DB_URL)
    init_db(engine)
    session = get_session(engine)

    draft = session.query(Draft).filter_by(id=draft_id, project_id=project_id).first()
    if not draft:
        raise click.UsageError(f"Draft #{draft_id} not found in project {project_id}")

    draft.status = DraftStatus.REJECTED
    session.commit()

    log_action(
        session, project_id, "reject_draft", "draft", draft_id,
        details={"reason": reason} if reason else None,
    )
    console.print(f"[yellow]Draft #{draft_id} rejected." + (f" Reason: {reason}" if reason else ""))
    session.close()

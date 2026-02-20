"""Pipeline statistics display."""

from __future__ import annotations

import click
from rich.panel import Panel

from signalops.cli.project import get_active_project


@click.command("stats")
@click.pass_context
def stats_cmd(ctx: click.Context) -> None:
    """Show pipeline statistics for the active project."""
    from signalops.config.defaults import DEFAULT_DB_URL
    from signalops.storage.database import (
        Draft,
        DraftStatus,
        Judgment,
        JudgmentLabel,
        NormalizedPost,
        Outcome,
        RawPost,
        Score,
        get_engine,
        get_session,
        init_db,
    )

    console = ctx.obj["console"]
    output_format = ctx.obj["format"]
    project_id = get_active_project(ctx)

    engine = get_engine(DEFAULT_DB_URL)
    init_db(engine)
    session = get_session(engine)

    # Gather counts
    raw_count = session.query(RawPost).filter_by(project_id=project_id).count()
    norm_count = session.query(NormalizedPost).filter_by(project_id=project_id).count()

    judged_relevant = (
        session.query(Judgment)
        .filter_by(project_id=project_id, label=JudgmentLabel.RELEVANT)
        .count()
    )
    judged_irrelevant = (
        session.query(Judgment)
        .filter_by(project_id=project_id, label=JudgmentLabel.IRRELEVANT)
        .count()
    )
    judged_maybe = (
        session.query(Judgment).filter_by(project_id=project_id, label=JudgmentLabel.MAYBE).count()
    )
    total_judged = judged_relevant + judged_irrelevant + judged_maybe

    scored_count = session.query(Score).filter_by(project_id=project_id).count()
    from sqlalchemy import func

    avg_score_result = (
        session.query(func.avg(Score.total_score)).filter_by(project_id=project_id).scalar()
    )
    avg_score = avg_score_result or 0.0
    high_score_count = (
        session.query(Score).filter(Score.project_id == project_id, Score.total_score > 70).count()
    )

    draft_pending = (
        session.query(Draft).filter_by(project_id=project_id, status=DraftStatus.PENDING).count()
    )
    draft_approved = (
        session.query(Draft).filter_by(project_id=project_id, status=DraftStatus.APPROVED).count()
    )
    draft_sent = (
        session.query(Draft).filter_by(project_id=project_id, status=DraftStatus.SENT).count()
    )
    draft_rejected = (
        session.query(Draft).filter_by(project_id=project_id, status=DraftStatus.REJECTED).count()
    )
    total_drafts = draft_pending + draft_approved + draft_sent + draft_rejected

    outcome_count = session.query(Outcome).filter_by(project_id=project_id).count()

    session.close()

    if output_format == "json":
        import json

        data = {
            "project_id": project_id,
            "raw_posts": raw_count,
            "normalized_posts": norm_count,
            "judgments": {
                "total": total_judged,
                "relevant": judged_relevant,
                "irrelevant": judged_irrelevant,
                "maybe": judged_maybe,
            },
            "scores": {
                "total": scored_count,
                "average": round(avg_score, 1),
                "above_70": high_score_count,
            },
            "drafts": {
                "total": total_drafts,
                "pending": draft_pending,
                "approved": draft_approved,
                "sent": draft_sent,
                "rejected": draft_rejected,
            },
            "outcomes": outcome_count,
        }
        console.print_json(json.dumps(data))
        return

    # Rich panel display
    def pct(part: int, total: int) -> str:
        return f"{part / total * 100:.1f}%" if total > 0 else "0.0%"

    lines = [
        f"[bold]Collected:[/bold]      {raw_count} tweets",
        f"[bold]Normalized:[/bold]     {norm_count}",
        f"[bold]Judged:[/bold]         {total_judged}",
        f"  Relevant:     {judged_relevant} ({pct(judged_relevant, total_judged)})",
        f"  Irrelevant:   {judged_irrelevant} ({pct(judged_irrelevant, total_judged)})",
        f"  Maybe:        {judged_maybe} ({pct(judged_maybe, total_judged)})",
        f"[bold]Scored:[/bold]         {scored_count}",
        f"  Avg score:    {avg_score:.1f}",
        f"  Score > 70:   {high_score_count} ({pct(high_score_count, scored_count)})",
        f"[bold]Drafted:[/bold]        {total_drafts}",
        f"  Pending:      {draft_pending}",
        f"  Approved:     {draft_approved}",
        f"  Sent:         {draft_sent}",
        f"  Rejected:     {draft_rejected}",
        f"[bold]Outcomes:[/bold]       {outcome_count}",
    ]

    panel = Panel(
        "\n".join(lines),
        title=f"{project_id} — Pipeline Stats",
        border_style="blue",
    )
    console.print(panel)

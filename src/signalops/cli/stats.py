"""Pipeline statistics display — enhanced Rich dashboard."""

from __future__ import annotations

from typing import Any

import click
from rich.columns import Columns
from rich.panel import Panel

from signalops.cli.project import get_active_project


def _pct(part: int, total: int) -> str:
    """Format as percentage, safe for zero totals."""
    return f"{part / total * 100:.1f}%" if total > 0 else "0.0%"


def _gather_stats(session: Any, project_id: str) -> dict[str, Any]:
    """Query all dashboard stats from the database."""
    from sqlalchemy import func

    from signalops.storage.database import (
        Draft,
        DraftStatus,
        Judgment,
        JudgmentLabel,
        NormalizedPost,
        Outcome,
        OutcomeType,
        RawPost,
        Score,
    )

    # Pipeline counts
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
    avg_score_result = (
        session.query(func.avg(Score.total_score)).filter_by(project_id=project_id).scalar()
    )
    avg_score = float(avg_score_result) if avg_score_result else 0.0
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

    # Outcome breakdown
    replies_received = (
        session.query(Outcome)
        .filter_by(
            project_id=project_id,
            outcome_type=OutcomeType.REPLY_RECEIVED,
        )
        .count()
    )
    likes_received = (
        session.query(Outcome)
        .filter_by(
            project_id=project_id,
            outcome_type=OutcomeType.LIKE_RECEIVED,
        )
        .count()
    )
    follows_received = (
        session.query(Outcome)
        .filter_by(
            project_id=project_id,
            outcome_type=OutcomeType.FOLLOW_RECEIVED,
        )
        .count()
    )
    negative_count = (
        session.query(Outcome)
        .filter_by(
            project_id=project_id,
            outcome_type=OutcomeType.NEGATIVE,
        )
        .count()
    )

    # Training data: human corrections
    human_corrections = (
        session.query(Judgment)
        .filter(
            Judgment.project_id == project_id,
            Judgment.human_label.isnot(None),
        )
        .count()
    )
    # Agreement = corrections where human_label == label
    agreements = (
        session.query(Judgment)
        .filter(
            Judgment.project_id == project_id,
            Judgment.human_label.isnot(None),
            Judgment.human_label == Judgment.label,
        )
        .count()
    )

    return {
        "project_id": project_id,
        "pipeline": {
            "collected": raw_count,
            "normalized": norm_count,
            "judged": total_judged,
            "relevant": judged_relevant,
            "irrelevant": judged_irrelevant,
            "maybe": judged_maybe,
            "scored": scored_count,
            "avg_score": round(avg_score, 1),
            "above_70": high_score_count,
            "drafted": total_drafts,
            "approved": draft_approved,
            "sent": draft_sent,
            "rejected": draft_rejected,
            "pending": draft_pending,
        },
        "outcomes": {
            "replies_received": replies_received,
            "likes_received": likes_received,
            "follows": follows_received,
            "negative": negative_count,
            "total_sent": draft_sent,
        },
        "training": {
            "human_corrections": human_corrections,
            "agreement_rate": (
                round(agreements / human_corrections * 100, 1) if human_corrections > 0 else 0.0
            ),
        },
    }


def _build_pipeline_panel(stats: dict[str, Any]) -> Panel:
    """Build the pipeline stats panel."""
    p = stats["pipeline"]
    lines = [
        f"[bold]Collected:[/bold]      {p['collected']:,} tweets",
        f"[bold]Judged:[/bold]         {p['judged']:,} ({_pct(p['judged'], p['collected'])})",
        f"  Relevant:       {p['relevant']:,} ({_pct(p['relevant'], p['judged'])})",
        f"  Irrelevant:     {p['irrelevant']:,} ({_pct(p['irrelevant'], p['judged'])})",
        f"  Maybe:           {p['maybe']:,} ({_pct(p['maybe'], p['judged'])})",
        f"[bold]Scored:[/bold]         {p['scored']:,}",
        f"  Avg score:      {p['avg_score']:.1f}",
        f"  Score > 70:     {p['above_70']:,} ({_pct(p['above_70'], p['scored'])})",
        f"[bold]Drafted:[/bold]        {p['drafted']:,}",
        f"  Approved:       {p['approved']:,} ({_pct(p['approved'], p['drafted'])})",
        f"  Sent:           {p['sent']:,}",
    ]
    return Panel(
        "\n".join(lines),
        title="Pipeline Stats",
        border_style="blue",
    )


def _build_outcomes_panel(stats: dict[str, Any]) -> Panel:
    """Build the outcomes panel."""
    o = stats["outcomes"]
    sent = o["total_sent"]
    lines = [
        f"Replies received: {o['replies_received']:,} ({_pct(o['replies_received'], sent)})",
        f"Likes received:   {o['likes_received']:,} ({_pct(o['likes_received'], sent)})",
        f"Follows:          {o['follows']:,} ({_pct(o['follows'], sent)})",
        f"Negative:         {o['negative']:,} ({_pct(o['negative'], sent)})",
    ]
    return Panel(
        "\n".join(lines),
        title="Outcomes",
        border_style="green",
    )


def _build_training_panel(stats: dict[str, Any]) -> Panel:
    """Build the training data panel."""
    t = stats["training"]
    lines = [
        f"Human corrections: {t['human_corrections']:,}",
        f"Agreement rate:    {t['agreement_rate']:.1f}%",
    ]
    return Panel(
        "\n".join(lines),
        title="Training Data",
        border_style="yellow",
    )


@click.command("stats")
@click.pass_context
def stats_cmd(ctx: click.Context) -> None:
    """Show pipeline statistics for the active project."""
    from signalops.config.defaults import DEFAULT_DB_URL
    from signalops.storage.database import get_engine, get_session, init_db

    console = ctx.obj["console"]
    output_format = ctx.obj["format"]
    project_id = get_active_project(ctx)

    engine = get_engine(DEFAULT_DB_URL)
    init_db(engine)
    session = get_session(engine)

    stats = _gather_stats(session, project_id)
    session.close()

    if output_format == "json":
        import json

        console.print_json(json.dumps(stats))
        return

    # Rich multi-panel dashboard
    console.print()
    console.rule(f"[bold]{project_id}[/bold] — Dashboard")
    console.print()

    pipeline_panel = _build_pipeline_panel(stats)
    outcomes_panel = _build_outcomes_panel(stats)
    training_panel = _build_training_panel(stats)

    console.print(pipeline_panel)
    console.print(Columns([outcomes_panel, training_panel], equal=True, expand=True))

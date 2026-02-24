"""Scoring plugin management CLI commands."""

from __future__ import annotations

import click


@click.group("scoring")
def scoring_group() -> None:
    """Manage scoring plugins and rules."""


@scoring_group.command("list-plugins")
@click.pass_context
def list_plugins_cmd(ctx: click.Context) -> None:
    """Show active scoring plugins."""
    from rich.table import Table

    from signalops.scoring.engine import ScoringEngine

    console = ctx.obj["console"]
    engine = ScoringEngine()

    plugins = engine.list_plugins()
    table = Table(title="Active Scoring Plugins")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Default Weight", style="yellow")

    for p in plugins:
        table.add_row(p["name"], p["version"], p["weight"])

    console.print(table)

    # Also show entry-point plugins
    ep_plugins = ScoringEngine.load_from_entry_points()
    if ep_plugins:
        console.print(f"\n[cyan]Entry-point plugins: {len(ep_plugins)}")
        for ep in ep_plugins:
            console.print(f"  {ep.name} v{ep.version}")
    else:
        console.print("\n[dim]No entry-point plugins installed.")


@scoring_group.command("list-rules")
@click.pass_context
def list_rules_cmd(ctx: click.Context) -> None:
    """Show custom scoring rules from active project config."""
    from signalops.cli.project import load_active_config

    console = ctx.obj["console"]
    config = load_active_config(ctx)

    rules = config.scoring.custom_rules
    if not rules:
        console.print("[dim]No custom scoring rules configured.")
        return

    from rich.table import Table

    table = Table(title="Custom Scoring Rules")
    table.add_column("Name", style="cyan")
    table.add_column("Condition", style="white")
    table.add_column("Boost", style="yellow")
    table.add_column("Description", style="dim")

    for rule in rules:
        boost_str = f"+{rule.boost}" if rule.boost > 0 else str(rule.boost)
        table.add_row(rule.name, rule.condition, boost_str, rule.description)

    console.print(table)


@scoring_group.command("test-rules")
@click.pass_context
def test_rules_cmd(ctx: click.Context) -> None:
    """Dry-run scoring rules against existing scored leads."""
    from signalops.cli.project import load_active_config
    from signalops.config.defaults import DEFAULT_DB_URL
    from signalops.storage.database import get_engine, get_session, init_db

    console = ctx.obj["console"]
    config = load_active_config(ctx)

    if not config.scoring.custom_rules:
        console.print("[dim]No custom rules to test.")
        return

    engine = get_engine(DEFAULT_DB_URL)
    init_db(engine)
    session = get_session(engine)

    from signalops.storage.database import Judgment as JudgmentRow
    from signalops.storage.database import JudgmentLabel, NormalizedPost

    rows = (
        session.query(NormalizedPost, JudgmentRow)
        .join(JudgmentRow, JudgmentRow.normalized_post_id == NormalizedPost.id)
        .filter(
            NormalizedPost.project_id == config.project_id,
            JudgmentRow.label.in_([JudgmentLabel.RELEVANT, JudgmentLabel.MAYBE]),
        )
        .limit(50)
        .all()
    )

    if not rows:
        console.print("[dim]No scored leads found to test against.")
        session.close()
        return

    from signalops.scoring.engine import ScoringEngine

    scoring_engine = ScoringEngine()
    config_dict = config.scoring.model_dump()
    config_dict["weights"] = {
        "relevance_judgment": config.scoring.relevance_judgment,
        "author_authority": config.scoring.author_authority,
        "engagement_signals": config.scoring.engagement_signals,
        "recency": config.scoring.recency,
        "intent_strength": config.scoring.intent_strength,
    }

    rule_hits = 0
    for post, judgment in rows:
        post_dict = {
            "text_cleaned": post.text_cleaned,
            "author_followers": post.author_followers,
            "author_verified": post.author_verified,
            "likes": post.likes,
            "replies": post.replies,
            "retweets": post.retweets,
            "views": post.views,
            "created_at": post.created_at,
        }
        judgment_dict = {
            "label": judgment.label.value if judgment.label else "maybe",
            "confidence": float(judgment.confidence or 0),
        }
        _, components = scoring_engine.score(post_dict, judgment_dict, config_dict)
        if "rule_adjustments" in components:
            rule_hits += 1

    console.print(
        f"[green]Rules matched on {rule_hits}/{len(rows)} leads (sampled {len(rows)} most recent)"
    )
    session.close()

"""Run score command — scores judged tweets."""

import click

from signalops.cli.collect import run_group


@run_group.command("score")
@click.pass_context
def score_cmd(ctx):
    """Score judged tweets."""
    from signalops.cli.project import load_active_config
    from signalops.config.defaults import DEFAULT_DB_URL
    from signalops.storage.database import (
        NormalizedPost,
        Score,
        get_engine,
        get_session,
        init_db,
    )

    console = ctx.obj["console"]
    config = load_active_config(ctx)
    dry_run = ctx.obj["dry_run"]

    engine = get_engine(DEFAULT_DB_URL)
    init_db(engine)
    session = get_session(engine)

    # Lazy imports for pipeline stages
    from signalops.pipeline.scorer import ScorerStage

    scorer = ScorerStage(db_session=session)

    if dry_run:
        console.print("[yellow][DRY RUN] Would score judged-relevant posts")
        session.close()
        return

    result = scorer.run(project_id=config.project_id, config=config, dry_run=dry_run)

    scored_count = result.get("scored", 0)
    console.print(f"[green]Scored {scored_count} posts")

    # Show top-5 table
    from rich.table import Table

    top_scores = (
        session.query(Score, NormalizedPost)
        .join(NormalizedPost, Score.normalized_post_id == NormalizedPost.id)
        .filter(Score.project_id == config.project_id)
        .order_by(Score.total_score.desc())
        .limit(5)
        .all()
    )

    if top_scores:
        table = Table(title="Top 5 Leads")
        table.add_column("#", justify="right")
        table.add_column("Score", justify="right")
        table.add_column("Author")
        table.add_column("Tweet", max_width=50)

        for i, (score, post) in enumerate(top_scores, 1):
            text_preview = (post.text_cleaned[:47] + "...") if len(post.text_cleaned) > 50 else post.text_cleaned
            table.add_row(
                str(i),
                f"{score.total_score:.1f}",
                f"@{post.author_username}",
                text_preview,
            )
        console.print(table)

    session.close()

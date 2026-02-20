"""Run draft command — generates reply drafts for top-scored leads."""

import click

from signalops.cli.collect import run_group


@run_group.command("draft")
@click.option("--top", default=10, help="Number of top-scored posts to draft replies for")
@click.pass_context
def draft_cmd(ctx, top):
    """Generate reply drafts for top-scored leads."""
    from signalops.cli.project import load_active_config
    from signalops.config.defaults import DEFAULT_DB_URL
    from signalops.storage.database import get_engine, get_session, init_db

    console = ctx.obj["console"]
    config = load_active_config(ctx)
    dry_run = ctx.obj["dry_run"]

    engine = get_engine(DEFAULT_DB_URL)
    init_db(engine)
    session = get_session(engine)

    # Lazy imports for pipeline stages
    from signalops.pipeline.drafter import DrafterStage
    from signalops.models.draft_model import LLMDraftGenerator
    from signalops.models.llm_gateway import LLMGateway

    gateway = LLMGateway()
    generator = LLMDraftGenerator(
        gateway=gateway,
        model_id=config.llm.get("draft_model", "claude-sonnet-4-6"),
    )
    drafter = DrafterStage(generator=generator, db_session=session)

    if dry_run:
        console.print(f"[yellow][DRY RUN] Would generate drafts for top {top} scored posts")
        session.close()
        return

    result = drafter.run(
        project_id=config.project_id,
        config=config,
        dry_run=dry_run,
        top_n=top,
    )

    drafted_count = result.get("drafted", 0)
    console.print(f"[green]Generated {drafted_count} reply drafts")
    console.print("Run [bold]signalops queue list[/bold] to review them.")
    session.close()

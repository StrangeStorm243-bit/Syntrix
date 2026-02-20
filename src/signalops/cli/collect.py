"""Pipeline run commands — collect, judge, score, draft, all."""

import click


@click.group("run")
def run_group():
    """Run pipeline stages."""


@run_group.command("collect")
@click.pass_context
def collect_cmd(ctx):
    """Collect tweets matching project queries."""
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
    from signalops.pipeline.collector import CollectorStage
    from signalops.connectors.x_api import XConnector
    from signalops.connectors.rate_limiter import RateLimiter

    import os
    from rich.progress import Progress

    bearer_token = os.environ.get("X_BEARER_TOKEN", "")
    rate_limiter = RateLimiter(max_requests=55, window_seconds=900)
    connector = XConnector(bearer_token=bearer_token, rate_limiter=rate_limiter)

    collector = CollectorStage(connector=connector, db_session=session)
    with Progress() as progress:
        task = progress.add_task("Collecting tweets...", total=len(config.queries))
        result = collector.run(config=config, dry_run=dry_run)
        progress.update(task, completed=len(config.queries))

    console.print(
        f"[green]Collected {result.get('total_new', 0)} tweets "
        f"({result.get('total_skipped', 0)} duplicates skipped)"
    )
    session.close()


@run_group.command("all")
@click.pass_context
def run_all_cmd(ctx):
    """Run full pipeline: collect -> normalize -> judge -> score -> draft."""
    from signalops.cli.project import load_active_config
    from signalops.config.defaults import DEFAULT_DB_URL
    from signalops.storage.database import get_engine, get_session, init_db

    console = ctx.obj["console"]
    config = load_active_config(ctx)
    dry_run = ctx.obj["dry_run"]

    engine = get_engine(DEFAULT_DB_URL)
    init_db(engine)
    session = get_session(engine)

    # Lazy imports
    from signalops.pipeline.orchestrator import PipelineOrchestrator
    from signalops.connectors.base import Connector
    from signalops.models.judge_model import LLMPromptJudge
    from signalops.models.draft_model import LLMDraftGenerator
    from signalops.models.llm_gateway import LLMGateway

    import os

    # Build connector
    from signalops.connectors.x_api import XConnector
    from signalops.connectors.rate_limiter import RateLimiter

    bearer_token = os.environ.get("X_BEARER_TOKEN", "")
    rate_limiter = RateLimiter(max_requests=55, window_seconds=900)
    connector = XConnector(bearer_token=bearer_token, rate_limiter=rate_limiter)

    # Build LLM components
    gateway = LLMGateway()
    judge = LLMPromptJudge(
        gateway=gateway,
        model_id=config.llm.get("judge_model", "claude-sonnet-4-6"),
    )
    draft_generator = LLMDraftGenerator(
        gateway=gateway,
        model_id=config.llm.get("draft_model", "claude-sonnet-4-6"),
    )

    orchestrator = PipelineOrchestrator(
        db_session=session,
        connector=connector,
        judge=judge,
        draft_generator=draft_generator,
    )

    if dry_run:
        console.print("[yellow][DRY RUN] Running full pipeline in preview mode...")

    results = orchestrator.run_all(config=config, dry_run=dry_run)

    console.print("\n[bold]Pipeline Results:[/bold]")
    for stage_name, result in results.items():
        if "error" in result:
            console.print(f"  [red]{stage_name}: ERROR — {result['error']}")
        else:
            console.print(f"  [green]{stage_name}: {result}")

    session.close()

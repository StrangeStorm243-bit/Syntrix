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

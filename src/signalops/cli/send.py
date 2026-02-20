"""Send approved drafts as replies."""

import click

from signalops.cli.approve import queue_group
from signalops.cli.project import load_active_config


@queue_group.command("send")
@click.option("--confirm", is_flag=True, default=False, help="Actually send (default is preview)")
@click.pass_context
def queue_send(ctx, confirm):
    """Send approved drafts as replies."""
    from signalops.config.defaults import DEFAULT_DB_URL
    from signalops.storage.database import get_engine, get_session, init_db

    console = ctx.obj["console"]
    config = load_active_config(ctx)
    dry_run = ctx.obj["dry_run"] or not confirm

    engine = get_engine(DEFAULT_DB_URL)
    init_db(engine)
    session = get_session(engine)

    # Lazy imports
    import os

    from signalops.connectors.rate_limiter import RateLimiter
    from signalops.connectors.x_api import XConnector
    from signalops.pipeline.sender import SenderStage

    bearer_token = os.environ.get("X_BEARER_TOKEN", "")
    rate_limiter = RateLimiter(max_requests=55, window_seconds=900)
    connector = XConnector(bearer_token=bearer_token, rate_limiter=rate_limiter)

    sender = SenderStage(connector=connector, db_session=session)

    if dry_run:
        console.print("[yellow]Preview mode — use --confirm to send for real")

    result = sender.run(project_id=config.project_id, config=config, dry_run=dry_run)

    sent = result.get("sent_count", 0)
    skipped = result.get("skipped_rate_limit", 0)
    failed = result.get("failed_count", 0)

    if dry_run:
        console.print(f"Would send {sent} replies. Use --confirm to send.")
    else:
        console.print(f"[green]Sent {sent} replies")

    if skipped:
        console.print(f"[yellow]Skipped {skipped} (rate limit)")
    if failed:
        console.print(f"[red]Failed {failed}")

    session.close()

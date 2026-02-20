"""Notification management CLI commands."""

from __future__ import annotations

import click

from signalops.cli.project import load_active_config
from signalops.notifications.base import get_notifiers


@click.group("notify")
def notify_group() -> None:
    """Notification management commands."""


@notify_group.command("test")
@click.pass_context
def notify_test(ctx: click.Context) -> None:
    """Send a test notification to configured webhooks."""
    console = ctx.obj["console"]
    config = load_active_config(ctx)

    notifiers = get_notifiers(config.notifications)
    if not notifiers:
        console.print("[yellow]No webhooks configured or notifications disabled.[/yellow]")
        console.print("Configure discord_webhook or slack_webhook in your project YAML.")
        return

    title = f"Test notification from {config.project_name}"
    message = "This is a test notification from SignalOps."
    fields = {"Status": "OK", "Project": config.project_name}

    console.print(f"Sending test to {len(notifiers)} webhook(s)...")
    for notifier in notifiers:
        name = type(notifier).__name__
        success = notifier.send(title=title, message=message, fields=fields)
        if success:
            console.print(f"  [green]{name}: sent[/green]")
        else:
            console.print(f"  [red]{name}: failed[/red]")


@notify_group.command("status")
@click.pass_context
def notify_status(ctx: click.Context) -> None:
    """Show webhook configuration and health status."""
    from rich.table import Table

    console = ctx.obj["console"]
    config = load_active_config(ctx)
    nc = config.notifications

    table = Table(title="Notification Configuration")
    table.add_column("Setting", style="bold")
    table.add_column("Value")

    table.add_row("Enabled", str(nc.enabled))
    table.add_row("Min score to notify", str(nc.min_score_to_notify))
    table.add_row(
        "Discord webhook",
        nc.discord_webhook[:40] + "..." if nc.discord_webhook else "not set",
    )
    table.add_row(
        "Slack webhook",
        nc.slack_webhook[:40] + "..." if nc.slack_webhook else "not set",
    )

    console.print(table)

    # Health checks
    notifiers = get_notifiers(nc)
    if not notifiers:
        console.print("\n[yellow]No active webhooks to check.[/yellow]")
        return

    console.print("\n[bold]Health Checks:[/bold]")
    for notifier in notifiers:
        name = type(notifier).__name__
        healthy = notifier.health_check()
        if healthy:
            console.print(f"  [green]{name}: healthy[/green]")
        else:
            console.print(f"  [red]{name}: unreachable[/red]")

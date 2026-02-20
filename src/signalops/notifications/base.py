"""Notifier ABC, payload dataclass, factory, and high-score dispatch."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from signalops.config.schema import NotificationConfig, ProjectConfig

logger = logging.getLogger(__name__)


@dataclass
class NotificationPayload:
    """Structured data for a notification."""

    project_name: str
    lead_count: int
    top_leads: list[dict[str, Any]] = field(default_factory=list)
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(tz=UTC).isoformat()


class Notifier(ABC):
    """Abstract base for webhook notifiers."""

    @abstractmethod
    def send(self, title: str, message: str, fields: dict[str, str] | None = None) -> bool:
        """Send a notification. Returns True if successful."""

    @abstractmethod
    def health_check(self) -> bool:
        """Verify webhook connectivity."""


def get_notifiers(config: NotificationConfig) -> list[Notifier]:
    """Factory: build notifiers from project notification config.

    Returns empty list if notifications disabled.
    """
    if not config.enabled:
        return []

    notifiers: list[Notifier] = []

    if config.discord_webhook:
        from signalops.notifications.discord import DiscordNotifier

        notifiers.append(DiscordNotifier(webhook_url=config.discord_webhook))

    if config.slack_webhook:
        from signalops.notifications.slack import SlackNotifier

        notifiers.append(SlackNotifier(webhook_url=config.slack_webhook))

    return notifiers


def notify_high_scores(
    scores: list[dict[str, Any]],
    config: ProjectConfig,
    notifiers: list[Notifier],
) -> dict[str, Any]:
    """Send notifications for scores above config threshold.

    Returns: {notified: N, failed: N, skipped: N}
    """
    threshold = config.notifications.min_score_to_notify
    high_scores = [s for s in scores if s.get("score", 0) >= threshold]

    if not high_scores:
        return {"notified": 0, "failed": 0, "skipped": len(scores)}

    # Build message
    title = f"{config.project_name}: {len(high_scores)} high-score lead(s)"
    lines: list[str] = []
    fields: dict[str, str] = {}
    for i, lead in enumerate(high_scores[:10], 1):
        author = lead.get("author", "unknown")
        score = lead.get("score", 0)
        preview = lead.get("text_preview", "")[:100]
        lines.append(f"{i}. @{author} (score: {score}) — {preview}")
        fields[f"Lead {i}"] = f"@{author} — score {score}"

    message = "\n".join(lines)

    notified = 0
    failed = 0
    for notifier in notifiers:
        try:
            if notifier.send(title=title, message=message, fields=fields):
                notified += 1
            else:
                failed += 1
        except Exception:
            logger.exception("Notifier %s raised unexpectedly", type(notifier).__name__)
            failed += 1

    return {
        "notified": notified,
        "failed": failed,
        "skipped": len(scores) - len(high_scores),
    }

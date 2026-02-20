"""Discord webhook notifier."""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

from signalops.notifications.base import Notifier

logger = logging.getLogger(__name__)

# Embed colors
COLOR_GREEN = 0x00FF00  # score > 80
COLOR_YELLOW = 0xFFFF00  # score 70-80


class DiscordNotifier(Notifier):
    """Sends notifications via Discord webhook."""

    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    def send(self, title: str, message: str, fields: dict[str, str] | None = None) -> bool:
        """POST embed to Discord webhook. Returns True on success."""
        try:
            import httpx

            embed = self._build_embed(title, message, fields)
            payload: dict[str, Any] = {"embeds": [embed]}

            for attempt in range(3):
                resp = httpx.post(self.webhook_url, json=payload, timeout=10.0)
                if resp.status_code in (200, 204):
                    logger.info("Discord notification sent: %s", title)
                    return True
                if resp.status_code >= 500 and attempt < 2:
                    time.sleep(2**attempt)
                    continue
                logger.warning("Discord webhook returned %d: %s", resp.status_code, resp.text)
                return False
            return False
        except Exception:
            logger.exception("Discord notification failed")
            return False

    def health_check(self) -> bool:
        """GET the webhook URL to verify it's reachable."""
        try:
            import httpx

            resp = httpx.get(self.webhook_url, timeout=10.0)
            return resp.status_code == 200
        except Exception:
            logger.exception("Discord health check failed")
            return False

    @staticmethod
    def _build_embed(
        title: str, message: str, fields: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """Build a Discord embed payload."""
        embed: dict[str, Any] = {
            "title": title,
            "description": message,
            "color": COLOR_GREEN,
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "footer": {"text": "SignalOps Notification"},
        }

        if fields:
            embed["fields"] = [{"name": k, "value": v, "inline": True} for k, v in fields.items()]

        return embed

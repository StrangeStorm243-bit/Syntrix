"""Slack webhook notifier."""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

from signalops.notifications.base import Notifier

logger = logging.getLogger(__name__)


class SlackNotifier(Notifier):
    """Sends notifications via Slack incoming webhook."""

    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    def send(self, title: str, message: str, fields: dict[str, str] | None = None) -> bool:
        """POST Block Kit payload to Slack webhook. Returns True on success."""
        try:
            import httpx

            blocks = self._build_blocks(title, message, fields)
            payload: dict[str, Any] = {"blocks": blocks}

            for attempt in range(3):
                resp = httpx.post(self.webhook_url, json=payload, timeout=10.0)
                if resp.status_code == 200 and resp.text == "ok":
                    logger.info("Slack notification sent: %s", title)
                    return True
                if resp.status_code >= 500 and attempt < 2:
                    time.sleep(2**attempt)
                    continue
                logger.warning("Slack webhook returned %d: %s", resp.status_code, resp.text)
                return False
            return False
        except Exception:
            logger.exception("Slack notification failed")
            return False

    def health_check(self) -> bool:
        """POST a minimal test to verify the webhook is reachable."""
        try:
            import httpx

            resp = httpx.post(
                self.webhook_url,
                json={"text": "SignalOps health check"},
                timeout=10.0,
            )
            return resp.status_code == 200
        except Exception:
            logger.exception("Slack health check failed")
            return False

    @staticmethod
    def _build_blocks(
        title: str, message: str, fields: dict[str, str] | None = None
    ) -> list[dict[str, Any]]:
        """Build Slack Block Kit blocks."""
        blocks: list[dict[str, Any]] = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": title[:150]},
            },
        ]

        # Lead info sections
        if fields:
            for name, value in fields.items():
                blocks.append(
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{name}*\n{value}",
                        },
                    }
                )
                blocks.append({"type": "divider"})
        else:
            blocks.append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": message},
                }
            )

        # Timestamp context
        ts = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC")
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"SignalOps | {ts}"},
                ],
            }
        )

        return blocks

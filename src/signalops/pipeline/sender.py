"""Sender stage — sends approved drafts as replies via the connector."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from signalops.config.schema import ProjectConfig
    from signalops.connectors.base import Connector

logger = logging.getLogger(__name__)


class SenderStage:
    """Sends approved drafts as replies via the connector."""

    def __init__(self, connector: Connector, db_session: Session):
        self.connector = connector
        self.session = db_session

    def run(
        self,
        project_id: str,
        config: ProjectConfig,
        dry_run: bool = False,
    ) -> dict:
        """Send approved/edited drafts as replies."""
        from signalops.storage.audit import log_action
        from signalops.storage.database import Draft, DraftStatus, NormalizedPost

        # Check rate limits first
        is_allowed, reason = self._check_rate_limits(project_id, config)
        if not is_allowed and not dry_run:
            logger.warning("Rate limit exceeded: %s", reason)
            return {
                "sent_count": 0,
                "skipped_rate_limit": 0,
                "failed_count": 0,
                "dry_run": dry_run,
                "rate_limit_reason": reason,
            }

        # Get approved/edited drafts
        drafts = (
            self.session.query(Draft)
            .filter(
                Draft.project_id == project_id,
                Draft.status.in_([DraftStatus.APPROVED, DraftStatus.EDITED]),
            )
            .all()
        )

        sent_count = 0
        skipped_rate_limit = 0
        failed_count = 0

        for draft in drafts:
            # Re-check per-item rate limits
            is_allowed, reason = self._check_rate_limits(project_id, config)
            if not is_allowed:
                skipped_rate_limit += len(drafts) - sent_count - failed_count
                break

            # Get associated post
            post = (
                self.session.query(NormalizedPost)
                .filter_by(id=draft.normalized_post_id)
                .first()
            )
            if not post:
                logger.error("NormalizedPost not found for draft %d", draft.id)
                failed_count += 1
                continue

            # Determine text to send
            send_text = draft.text_final if draft.text_final else draft.text_generated

            if dry_run:
                logger.info(
                    "[DRY RUN] Would send reply to @%s: %s",
                    post.author_username,
                    send_text[:60],
                )
                sent_count += 1
                continue

            try:
                reply_id = self.connector.post_reply(
                    in_reply_to_id=post.platform_id,
                    text=send_text,
                )
                draft.status = DraftStatus.SENT
                draft.sent_at = datetime.now(UTC)
                draft.sent_post_id = reply_id
                self.session.commit()

                log_action(
                    self.session,
                    project_id,
                    "send",
                    entity_type="draft",
                    entity_id=draft.id,
                    details={
                        "reply_to": post.platform_id,
                        "sent_post_id": reply_id,
                    },
                )
                sent_count += 1
            except Exception as e:
                logger.error("Failed to send draft %d: %s", draft.id, e)
                draft.status = DraftStatus.FAILED
                self.session.commit()
                failed_count += 1

        return {
            "sent_count": sent_count,
            "skipped_rate_limit": skipped_rate_limit,
            "failed_count": failed_count,
            "dry_run": dry_run,
        }

    def _check_rate_limits(
        self, project_id: str, config: ProjectConfig
    ) -> tuple[bool, str]:
        """Check if we're within rate limits. Returns (is_allowed, reason)."""
        from signalops.storage.database import Draft, DraftStatus

        now = datetime.now(UTC)
        max_per_hour = config.rate_limits.get("max_replies_per_hour", 5)
        max_per_day = config.rate_limits.get("max_replies_per_day", 20)

        # Count sent in last hour
        hour_ago = now - timedelta(hours=1)
        sent_last_hour = (
            self.session.query(Draft)
            .filter(
                Draft.project_id == project_id,
                Draft.status == DraftStatus.SENT,
                Draft.sent_at >= hour_ago,
            )
            .count()
        )
        if sent_last_hour >= max_per_hour:
            return False, f"Hourly limit reached ({sent_last_hour}/{max_per_hour})"

        # Count sent today
        day_ago = now - timedelta(days=1)
        sent_today = (
            self.session.query(Draft)
            .filter(
                Draft.project_id == project_id,
                Draft.status == DraftStatus.SENT,
                Draft.sent_at >= day_ago,
            )
            .count()
        )
        if sent_today >= max_per_day:
            return False, f"Daily limit reached ({sent_today}/{max_per_day})"

        return True, ""

"""Outcome tracker — polls engagement metrics on sent replies."""

from __future__ import annotations

import logging
from typing import Any, Protocol

from sqlalchemy.orm import Session

from signalops.storage.database import (
    Draft,
    DraftStatus,
    Outcome,
    OutcomeType,
)

logger = logging.getLogger(__name__)

BATCH_SIZE = 100


class EngagementPoller(Protocol):
    """Protocol for polling tweet engagement metrics."""

    def get_tweet_metrics(self, tweet_ids: list[str]) -> dict[str, dict[str, int]]: ...


class OutcomeTracker:
    """Polls engagement on sent replies and records outcomes."""

    def __init__(self, db_session: Session, poller: EngagementPoller) -> None:
        self.db = db_session
        self.poller = poller

    def track_outcomes(self, project_id: str) -> dict[str, Any]:
        """Poll engagement on all sent replies for this project.

        1. Query drafts where status=SENT and sent_post_id IS NOT NULL
        2. Call poller.get_tweet_metrics() with sent_post_id values (batch)
        3. For each reply, compare current metrics against previous outcomes:
           - New likes -> create Outcome(outcome_type=LIKE_RECEIVED)
           - New replies -> create Outcome(outcome_type=REPLY_RECEIVED)
        4. Store baseline metrics in Outcome.details JSON for delta tracking
        5. Return: {tracked: N, new_likes: N, new_replies: N, new_follows: N}
        """
        sent_drafts = (
            self.db.query(Draft)
            .filter(
                Draft.project_id == project_id,
                Draft.status == DraftStatus.SENT,
                Draft.sent_post_id.isnot(None),
            )
            .all()
        )

        if not sent_drafts:
            return {"tracked": 0, "new_likes": 0, "new_replies": 0, "new_follows": 0}

        # Build mapping: sent_post_id -> draft
        draft_by_post_id: dict[str, Draft] = {}
        tweet_ids: list[str] = []
        for d in sent_drafts:
            post_id = str(d.sent_post_id)
            draft_by_post_id[post_id] = d
            tweet_ids.append(post_id)

        # Poll in batches
        all_metrics: dict[str, dict[str, int]] = {}
        for i in range(0, len(tweet_ids), BATCH_SIZE):
            batch = tweet_ids[i : i + BATCH_SIZE]
            batch_metrics = self.poller.get_tweet_metrics(batch)
            all_metrics.update(batch_metrics)

        new_likes = 0
        new_replies = 0
        new_follows = 0

        for post_id, metrics in all_metrics.items():
            draft = draft_by_post_id.get(post_id)
            if draft is None:
                continue

            # Get previous baseline from existing outcomes
            prev = self._get_previous_metrics(draft.id, project_id)  # type: ignore[arg-type]

            likes_delta = metrics.get("likes", 0) - prev.get("likes", 0)
            replies_delta = metrics.get("replies", 0) - prev.get("replies", 0)

            if likes_delta > 0:
                self._record_outcome(
                    draft_id=draft.id,  # type: ignore[arg-type]
                    project_id=project_id,
                    outcome_type=OutcomeType.LIKE_RECEIVED,
                    details={"likes": metrics.get("likes", 0), "delta": likes_delta},
                )
                new_likes += likes_delta

            if replies_delta > 0:
                self._record_outcome(
                    draft_id=draft.id,  # type: ignore[arg-type]
                    project_id=project_id,
                    outcome_type=OutcomeType.REPLY_RECEIVED,
                    details={"replies": metrics.get("replies", 0), "delta": replies_delta},
                )
                new_replies += replies_delta

        self.db.commit()

        return {
            "tracked": len(sent_drafts),
            "new_likes": new_likes,
            "new_replies": new_replies,
            "new_follows": new_follows,
        }

    def check_for_negative(self, project_id: str) -> list[Outcome]:
        """Check if any sent replies resulted in blocks/reports."""
        negatives: list[Outcome] = (
            self.db.query(Outcome)
            .filter(
                Outcome.project_id == project_id,
                Outcome.outcome_type == OutcomeType.NEGATIVE,
            )
            .all()
        )

        if negatives:
            logger.warning(
                "Negative outcomes detected for project %s: %d",
                project_id,
                len(negatives),
            )

        return negatives

    def get_outcome_summary(self, project_id: str) -> dict[str, Any]:
        """Aggregate outcome stats for display in stats dashboard."""
        total_sent = (
            self.db.query(Draft)
            .filter(
                Draft.project_id == project_id,
                Draft.status == DraftStatus.SENT,
            )
            .count()
        )

        outcomes = self.db.query(Outcome).filter(Outcome.project_id == project_id).all()

        likes = sum(1 for o in outcomes if o.outcome_type == OutcomeType.LIKE_RECEIVED)
        replies = sum(1 for o in outcomes if o.outcome_type == OutcomeType.REPLY_RECEIVED)
        follows = sum(1 for o in outcomes if o.outcome_type == OutcomeType.FOLLOW_RECEIVED)
        negatives = sum(1 for o in outcomes if o.outcome_type == OutcomeType.NEGATIVE)

        total_engagement = likes + replies + follows
        engagement_rate = total_engagement / total_sent if total_sent > 0 else 0.0

        return {
            "total_sent": total_sent,
            "likes": likes,
            "replies": replies,
            "follows": follows,
            "negatives": negatives,
            "engagement_rate": round(engagement_rate, 4),
        }

    def _get_previous_metrics(self, draft_id: int, project_id: str) -> dict[str, int]:
        """Get the latest recorded metrics for a draft from existing outcomes."""
        result: dict[str, int] = {"likes": 0, "replies": 0}

        for otype, key in [
            (OutcomeType.LIKE_RECEIVED, "likes"),
            (OutcomeType.REPLY_RECEIVED, "replies"),
        ]:
            latest = (
                self.db.query(Outcome)
                .filter(
                    Outcome.draft_id == draft_id,
                    Outcome.project_id == project_id,
                    Outcome.outcome_type == otype,
                )
                .order_by(Outcome.observed_at.desc())
                .first()
            )
            if latest and latest.details:
                result[key] = latest.details.get(key, 0)

        return result

    def _record_outcome(
        self,
        draft_id: int,
        project_id: str,
        outcome_type: OutcomeType,
        details: dict[str, Any],
    ) -> None:
        """Record a single outcome."""
        outcome = Outcome(
            draft_id=draft_id,
            project_id=project_id,
            outcome_type=outcome_type,
            details=details,
        )
        self.db.add(outcome)

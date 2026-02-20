"""Tests for outcome tracker — engagement polling on sent replies."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from signalops.storage.database import (
    Draft,
    DraftStatus,
    NormalizedPost,
    Outcome,
    OutcomeType,
    RawPost,
)

# ── Helpers ──


def _create_sent_draft(
    db_session: Session,
    project_id: str,
    sent_post_id: str,
    normalized_post_id: int,
) -> Draft:
    """Insert a SENT draft with a sent_post_id."""
    draft = Draft(
        normalized_post_id=normalized_post_id,
        project_id=project_id,
        text_generated="Great thread!",
        model_id="test-model",
        status=DraftStatus.SENT,
        sent_post_id=sent_post_id,
        sent_at=datetime.now(UTC),
    )
    db_session.add(draft)
    db_session.commit()
    return draft


def _seed_post_chain(db_session: Session, project_id: str, platform_id: str = "post1") -> int:
    """Create raw + normalized post, return normalized_post_id."""
    raw = RawPost(
        project_id=project_id,
        platform="x",
        platform_id=platform_id,
        raw_json={"text": "test"},
    )
    db_session.add(raw)
    db_session.flush()

    norm = NormalizedPost(
        raw_post_id=raw.id,
        project_id=project_id,
        platform="x",
        platform_id=platform_id,
        author_id="author1",
        author_username="testuser",
        text_original="test post",
        text_cleaned="test post",
        created_at=datetime.now(UTC),
    )
    db_session.add(norm)
    db_session.commit()
    return norm.id  # type: ignore[return-value]


def _make_poller(metrics: dict[str, dict[str, int]]) -> MagicMock:
    """Create a mock EngagementPoller returning given metrics."""
    poller = MagicMock()
    poller.get_tweet_metrics.return_value = metrics
    return poller


# ── Tests ──


class TestTrackOutcomes:
    """Tests for OutcomeTracker.track_outcomes()."""

    def test_detects_new_likes(self, db_session: Session, sample_project_in_db: str) -> None:
        """New likes on a sent reply create LIKE_RECEIVED outcomes."""
        from signalops.pipeline.outcome_tracker import OutcomeTracker

        pid = sample_project_in_db
        nid = _seed_post_chain(db_session, pid)
        _create_sent_draft(db_session, pid, sent_post_id="reply_1", normalized_post_id=nid)

        poller = _make_poller({"reply_1": {"likes": 5, "replies": 0, "retweets": 0}})
        tracker = OutcomeTracker(db_session=db_session, poller=poller)

        result = tracker.track_outcomes(project_id=pid)

        assert result["tracked"] == 1
        assert result["new_likes"] >= 1

        outcomes = db_session.query(Outcome).filter_by(project_id=pid).all()
        like_outcomes = [o for o in outcomes if o.outcome_type == OutcomeType.LIKE_RECEIVED]
        assert len(like_outcomes) >= 1

    def test_detects_new_replies(self, db_session: Session, sample_project_in_db: str) -> None:
        """New replies on a sent reply create REPLY_RECEIVED outcomes."""
        from signalops.pipeline.outcome_tracker import OutcomeTracker

        pid = sample_project_in_db
        nid = _seed_post_chain(db_session, pid)
        _create_sent_draft(db_session, pid, sent_post_id="reply_2", normalized_post_id=nid)

        poller = _make_poller({"reply_2": {"likes": 0, "replies": 3, "retweets": 0}})
        tracker = OutcomeTracker(db_session=db_session, poller=poller)

        result = tracker.track_outcomes(project_id=pid)

        assert result["tracked"] == 1
        assert result["new_replies"] >= 1

        outcomes = db_session.query(Outcome).filter_by(project_id=pid).all()
        reply_outcomes = [o for o in outcomes if o.outcome_type == OutcomeType.REPLY_RECEIVED]
        assert len(reply_outcomes) >= 1

    def test_noop_when_no_sent_drafts(self, db_session: Session, sample_project_in_db: str) -> None:
        """No sent drafts → no polling, zero results."""
        from signalops.pipeline.outcome_tracker import OutcomeTracker

        pid = sample_project_in_db
        poller = _make_poller({})
        tracker = OutcomeTracker(db_session=db_session, poller=poller)

        result = tracker.track_outcomes(project_id=pid)

        assert result["tracked"] == 0
        assert result["new_likes"] == 0
        assert result["new_replies"] == 0
        poller.get_tweet_metrics.assert_not_called()

    def test_duplicate_outcome_prevention(
        self, db_session: Session, sample_project_in_db: str
    ) -> None:
        """Running track_outcomes twice with same metrics doesn't double-count."""
        from signalops.pipeline.outcome_tracker import OutcomeTracker

        pid = sample_project_in_db
        nid = _seed_post_chain(db_session, pid)
        _create_sent_draft(db_session, pid, sent_post_id="reply_3", normalized_post_id=nid)

        metrics: dict[str, dict[str, int]] = {
            "reply_3": {"likes": 2, "replies": 1, "retweets": 0},
        }
        poller = _make_poller(metrics)
        tracker = OutcomeTracker(db_session=db_session, poller=poller)

        # First run creates outcomes
        result1 = tracker.track_outcomes(project_id=pid)
        assert result1["new_likes"] >= 1

        # Second run with same metrics — no new outcomes
        result2 = tracker.track_outcomes(project_id=pid)
        assert result2["new_likes"] == 0
        assert result2["new_replies"] == 0

    def test_batching_over_100_tweet_ids(
        self, db_session: Session, sample_project_in_db: str
    ) -> None:
        """More than 100 sent tweet IDs are split into batches."""
        from signalops.pipeline.outcome_tracker import OutcomeTracker

        pid = sample_project_in_db

        # Create 105 sent drafts
        for i in range(105):
            nid = _seed_post_chain(db_session, pid, platform_id=f"post_{i}")
            _create_sent_draft(db_session, pid, sent_post_id=f"reply_{i}", normalized_post_id=nid)

        # Poller returns empty metrics (no engagement)
        poller = _make_poller({})
        # Make get_tweet_metrics return empty dict for any call
        poller.get_tweet_metrics.side_effect = lambda ids: {}

        tracker = OutcomeTracker(db_session=db_session, poller=poller)
        result = tracker.track_outcomes(project_id=pid)

        assert result["tracked"] == 105
        # Should have been called more than once (batched)
        assert poller.get_tweet_metrics.call_count >= 2

    def test_delta_tracking_via_details(
        self, db_session: Session, sample_project_in_db: str
    ) -> None:
        """Outcome.details stores baseline metrics for delta tracking."""
        from signalops.pipeline.outcome_tracker import OutcomeTracker

        pid = sample_project_in_db
        nid = _seed_post_chain(db_session, pid)
        _create_sent_draft(db_session, pid, sent_post_id="reply_d", normalized_post_id=nid)

        poller = _make_poller({"reply_d": {"likes": 3, "replies": 0, "retweets": 0}})
        tracker = OutcomeTracker(db_session=db_session, poller=poller)

        tracker.track_outcomes(project_id=pid)

        outcome = (
            db_session.query(Outcome)
            .filter_by(project_id=pid, outcome_type=OutcomeType.LIKE_RECEIVED)
            .first()
        )
        assert outcome is not None
        assert outcome.details is not None
        assert "likes" in outcome.details


class TestCheckForNegative:
    """Tests for OutcomeTracker.check_for_negative()."""

    def test_returns_negative_outcomes(
        self, db_session: Session, sample_project_in_db: str
    ) -> None:
        """Reports existing negative outcomes for the project."""
        from signalops.pipeline.outcome_tracker import OutcomeTracker

        pid = sample_project_in_db
        nid = _seed_post_chain(db_session, pid)
        draft = _create_sent_draft(db_session, pid, sent_post_id="neg_1", normalized_post_id=nid)

        # Manually insert a negative outcome
        neg = Outcome(
            draft_id=draft.id,
            project_id=pid,
            outcome_type=OutcomeType.NEGATIVE,
            details={"reason": "blocked"},
        )
        db_session.add(neg)
        db_session.commit()

        poller = _make_poller({})
        tracker = OutcomeTracker(db_session=db_session, poller=poller)

        negatives = tracker.check_for_negative(project_id=pid)
        assert len(negatives) == 1
        assert negatives[0].outcome_type == OutcomeType.NEGATIVE


class TestGetOutcomeSummary:
    """Tests for OutcomeTracker.get_outcome_summary()."""

    def test_aggregates_outcomes(self, db_session: Session, sample_project_in_db: str) -> None:
        """Summary aggregates counts by outcome type."""
        from signalops.pipeline.outcome_tracker import OutcomeTracker

        pid = sample_project_in_db
        nid = _seed_post_chain(db_session, pid)
        draft = _create_sent_draft(db_session, pid, sent_post_id="sum_1", normalized_post_id=nid)

        # Add various outcomes
        otypes = [
            OutcomeType.LIKE_RECEIVED,
            OutcomeType.LIKE_RECEIVED,
            OutcomeType.REPLY_RECEIVED,
        ]
        for otype in otypes:
            db_session.add(
                Outcome(draft_id=draft.id, project_id=pid, outcome_type=otype, details={})
            )
        db_session.commit()

        poller = _make_poller({})
        tracker = OutcomeTracker(db_session=db_session, poller=poller)

        summary = tracker.get_outcome_summary(project_id=pid)
        assert summary["likes"] == 2
        assert summary["replies"] == 1
        assert summary["total_sent"] >= 1
        assert "engagement_rate" in summary

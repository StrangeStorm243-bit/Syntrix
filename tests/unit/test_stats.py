"""Tests for the enhanced stats dashboard."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from signalops.cli.stats import _gather_stats, _pct
from signalops.storage.database import (
    Draft,
    DraftStatus,
    Judgment,
    JudgmentLabel,
    NormalizedPost,
    Outcome,
    OutcomeType,
    RawPost,
    Score,
)


class TestPct:
    def test_normal(self) -> None:
        assert _pct(31, 100) == "31.0%"

    def test_zero_total(self) -> None:
        assert _pct(0, 0) == "0.0%"

    def test_rounding(self) -> None:
        assert _pct(1, 3) == "33.3%"


class TestGatherStatsEmpty:
    """Stats from an empty database should return zeros, not crash."""

    def test_empty_db(
        self,
        db_session,
        sample_project_in_db,  # type: ignore[no-untyped-def]
    ) -> None:
        stats = _gather_stats(db_session, "test-project")

        assert stats["project_id"] == "test-project"
        p = stats["pipeline"]
        assert p["collected"] == 0
        assert p["judged"] == 0
        assert p["scored"] == 0
        assert p["avg_score"] == 0.0
        assert p["drafted"] == 0
        assert p["sent"] == 0

        o = stats["outcomes"]
        assert o["replies_received"] == 0
        assert o["likes_received"] == 0
        assert o["follows"] == 0
        assert o["negative"] == 0

        t = stats["training"]
        assert t["human_corrections"] == 0
        assert t["agreement_rate"] == 0.0


class TestGatherStatsPopulated:
    """Stats with data should return correct counts and percentages."""

    def _populate_db(self, session) -> None:  # type: ignore[no-untyped-def]
        """Insert sample data into the DB."""
        # Raw posts
        for i in range(10):
            session.add(
                RawPost(
                    project_id="test-project",
                    platform="x",
                    platform_id=f"raw-{i}",
                    raw_json={"text": f"tweet {i}"},
                    query_used="test query",
                )
            )
        session.flush()

        # Normalized posts
        now = datetime.now(tz=UTC)
        for i in range(10):
            session.add(
                NormalizedPost(
                    raw_post_id=i + 1,
                    project_id="test-project",
                    platform="x",
                    platform_id=f"raw-{i}",
                    author_id=f"author-{i}",
                    author_username=f"user{i}",
                    text_original=f"tweet {i}",
                    text_cleaned=f"tweet {i}",
                    created_at=now,
                )
            )
        session.flush()

        # Judgments: 6 relevant, 3 irrelevant, 1 maybe
        labels = (
            [JudgmentLabel.RELEVANT] * 6 + [JudgmentLabel.IRRELEVANT] * 3 + [JudgmentLabel.MAYBE]
        )
        for i, label in enumerate(labels):
            j = Judgment(
                normalized_post_id=i + 1,
                project_id="test-project",
                label=label,  # type: ignore[assignment]
                confidence=0.9,
                model_id="test-model",
            )
            # Add 2 human corrections: 1 agrees, 1 disagrees
            if i == 0:
                j.human_label = JudgmentLabel.RELEVANT  # type: ignore[assignment]
            elif i == 1:
                j.human_label = JudgmentLabel.IRRELEVANT  # type: ignore[assignment]
            session.add(j)
        session.flush()

        # Scores for the 6 relevant posts
        for i in range(6):
            session.add(
                Score(
                    normalized_post_id=i + 1,
                    project_id="test-project",
                    total_score=60.0 + i * 5,  # 60, 65, 70, 75, 80, 85
                    components={"relevance": 0.8},
                    scoring_version="v1",
                )
            )
        session.flush()

        # 3 drafts: 1 approved, 1 sent, 1 pending
        session.add(
            Draft(
                normalized_post_id=1,
                project_id="test-project",
                text_generated="draft 1",
                model_id="test-model",
                status=DraftStatus.APPROVED,  # type: ignore[assignment]
            )
        )
        session.add(
            Draft(
                normalized_post_id=2,
                project_id="test-project",
                text_generated="draft 2",
                model_id="test-model",
                status=DraftStatus.SENT,  # type: ignore[assignment]
            )
        )
        session.add(
            Draft(
                normalized_post_id=3,
                project_id="test-project",
                text_generated="draft 3",
                model_id="test-model",
                status=DraftStatus.PENDING,  # type: ignore[assignment]
            )
        )
        session.flush()

        # Outcomes for the sent draft (draft_id=2)
        session.add(
            Outcome(
                draft_id=2,
                project_id="test-project",
                outcome_type=OutcomeType.LIKE_RECEIVED,  # type: ignore[assignment]
            )
        )
        session.add(
            Outcome(
                draft_id=2,
                project_id="test-project",
                outcome_type=OutcomeType.REPLY_RECEIVED,  # type: ignore[assignment]
            )
        )
        session.commit()

    def test_populated_pipeline_stats(
        self,
        db_session,
        sample_project_in_db,  # type: ignore[no-untyped-def]
    ) -> None:
        self._populate_db(db_session)
        stats = _gather_stats(db_session, "test-project")

        p = stats["pipeline"]
        assert p["collected"] == 10
        assert p["judged"] == 10
        assert p["relevant"] == 6
        assert p["irrelevant"] == 3
        assert p["maybe"] == 1
        assert p["scored"] == 6
        assert p["above_70"] == 3  # scores: 70, 75, 80, 85 -> 4? No, > 70
        # Actually scores are 60, 65, 70, 75, 80, 85
        # > 70 means 75, 80, 85 = 3
        assert p["drafted"] == 3
        assert p["approved"] == 1
        assert p["sent"] == 1

    def test_populated_outcomes(
        self,
        db_session,
        sample_project_in_db,  # type: ignore[no-untyped-def]
    ) -> None:
        self._populate_db(db_session)
        stats = _gather_stats(db_session, "test-project")

        o = stats["outcomes"]
        assert o["replies_received"] == 1
        assert o["likes_received"] == 1
        assert o["follows"] == 0
        assert o["negative"] == 0
        assert o["total_sent"] == 1

    def test_populated_training(
        self,
        db_session,
        sample_project_in_db,  # type: ignore[no-untyped-def]
    ) -> None:
        self._populate_db(db_session)
        stats = _gather_stats(db_session, "test-project")

        t = stats["training"]
        assert t["human_corrections"] == 2
        # 1 agrees (human_label == label), 1 disagrees
        assert t["agreement_rate"] == 50.0


class TestStatsJsonOutput:
    """Test --format json produces valid JSON with expected keys."""

    def test_json_output_has_expected_keys(
        self,
        db_session,
        sample_project_in_db,  # type: ignore[no-untyped-def]
    ) -> None:
        stats = _gather_stats(db_session, "test-project")

        assert "project_id" in stats
        assert "pipeline" in stats
        assert "outcomes" in stats
        assert "training" in stats

        # Pipeline sub-keys
        p = stats["pipeline"]
        for key in [
            "collected",
            "judged",
            "relevant",
            "scored",
            "avg_score",
            "above_70",
            "drafted",
            "sent",
        ]:
            assert key in p

        # Outcomes sub-keys
        o = stats["outcomes"]
        for key in [
            "replies_received",
            "likes_received",
            "follows",
            "negative",
        ]:
            assert key in o

    def test_json_serializable(
        self,
        db_session,
        sample_project_in_db,  # type: ignore[no-untyped-def]
    ) -> None:
        stats = _gather_stats(db_session, "test-project")
        # Should not raise
        result = json.dumps(stats)
        parsed = json.loads(result)
        assert parsed["project_id"] == "test-project"

"""Tests for the A/B test judge implementation."""

from __future__ import annotations

from unittest.mock import MagicMock

from signalops.models.ab_test import ABTestJudge, _create_single_judge
from signalops.models.judge_model import Judgment


def _make_mock_judge(label: str = "relevant", confidence: float = 0.8) -> MagicMock:
    judge = MagicMock()
    judge.judge.return_value = Judgment(
        label=label,
        confidence=confidence,
        reasoning="mock reasoning",
        model_id=f"mock-{label}",
        latency_ms=100.0,
    )
    return judge


class TestABTestJudge:
    def test_routes_to_primary_when_canary_pct_zero(self) -> None:
        primary = _make_mock_judge("relevant")
        canary = _make_mock_judge("irrelevant")
        ab_judge = ABTestJudge(primary=primary, canary=canary, canary_pct=0.0)
        result = ab_judge.judge("test", "", {})
        assert result.label == "relevant"
        primary.judge.assert_called_once()
        canary.judge.assert_not_called()

    def test_routes_to_canary_when_canary_pct_one(self) -> None:
        primary = _make_mock_judge("relevant")
        canary = _make_mock_judge("irrelevant")
        ab_judge = ABTestJudge(primary=primary, canary=canary, canary_pct=1.0)
        result = ab_judge.judge("test", "", {})
        assert result.label == "irrelevant"
        assert result.model_id.startswith("canary:")
        canary.judge.assert_called_once()

    def test_canary_tag_added_to_model_id(self) -> None:
        primary = _make_mock_judge("relevant")
        canary = _make_mock_judge("irrelevant")
        ab_judge = ABTestJudge(primary=primary, canary=canary, canary_pct=1.0)
        result = ab_judge.judge("test", "", {})
        assert result.model_id == "canary:mock-irrelevant"

    def test_primary_model_id_unchanged(self) -> None:
        primary = _make_mock_judge("relevant")
        canary = _make_mock_judge("irrelevant")
        ab_judge = ABTestJudge(primary=primary, canary=canary, canary_pct=0.0)
        result = ab_judge.judge("test", "", {})
        assert result.model_id == "mock-relevant"

    def test_judge_batch(self) -> None:
        primary = _make_mock_judge("relevant")
        canary = _make_mock_judge("irrelevant")
        ab_judge = ABTestJudge(primary=primary, canary=canary, canary_pct=0.0)
        items = [
            {"post_text": "t1", "author_bio": "", "project_context": {}},
            {"post_text": "t2", "author_bio": "", "project_context": {}},
        ]
        results = ab_judge.judge_batch(items)
        assert len(results) == 2

    def test_traffic_split_statistical(self) -> None:
        """With 50% canary, roughly half should go to each."""
        primary = _make_mock_judge("relevant")
        canary = _make_mock_judge("irrelevant")
        ab_judge = ABTestJudge(primary=primary, canary=canary, canary_pct=0.5)

        canary_count = 0
        n = 200
        for _ in range(n):
            result = ab_judge.judge("test", "", {})
            if result.model_id.startswith("canary:"):
                canary_count += 1

        # Should be roughly 50% — allow 20% tolerance
        assert 40 < canary_count < 160

    def test_records_result_with_db_session(self) -> None:
        primary = _make_mock_judge("relevant")
        canary = _make_mock_judge("irrelevant")
        session = MagicMock()
        ab_judge = ABTestJudge(
            primary=primary,
            canary=canary,
            canary_pct=0.0,
            experiment_id="exp-1",
            db_session=session,
        )
        ab_judge.judge("test", "", {})
        session.add.assert_called_once()


class TestCreateSingleJudge:
    def test_finetuned_model(self) -> None:
        gateway = MagicMock()
        judge = _create_single_judge("ft:gpt-4o-mini:org:v1", gateway)
        from signalops.models.finetuned import FineTunedJudge

        assert isinstance(judge, FineTunedJudge)

    def test_regular_model(self) -> None:
        gateway = MagicMock()
        judge = _create_single_judge("claude-sonnet-4-6", gateway)
        from signalops.models.judge_model import LLMPromptJudge

        assert isinstance(judge, LLMPromptJudge)

"""Tests for offline evaluation runner — classification metrics on test sets."""

from __future__ import annotations

import json
import os
import tempfile
from typing import Any

from signalops.models.judge_model import Judgment, RelevanceJudge

# ── Mock Judge ──


class _MockJudge(RelevanceJudge):
    """A mock judge that returns predetermined labels."""

    def __init__(self, predictions: list[str], model_id: str = "mock-judge") -> None:
        self._predictions = predictions
        self._index = 0
        self._model_id = model_id

    def judge(self, post_text: str, author_bio: str, project_context: dict[str, Any]) -> Judgment:
        label = self._predictions[self._index]
        self._index += 1
        return Judgment(
            label=label,
            confidence=0.9,
            reasoning="Mock judgment",
            model_id=self._model_id,
            latency_ms=10.0,
        )

    def judge_batch(self, items: list[dict[str, Any]]) -> list[Judgment]:
        return [
            self.judge(
                item["post_text"],
                item.get("author_bio", ""),
                item.get("project_context", {}),
            )
            for item in items
        ]


def _create_test_set(labels: list[str], texts: list[str] | None = None) -> str:
    """Create a temporary JSONL test set file and return its path."""
    if texts is None:
        texts = [f"Test post {i}" for i in range(len(labels))]

    fd, path = tempfile.mkstemp(suffix=".jsonl")
    with os.fdopen(fd, "w") as f:
        for label, text in zip(labels, texts):
            record = {
                "text": text,
                "author_bio": "Software engineer",
                "gold_label": label,
                "author_followers": 1000,
                "engagement": {"likes": 5, "replies": 2, "retweets": 1},
            }
            f.write(json.dumps(record) + "\n")
    return path


# ── Tests ──


class TestEvaluate:
    """Tests for JudgeEvaluator.evaluate()."""

    def test_perfect_predictions(self) -> None:
        """Perfect predictions -> precision/recall/F1 all 1.0."""
        from signalops.training.evaluator import JudgeEvaluator

        labels = ["relevant", "relevant", "irrelevant", "irrelevant"]
        test_set = _create_test_set(labels)

        try:
            judge = _MockJudge(predictions=labels)
            evaluator = JudgeEvaluator(judge=judge)
            result = evaluator.evaluate(
                test_set_path=test_set,
                project_context={"project_name": "test"},
            )

            assert result["n_examples"] == 4
            assert result["mcc"] == 1.0
            assert "classification_report" in result
            assert "latency_stats" in result
        finally:
            os.unlink(test_set)

    def test_all_wrong_predictions(self) -> None:
        """All-wrong predictions -> metrics near 0."""
        from signalops.training.evaluator import JudgeEvaluator

        gold = ["relevant", "relevant", "irrelevant", "irrelevant"]
        predictions = ["irrelevant", "irrelevant", "relevant", "relevant"]
        test_set = _create_test_set(gold)

        try:
            judge = _MockJudge(predictions=predictions)
            evaluator = JudgeEvaluator(judge=judge)
            result = evaluator.evaluate(
                test_set_path=test_set,
                project_context={"project_name": "test"},
            )

            assert result["n_examples"] == 4
            assert result["mcc"] <= 0.0
        finally:
            os.unlink(test_set)

    def test_handles_missing_optional_fields(self) -> None:
        """JSONL parsing handles missing optional fields."""
        from signalops.training.evaluator import JudgeEvaluator

        fd, path = tempfile.mkstemp(suffix=".jsonl")
        with os.fdopen(fd, "w") as f:
            # Minimal record - only required fields
            record = {"text": "Hello world", "gold_label": "relevant"}
            f.write(json.dumps(record) + "\n")

        try:
            judge = _MockJudge(predictions=["relevant"])
            evaluator = JudgeEvaluator(judge=judge)
            result = evaluator.evaluate(
                test_set_path=path,
                project_context={"project_name": "test"},
            )
            assert result["n_examples"] == 1
        finally:
            os.unlink(path)

    def test_handles_empty_test_set(self) -> None:
        """Empty test set -> graceful result."""
        from signalops.training.evaluator import JudgeEvaluator

        fd, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)

        try:
            judge = _MockJudge(predictions=[])
            evaluator = JudgeEvaluator(judge=judge)
            result = evaluator.evaluate(
                test_set_path=path,
                project_context={"project_name": "test"},
            )
            assert result["n_examples"] == 0
        finally:
            os.unlink(path)


class TestCompare:
    """Tests for JudgeEvaluator.compare()."""

    def test_compare_returns_side_by_side(self) -> None:
        """Compare returns side-by-side results for multiple judges."""
        from signalops.training.evaluator import JudgeEvaluator

        labels = ["relevant", "irrelevant", "relevant"]
        test_set = _create_test_set(labels)

        try:
            judge_a = _MockJudge(predictions=labels, model_id="model-a")
            judge_b = _MockJudge(
                predictions=["irrelevant", "irrelevant", "relevant"],
                model_id="model-b",
            )

            evaluator = JudgeEvaluator(judge=judge_a)
            result = evaluator.compare(
                test_set_path=test_set,
                judges=[judge_a, judge_b],
                project_context={"project_name": "test"},
            )

            assert len(result["results"]) == 2
            assert result["results"][0]["model_id"] == "model-a"
            assert result["results"][1]["model_id"] == "model-b"
        finally:
            os.unlink(test_set)

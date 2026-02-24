"""Tests for the fine-tuned judge implementation."""

from __future__ import annotations

from unittest.mock import MagicMock

from signalops.models.finetuned import FineTunedJudge


class TestFineTunedJudge:
    def _make_judge(self, response: dict[str, object] | None = None) -> FineTunedJudge:
        gateway = MagicMock()
        gateway.complete_json.return_value = response or {
            "label": "relevant",
            "confidence": 0.92,
            "reasoning": "Matches product signals",
        }
        return FineTunedJudge(gateway=gateway, model_id="ft:gpt-4o-mini:org:spectra-v1")

    def test_returns_judgment(self) -> None:
        judge = self._make_judge()
        result = judge.judge("Looking for AI tools", "Engineer", {})
        assert result.label == "relevant"
        assert result.confidence == 0.92
        assert result.model_id == "ft:gpt-4o-mini:org:spectra-v1"

    def test_clamps_confidence(self) -> None:
        judge = self._make_judge({"label": "relevant", "confidence": 1.5, "reasoning": ""})
        result = judge.judge("test", "", {})
        assert result.confidence == 1.0

    def test_clamps_negative_confidence(self) -> None:
        judge = self._make_judge({"label": "relevant", "confidence": -0.5, "reasoning": ""})
        result = judge.judge("test", "", {})
        assert result.confidence == 0.0

    def test_invalid_label_defaults_to_maybe(self) -> None:
        judge = self._make_judge({"label": "unknown_label", "confidence": 0.5, "reasoning": ""})
        result = judge.judge("test", "", {})
        assert result.label == "maybe"

    def test_fallback_on_exception(self) -> None:
        gateway = MagicMock()
        gateway.complete_json.side_effect = RuntimeError("API error")
        judge = FineTunedJudge(gateway=gateway, model_id="ft:gpt-4o-mini:org:v1")
        result = judge.judge("test", "", {})
        assert result.label == "maybe"
        assert result.confidence == 0.3
        assert "fallback:" in result.model_id

    def test_judge_batch(self) -> None:
        judge = self._make_judge()
        items = [
            {"post_text": "tweet 1", "author_bio": "bio 1", "project_context": {}},
            {"post_text": "tweet 2"},
        ]
        results = judge.judge_batch(items)
        assert len(results) == 2
        assert all(r.label == "relevant" for r in results)

    def test_latency_is_positive(self) -> None:
        judge = self._make_judge()
        result = judge.judge("test", "", {})
        assert result.latency_ms >= 0

    def test_system_prompt_includes_project_name(self) -> None:
        judge = self._make_judge()
        prompt = judge._build_system_prompt({"project_name": "TestProject"})
        assert "TestProject" in prompt

    def test_user_prompt_includes_bio(self) -> None:
        judge = self._make_judge()
        prompt = judge._build_user_prompt("tweet text", "AI engineer")
        assert "AI engineer" in prompt

    def test_user_prompt_without_bio(self) -> None:
        judge = self._make_judge()
        prompt = judge._build_user_prompt("tweet text", "")
        assert "Author bio" not in prompt

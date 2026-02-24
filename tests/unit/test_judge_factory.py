"""Tests for the judge factory routing logic."""

from __future__ import annotations

from unittest.mock import MagicMock

from signalops.config.schema import ExperimentConfig, LLMConfig, ProjectConfig
from signalops.models.judge_factory import create_judge


def _make_config(
    judge_model: str = "claude-sonnet-4-6",
    experiments_enabled: bool = False,
) -> ProjectConfig:
    """Build a minimal ProjectConfig for testing."""
    from signalops.config.schema import PersonaConfig, QueryConfig, RelevanceRubric

    return ProjectConfig(
        project_id="test",
        project_name="Test",
        description="Test project",
        queries=[QueryConfig(text="q", label="Q")],
        relevance=RelevanceRubric(
            system_prompt="test",
            positive_signals=["a"],
            negative_signals=["b"],
        ),
        persona=PersonaConfig(name="Bot", role="t", tone="t", voice_notes="t", example_reply="t"),
        llm=LLMConfig(judge_model=judge_model),
        experiments=ExperimentConfig(enabled=experiments_enabled),
    )


class TestJudgeFactory:
    def test_default_returns_llm_prompt_judge(self) -> None:
        from signalops.models.judge_model import LLMPromptJudge

        config = _make_config()
        gateway = MagicMock()
        judge = create_judge(config, gateway)
        assert isinstance(judge, LLMPromptJudge)

    def test_finetuned_model_returns_finetuned_judge(self) -> None:
        from signalops.models.finetuned import FineTunedJudge

        config = _make_config(judge_model="ft:gpt-4o-mini:org:spectra-v1")
        gateway = MagicMock()
        judge = create_judge(config, gateway)
        assert isinstance(judge, FineTunedJudge)

    def test_experiments_enabled_returns_ab_test_judge(self) -> None:
        from signalops.models.ab_test import ABTestJudge

        config = _make_config(experiments_enabled=True)
        gateway = MagicMock()
        judge = create_judge(config, gateway)
        assert isinstance(judge, ABTestJudge)

    def test_finetuned_takes_priority_over_experiments(self) -> None:
        from signalops.models.finetuned import FineTunedJudge

        config = _make_config(judge_model="ft:gpt-4o-mini:org:v1", experiments_enabled=True)
        gateway = MagicMock()
        judge = create_judge(config, gateway)
        assert isinstance(judge, FineTunedJudge)

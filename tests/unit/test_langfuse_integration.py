"""Tests for Langfuse integration — verifies no-op fallback path works correctly."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch


class TestLangfuseNoOpFallback:
    """Verify that the no-op observe decorator works when langfuse is absent."""

    def test_noop_observe_returns_original_function(self) -> None:
        """A no-op observe decorator must return the original function unchanged."""

        def _noop_observe(**kwargs: Any) -> Any:
            def decorator(func: Any) -> Any:
                return func

            return decorator

        @_noop_observe(name="test")
        def my_func(x: int) -> int:
            return x * 2

        assert my_func(5) == 10

    def test_noop_observe_with_as_type_kwarg(self) -> None:
        """The no-op must accept arbitrary kwargs like as_type='generation'."""

        def _noop_observe(**kwargs: Any) -> Any:
            def decorator(func: Any) -> Any:
                return func

            return decorator

        @_noop_observe(as_type="generation")
        def my_func(a: str, b: str) -> str:
            return a + b

        assert my_func("hello", " world") == "hello world"


class TestGatewayLangfuseFlag:
    """Verify the _HAS_LANGFUSE flag exists in each instrumented module."""

    def test_llm_gateway_has_langfuse_flag(self) -> None:
        from signalops.models import llm_gateway

        assert hasattr(llm_gateway, "_HAS_LANGFUSE")
        assert isinstance(llm_gateway._HAS_LANGFUSE, bool)

    def test_judge_model_has_langfuse_flag(self) -> None:
        from signalops.models import judge_model

        assert hasattr(judge_model, "_HAS_LANGFUSE")
        assert isinstance(judge_model._HAS_LANGFUSE, bool)

    def test_draft_model_has_langfuse_flag(self) -> None:
        from signalops.models import draft_model

        assert hasattr(draft_model, "_HAS_LANGFUSE")
        assert isinstance(draft_model._HAS_LANGFUSE, bool)

    def test_ab_test_has_langfuse_flag(self) -> None:
        from signalops.models import ab_test

        assert hasattr(ab_test, "_HAS_LANGFUSE")
        assert isinstance(ab_test._HAS_LANGFUSE, bool)


class TestGatewayCompleteWithoutLangfuse:
    """LLMGateway.complete() works normally regardless of Langfuse availability."""

    def test_complete_works_when_langfuse_unavailable(self) -> None:
        """Patch _HAS_LANGFUSE to False and verify complete() still works."""
        from signalops.models.llm_gateway import LLMGateway

        gateway = LLMGateway(default_model="test-model")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "test response"

        with (
            patch("signalops.models.llm_gateway._HAS_LANGFUSE", False),
            patch("litellm.completion", return_value=mock_response) as mock_completion,
        ):
            result = gateway.complete("system", "user")

        assert result == "test response"
        mock_completion.assert_called_once()


class TestJudgeWithoutLangfuse:
    """LLMPromptJudge.judge() works normally regardless of Langfuse availability."""

    def test_judge_works_when_langfuse_unavailable(self) -> None:
        from signalops.models.judge_model import LLMPromptJudge

        mock_gateway = MagicMock()
        mock_gateway.complete_json.return_value = {
            "label": "relevant",
            "confidence": 0.9,
            "reasoning": "test reasoning",
        }

        judge = LLMPromptJudge(gateway=mock_gateway, model="test-model")

        with patch("signalops.models.judge_model._HAS_LANGFUSE", False):
            result = judge.judge("test post", "test bio", {"project_name": "test"})

        assert result.label == "relevant"
        assert result.confidence == 0.9


class TestDraftWithoutLangfuse:
    """LLMDraftGenerator.generate() works normally regardless of Langfuse."""

    def test_generate_works_when_langfuse_unavailable(self) -> None:
        from signalops.models.draft_model import LLMDraftGenerator

        mock_gateway = MagicMock()
        mock_gateway.complete.return_value = "Great insight!"

        generator = LLMDraftGenerator(gateway=mock_gateway, model="test-model")

        with patch("signalops.models.draft_model._HAS_LANGFUSE", False):
            result = generator.generate(
                "original post",
                "author context",
                {"project_name": "test"},
                {"name": "Bot", "role": "helper", "tone": "friendly"},
            )

        assert result.text == "Great insight!"
        assert result.model_id == "test-model"


class TestABTestWithoutLangfuse:
    """ABTestJudge.judge() works normally regardless of Langfuse availability."""

    def test_ab_judge_works_when_langfuse_unavailable(self) -> None:
        from signalops.models.ab_test import ABTestJudge
        from signalops.models.judge_model import Judgment

        mock_primary = MagicMock()
        mock_primary.judge.return_value = Judgment(
            label="relevant",
            confidence=0.8,
            reasoning="primary judge",
            model_id="primary-model",
            latency_ms=50.0,
        )

        ab_judge = ABTestJudge(
            primary=mock_primary,
            canary=mock_primary,
            canary_pct=0.0,
            experiment_id="test-exp",
        )

        with patch("signalops.models.ab_test._HAS_LANGFUSE", False):
            result = ab_judge.judge("test post", "test bio", {"project_name": "test"})

        assert result.label == "relevant"
        mock_primary.judge.assert_called_once()

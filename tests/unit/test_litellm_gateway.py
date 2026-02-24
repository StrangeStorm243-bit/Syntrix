"""Tests for the LiteLLM gateway wrapper."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from signalops.models.llm_gateway import LLMGateway


class TestLLMGatewayComplete:
    def test_returns_text(self) -> None:
        gateway = LLMGateway(default_model="test-model")
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello world"

        with patch("signalops.models.llm_gateway.litellm") as mock_litellm:
            mock_litellm.completion.return_value = mock_response
            result = gateway.complete("system", "user")

        assert result == "Hello world"
        mock_litellm.completion.assert_called_once()

    def test_uses_default_model(self) -> None:
        gateway = LLMGateway(default_model="claude-sonnet-4-6")
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "response"

        with patch("signalops.models.llm_gateway.litellm") as mock_litellm:
            mock_litellm.completion.return_value = mock_response
            gateway.complete("system", "user")

        call_kwargs = mock_litellm.completion.call_args
        assert call_kwargs.kwargs["model"] == "claude-sonnet-4-6"

    def test_overrides_model(self) -> None:
        gateway = LLMGateway(default_model="default-model")
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "response"

        with patch("signalops.models.llm_gateway.litellm") as mock_litellm:
            mock_litellm.completion.return_value = mock_response
            gateway.complete("system", "user", model="override-model")

        call_kwargs = mock_litellm.completion.call_args
        assert call_kwargs.kwargs["model"] == "override-model"

    def test_overrides_temperature(self) -> None:
        gateway = LLMGateway(temperature=0.3)
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "response"

        with patch("signalops.models.llm_gateway.litellm") as mock_litellm:
            mock_litellm.completion.return_value = mock_response
            gateway.complete("system", "user", temperature=0.9)

        call_kwargs = mock_litellm.completion.call_args
        assert call_kwargs.kwargs["temperature"] == 0.9

    def test_passes_fallback_models(self) -> None:
        gateway = LLMGateway(fallback_models=["fallback-1", "fallback-2"])
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "response"

        with patch("signalops.models.llm_gateway.litellm") as mock_litellm:
            mock_litellm.completion.return_value = mock_response
            gateway.complete("system", "user")

        call_kwargs = mock_litellm.completion.call_args
        assert call_kwargs.kwargs["fallbacks"] == ["fallback-1", "fallback-2"]

    def test_no_fallbacks_passes_none(self) -> None:
        gateway = LLMGateway()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "response"

        with patch("signalops.models.llm_gateway.litellm") as mock_litellm:
            mock_litellm.completion.return_value = mock_response
            gateway.complete("system", "user")

        call_kwargs = mock_litellm.completion.call_args
        assert call_kwargs.kwargs["fallbacks"] is None

    def test_handles_none_content(self) -> None:
        gateway = LLMGateway()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None

        with patch("signalops.models.llm_gateway.litellm") as mock_litellm:
            mock_litellm.completion.return_value = mock_response
            result = gateway.complete("system", "user")

        assert result == ""


class TestLLMGatewayCompleteJSON:
    def test_parses_json(self) -> None:
        gateway = LLMGateway()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"label": "relevant", "confidence": 0.9}'

        with patch("signalops.models.llm_gateway.litellm") as mock_litellm:
            mock_litellm.completion.return_value = mock_response
            result = gateway.complete_json("system", "user")

        assert result == {"label": "relevant", "confidence": 0.9}

    def test_strips_markdown_fences(self) -> None:
        gateway = LLMGateway()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '```json\n{"label": "relevant"}\n```'

        with patch("signalops.models.llm_gateway.litellm") as mock_litellm:
            mock_litellm.completion.return_value = mock_response
            result = gateway.complete_json("system", "user")

        assert result == {"label": "relevant"}

    def test_handles_malformed_json(self) -> None:
        gateway = LLMGateway()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "not valid json at all"

        with patch("signalops.models.llm_gateway.litellm") as mock_litellm:
            mock_litellm.completion.return_value = mock_response
            result = gateway.complete_json("system", "user")

        assert result["error"] == "parse_failed"
        assert "not valid json" in result["raw"]


class TestLLMGatewayGetCost:
    def test_returns_cost(self) -> None:
        gateway = LLMGateway()
        with patch("signalops.models.llm_gateway.litellm") as mock_litellm:
            mock_litellm.completion_cost.return_value = 0.0015
            cost = gateway.get_cost("claude-sonnet-4-6", 100, 50)

        assert cost == 0.0015

    def test_returns_zero_on_error(self) -> None:
        gateway = LLMGateway()
        with patch("signalops.models.llm_gateway.litellm") as mock_litellm:
            mock_litellm.completion_cost.side_effect = Exception("unknown model")
            cost = gateway.get_cost("unknown-model", 100, 50)

        assert cost == 0.0

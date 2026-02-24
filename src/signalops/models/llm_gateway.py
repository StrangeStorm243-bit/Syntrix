"""LLM Gateway — thin wrapper around LiteLLM for unified model access."""

from __future__ import annotations

import json
import logging
from typing import Any

import litellm

logger = logging.getLogger(__name__)

# Disable LiteLLM's verbose logging
litellm.suppress_debug_info = True


class LLMGateway:
    """Unified LLM interface powered by LiteLLM.

    Supports 100+ providers (OpenAI, Anthropic, Cohere, local models, etc.)
    via a single API. Handles routing, retries, and fallbacks.

    LiteLLM reads API keys from environment variables automatically:
    - ANTHROPIC_API_KEY for Claude models
    - OPENAI_API_KEY for GPT / fine-tuned models
    """

    def __init__(
        self,
        default_model: str = "claude-sonnet-4-6",
        fallback_models: list[str] | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> None:
        self._default_model = default_model
        self._fallback_models = fallback_models or []
        self._temperature = temperature
        self._max_tokens = max_tokens

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        temperature: float | None = None,
        **kwargs: Any,
    ) -> str:
        """Get a text completion from the LLM."""
        model = model or self._default_model
        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = litellm.completion(
            model=model,
            messages=messages,
            temperature=temperature if temperature is not None else self._temperature,
            max_tokens=self._max_tokens,
            fallbacks=self._fallback_models if self._fallback_models else None,
            num_retries=2,
        )
        return str(response.choices[0].message.content or "")

    def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        temperature: float | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Get a JSON completion, parsed into a dict."""
        raw = self.complete(system_prompt, user_prompt, model, temperature)
        # Strip markdown code fences if present
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
        try:
            return json.loads(raw)  # type: ignore[no-any-return]
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM JSON response: %s", raw[:200])
            return {"error": "parse_failed", "raw": raw}

    def get_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Get cost estimate for a completion using LiteLLM's cost tracking."""
        try:
            return float(
                litellm.completion_cost(
                    model=model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                )
            )
        except Exception:
            return 0.0

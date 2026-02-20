"""Anthropic Claude provider implementation."""

from __future__ import annotations

import json
import re
from typing import Any

from signalops.models.providers.base import LLMProvider, ProviderConfig


class AnthropicProvider(LLMProvider):
    """LLM provider for Anthropic Claude models.

    Supported models: claude-sonnet-4-6, claude-haiku-4-5, claude-opus-4-6
    """

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config
        import anthropic

        self._client = anthropic.Anthropic(api_key=config.api_key, timeout=config.timeout)

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        response = self._client.messages.create(
            model=self.config.model,
            max_tokens=max_tokens or self.config.max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=temperature if temperature is not None else self.config.temperature,
        )
        block = response.content[0]
        return block.text if hasattr(block, "text") else str(block)

    def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        raw = self.complete(system_prompt, user_prompt)
        try:
            result: dict[str, Any] = json.loads(raw)
            return result
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
            if match:
                try:
                    result = json.loads(match.group(1).strip())
                    return result
                except json.JSONDecodeError:
                    pass
            # Try to find raw JSON object in the response
            match = re.search(r"\{[\s\S]*\}", raw)
            if match:
                try:
                    result = json.loads(match.group(0))
                    return result
                except json.JSONDecodeError:
                    pass
            raise ValueError(f"Could not parse JSON from response: {raw[:200]}")

    @property
    def model_id(self) -> str:
        return self.config.model

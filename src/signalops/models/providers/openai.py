"""OpenAI provider implementation."""

from __future__ import annotations

import json
from typing import Any

from signalops.models.providers.base import LLMProvider, ProviderConfig


class OpenAIProvider(LLMProvider):
    """LLM provider for OpenAI models.

    Supported models: gpt-4o, gpt-4o-mini
    """

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config
        import openai

        self._client = openai.OpenAI(api_key=config.api_key, timeout=config.timeout)

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        response = self._client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature if temperature is not None else self.config.temperature,
            max_tokens=max_tokens or self.config.max_tokens,
        )
        content = response.choices[0].message.content
        return content or ""

    def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = self._client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or ""
        result: dict[str, Any] = json.loads(raw)
        return result

    @property
    def model_id(self) -> str:
        return self.config.model

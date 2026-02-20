"""Abstract base class for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""

    api_key: str
    model: str
    temperature: float = 0.3
    max_tokens: int = 1024
    timeout: float = 30.0


class LLMProvider(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    def __init__(self, config: ProviderConfig) -> None: ...

    @abstractmethod
    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Returns raw text completion."""

    @abstractmethod
    def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Returns parsed JSON from LLM. Handles parsing errors."""

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Returns the model identifier string."""

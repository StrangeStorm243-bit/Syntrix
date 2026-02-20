"""LLM Gateway — routes calls to providers with retries and circuit breaking."""

from __future__ import annotations

import logging
import time

from signalops.models.providers.base import LLMProvider, ProviderConfig

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Trips after N failures, stays open for recovery_timeout seconds."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._failure_count = 0
        self._last_failure_time: float | None = None
        self._tripped = False

    def record_success(self) -> None:
        self._failure_count = 0
        self._tripped = False

    def record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self._failure_threshold:
            self._tripped = True

    def is_open(self) -> bool:
        if not self._tripped:
            return False
        # Check if recovery timeout has elapsed
        if self._last_failure_time is not None:
            elapsed = time.monotonic() - self._last_failure_time
            if elapsed >= self._recovery_timeout:
                # Move to half-open — allow one attempt
                return False
        return True

    @property
    def state(self) -> str:
        if not self._tripped:
            return "closed"
        if self._last_failure_time is not None:
            elapsed = time.monotonic() - self._last_failure_time
            if elapsed >= self._recovery_timeout:
                return "half-open"
        return "open"


class LLMGateway:
    """Routes LLM calls to the right provider. Handles retries and circuit breaking."""

    def __init__(
        self,
        anthropic_api_key: str | None = None,
        openai_api_key: str | None = None,
        default_model: str = "claude-sonnet-4-6",
    ):
        self._api_keys = {
            "anthropic": anthropic_api_key,
            "openai": openai_api_key,
        }
        self._providers: dict[str, LLMProvider] = {}
        self._circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
        self._default_model = default_model

    def _get_provider(self, model: str) -> LLMProvider:
        """Route to provider based on model name prefix. Cache instances."""
        if model in self._providers:
            return self._providers[model]

        if model.startswith("claude-"):
            from signalops.models.providers.anthropic import AnthropicProvider

            api_key = self._api_keys.get("anthropic")
            if not api_key:
                raise ValueError("Anthropic API key not configured")
            config = ProviderConfig(api_key=api_key, model=model)
            provider = AnthropicProvider(config)
        elif model.startswith("gpt-"):
            from signalops.models.providers.openai import OpenAIProvider

            api_key = self._api_keys.get("openai")
            if not api_key:
                raise ValueError("OpenAI API key not configured")
            config = ProviderConfig(api_key=api_key, model=model)
            provider = OpenAIProvider(config)
        else:
            raise ValueError(f"Unknown model prefix: {model}")

        self._providers[model] = provider
        return provider

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        **kwargs,
    ) -> str:
        """Complete with retry logic and circuit breaking."""
        model = model or self._default_model
        provider = self._get_provider(model)

        last_error: Exception | None = None
        for attempt in range(3):
            if self._circuit_breaker.is_open():
                raise RuntimeError(
                    f"Circuit breaker is open after repeated failures (state={self._circuit_breaker.state})"
                )
            try:
                result = provider.complete(system_prompt, user_prompt, **kwargs)
                self._circuit_breaker.record_success()
                return result
            except Exception as e:
                last_error = e
                self._circuit_breaker.record_failure()
                logger.warning(
                    "LLM call failed (attempt %d/3, model=%s): %s",
                    attempt + 1,
                    model,
                    e,
                )
                if attempt < 2:
                    time.sleep(2**attempt)  # 1s, 2s

        raise RuntimeError(f"All 3 retry attempts failed for model {model}") from last_error

    def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        **kwargs,
    ) -> dict:
        """Complete JSON with retry logic and circuit breaking."""
        model = model or self._default_model
        provider = self._get_provider(model)

        last_error: Exception | None = None
        for attempt in range(3):
            if self._circuit_breaker.is_open():
                raise RuntimeError(
                    f"Circuit breaker is open after repeated failures (state={self._circuit_breaker.state})"
                )
            try:
                result = provider.complete_json(system_prompt, user_prompt, **kwargs)
                self._circuit_breaker.record_success()
                return result
            except Exception as e:
                last_error = e
                self._circuit_breaker.record_failure()
                logger.warning(
                    "LLM JSON call failed (attempt %d/3, model=%s): %s",
                    attempt + 1,
                    model,
                    e,
                )
                if attempt < 2:
                    time.sleep(2**attempt)

        raise RuntimeError(
            f"All 3 retry attempts failed for model {model}"
        ) from last_error

"""Relevance judge: LLM-based and keyword-based implementations."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from signalops.models.llm_gateway import LLMGateway


@dataclass
class Judgment:
    """Result of a relevance judgment."""

    label: str  # "relevant", "irrelevant", "maybe"
    confidence: float  # 0.0 - 1.0
    reasoning: str
    model_id: str
    latency_ms: float


class RelevanceJudge(ABC):
    """Abstract interface for relevance judges."""

    @abstractmethod
    def judge(self, post_text: str, author_bio: str, project_context: dict[str, Any]) -> Judgment:
        """Judge whether a post is relevant to the project."""

    @abstractmethod
    def judge_batch(self, items: list[dict[str, Any]]) -> list[Judgment]:
        """Batch judgment for efficiency."""


class LLMPromptJudge(RelevanceJudge):
    """Uses an LLM to judge relevance based on project context."""

    def __init__(self, gateway: LLMGateway, model: str = "claude-sonnet-4-6"):
        self._gateway = gateway
        self._model = model

    def judge(self, post_text: str, author_bio: str, project_context: dict[str, Any]) -> Judgment:
        system_prompt = self._build_system_prompt(project_context)
        user_prompt = self._build_user_prompt(post_text, author_bio, project_context)

        start = time.perf_counter()
        try:
            result = self._gateway.complete_json(system_prompt, user_prompt, model=self._model)
            latency_ms = (time.perf_counter() - start) * 1000

            label = result.get("label", "maybe")
            if label not in ("relevant", "irrelevant", "maybe"):
                label = "maybe"

            confidence = float(result.get("confidence", 0.5))
            confidence = max(0.0, min(1.0, confidence))

            return Judgment(
                label=label,
                confidence=confidence,
                reasoning=result.get("reasoning", ""),
                model_id=self._model,
                latency_ms=latency_ms,
            )
        except Exception:
            latency_ms = (time.perf_counter() - start) * 1000
            return Judgment(
                label="maybe",
                confidence=0.3,
                reasoning="Fallback: failed to parse LLM response",
                model_id="fallback-parse-error",
                latency_ms=latency_ms,
            )

    def judge_batch(self, items: list[dict[str, Any]]) -> list[Judgment]:
        results = []
        for item in items:
            judgment = self.judge(
                item["post_text"],
                item.get("author_bio", ""),
                item.get("project_context", {}),
            )
            results.append(judgment)
        return results

    def _build_system_prompt(self, project_context: dict[str, Any]) -> str:
        project_name = project_context.get("project_name", "Unknown Project")
        description = project_context.get("description", "")
        relevance = project_context.get("relevance", {})
        system_prompt_text = relevance.get("system_prompt", "")
        positive_signals = relevance.get("positive_signals", [])
        negative_signals = relevance.get("negative_signals", [])

        positive_block = "\n".join(f"- {s}" for s in positive_signals)
        negative_block = "\n".join(f"- {s}" for s in negative_signals)

        return (
            f"You are a relevance judge for {project_name}. {description}\n\n"
            f"{system_prompt_text}\n\n"
            f"Positive signals that make a tweet RELEVANT:\n{positive_block}\n\n"
            f"Negative signals that make a tweet IRRELEVANT:\n{negative_block}\n\n"
            "Evaluate the following tweet and respond with ONLY valid JSON:\n"
            "{\n"
            '  "label": "relevant" | "irrelevant" | "maybe",\n'
            '  "confidence": 0.0 to 1.0,\n'
            '  "reasoning": "1-2 sentence explanation"\n'
            "}"
        )

    def _build_user_prompt(
        self, post_text: str, author_bio: str, metrics: dict[str, Any] | None = None
    ) -> str:
        parts = [f'Tweet: "{post_text}"']
        if author_bio:
            parts.append(f'Author bio: "{author_bio}"')
        if metrics:
            parts.append(
                f"Engagement: {metrics.get('likes', 0)} likes, "
                f"{metrics.get('replies', 0)} replies, "
                f"{metrics.get('retweets', 0)} retweets"
            )
        return "\n".join(parts)


class KeywordFallbackJudge(RelevanceJudge):
    """Rule-based judge using keyword matching."""

    def __init__(
        self,
        keywords_required: list[str] | None = None,
        keywords_excluded: list[str] | None = None,
    ):
        self._keywords_required = keywords_required or []
        self._keywords_excluded = keywords_excluded or []

    def judge(self, post_text: str, author_bio: str, project_context: dict[str, Any]) -> Judgment:
        start = time.perf_counter()
        text_lower = post_text.lower()

        # Check excluded keywords
        for kw in self._keywords_excluded:
            if kw.lower() in text_lower:
                latency_ms = (time.perf_counter() - start) * 1000
                return Judgment(
                    label="irrelevant",
                    confidence=0.9,
                    reasoning=f"Excluded keyword found: '{kw}'",
                    model_id="keyword-fallback",
                    latency_ms=latency_ms,
                )

        # Check required keywords
        if self._keywords_required:
            found = any(kw.lower() in text_lower for kw in self._keywords_required)
            if not found:
                latency_ms = (time.perf_counter() - start) * 1000
                return Judgment(
                    label="irrelevant",
                    confidence=0.7,
                    reasoning="No required keywords found",
                    model_id="keyword-fallback",
                    latency_ms=latency_ms,
                )

        latency_ms = (time.perf_counter() - start) * 1000
        return Judgment(
            label="maybe",
            confidence=0.4,
            reasoning="No keyword exclusion or requirement triggered",
            model_id="keyword-fallback",
            latency_ms=latency_ms,
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

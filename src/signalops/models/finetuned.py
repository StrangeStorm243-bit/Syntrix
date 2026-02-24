"""Fine-tuned model judge — calls cloud provider fine-tuned endpoints."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from signalops.models.judge_model import Judgment, RelevanceJudge

if TYPE_CHECKING:
    from signalops.models.llm_gateway import LLMGateway


class FineTunedJudge(RelevanceJudge):
    """Calls a fine-tuned model (OpenAI or Anthropic) for relevance judgment."""

    def __init__(self, gateway: LLMGateway, model_id: str) -> None:
        self._gateway = gateway
        self._model_id = model_id

    def judge(self, post_text: str, author_bio: str, project_context: dict[str, Any]) -> Judgment:
        """Judge using fine-tuned model. Same prompt format as training data."""
        system_prompt = self._build_system_prompt(project_context)
        user_prompt = self._build_user_prompt(post_text, author_bio)

        start = time.perf_counter()
        try:
            result = self._gateway.complete_json(system_prompt, user_prompt, model=self._model_id)
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
                model_id=self._model_id,
                latency_ms=latency_ms,
            )
        except Exception:
            latency_ms = (time.perf_counter() - start) * 1000
            return Judgment(
                label="maybe",
                confidence=0.3,
                reasoning="Fallback: fine-tuned model call failed",
                model_id=f"fallback:{self._model_id}",
                latency_ms=latency_ms,
            )

    def judge_batch(self, items: list[dict[str, Any]]) -> list[Judgment]:
        """Batch by calling individual judge sequentially."""
        return [
            self.judge(
                item["post_text"],
                item.get("author_bio", ""),
                item.get("project_context", {}),
            )
            for item in items
        ]

    def _build_system_prompt(self, project_context: dict[str, Any]) -> str:
        """Use the same format as training data export for consistency."""
        project_name = project_context.get("project_name", "Unknown Project")
        description = project_context.get("description", "")
        relevance = project_context.get("relevance", {})
        system_prompt_text = relevance.get("system_prompt", "")
        positive_signals: list[str] = relevance.get("positive_signals", [])
        negative_signals: list[str] = relevance.get("negative_signals", [])

        positive_block = "\n".join(f"- {s}" for s in positive_signals)
        negative_block = "\n".join(f"- {s}" for s in negative_signals)

        return (
            f"You are a relevance judge for {project_name}. {description}\n\n"
            f"{system_prompt_text}\n\n"
            f"Positive signals:\n{positive_block}\n\n"
            f"Negative signals:\n{negative_block}\n\n"
            'Respond with JSON: {"label": "relevant"|"irrelevant"|"maybe", '
            '"confidence": 0.0-1.0, "reasoning": "..."}'
        )

    def _build_user_prompt(self, post_text: str, author_bio: str) -> str:
        parts = [f'Tweet: "{post_text}"']
        if author_bio:
            parts.append(f'Author bio: "{author_bio}"')
        return "\n".join(parts)

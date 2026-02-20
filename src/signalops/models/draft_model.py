"""Draft generator: LLM-based reply draft generation with persona system."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from signalops.models.llm_gateway import LLMGateway


@dataclass
class Draft:
    """A generated reply draft."""

    text: str
    tone: str
    model_id: str
    template_used: str | None


class DraftGenerator(ABC):
    """Abstract interface for draft generators."""

    @abstractmethod
    def generate(
        self,
        post_text: str,
        author_context: str,
        project_context: dict[str, Any],
        persona: dict[str, Any],
    ) -> Draft:
        """Generate a reply draft for a relevant post."""


class LLMDraftGenerator(DraftGenerator):
    """Uses an LLM to generate reply drafts based on persona."""

    MAX_CHARS = 240

    def __init__(self, gateway: LLMGateway, model: str = "claude-sonnet-4-6"):
        self._gateway = gateway
        self._model = model

    def generate(
        self,
        post_text: str,
        author_context: str,
        project_context: dict[str, Any],
        persona: dict[str, Any],
    ) -> Draft:
        system_prompt = self._build_system_prompt(persona, project_context)
        user_prompt = self._build_user_prompt(post_text, author_context, project_context)

        text = self._gateway.complete(system_prompt, user_prompt, model=self._model).strip()

        # Enforce character limit
        if len(text) > self.MAX_CHARS:
            shorten_prompt = (
                f"Shorten this reply to under {self.MAX_CHARS} characters while "
                f"keeping the same meaning and tone:\n\n{text}"
            )
            text = self._gateway.complete(system_prompt, shorten_prompt, model=self._model).strip()

        # Hard truncate if still over
        if len(text) > self.MAX_CHARS:
            text = text[: self.MAX_CHARS].rsplit(" ", 1)[0]

        return Draft(
            text=text,
            tone=persona.get("tone", "helpful"),
            model_id=self._model,
            template_used=None,
        )

    def _build_system_prompt(self, persona: dict[str, Any], project_context: dict[str, Any]) -> str:
        project_name = project_context.get("project_name", "the product")
        return (
            f"You are {persona.get('name', 'an assistant')}, "
            f"a {persona.get('role', 'team member')} for {project_name}.\n"
            f"Your tone is {persona.get('tone', 'helpful')}.\n\n"
            f"{persona.get('voice_notes', '')}\n\n"
            f"Example reply style:\n"
            f'"{persona.get("example_reply", "")}"\n\n'
            f"Rules:\n"
            f"- Keep reply under {self.MAX_CHARS} characters\n"
            f"- Be genuinely helpful, not salesy\n"
            f"- Reference something specific from their tweet\n"
            f"- Only mention {project_name} if it's truly relevant to their situation\n"
            f"- No hashtags, no emojis (unless the original poster uses them)\n"
            f"- Sound human, not corporate\n"
            f'- Never use phrases like "I understand your frustration" or "Great question!"'
        )

    def _build_user_prompt(
        self, post_text: str, author_context: str, project_context: dict[str, Any]
    ) -> str:
        parts = [
            "Write a reply to this tweet.\n",
            f'Tweet: "{post_text}"',
        ]
        if author_context:
            parts.append(f"Author: {author_context}")
        query_used = project_context.get("query_used", "")
        score = project_context.get("score", "")
        reasoning = project_context.get("reasoning", "")
        if query_used:
            parts.append(f'Context: Found via query "{query_used}", scored {score}/100.')
        if reasoning:
            parts.append(f'Relevance reasoning: "{reasoning}"')
        return "\n".join(parts)

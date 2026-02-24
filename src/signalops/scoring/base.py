"""Scoring plugin abstract base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class PluginScoreResult:
    """Result from a single scoring plugin."""

    plugin_name: str
    score: float  # 0-100 contribution
    weight: float  # How much this contributes to final score
    details: dict[str, Any]  # Plugin-specific details for transparency
    version: str = "1.0"


class ScoringPlugin(ABC):
    """Abstract interface for scoring plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique plugin name."""

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version string."""

    @property
    def default_weight(self) -> float:
        """Default weight if not overridden in config. Should be 0.0-1.0."""
        return 0.1

    @abstractmethod
    def score(
        self,
        post: dict[str, Any],
        judgment: dict[str, Any],
        config: dict[str, Any],
    ) -> PluginScoreResult:
        """Score a lead.

        Args:
            post: Normalized post data (text, author, engagement, etc.)
            judgment: Judgment result (label, confidence, reasoning)
            config: Project config dict for plugin-specific settings

        Returns:
            PluginScoreResult with score 0-100, weight, and details
        """

    def validate_config(self, config: dict[str, Any]) -> list[str]:
        """Validate plugin-specific config. Returns list of errors (empty = valid)."""
        return []

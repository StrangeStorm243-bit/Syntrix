"""Keyword boost scoring plugin — boosts score for specific keywords."""

from __future__ import annotations

from typing import Any

from signalops.scoring.base import PluginScoreResult, ScoringPlugin


class KeywordBoostPlugin(ScoringPlugin):
    """Boosts score when post contains configured keywords."""

    @property
    def name(self) -> str:
        return "keyword_boost"

    @property
    def version(self) -> str:
        return "1.0"

    @property
    def default_weight(self) -> float:
        return 0.0  # Only active when configured

    def score(
        self,
        post: dict[str, Any],
        judgment: dict[str, Any],
        config: dict[str, Any],
    ) -> PluginScoreResult:
        boost_keywords: list[str] = config.get("keyword_boost", {}).get("keywords", [])
        if not boost_keywords:
            return PluginScoreResult(
                plugin_name=self.name,
                score=0.0,
                weight=0.0,
                details={"active": False},
            )

        text = str(post.get("text_cleaned", "")).lower()
        matched = [kw for kw in boost_keywords if kw.lower() in text]
        score = min(len(matched) * 20, 100)

        return PluginScoreResult(
            plugin_name=self.name,
            score=float(score),
            weight=config.get("keyword_boost", {}).get("weight", 0.05),
            details={"matched_keywords": matched},
            version=self.version,
        )

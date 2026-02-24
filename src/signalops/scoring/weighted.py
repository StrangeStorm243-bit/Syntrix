"""Default weighted scorer — extracted from pipeline/scorer.py."""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any

from signalops.scoring.base import PluginScoreResult, ScoringPlugin


class RelevancePlugin(ScoringPlugin):
    """Score based on judgment confidence and label."""

    @property
    def name(self) -> str:
        return "relevance_judgment"

    @property
    def version(self) -> str:
        return "1.0"

    @property
    def default_weight(self) -> float:
        return 0.35

    def score(
        self,
        post: dict[str, Any],
        judgment: dict[str, Any],
        config: dict[str, Any],
    ) -> PluginScoreResult:
        multiplier = {"relevant": 1.0, "maybe": 0.3, "irrelevant": 0.0}
        label = judgment.get("label", "maybe")
        confidence = float(judgment.get("confidence", 0.5))
        raw_score = confidence * multiplier.get(label, 0.0) * 100

        return PluginScoreResult(
            plugin_name=self.name,
            score=raw_score,
            weight=config.get("weights", {}).get("relevance_judgment", self.default_weight),
            details={"label": label, "confidence": confidence},
            version=self.version,
        )


class AuthorityPlugin(ScoringPlugin):
    """Score based on author followers, verified status, bio match."""

    @property
    def name(self) -> str:
        return "author_authority"

    @property
    def version(self) -> str:
        return "1.0"

    @property
    def default_weight(self) -> float:
        return 0.25

    def score(
        self,
        post: dict[str, Any],
        judgment: dict[str, Any],
        config: dict[str, Any],
    ) -> PluginScoreResult:
        score = 0.0
        followers = int(post.get("author_followers", 0))
        if followers > 0:
            score += min(math.log10(followers) / 6 * 60, 60)
        if post.get("author_verified", False):
            score += 20
        score += 10  # Baseline for having a profile

        return PluginScoreResult(
            plugin_name=self.name,
            score=min(score, 100),
            weight=config.get("weights", {}).get("author_authority", self.default_weight),
            details={"followers": followers, "verified": post.get("author_verified", False)},
            version=self.version,
        )


class EngagementPlugin(ScoringPlugin):
    """Score based on likes, replies, retweets, views."""

    @property
    def name(self) -> str:
        return "engagement_signals"

    @property
    def version(self) -> str:
        return "1.0"

    @property
    def default_weight(self) -> float:
        return 0.15

    def score(
        self,
        post: dict[str, Any],
        judgment: dict[str, Any],
        config: dict[str, Any],
    ) -> PluginScoreResult:
        score = 0.0
        likes = int(post.get("likes", 0))
        replies = int(post.get("replies", 0))
        retweets = int(post.get("retweets", 0))
        views = int(post.get("views", 0))

        score += min(likes * 3, 30)
        score += min(replies * 5, 30)
        score += min(retweets * 4, 20)
        score += min(views / 500, 20)

        return PluginScoreResult(
            plugin_name=self.name,
            score=min(score, 100),
            weight=config.get("weights", {}).get("engagement_signals", self.default_weight),
            details={"likes": likes, "replies": replies, "retweets": retweets, "views": views},
            version=self.version,
        )


class RecencyPlugin(ScoringPlugin):
    """Score based on post age — newer = higher."""

    @property
    def name(self) -> str:
        return "recency"

    @property
    def version(self) -> str:
        return "1.0"

    @property
    def default_weight(self) -> float:
        return 0.15

    def score(
        self,
        post: dict[str, Any],
        judgment: dict[str, Any],
        config: dict[str, Any],
    ) -> PluginScoreResult:
        created_at = post.get("created_at")
        if not created_at:
            return PluginScoreResult(
                plugin_name=self.name,
                score=0.0,
                weight=self.default_weight,
                details={"hours_ago": None},
            )

        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)

        hours_ago = (datetime.now(UTC) - created_at).total_seconds() / 3600
        if hours_ago <= 0:
            raw_score = 100.0
        elif hours_ago >= 168:
            raw_score = 0.0
        else:
            raw_score = max(0.0, 100 * math.exp(-0.03 * hours_ago))

        return PluginScoreResult(
            plugin_name=self.name,
            score=raw_score,
            weight=config.get("weights", {}).get("recency", self.default_weight),
            details={"hours_ago": round(hours_ago, 1)},
            version=self.version,
        )


class IntentPlugin(ScoringPlugin):
    """Score based on intent signals in text."""

    @property
    def name(self) -> str:
        return "intent_strength"

    @property
    def version(self) -> str:
        return "1.0"

    @property
    def default_weight(self) -> float:
        return 0.10

    def score(
        self,
        post: dict[str, Any],
        judgment: dict[str, Any],
        config: dict[str, Any],
    ) -> PluginScoreResult:
        text = str(post.get("text_cleaned", "")).lower()
        score = 0.0
        signals_found: list[str] = []

        if "?" in text:
            score += 40
            signals_found.append("question_mark")

        search_phrases = [
            "looking for",
            "anyone recommend",
            "anyone know",
            "suggestions for",
            "alternative to",
            "switching from",
        ]
        if any(phrase in text for phrase in search_phrases):
            score += 30
            signals_found.append("search_phrase")

        pain_phrases = [
            "frustrated",
            "annoying",
            "painful",
            "hate",
            "takes forever",
            "waste of time",
            "there has to be",
        ]
        if any(phrase in text for phrase in pain_phrases):
            score += 20
            signals_found.append("pain_phrase")

        eval_phrases = ["evaluating", "comparing", "trying out", "testing"]
        if any(phrase in text for phrase in eval_phrases):
            score += 10
            signals_found.append("eval_phrase")

        return PluginScoreResult(
            plugin_name=self.name,
            score=min(score, 100),
            weight=config.get("weights", {}).get("intent_strength", self.default_weight),
            details={"signals": signals_found},
            version=self.version,
        )

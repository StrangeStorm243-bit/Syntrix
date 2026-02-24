"""Scoring engine — orchestrates plugins and rules to produce final scores."""

from __future__ import annotations

import logging
from typing import Any

from signalops.scoring.base import PluginScoreResult, ScoringPlugin

logger = logging.getLogger(__name__)

DEFAULT_PLUGINS = [
    "signalops.scoring.weighted:RelevancePlugin",
    "signalops.scoring.weighted:AuthorityPlugin",
    "signalops.scoring.weighted:EngagementPlugin",
    "signalops.scoring.weighted:RecencyPlugin",
    "signalops.scoring.weighted:IntentPlugin",
]


class ScoringEngine:
    """Orchestrates scoring plugins to produce final lead scores."""

    def __init__(self, plugins: list[ScoringPlugin] | None = None) -> None:
        self._plugins = plugins or self._load_default_plugins()

    def score(
        self,
        post: dict[str, Any],
        judgment: dict[str, Any],
        config: dict[str, Any],
    ) -> tuple[float, dict[str, Any]]:
        """Score a lead using all active plugins.

        Returns:
            (total_score, components_dict) where total is 0-100
        """
        results: list[PluginScoreResult] = []

        for plugin in self._plugins:
            try:
                result = plugin.score(post, judgment, config)
                results.append(result)
            except Exception as e:
                logger.warning("Plugin '%s' failed: %s", plugin.name, e)

        rules: list[dict[str, Any]] = config.get("custom_rules", [])
        rule_adjustments = self._apply_rules(post, judgment, rules)

        total = sum(r.score * r.weight for r in results)

        for adj in rule_adjustments:
            total += adj["adjustment"]

        total = min(max(total, 0.0), 100.0)

        components: dict[str, Any] = {}
        for r in results:
            components[r.plugin_name] = r.score
        if rule_adjustments:
            components["rule_adjustments"] = rule_adjustments

        return total, components

    def list_plugins(self) -> list[dict[str, str]]:
        """List all active plugins with name and version."""
        return [
            {"name": p.name, "version": p.version, "weight": str(p.default_weight)}
            for p in self._plugins
        ]

    def _apply_rules(
        self,
        post: dict[str, Any],
        judgment: dict[str, Any],
        rules: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Apply config-driven scoring rules (boost/penalty)."""
        adjustments: list[dict[str, Any]] = []

        for rule in rules:
            condition = str(rule.get("condition", ""))
            adjustment = float(rule.get("boost", 0))

            if self._evaluate_condition(condition, post, judgment):
                adjustments.append(
                    {
                        "rule_name": rule.get("name", "unnamed"),
                        "condition": condition,
                        "adjustment": adjustment,
                    }
                )

        return adjustments

    def _evaluate_condition(
        self,
        condition: str,
        post: dict[str, Any],
        judgment: dict[str, Any],
    ) -> bool:
        """Evaluate a simple condition string against post/judgment data."""
        condition = condition.strip()

        # Pattern: "text contains 'phrase'"
        if "text contains" in condition:
            phrase = condition.split("'")[1] if "'" in condition else ""
            text = str(post.get("text_cleaned", "")).lower()
            return phrase.lower() in text

        # Pattern: "author_verified == true"
        if "author_verified == true" in condition:
            return bool(post.get("author_verified", False))

        # Pattern: "author_followers > N"
        if "author_followers >" in condition:
            try:
                threshold = int(condition.split(">")[1].strip())
                return int(post.get("author_followers", 0)) > threshold
            except (ValueError, IndexError):
                return False

        # Pattern: "label == relevant"
        if "label ==" in condition:
            expected = condition.split("==")[1].strip().strip("'\"")
            return str(judgment.get("label", "")) == expected

        logger.warning("Unknown rule condition: %s", condition)
        return False

    def _load_default_plugins(self) -> list[ScoringPlugin]:
        """Load the default set of built-in plugins."""
        plugins: list[ScoringPlugin] = []
        for plugin_path in DEFAULT_PLUGINS:
            try:
                module_path, class_name = plugin_path.rsplit(":", 1)
                module = __import__(module_path, fromlist=[class_name])
                cls = getattr(module, class_name)
                plugins.append(cls())
            except Exception as e:
                logger.error("Failed to load plugin '%s': %s", plugin_path, e)
        return plugins

    @staticmethod
    def load_from_entry_points() -> list[ScoringPlugin]:
        """Load plugins from setuptools entry points."""
        try:
            from importlib.metadata import entry_points

            eps = entry_points(group="signalops.scorers")
            plugins: list[ScoringPlugin] = []
            for ep in eps:
                try:
                    plugin_cls = ep.load()
                    plugins.append(plugin_cls())
                except Exception as e:
                    logger.error("Failed to load entry point '%s': %s", ep.name, e)
            return plugins
        except Exception:
            return []

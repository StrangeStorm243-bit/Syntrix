"""Tests for the ScoringEngine orchestrator."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from signalops.scoring.base import PluginScoreResult, ScoringPlugin
from signalops.scoring.engine import ScoringEngine


def _post(**overrides: Any) -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "text_cleaned": "Looking for a code review tool?",
        "author_followers": 1000,
        "author_verified": False,
        "likes": 5,
        "replies": 2,
        "retweets": 1,
        "views": 1000,
        "created_at": datetime.now(UTC) - timedelta(hours=1),
    }
    defaults.update(overrides)
    return defaults


def _judgment(label: str = "relevant", confidence: float = 0.85) -> dict[str, Any]:
    return {"label": label, "confidence": confidence}


class FakePlugin(ScoringPlugin):
    """Test plugin with fixed score."""

    def __init__(self, plugin_name: str = "fake", score_value: float = 50.0) -> None:
        self._name = plugin_name
        self._score_value = score_value

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return "1.0"

    @property
    def default_weight(self) -> float:
        return 0.5

    def score(
        self,
        post: dict[str, Any],
        judgment: dict[str, Any],
        config: dict[str, Any],
    ) -> PluginScoreResult:
        return PluginScoreResult(
            plugin_name=self.name,
            score=self._score_value,
            weight=config.get("weights", {}).get(self.name, self.default_weight),
            details={},
        )


class ErrorPlugin(ScoringPlugin):
    """Plugin that always raises."""

    @property
    def name(self) -> str:
        return "error_plugin"

    @property
    def version(self) -> str:
        return "1.0"

    def score(
        self,
        post: dict[str, Any],
        judgment: dict[str, Any],
        config: dict[str, Any],
    ) -> PluginScoreResult:
        msg = "boom"
        raise RuntimeError(msg)


class TestScoringEngine:
    def test_weighted_total(self) -> None:
        engine = ScoringEngine(
            plugins=[
                FakePlugin("a", 80.0),
                FakePlugin("b", 40.0),
            ]
        )
        total, components = engine.score(_post(), _judgment(), {"weights": {"a": 0.6, "b": 0.4}})
        expected = 80 * 0.6 + 40 * 0.4
        assert abs(total - expected) < 0.1

    def test_default_plugins_load(self) -> None:
        engine = ScoringEngine()  # Should load 5 default plugins
        plugins = engine.list_plugins()
        assert len(plugins) == 5
        names = {p["name"] for p in plugins}
        assert names == {
            "relevance_judgment",
            "author_authority",
            "engagement_signals",
            "recency",
            "intent_strength",
        }

    def test_score_range_0_100(self) -> None:
        engine = ScoringEngine()
        total, _ = engine.score(_post(), _judgment(), {})
        assert 0 <= total <= 100

    def test_plugin_error_handled(self) -> None:
        engine = ScoringEngine(plugins=[FakePlugin("good", 50), ErrorPlugin()])
        total, components = engine.score(_post(), _judgment(), {})
        assert "good" in components
        assert "error_plugin" not in components

    def test_list_plugins(self) -> None:
        engine = ScoringEngine(plugins=[FakePlugin("test")])
        result = engine.list_plugins()
        assert result == [{"name": "test", "version": "1.0", "weight": "0.5"}]

    def test_entry_points_no_error(self) -> None:
        plugins = ScoringEngine.load_from_entry_points()
        assert isinstance(plugins, list)


class TestScoringRules:
    def test_text_contains_rule(self) -> None:
        engine = ScoringEngine(plugins=[FakePlugin("a", 50)])
        config: dict[str, Any] = {
            "custom_rules": [{"name": "boost", "condition": "text contains 'help'", "boost": 15}]
        }
        total, components = engine.score(
            _post(text_cleaned="I need help with reviews"),
            _judgment(),
            config,
        )
        assert components["rule_adjustments"][0]["adjustment"] == 15

    def test_text_contains_no_match(self) -> None:
        engine = ScoringEngine(plugins=[FakePlugin("a", 50)])
        config: dict[str, Any] = {
            "custom_rules": [{"name": "boost", "condition": "text contains 'xyz'", "boost": 15}]
        }
        _, components = engine.score(_post(), _judgment(), config)
        assert "rule_adjustments" not in components

    def test_verified_rule(self) -> None:
        engine = ScoringEngine(plugins=[FakePlugin("a", 50)])
        config: dict[str, Any] = {
            "custom_rules": [
                {"name": "verified", "condition": "author_verified == true", "boost": 5}
            ]
        }
        _, c1 = engine.score(_post(author_verified=False), _judgment(), config)
        _, c2 = engine.score(_post(author_verified=True), _judgment(), config)
        assert "rule_adjustments" not in c1
        assert c2["rule_adjustments"][0]["adjustment"] == 5

    def test_followers_rule(self) -> None:
        engine = ScoringEngine(plugins=[FakePlugin("a", 50)])
        config: dict[str, Any] = {
            "custom_rules": [
                {"name": "high_followers", "condition": "author_followers > 5000", "boost": 8}
            ]
        }
        _, c1 = engine.score(_post(author_followers=1000), _judgment(), config)
        _, c2 = engine.score(_post(author_followers=10000), _judgment(), config)
        assert "rule_adjustments" not in c1
        assert c2["rule_adjustments"][0]["adjustment"] == 8

    def test_label_rule(self) -> None:
        engine = ScoringEngine(plugins=[FakePlugin("a", 50)])
        config: dict[str, Any] = {
            "custom_rules": [
                {"name": "relevant_bonus", "condition": "label == relevant", "boost": 10}
            ]
        }
        _, c1 = engine.score(_post(), _judgment("relevant"), config)
        _, c2 = engine.score(_post(), _judgment("maybe"), config)
        assert c1["rule_adjustments"][0]["adjustment"] == 10
        assert "rule_adjustments" not in c2

    def test_score_clamped_at_100(self) -> None:
        engine = ScoringEngine(plugins=[FakePlugin("a", 100)])
        config: dict[str, Any] = {
            "weights": {"a": 1.0},
            "custom_rules": [
                {"name": "boost", "condition": "text contains 'looking'", "boost": 50}
            ],
        }
        total, _ = engine.score(
            _post(text_cleaned="looking for a tool"),
            _judgment(),
            config,
        )
        assert total == 100.0

    def test_score_clamped_at_0(self) -> None:
        engine = ScoringEngine(plugins=[FakePlugin("a", 10)])
        config: dict[str, Any] = {
            "weights": {"a": 0.1},
            "custom_rules": [
                {"name": "penalty", "condition": "text contains 'looking'", "boost": -50}
            ],
        }
        total, _ = engine.score(
            _post(text_cleaned="looking for a tool"),
            _judgment(),
            config,
        )
        assert total == 0.0

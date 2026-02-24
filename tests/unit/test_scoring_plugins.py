"""Tests for individual scoring plugins."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from signalops.scoring.account_age import AccountAgePlugin
from signalops.scoring.keyword_boost import KeywordBoostPlugin
from signalops.scoring.weighted import (
    AuthorityPlugin,
    EngagementPlugin,
    IntentPlugin,
    RecencyPlugin,
    RelevancePlugin,
)


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


def _config(**overrides: Any) -> dict[str, Any]:
    return dict(overrides)


# ── RelevancePlugin ──


class TestRelevancePlugin:
    def test_relevant_high_confidence(self) -> None:
        p = RelevancePlugin()
        result = p.score(_post(), _judgment("relevant", 0.95), _config())
        assert abs(result.score - 95) < 1

    def test_maybe_low_confidence(self) -> None:
        p = RelevancePlugin()
        result = p.score(_post(), _judgment("maybe", 0.5), _config())
        assert abs(result.score - 15) < 1

    def test_irrelevant(self) -> None:
        p = RelevancePlugin()
        result = p.score(_post(), _judgment("irrelevant", 0.9), _config())
        assert result.score == 0.0

    def test_weight_from_config(self) -> None:
        p = RelevancePlugin()
        result = p.score(_post(), _judgment(), _config(weights={"relevance_judgment": 0.5}))
        assert result.weight == 0.5

    def test_default_weight(self) -> None:
        p = RelevancePlugin()
        result = p.score(_post(), _judgment(), _config())
        assert result.weight == 0.35


# ── AuthorityPlugin ──


class TestAuthorityPlugin:
    def test_high_followers(self) -> None:
        p = AuthorityPlugin()
        result = p.score(_post(author_followers=1_000_000), _judgment(), _config())
        assert result.score > 60

    def test_zero_followers(self) -> None:
        p = AuthorityPlugin()
        result = p.score(_post(author_followers=0), _judgment(), _config())
        assert result.score == 10  # Baseline only

    def test_verified_bonus(self) -> None:
        p = AuthorityPlugin()
        r1 = p.score(_post(author_verified=False), _judgment(), _config())
        r2 = p.score(_post(author_verified=True), _judgment(), _config())
        assert r2.score - r1.score == 20


# ── EngagementPlugin ──


class TestEngagementPlugin:
    def test_high_engagement(self) -> None:
        p = EngagementPlugin()
        result = p.score(
            _post(likes=50, replies=20, retweets=10, views=20000),
            _judgment(),
            _config(),
        )
        assert result.score > 80

    def test_zero_engagement(self) -> None:
        p = EngagementPlugin()
        result = p.score(
            _post(likes=0, replies=0, retweets=0, views=0),
            _judgment(),
            _config(),
        )
        assert result.score == 0


# ── RecencyPlugin ──


class TestRecencyPlugin:
    def test_recent_post(self) -> None:
        p = RecencyPlugin()
        result = p.score(_post(created_at=datetime.now(UTC)), _judgment(), _config())
        assert result.score > 95

    def test_day_old(self) -> None:
        p = RecencyPlugin()
        result = p.score(
            _post(created_at=datetime.now(UTC) - timedelta(hours=24)),
            _judgment(),
            _config(),
        )
        assert 30 <= result.score <= 60

    def test_week_old(self) -> None:
        p = RecencyPlugin()
        result = p.score(
            _post(created_at=datetime.now(UTC) - timedelta(hours=168)),
            _judgment(),
            _config(),
        )
        assert result.score == 0.0

    def test_no_created_at(self) -> None:
        p = RecencyPlugin()
        result = p.score(_post(created_at=None), _judgment(), _config())
        assert result.score == 0.0

    def test_string_date(self) -> None:
        p = RecencyPlugin()
        dt = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
        result = p.score(_post(created_at=dt), _judgment(), _config())
        assert result.score > 90


# ── IntentPlugin ──


class TestIntentPlugin:
    def test_question_mark(self) -> None:
        p = IntentPlugin()
        result = p.score(_post(text_cleaned="Anyone recommend a tool?"), _judgment(), _config())
        assert result.score >= 40

    def test_search_phrase(self) -> None:
        p = IntentPlugin()
        result = p.score(
            _post(text_cleaned="looking for a good solution"),
            _judgment(),
            _config(),
        )
        assert result.score >= 30

    def test_pain_phrase(self) -> None:
        p = IntentPlugin()
        result = p.score(
            _post(text_cleaned="so frustrated with current tools"),
            _judgment(),
            _config(),
        )
        assert result.score >= 20

    def test_no_signals(self) -> None:
        p = IntentPlugin()
        result = p.score(_post(text_cleaned="Beautiful day today"), _judgment(), _config())
        assert result.score == 0

    def test_multiple_signals(self) -> None:
        p = IntentPlugin()
        result = p.score(
            _post(text_cleaned="Anyone recommend? Looking for a tool, so frustrated"),
            _judgment(),
            _config(),
        )
        assert result.score >= 90


# ── KeywordBoostPlugin ──


class TestKeywordBoostPlugin:
    def test_no_keywords_configured(self) -> None:
        p = KeywordBoostPlugin()
        result = p.score(_post(), _judgment(), _config())
        assert result.score == 0
        assert result.weight == 0

    def test_matching_keywords(self) -> None:
        p = KeywordBoostPlugin()
        result = p.score(
            _post(text_cleaned="I need a code review tool for PRs"),
            _judgment(),
            _config(keyword_boost={"keywords": ["code review", "PR automation"], "weight": 0.05}),
        )
        assert result.score == 20
        assert result.weight == 0.05

    def test_no_match(self) -> None:
        p = KeywordBoostPlugin()
        result = p.score(
            _post(text_cleaned="Beautiful day"),
            _judgment(),
            _config(keyword_boost={"keywords": ["code review"], "weight": 0.05}),
        )
        assert result.score == 0


# ── AccountAgePlugin ──


class TestAccountAgePlugin:
    def test_no_account_created(self) -> None:
        p = AccountAgePlugin()
        result = p.score(_post(), _judgment(), _config())
        assert result.score == 50
        assert result.weight == 0

    def test_old_account(self) -> None:
        p = AccountAgePlugin()
        result = p.score(
            _post(author_account_created=datetime.now(UTC) - timedelta(days=1500)),
            _judgment(),
            _config(),
        )
        assert result.score == 100

    def test_new_account(self) -> None:
        p = AccountAgePlugin()
        result = p.score(
            _post(author_account_created=datetime.now(UTC) - timedelta(days=5)),
            _judgment(),
            _config(),
        )
        assert result.score == 5

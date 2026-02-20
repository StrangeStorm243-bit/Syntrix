"""Tests for the scoring engine."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from signalops.config.schema import (
    ICPConfig,
    PersonaConfig,
    ProjectConfig,
    QueryConfig,
    RelevanceRubric,
    ScoringWeights,
)
from signalops.pipeline.scorer import ScorerStage
from signalops.storage.database import JudgmentLabel


# ── Helpers ──


def make_post(**overrides):
    """Create a mock NormalizedPost."""
    defaults = {
        "id": 1,
        "author_followers": 1000,
        "author_verified": False,
        "author_display_name": "Test User",
        "likes": 5,
        "replies": 2,
        "retweets": 1,
        "views": 1000,
        "text_cleaned": "Looking for a code review tool?",
        "created_at": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    defaults.update(overrides)
    post = MagicMock()
    for k, v in defaults.items():
        setattr(post, k, v)
    return post


def make_judgment(label="relevant", confidence=0.85):
    """Create a mock JudgmentRow."""
    j = MagicMock()
    j.label = JudgmentLabel(label)
    j.confidence = confidence
    return j


def make_config(**weight_overrides):
    weights = ScoringWeights(**weight_overrides) if weight_overrides else ScoringWeights()
    return ProjectConfig(
        project_id="test",
        project_name="Test",
        description="Test project",
        queries=[QueryConfig(text="q", label="q")],
        relevance=RelevanceRubric(
            system_prompt="judge",
            positive_signals=["need"],
            negative_signals=["spam"],
        ),
        scoring=weights,
        persona=PersonaConfig(
            name="Bot",
            role="helper",
            tone="helpful",
            voice_notes="Be concise.",
            example_reply="Hi!",
        ),
    )


# ── Tests ──


def test_perfect_score():
    """All signals max -> score between 90-100."""
    stage = ScorerStage(MagicMock())
    post = make_post(
        author_followers=1_000_000,
        author_verified=True,
        likes=50,
        replies=20,
        retweets=10,
        views=20000,
        text_cleaned="Anyone recommend a code review tool? So frustrated with current one.",
        created_at=datetime.now(timezone.utc),
    )
    judgment = make_judgment("relevant", 0.95)
    config = make_config()

    total, components = stage.compute_score(post, judgment, config)
    assert 85 <= total <= 100, f"Expected 85-100, got {total}"


def test_zero_score():
    """Irrelevant, 0 followers, 0 engagement, 7 days old, no intent -> near 0."""
    stage = ScorerStage(MagicMock())
    post = make_post(
        author_followers=0,
        author_verified=False,
        likes=0,
        replies=0,
        retweets=0,
        views=0,
        text_cleaned="Beautiful day today",
        created_at=datetime.now(timezone.utc) - timedelta(days=7),
    )
    judgment = make_judgment("irrelevant", 0.9)
    config = make_config()

    total, _ = stage.compute_score(post, judgment, config)
    assert total < 15, f"Expected < 15, got {total}"


def test_zero_followers_no_crash():
    stage = ScorerStage(MagicMock())
    post = make_post(author_followers=0)
    judgment = make_judgment()
    config = make_config()

    total, _ = stage.compute_score(post, judgment, config)
    assert total >= 0


def test_negative_followers_no_crash():
    stage = ScorerStage(MagicMock())
    post = make_post(author_followers=-1)
    judgment = make_judgment()
    config = make_config()

    total, _ = stage.compute_score(post, judgment, config)
    assert total >= 0


def test_weights_sum_to_one():
    w = ScoringWeights()
    total = (
        w.relevance_judgment
        + w.author_authority
        + w.engagement_signals
        + w.recency
        + w.intent_strength
    )
    assert abs(total - 1.0) < 0.01


def test_custom_weights():
    stage = ScorerStage(MagicMock())
    post = make_post()
    judgment = make_judgment("relevant", 0.9)

    config_default = make_config()
    config_custom = make_config(relevance_judgment=0.9, author_authority=0.025,
                                engagement_signals=0.025, recency=0.025, intent_strength=0.025)

    total_default, _ = stage.compute_score(post, judgment, config_default)
    total_custom, _ = stage.compute_score(post, judgment, config_custom)

    assert total_default != total_custom


def test_recency_decay_recent():
    """1 hour ago -> recency > 90."""
    stage = ScorerStage(MagicMock())
    score = stage._score_recency(datetime.now(timezone.utc) - timedelta(hours=1))
    assert score > 90


def test_recency_decay_day_old():
    """24 hours ago -> recency around 40-60."""
    stage = ScorerStage(MagicMock())
    score = stage._score_recency(datetime.now(timezone.utc) - timedelta(hours=24))
    assert 30 <= score <= 60


def test_recency_decay_old():
    """72 hours ago -> recency < 15."""
    stage = ScorerStage(MagicMock())
    score = stage._score_recency(datetime.now(timezone.utc) - timedelta(hours=72))
    assert score < 15


def test_recency_decay_week_old():
    """168 hours ago -> recency = 0."""
    stage = ScorerStage(MagicMock())
    score = stage._score_recency(datetime.now(timezone.utc) - timedelta(hours=168))
    assert score == 0.0


def test_intent_detection_question():
    stage = ScorerStage(MagicMock())
    score = stage._score_intent("Anyone recommend a good tool?")
    assert score > 0


def test_intent_detection_search():
    stage = ScorerStage(MagicMock())
    score = stage._score_intent("looking for a tool to help")
    assert score > 0


def test_intent_detection_pain():
    stage = ScorerStage(MagicMock())
    score = stage._score_intent("so frustrated with code reviews")
    assert score > 0


def test_intent_detection_none():
    stage = ScorerStage(MagicMock())
    score = stage._score_intent("Beautiful day today")
    assert score == 0


def test_engagement_high():
    stage = ScorerStage(MagicMock())
    post = make_post(likes=50, replies=20, retweets=10, views=10000)
    score = stage._score_engagement(post)
    assert score > 80


def test_engagement_zero():
    stage = ScorerStage(MagicMock())
    post = make_post(likes=0, replies=0, retweets=0, views=0)
    score = stage._score_engagement(post)
    assert score == 0


def test_relevance_relevant_high_conf():
    stage = ScorerStage(MagicMock())
    judgment = make_judgment("relevant", 0.95)
    score = stage._score_relevance(judgment)
    assert abs(score - 95) < 1


def test_relevance_maybe_low():
    stage = ScorerStage(MagicMock())
    judgment = make_judgment("maybe", 0.5)
    score = stage._score_relevance(judgment)
    assert abs(score - 15) < 1


def test_relevance_irrelevant():
    stage = ScorerStage(MagicMock())
    judgment = make_judgment("irrelevant", 0.9)
    score = stage._score_relevance(judgment)
    assert score == 0


def test_score_range():
    """Total is always 0-100."""
    stage = ScorerStage(MagicMock())
    config = make_config()

    for label in ["relevant", "maybe", "irrelevant"]:
        for followers in [0, 100, 1_000_000]:
            post = make_post(
                author_followers=followers,
                created_at=datetime.now(timezone.utc),
            )
            judgment = make_judgment(label, 0.8)
            total, _ = stage.compute_score(post, judgment, config)
            assert 0 <= total <= 100, f"Score {total} out of range"

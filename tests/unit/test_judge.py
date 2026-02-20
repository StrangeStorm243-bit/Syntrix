"""Tests for the judge system: LLMPromptJudge, KeywordFallbackJudge, and JudgeStage."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from signalops.config.schema import PersonaConfig, ProjectConfig, QueryConfig, RelevanceRubric
from signalops.models.judge_model import (
    Judgment,
    KeywordFallbackJudge,
    LLMPromptJudge,
)
from signalops.pipeline.judge import JudgeStage
from signalops.storage.database import (
    Judgment as JudgmentRow,
)
from signalops.storage.database import (
    JudgmentLabel,
    NormalizedPost,
)

# ── Fixtures ──


@pytest.fixture
def mock_gateway():
    gw = MagicMock()
    gw.complete_json.return_value = {
        "label": "relevant",
        "confidence": 0.85,
        "reasoning": "The post expresses a pain point about code review.",
    }
    return gw


@pytest.fixture
def project_context():
    return {
        "project_name": "Spectra",
        "description": "AI code review tool",
        "relevance": {
            "system_prompt": "Judge tweet relevance for a code review tool.",
            "positive_signals": ["expressing frustration with code review"],
            "negative_signals": ["hiring posts", "spam"],
        },
    }


@pytest.fixture
def sample_config():
    return ProjectConfig(
        project_id="test-project",
        project_name="Test Project",
        description="A test project",
        queries=[QueryConfig(text="test query", label="test")],
        relevance=RelevanceRubric(
            system_prompt="Judge relevance.",
            positive_signals=["need for tool"],
            negative_signals=["spam"],
            keywords_excluded=["hiring", "sponsored"],
            keywords_required=[],
        ),
        persona=PersonaConfig(
            name="Bot",
            role="helper",
            tone="helpful",
            voice_notes="Be concise.",
            example_reply="Here to help!",
        ),
    )


# ── LLMPromptJudge Tests ──


def test_parse_valid_judgment(mock_gateway, project_context):
    judge = LLMPromptJudge(mock_gateway)
    result = judge.judge("PR review took 3 hours", "Senior dev", project_context)
    assert isinstance(result, Judgment)
    assert result.label == "relevant"
    assert result.confidence == 0.85
    assert result.model_id == "claude-sonnet-4-6"


def test_parse_relevant_judgment(mock_gateway, project_context):
    mock_gateway.complete_json.return_value = {
        "label": "relevant",
        "confidence": 0.85,
        "reasoning": "Clear pain point.",
    }
    judge = LLMPromptJudge(mock_gateway)
    result = judge.judge("Code reviews are painful", "", project_context)
    assert result.label == "relevant"
    assert result.confidence == 0.85


def test_parse_irrelevant_judgment(mock_gateway, project_context):
    mock_gateway.complete_json.return_value = {
        "label": "irrelevant",
        "confidence": 0.92,
        "reasoning": "Hiring post.",
    }
    judge = LLMPromptJudge(mock_gateway)
    result = judge.judge("We're hiring!", "HR", project_context)
    assert result.label == "irrelevant"
    assert result.confidence == 0.92


def test_parse_maybe_judgment(mock_gateway, project_context):
    mock_gateway.complete_json.return_value = {
        "label": "maybe",
        "confidence": 0.55,
        "reasoning": "Unclear intent.",
    }
    judge = LLMPromptJudge(mock_gateway)
    result = judge.judge("Interesting day coding", "", project_context)
    assert result.label == "maybe"
    assert result.confidence == 0.55


def test_malformed_json_fallback(mock_gateway, project_context):
    mock_gateway.complete_json.side_effect = ValueError("Bad JSON")
    judge = LLMPromptJudge(mock_gateway)
    result = judge.judge("test", "", project_context)
    assert result.label == "maybe"
    assert result.confidence == 0.3
    assert result.model_id == "fallback-parse-error"


def test_gateway_exception_handling(mock_gateway, project_context):
    mock_gateway.complete_json.side_effect = RuntimeError("API down")
    judge = LLMPromptJudge(mock_gateway)
    result = judge.judge("test", "", project_context)
    assert result.label == "maybe"
    assert result.confidence == 0.3


def test_confidence_range(mock_gateway, project_context):
    mock_gateway.complete_json.return_value = {
        "label": "relevant",
        "confidence": 1.5,
        "reasoning": "Out of range.",
    }
    judge = LLMPromptJudge(mock_gateway)
    result = judge.judge("test", "", project_context)
    assert 0.0 <= result.confidence <= 1.0


def test_latency_tracked(mock_gateway, project_context):
    judge = LLMPromptJudge(mock_gateway)
    result = judge.judge("test", "", project_context)
    assert result.latency_ms > 0


def test_judge_batch(mock_gateway, project_context):
    judge = LLMPromptJudge(mock_gateway)
    items = [
        {"post_text": "text1", "author_bio": "bio1", "project_context": project_context},
        {"post_text": "text2", "author_bio": "bio2", "project_context": project_context},
        {"post_text": "text3", "author_bio": "bio3", "project_context": project_context},
    ]
    results = judge.judge_batch(items)
    assert len(results) == 3
    assert all(isinstance(r, Judgment) for r in results)


# ── KeywordFallbackJudge Tests ──


def test_keyword_exclusion_auto_reject():
    judge = KeywordFallbackJudge(keywords_excluded=["hiring"])
    result = judge.judge("We are hiring engineers!", "", {})
    assert result.label == "irrelevant"
    assert result.confidence == 0.9


def test_keyword_exclusion_case_insensitive():
    judge = KeywordFallbackJudge(keywords_excluded=["hiring"])
    result = judge.judge("HIRING managers needed", "", {})
    assert result.label == "irrelevant"


def test_keywords_required_miss():
    judge = KeywordFallbackJudge(keywords_required=["code review"])
    result = judge.judge("Beautiful day today", "", {})
    assert result.label == "irrelevant"
    assert result.confidence == 0.7


def test_keywords_required_hit():
    judge = KeywordFallbackJudge(keywords_required=["code review"])
    result = judge.judge("This code review tool is amazing", "", {})
    assert result.label == "maybe"
    assert result.confidence == 0.4


# ── JudgeStage Tests ──


def test_judge_stage_skips_already_judged(db_session, sample_config):
    """Posts with existing judgments should not be re-judged."""
    # Create a normalized post
    post = NormalizedPost(
        raw_post_id=1,
        project_id="test-project",
        platform="twitter",
        platform_id="t1",
        author_id="a1",
        author_username="user1",
        text_original="test text",
        text_cleaned="test text",
        created_at=datetime.now(UTC),
    )
    db_session.add(post)
    db_session.commit()

    # Create a judgment for it
    existing = JudgmentRow(
        normalized_post_id=post.id,
        project_id="test-project",
        label=JudgmentLabel.RELEVANT,
        confidence=0.9,
        reasoning="Already judged",
        model_id="test",
    )
    db_session.add(existing)
    db_session.commit()

    mock_judge = MagicMock()
    stage = JudgeStage(mock_judge, db_session)
    result = stage.run("test-project", sample_config)

    # The mock judge should NOT have been called (post already judged)
    mock_judge.judge.assert_not_called()
    assert result["total"] == 0

"""Tests for the draft generator and drafter stage."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from signalops.config.schema import (
    PersonaConfig,
    ProjectConfig,
    QueryConfig,
    RelevanceRubric,
)
from signalops.models.draft_model import Draft, LLMDraftGenerator
from signalops.pipeline.drafter import PLATFORM_CHAR_LIMITS, DrafterStage
from signalops.storage.database import (
    Draft as DraftRow,
)
from signalops.storage.database import (
    DraftStatus,
    JudgmentLabel,
    NormalizedPost,
)
from signalops.storage.database import (
    Judgment as JudgmentRow,
)
from signalops.storage.database import (
    Score as ScoreRow,
)

# ── Fixtures ──


@pytest.fixture
def mock_gateway():
    gw = MagicMock()
    gw.complete.return_value = (
        "That sounds painful \u2014 3 hours for one PR is brutal. "
        "Have you tried breaking reviews into smaller chunks?"
    )
    return gw


@pytest.fixture
def persona():
    return {
        "name": "Alex",
        "role": "developer advocate",
        "tone": "helpful",
        "voice_notes": "Be casual but knowledgeable. Reference specific details.",
        "example_reply": "That's rough — we've found smaller PRs help a lot.",
    }


@pytest.fixture
def project_context():
    return {
        "project_name": "Spectra",
        "description": "AI code review tool",
        "query_used": "code review pain",
        "score": 85,
        "reasoning": "Clear pain point about code review process.",
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
        ),
        persona=PersonaConfig(
            name="Alex",
            role="developer advocate",
            tone="helpful",
            voice_notes="Be casual.",
            example_reply="Happy to help!",
        ),
    )


# ── LLMDraftGenerator Tests ──


def test_generate_basic_draft(mock_gateway, persona, project_context):
    gen = LLMDraftGenerator(mock_gateway)
    draft = gen.generate(
        "PR reviews take forever",
        "@dev (500 followers)",
        project_context,
        persona,
    )
    assert isinstance(draft, Draft)
    assert len(draft.text) <= 240
    assert draft.tone == "helpful"
    assert draft.model_id == "claude-sonnet-4-6"


def test_character_limit_enforcement(mock_gateway, persona, project_context):
    """Text > 240 chars triggers re-generation."""
    long_text = "A" * 300
    mock_gateway.complete.side_effect = [long_text, "Short reply here."]
    gen = LLMDraftGenerator(mock_gateway)
    draft = gen.generate("test", "", project_context, persona)
    assert len(draft.text) <= 240
    # Gateway was called twice: once for the long response, once to shorten
    assert mock_gateway.complete.call_count == 2


def test_character_limit_hard_truncate(mock_gateway, persona, project_context):
    """If re-generation still too long, hard truncate."""
    long_text = "word " * 100  # 500 chars
    mock_gateway.complete.return_value = long_text.strip()
    gen = LLMDraftGenerator(mock_gateway)
    draft = gen.generate("test", "", project_context, persona)
    assert len(draft.text) <= 240


def test_persona_injection(mock_gateway, persona, project_context):
    gen = LLMDraftGenerator(mock_gateway)
    gen.generate("test", "", project_context, persona)
    system_prompt = mock_gateway.complete.call_args[0][0]
    assert "Alex" in system_prompt
    assert "developer advocate" in system_prompt
    assert "helpful" in system_prompt


def test_voice_notes_in_prompt(mock_gateway, persona, project_context):
    gen = LLMDraftGenerator(mock_gateway)
    gen.generate("test", "", project_context, persona)
    system_prompt = mock_gateway.complete.call_args[0][0]
    assert "casual but knowledgeable" in system_prompt


def test_example_reply_in_prompt(mock_gateway, persona, project_context):
    gen = LLMDraftGenerator(mock_gateway)
    gen.generate("test", "", project_context, persona)
    system_prompt = mock_gateway.complete.call_args[0][0]
    assert "smaller PRs" in system_prompt


def test_project_name_in_prompt(mock_gateway, persona, project_context):
    gen = LLMDraftGenerator(mock_gateway)
    gen.generate("test", "", project_context, persona)
    system_prompt = mock_gateway.complete.call_args[0][0]
    assert "Spectra" in system_prompt


def test_tone_field_set(mock_gateway, persona, project_context):
    gen = LLMDraftGenerator(mock_gateway)
    draft = gen.generate("test", "", project_context, persona)
    assert draft.tone == persona["tone"]


def test_model_id_set(mock_gateway, persona, project_context):
    gen = LLMDraftGenerator(mock_gateway, model="gpt-4o")
    draft = gen.generate("test", "", project_context, persona)
    assert draft.model_id == "gpt-4o"


# ── DrafterStage Tests ──


def test_draft_stage_min_score_filter(db_session, sample_config):
    """Only posts above min_score get drafted."""
    # Create a post with low score
    post = NormalizedPost(
        raw_post_id=1,
        project_id="test-project",
        platform="twitter",
        platform_id="t1",
        author_id="a1",
        text_original="test",
        text_cleaned="test",
        created_at=datetime.now(UTC),
    )
    db_session.add(post)
    db_session.commit()

    judgment = JudgmentRow(
        normalized_post_id=post.id,
        project_id="test-project",
        label=JudgmentLabel.RELEVANT,
        confidence=0.5,
        reasoning="Low relevance",
        model_id="test",
    )
    db_session.add(judgment)

    score = ScoreRow(
        normalized_post_id=post.id,
        project_id="test-project",
        total_score=30.0,
        components={},
        scoring_version="v1",
    )
    db_session.add(score)
    db_session.commit()

    mock_gen = MagicMock()
    stage = DrafterStage(mock_gen, db_session)
    result = stage.run("test-project", sample_config, min_score=50.0)

    mock_gen.generate.assert_not_called()
    assert result["drafted_count"] == 0


def test_draft_stage_top_n_limit(db_session, sample_config):
    """Only top N posts get drafted."""
    for i in range(5):
        post = NormalizedPost(
            raw_post_id=i + 1,
            project_id="test-project",
            platform="twitter",
            platform_id=f"t{i}",
            author_id=f"a{i}",
            text_original=f"test {i}",
            text_cleaned=f"test {i}",
            created_at=datetime.now(UTC),
        )
        db_session.add(post)
        db_session.commit()

        judgment = JudgmentRow(
            normalized_post_id=post.id,
            project_id="test-project",
            label=JudgmentLabel.RELEVANT,
            confidence=0.9,
            reasoning="Relevant",
            model_id="test",
        )
        db_session.add(judgment)

        score = ScoreRow(
            normalized_post_id=post.id,
            project_id="test-project",
            total_score=80.0 + i,
            components={},
            scoring_version="v1",
        )
        db_session.add(score)
    db_session.commit()

    mock_gen = MagicMock()
    mock_gen.generate.return_value = Draft(
        text="Short reply", tone="helpful", model_id="test", template_used=None
    )
    stage = DrafterStage(mock_gen, db_session)
    result = stage.run("test-project", sample_config, top_n=2, min_score=50.0)

    assert result["drafted_count"] == 2
    assert mock_gen.generate.call_count == 2


def test_draft_stage_skips_already_drafted(db_session, sample_config):
    """Posts with existing drafts are skipped."""
    post = NormalizedPost(
        raw_post_id=1,
        project_id="test-project",
        platform="twitter",
        platform_id="t1",
        author_id="a1",
        text_original="test",
        text_cleaned="test",
        created_at=datetime.now(UTC),
    )
    db_session.add(post)
    db_session.commit()

    judgment = JudgmentRow(
        normalized_post_id=post.id,
        project_id="test-project",
        label=JudgmentLabel.RELEVANT,
        confidence=0.9,
        reasoning="Relevant",
        model_id="test",
    )
    score = ScoreRow(
        normalized_post_id=post.id,
        project_id="test-project",
        total_score=85.0,
        components={},
        scoring_version="v1",
    )
    existing_draft = DraftRow(
        normalized_post_id=post.id,
        project_id="test-project",
        text_generated="Already drafted",
        model_id="test",
        status=DraftStatus.PENDING,
    )
    db_session.add_all([judgment, score, existing_draft])
    db_session.commit()

    mock_gen = MagicMock()
    stage = DrafterStage(mock_gen, db_session)
    result = stage.run("test-project", sample_config)

    mock_gen.generate.assert_not_called()
    assert result["drafted_count"] == 0


def test_draft_stage_dry_run(db_session, sample_config):
    """dry_run=True doesn't create DB rows."""
    post = NormalizedPost(
        raw_post_id=1,
        project_id="test-project",
        platform="twitter",
        platform_id="t1",
        author_id="a1",
        text_original="test",
        text_cleaned="test",
        created_at=datetime.now(UTC),
    )
    db_session.add(post)
    db_session.commit()

    judgment = JudgmentRow(
        normalized_post_id=post.id,
        project_id="test-project",
        label=JudgmentLabel.RELEVANT,
        confidence=0.9,
        reasoning="Relevant",
        model_id="test",
    )
    score = ScoreRow(
        normalized_post_id=post.id,
        project_id="test-project",
        total_score=85.0,
        components={},
        scoring_version="v1",
    )
    db_session.add_all([judgment, score])
    db_session.commit()

    mock_gen = MagicMock()
    mock_gen.generate.return_value = Draft(
        text="Draft text", tone="helpful", model_id="test", template_used=None
    )
    stage = DrafterStage(mock_gen, db_session)
    result = stage.run("test-project", sample_config, dry_run=True)

    assert result["drafted_count"] == 1
    # No draft rows should be in the DB
    draft_count = db_session.query(DraftRow).count()
    assert draft_count == 0


# ── Platform Char Limits Tests ──


def test_platform_specific_char_limits():
    """Drafter respects platform-specific character limits."""
    assert PLATFORM_CHAR_LIMITS["x"] == 280
    assert PLATFORM_CHAR_LIMITS["linkedin"] == 1300


def test_platform_char_limits_has_all_platforms():
    """All expected platforms have char limits defined."""
    assert "x" in PLATFORM_CHAR_LIMITS
    assert "linkedin" in PLATFORM_CHAR_LIMITS

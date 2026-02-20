"""Tests for training data exporter — enhanced exports with filtering and outcomes."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from signalops.storage.database import (
    Draft,
    DraftStatus,
    Judgment,
    JudgmentLabel,
    NormalizedPost,
    Outcome,
    OutcomeType,
    RawPost,
)

# ── Helpers ──


def _seed_judgment(
    db_session: Session,
    project_id: str,
    *,
    human_label: JudgmentLabel | None = None,
    confidence: float = 0.8,
    created_at: datetime | None = None,
    text: str = "test post",
) -> Judgment:
    """Create a raw -> normalized -> judgment chain."""
    raw = RawPost(
        project_id=project_id,
        platform="x",
        platform_id=f"post_{id(text)}_{confidence}",
        raw_json={"text": text},
    )
    db_session.add(raw)
    db_session.flush()

    norm = NormalizedPost(
        raw_post_id=raw.id,
        project_id=project_id,
        platform="x",
        platform_id=raw.platform_id,
        author_id="author1",
        author_username="testuser",
        author_followers=500,
        text_original=text,
        text_cleaned=text,
        likes=10,
        replies=2,
        created_at=created_at or datetime.now(UTC),
    )
    db_session.add(norm)
    db_session.flush()

    judgment = Judgment(
        normalized_post_id=norm.id,
        project_id=project_id,
        label=JudgmentLabel.RELEVANT,
        confidence=confidence,
        reasoning="Test reasoning",
        model_id="test-model",
        latency_ms=100.0,
        created_at=created_at or datetime.now(UTC),
    )
    if human_label is not None:
        judgment.human_label = human_label  # type: ignore[assignment]
        judgment.human_corrected_at = datetime.now(UTC)  # type: ignore[assignment]
        judgment.human_reason = "Human corrected"  # type: ignore[assignment]

    db_session.add(judgment)
    db_session.commit()
    return judgment


def _seed_draft_with_outcome(
    db_session: Session,
    project_id: str,
    *,
    text_generated: str = "original reply",
    text_final: str | None = "edited reply",
    outcome_type: OutcomeType = OutcomeType.LIKE_RECEIVED,
) -> Draft:
    """Create a sent draft with an outcome."""
    raw = RawPost(
        project_id=project_id,
        platform="x",
        platform_id=f"post_draft_{id(text_generated)}",
        raw_json={"text": "original"},
    )
    db_session.add(raw)
    db_session.flush()

    norm = NormalizedPost(
        raw_post_id=raw.id,
        project_id=project_id,
        platform="x",
        platform_id=raw.platform_id,
        author_id="author1",
        author_username="testuser",
        text_original="original post",
        text_cleaned="original post",
        created_at=datetime.now(UTC),
    )
    db_session.add(norm)
    db_session.flush()

    draft = Draft(
        normalized_post_id=norm.id,
        project_id=project_id,
        text_generated=text_generated,
        text_final=text_final,
        model_id="test-model",
        status=DraftStatus.SENT if text_final is None else DraftStatus.EDITED,
        sent_post_id="reply_123",
        sent_at=datetime.now(UTC),
    )
    db_session.add(draft)
    db_session.flush()

    outcome = Outcome(
        draft_id=draft.id,
        project_id=project_id,
        outcome_type=outcome_type,
        details={"delta": 1},
    )
    db_session.add(outcome)
    db_session.commit()
    return draft


# ── Tests ──


class TestExportJudgments:
    """Tests for judgment JSONL export."""

    def test_openai_format_has_messages_array(
        self, db_session: Session, sample_project_in_db: str
    ) -> None:
        """Judgment JSONL matches OpenAI fine-tuning spec (messages array)."""
        from signalops.training.exporter import TrainingDataExporter

        pid = sample_project_in_db
        _seed_judgment(db_session, pid, human_label=JudgmentLabel.RELEVANT)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            output = f.name

        try:
            exporter = TrainingDataExporter(db_session=db_session)
            result = exporter.export_judgments(project_id=pid, output=output)

            assert result["records"] == 1

            with open(output) as f:
                record = json.loads(f.readline())

            assert "messages" in record
            roles = [m["role"] for m in record["messages"]]
            assert roles == ["system", "user", "assistant"]
        finally:
            os.unlink(output)

    def test_since_filter_excludes_old(
        self, db_session: Session, sample_project_in_db: str
    ) -> None:
        """--since filtering excludes old records."""
        from signalops.training.exporter import TrainingDataExporter

        pid = sample_project_in_db
        old_date = datetime.now(UTC) - timedelta(days=30)
        recent_date = datetime.now(UTC) - timedelta(hours=1)

        _seed_judgment(
            db_session,
            pid,
            human_label=JudgmentLabel.RELEVANT,
            created_at=old_date,
            text="old post",
            confidence=0.9,
        )
        _seed_judgment(
            db_session,
            pid,
            human_label=JudgmentLabel.IRRELEVANT,
            created_at=recent_date,
            text="recent post",
            confidence=0.7,
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            output = f.name

        try:
            exporter = TrainingDataExporter(db_session=db_session)
            since_cutoff = datetime.now(UTC) - timedelta(days=7)
            result = exporter.export_judgments(project_id=pid, output=output, since=since_cutoff)
            assert result["records"] == 1
        finally:
            os.unlink(output)

    def test_min_confidence_filter(self, db_session: Session, sample_project_in_db: str) -> None:
        """--min-confidence filtering excludes low-confidence judgments."""
        from signalops.training.exporter import TrainingDataExporter

        pid = sample_project_in_db
        _seed_judgment(
            db_session,
            pid,
            human_label=JudgmentLabel.RELEVANT,
            confidence=0.3,
            text="low conf",
        )
        _seed_judgment(
            db_session,
            pid,
            human_label=JudgmentLabel.RELEVANT,
            confidence=0.9,
            text="high conf",
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            output = f.name

        try:
            exporter = TrainingDataExporter(db_session=db_session)
            result = exporter.export_judgments(project_id=pid, output=output, min_confidence=0.5)
            assert result["records"] == 1
        finally:
            os.unlink(output)

    def test_metadata_included(self, db_session: Session, sample_project_in_db: str) -> None:
        """Metadata included in export result when requested."""
        from signalops.training.exporter import TrainingDataExporter

        pid = sample_project_in_db
        _seed_judgment(db_session, pid, human_label=JudgmentLabel.RELEVANT)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            output = f.name

        try:
            exporter = TrainingDataExporter(db_session=db_session)
            result = exporter.export_judgments(project_id=pid, output=output, include_metadata=True)
            assert result["metadata"]["project_id"] == pid
            assert result["metadata"]["version"] == "0.2"
            assert "exported_at" in result["metadata"]
            assert result["metadata"]["record_count"] == 1
        finally:
            os.unlink(output)

    def test_empty_export(self, db_session: Session, sample_project_in_db: str) -> None:
        """No matching records -> empty file, zero count."""
        from signalops.training.exporter import TrainingDataExporter

        pid = sample_project_in_db

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            output = f.name

        try:
            exporter = TrainingDataExporter(db_session=db_session)
            result = exporter.export_judgments(project_id=pid, output=output)
            assert result["records"] == 0

            with open(output) as f:
                lines = f.readlines()
            assert len(lines) == 0
        finally:
            os.unlink(output)


class TestExportDraftPreferences:
    """Tests for DPO draft preferences export."""

    def test_dpo_format_has_prompt_chosen_rejected(
        self, db_session: Session, sample_project_in_db: str
    ) -> None:
        """DPO format has prompt/chosen/rejected fields."""
        from signalops.training.exporter import TrainingDataExporter

        pid = sample_project_in_db
        _seed_draft_with_outcome(db_session, pid)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            output = f.name

        try:
            exporter = TrainingDataExporter(db_session=db_session)
            result = exporter.export_draft_preferences(project_id=pid, output=output)
            assert result["records"] >= 1

            with open(output) as f:
                record = json.loads(f.readline())

            assert "prompt" in record
            assert "chosen" in record
            assert "rejected" in record
        finally:
            os.unlink(output)


class TestExportOutcomes:
    """Tests for outcome data export."""

    def test_outcome_export_format(self, db_session: Session, sample_project_in_db: str) -> None:
        """Outcome export has draft_text, score, outcomes, total_engagement."""
        from signalops.training.exporter import TrainingDataExporter

        pid = sample_project_in_db
        _seed_draft_with_outcome(
            db_session,
            pid,
            text_generated="great reply",
            text_final=None,
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            output = f.name

        try:
            exporter = TrainingDataExporter(db_session=db_session)
            result = exporter.export_outcomes(project_id=pid, output=output)
            assert result["records"] >= 1

            with open(output) as f:
                record = json.loads(f.readline())

            assert "draft_text" in record
            assert "outcomes" in record
            assert "total_engagement" in record
        finally:
            os.unlink(output)

    def test_outcome_export_empty(self, db_session: Session, sample_project_in_db: str) -> None:
        """No outcomes -> empty file, zero count."""
        from signalops.training.exporter import TrainingDataExporter

        pid = sample_project_in_db

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            output = f.name

        try:
            exporter = TrainingDataExporter(db_session=db_session)
            result = exporter.export_outcomes(project_id=pid, output=output)
            assert result["records"] == 0
        finally:
            os.unlink(output)

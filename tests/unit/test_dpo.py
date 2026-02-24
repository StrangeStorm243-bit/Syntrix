"""Tests for DPO preference pair collection."""

from __future__ import annotations

import json
from pathlib import Path

from signalops.storage.database import (
    Draft,
    DraftStatus,
    NormalizedPost,
    Project,
    RawPost,
    get_engine,
    get_session,
    init_db,
)
from signalops.training.dpo import DPOCollector, export_dpo_pairs


def _setup_db() -> tuple[object, object]:
    """Create in-memory DB with test data."""
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    session = get_session(engine)

    project = Project(id="test", name="Test", config_path="/tmp/test.yaml")
    session.add(project)

    raw_post = RawPost(
        project_id="test",
        platform="x",
        platform_id="123",
        raw_json={"id": "123", "text": "test"},
    )
    session.add(raw_post)
    session.flush()

    from datetime import datetime

    norm_post = NormalizedPost(
        raw_post_id=raw_post.id,
        project_id="test",
        platform="x",
        platform_id="123",
        author_id="author1",
        author_username="testuser",
        text_original="Looking for AI tools",
        text_cleaned="looking for ai tools",
        created_at=datetime(2024, 1, 1),
    )
    session.add(norm_post)
    session.flush()

    return session, norm_post


class TestDPOCollectorFromEdit:
    def test_collects_from_edited_draft(self) -> None:
        session, norm_post = _setup_db()
        draft = Draft(
            normalized_post_id=norm_post.id,
            project_id="test",
            text_generated="Original draft text",
            text_final="Human edited text",
            model_id="test-model",
            status=DraftStatus.EDITED,
        )
        session.add(draft)
        session.flush()

        collector = DPOCollector(session)
        pair = collector.collect_from_edit(int(draft.id))

        assert pair is not None
        assert pair.chosen_text == "Human edited text"
        assert pair.rejected_text == "Original draft text"
        assert pair.source == "edit"
        session.close()

    def test_skips_non_edited_draft(self) -> None:
        session, norm_post = _setup_db()
        draft = Draft(
            normalized_post_id=norm_post.id,
            project_id="test",
            text_generated="Draft text",
            model_id="test-model",
            status=DraftStatus.PENDING,
        )
        session.add(draft)
        session.flush()

        collector = DPOCollector(session)
        pair = collector.collect_from_edit(int(draft.id))
        assert pair is None
        session.close()

    def test_no_duplicate_pairs(self) -> None:
        session, norm_post = _setup_db()
        draft = Draft(
            normalized_post_id=norm_post.id,
            project_id="test",
            text_generated="Original",
            text_final="Edited",
            model_id="test-model",
            status=DraftStatus.EDITED,
        )
        session.add(draft)
        session.flush()

        collector = DPOCollector(session)
        pair1 = collector.collect_from_edit(int(draft.id))
        pair2 = collector.collect_from_edit(int(draft.id))
        assert pair1 is not None
        assert pair2 is None
        session.close()

    def test_skips_draft_without_final_text(self) -> None:
        session, norm_post = _setup_db()
        draft = Draft(
            normalized_post_id=norm_post.id,
            project_id="test",
            text_generated="Draft",
            text_final=None,
            model_id="test-model",
            status=DraftStatus.EDITED,
        )
        session.add(draft)
        session.flush()

        collector = DPOCollector(session)
        pair = collector.collect_from_edit(int(draft.id))
        assert pair is None
        session.close()


class TestDPOCollectorFromRejection:
    def test_collects_with_better_text(self) -> None:
        session, norm_post = _setup_db()
        draft = Draft(
            normalized_post_id=norm_post.id,
            project_id="test",
            text_generated="Bad draft",
            model_id="test-model",
            status=DraftStatus.REJECTED,
        )
        session.add(draft)
        session.flush()

        collector = DPOCollector(session)
        pair = collector.collect_from_rejection(int(draft.id), "Better text")

        assert pair is not None
        assert pair.chosen_text == "Better text"
        assert pair.rejected_text == "Bad draft"
        assert pair.source == "reject"
        session.close()

    def test_skips_without_better_text(self) -> None:
        session, norm_post = _setup_db()
        draft = Draft(
            normalized_post_id=norm_post.id,
            project_id="test",
            text_generated="Bad draft",
            model_id="test-model",
            status=DraftStatus.REJECTED,
        )
        session.add(draft)
        session.flush()

        collector = DPOCollector(session)
        pair = collector.collect_from_rejection(int(draft.id))
        assert pair is None
        session.close()


class TestDPOExport:
    def test_exports_jsonl(self, tmp_path: Path) -> None:
        session, norm_post = _setup_db()
        draft = Draft(
            normalized_post_id=norm_post.id,
            project_id="test",
            text_generated="Original",
            text_final="Edited",
            model_id="test-model",
            status=DraftStatus.EDITED,
        )
        session.add(draft)
        session.flush()

        collector = DPOCollector(session)
        collector.collect_from_edit(int(draft.id))

        output = tmp_path / "prefs.jsonl"
        result = export_dpo_pairs(session, "test", str(output))

        assert result["records"] == 1
        lines = output.read_text().strip().split("\n")
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert "prompt" in record
        assert record["chosen"] == "Edited"
        assert record["rejected"] == "Original"
        session.close()

    def test_empty_export(self, tmp_path: Path) -> None:
        session, _ = _setup_db()
        output = tmp_path / "empty.jsonl"
        result = export_dpo_pairs(session, "test", str(output))
        assert result["records"] == 0
        session.close()

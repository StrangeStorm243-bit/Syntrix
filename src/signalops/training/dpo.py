"""DPO preference pair collection from draft approvals/rejections."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from signalops.storage.database import (
    Draft,
    DraftStatus,
    NormalizedPost,
    PreferencePair,
    Project,
)


class DPOCollector:
    """Automatically generates DPO preference pairs from draft lifecycle events."""

    def __init__(self, db_session: Session) -> None:
        self._session = db_session

    def collect_from_edit(self, draft_id: int) -> PreferencePair | None:
        """When a draft is edited, the edit is 'chosen' and original is 'rejected'."""
        draft = self._session.query(Draft).filter(Draft.id == draft_id).first()
        if not draft or draft.status != DraftStatus.EDITED:
            return None
        if not draft.text_final or not draft.text_generated:
            return None

        # Don't create duplicate pairs
        existing = (
            self._session.query(PreferencePair).filter(PreferencePair.draft_id == draft_id).first()
        )
        if existing:
            return None

        prompt = self._build_prompt(draft)
        pair = PreferencePair(
            draft_id=draft_id,
            project_id=str(draft.project_id),
            prompt=prompt,
            chosen_text=str(draft.text_final),
            rejected_text=str(draft.text_generated),
            source="edit",
        )
        self._session.add(pair)
        self._session.commit()
        return pair

    def collect_from_rejection(
        self, draft_id: int, better_text: str | None = None
    ) -> PreferencePair | None:
        """When a draft is rejected. If better_text provided, use as 'chosen'."""
        draft = self._session.query(Draft).filter(Draft.id == draft_id).first()
        if not draft or draft.status != DraftStatus.REJECTED:
            return None

        if not better_text:
            return None  # Can't create a pair without a chosen alternative

        existing = (
            self._session.query(PreferencePair).filter(PreferencePair.draft_id == draft_id).first()
        )
        if existing:
            return None

        prompt = self._build_prompt(draft)
        pair = PreferencePair(
            draft_id=draft_id,
            project_id=str(draft.project_id),
            prompt=prompt,
            chosen_text=better_text,
            rejected_text=str(draft.text_generated),
            source="reject",
        )
        self._session.add(pair)
        self._session.commit()
        return pair

    def collect_all_pending(self, project_id: str) -> dict[str, int]:
        """Scan for edited/rejected drafts that don't have preference pairs yet."""
        stats: dict[str, int] = {"edits_collected": 0, "rejections_skipped": 0}

        edited_drafts = (
            self._session.query(Draft)
            .filter(
                Draft.project_id == project_id,
                Draft.status == DraftStatus.EDITED,
                Draft.text_final.isnot(None),
            )
            .all()
        )

        for draft in edited_drafts:
            pair = self.collect_from_edit(int(draft.id))
            if pair:
                stats["edits_collected"] += 1

        rejected_count = (
            self._session.query(Draft)
            .filter(
                Draft.project_id == project_id,
                Draft.status == DraftStatus.REJECTED,
            )
            .count()
        )
        stats["rejections_skipped"] = rejected_count

        return stats

    def _build_prompt(self, draft: Draft) -> str:
        """Reconstruct the prompt that generated this draft."""
        post = (
            self._session.query(NormalizedPost)
            .filter(NormalizedPost.id == draft.normalized_post_id)
            .first()
        )
        project = self._session.query(Project).filter(Project.id == draft.project_id).first()

        project_name = str(project.name) if project else "Unknown"
        post_text = str(post.text_original) if post else "Unknown"
        author = str(post.author_username) if post else "Unknown"

        return (
            f"Write a helpful reply to this tweet for {project_name}.\n\n"
            f'Tweet: "{post_text}"\n'
            f"Author: @{author}\n"
        )


def export_dpo_pairs(
    db_session: Session,
    project_id: str,
    output_path: str = "preferences.jsonl",
) -> dict[str, Any]:
    """Export preference pairs as JSONL for DPO fine-tuning."""
    pairs = db_session.query(PreferencePair).filter(PreferencePair.project_id == project_id).all()

    records: list[dict[str, Any]] = []
    for pair in pairs:
        record: dict[str, Any] = {
            "prompt": pair.prompt,
            "chosen": pair.chosen_text,
            "rejected": pair.rejected_text,
        }
        records.append(record)

    with open(output_path, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    return {"records": len(records), "output": output_path}

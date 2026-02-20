"""Training data exporter for fine-tuning LLM judges and draft generators."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session


class TrainingDataExporter:
    """Exports human-corrected data as JSONL for fine-tuning."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def export_judgments(
        self,
        project_id: str,
        format: str = "openai",
        output: str = "judgments.jsonl",
    ) -> dict[str, Any]:
        """Export human-corrected judgments as fine-tuning data."""
        from signalops.storage.database import Judgment, NormalizedPost, Project

        judgments = (
            self.db.query(Judgment)
            .filter(
                Judgment.project_id == project_id,
                Judgment.human_label.isnot(None),
            )
            .all()
        )

        records = []
        for j in judgments:
            post = self.db.query(NormalizedPost).filter_by(id=j.normalized_post_id).first()
            project = self.db.query(Project).get(project_id)

            record = {
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            f"You are a relevance judge for "
                            f"{project.name if project else project_id}."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Tweet: '{post.text_cleaned if post else ''}'\n"
                            f"Author: @{post.author_username if post else 'unknown'}"
                        ),
                    },
                    {
                        "role": "assistant",
                        "content": json.dumps(
                            {
                                "label": j.human_label.value,
                                "confidence": 0.95,
                                "reasoning": j.human_reason or j.reasoning or "",
                            }
                        ),
                    },
                ]
            }
            records.append(record)

        with open(output, "w") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        return {"records": len(records), "output": output}

    def export_draft_preferences(
        self,
        project_id: str,
        output: str = "preferences.jsonl",
    ) -> dict[str, Any]:
        """Export draft edits as DPO preference pairs."""
        from signalops.storage.database import Draft, DraftStatus, NormalizedPost

        drafts = (
            self.db.query(Draft)
            .filter(
                Draft.project_id == project_id,
                Draft.status == DraftStatus.EDITED,
                Draft.text_final.isnot(None),
            )
            .all()
        )

        records = []
        for d in drafts:
            post = self.db.query(NormalizedPost).filter_by(id=d.normalized_post_id).first()
            record = {
                "prompt": f"Write a reply to: '{post.text_cleaned if post else ''}'",
                "chosen": d.text_final,
                "rejected": d.text_generated,
            }
            records.append(record)

        with open(output, "w") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        return {"records": len(records), "output": output}

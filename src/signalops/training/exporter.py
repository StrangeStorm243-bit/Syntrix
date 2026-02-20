"""Training data exporter for fine-tuning LLM judges and draft generators."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session


class TrainingDataExporter:
    """Exports human-corrected data as JSONL for fine-tuning."""

    def __init__(self, db_session: Session) -> None:
        self.db = db_session

    def export_judgments(
        self,
        project_id: str,
        format: str = "openai",
        output: str = "judgments.jsonl",
        since: datetime | None = None,
        min_confidence: float | None = None,
        include_metadata: bool = False,
    ) -> dict[str, Any]:
        """Export human-corrected judgments as fine-tuning data.

        Args:
            project_id: Project to export for.
            format: Output format ('openai' or 'dpo').
            output: Output file path.
            since: Only export judgments created after this datetime.
            min_confidence: Only export judgments with confidence >= this.
            include_metadata: Include export metadata in result.
        """
        from signalops.storage.database import Judgment, NormalizedPost, Project

        query = self.db.query(Judgment).filter(
            Judgment.project_id == project_id,
            Judgment.human_label.isnot(None),
        )

        if since is not None:
            query = query.filter(Judgment.created_at >= since)
        if min_confidence is not None:
            query = query.filter(Judgment.confidence >= min_confidence)

        judgments = query.all()

        records = []
        for j in judgments:
            post = self.db.query(NormalizedPost).filter_by(id=j.normalized_post_id).first()
            project = self.db.get(Project, project_id)

            user_content = (
                f"Tweet: '{post.text_cleaned if post else ''}'\n"
                f"Author: @{post.author_username if post else 'unknown'}"
            )
            if post:
                user_content += (
                    f"\nMetrics: {post.likes} likes, "
                    f"{post.replies} replies, "
                    f"{post.author_followers} followers"
                )

            record: dict[str, Any] = {
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            f"You are a relevance judge for "
                            f"{project.name if project else project_id}."
                        ),
                    },
                    {"role": "user", "content": user_content},
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

        result: dict[str, Any] = {"records": len(records), "output": output}

        if include_metadata:
            result["metadata"] = {
                "project_id": project_id,
                "exported_at": datetime.now(UTC).isoformat(),
                "record_count": len(records),
                "version": "0.2",
            }

        return result

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
            record: dict[str, Any] = {
                "prompt": f"Write a reply to: '{post.text_cleaned if post else ''}'",
                "chosen": d.text_final,
                "rejected": d.text_generated,
            }
            records.append(record)

        with open(output, "w") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        return {"records": len(records), "output": output}

    def export_outcomes(
        self,
        project_id: str,
        output: str = "outcomes.jsonl",
    ) -> dict[str, Any]:
        """Export outcome data for reward modeling.

        Each record contains draft text, outcomes, and total engagement.
        """
        from signalops.storage.database import Draft, DraftStatus, Outcome

        drafts = (
            self.db.query(Draft)
            .filter(
                Draft.project_id == project_id,
                Draft.status.in_([DraftStatus.SENT, DraftStatus.EDITED]),
                Draft.sent_post_id.isnot(None),
            )
            .all()
        )

        records = []
        for d in drafts:
            outcomes = self.db.query(Outcome).filter(Outcome.draft_id == d.id).all()

            outcome_list = [
                {
                    "type": o.outcome_type.value,
                    "observed_at": (o.observed_at.isoformat() if o.observed_at else None),
                }
                for o in outcomes
            ]

            total_engagement = len([o for o in outcomes if o.outcome_type.value != "negative"])

            record: dict[str, Any] = {
                "draft_text": d.text_final or d.text_generated,
                "score": None,
                "outcomes": outcome_list,
                "total_engagement": total_engagement,
            }
            records.append(record)

        with open(output, "w") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        return {"records": len(records), "output": output}

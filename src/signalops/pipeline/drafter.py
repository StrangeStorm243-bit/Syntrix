"""Drafter pipeline stage — generates reply drafts for top-scored leads."""

from __future__ import annotations

from sqlalchemy.orm import Session

from signalops.config.schema import ProjectConfig
from signalops.models.draft_model import DraftGenerator
from signalops.storage.database import (
    Draft as DraftRow,
    DraftStatus,
    Judgment as JudgmentRow,
    NormalizedPost,
    Score as ScoreRow,
)


class DrafterStage:
    """Pipeline stage that generates reply drafts for top-scored leads."""

    def __init__(self, generator: DraftGenerator, db_session: Session):
        self._generator = generator
        self._session = db_session

    def run(
        self,
        project_id: str,
        config: ProjectConfig,
        top_n: int = 10,
        min_score: float = 50.0,
        dry_run: bool = False,
    ) -> dict:
        # Find top-scored posts without drafts
        already_drafted_ids = (
            self._session.query(DraftRow.normalized_post_id)
            .filter(DraftRow.project_id == project_id)
            .scalar_subquery()
        )
        rows = (
            self._session.query(NormalizedPost, ScoreRow, JudgmentRow)
            .join(ScoreRow, ScoreRow.normalized_post_id == NormalizedPost.id)
            .join(JudgmentRow, JudgmentRow.normalized_post_id == NormalizedPost.id)
            .filter(
                NormalizedPost.project_id == project_id,
                ScoreRow.total_score >= min_score,
                ~NormalizedPost.id.in_(already_drafted_ids),
            )
            .order_by(ScoreRow.total_score.desc())
            .limit(top_n)
            .all()
        )

        stats = {
            "drafted_count": 0,
            "avg_score_of_drafted": 0.0,
            "skipped_count": 0,
        }
        total_score_sum = 0.0

        persona = {
            "name": config.persona.name,
            "role": config.persona.role,
            "tone": config.persona.tone,
            "voice_notes": config.persona.voice_notes,
            "example_reply": config.persona.example_reply,
        }

        for post, score_row, judgment_row in rows:
            author_context = (
                f"@{post.author_username or 'unknown'} "
                f"({post.author_followers or 0} followers)"
            )
            project_context = {
                "project_name": config.project_name,
                "description": config.description,
                "query_used": "",
                "score": score_row.total_score,
                "reasoning": judgment_row.reasoning or "",
            }

            try:
                draft = self._generator.generate(
                    post.text_cleaned or post.text_original or "",
                    author_context,
                    project_context,
                    persona,
                )
            except Exception:
                stats["skipped_count"] += 1
                continue

            stats["drafted_count"] += 1
            total_score_sum += score_row.total_score

            if not dry_run:
                row = DraftRow(
                    normalized_post_id=post.id,
                    project_id=project_id,
                    text_generated=draft.text,
                    tone=draft.tone,
                    template_used=draft.template_used,
                    model_id=draft.model_id,
                    status=DraftStatus.PENDING,
                )
                self._session.add(row)

        if not dry_run and stats["drafted_count"] > 0:
            self._session.commit()

        if stats["drafted_count"] > 0:
            stats["avg_score_of_drafted"] = total_score_sum / stats["drafted_count"]

        return stats

"""Judge pipeline stage — scores posts for relevance."""

from __future__ import annotations

from sqlalchemy.orm import Session

from signalops.config.schema import ProjectConfig
from signalops.models.judge_model import RelevanceJudge
from signalops.storage.database import (
    Judgment as JudgmentRow,
)
from signalops.storage.database import (
    JudgmentLabel,
    NormalizedPost,
)


class JudgeStage:
    """Pipeline stage that judges relevance of normalized posts."""

    def __init__(self, judge: RelevanceJudge, db_session: Session):
        self._judge = judge
        self._session = db_session

    def run(
        self, project_id: str, config: ProjectConfig, dry_run: bool = False
    ) -> dict:
        # Find posts without judgments
        already_judged_ids = (
            self._session.query(JudgmentRow.normalized_post_id)
            .filter(JudgmentRow.project_id == project_id)
            .scalar_subquery()
        )
        posts = (
            self._session.query(NormalizedPost)
            .filter(
                NormalizedPost.project_id == project_id,
                ~NormalizedPost.id.in_(already_judged_ids),
            )
            .all()
        )

        project_context = self._build_project_context(config)
        keywords_excluded = config.relevance.keywords_excluded

        stats = {
            "total": len(posts),
            "relevant_count": 0,
            "irrelevant_count": 0,
            "maybe_count": 0,
            "avg_confidence": 0.0,
        }
        total_confidence = 0.0

        for post in posts:
            text_cleaned = post.text_cleaned or ""

            # Cheap keyword exclusion filter first
            excluded = False
            if keywords_excluded:
                text_lower = text_cleaned.lower()
                for kw in keywords_excluded:
                    if kw.lower() in text_lower:
                        judgment_result_label = "irrelevant"
                        judgment_result_confidence = 0.95
                        judgment_result_reasoning = f"Auto-excluded: keyword '{kw}'"
                        judgment_result_model_id = "keyword-exclude"
                        judgment_result_latency = 0.0
                        excluded = True
                        break

            if not excluded:
                result = self._judge.judge(
                    text_cleaned,
                    post.author_display_name or "",
                    project_context,
                )
                judgment_result_label = result.label
                judgment_result_confidence = result.confidence
                judgment_result_reasoning = result.reasoning
                judgment_result_model_id = result.model_id
                judgment_result_latency = result.latency_ms

            # Track stats
            if judgment_result_label == "relevant":
                stats["relevant_count"] += 1
            elif judgment_result_label == "irrelevant":
                stats["irrelevant_count"] += 1
            else:
                stats["maybe_count"] += 1
            total_confidence += judgment_result_confidence

            if not dry_run:
                label_enum = JudgmentLabel(judgment_result_label)
                row = JudgmentRow(
                    normalized_post_id=post.id,
                    project_id=project_id,
                    label=label_enum,
                    confidence=judgment_result_confidence,
                    reasoning=judgment_result_reasoning,
                    model_id=judgment_result_model_id,
                    latency_ms=judgment_result_latency,
                )
                self._session.add(row)

        if not dry_run:
            self._session.commit()

        if stats["total"] > 0:
            stats["avg_confidence"] = total_confidence / stats["total"]

        return stats

    def _build_project_context(self, config: ProjectConfig) -> dict:
        return {
            "project_name": config.project_name,
            "description": config.description,
            "relevance": {
                "system_prompt": config.relevance.system_prompt,
                "positive_signals": config.relevance.positive_signals,
                "negative_signals": config.relevance.negative_signals,
            },
        }

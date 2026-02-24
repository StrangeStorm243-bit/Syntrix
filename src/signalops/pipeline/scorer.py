"""Scoring pipeline stage — calculates weighted lead scores."""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from signalops.config.schema import ICPConfig, ProjectConfig
from signalops.storage.database import (
    Judgment as JudgmentRow,
)
from signalops.storage.database import (
    JudgmentLabel,
    NormalizedPost,
)
from signalops.storage.database import (
    Score as ScoreRow,
)


class ScorerStage:
    """Calculates lead scores using weighted criteria."""

    def __init__(self, db_session: Session):
        self._session = db_session

    def run(self, project_id: str, config: ProjectConfig, dry_run: bool = False) -> dict[str, Any]:
        # Find relevant/maybe posts without scores
        already_scored_ids = (
            self._session.query(ScoreRow.normalized_post_id)
            .filter(ScoreRow.project_id == project_id)
            .scalar_subquery()
        )
        rows = (
            self._session.query(NormalizedPost, JudgmentRow)
            .join(
                JudgmentRow,
                JudgmentRow.normalized_post_id == NormalizedPost.id,
            )
            .filter(
                NormalizedPost.project_id == project_id,
                JudgmentRow.label.in_([JudgmentLabel.RELEVANT, JudgmentLabel.MAYBE]),
                ~NormalizedPost.id.in_(already_scored_ids),
            )
            .all()
        )

        stats: dict[str, Any] = {
            "scored_count": 0,
            "avg_score": 0.0,
            "max_score": 0.0,
            "min_score": 100.0,
            "above_70_count": 0,
        }
        total_score_sum = 0.0

        engine = self._get_engine(config)
        plugin_info = [{"name": p["name"], "version": p["version"]} for p in engine.list_plugins()]

        for post, judgment in rows:
            total_score, components = self.compute_score(post, judgment, config)

            stats["scored_count"] += 1
            total_score_sum += total_score
            stats["max_score"] = max(stats["max_score"], total_score)
            stats["min_score"] = min(stats["min_score"], total_score)
            if total_score >= 70:
                stats["above_70_count"] += 1

            if not dry_run:
                row = ScoreRow(
                    normalized_post_id=post.id,
                    project_id=project_id,
                    total_score=total_score,
                    components=components,
                    scoring_version="v2",
                    scoring_plugins=plugin_info,
                )
                self._session.add(row)

        if not dry_run and stats["scored_count"] > 0:
            self._session.commit()

        if stats["scored_count"] > 0:
            stats["avg_score"] = total_score_sum / stats["scored_count"]
        else:
            stats["min_score"] = 0.0

        return stats

    def compute_score(
        self,
        post: NormalizedPost,
        judgment: JudgmentRow,
        config: ProjectConfig,
    ) -> tuple[float, dict[str, Any]]:
        """Score a lead using the plugin-based ScoringEngine."""
        engine = self._get_engine(config)
        post_dict = self._post_to_dict(post)
        judgment_dict = self._judgment_to_dict(judgment)
        config_dict: dict[str, Any] = (
            config.scoring.model_dump() if hasattr(config.scoring, "model_dump") else {}
        )
        # Map weight fields into a "weights" sub-dict for plugin lookup
        config_dict["weights"] = {
            "relevance_judgment": config.scoring.relevance_judgment,
            "author_authority": config.scoring.author_authority,
            "engagement_signals": config.scoring.engagement_signals,
            "recency": config.scoring.recency,
            "intent_strength": config.scoring.intent_strength,
        }
        return engine.score(post_dict, judgment_dict, config_dict)

    def _get_engine(self, config: ProjectConfig) -> Any:
        """Build a ScoringEngine for the given config."""
        from signalops.scoring.engine import ScoringEngine

        return ScoringEngine()

    def _post_to_dict(self, post: NormalizedPost) -> dict[str, Any]:
        """Convert ORM NormalizedPost to dict for plugin interface."""
        return {
            "text_cleaned": post.text_cleaned,
            "author_username": post.author_username,
            "author_display_name": post.author_display_name,
            "author_followers": post.author_followers,
            "author_verified": post.author_verified,
            "likes": post.likes,
            "replies": post.replies,
            "retweets": post.retweets,
            "views": post.views,
            "created_at": post.created_at,
        }

    def _judgment_to_dict(self, judgment: JudgmentRow) -> dict[str, Any]:
        """Convert ORM Judgment to dict for plugin interface."""
        return {
            "label": judgment.label.value if judgment.label else "maybe",
            "confidence": float(judgment.confidence or 0),
            "reasoning": judgment.reasoning or "",
        }

    # ── Legacy methods kept for backward compatibility with existing tests ──

    def _score_relevance(self, judgment: JudgmentRow) -> float:
        """confidence * label_multiplier."""
        multiplier: dict[JudgmentLabel, float] = {
            JudgmentLabel.RELEVANT: 1.0,
            JudgmentLabel.MAYBE: 0.3,
            JudgmentLabel.IRRELEVANT: 0.0,
        }
        label = JudgmentLabel(judgment.label)
        return float(judgment.confidence) * multiplier.get(label, 0.0) * 100

    def _score_authority(self, post: NormalizedPost, icp: ICPConfig) -> float:
        """Normalized score from followers, verified, bio match."""
        score = 0.0
        followers = int(post.author_followers or 0)
        if followers > 0:
            score += min(math.log10(followers) / 6 * 60, 60)
        if post.author_verified:
            score += 20
        # Baseline for having a profile
        score += 10
        return min(score, 100)

    def _score_engagement(self, post: NormalizedPost) -> float:
        """Normalized from likes, replies, retweets, views."""
        score = 0.0
        score += min(int(post.likes or 0) * 3, 30)
        score += min(int(post.replies or 0) * 5, 30)
        score += min(int(post.retweets or 0) * 4, 20)
        score += min(int(post.views or 0) / 500, 20)
        return min(score, 100)

    def _score_recency(self, created_at: datetime | None) -> float:
        """Decay: 100 at 0h, ~50 at 24h, ~10 at 72h, 0 at 168h."""
        if created_at is None:
            return 0.0
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)
        hours_ago = (datetime.now(UTC) - created_at).total_seconds() / 3600
        if hours_ago <= 0:
            return 100.0
        if hours_ago >= 168:
            return 0.0
        return max(0.0, 100 * math.exp(-0.03 * hours_ago))

    def _score_intent(self, text: str) -> float:
        """Detect intent signals in text."""
        score = 0.0
        text_lower = text.lower()

        if "?" in text:
            score += 40

        search_phrases = [
            "looking for",
            "anyone recommend",
            "anyone know",
            "suggestions for",
            "alternative to",
            "switching from",
        ]
        if any(phrase in text_lower for phrase in search_phrases):
            score += 30

        pain_phrases = [
            "frustrated",
            "annoying",
            "painful",
            "hate",
            "takes forever",
            "waste of time",
            "there has to be",
        ]
        if any(phrase in text_lower for phrase in pain_phrases):
            score += 20

        eval_phrases = ["evaluating", "comparing", "trying out", "testing"]
        if any(phrase in text_lower for phrase in eval_phrases):
            score += 10

        return min(score, 100)

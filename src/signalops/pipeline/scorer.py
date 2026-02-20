"""Scoring pipeline stage — calculates weighted lead scores."""

from __future__ import annotations

import math
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from signalops.config.schema import ICPConfig, ProjectConfig
from signalops.storage.database import (
    Judgment as JudgmentRow,
    JudgmentLabel,
    NormalizedPost,
    Score as ScoreRow,
)


class ScorerStage:
    """Calculates lead scores using weighted criteria."""

    def __init__(self, db_session: Session):
        self._session = db_session

    def run(
        self, project_id: str, config: ProjectConfig, dry_run: bool = False
    ) -> dict:
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

        stats = {
            "scored_count": 0,
            "avg_score": 0.0,
            "max_score": 0.0,
            "min_score": 100.0,
            "above_70_count": 0,
        }
        total_score_sum = 0.0

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
                    scoring_version="v1",
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
    ) -> tuple[float, dict]:
        """Returns (total_score, components_dict). Total is 0-100."""
        weights = config.scoring

        relevance_score = self._score_relevance(judgment)
        authority_score = self._score_authority(post, config.icp)
        engagement_score = self._score_engagement(post)
        recency_score = self._score_recency(post.created_at)
        intent_score = self._score_intent(post.text_cleaned or "")

        components = {
            "relevance_judgment": relevance_score,
            "author_authority": authority_score,
            "engagement_signals": engagement_score,
            "recency": recency_score,
            "intent_strength": intent_score,
        }

        total = (
            relevance_score * weights.relevance_judgment
            + authority_score * weights.author_authority
            + engagement_score * weights.engagement_signals
            + recency_score * weights.recency
            + intent_score * weights.intent_strength
        )

        return min(max(total, 0.0), 100.0), components

    def _score_relevance(self, judgment: JudgmentRow) -> float:
        """confidence * label_multiplier."""
        multiplier = {
            JudgmentLabel.RELEVANT: 1.0,
            JudgmentLabel.MAYBE: 0.3,
            JudgmentLabel.IRRELEVANT: 0.0,
        }
        return judgment.confidence * multiplier.get(judgment.label, 0) * 100

    def _score_authority(self, post: NormalizedPost, icp: ICPConfig) -> float:
        """Normalized score from followers, verified, bio match."""
        score = 0.0
        followers = post.author_followers or 0
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
        score += min((post.likes or 0) * 3, 30)
        score += min((post.replies or 0) * 5, 30)
        score += min((post.retweets or 0) * 4, 20)
        score += min((post.views or 0) / 500, 20)
        return min(score, 100)

    def _score_recency(self, created_at: datetime | None) -> float:
        """Decay: 100 at 0h, ~50 at 24h, ~10 at 72h, 0 at 168h."""
        if created_at is None:
            return 0.0
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        hours_ago = (datetime.now(timezone.utc) - created_at).total_seconds() / 3600
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

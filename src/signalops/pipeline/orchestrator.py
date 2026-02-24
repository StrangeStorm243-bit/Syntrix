"""Pipeline orchestrator — runs the full pipeline in sequence."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from signalops.config.schema import ProjectConfig
    from signalops.connectors.base import Connector
    from signalops.models.draft_model import DraftGenerator
    from signalops.models.judge_model import RelevanceJudge
    from signalops.notifications.base import Notifier

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Runs the full pipeline: collect -> normalize -> judge -> score -> draft."""

    def __init__(
        self,
        db_session: Session,
        connector: Connector,
        judge: RelevanceJudge,
        draft_generator: DraftGenerator,
        notifiers: list[Notifier] | None = None,
    ) -> None:
        self.session = db_session
        self.connector = connector
        self.judge = judge
        self.draft_generator = draft_generator
        self.notifiers = notifiers or []

    def run_all(self, config: ProjectConfig, dry_run: bool = False) -> dict[str, Any]:
        """Execute the full pipeline in sequence."""
        from rich.progress import Progress, SpinnerColumn, TextColumn

        results = {}
        stages = [
            ("Collecting tweets", self._run_collect),
            ("Normalizing posts", self._run_normalize),
            ("Judging relevance", self._run_judge),
            ("Scoring leads", self._run_score),
            ("Sending notifications", self._run_notify),
            ("Generating drafts", self._run_draft),
        ]

        with Progress(SpinnerColumn(), TextColumn("{task.description}")) as progress:
            for description, stage_fn in stages:
                task = progress.add_task(description)
                try:
                    result = stage_fn(config, dry_run)
                    results[description] = result
                except Exception as e:
                    logger.error("Stage '%s' failed: %s", description, e)
                    results[description] = {"error": str(e)}
                progress.update(task, completed=True)

        return results

    def _run_collect(self, config: ProjectConfig, dry_run: bool) -> dict[str, Any]:
        if config.batch.enabled:
            return self._run_batch_collect(config, dry_run)

        from signalops.pipeline.collector import CollectorStage

        collector = CollectorStage(connector=self.connector, db_session=self.session)
        return collector.run(config=config, dry_run=dry_run)

    def _run_batch_collect(self, config: ProjectConfig, dry_run: bool) -> dict[str, Any]:
        import os

        from signalops.connectors.rate_limiter import RateLimiter
        from signalops.pipeline.batch import run_batch_sync

        bearer_token = os.environ.get("X_BEARER_TOKEN", "")
        rate_limiter = RateLimiter(max_requests=55, window_seconds=900)

        result = run_batch_sync(
            bearer_token=bearer_token,
            db_session=self.session,
            rate_limiter=rate_limiter,
            config=config,
            concurrency=config.batch.concurrency,
            dry_run=dry_run,
        )
        return {
            "total_queries": result.total_queries,
            "successful_queries": result.successful_queries,
            "failed_queries": result.failed_queries,
            "total_tweets_found": result.total_tweets_found,
            "total_new_tweets": result.total_new_tweets,
        }

    def _run_normalize(self, config: ProjectConfig, dry_run: bool) -> dict[str, Any]:
        from signalops.pipeline.normalizer import NormalizerStage

        normalizer = NormalizerStage()
        return normalizer.run(
            db_session=self.session,
            project_id=config.project_id,
            dry_run=dry_run,
        )

    def _run_judge(self, config: ProjectConfig, dry_run: bool) -> dict[str, Any]:
        from signalops.pipeline.judge import JudgeStage

        judge_stage = JudgeStage(judge=self.judge, db_session=self.session)
        return judge_stage.run(
            project_id=config.project_id,
            config=config,
            dry_run=dry_run,
        )

    def _run_score(self, config: ProjectConfig, dry_run: bool) -> dict[str, Any]:
        from signalops.pipeline.scorer import ScorerStage

        scorer = ScorerStage(db_session=self.session)
        return scorer.run(
            project_id=config.project_id,
            config=config,
            dry_run=dry_run,
        )

    def _run_notify(self, config: ProjectConfig, dry_run: bool) -> dict[str, Any]:
        """Send notifications for high-score leads. Never fails the pipeline."""
        if not self.notifiers or not config.notifications.enabled:
            return {"skipped": True, "reason": "notifications disabled"}
        try:
            from signalops.notifications.base import notify_high_scores
            from signalops.storage.database import Score

            threshold = config.notifications.min_score_to_notify
            rows = (
                self.session.query(Score)
                .filter(
                    Score.project_id == config.project_id,
                    Score.total_score >= threshold,
                )
                .all()
            )
            scores = [
                {
                    "author": "unknown",
                    "score": row.total_score,
                    "text_preview": "",
                }
                for row in rows
            ]
            return notify_high_scores(scores, config, self.notifiers)
        except Exception as e:
            logger.warning("Notification failed (non-fatal): %s", e)
            return {"error": str(e)}

    def _run_draft(self, config: ProjectConfig, dry_run: bool) -> dict[str, Any]:
        from signalops.pipeline.drafter import DrafterStage

        drafter = DrafterStage(generator=self.draft_generator, db_session=self.session)
        return drafter.run(
            project_id=config.project_id,
            config=config,
            dry_run=dry_run,
        )

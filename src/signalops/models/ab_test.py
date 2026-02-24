"""A/B test judge — wraps two judges with configurable traffic routing."""

from __future__ import annotations

import random
import time
from typing import TYPE_CHECKING, Any

from signalops.models.judge_model import Judgment, RelevanceJudge

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from signalops.config.schema import ProjectConfig
    from signalops.models.llm_gateway import LLMGateway


class ABTestJudge(RelevanceJudge):
    """Routes judgments between primary and canary models for A/B testing."""

    def __init__(
        self,
        primary: RelevanceJudge,
        canary: RelevanceJudge,
        canary_pct: float = 0.1,
        experiment_id: str = "",
        db_session: Session | None = None,
    ) -> None:
        self._primary = primary
        self._canary = canary
        self._canary_pct = canary_pct
        self._experiment_id = experiment_id
        self._session = db_session

    def judge(self, post_text: str, author_bio: str, project_context: dict[str, Any]) -> Judgment:
        use_canary = random.random() < self._canary_pct  # noqa: S311
        judge = self._canary if use_canary else self._primary

        start = time.perf_counter()
        result = judge.judge(post_text, author_bio, project_context)
        latency_ms = (time.perf_counter() - start) * 1000

        # Tag the result with experiment metadata
        if use_canary:
            result.model_id = f"canary:{result.model_id}"

        # Record A/B result if we have a DB session
        if self._session and self._experiment_id:
            self._record_result(result, latency_ms)

        return result

    def judge_batch(self, items: list[dict[str, Any]]) -> list[Judgment]:
        return [
            self.judge(
                item["post_text"],
                item.get("author_bio", ""),
                item.get("project_context", {}),
            )
            for item in items
        ]

    def _record_result(self, judgment: Judgment, latency_ms: float) -> Any:
        """Store A/B test result for later analysis.

        judgment_id is left NULL here because the Judgment row hasn't been
        persisted yet. The caller (JudgeStage) must call
        ``ab_result.judgment_id = judgment_row.id`` after flushing the
        judgment, then commit both together.
        """
        from signalops.storage.database import ABResult

        result = ABResult(
            experiment_id=self._experiment_id,
            judgment_id=None,
            model_used=judgment.model_id,
            latency_ms=latency_ms,
        )
        if self._session:
            self._session.add(result)
        return result


def create_ab_test_judge(
    config: ProjectConfig,
    gateway: LLMGateway,
    db_session: Session | None = None,
) -> ABTestJudge:
    """Create an ABTestJudge from config. Finds the active experiment."""
    from signalops.models.judge_model import LLMPromptJudge

    if db_session:
        from signalops.storage.database import ABExperiment

        experiment = (
            db_session.query(ABExperiment)
            .filter(
                ABExperiment.project_id == config.project_id,
                ABExperiment.status == "active",
            )
            .first()
        )
        if experiment:
            primary = _create_single_judge(str(experiment.primary_model), gateway)
            canary = _create_single_judge(str(experiment.canary_model), gateway)
            return ABTestJudge(
                primary=primary,
                canary=canary,
                canary_pct=float(experiment.canary_pct),
                experiment_id=str(experiment.experiment_id),
                db_session=db_session,
            )

    # No active experiment — return primary only wrapped in AB test
    primary = LLMPromptJudge(gateway=gateway, model=config.llm.judge_model)
    return ABTestJudge(primary=primary, canary=primary, canary_pct=0.0)


def _create_single_judge(model_id: str, gateway: LLMGateway) -> RelevanceJudge:
    """Create a judge for a specific model ID."""
    from signalops.models.finetuned import FineTunedJudge
    from signalops.models.judge_model import LLMPromptJudge

    if model_id.startswith("ft:"):
        return FineTunedJudge(gateway=gateway, model_id=model_id)
    return LLMPromptJudge(gateway=gateway, model=model_id)

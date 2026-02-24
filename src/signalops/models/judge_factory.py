"""Factory for creating the appropriate RelevanceJudge based on config."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from signalops.config.schema import ProjectConfig
    from signalops.models.judge_model import RelevanceJudge
    from signalops.models.llm_gateway import LLMGateway


def create_judge(
    config: ProjectConfig,
    gateway: LLMGateway,
    db_session: Session | None = None,
) -> RelevanceJudge:
    """Route to the correct judge implementation based on config.

    Routing logic:
    - If model starts with ``ft:``, use FineTunedJudge
    - If experiments enabled, use ABTestJudge (wraps two judges)
    - Otherwise, use default LLMPromptJudge
    """
    model_id = config.llm.judge_model

    if model_id.startswith("ft:"):
        from signalops.models.finetuned import FineTunedJudge

        return FineTunedJudge(gateway=gateway, model_id=model_id)

    if config.experiments.enabled:
        from signalops.models.ab_test import create_ab_test_judge

        return create_ab_test_judge(config, gateway, db_session)

    from signalops.models.judge_model import LLMPromptJudge

    return LLMPromptJudge(gateway=gateway, model=model_id)

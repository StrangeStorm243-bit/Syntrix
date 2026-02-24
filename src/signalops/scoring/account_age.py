"""Account age scoring plugin — newer accounts may be less trustworthy."""

from __future__ import annotations

from typing import Any

from signalops.scoring.base import PluginScoreResult, ScoringPlugin


class AccountAgePlugin(ScoringPlugin):
    """Scores based on author account age. Older = more trustworthy."""

    @property
    def name(self) -> str:
        return "account_age"

    @property
    def version(self) -> str:
        return "1.0"

    @property
    def default_weight(self) -> float:
        return 0.0  # Only active when configured

    def score(
        self,
        post: dict[str, Any],
        judgment: dict[str, Any],
        config: dict[str, Any],
    ) -> PluginScoreResult:
        account_created = post.get("author_account_created")
        if not account_created:
            return PluginScoreResult(
                plugin_name=self.name,
                score=50.0,
                weight=0.0,
                details={"available": False},
            )

        from datetime import UTC, datetime

        if isinstance(account_created, str):
            created = datetime.fromisoformat(account_created)
        else:
            created = account_created

        if created.tzinfo is None:
            created = created.replace(tzinfo=UTC)

        days_old = (datetime.now(UTC) - created).days
        if days_old >= 1000:
            score = 100.0
        elif days_old >= 365:
            score = 80.0 + (days_old - 365) / 635 * 20
        elif days_old >= 30:
            score = 30.0 + (days_old - 30) / 335 * 50
        else:
            score = float(days_old)

        return PluginScoreResult(
            plugin_name=self.name,
            score=score,
            weight=config.get("account_age", {}).get("weight", self.default_weight),
            details={"days_old": days_old},
            version=self.version,
        )

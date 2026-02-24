"""Integration test: full A/B test pipeline — both models called, results stored, analysis works."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest

from signalops.config.schema import ExperimentConfig, ProjectConfig
from signalops.models.ab_analysis import analyze_experiment
from signalops.models.ab_test import ABTestJudge, create_ab_test_judge
from signalops.models.judge_model import Judgment, RelevanceJudge
from signalops.storage.database import (
    ABExperiment,
    ABResult,
    JudgmentLabel,
    NormalizedPost,
)
from signalops.storage.database import (
    Judgment as JudgmentRow,
)
from signalops.storage.database import (
    RawPost as RawPostDB,
)
from signalops.training.dpo import DPOCollector, export_dpo_pairs


class StubJudge(RelevanceJudge):
    """Deterministic judge for testing."""

    def __init__(self, label: str, confidence: float, model_id: str) -> None:
        self._label = label
        self._confidence = confidence
        self._model_id = model_id

    def judge(self, post_text: str, author_bio: str, project_context: dict[str, Any]) -> Judgment:
        return Judgment(
            label=self._label,
            confidence=self._confidence,
            reasoning=f"Stub: {self._label}",
            model_id=self._model_id,
            latency_ms=10.0,
        )

    def judge_batch(self, items: list[dict[str, Any]]) -> list[Judgment]:
        return [
            self.judge(i["post_text"], i.get("author_bio", ""), i.get("project_context", {}))
            for i in items
        ]


@pytest.fixture
def project_with_experiment(db_session: Any, sample_project_in_db: str) -> str:
    """Insert an active A/B experiment and return its experiment_id."""
    experiment = ABExperiment(
        experiment_id="exp-integ-001",
        project_id="test-project",
        primary_model="claude-sonnet-4-6",
        canary_model="ft:gpt-4o-mini:spectra-v1",
        canary_pct=0.5,
        status="active",
        hypothesis="Fine-tuned model has higher precision",
    )
    db_session.add(experiment)
    db_session.commit()
    return "exp-integ-001"


class TestABPipelineIntegration:
    """Full pipeline integration test with A/B test active."""

    def test_ab_judge_stores_results_in_db(
        self, db_session: Any, project_with_experiment: str
    ) -> None:
        """Both primary and canary models get called; results are stored in ab_results."""
        primary = StubJudge("relevant", 0.9, "claude-sonnet-4-6")
        canary = StubJudge("irrelevant", 0.7, "ft:gpt-4o-mini:spectra-v1")

        ab_judge = ABTestJudge(
            primary=primary,
            canary=canary,
            canary_pct=0.5,
            experiment_id="exp-integ-001",
            db_session=db_session,
        )

        # Run enough judgments to get both models called
        results = []
        for _ in range(40):
            r = ab_judge.judge("test tweet", "test bio", {})
            results.append(r)
        db_session.commit()

        # Verify results stored
        stored = db_session.query(ABResult).filter_by(experiment_id="exp-integ-001").all()
        assert len(stored) == 40

        canary_results = [r for r in stored if str(r.model_used).startswith("canary:")]
        primary_results = [r for r in stored if not str(r.model_used).startswith("canary:")]
        assert len(canary_results) > 5  # At least some canary calls
        assert len(primary_results) > 5  # At least some primary calls

    def test_ab_results_with_judgments_enables_analysis(
        self, db_session: Any, project_with_experiment: str
    ) -> None:
        """Store A/B results + judgment rows, then run analyze_experiment()."""
        # Need a NormalizedPost to satisfy NOT NULL on judgments.normalized_post_id
        raw = RawPostDB(
            project_id="test-project",
            platform="x",
            platform_id="ab-analysis-raw",
            raw_json={"text": "test"},
        )
        db_session.add(raw)
        db_session.flush()

        post = NormalizedPost(
            raw_post_id=raw.id,
            project_id="test-project",
            platform="x",
            platform_id="ab-analysis-post",
            author_id="a1",
            author_username="testuser",
            author_display_name="Test",
            author_followers=100,
            author_verified=False,
            text_original="test tweet",
            text_cleaned="test tweet",
            created_at=datetime.now(UTC),
        )
        db_session.add(post)
        db_session.flush()

        # Create judgment rows and link them to AB results
        for i in range(20):
            is_canary = i % 2 == 0
            model_id = "canary:ft:gpt-4o-mini:spectra-v1" if is_canary else "claude-sonnet-4-6"
            label = JudgmentLabel.RELEVANT if i % 3 != 0 else JudgmentLabel.IRRELEVANT

            judgment = JudgmentRow(
                normalized_post_id=post.id,
                project_id="test-project",
                label=label,
                confidence=0.85,
                reasoning="test",
                model_id=model_id,
                latency_ms=50.0,
                experiment_id="exp-integ-001",
            )
            db_session.add(judgment)
            db_session.flush()

            ab_result = ABResult(
                experiment_id="exp-integ-001",
                judgment_id=judgment.id,
                model_used=model_id,
                latency_ms=50.0,
            )
            db_session.add(ab_result)

        db_session.commit()

        # Run analysis
        analysis = analyze_experiment(db_session, "exp-integ-001")
        assert analysis.experiment_id == "exp-integ-001"
        assert analysis.primary_count == 10
        assert analysis.canary_count == 10
        assert analysis.primary_metrics["relevant_pct"] > 0
        assert analysis.canary_metrics["relevant_pct"] > 0
        assert isinstance(analysis.recommendation, str)
        assert len(analysis.recommendation) > 0

    def test_create_ab_test_judge_from_config(
        self,
        db_session: Any,
        project_with_experiment: str,
        sample_project_config: ProjectConfig,
    ) -> None:
        """create_ab_test_judge() finds the active experiment and returns an ABTestJudge."""
        sample_project_config.project_id = "test-project"
        sample_project_config.experiments = ExperimentConfig(enabled=True)

        gateway = MagicMock()
        gateway.complete_json.return_value = {
            "label": "relevant",
            "confidence": 0.9,
            "reasoning": "test",
        }

        judge = create_ab_test_judge(sample_project_config, gateway, db_session)
        assert isinstance(judge, ABTestJudge)
        assert judge._experiment_id == "exp-integ-001"
        assert judge._canary_pct == 0.5


class TestDPOIntegration:
    """Integration test: DPO collection + export round-trip."""

    def test_edit_creates_pair_and_exports_to_jsonl(
        self, db_session: Any, sample_project_in_db: str, tmp_path: Any
    ) -> None:
        """Full flow: create draft, mark edited, collect DPO pair, export to JSONL."""
        from signalops.storage.database import Draft, DraftStatus

        # Create a raw post and normalized post
        raw = RawPostDB(
            project_id="test-project",
            platform="x",
            platform_id="dpo-test-123",
            raw_json={"text": "Need help with testing"},
        )
        db_session.add(raw)
        db_session.flush()

        post = NormalizedPost(
            raw_post_id=raw.id,
            project_id="test-project",
            platform="x",
            platform_id="dpo-test-123",
            author_id="author1",
            author_username="testuser",
            author_display_name="Test User",
            author_followers=500,
            author_verified=False,
            text_original="Need help with testing",
            text_cleaned="Need help with testing",
            created_at=datetime.now(UTC),
        )
        db_session.add(post)
        db_session.flush()

        # Create a draft that was edited
        draft = Draft(
            normalized_post_id=post.id,
            project_id="test-project",
            text_generated="Here is the original generated reply.",
            text_final="Here is the human-edited better reply.",
            model_id="claude-sonnet-4-6",
            status=DraftStatus.EDITED,
            approved_at=datetime.now(UTC),
        )
        db_session.add(draft)
        db_session.commit()

        # Collect DPO pair
        collector = DPOCollector(db_session)
        pair = collector.collect_from_edit(int(draft.id))
        assert pair is not None
        assert pair.chosen_text == "Here is the human-edited better reply."
        assert pair.rejected_text == "Here is the original generated reply."
        assert pair.source == "edit"

        # Export to JSONL
        output_file = str(tmp_path / "preferences.jsonl")
        result = export_dpo_pairs(db_session, "test-project", output_file)
        assert result["records"] == 1

        # Verify JSONL content
        import json

        with open(output_file) as f:
            record = json.loads(f.readline())
        assert record["chosen"] == "Here is the human-edited better reply."
        assert record["rejected"] == "Here is the original generated reply."
        assert "prompt" in record

"""Tests for A/B test statistical analysis."""

from __future__ import annotations

from signalops.models.ab_analysis import _compute_metrics, _generate_recommendation


class TestComputeMetrics:
    def test_empty_judgments(self) -> None:
        metrics = _compute_metrics([])
        assert metrics["relevant_pct"] == 0.0
        assert metrics["avg_confidence"] == 0.0
        assert metrics["avg_latency_ms"] == 0.0
        assert metrics["human_agreement_rate"] == 0.0

    def test_all_relevant(self) -> None:
        judgments = [
            {
                "label": "relevant",
                "confidence": 0.9,
                "latency_ms": 100.0,
                "human_corrected": False,
                "human_agreed": None,
            },
            {
                "label": "relevant",
                "confidence": 0.8,
                "latency_ms": 200.0,
                "human_corrected": False,
                "human_agreed": None,
            },
        ]
        metrics = _compute_metrics(judgments)
        assert metrics["relevant_pct"] == 1.0
        assert abs(metrics["avg_confidence"] - 0.85) < 1e-9
        assert metrics["avg_latency_ms"] == 150.0

    def test_mixed_labels(self) -> None:
        judgments = [
            {
                "label": "relevant",
                "confidence": 0.9,
                "latency_ms": 100,
                "human_corrected": False,
                "human_agreed": None,
            },
            {
                "label": "irrelevant",
                "confidence": 0.8,
                "latency_ms": 100,
                "human_corrected": False,
                "human_agreed": None,
            },
        ]
        metrics = _compute_metrics(judgments)
        assert metrics["relevant_pct"] == 0.5

    def test_human_agreement(self) -> None:
        judgments = [
            {
                "label": "relevant",
                "confidence": 0.9,
                "latency_ms": 100,
                "human_corrected": True,
                "human_agreed": True,
            },
            {
                "label": "relevant",
                "confidence": 0.8,
                "latency_ms": 100,
                "human_corrected": True,
                "human_agreed": False,
            },
        ]
        metrics = _compute_metrics(judgments)
        assert metrics["human_agreement_rate"] == 0.5


class TestGenerateRecommendation:
    def test_not_significant(self) -> None:
        result = _generate_recommendation(
            {"human_agreement_rate": 0.8}, {"human_agreement_rate": 0.9}, is_significant=False
        )
        assert "Collect more data" in result

    def test_canary_better(self) -> None:
        result = _generate_recommendation(
            {"human_agreement_rate": 0.7}, {"human_agreement_rate": 0.85}, is_significant=True
        )
        assert "promoting canary" in result

    def test_primary_better(self) -> None:
        result = _generate_recommendation(
            {"human_agreement_rate": 0.85}, {"human_agreement_rate": 0.7}, is_significant=True
        )
        assert "Keep current primary" in result

    def test_similar_performance(self) -> None:
        result = _generate_recommendation(
            {"human_agreement_rate": 0.80}, {"human_agreement_rate": 0.82}, is_significant=True
        )
        assert "similarly" in result

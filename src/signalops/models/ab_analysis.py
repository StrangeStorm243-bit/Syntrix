"""Statistical analysis for A/B test experiments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session


@dataclass
class ABTestResults:
    """Summary of an A/B test experiment."""

    experiment_id: str
    primary_model: str
    canary_model: str
    primary_count: int
    canary_count: int
    primary_metrics: dict[str, float]
    canary_metrics: dict[str, float]
    chi_squared: float | None
    p_value: float | None
    is_significant: bool
    recommendation: str


def analyze_experiment(
    db_session: Session,
    experiment_id: str,
) -> ABTestResults:
    """Compute metrics and statistical significance for an A/B experiment."""
    from signalops.storage.database import ABExperiment, ABResult
    from signalops.storage.database import Judgment as JudgmentRow

    experiment = (
        db_session.query(ABExperiment).filter(ABExperiment.experiment_id == experiment_id).first()
    )
    if not experiment:
        msg = f"Experiment {experiment_id} not found"
        raise ValueError(msg)

    results = (
        db_session.query(ABResult, JudgmentRow)
        .join(JudgmentRow, ABResult.judgment_id == JudgmentRow.id)
        .filter(ABResult.experiment_id == experiment_id)
        .all()
    )

    primary_judgments: list[dict[str, Any]] = []
    canary_judgments: list[dict[str, Any]] = []

    for ab_result, judgment in results:
        entry: dict[str, Any] = {
            "label": judgment.label.value if judgment.label else "maybe",
            "confidence": float(judgment.confidence or 0),
            "latency_ms": float(ab_result.latency_ms or 0),
            "human_corrected": judgment.human_label is not None,
            "human_agreed": (
                judgment.human_label == judgment.label if judgment.human_label is not None else None
            ),
        }
        model_str = str(ab_result.model_used)
        if model_str.startswith("canary:"):
            canary_judgments.append(entry)
        else:
            primary_judgments.append(entry)

    primary_metrics = _compute_metrics(primary_judgments)
    canary_metrics = _compute_metrics(canary_judgments)

    chi_sq, p_val = _chi_squared_test(primary_judgments, canary_judgments)
    is_significant = p_val is not None and p_val < 0.05

    recommendation = _generate_recommendation(primary_metrics, canary_metrics, is_significant)

    return ABTestResults(
        experiment_id=experiment_id,
        primary_model=str(experiment.primary_model),
        canary_model=str(experiment.canary_model),
        primary_count=len(primary_judgments),
        canary_count=len(canary_judgments),
        primary_metrics=primary_metrics,
        canary_metrics=canary_metrics,
        chi_squared=chi_sq,
        p_value=p_val,
        is_significant=is_significant,
        recommendation=recommendation,
    )


def _compute_metrics(judgments: list[dict[str, Any]]) -> dict[str, float]:
    """Compute summary metrics for a set of judgments."""
    if not judgments:
        return {
            "relevant_pct": 0.0,
            "avg_confidence": 0.0,
            "avg_latency_ms": 0.0,
            "human_agreement_rate": 0.0,
        }
    total = len(judgments)
    relevant = sum(1 for j in judgments if j["label"] == "relevant")
    avg_conf = sum(j["confidence"] for j in judgments) / total
    avg_latency = sum(j["latency_ms"] for j in judgments) / total

    corrected = [j for j in judgments if j["human_corrected"]]
    agreement_rate = (
        sum(1 for j in corrected if j["human_agreed"]) / len(corrected) if corrected else 0.0
    )

    return {
        "relevant_pct": relevant / total,
        "avg_confidence": avg_conf,
        "avg_latency_ms": avg_latency,
        "human_agreement_rate": agreement_rate,
    }


def _chi_squared_test(
    primary: list[dict[str, Any]],
    canary: list[dict[str, Any]],
) -> tuple[float | None, float | None]:
    """Chi-squared test on label distribution between primary and canary."""
    if len(primary) < 5 or len(canary) < 5:
        return None, None

    try:
        import numpy as np
        from scipy.stats import chi2_contingency

        labels = ["relevant", "irrelevant", "maybe"]
        primary_counts = [sum(1 for j in primary if j["label"] == la) for la in labels]
        canary_counts = [sum(1 for j in canary if j["label"] == la) for la in labels]

        table = np.array([primary_counts, canary_counts])
        table = table[:, table.sum(axis=0) > 0]
        if table.shape[1] < 2:
            return None, None

        chi2, p, _, _ = chi2_contingency(table)
        return float(chi2), float(p)
    except ImportError:
        return None, None


def _generate_recommendation(
    primary: dict[str, float],
    canary: dict[str, float],
    is_significant: bool,
) -> str:
    """Generate a human-readable recommendation."""
    if not is_significant:
        return "No statistically significant difference between models yet. Collect more data."

    if canary["human_agreement_rate"] > primary["human_agreement_rate"] + 0.05:
        return (
            f"Canary model shows higher human agreement "
            f"({canary['human_agreement_rate']:.0%} vs {primary['human_agreement_rate']:.0%}). "
            f"Consider promoting canary to primary."
        )
    if primary["human_agreement_rate"] > canary["human_agreement_rate"] + 0.05:
        return (
            f"Primary model performs better "
            f"({primary['human_agreement_rate']:.0%} vs {canary['human_agreement_rate']:.0%}). "
            f"Keep current primary."
        )
    return "Models perform similarly. Consider other factors (latency, cost)."

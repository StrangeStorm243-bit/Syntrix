"""Offline evaluation runner for judge models."""

from __future__ import annotations

import json
import time
from collections.abc import Sequence
from typing import Any

from signalops.models.judge_model import RelevanceJudge


class JudgeEvaluator:
    """Evaluates judge model quality against labeled test sets."""

    def __init__(self, judge: RelevanceJudge) -> None:
        self._judge = judge

    def evaluate(
        self,
        test_set_path: str,
        project_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Run eval on a JSONL test set with gold labels.

        Each line: {text, author_bio, gold_label, author_followers, engagement}

        Returns: classification_report, MCC, confusion_matrix, mean_confidence,
                 n_examples, model_id, latency_stats
        """
        examples = self._load_test_set(test_set_path)

        if not examples:
            return {
                "n_examples": 0,
                "classification_report": {},
                "mcc": 0.0,
                "confusion_matrix": {},
                "mean_confidence": 0.0,
                "model_id": "",
                "latency_stats": {},
            }

        gold_labels: list[str] = []
        pred_labels: list[str] = []
        confidences: list[float] = []
        latencies: list[float] = []
        model_id = ""

        for ex in examples:
            text = ex.get("text", "")
            author_bio = ex.get("author_bio", "")
            gold = ex["gold_label"]

            start = time.perf_counter()
            judgment = self._judge.judge(text, author_bio, project_context)
            latency_ms = (time.perf_counter() - start) * 1000

            gold_labels.append(gold)
            pred_labels.append(judgment.label)
            confidences.append(judgment.confidence)
            latencies.append(latency_ms)
            model_id = judgment.model_id

        return self._compute_metrics(gold_labels, pred_labels, confidences, latencies, model_id)

    def compare(
        self,
        test_set_path: str,
        judges: Sequence[RelevanceJudge],
        project_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Run multiple judges on same test set for model selection."""
        results: list[dict[str, Any]] = []

        for judge in judges:
            evaluator = JudgeEvaluator(judge=judge)
            result = evaluator.evaluate(test_set_path, project_context)
            results.append(result)

        return {"results": results}

    def _load_test_set(self, path: str) -> list[dict[str, Any]]:
        """Load JSONL test set, handling missing optional fields."""
        examples: list[dict[str, Any]] = []
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                examples.append(record)
        return examples

    def _compute_metrics(
        self,
        gold: list[str],
        pred: list[str],
        confidences: list[float],
        latencies: list[float],
        model_id: str,
    ) -> dict[str, Any]:
        """Compute classification metrics."""
        try:
            from sklearn.metrics import (
                classification_report,
                confusion_matrix,
                matthews_corrcoef,
            )

            labels = sorted(set(gold) | set(pred))
            report = classification_report(
                gold, pred, labels=labels, output_dict=True, zero_division=0
            )
            mcc = float(matthews_corrcoef(gold, pred))
            cm = confusion_matrix(gold, pred, labels=labels).tolist()

        except ImportError:
            # Fallback: compute basic metrics without sklearn
            report, mcc, cm = self._basic_metrics(gold, pred)

        mean_conf = sum(confidences) / len(confidences) if confidences else 0.0
        mean_latency = sum(latencies) / len(latencies) if latencies else 0.0

        return {
            "n_examples": len(gold),
            "classification_report": report,
            "mcc": round(mcc, 4),
            "confusion_matrix": cm,
            "mean_confidence": round(mean_conf, 4),
            "model_id": model_id,
            "latency_stats": {
                "mean_ms": round(mean_latency, 2),
                "min_ms": round(min(latencies), 2) if latencies else 0.0,
                "max_ms": round(max(latencies), 2) if latencies else 0.0,
            },
        }

    def _basic_metrics(
        self, gold: list[str], pred: list[str]
    ) -> tuple[dict[str, Any], float, list[list[int]]]:
        """Compute basic metrics without sklearn."""
        labels = sorted(set(gold) | set(pred))
        correct = sum(1 for g, p in zip(gold, pred) if g == p)
        total = len(gold)
        accuracy = correct / total if total > 0 else 0.0

        # Basic confusion matrix
        label_idx = {lbl: i for i, lbl in enumerate(labels)}
        n = len(labels)
        cm = [[0] * n for _ in range(n)]
        for g, p in zip(gold, pred):
            cm[label_idx[g]][label_idx[p]] += 1

        # Basic MCC for binary case
        if len(labels) == 2:
            tp = cm[0][0]
            tn = cm[1][1]
            fp = cm[1][0]
            fn = cm[0][1]
            denom = ((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)) ** 0.5
            mcc = (tp * tn - fp * fn) / denom if denom > 0 else 0.0
        else:
            mcc = accuracy * 2 - 1  # rough approximation

        report: dict[str, Any] = {"accuracy": accuracy}
        return report, mcc, cm

"""Evaluation CLI commands."""

from __future__ import annotations

from typing import Any

import click


@click.group("eval")
def eval_group() -> None:
    """Evaluate judge models against test sets."""


@eval_group.command("judge")
@click.option("--test-set", required=True, type=click.Path(exists=True), help="JSONL test set path")
@click.option("--project", "project_name", default=None, help="Project name override")
@click.pass_context
def eval_judge(ctx: click.Context, test_set: str, project_name: str | None) -> None:
    """Evaluate current judge model against a labeled test set."""
    from signalops.cli.project import load_active_config
    from signalops.models.judge_model import LLMPromptJudge
    from signalops.models.llm_gateway import LLMGateway
    from signalops.training.evaluator import JudgeEvaluator

    console = ctx.obj["console"]

    config = load_active_config(ctx)
    project_context = {
        "project_name": config.project_name,
        "description": config.description,
        "relevance": {
            "system_prompt": config.relevance.system_prompt,
            "positive_signals": config.relevance.positive_signals,
            "negative_signals": config.relevance.negative_signals,
        },
    }

    gateway = LLMGateway(
        default_model=config.llm.judge_model,
        fallback_models=config.llm.fallback_models,
        temperature=config.llm.temperature,
        max_tokens=config.llm.max_tokens,
    )
    judge = LLMPromptJudge(gateway=gateway, model=config.llm.judge_model)

    evaluator = JudgeEvaluator(judge=judge)
    result = evaluator.evaluate(test_set_path=test_set, project_context=project_context)

    _display_results(console, result)


@eval_group.command("compare")
@click.option("--test-set", required=True, type=click.Path(exists=True), help="JSONL test set path")
@click.option("--models", required=True, help="Comma-separated model IDs")
@click.pass_context
def eval_compare(ctx: click.Context, test_set: str, models: str) -> None:
    """Compare multiple judge models on the same test set."""
    from rich.table import Table

    from signalops.cli.project import load_active_config
    from signalops.models.judge_model import LLMPromptJudge
    from signalops.models.llm_gateway import LLMGateway
    from signalops.training.evaluator import JudgeEvaluator

    console = ctx.obj["console"]

    config = load_active_config(ctx)
    project_context = {
        "project_name": config.project_name,
        "description": config.description,
        "relevance": {
            "system_prompt": config.relevance.system_prompt,
            "positive_signals": config.relevance.positive_signals,
            "negative_signals": config.relevance.negative_signals,
        },
    }

    model_ids = [m.strip() for m in models.split(",")]
    gateway = LLMGateway(
        default_model=config.llm.judge_model,
        fallback_models=config.llm.fallback_models,
        temperature=config.llm.temperature,
        max_tokens=config.llm.max_tokens,
    )
    judges = [LLMPromptJudge(gateway=gateway, model=m) for m in model_ids]

    evaluator = JudgeEvaluator(judge=judges[0])
    comparison = evaluator.compare(
        test_set_path=test_set, judges=judges, project_context=project_context
    )

    table = Table(title="Judge Model Comparison")
    table.add_column("Model", style="bold")
    table.add_column("MCC", justify="right")
    table.add_column("Accuracy", justify="right")
    table.add_column("Confidence", justify="right")
    table.add_column("Latency (ms)", justify="right")

    for r in comparison["results"]:
        report = r.get("classification_report", {})
        accuracy = report.get("accuracy", 0.0) if isinstance(report, dict) else 0.0
        table.add_row(
            r["model_id"],
            f"{r['mcc']:.4f}",
            f"{accuracy:.2%}" if isinstance(accuracy, float) else str(accuracy),
            f"{r['mean_confidence']:.4f}",
            f"{r['latency_stats']['mean_ms']:.1f}",
        )

    console.print(table)


def _display_results(console: Any, result: dict[str, Any]) -> None:
    """Display evaluation results in a Rich table."""
    from rich.table import Table

    table = Table(title=f"Evaluation Results — {result['model_id']}")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Examples", str(result["n_examples"]))
    table.add_row("MCC", f"{result['mcc']}")
    table.add_row("Mean Confidence", f"{result['mean_confidence']}")

    latency = result.get("latency_stats", {})
    if isinstance(latency, dict):
        table.add_row(
            "Latency (mean)",
            f"{latency.get('mean_ms', 0):.1f} ms",
        )

    console.print(table)

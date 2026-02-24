# Terminal 2 — Fine-Tuned Models + A/B Testing + DPO Preference Data

> **Scope:** Deploy fine-tuned classifiers, A/B test between models, collect DPO preference pairs,
> integrate LiteLLM as unified LLM gateway, add Langfuse observability, optional Argilla export
> **New files:** `models/ab_test.py`, `models/finetuned.py`, `training/dpo.py`, CLI commands
> **Touches existing:** `llm_gateway.py` (replaced by LiteLLM), `judge_model.py`, `orchestrator.py`, `schema.py`, `database.py`, `exporter.py`
> **Depends on:** None (fully isolated until Phase 3 integration)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Phase 0 — LiteLLM Gateway Replacement](#2-phase-0--litellm-gateway-replacement)
3. [Phase 1 — Fine-Tuned Model Support](#3-phase-1--fine-tuned-model-support)
4. [Phase 2 — A/B Testing Framework](#4-phase-2--ab-testing-framework)
5. [Phase 2.5 — Langfuse LLM Observability](#5-phase-25--langfuse-llm-observability)
6. [Phase 3 — DPO Preference Collection](#6-phase-3--dpo-preference-collection)
7. [Phase 4 — CLI Commands + Integration](#7-phase-4--cli-commands--integration)
8. [File Manifest](#8-file-manifest)
9. [Testing Plan](#9-testing-plan)

---

## 1. Overview

This terminal adds three core ML pipeline features plus three key integrations:

**Core Features:**

1. **Fine-Tuned Model Deployment** — The `RelevanceJudge` interface already supports swappable
   implementations. We add `FineTunedJudge` that calls OpenAI's fine-tuned model API and a
   `ModelRegistry` to track deployed models.

2. **A/B Testing** — `ABTestJudge` wraps two judges and routes traffic based on configurable
   percentages. Results are stored per-judgment for statistical comparison.

3. **DPO Preference Collection** — When a human edits a draft (chosen=edited, rejected=original)
   or rejects a draft, we auto-generate preference pairs for DPO fine-tuning.

**Integrations:**

4. **LiteLLM Gateway** — Replace the hand-rolled `llm_gateway.py` + `providers/` package with
   [LiteLLM](https://github.com/BerriAI/litellm) (16k+ stars). Unified API for 100+ LLM
   providers, automatic fallbacks, cost tracking, built-in rate limiting. This simplifies
   fine-tuned model routing (LiteLLM natively handles `ft:` prefixed models) and reduces
   code we need to maintain.

5. **Langfuse Observability** — Add [Langfuse](https://github.com/langfuse/langfuse) (19k+ stars)
   tracing to all LLM calls via `@observe()` decorators. Every judge and draft call gets traced
   with latency, token usage, cost, and output quality. The Langfuse dashboard provides
   experiment comparison UI for A/B tests, reducing the need for custom analytics code.

6. **Argilla Export (optional)** — Add [Argilla](https://github.com/argilla-io/argilla) (4k+ stars)
   as an optional export target for DPO preference pairs and human corrections. Gives a proper
   annotation UI for reviewing training data before fine-tuning. Not a hard dependency —
   users without Argilla use the existing JSONL export.

**Key design decisions:**
- LiteLLM replaces custom gateway — reduces provider-specific code to near zero
- Langfuse traces power A/B test analytics — less custom stats code needed
- Cloud-only fine-tuned models (OpenAI fine-tuning API) — no self-hosted inference
- A/B test is transparent to the pipeline — same `RelevanceJudge` interface
- DPO pairs auto-generated from existing approval flow — no new user actions needed
- Argilla is optional (`pip install signalops[argilla]`) — not a core dependency
- Model registry in DB for versioning and audit trail

---

## 2. Phase 0 — LiteLLM Gateway Replacement

> **Do this first.** LiteLLM replaces the foundation that all other T2 features build on.

### Step 0.1: Replace LLM Gateway

**Refactor `src/signalops/models/llm_gateway.py`:**

Replace the custom gateway with a thin wrapper around LiteLLM's `completion()` API:

```python
"""LLM Gateway — thin wrapper around LiteLLM for unified model access."""

from __future__ import annotations

import json
import logging
from typing import Any

import litellm

logger = logging.getLogger(__name__)

# Disable LiteLLM's verbose logging
litellm.suppress_debug_info = True


class LLMGateway:
    """Unified LLM interface powered by LiteLLM.

    Supports 100+ providers (OpenAI, Anthropic, Cohere, local models, etc.)
    via a single API. Handles routing, retries, and fallbacks.
    """

    def __init__(
        self,
        default_model: str = "claude-sonnet-4-6",
        fallback_models: list[str] | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> None:
        self._default_model = default_model
        self._fallback_models = fallback_models or []
        self._temperature = temperature
        self._max_tokens = max_tokens

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        temperature: float | None = None,
    ) -> str:
        """Get a text completion from the LLM."""
        model = model or self._default_model
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = litellm.completion(
            model=model,
            messages=messages,
            temperature=temperature or self._temperature,
            max_tokens=self._max_tokens,
            fallbacks=self._fallback_models if self._fallback_models else None,
        )
        return response.choices[0].message.content or ""

    def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        """Get a JSON completion, parsed into a dict."""
        raw = self.complete(system_prompt, user_prompt, model, temperature)
        # Strip markdown code fences if present
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
        try:
            return json.loads(raw)  # type: ignore[no-any-return]
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM JSON response: %s", raw[:200])
            return {"error": "parse_failed", "raw": raw}

    def get_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Get cost estimate for a completion using LiteLLM's cost tracking."""
        try:
            return litellm.completion_cost(
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )
        except Exception:
            return 0.0
```

### Step 0.2: Remove Custom Providers

**Delete or gut these files:**
- `src/signalops/models/providers/anthropic.py` — no longer needed, LiteLLM handles it
- `src/signalops/models/providers/openai.py` — no longer needed
- `src/signalops/models/providers/base.py` — no longer needed

Keep `providers/__init__.py` as an empty package if needed for imports, or remove the
entire `providers/` directory.

### Step 0.3: Update Config

**Update `src/signalops/config/schema.py`:**

```python
class LLMConfig(BaseModel):
    """LLM configuration — powered by LiteLLM."""
    judge_model: str = "claude-sonnet-4-6"
    draft_model: str = "claude-sonnet-4-6"
    temperature: float = 0.3
    max_tokens: int = 1024
    fallback_models: list[str] = []           # Automatic fallback chain
    judge_fallback_model: str | None = None   # Judge-specific fallback
    max_judge_latency_ms: float = 5000        # Timeout before fallback
```

### Step 0.4: Update Dependencies

**Update `pyproject.toml`:**

```toml
dependencies = [
    # ... existing ...
    "litellm>=1.55",
    # Remove: "anthropic>=0.40" and "openai>=1.50"
    # (LiteLLM includes them as transitive deps)
]
```

### Step 0.5: Update Tests

- Update all tests that mock `LLMGateway` — the interface stays the same, just the internals change
- Add `tests/unit/test_litellm_gateway.py` — test the new gateway wrapper
- Verify `complete_json()` still handles malformed LLM responses correctly

**Acceptance criteria for Phase 0:**
- [ ] `litellm.completion()` is the only way LLM calls are made
- [ ] `providers/` directory is removed or emptied
- [ ] All existing judge and draft tests pass with the new gateway
- [ ] Fallback chain works: if primary model fails, fallback is tried
- [ ] Cost tracking via `litellm.completion_cost()` works

---

## 3. Phase 1 — Fine-Tuned Model Support

### Step 1: Model Registry

**Create DB migration — add `model_registry` table:**

```python
# Add to src/signalops/storage/database.py

class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(String(256), nullable=False, unique=True)  # "ft:gpt-4o-mini-2024-07-18:org:spectra-judge-v1"
    provider = Column(String(32), nullable=False)     # "openai", "anthropic"
    model_type = Column(String(32), nullable=False)   # "judge", "drafter"
    display_name = Column(String(256))                # Human-friendly name
    base_model = Column(String(128))                  # Original model fine-tuned from
    training_file = Column(String(512))               # Path to training JSONL used
    training_examples = Column(Integer)               # Number of training examples
    version = Column(String(64))                      # "v1", "v2", etc.
    deployed_at = Column(DateTime, server_default=func.now())
    is_active = Column(Boolean, default=True)
    metrics = Column(JSON)                            # {"precision": 0.92, "recall": 0.85, ...}
    metadata_ = Column("metadata", JSON)              # Arbitrary metadata

    __table_args__ = (
        Index("ix_model_registry_type_active", "model_type", "is_active"),
    )
```

### Step 2: Fine-Tuned Judge Implementation

**Create `src/signalops/models/finetuned.py`:**

```python
"""Fine-tuned model judge — calls cloud provider fine-tuned endpoints."""

from __future__ import annotations

import time
from typing import Any

from signalops.models.judge_model import Judgment, RelevanceJudge
from signalops.models.llm_gateway import LLMGateway


class FineTunedJudge(RelevanceJudge):
    """Calls a fine-tuned model (OpenAI or Anthropic) for relevance judgment."""

    def __init__(self, gateway: LLMGateway, model_id: str) -> None:
        self._gateway = gateway
        self._model_id = model_id

    def judge(self, post_text: str, author_bio: str,
              project_context: dict[str, Any]) -> Judgment:
        """Judge using fine-tuned model. Same prompt format as training data."""
        system_prompt = self._build_system_prompt(project_context)
        user_prompt = self._build_user_prompt(post_text, author_bio, project_context)

        start = time.perf_counter()
        try:
            result = self._gateway.complete_json(
                system_prompt, user_prompt, model=self._model_id
            )
            latency_ms = (time.perf_counter() - start) * 1000

            label = result.get("label", "maybe")
            if label not in ("relevant", "irrelevant", "maybe"):
                label = "maybe"

            confidence = float(result.get("confidence", 0.5))
            confidence = max(0.0, min(1.0, confidence))

            return Judgment(
                label=label,
                confidence=confidence,
                reasoning=result.get("reasoning", ""),
                model_id=self._model_id,
                latency_ms=latency_ms,
            )
        except Exception:
            latency_ms = (time.perf_counter() - start) * 1000
            return Judgment(
                label="maybe",
                confidence=0.3,
                reasoning="Fallback: fine-tuned model call failed",
                model_id=f"fallback:{self._model_id}",
                latency_ms=latency_ms,
            )

    def judge_batch(self, items: list[dict[str, Any]]) -> list[Judgment]:
        """Batch by calling individual judge sequentially.
        Fine-tuned models are fast enough that batching via prompt isn't needed."""
        return [
            self.judge(
                item["post_text"],
                item.get("author_bio", ""),
                item.get("project_context", {}),
            )
            for item in items
        ]

    def _build_system_prompt(self, project_context: dict[str, Any]) -> str:
        """Use the same format as training data export for consistency."""
        # Mirror the format from TrainingDataExporter.export_judgments
        project_name = project_context.get("project_name", "Unknown Project")
        description = project_context.get("description", "")
        relevance = project_context.get("relevance", {})
        system_prompt_text = relevance.get("system_prompt", "")
        positive_signals = relevance.get("positive_signals", [])
        negative_signals = relevance.get("negative_signals", [])

        positive_block = "\n".join(f"- {s}" for s in positive_signals)
        negative_block = "\n".join(f"- {s}" for s in negative_signals)

        return (
            f"You are a relevance judge for {project_name}. {description}\n\n"
            f"{system_prompt_text}\n\n"
            f"Positive signals:\n{positive_block}\n\n"
            f"Negative signals:\n{negative_block}\n\n"
            'Respond with JSON: {"label": "relevant"|"irrelevant"|"maybe", '
            '"confidence": 0.0-1.0, "reasoning": "..."}'
        )

    def _build_user_prompt(self, post_text: str, author_bio: str,
                           metrics: dict[str, Any] | None = None) -> str:
        parts = [f'Tweet: "{post_text}"']
        if author_bio:
            parts.append(f'Author bio: "{author_bio}"')
        return "\n".join(parts)
```

### Step 3: Model Routing in Config

**Extend `src/signalops/config/schema.py`:**

```python
class LLMConfig(BaseModel):
    """LLM configuration with model routing."""
    judge_model: str = "claude-sonnet-4-6"
    draft_model: str = "claude-sonnet-4-6"
    temperature: float = 0.3
    # New fields for v0.3:
    judge_fallback_model: str | None = None    # Fallback if primary fails
    max_judge_latency_ms: float = 5000         # Timeout before fallback

class ExperimentConfig(BaseModel):
    """A/B testing configuration."""
    enabled: bool = False
    default_canary_pct: float = 0.1
```

**Update `ProjectConfig`:**
```python
class ProjectConfig(BaseModel):
    # ... existing fields ...
    llm: LLMConfig = LLMConfig()               # Replace dict with typed model
    experiments: ExperimentConfig = ExperimentConfig()
```

> **Note:** Changing `llm` from `dict[str, Any]` to `LLMConfig` is a **breaking change** for
> existing project YAML files. Add backward compatibility in the config loader:
> if `llm` is a dict, construct `LLMConfig` from it.

### Step 4: Judge Factory

**Update orchestrator or create `src/signalops/models/judge_factory.py`:**

```python
"""Factory for creating the appropriate RelevanceJudge based on config."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from signalops.config.schema import ProjectConfig
    from signalops.models.judge_model import RelevanceJudge
    from signalops.models.llm_gateway import LLMGateway


def create_judge(config: ProjectConfig, gateway: LLMGateway) -> RelevanceJudge:
    """Route to the correct judge implementation based on config."""
    model_id = config.llm.judge_model

    if model_id.startswith("ft:"):
        from signalops.models.finetuned import FineTunedJudge
        return FineTunedJudge(gateway=gateway, model_id=model_id)

    if config.experiments.enabled:
        from signalops.models.ab_test import create_ab_test_judge
        return create_ab_test_judge(config, gateway)

    from signalops.models.judge_model import LLMPromptJudge
    return LLMPromptJudge(gateway=gateway, model=model_id)
```

---

## 3. Phase 2 — A/B Testing Framework

### Step 5: A/B Test Database Tables

**Add to `src/signalops/storage/database.py`:**

```python
class ABExperiment(Base):
    __tablename__ = "ab_experiments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String(64), nullable=False, unique=True)
    project_id = Column(String(64), ForeignKey("projects.id"), nullable=False)
    primary_model = Column(String(256), nullable=False)
    canary_model = Column(String(256), nullable=False)
    canary_pct = Column(Float, nullable=False, default=0.1)
    status = Column(String(16), nullable=False, default="active")  # active, paused, completed
    started_at = Column(DateTime, server_default=func.now())
    ended_at = Column(DateTime)
    hypothesis = Column(Text)                    # "Fine-tuned v2 has higher precision"
    metadata_ = Column("metadata", JSON)

    __table_args__ = (
        Index("ix_ab_experiment_project_status", "project_id", "status"),
    )


class ABResult(Base):
    __tablename__ = "ab_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String(64), ForeignKey("ab_experiments.experiment_id"), nullable=False)
    judgment_id = Column(Integer, ForeignKey("judgments.id"), nullable=False)
    model_used = Column(String(256), nullable=False)
    latency_ms = Column(Float)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_ab_result_experiment", "experiment_id"),
    )
```

**Add to `judgments` table:**
```python
# In Judgment class:
experiment_id = Column(String(64))  # Nullable — only set during A/B tests
```

### Step 6: ABTestJudge Implementation

**Create `src/signalops/models/ab_test.py`:**

```python
"""A/B test judge — wraps two judges with configurable traffic routing."""

from __future__ import annotations

import random
import time
from typing import Any

from sqlalchemy.orm import Session

from signalops.models.judge_model import Judgment, RelevanceJudge


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

    def judge(self, post_text: str, author_bio: str,
              project_context: dict[str, Any]) -> Judgment:
        use_canary = random.random() < self._canary_pct
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

    def _record_result(self, judgment: Judgment, latency_ms: float) -> None:
        """Store A/B test result for later analysis."""
        from signalops.storage.database import ABResult

        result = ABResult(
            experiment_id=self._experiment_id,
            judgment_id=0,  # Will be updated after judgment is persisted
            model_used=judgment.model_id,
            latency_ms=latency_ms,
        )
        if self._session:
            self._session.add(result)


def create_ab_test_judge(
    config: "ProjectConfig",
    gateway: "LLMGateway",
    db_session: Session | None = None,
) -> ABTestJudge:
    """Create an ABTestJudge from config. Finds the active experiment."""
    from signalops.models.finetuned import FineTunedJudge
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
            primary = _create_single_judge(experiment.primary_model, gateway)
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


def _create_single_judge(model_id: str, gateway: "LLMGateway") -> RelevanceJudge:
    """Create a judge for a specific model ID."""
    from signalops.models.finetuned import FineTunedJudge
    from signalops.models.judge_model import LLMPromptJudge

    if model_id.startswith("ft:"):
        return FineTunedJudge(gateway=gateway, model_id=model_id)
    return LLMPromptJudge(gateway=gateway, model=model_id)
```

### Step 7: Statistical Analysis

**Create `src/signalops/models/ab_analysis.py`:**

```python
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
    primary_metrics: dict[str, float]   # {"relevant_pct": 0.35, "avg_confidence": 0.82, ...}
    canary_metrics: dict[str, float]
    chi_squared: float | None           # Chi-squared test statistic
    p_value: float | None               # Statistical significance
    is_significant: bool                 # p < 0.05
    recommendation: str                  # "canary is better", "no significant difference", etc.


def analyze_experiment(
    db_session: Session,
    experiment_id: str,
) -> ABTestResults:
    """Compute metrics and statistical significance for an A/B experiment."""
    from signalops.storage.database import ABExperiment, ABResult, Judgment as JudgmentRow

    experiment = (
        db_session.query(ABExperiment)
        .filter(ABExperiment.experiment_id == experiment_id)
        .first()
    )
    if not experiment:
        raise ValueError(f"Experiment {experiment_id} not found")

    # Fetch all results with their judgments
    results = (
        db_session.query(ABResult, JudgmentRow)
        .join(JudgmentRow, ABResult.judgment_id == JudgmentRow.id)
        .filter(ABResult.experiment_id == experiment_id)
        .all()
    )

    primary_judgments: list[dict[str, Any]] = []
    canary_judgments: list[dict[str, Any]] = []

    for ab_result, judgment in results:
        entry = {
            "label": judgment.label.value if judgment.label else "maybe",
            "confidence": float(judgment.confidence or 0),
            "latency_ms": float(ab_result.latency_ms or 0),
            "human_corrected": judgment.human_label is not None,
            "human_agreed": (
                judgment.human_label == judgment.label
                if judgment.human_label is not None
                else None
            ),
        }
        model_str = str(ab_result.model_used)
        if model_str.startswith("canary:"):
            canary_judgments.append(entry)
        else:
            primary_judgments.append(entry)

    primary_metrics = _compute_metrics(primary_judgments)
    canary_metrics = _compute_metrics(canary_judgments)

    # Chi-squared test on label distribution
    chi_sq, p_val = _chi_squared_test(primary_judgments, canary_judgments)
    is_significant = p_val is not None and p_val < 0.05

    recommendation = _generate_recommendation(
        primary_metrics, canary_metrics, is_significant
    )

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
            "relevant_pct": 0.0, "avg_confidence": 0.0,
            "avg_latency_ms": 0.0, "human_agreement_rate": 0.0,
        }
    total = len(judgments)
    relevant = sum(1 for j in judgments if j["label"] == "relevant")
    avg_conf = sum(j["confidence"] for j in judgments) / total
    avg_latency = sum(j["latency_ms"] for j in judgments) / total

    corrected = [j for j in judgments if j["human_corrected"]]
    agreement_rate = (
        sum(1 for j in corrected if j["human_agreed"]) / len(corrected)
        if corrected else 0.0
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
        return None, None  # Not enough data

    try:
        from scipy.stats import chi2_contingency
        import numpy as np

        labels = ["relevant", "irrelevant", "maybe"]
        primary_counts = [sum(1 for j in primary if j["label"] == l) for l in labels]
        canary_counts = [sum(1 for j in canary if j["label"] == l) for l in labels]

        table = np.array([primary_counts, canary_counts])
        # Remove columns with all zeros
        table = table[:, table.sum(axis=0) > 0]
        if table.shape[1] < 2:
            return None, None

        chi2, p, _, _ = chi2_contingency(table)
        return float(chi2), float(p)
    except ImportError:
        # scipy not available — skip significance test
        return None, None


def _generate_recommendation(
    primary: dict[str, float],
    canary: dict[str, float],
    is_significant: bool,
) -> str:
    """Generate a human-readable recommendation."""
    if not is_significant:
        return "No statistically significant difference between models yet. Collect more data."

    # Compare human agreement rates
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
```

---

## 5. Phase 2.5 — Langfuse LLM Observability

### Step 7.5: Add Langfuse Tracing

**Install:** `pip install langfuse`

**Update `pyproject.toml`:**
```toml
dependencies = [
    # ... existing ...
    "langfuse>=2.50",
]
```

**Instrument the LLM Gateway (`src/signalops/models/llm_gateway.py`):**

```python
from langfuse.decorators import observe, langfuse_context

class LLMGateway:
    # ... existing __init__ ...

    @observe(as_type="generation")
    def complete(self, system_prompt: str, user_prompt: str,
                 model: str | None = None, temperature: float | None = None) -> str:
        """Get a text completion — traced by Langfuse."""
        model = model or self._default_model
        langfuse_context.update_current_observation(
            model=model,
            metadata={"temperature": temperature or self._temperature},
        )
        # ... existing litellm.completion() call ...
```

**Instrument the Judge (`src/signalops/models/judge_model.py`):**

```python
from langfuse.decorators import observe

class LLMPromptJudge(RelevanceJudge):
    @observe(name="judge_relevance")
    def judge(self, post_text, author_bio, project_context):
        # ... existing logic — Langfuse auto-captures the LLM call inside ...
```

**Instrument the Drafter (`src/signalops/models/draft_model.py`):**

```python
from langfuse.decorators import observe

class LLMDraftGenerator(DraftGenerator):
    @observe(name="generate_draft")
    def generate(self, post_text, author_context, project_context, persona):
        # ... existing logic ...
```

**Tag A/B test experiments:**

```python
# In ABTestJudge.judge():
from langfuse.decorators import langfuse_context

langfuse_context.update_current_trace(
    tags=["ab-test", f"experiment:{self._experiment_id}"],
    metadata={"model_variant": "canary" if use_canary else "primary"},
)
```

**Environment variables:**
```bash
# .env additions
LANGFUSE_PUBLIC_KEY=pk-...      # From Langfuse dashboard (self-hosted or cloud)
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_HOST=http://localhost:3000  # Self-hosted URL, or https://cloud.langfuse.com
```

**What this gives you:**
- Every LLM call traced with latency, tokens, cost, input/output
- A/B test experiments tagged and filterable in Langfuse dashboard
- Model comparison views (fine-tuned vs prompt-based) without custom code
- Cost tracking per project, per model, per time period
- The Experiments page in T1's React dashboard can link to Langfuse instead of building custom charts

**Acceptance criteria:**
- [ ] Every judge and draft LLM call appears in Langfuse traces
- [ ] A/B test experiments are tagged and filterable
- [ ] Langfuse is optional — if env vars are missing, tracing is silently disabled
- [ ] No performance impact when Langfuse is disabled

---

## 6. Phase 3 — DPO Preference Collection

### Step 8: Preference Pairs Table

**Add to `src/signalops/storage/database.py`:**

```python
class PreferencePair(Base):
    __tablename__ = "preference_pairs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    draft_id = Column(Integer, ForeignKey("drafts.id"), nullable=False)
    project_id = Column(String(64), ForeignKey("projects.id"), nullable=False)
    prompt = Column(Text, nullable=False)              # The draft generation prompt
    chosen_text = Column(Text, nullable=False)         # Human-preferred text
    rejected_text = Column(Text, nullable=False)       # Machine-generated (rejected) text
    source = Column(String(32), nullable=False)        # "edit", "reject", "manual"
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_pref_pair_project", "project_id"),
    )
```

### Step 9: DPO Collector

**Create `src/signalops/training/dpo.py`:**

```python
"""DPO preference pair collection from draft approvals/rejections."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from signalops.storage.database import (
    Draft,
    DraftStatus,
    NormalizedPost,
    PreferencePair,
    Project,
)


class DPOCollector:
    """Automatically generates DPO preference pairs from draft lifecycle events."""

    def __init__(self, db_session: Session) -> None:
        self._session = db_session

    def collect_from_edit(self, draft_id: int) -> PreferencePair | None:
        """When a draft is edited, the edit is 'chosen' and original is 'rejected'."""
        draft = self._session.query(Draft).filter(Draft.id == draft_id).first()
        if not draft or draft.status != DraftStatus.EDITED:
            return None
        if not draft.text_final or not draft.text_generated:
            return None

        # Don't create duplicate pairs
        existing = (
            self._session.query(PreferencePair)
            .filter(PreferencePair.draft_id == draft_id)
            .first()
        )
        if existing:
            return None

        prompt = self._build_prompt(draft)
        pair = PreferencePair(
            draft_id=draft_id,
            project_id=str(draft.project_id),
            prompt=prompt,
            chosen_text=str(draft.text_final),
            rejected_text=str(draft.text_generated),
            source="edit",
        )
        self._session.add(pair)
        self._session.commit()
        return pair

    def collect_from_rejection(
        self, draft_id: int, better_text: str | None = None
    ) -> PreferencePair | None:
        """When a draft is rejected. If better_text provided, use as 'chosen'."""
        draft = self._session.query(Draft).filter(Draft.id == draft_id).first()
        if not draft or draft.status != DraftStatus.REJECTED:
            return None

        # For rejections without a better alternative, we can still record
        # the rejection as a negative signal (rejected_text only)
        if not better_text:
            return None  # Can't create a pair without a chosen alternative

        existing = (
            self._session.query(PreferencePair)
            .filter(PreferencePair.draft_id == draft_id)
            .first()
        )
        if existing:
            return None

        prompt = self._build_prompt(draft)
        pair = PreferencePair(
            draft_id=draft_id,
            project_id=str(draft.project_id),
            prompt=prompt,
            chosen_text=better_text,
            rejected_text=str(draft.text_generated),
            source="reject",
        )
        self._session.add(pair)
        self._session.commit()
        return pair

    def collect_all_pending(self, project_id: str) -> dict[str, int]:
        """Scan for edited/rejected drafts that don't have preference pairs yet."""
        stats = {"edits_collected": 0, "rejections_skipped": 0}

        edited_drafts = (
            self._session.query(Draft)
            .filter(
                Draft.project_id == project_id,
                Draft.status == DraftStatus.EDITED,
                Draft.text_final.isnot(None),
            )
            .all()
        )

        for draft in edited_drafts:
            pair = self.collect_from_edit(int(draft.id))
            if pair:
                stats["edits_collected"] += 1

        rejected_count = (
            self._session.query(Draft)
            .filter(
                Draft.project_id == project_id,
                Draft.status == DraftStatus.REJECTED,
            )
            .count()
        )
        stats["rejections_skipped"] = rejected_count

        return stats

    def _build_prompt(self, draft: Draft) -> str:
        """Reconstruct the prompt that generated this draft."""
        post = (
            self._session.query(NormalizedPost)
            .filter(NormalizedPost.id == draft.normalized_post_id)
            .first()
        )
        project = (
            self._session.query(Project)
            .filter(Project.id == draft.project_id)
            .first()
        )

        project_name = str(project.name) if project else "Unknown"
        post_text = str(post.text_original) if post else "Unknown"
        author = str(post.author_username) if post else "Unknown"

        return (
            f"Write a helpful reply to this tweet for {project_name}.\n\n"
            f"Tweet: \"{post_text}\"\n"
            f"Author: @{author}\n"
        )


def export_dpo_pairs(
    db_session: Session,
    project_id: str,
    output_path: str = "preferences.jsonl",
) -> dict[str, Any]:
    """Export preference pairs as JSONL for DPO fine-tuning."""
    import json

    pairs = (
        db_session.query(PreferencePair)
        .filter(PreferencePair.project_id == project_id)
        .all()
    )

    records = []
    for pair in pairs:
        record = {
            "prompt": pair.prompt,
            "chosen": pair.chosen_text,
            "rejected": pair.rejected_text,
        }
        records.append(record)

    with open(output_path, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    return {"records": len(records), "output": output_path}
```

### Step 10: Hook DPO into Approval Flow

**Modify `src/signalops/cli/approve.py`:**
- After `edit` action: call `DPOCollector.collect_from_edit(draft_id)`
- After `reject` action: prompt for better text (optional), call `collect_from_rejection`
- Add `--collect-dpo` flag (default: True) to control preference pair generation

**Modify `src/signalops/pipeline/sender.py`:**
- After marking draft as EDITED via API, also trigger DPO collection

---

## 5. Phase 4 — CLI Commands + Integration

### Step 11: Experiment CLI Commands

**Create `src/signalops/cli/experiment.py`:**

```
signalops experiment create --primary "claude-sonnet-4-6" --canary "ft:gpt-4o-mini:spectra-v1" --canary-pct 0.1
signalops experiment list
signalops experiment results <experiment_id>
signalops experiment stop <experiment_id>
```

**Commands:**

- `create` — Creates a new A/B experiment, stores in DB, prints experiment_id
- `list` — Shows active and recent experiments with status
- `results` — Computes and displays ABTestResults with table formatting
- `stop` — Sets experiment status to "completed", records end time

### Step 12: Model Registry CLI Commands

**Create `src/signalops/cli/model.py`:**

```
signalops model register --model-id "ft:gpt-4o-mini:spectra-v1" --provider openai --type judge
signalops model list
signalops model activate <model_id>
signalops model deactivate <model_id>
```

### Step 13: DPO Export CLI Extension

**Extend `src/signalops/cli/export.py`:**

```
signalops export training-data --type dpo --project spectra --output preferences.jsonl
```

- Add `dpo` as a valid `--type` option alongside existing `judgments`
- Calls `export_dpo_pairs()` from `training/dpo.py`

### Step 13.5: Argilla Export (Optional)

**Create `src/signalops/training/argilla_export.py`:**

```python
"""Optional Argilla export for DPO pairs and human corrections."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session


def export_to_argilla(
    db_session: Session,
    project_id: str,
    argilla_api_url: str = "http://localhost:6900",
    argilla_api_key: str = "",
    dataset_name: str | None = None,
) -> dict[str, Any]:
    """Push preference pairs to Argilla for annotation review.

    Requires: pip install signalops[argilla]
    """
    try:
        import argilla as rg
    except ImportError:
        return {"error": "argilla not installed. Run: pip install signalops[argilla]"}

    client = rg.Argilla(api_url=argilla_api_url, api_key=argilla_api_key)
    name = dataset_name or f"signalops-dpo-{project_id}"

    from signalops.storage.database import PreferencePair

    pairs = (
        db_session.query(PreferencePair)
        .filter(PreferencePair.project_id == project_id)
        .all()
    )

    records = [
        rg.Record(
            fields={"prompt": pair.prompt, "chosen": pair.chosen_text, "rejected": pair.rejected_text},
            metadata={"source": pair.source, "draft_id": pair.draft_id},
        )
        for pair in pairs
    ]

    dataset = rg.Dataset(name=name, records=records)
    dataset.push_to_argilla(client)
    return {"records": len(records), "dataset": name}
```

**Extend CLI (`src/signalops/cli/export.py`):**
```
signalops export training-data --type dpo --output argilla --argilla-url http://localhost:6900
```

Add `--output` option: `jsonl` (default) or `argilla`. When `argilla`, calls `export_to_argilla()`.

**Update `pyproject.toml`:**
```toml
[project.optional-dependencies]
argilla = ["argilla>=2.0"]
```

### Step 14: Update Orchestrator

**Modify `src/signalops/pipeline/orchestrator.py`:**
- Use `create_judge()` factory instead of directly using the judge parameter
- This allows A/B testing to be transparent to the caller
- Add `experiment_id` to judgment rows when A/B test is active

---

## 6. File Manifest

### New Files

```
src/signalops/models/finetuned.py       # FineTunedJudge
src/signalops/models/ab_test.py         # ABTestJudge + create_ab_test_judge
src/signalops/models/ab_analysis.py     # Statistical analysis
src/signalops/models/judge_factory.py   # Judge routing factory
src/signalops/training/dpo.py           # DPO preference pair collection + export
src/signalops/cli/experiment.py         # experiment create/list/results/stop
src/signalops/cli/model.py             # model register/list/activate/deactivate
tests/unit/test_finetuned.py
tests/unit/test_ab_test.py
tests/unit/test_ab_analysis.py
tests/unit/test_dpo.py
tests/unit/test_judge_factory.py
tests/integration/test_ab_pipeline.py
```

### Modified Files

```
src/signalops/storage/database.py       # Add ModelRegistry, ABExperiment, ABResult, PreferencePair tables
src/signalops/config/schema.py          # Add LLMConfig, ExperimentConfig models
src/signalops/config/loader.py          # Backward compat for llm dict → LLMConfig
src/signalops/cli/main.py              # Register experiment and model command groups
src/signalops/cli/approve.py           # Hook DPO collection into edit/reject
src/signalops/cli/export.py            # Add --type dpo option
src/signalops/pipeline/orchestrator.py  # Use judge factory, record experiment_id
pyproject.toml                          # Add scipy optional dependency
```

---

## 7. Testing Plan

### Unit Tests

| Test File | Coverage |
|-----------|----------|
| `test_finetuned.py` | Mock LLM gateway, test judgment parsing, test fallback on error |
| `test_ab_test.py` | Traffic split ratio, canary tagging, result recording |
| `test_ab_analysis.py` | Metric computation, chi-squared test, recommendation generation |
| `test_dpo.py` | Pair generation from edits, rejection handling, duplicate prevention, JSONL export |
| `test_judge_factory.py` | Routing: ft: prefix → FineTunedJudge, experiment → ABTestJudge, default → LLMPromptJudge |

### Integration Tests

| Test File | Coverage |
|-----------|----------|
| `test_ab_pipeline.py` | Full pipeline with A/B test active: both models called, results stored, analysis works |

### Key Test Cases

```python
# A/B split respects ratio
def test_canary_traffic_split():
    """With canary_pct=0.2, ~20% of calls should go to canary."""
    ab_judge = ABTestJudge(primary, canary, canary_pct=0.2)
    results = [ab_judge.judge(...) for _ in range(1000)]
    canary_count = sum(1 for r in results if r.model_id.startswith("canary:"))
    assert 150 < canary_count < 250  # ~200 expected, allow variance

# DPO pairs from edits
def test_dpo_from_edit():
    """Editing a draft generates a preference pair."""
    # Create draft, mark as edited with text_final
    collector = DPOCollector(session)
    pair = collector.collect_from_edit(draft.id)
    assert pair.chosen_text == "edited text"
    assert pair.rejected_text == "original text"
    assert pair.source == "edit"

# Judge factory routing
def test_factory_routes_finetuned():
    config.llm.judge_model = "ft:gpt-4o-mini:spectra-v1"
    judge = create_judge(config, gateway)
    assert isinstance(judge, FineTunedJudge)
```

---

## Acceptance Criteria

- [ ] `signalops model register` creates entry in model_registry table
- [ ] Config with `judge_model: "ft:..."` routes to FineTunedJudge
- [ ] `signalops experiment create` starts A/B test with traffic split
- [ ] A/B results stored per-judgment with model attribution
- [ ] `signalops experiment results` shows statistical comparison table
- [ ] Draft edits auto-generate DPO preference pairs
- [ ] `signalops export training-data --type dpo` outputs valid JSONL
- [ ] Backward compatibility: existing project YAML files still load
- [ ] `ruff check` and `mypy --strict` pass on all new code
- [ ] All new tests pass

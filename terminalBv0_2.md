# Terminal B — Learning Loop + Evaluation (v0.2)

> **Branch:** `v02/learning` | **Worktree:** `.claude/worktrees/v02-learning`
> **Role:** Build the closed-loop learning system — outcome tracking, human corrections, training data export, offline evaluation.
> **Merge order:** B merges SECOND (after A's infrastructure).

---

## Context

Read PLANA.md (especially Section 6 — LLM Training & Learning Roadmap) and CLAUDE.md for full project context. You are Terminal B in a 3-terminal parallel v0.2 build.

This is NOT greenfield. The v0.1 codebase (45 source files) is complete. You are building the learning loop ON TOP of existing infrastructure. **Read each file BEFORE modifying it.**

### What Already Exists in the DB Schema

The v0.1 schema already has all the hooks you need:
- `Outcome` table with `OutcomeType` enum (`REPLY_RECEIVED`, `LIKE_RECEIVED`, `FOLLOW_RECEIVED`, `PROFILE_CLICK`, `LINK_CLICK`, `BOOKING`, `NEGATIVE`)
- `Judgment.human_label`, `Judgment.human_corrected_at`, `Judgment.human_reason` — nullable fields for human corrections
- `Draft.text_final` — stores the human-edited version (for DPO pairs)
- `Draft.sent_post_id` — ID of our reply tweet on X (what we poll for engagement)
- `DraftStatus.SENT`, `DraftStatus.EDITED` — statuses that indicate actionable data

You are building the **LOGIC** that reads/writes these existing columns.

### Cross-Terminal Dependency

Terminal A is simultaneously building `connectors/x_api.py` with a new `get_tweet_metrics()` method. Your `OutcomeTracker` will call that method at runtime, but Terminal A owns that file. Design your code to compile independently using a Protocol:

```python
from typing import Protocol

class EngagementPoller(Protocol):
    def get_tweet_metrics(self, tweet_ids: list[str]) -> dict[str, dict[str, int]]: ...
```

At merge time, `XConnector` will satisfy this Protocol (it will have `get_tweet_metrics()`).

### Critical Rules
- `from __future__ import annotations` in all files
- `dict[str, Any]` not bare `dict` (mypy strict)
- SQLAlchemy Column assignments: `# type: ignore[assignment]`
- 100-char line length (ruff)
- Do NOT modify `pyproject.toml` (Terminal A owns it)
- Run CI checks after each phase

---

## File Ownership

You own these files and ONLY these files. Do not touch anything else.

```
NEW FILES:
src/signalops/pipeline/outcome_tracker.py   ← Engagement outcome tracking
src/signalops/training/evaluator.py         ← Offline evaluation runner
src/signalops/training/labeler.py           ← Human correction helpers
src/signalops/cli/correct.py               ← correct command
src/signalops/cli/eval.py                  ← eval command group
tests/unit/test_outcome_tracker.py          ← Outcome tracker tests
tests/unit/test_evaluator.py               ← Evaluator tests
tests/unit/test_exporter.py                ← Exporter tests
tests/fixtures/eval_set.jsonl              ← 50 labeled test examples

MODIFIED FILES:
src/signalops/training/exporter.py         ← Enhanced training data exports
src/signalops/cli/export.py               ← Enhanced export CLI options
src/signalops/cli/main.py                 ← Register correct + eval commands
```

---

## Phase B1: Outcome Tracking

### 1. NEW `src/signalops/pipeline/outcome_tracker.py`

`OutcomeTracker` class that polls engagement on sent replies:

```python
class EngagementPoller(Protocol):
    def get_tweet_metrics(self, tweet_ids: list[str]) -> dict[str, dict[str, int]]: ...

class OutcomeTracker:
    def __init__(self, db_session: Session, poller: EngagementPoller) -> None: ...

    def track_outcomes(self, project_id: str) -> dict[str, Any]:
        """Poll engagement on all sent replies for this project.

        1. Query drafts where status=SENT and sent_post_id IS NOT NULL
        2. Call poller.get_tweet_metrics() with sent_post_id values (batch)
        3. For each reply, compare current metrics against previous check:
           - New likes → create Outcome(outcome_type=LIKE_RECEIVED)
           - New replies → create Outcome(outcome_type=REPLY_RECEIVED)
        4. Store baseline metrics in Outcome.details JSON for delta tracking
        5. Return: {tracked: N, new_likes: N, new_replies: N, new_follows: N}
        """

    def check_for_negative(self, project_id: str) -> list[Outcome]:
        """Check if any sent replies resulted in blocks/reports.
        If negative outcomes detected, log warning."""

    def get_outcome_summary(self, project_id: str) -> dict[str, Any]:
        """Aggregate outcome stats for display in stats dashboard.
        Returns: {total_sent, likes, replies, follows, negatives, engagement_rate}"""
```

### 2. NEW `tests/unit/test_outcome_tracker.py`

Test with mocked EngagementPoller:
- Test new likes detected (delta from previous check)
- Test new replies detected
- Test negative outcome detection
- Test no-op when no sent drafts exist
- Test batching of tweet IDs (>100 splits correctly)
- Test duplicate outcome prevention (same like not counted twice)

### Verify Phase B1
```bash
pytest tests/unit/test_outcome_tracker.py -v
ruff check src/signalops/pipeline/outcome_tracker.py tests/unit/test_outcome_tracker.py
mypy src/signalops/pipeline/outcome_tracker.py --strict
```

### Commit
```
feat(outcomes): outcome tracker for engagement polling on sent replies
```

---

## Phase B2: Feedback Loop (Human Corrections)

### 3. NEW `src/signalops/training/labeler.py`

Label collection helpers:

```python
def correct_judgment(
    db_session: Session,
    judgment_id: int,
    new_label: str,
    reason: str | None = None,
) -> Judgment:
    """Apply human correction to a judgment.
    Sets human_label, human_corrected_at, human_reason.
    Logs to audit. Returns updated judgment."""

def get_correction_stats(db_session: Session, project_id: str) -> dict[str, Any]:
    """Stats: total corrections, agreement rate (human == model), by label."""

def get_uncorrected_sample(
    db_session: Session,
    project_id: str,
    n: int = 10,
    strategy: str = "low_confidence",
) -> list[Judgment]:
    """Get judgments for human review.
    Strategies: 'low_confidence', 'random', 'recent'."""
```

### 4. NEW `src/signalops/cli/correct.py`

Two modes:

**Direct correction:**
```
signalops correct <judgment_id> --label [relevant|irrelevant|maybe] --reason "..."
```
- Show original post text, model judgment, confidence
- Apply correction via `labeler.correct_judgment()`
- Show before/after confirmation

**Interactive review mode:**
```
signalops correct --review [--n 10] [--strategy low_confidence]
```
- Pull N uncorrected judgments (low confidence first by default)
- For each: show post text, author, model judgment + confidence
- Prompt for label (relevant/irrelevant/maybe/skip)
- Optional reason prompt
- Track session stats (N corrected, N skipped, agreement rate)

### 5. MODIFY `src/signalops/cli/main.py`

Read the file first. Add at the bottom with existing registrations:

```python
from signalops.cli.correct import correct_cmd  # noqa: E402
from signalops.cli.eval import eval_group  # noqa: E402

cli.add_command(correct_cmd, "correct")
cli.add_command(eval_group, "eval")
```

### Verify Phase B2
```bash
pytest tests/unit/ -v
ruff check src/ tests/ && ruff format --check src/ tests/
mypy src/signalops --strict
```

### Commit
```
feat(feedback): human correction flow with interactive review mode
```

---

## Phase B3: Training Data Export Enhancement

### 6. MODIFY `src/signalops/training/exporter.py`

Read the file first. Enhance the existing `TrainingDataExporter`:

- **New method:** `export_outcomes(project_id, output)` → JSONL with outcome data for reward modeling
  - Each record: `{draft_text, score, outcomes: [{type, observed_at}], total_engagement}`
- **Add metadata** to all exports: `{project_id, exported_at, record_count, version: "0.2"}`
- **Add filtering:** `since: datetime | None` and `min_confidence: float | None` parameters
- **Improve `export_judgments`:** include post metrics (likes, followers) for richer training data
- **Improve `export_draft_preferences`:** include outcome data (did the chosen draft get engagement?)

### 7. MODIFY `src/signalops/cli/export.py`

Read the file first. Add new CLI options:
- `--since DATE` — only export data after this date
- `--min-confidence FLOAT` — only export judgments above this confidence
- `--type outcomes` — new export type for outcome data
- `--include-metadata` flag — include export metadata in output
- Show export summary after completion: record count, output path, file size

### 8. NEW `tests/unit/test_exporter.py`

Test export formats and filtering:
- Test judgment JSONL format matches OpenAI fine-tuning spec (messages array)
- Test DPO format has prompt/chosen/rejected fields
- Test outcome export format
- Test `--since` filtering excludes old records
- Test `--min-confidence` filtering excludes low-confidence judgments
- Test metadata inclusion when flag is set
- Test empty export (no matching records) → empty file, zero count

### Verify Phase B3
```bash
pytest tests/unit/test_exporter.py -v
ruff check src/ tests/ && ruff format --check src/ tests/
mypy src/signalops --strict
```

### Commit
```
feat(export): enhanced training data export with filtering and outcomes
```

---

## Phase B4: Offline Evaluation

### 9. NEW `src/signalops/training/evaluator.py`

`JudgeEvaluator` class (from PLANA.md Section 6):

```python
class JudgeEvaluator:
    def __init__(self, judge: RelevanceJudge) -> None: ...

    def evaluate(self, test_set_path: str, project_context: dict[str, Any]) -> dict[str, Any]:
        """Run eval on a JSONL test set with gold labels.

        Each line: {text, author_bio, gold_label, author_followers, engagement}
        Returns: classification_report, MCC, confusion_matrix, mean_confidence,
                 n_examples, model_id, latency_stats
        """

    def compare(
        self, test_set_path: str, judges: list[RelevanceJudge], project_context: dict[str, Any]
    ) -> dict[str, Any]:
        """Run multiple judges on same test set for model selection.
        Returns side-by-side comparison."""
```

**Important:** Use sklearn but don't modify pyproject.toml (Terminal A owns it). Use a guarded import:
```python
try:
    from sklearn.metrics import classification_report, matthews_corrcoef
except ImportError as e:
    raise ImportError("scikit-learn required for eval: pip install scikit-learn") from e
```

### 10. NEW `src/signalops/cli/eval.py`

Eval command group:

```
signalops eval judge --test-set <path> [--project <name>]
signalops eval compare --test-set <path> --models "claude-sonnet-4-6,gpt-4o-mini"
```

- Load test set from JSONL file
- Instantiate judge(s) based on project config or `--models` flag
- Run evaluator, display Rich table with classification report
- Show: precision, recall, F1, MCC, mean confidence, avg latency

### 11. NEW `tests/unit/test_evaluator.py`

Test evaluation logic with mock judges:
- Test with perfect predictions → precision/recall/F1 all 1.0
- Test with all-wrong predictions → metrics near 0
- Test JSONL parsing of test set (handles missing optional fields)
- Test `compare()` returns side-by-side results
- Test handles empty test set gracefully

### 12. NEW `tests/fixtures/eval_set.jsonl`

50 labeled examples for offline evaluation:
- 25 relevant, 20 irrelevant, 5 maybe
- Varied content: pain points, tool searches, competitor mentions, generic posts
- Each line format:
```json
{"text": "...", "author_bio": "...", "gold_label": "relevant", "author_followers": 2340, "engagement": {"likes": 5, "replies": 2, "retweets": 1}}
```
- Include edge cases: borderline confidence, ambiguous posts, non-English (should be irrelevant)

### Verify Phase B4
```bash
pytest tests/unit/test_evaluator.py -v
ruff check src/ tests/ && ruff format --check src/ tests/
mypy src/signalops --strict
```

### Commit
```
feat(eval): offline evaluation runner with classification metrics
```

---

## Final Verification (before signaling DONE)

Run the full CI suite from your worktree:

```bash
cd /c/Users/niran/OneDrive/Desktop/Syntrix/.claude/worktrees/v02-learning

# Lint + format
ruff check src/ tests/
ruff format --check src/ tests/

# Type check
mypy src/signalops --strict

# All tests (existing v0.1 + your new tests)
pytest tests/ -v --tb=short

# Verify all commits are clean
git log --oneline v02/learning ^main
```

All 4 commits should be on the `v02/learning` branch:
1. `feat(outcomes): outcome tracker for engagement polling on sent replies`
2. `feat(feedback): human correction flow with interactive review mode`
3. `feat(export): enhanced training data export with filtering and outcomes`
4. `feat(eval): offline evaluation runner with classification metrics`

**Signal DONE when all CI checks pass.**

# Terminal C — UX & Observability (v0.2)

> **Branch:** `v02/ux` | **Worktree:** `.claude/worktrees/v02-ux`
> **Role:** User-facing features — notification webhooks, enhanced stats dashboard, orchestrator integration.
> **Merge order:** C merges LAST (builds on both A and B).

---

## Context

Read PLANA.md and CLAUDE.md for full project context. You are Terminal C in a 3-terminal parallel v0.2 build.

This is NOT greenfield. The v0.1 codebase (45 source files) is complete. You are building user-facing features ON TOP of existing infrastructure. **Read each file BEFORE modifying it.**

### Cross-Terminal Dependencies

- **Terminal A** is building Redis cache, Filtered Stream, and engagement polling. You don't depend on these directly.
- **Terminal B** is building outcome tracking with an `OutcomeTracker.get_outcome_summary()` method. Your enhanced stats will eventually call this, but for now query the `Outcome` table directly (it already exists in v0.1 schema). At merge time, you can optionally use Terminal B's helper.
- The existing `pipeline/orchestrator.py` runs stages sequentially. You will add a minimal notification hook after the scoring stage.

### Design Principle

Your notification system should be a **standalone module**. The orchestrator calls into it, not the other way around. Design a single entry point: `notify_high_scores(scores, config, notifiers)`.

### Critical Rules
- `from __future__ import annotations` in all files
- `dict[str, Any]` not bare `dict` (mypy strict)
- 100-char line length (ruff)
- Do NOT modify `pyproject.toml` (Terminal A owns it)
- Do NOT modify `cli/main.py` (Terminal B owns it)
- Notification errors must NEVER crash the pipeline — log and continue
- Run CI checks after each phase

---

## File Ownership

You own these files and ONLY these files. Do not touch anything else.

```
NEW FILES:
src/signalops/notifications/base.py                 ← Notifier ABC + factory + payload
src/signalops/notifications/discord.py              ← Discord webhook notifier
src/signalops/notifications/slack.py                ← Slack webhook notifier
src/signalops/cli/notify.py                         ← Notification test/status commands
tests/unit/test_notifications.py                    ← Notifier tests
tests/unit/test_stats.py                            ← Enhanced stats tests
tests/unit/test_orchestrator_notifications.py       ← Orchestrator hook tests
tests/unit/test_notify_cli.py                       ← Notify CLI tests

MODIFIED FILES:
src/signalops/cli/stats.py                         ← Enhanced Rich dashboard
src/signalops/pipeline/orchestrator.py             ← Add notification hook after scoring
src/signalops/notifications/__init__.py            ← Module exports
```

---

## Phase C1: Notification System

### 1. NEW `src/signalops/notifications/base.py`

Notifier ABC, payload dataclass, and factory:

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

@dataclass
class NotificationPayload:
    project_name: str
    lead_count: int
    top_leads: list[dict[str, Any]]  # [{author, score, text_preview, query}]
    timestamp: str

class Notifier(ABC):
    @abstractmethod
    def send(self, title: str, message: str, fields: dict[str, str] | None = None) -> bool:
        """Send a notification. Returns True if successful."""

    @abstractmethod
    def health_check(self) -> bool:
        """Verify webhook connectivity."""

def get_notifiers(config: NotificationConfig) -> list[Notifier]:
    """Factory: build notifiers from project config.
    Returns empty list if notifications disabled."""

def notify_high_scores(
    scores: list[dict[str, Any]],
    config: ProjectConfig,
    notifiers: list[Notifier],
) -> dict[str, Any]:
    """Send notifications for scores above config threshold.
    Returns: {notified: N, failed: N, skipped: N}"""
```

Use `TYPE_CHECKING` imports for config types from `signalops.config.schema`.

### 2. NEW `src/signalops/notifications/discord.py`

`DiscordNotifier(Notifier)`:
- `__init__(webhook_url: str)`
- `send()` → POST to Discord webhook URL with embed format
  - Embed color: green (`0x00FF00`) for scores >80, yellow (`0xFFFF00`) for 70-80
  - Fields for each lead: author, score, text preview
  - Footer with timestamp
- `health_check()` → GET the webhook URL, check for 200 response
- All errors caught and logged — never raises

### 3. NEW `src/signalops/notifications/slack.py`

`SlackNotifier(Notifier)`:
- `__init__(webhook_url: str)`
- `send()` → POST to Slack incoming webhook with Block Kit format
  - Header block with title
  - Section blocks with lead info (author, score, text preview)
  - Dividers between leads
  - Context block with timestamp
- `health_check()` → POST a test payload, check for `ok` response
- All errors caught and logged — never raises

### 4. NEW `tests/unit/test_notifications.py`

Mock httpx for all tests:
- Test Discord embed formatting (correct structure, colors)
- Test Slack Block Kit formatting (correct block types)
- Test `health_check()` success and failure for both
- Test graceful error handling (webhook URL down → returns False, no exception)
- Test `get_notifiers()` factory:
  - Both Discord + Slack configured → returns 2 notifiers
  - Only Discord configured → returns 1
  - Notifications disabled → returns empty list
- Test `notify_high_scores()` with scores above/below threshold

### Verify Phase C1
```bash
pytest tests/unit/test_notifications.py -v
ruff check src/signalops/notifications/ tests/unit/test_notifications.py
mypy src/signalops/notifications/ --strict
```

### Commit
```
feat(notifications): Discord and Slack webhook notifiers
```

---

## Phase C2: Enhanced Stats Dashboard

### 5. MODIFY `src/signalops/cli/stats.py`

Read the file first. Rebuild as a comprehensive Rich dashboard matching PLANA.md Section 8 mockup.

**Pipeline Stats Panel:**
```
Collected:      1,247 tweets
Judged:         1,247 (100%)
  Relevant:       389 (31.2%)
  Irrelevant:     798 (64.0%)
  Maybe:           60 (4.8%)
Scored:           389
  Avg score:      62.4
  Score > 70:     142 (36.5%)
Drafted:          87
Approved:         64 (73.6%)
Sent:             58
```

**Outcomes Panel** (query from existing `Outcome` table):
```
Replies received: 12 (20.7%)
Likes received:   23 (39.7%)
Follows:          4 (6.9%)
Negative:         1 (1.7%)
```

**Training Data Panel:**
```
Human corrections: 34
Agreement rate:    78.2%
Last export:       2026-02-15
```

**API Usage Panel:**
```
Monthly reads:  3,420 / 10,000
Monthly writes:   287 / 3,000
```

Implementation:
- Use `Rich.Panel`, `Rich.Table`, `Rich.Columns` for layout
- Query all stats directly from DB using SQLAlchemy
- Support `--format json` for machine-readable output (dict of all stats)
- Handle empty DB gracefully (show zeros, no crashes)

### 6. NEW `tests/unit/test_stats.py`

Test with in-memory SQLite fixtures:
- Test with populated DB → correct counts and percentages
- Test with empty DB → all zeros, no crashes
- Test `--format json` output is valid JSON with expected keys
- Test outcome percentage calculations (division by zero when 0 sent)
- Test training data panel (corrections count, agreement rate)

### Verify Phase C2
```bash
pytest tests/unit/test_stats.py -v
ruff check src/ tests/ && ruff format --check src/ tests/
mypy src/signalops --strict
```

### Commit
```
feat(stats): enhanced Rich dashboard with outcomes and training data panels
```

---

## Phase C3: Orchestrator Notification Hook

### 7. MODIFY `src/signalops/pipeline/orchestrator.py`

Read the file first. Make minimal, surgical changes:

Add optional `notifiers` parameter to `__init__`:
```python
def __init__(
    self,
    db_session: Session,
    connector: Connector,
    judge: RelevanceJudge,
    draft_generator: DraftGenerator,
    notifiers: list[Notifier] | None = None,  # NEW
) -> None:
    # ... existing init ...
    self.notifiers = notifiers or []
```

Add a notification step after scoring in `run_all()`:
```python
# In the stages list, after scoring:
("Sending notifications", self._run_notify),
```

Add the notification method:
```python
def _run_notify(self, config: ProjectConfig, dry_run: bool) -> dict[str, Any]:
    """Send notifications for high-score leads. Never fails the pipeline."""
    if not self.notifiers or not config.notifications.enabled:
        return {"skipped": True, "reason": "notifications disabled"}
    try:
        from signalops.notifications.base import notify_high_scores
        # Query recent scores above threshold
        # Call notify_high_scores()
        return result
    except Exception as e:
        logger.warning("Notification failed (non-fatal): %s", e)
        return {"error": str(e)}
```

**Critical:** Notification failures must NEVER crash the pipeline. Wrap in try/except, log warning, continue.

### 8. NEW `tests/unit/test_orchestrator_notifications.py`

Test notification integration:
- Test notifications fire when scores exceed `min_score_to_notify` threshold
- Test notifications skip when `config.notifications.enabled = False`
- Test notifications skip when no notifiers provided
- Test notification failure doesn't crash pipeline (mock notifier that raises)
- Test dry_run still sends notifications (notifications are read-only, safe in dry-run)

### Verify Phase C3
```bash
pytest tests/unit/test_orchestrator_notifications.py -v
ruff check src/ tests/ && ruff format --check src/ tests/
mypy src/signalops --strict
```

### Commit
```
feat(orchestrator): notification hook after scoring for high-score leads
```

---

## Phase C4: Notification CLI

### 9. NEW `src/signalops/cli/notify.py`

Notification test and status commands:

```python
@click.group()
def notify_group() -> None:
    """Notification management commands."""

@notify_group.command("test")
@click.pass_context
def notify_test(ctx: click.Context) -> None:
    """Send a test notification to configured webhooks.

    Usage: signalops notify test --project spectra
    """
    # Load project config
    # Build notifiers from config
    # Send test payload with sample data
    # Show results (success/failure per webhook)

@notify_group.command("status")
@click.pass_context
def notify_status(ctx: click.Context) -> None:
    """Show webhook configuration and health status.

    Usage: signalops notify status --project spectra
    """
    # Load project config
    # Show: which webhooks configured (Discord URL, Slack URL)
    # Run health_check() on each
    # Display Rich table with status (healthy/unreachable)
```

**Note:** Terminal B owns `cli/main.py` modifications. To register this command group, either:
- Add registration during the merge phase, OR
- Create the group so it can be imported and registered easily:
  ```python
  # In cli/notify.py, export notify_group for registration
  ```

### 10. NEW `tests/unit/test_notify_cli.py`

Test with Click's CliRunner:
- Test `notify test` with mocked notifiers → shows success
- Test `notify test` with no webhooks configured → shows warning
- Test `notify status` displays configuration table
- Test `notify status` with unreachable webhook → shows "unreachable"

### Verify Phase C4
```bash
pytest tests/unit/test_notify_cli.py -v
ruff check src/ tests/ && ruff format --check src/ tests/
mypy src/signalops --strict
```

### Commit
```
feat(cli): notification test and status commands
```

---

## Final Verification (before signaling DONE)

Run the full CI suite from your worktree:

```bash
cd /c/Users/niran/OneDrive/Desktop/Syntrix/.claude/worktrees/v02-ux

# Lint + format
ruff check src/ tests/
ruff format --check src/ tests/

# Type check
mypy src/signalops --strict

# All tests (existing v0.1 + your new tests)
pytest tests/ -v --tb=short

# Verify all commits are clean
git log --oneline v02/ux ^main
```

All 4 commits should be on the `v02/ux` branch:
1. `feat(notifications): Discord and Slack webhook notifiers`
2. `feat(stats): enhanced Rich dashboard with outcomes and training data panels`
3. `feat(orchestrator): notification hook after scoring for high-score leads`
4. `feat(cli): notification test and status commands`

**Signal DONE when all CI checks pass.**

---

## Post-Merge Note

After all 3 branches are merged, these integrations will need wiring:
- `cli/main.py` needs `notify_group` registration (Terminal B's file — add during merge)
- `cli/stats.py` can optionally import `OutcomeTracker.get_outcome_summary()` from Terminal B's code
- `orchestrator.py` notifications are self-contained (already wired by you)

# 3-Terminal Parallel Build Plan — Syntrix v0.2

> **Strategy:** Three Claude Code instances running in isolated git worktrees, building independent v0.2 workstreams against the existing v0.1 codebase. Each terminal modifies distinct files — zero merge conflicts by design. Merge in sequence: A → B → C.

---

## Architecture: Why 3 Terminals Work for v0.2

```
                    ┌─────────────────────────────────────────────────┐
                    │          v0.1 Codebase (45 source files)         │
                    │   Shared foundation: DB schema, pipeline, CLI    │
                    └──────┬──────────────┬──────────────┬────────────┘
                           │              │              │
               ┌───────────▼──┐  ┌────────▼───────┐  ┌──▼─────────────┐
               │ TERMINAL A   │  │  TERMINAL B    │  │  TERMINAL C    │
               │ Infra +      │  │  Learning Loop │  │  UX +          │
               │ Data Layer   │  │  + Evaluation  │  │  Observability │
               │              │  │                │  │                │
               │ Worktree:    │  │ Worktree:      │  │ Worktree:      │
               │ v02/infra    │  │ v02/learning   │  │ v02/ux         │
               └──────┬───────┘  └───────┬────────┘  └──────┬─────────┘
                      │                  │                   │
                      ▼                  ▼                   ▼
               ┌──────────────────────────────────────────────────────┐
               │   MERGE ORDER: A → B → C (sequential, not parallel)  │
               │   A is foundation, B builds on it, C reads from both │
               └──────────────────────────────────────────────────────┘
```

### Why This Split?

| Terminal | Domain | New Files | Modified Files | Risk Level |
|----------|--------|-----------|----------------|------------|
| **A** | Infrastructure (Redis cache, Filtered Stream, engagement polling, multi-project) | 5 | 7 | **Medium** — touches connectors + config (foundational) |
| **B** | Learning Loop (outcome tracking, feedback, eval, export) | 8 | 3 | **Low** — mostly new files, few modifications |
| **C** | UX & Observability (notifications, enhanced stats, orchestrator hooks) | 6 | 3 | **Low** — mostly new files, isolated concerns |

**Key insight:** v0.1 was greenfield (51 new files, zero overlap). v0.2 modifies existing code, so the split is designed around **file ownership** — no two terminals touch the same file. This guarantees zero merge conflicts.

---

## Pre-Flight Setup (Run ONCE before launching terminals)

```bash
cd /c/Users/niran/OneDrive/Desktop/Syntrix

# 1. Ensure main is clean and up to date
git status                      # Should be clean
git log --oneline -5            # Verify we're on latest main

# 2. Create worktrees (NOT branches — each gets its own directory)
git worktree add .claude/worktrees/v02-infra    -b v02/infra
git worktree add .claude/worktrees/v02-learning -b v02/learning
git worktree add .claude/worktrees/v02-ux       -b v02/ux

# 3. Verify worktrees
git worktree list
# Should show:
#   /c/Users/niran/OneDrive/Desktop/Syntrix                         main
#   /c/Users/niran/OneDrive/Desktop/Syntrix/.claude/worktrees/v02-infra    v02/infra
#   /c/Users/niran/OneDrive/Desktop/Syntrix/.claude/worktrees/v02-learning v02/learning
#   /c/Users/niran/OneDrive/Desktop/Syntrix/.claude/worktrees/v02-ux       v02/ux

# 4. Install dev deps in each worktree
cd .claude/worktrees/v02-infra && pip install -e ".[dev]" && cd -
cd .claude/worktrees/v02-learning && pip install -e ".[dev]" && cd -
cd .claude/worktrees/v02-ux && pip install -e ".[dev]" && cd -
```

---

## TERMINAL A — Infrastructure & Data Layer

**Worktree:** `.claude/worktrees/v02-infra`
**Branch:** `v02/infra`
**Owns:** storage/cache.py, connectors/x_stream.py, + modifications to connectors, pipeline/collector, config, cli/project, pyproject.toml

### Prompt for Terminal A

```
cd /c/Users/niran/OneDrive/Desktop/Syntrix/.claude/worktrees/v02-infra

Read PLANA.md and CLAUDE.md for full context. You are Terminal A in a 3-terminal parallel v0.2 build.

This is NOT greenfield. The v0.1 codebase is complete. You are MODIFYING existing files and adding new ones.
Read each file BEFORE modifying it. Understand existing patterns. Match the code style.

IMPORTANT: Redis is OPTIONAL with graceful fallback. Every Redis operation must have an in-memory/no-op
fallback path. Never crash if Redis is unavailable.

YOUR SCOPE — Files you own (ONLY touch these):

## Phase A1: Redis Caching Layer
1. MODIFY src/signalops/config/schema.py — Add a RedisConfig model:
   ```python
   class RedisConfig(BaseModel):
       url: str = "redis://localhost:6379/0"
       enabled: bool = False
       search_cache_ttl: int = 1800     # 30 min
       dedup_ttl: int = 86400           # 24 hours
       rate_limit_ttl: int = 900        # 15 min
   ```
   Add `redis: RedisConfig = RedisConfig()` field to ProjectConfig.
   Also add a StreamConfig model:
   ```python
   class StreamConfig(BaseModel):
       enabled: bool = False
       rules: list[str] = []
       backfill_minutes: int = 5
   ```
   Add `stream: StreamConfig = StreamConfig()` field to ProjectConfig.

2. MODIFY pyproject.toml — Add `"redis>=5.0"` to dependencies list.

3. NEW src/signalops/storage/cache.py — Redis cache wrapper:
   - CacheBackend ABC with: get(key), set(key, value, ttl), exists(key), delete(key)
   - RedisCache(CacheBackend) — wraps redis-py, lazy connection
   - InMemoryCache(CacheBackend) — dict-based fallback with TTL via timestamps
   - get_cache(config) -> CacheBackend — factory that returns RedisCache if enabled and connectable, else InMemoryCache with a warning log
   - search_cache: cache_search_results(query, results, ttl), get_cached_search(query) -> results | None
   - dedup_cache: is_duplicate(platform, platform_id, project_id) -> bool, mark_seen(platform, platform_id, project_id, ttl)

4. NEW tests/unit/test_cache.py — Test both InMemoryCache and RedisCache (mock redis):
   - Test get/set/exists/delete for both backends
   - Test TTL expiry for InMemoryCache
   - Test graceful fallback when Redis is unavailable
   - Test search caching round-trip
   - Test dedup check logic

## Phase A2: Redis Integration with Existing Pipeline
5. MODIFY src/signalops/connectors/rate_limiter.py — Add optional Redis-backed state:
   - Add a `cache: CacheBackend | None = None` parameter to __init__
   - If cache provided, persist rate limit state (remaining tokens, window reset) to Redis
   - If no cache, behavior is identical to v0.1 (in-memory only)
   - This allows rate limit state to survive process restarts

6. MODIFY src/signalops/pipeline/collector.py — Use cache for dedup:
   - Add optional `cache: CacheBackend | None = None` parameter
   - Before DB dedup check, do a fast cache check: `cache.is_duplicate(platform, platform_id, project_id)`
   - After storing a new post, `cache.mark_seen(platform, platform_id, project_id)`
   - Cache miss → fall through to existing DB UniqueConstraint check (current behavior preserved)
   - Also add search result caching: before calling connector.search(), check `cache.get_cached_search(query)`

7. MODIFY tests/integration/test_collector.py — Add tests for cache-accelerated dedup:
   - Test collector with InMemoryCache
   - Test collector without cache (existing behavior preserved)
   - Test cache-hit skips DB query

## Phase A3: Engagement Polling (for Outcome Tracking)
8. MODIFY src/signalops/connectors/x_api.py — Add engagement polling method:
   ```python
   def get_tweet_metrics(self, tweet_ids: list[str]) -> dict[str, dict[str, int]]:
       """Fetch current engagement metrics for tweets (likes, replies, retweets, views).
       Used by outcome tracker to check if our sent replies got engagement."""
   ```
   Use X API v2 GET /2/tweets endpoint with tweet.fields=public_metrics.
   Batch up to 100 IDs per request.
   Return: {"tweet_id": {"likes": N, "retweets": N, "replies": N, "views": N}}

9. NEW tests/unit/test_engagement_polling.py — Mock X API responses, test batching, test error handling

## Phase A4: Filtered Stream (Interface + Stub)
10. NEW src/signalops/connectors/x_stream.py — Filtered Stream connector:
    - StreamConnector class with methods:
      - add_rules(rules: list[str]) -> list[str]  (rule IDs)
      - delete_rules(rule_ids: list[str]) -> None
      - stream(callback: Callable[[RawPost], None], backfill_minutes: int) -> None
    - Implementation connects to X API v2 POST /2/tweets/search/stream
    - Uses httpx streaming response
    - Parses each line as JSON, converts to RawPost, calls callback
    - Includes reconnection logic with exponential backoff
    - IMPORTANT: This requires X API Pro tier. Include a check_tier() method that verifies access.
      If not Pro tier, raise a clear error: "Filtered Stream requires X API Pro tier ($5K/month)"

11. MODIFY src/signalops/pipeline/collector.py — Add stream collection mode:
    - Add `run_stream(config, callback, duration_seconds)` method to CollectorStage
    - Instantiates StreamConnector, adds rules from config.stream.rules
    - Stores incoming posts same as search mode (dedup, normalize)
    - This is an alternative to the existing `run()` search mode

12. NEW tests/unit/test_stream.py — Test stream parsing, reconnection, rule management (mock httpx)

## Phase A5: Multi-Project Enhancements
13. MODIFY src/signalops/config/loader.py — Add multi-project helpers:
    - scan_projects(directory: str | Path) -> list[ProjectConfig] — scan projects/ dir
    - get_active_project() -> str | None — read from ~/.signalops/active_project
    - set_active_project(project_id: str) -> None — write to ~/.signalops/active_project
    - resolve_project(project_name: str | None, ctx: click.Context) -> ProjectConfig — resolve from --project flag, active project, or error

14. MODIFY src/signalops/cli/project.py — Enhance project commands:
    - `project list` — show Rich table with project name, query count, last run, active indicator
    - `project set <name>` — validate project exists, set active, show confirmation
    - `project init` — NEW interactive wizard using Rich prompts:
      - Prompt for: project_id, project_name, description, product_url
      - Prompt for queries (add multiple)
      - Prompt for ICP settings
      - Prompt for persona (name, role, tone)
      - Generate and save to projects/<project_id>.yaml
      - Validate with Pydantic before saving

15. MODIFY tests/unit/test_config.py — Add tests for new config fields (RedisConfig, StreamConfig),
    scan_projects, resolve_project

After each phase, run:
- pytest tests/unit/test_cache.py tests/unit/test_config.py -v  (Phase A1)
- pytest tests/unit/ tests/integration/test_collector.py -v      (Phase A2)
- pytest tests/unit/test_engagement_polling.py -v                (Phase A3)
- pytest tests/unit/test_stream.py -v                            (Phase A4)
- ruff check src/ tests/ && ruff format --check src/ tests/
- mypy src/signalops --strict

Commit after each phase:
- "feat(cache): Redis caching layer with in-memory fallback"
- "feat(cache): integrate Redis cache with collector dedup and rate limiter"
- "feat(connectors): engagement polling for outcome tracking"
- "feat(stream): Filtered Stream connector interface and stub"
- "feat(project): multi-project enhancements with init wizard"
```

### Terminal A File Ownership (19 files)

```
NEW FILES:
src/signalops/storage/cache.py              ← Redis/in-memory cache
src/signalops/connectors/x_stream.py        ← Filtered Stream connector
tests/unit/test_cache.py                     ← Cache tests
tests/unit/test_engagement_polling.py        ← Engagement polling tests
tests/unit/test_stream.py                    ← Stream tests

MODIFIED FILES:
src/signalops/config/schema.py              ← Add RedisConfig, StreamConfig
src/signalops/config/loader.py              ← Multi-project helpers
src/signalops/connectors/x_api.py           ← Add get_tweet_metrics()
src/signalops/connectors/rate_limiter.py    ← Optional Redis-backed state
src/signalops/pipeline/collector.py         ← Cache dedup, stream mode
src/signalops/cli/project.py               ← Project init wizard
pyproject.toml                              ← Add redis dependency
tests/unit/test_config.py                   ← New schema field tests
tests/integration/test_collector.py         ← Cache dedup tests
```

---

## TERMINAL B — Learning Loop + Evaluation

**Worktree:** `.claude/worktrees/v02-learning`
**Branch:** `v02/learning`
**Owns:** pipeline/outcome_tracker.py, training/evaluator.py, training/labeler.py, cli/correct.py, cli/eval.py, + modifications to training/exporter.py, cli/export.py, cli/main.py

### Prompt for Terminal B

```
cd /c/Users/niran/OneDrive/Desktop/Syntrix/.claude/worktrees/v02-learning

Read PLANA.md (especially Section 6 — LLM Training & Learning Roadmap) and CLAUDE.md for full context.
You are Terminal B in a 3-terminal parallel v0.2 build.

This is NOT greenfield. The v0.1 codebase is complete. You are building the learning loop ON TOP of
existing infrastructure. Read each file BEFORE modifying it.

IMPORTANT: Terminal A is simultaneously building connectors/x_api.py with a new get_tweet_metrics() method.
Your OutcomeTracker will CALL that method at runtime, but Terminal A owns that file. Use TYPE_CHECKING
imports for the connector and design OutcomeTracker to accept a callable for engagement polling:

```python
from typing import Protocol

class EngagementPoller(Protocol):
    def get_tweet_metrics(self, tweet_ids: list[str]) -> dict[str, dict[str, int]]: ...
```

This way your code compiles independently.

The DB schema ALREADY has:
- Outcome table with OutcomeType enum (REPLY_RECEIVED, LIKE_RECEIVED, FOLLOW_RECEIVED, etc.)
- Judgment.human_label, Judgment.human_corrected_at, Judgment.human_reason fields
- Draft.text_final (for edited drafts — DPO pairs)
- Draft.sent_post_id (ID of our reply on X — what we poll for engagement)

You are building the LOGIC that uses these existing schema hooks.

YOUR SCOPE — Files you own (ONLY touch these):

## Phase B1: Outcome Tracking
1. NEW src/signalops/pipeline/outcome_tracker.py — OutcomeTracker class:
   - __init__(db_session, poller: EngagementPoller)
   - track_outcomes(project_id: str) -> dict:
     - Query drafts where status=SENT and sent_post_id IS NOT NULL
     - Call poller.get_tweet_metrics() with sent_post_id values (batch)
     - For each reply, compare current metrics against previous check:
       - New likes → create Outcome(outcome_type=LIKE_RECEIVED)
       - New replies → create Outcome(outcome_type=REPLY_RECEIVED)
     - Store baseline metrics in Outcome.details JSON for delta tracking
     - Return: {tracked: N, new_likes: N, new_replies: N, new_follows: N}
   - check_for_negative(project_id: str) -> list[Outcome]:
     - Check if any sent replies resulted in blocks/reports
     - If negative outcomes detected, log warning
   - get_outcome_summary(project_id: str) -> dict:
     - Aggregate outcome stats for display

2. NEW tests/unit/test_outcome_tracker.py — Test with mocked poller:
   - Test new likes are detected (delta from previous check)
   - Test new replies are detected
   - Test negative outcome detection
   - Test no-op when no sent drafts exist
   - Test batching of tweet IDs

## Phase B2: Feedback Loop (Human Corrections)
3. NEW src/signalops/training/labeler.py — Label collection helpers:
   - correct_judgment(db_session, judgment_id: int, new_label: str, reason: str | None) -> Judgment:
     - Load judgment by ID
     - Set human_label, human_corrected_at, human_reason
     - Log to audit
     - Return updated judgment
   - get_correction_stats(db_session, project_id: str) -> dict:
     - Count: total corrections, agreement rate (human == model), by label
   - get_uncorrected_sample(db_session, project_id: str, n: int, strategy: str) -> list:
     - Strategies: "low_confidence" (judge was uncertain), "random", "recent"
     - Returns judgments for human review

4. NEW src/signalops/cli/correct.py — `correct` command:
   ```
   signalops correct <judgment_id> --label [relevant|irrelevant|maybe] --reason "..."
   ```
   - Show the original post text, model judgment, confidence
   - Apply correction via labeler.correct_judgment()
   - Show confirmation with before/after
   - Also: `signalops correct --review` interactive mode:
     - Pull N uncorrected judgments (low confidence first)
     - Show each one, prompt for label
     - Track session stats (N corrected, agreement rate)

5. MODIFY src/signalops/cli/main.py — Register new commands:
   - Import and register correct_cmd
   - Import and register eval_group
   Add at the bottom with the existing registrations:
   ```python
   from signalops.cli.correct import correct_cmd  # noqa: E402
   from signalops.cli.eval import eval_group  # noqa: E402
   cli.add_command(correct_cmd, "correct")
   cli.add_command(eval_group, "eval")
   ```

## Phase B3: Training Data Export Enhancement
6. MODIFY src/signalops/training/exporter.py — Enhance exports:
   - Add export_outcomes(project_id, output) → JSONL with outcome data for reward modeling
   - Add summary metadata to all exports: {project_id, exported_at, record_count, version}
   - Add filtering: --since DATE, --min-confidence FLOAT
   - Improve export_judgments: include post metrics (likes, followers) for richer training data
   - Improve export_draft_preferences: include outcome data (did the chosen draft get engagement?)

7. MODIFY src/signalops/cli/export.py — Enhance CLI options:
   - Add --since DATE option
   - Add --min-confidence FLOAT option
   - Add --type outcomes option
   - Add --include-metadata flag
   - Show export summary: record count, output path, file size

8. NEW tests/unit/test_exporter.py — Test export formats:
   - Test judgment JSONL format matches OpenAI fine-tuning spec
   - Test DPO format has prompt/chosen/rejected fields
   - Test outcome export format
   - Test --since filtering
   - Test --min-confidence filtering
   - Test metadata inclusion

## Phase B4: Offline Evaluation
9. NEW src/signalops/training/evaluator.py — JudgeEvaluator class (from PLANA.md Section 6):
   - __init__(judge: RelevanceJudge)
   - evaluate(test_set_path: str, project_context: dict) -> dict:
     - Load JSONL test set (each line: {text, author_bio, gold_label, ...})
     - Run judge on each example
     - Compute: precision, recall, F1 per class
     - Compute Matthews Correlation Coefficient (MCC)
     - Compute confusion matrix
     - Return full classification report + summary metrics
   - compare(test_set_path: str, judges: list[RelevanceJudge]) -> dict:
     - Run multiple judges on same test set
     - Return side-by-side comparison for model selection
   Note: Use sklearn.metrics for classification_report and matthews_corrcoef.
   Add "scikit-learn>=1.4" to [project.optional-dependencies] dev list ONLY if not already present.
   Actually — do NOT modify pyproject.toml (Terminal A owns it). Instead, use a try/except import:
   ```python
   try:
       from sklearn.metrics import classification_report, matthews_corrcoef
   except ImportError:
       raise ImportError("scikit-learn required for eval: pip install scikit-learn")
   ```

10. NEW src/signalops/cli/eval.py — `eval` command group:
    ```
    signalops eval judge --test-set <path> [--project <name>]
    signalops eval compare --test-set <path> --models "claude-sonnet-4-6,gpt-4o-mini"
    ```
    - Load test set from JSONL file
    - Instantiate judge(s) based on project config
    - Run evaluator, display Rich table with classification report
    - Show: precision, recall, F1, MCC, mean confidence, latency stats

11. NEW tests/unit/test_evaluator.py — Test evaluation logic:
    - Test with perfect predictions → all metrics 1.0
    - Test with random predictions → metrics near chance
    - Test JSONL parsing of test set
    - Test comparison between two judges
    - Test handles missing optional fields gracefully

12. NEW tests/fixtures/eval_set.jsonl — 50 labeled examples:
    - 25 relevant, 20 irrelevant, 5 maybe
    - Varied: high/low confidence, different topics, edge cases
    - Each line: {"text": "...", "author_bio": "...", "gold_label": "relevant|irrelevant|maybe",
      "author_followers": N, "engagement": {...}}

After each phase, run:
- pytest tests/unit/test_outcome_tracker.py -v     (Phase B1)
- pytest tests/unit/ -v                              (Phase B2)
- pytest tests/unit/test_exporter.py -v              (Phase B3)
- pytest tests/unit/test_evaluator.py -v             (Phase B4)
- ruff check src/ tests/ && ruff format --check src/ tests/
- mypy src/signalops --strict

Commit after each phase:
- "feat(outcomes): outcome tracker for engagement polling on sent replies"
- "feat(feedback): human correction flow with interactive review mode"
- "feat(export): enhanced training data export with filtering and outcomes"
- "feat(eval): offline evaluation runner with classification metrics"
```

### Terminal B File Ownership (16 files)

```
NEW FILES:
src/signalops/pipeline/outcome_tracker.py   ← Engagement tracking
src/signalops/training/evaluator.py         ← Offline eval runner
src/signalops/training/labeler.py           ← Label/correction helpers
src/signalops/cli/correct.py               ← correct command
src/signalops/cli/eval.py                  ← eval command group
tests/unit/test_outcome_tracker.py          ← Outcome tracker tests
tests/unit/test_evaluator.py               ← Evaluator tests
tests/unit/test_exporter.py                ← Exporter tests
tests/fixtures/eval_set.jsonl              ← 50 labeled examples

MODIFIED FILES:
src/signalops/training/exporter.py         ← Enhanced exports
src/signalops/cli/export.py               ← Enhanced CLI options
src/signalops/cli/main.py                 ← Register correct + eval commands
```

---

## TERMINAL C — UX & Observability

**Worktree:** `.claude/worktrees/v02-ux`
**Branch:** `v02/ux`
**Owns:** notifications/*, cli/stats.py enhancement, pipeline/orchestrator.py notification hook

### Prompt for Terminal C

```
cd /c/Users/niran/OneDrive/Desktop/Syntrix/.claude/worktrees/v02-ux

Read PLANA.md and CLAUDE.md for full context. You are Terminal C in a 3-terminal parallel v0.2 build.

This is NOT greenfield. The v0.1 codebase is complete. You are building user-facing features ON TOP of
existing infrastructure. Read each file BEFORE modifying it.

IMPORTANT: Terminals A and B are building features in parallel. Your notification system will eventually
be triggered by the orchestrator after scoring. Design the Notifier as a standalone module that the
orchestrator calls — a single function: `notify_high_scores(scores, config)`.

The existing orchestrator (pipeline/orchestrator.py) runs stages in sequence. You'll add a notification
step after scoring. The modification is minimal — a single method call.

Terminal B is building outcome tracking. Your enhanced stats will display outcome data from the DB.
Since you're both reading from the same Outcome table (which already exists in the v0.1 schema),
there's no conflict — you just query it.

YOUR SCOPE — Files you own (ONLY touch these):

## Phase C1: Notification System
1. NEW src/signalops/notifications/base.py — Notifier ABC:
   ```python
   class Notifier(ABC):
       @abstractmethod
       def send(self, title: str, message: str, fields: dict[str, str] | None = None) -> bool:
           """Send a notification. Returns True if successful."""

       @abstractmethod
       def health_check(self) -> bool:
           """Verify webhook connectivity."""
   ```
   Also: NotificationPayload dataclass:
   ```python
   @dataclass
   class NotificationPayload:
       project_name: str
       lead_count: int
       top_leads: list[dict]  # [{author, score, text_preview, query}]
       timestamp: str
   ```
   And a factory: get_notifiers(config: NotificationConfig) -> list[Notifier]

2. NEW src/signalops/notifications/discord.py — DiscordNotifier(Notifier):
   - __init__(webhook_url: str)
   - send() → POST to Discord webhook with embed format
   - Format: embed with title, color (green for scores >80, yellow for 70-80), fields for each lead
   - health_check() → send a ping/test message
   - Handle errors gracefully (log warning, don't crash pipeline)

3. NEW src/signalops/notifications/slack.py — SlackNotifier(Notifier):
   - __init__(webhook_url: str)
   - send() → POST to Slack incoming webhook with Block Kit format
   - Format: section blocks with lead info, dividers between leads
   - health_check() → verify webhook URL responds
   - Handle errors gracefully

4. NEW tests/unit/test_notifications.py — Test both notifiers (mock httpx):
   - Test Discord embed formatting
   - Test Slack Block Kit formatting
   - Test health_check success/failure
   - Test graceful error handling (webhook down → warning, not crash)
   - Test get_notifiers factory with both/one/none configured

## Phase C2: Enhanced Stats Dashboard
5. MODIFY src/signalops/cli/stats.py — Rebuild as comprehensive Rich dashboard:
   Current stats.py shows basic counts. Enhance to match PLANA.md Section 8 mockup:

   Pipeline Stats Panel:
   - Collected: N tweets
   - Judged: N (100%)
     - Relevant: N (X%)
     - Irrelevant: N (X%)
     - Maybe: N (X%)
   - Scored: N
     - Avg score: X
     - Score > 70: N (X%)
   - Drafted: N
   - Approved: N (X%)
   - Sent: N

   Outcomes Panel (reads from existing Outcome table):
   - Replies received: N (X%)
   - Likes received: N (X%)
   - Follows: N (X%)
   - Negative: N (X%)

   Training Data Panel:
   - Human corrections: N
   - Agreement rate: X%
   - Last export: DATE

   API Usage Panel:
   - Monthly reads: N / 10,000
   - Monthly writes: N / 3,000

   Use Rich Panels, Tables, and Columns for a polished layout.
   Support --format json for machine-readable output.

6. NEW tests/unit/test_stats.py — Test stats queries and formatting:
   - Test with populated DB → correct counts
   - Test with empty DB → zeros, no crashes
   - Test --format json output structure
   - Test outcome percentages calculated correctly

## Phase C3: Orchestrator Notification Hook
7. MODIFY src/signalops/pipeline/orchestrator.py — Add notification after scoring:
   - Add optional `notifiers: list[Notifier] | None = None` parameter to __init__
   - After _run_score() completes, if notifiers configured and scores exist:
     ```python
     def _notify_high_scores(self, config: ProjectConfig, score_results: dict) -> None:
         if not self.notifiers or not config.notifications.enabled:
             return
         # Query scores above threshold from DB
         # Build NotificationPayload
         # Send to each notifier
     ```
   - Add "Sending notifications" as a new stage in the Progress display
   - Handle notification errors gracefully (log, don't fail pipeline)

8. NEW tests/unit/test_orchestrator_notifications.py — Test notification integration:
   - Test notifications fire when scores exceed threshold
   - Test notifications skip when disabled
   - Test notification failure doesn't crash pipeline

## Phase C4: Notification CLI
9. NEW src/signalops/cli/notify.py — Notification test commands:
   ```
   signalops notify test --project <name>
   signalops notify status --project <name>
   ```
   - `notify test` — send a test notification to configured webhooks
   - `notify status` — show which webhooks are configured and their health

10. NEW tests/unit/test_notify_cli.py — CLI tests with Click CliRunner

After each phase, run:
- pytest tests/unit/test_notifications.py -v             (Phase C1)
- pytest tests/unit/test_stats.py -v                      (Phase C2)
- pytest tests/unit/test_orchestrator_notifications.py -v (Phase C3)
- ruff check src/ tests/ && ruff format --check src/ tests/
- mypy src/signalops --strict

Commit after each phase:
- "feat(notifications): Discord and Slack webhook notifiers"
- "feat(stats): enhanced Rich dashboard with outcomes and training data panels"
- "feat(orchestrator): notification hook after scoring for high-score leads"
- "feat(cli): notification test and status commands"
```

### Terminal C File Ownership (14 files)

```
NEW FILES:
src/signalops/notifications/base.py                 ← Notifier ABC + factory
src/signalops/notifications/discord.py              ← Discord webhook
src/signalops/notifications/slack.py                ← Slack webhook
src/signalops/cli/notify.py                         ← Notify commands
tests/unit/test_notifications.py                    ← Notifier tests
tests/unit/test_stats.py                            ← Stats tests
tests/unit/test_orchestrator_notifications.py       ← Orchestrator hook tests
tests/unit/test_notify_cli.py                       ← Notify CLI tests

MODIFIED FILES:
src/signalops/cli/stats.py                         ← Enhanced Rich dashboard
src/signalops/pipeline/orchestrator.py             ← Notification hook
src/signalops/notifications/__init__.py            ← Exports
```

---

## File Conflict Matrix

Zero conflicts by design. Every file is owned by exactly one terminal:

| File | Terminal A | Terminal B | Terminal C |
|------|:---------:|:---------:|:---------:|
| `storage/cache.py` | **OWN** | | |
| `connectors/x_stream.py` | **OWN** | | |
| `connectors/x_api.py` | **MOD** | | |
| `connectors/rate_limiter.py` | **MOD** | | |
| `pipeline/collector.py` | **MOD** | | |
| `config/schema.py` | **MOD** | | |
| `config/loader.py` | **MOD** | | |
| `cli/project.py` | **MOD** | | |
| `pyproject.toml` | **MOD** | | |
| `pipeline/outcome_tracker.py` | | **OWN** | |
| `training/evaluator.py` | | **OWN** | |
| `training/labeler.py` | | **OWN** | |
| `cli/correct.py` | | **OWN** | |
| `cli/eval.py` | | **OWN** | |
| `training/exporter.py` | | **MOD** | |
| `cli/export.py` | | **MOD** | |
| `cli/main.py` | | **MOD** | |
| `notifications/base.py` | | | **OWN** |
| `notifications/discord.py` | | | **OWN** |
| `notifications/slack.py` | | | **OWN** |
| `cli/notify.py` | | | **OWN** |
| `cli/stats.py` | | | **MOD** |
| `pipeline/orchestrator.py` | | | **MOD** |

---

## Sync Points & Merge Strategy

### Timeline (estimated)

```
TIME    TERMINAL A              TERMINAL B              TERMINAL C
─────── ─────────────────────── ─────────────────────── ───────────────────────
 0:00   A1: Redis Cache Layer   B1: Outcome Tracker     C1: Notification System
        (schema, cache.py,      (outcome_tracker.py,    (base, discord, slack,
         tests)                  tests)                  tests)

 0:30   A2: Cache Integration   B2: Feedback Loop       C2: Enhanced Stats
        (rate_limiter,           (labeler, correct,      (stats.py rebuild,
         collector, tests)       main.py, tests)         tests)

 1:00   A3: Engagement Polling  B3: Export Enhancement  C3: Orchestrator Hook
        (x_api.py,              (exporter, export CLI,  (orchestrator.py,
         tests)                  tests)                  tests)

 1:30   A4: Filtered Stream     B4: Offline Eval        C4: Notify CLI
        (x_stream.py,           (evaluator, eval CLI,   (notify.py,
         collector, tests)       eval_set.jsonl, tests)  tests)

 2:00   A5: Multi-Project       ✓ B DONE                ✓ C DONE
        (loader, project CLI)

 2:15   ✓ A DONE

═══════ SYNC POINT: MERGE ═══════════════════════════════════════════════════

 2:30   MERGE (sequential, from any terminal):
        1. git checkout main
        2. git merge v02/infra       (A — infrastructure first)
        3. git merge v02/learning    (B — builds on A's engagement polling)
        4. git merge v02/ux          (C — builds on both)
        5. pip install -e ".[dev]"
        6. Fix any import wiring between modules
        7. Run full CI: ruff + mypy + pytest
        8. Final commit: "feat: v0.2 — learning loop, caching, notifications"

 3:00   INTEGRATION TESTING:
        - Test outcome tracker with real engagement polling method
        - Test notification hook fires from orchestrator
        - Test stats shows all new data sections
        - Test Redis fallback path
        - Test eval command end-to-end
```

### Merge Commands (run from main worktree after all 3 are done)

```bash
# Step 1: Return to main working directory
cd /c/Users/niran/OneDrive/Desktop/Syntrix

# Step 2: Merge in sequence (order matters!)
git merge v02/infra    -m "merge: Terminal A — infrastructure (Redis, stream, multi-project)"
git merge v02/learning -m "merge: Terminal B — learning loop (outcomes, feedback, eval)"
git merge v02/ux       -m "merge: Terminal C — UX (notifications, stats, orchestrator hooks)"

# Step 3: Install with new dependencies
pip install -e ".[dev]"

# Step 4: Run full CI
ruff check src/ tests/
ruff format --check src/ tests/
mypy src/signalops --strict
pytest tests/ -v --tb=short

# Step 5: Integration wiring (may need manual fixes)
# - Ensure outcome_tracker imports get_tweet_metrics from x_api.py
# - Ensure orchestrator imports get_notifiers from notifications
# - Ensure cli/main.py has all command registrations
# - Ensure pyproject.toml has all new dependencies

# Step 6: Smoke test
signalops --help
signalops project list
signalops stats --project spectra
signalops eval judge --test-set tests/fixtures/eval_set.jsonl --project spectra --dry-run
signalops notify test --project spectra --dry-run
signalops correct --review --project spectra --dry-run

# Step 7: Clean up worktrees
git worktree remove .claude/worktrees/v02-infra
git worktree remove .claude/worktrees/v02-learning
git worktree remove .claude/worktrees/v02-ux
```

---

## Integration Points (Post-Merge Wiring)

These connections between terminals need to be verified/wired during merge:

| Connection | From (Terminal) | To (Terminal) | Integration |
|-----------|----------------|---------------|-------------|
| Outcome tracker calls engagement polling | B: `outcome_tracker.py` | A: `x_api.py::get_tweet_metrics()` | Replace Protocol with direct import |
| Orchestrator triggers notifications | C: `orchestrator.py` | C: `notifications/base.py` | Already wired by Terminal C |
| Stats shows outcomes | C: `stats.py` | B: `outcome_tracker.py::get_outcome_summary()` | Import and call in stats |
| Cache used by collector | A: `collector.py` | A: `cache.py` | Already wired by Terminal A |
| Correct command uses labeler | B: `cli/correct.py` | B: `training/labeler.py` | Already wired by Terminal B |
| Eval uses judge model | B: `cli/eval.py` | Existing: `models/judge_model.py` | Already exists in v0.1 |

### Integration Fix-Up Checklist

After merging all 3 branches, verify these imports compile:

```python
# 1. Outcome tracker → engagement polling (B → A)
from signalops.connectors.x_api import XConnector
tracker = OutcomeTracker(db_session, connector)  # connector has get_tweet_metrics

# 2. Stats → outcome summary (C → B)
from signalops.pipeline.outcome_tracker import OutcomeTracker
summary = tracker.get_outcome_summary(project_id)

# 3. Orchestrator → notifiers (C internal)
from signalops.notifications.base import get_notifiers
notifiers = get_notifiers(config.notifications)

# 4. CLI main → all new commands (B's changes to main.py)
from signalops.cli.correct import correct_cmd
from signalops.cli.eval import eval_group
```

---

## Conflict Prevention Rules

| Rule | Why |
|------|-----|
| **Each terminal only writes to its owned files** (listed above) | No two terminals touch the same file |
| **Terminal B owns cli/main.py modifications** | Only B adds new command registrations |
| **Terminal A owns pyproject.toml** | Only A adds new dependencies (redis) |
| **Terminal C owns pipeline/orchestrator.py** | Only C modifies the orchestrator |
| **TYPE_CHECKING imports for cross-terminal types** | No runtime import errors during parallel dev |
| **Protocol classes for cross-terminal interfaces** | B's EngagementPoller, C's Notifier — compile independently |
| **Each terminal runs its own tests only** | No test file conflicts |

### If You DO Hit a Conflict

The only likely conflicts are in `__init__.py` files (each terminal may add exports). Resolution is always "keep both sides":

```python
# Terminal A added:
from signalops.storage.cache import CacheBackend, get_cache
# Terminal B added:
from signalops.training.evaluator import JudgeEvaluator
# MERGED — keep both:
from signalops.storage.cache import CacheBackend, get_cache
from signalops.training.evaluator import JudgeEvaluator
```

---

## Verification Checklist (Post-Merge)

Run these after merging all 3 branches:

```bash
# 1. All tests pass
pytest tests/ -v --tb=short --cov=signalops

# 2. Lint clean
ruff check src/ tests/
ruff format --check src/ tests/

# 3. Type check
mypy src/signalops --strict

# 4. CLI works — existing commands still function
signalops --help
signalops project list
signalops project set spectra
signalops run all --project spectra --dry-run

# 5. New v0.2 commands work
signalops correct --review --project spectra
signalops eval judge --test-set tests/fixtures/eval_set.jsonl --project spectra
signalops export training-data --project spectra --type judgments --since 2026-01-01
signalops export training-data --project spectra --type outcomes
signalops notify test --project spectra
signalops notify status --project spectra

# 6. Enhanced stats
signalops stats --project spectra
signalops stats --project spectra --format json

# 7. Project init wizard
signalops project init

# 8. Redis fallback (with Redis NOT running)
signalops run collect --project spectra --dry-run
# Should work fine with "Redis unavailable, using in-memory cache" warning
```

### Expected Test Count

| Terminal | Unit Tests | Integration Tests | Total |
|----------|-----------|-------------------|-------|
| A | ~15 | ~5 | ~20 |
| B | ~25 | ~0 | ~25 |
| C | ~15 | ~0 | ~15 |
| Existing v0.1 | ~40 | ~15 | ~55 |
| **Total** | **~95** | **~20** | **~115** |

---

## Quick Reference: Terminal Launch Commands

### Pre-Flight (run once)
```bash
cd /c/Users/niran/OneDrive/Desktop/Syntrix
git worktree add .claude/worktrees/v02-infra    -b v02/infra
git worktree add .claude/worktrees/v02-learning -b v02/learning
git worktree add .claude/worktrees/v02-ux       -b v02/ux
```

### Terminal A
```bash
cd /c/Users/niran/OneDrive/Desktop/Syntrix/.claude/worktrees/v02-infra && claude
```
Then paste the Terminal A prompt.

### Terminal B
```bash
cd /c/Users/niran/OneDrive/Desktop/Syntrix/.claude/worktrees/v02-learning && claude
```
Then paste the Terminal B prompt.

### Terminal C
```bash
cd /c/Users/niran/OneDrive/Desktop/Syntrix/.claude/worktrees/v02-ux && claude
```
Then paste the Terminal C prompt.

### Merge Terminal (after all 3 complete)
```bash
cd /c/Users/niran/OneDrive/Desktop/Syntrix && claude
```
Then paste: "Merge v02/infra, v02/learning, v02/ux into main. Fix any import wiring between modules. Run full CI. Make everything work together. See PLANB_3TERMINAL.md for the integration checklist."

---

## Appendix: v0.2 Dependency Changes

Only Terminal A modifies `pyproject.toml`. The full diff:

```diff
 dependencies = [
     "click>=8.1",
     "rich>=13.0",
     "pydantic>=2.0",
     "pyyaml>=6.0",
     "sqlalchemy>=2.0",
     "alembic>=1.13",
     "httpx>=0.27",
     "anthropic>=0.40",
     "openai>=1.50",
     "python-dotenv>=1.0",
+    "redis>=5.0",
 ]

 [project.optional-dependencies]
 dev = [
     "pytest>=8.0",
     "pytest-cov>=5.0",
     "pytest-asyncio>=0.23",
     "mypy>=1.11",
     "ruff>=0.6",
     "respx>=0.21",
     "types-PyYAML>=6.0",
+    "scikit-learn>=1.4",
 ]
```

## Appendix: File Count Summary

| Category | Terminal A | Terminal B | Terminal C | Total |
|----------|-----------|-----------|-----------|-------|
| New source files | 2 | 5 | 4 | 11 |
| Modified source files | 7 | 3 | 3 | 13 |
| New test files | 3 | 4 | 4 | 11 |
| Modified test files | 2 | 0 | 0 | 2 |
| New fixture files | 0 | 1 | 0 | 1 |
| **Total touched** | **14** | **13** | **11** | **38** |

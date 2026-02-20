# 3-Terminal Parallel Build Plan — Syntrix v0.1 MVP

> **Strategy:** Three Claude Code terminals running simultaneously on isolated git branches, building independent workstreams against shared interfaces defined in PLANA.md. Merge in sequence at sync points.

---

## Architecture: Why 3 Terminals Work

```
                    ┌─────────────────────────────────────────────┐
                    │           PLANA.md (shared contract)         │
                    │  Interfaces, schemas, data models defined    │
                    └──────┬──────────────┬──────────────┬────────┘
                           │              │              │
               ┌───────────▼──┐  ┌────────▼───────┐  ┌──▼────────────┐
               │ TERMINAL A   │  │  TERMINAL B    │  │  TERMINAL C   │
               │ Foundation + │  │  Intelligence  │  │  CLI + Orch.  │
               │ Data Pipeline│  │  Layer         │  │  + Integration│
               │              │  │                │  │               │
               │ Branch:      │  │ Branch:        │  │ Branch:       │
               │ feat/data    │  │ feat/intel     │  │ feat/cli      │
               └──────┬───────┘  └───────┬────────┘  └──────┬────────┘
                      │                  │                   │
                      ▼                  ▼                   ▼
               ┌──────────────────────────────────────────────────┐
               │        SYNC POINT → Merge to main               │
               │        Final integration + E2E tests             │
               └──────────────────────────────────────────────────┘
```

### Why This Split?

| Terminal | Domain | Files | Dependency Level |
|----------|--------|-------|------------------|
| **A** | Data in/out (config, storage, connectors, collect, normalize) | 19 files | **None** — builds the foundation |
| **B** | AI processing (LLM gateway, providers, judge, score, draft) | 14 files | **Interface-only** — imports ABCs from A |
| **C** | User-facing (CLI commands, orchestrator, sender, integration) | 14 files | **Interface-only** — imports ABCs from A+B |

The key insight: PLANA.md already defines every interface contract (Connector ABC, RelevanceJudge ABC, DraftGenerator ABC, PipelineStage ABC). Each terminal builds against these contracts independently. Integration conflicts are minimal because each terminal owns distinct files.

---

## Pre-Flight Setup (Run ONCE before launching terminals)

Open one terminal and run:

```bash
# 1. Create the full directory skeleton so all 3 terminals can work without conflicts
cd /c/Users/niran/OneDrive/Desktop/Syntrix

mkdir -p src/signalops/{cli,connectors,pipeline,models/providers,storage/migrations,config,training,notifications}
mkdir -p tests/{unit,integration,fixtures}
mkdir -p projects
mkdir -p .github/workflows

# 2. Create all __init__.py files
touch src/signalops/__init__.py
touch src/signalops/cli/__init__.py
touch src/signalops/connectors/__init__.py
touch src/signalops/pipeline/__init__.py
touch src/signalops/models/__init__.py
touch src/signalops/models/providers/__init__.py
touch src/signalops/storage/__init__.py
touch src/signalops/config/__init__.py
touch src/signalops/training/__init__.py
touch src/signalops/notifications/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py

# 3. Create pyproject.toml (shared dependency file)
cat > pyproject.toml << 'PYPROJECT'
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "signalops"
version = "0.1.0"
description = "Agentic social lead finder + outreach workbench"
requires-python = ">=3.11"
license = {text = "MIT"}
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
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "pytest-asyncio>=0.23",
    "mypy>=1.11",
    "ruff>=0.6",
    "respx>=0.21",
]

[project.scripts]
signalops = "signalops.cli.main:cli"

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
PYPROJECT

# 4. Install in dev mode
pip install -e ".[dev]"

# 5. Commit skeleton
git add -A
git commit -m "chore: project skeleton — directory structure, pyproject.toml, __init__.py files"

# 6. Create 3 working branches
git branch feat/data
git branch feat/intel
git branch feat/cli
```

---

## TERMINAL A — Foundation + Data Pipeline

**Branch:** `feat/data`
**Owns:** config/, storage/, connectors/, pipeline/collector.py, pipeline/normalizer.py, tests/fixtures/, projects/
**Claude Code Prompt:**

```
Open a NEW Claude Code terminal and paste this prompt:
```

### Prompt for Terminal A

```
git checkout feat/data

Read PLANA.md for full context. You are Terminal A in a 3-terminal parallel build.

YOUR SCOPE — Build these files in order. Do NOT touch any files outside your scope:

## Phase A1: Config System (do first — other terminals depend on these types)
1. src/signalops/config/schema.py — All Pydantic models (ProjectConfig, QueryConfig, ICPConfig, RelevanceRubric, ScoringWeights, PersonaConfig, TemplateConfig, NotificationConfig) exactly as specified in PLANA.md Section 5
2. src/signalops/config/loader.py — YAML loader with env var resolution, config_hash function
3. src/signalops/config/defaults.py — Default values and constants
4. projects/spectra.yaml — Example config from PLANA.md
5. projects/salesense.yaml — Example config from PLANA.md
6. tests/unit/test_config.py — Test loading both YAML files, env var resolution, invalid configs, schema validation

## Phase A2: Storage Layer
7. src/signalops/storage/database.py — ALL SQLAlchemy models (Project, RawPost, NormalizedPost, Judgment, Score, Draft, Outcome, AuditLog) with enums, exactly as in PLANA.md Section 4. Include a get_engine() and get_session() factory.
8. src/signalops/storage/audit.py — Append-only audit logger: log_action(session, project_id, action, entity_type, entity_id, details, user)
9. tests/conftest.py — Shared fixtures: in-memory SQLite engine, session fixture, sample ProjectConfig fixture, sample RawPost data fixture

## Phase A3: Connectors
10. src/signalops/connectors/base.py — Connector ABC + RawPost dataclass exactly as PLANA.md Section 3
11. src/signalops/connectors/rate_limiter.py — Sliding window rate limiter with: acquire() -> wait_seconds, update_from_headers(headers), jitter support, configurable window
12. src/signalops/connectors/x_auth.py — OAuth 2.0 PKCE flow: generate_pkce_pair(), build_auth_url(), exchange_code(), refresh_token(), store/load tokens from ~/.signalops/credentials.json
13. src/signalops/connectors/x_api.py — XConnector(Connector) implementation: search() using httpx to X API v2 /2/tweets/search/recent, get_user(), post_reply(), health_check(). Use rate_limiter internally. Parse X API v2 response format into RawPost objects.
14. tests/unit/test_rate_limiter.py — Test within-limit, over-limit blocking, header updates, jitter range
15. tests/fixtures/tweets.json — 20 realistic X API v2 tweet response payloads with varied: engagement levels, languages, reply chains, author profiles

## Phase A4: Collection + Normalization Pipeline
16. src/signalops/pipeline/collector.py — CollectorStage: takes queries from config, calls connector.search() for each, stores RawPost rows, deduplicates by (platform, platform_id, project_id), tracks since_id per query for incremental collection
17. src/signalops/pipeline/normalizer.py — NormalizerStage: strip URLs, collapse whitespace, extract hashtags/mentions/urls into JSON fields, detect language (use simple heuristic or langdetect), populate NormalizedPost from RawPost
18. tests/unit/test_normalizer.py — URL stripping, whitespace collapsing, entity extraction, language detection
19. tests/integration/test_collector.py — Mock httpx responses with respx, test collector stores to DB, test dedup

After each phase, run pytest on your new tests to verify. Commit after each phase:
- "feat(config): config system with Pydantic schemas and YAML loader"
- "feat(storage): SQLAlchemy models, audit logger, and test fixtures"
- "feat(connectors): X API v2 connector, OAuth 2.0 PKCE, rate limiter"
- "feat(pipeline): collector and normalizer stages with tests"

Use the Task tool to run tests in background while you continue coding.
Use parallel tool calls whenever reading/writing independent files.
Be thorough — these are the foundation types everything else imports.
```

### Terminal A File Ownership (19 files)

```
src/signalops/config/schema.py          ← Pydantic models
src/signalops/config/loader.py          ← YAML loader
src/signalops/config/defaults.py        ← Defaults
src/signalops/storage/database.py       ← SQLAlchemy models
src/signalops/storage/audit.py          ← Audit logger
src/signalops/connectors/base.py        ← Connector ABC + RawPost
src/signalops/connectors/rate_limiter.py
src/signalops/connectors/x_auth.py
src/signalops/connectors/x_api.py
src/signalops/pipeline/collector.py
src/signalops/pipeline/normalizer.py
projects/spectra.yaml
projects/salesense.yaml
.env.example
tests/conftest.py
tests/unit/test_config.py
tests/unit/test_rate_limiter.py
tests/unit/test_normalizer.py
tests/integration/test_collector.py
tests/fixtures/tweets.json
```

---

## TERMINAL B — Intelligence Layer

**Branch:** `feat/intel`
**Owns:** models/, pipeline/judge.py, pipeline/scorer.py, pipeline/drafter.py
**Claude Code Prompt:**

### Prompt for Terminal B

```
git checkout feat/intel

Read PLANA.md for full context. You are Terminal B in a 3-terminal parallel build.

IMPORTANT: Terminal A is building config/schema.py, storage/database.py, and connectors/base.py
on a parallel branch at the same time. You will import types from those modules. For now,
create minimal LOCAL stub versions of the types you need at the top of your files using
TYPE_CHECKING imports so your code is self-contained. When we merge, the real implementations
will replace the stubs.

Use this pattern at the top of files that need shared types:
```python
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from signalops.config.schema import ProjectConfig, RelevanceRubric, ScoringWeights, PersonaConfig
    from signalops.storage.database import NormalizedPost, Judgment as JudgmentRow, Score as ScoreRow, Draft as DraftRow
```

YOUR SCOPE — Build these files in order:

## Phase B1: LLM Infrastructure
1. src/signalops/models/providers/base.py — LLMProvider ABC with methods: complete(system_prompt, user_prompt, temperature, max_tokens) -> str, complete_json(system_prompt, user_prompt, response_schema) -> dict. Include a ProviderConfig dataclass.
2. src/signalops/models/providers/anthropic.py — AnthropicProvider(LLMProvider): uses the anthropic SDK, supports claude-sonnet-4-6/claude-haiku-4-5, implements structured JSON output via tool_use or json mode
3. src/signalops/models/providers/openai.py — OpenAIProvider(LLMProvider): uses the openai SDK, supports gpt-4o/gpt-4o-mini, implements structured JSON output via response_format
4. src/signalops/models/llm_gateway.py — LLMGateway class: routes to providers based on model name prefix ("claude-" -> Anthropic, "gpt-" -> OpenAI), handles retries with exponential backoff (3 attempts), circuit breaker (5 failures -> open for 60s), tracks latency, falls back to fallback classifier on total failure

## Phase B2: Judge System
5. src/signalops/models/judge_model.py — Judgment dataclass + RelevanceJudge ABC (from PLANA.md Section 3). Then implement:
   - LLMPromptJudge(RelevanceJudge): builds the judge prompt from PLANA.md Appendix C, parses structured JSON response, handles malformed JSON gracefully
   - KeywordFallbackJudge(RelevanceJudge): rule-based using keywords_required + keywords_excluded from config
6. src/signalops/models/fallback.py — TF-IDF keyword classifier: train_from_examples(texts, labels), predict(text) -> (label, confidence). Use sklearn TfidfVectorizer + LogisticRegression. Serialize/load model with joblib.
7. src/signalops/pipeline/judge.py — JudgeStage(PipelineStage): takes NormalizedPosts, runs through judge, applies keyword exclusion rules FIRST (cheap filter), then LLM judge on remaining, stores Judgment rows. Supports batch judging.
8. tests/unit/test_judge.py — Test structured JSON parsing, malformed JSON fallback, keyword exclusion auto-reject, confidence thresholds, batch judging

## Phase B3: Scoring Engine
9. src/signalops/pipeline/scorer.py — ScorerStage: implements the weighted scoring formula from PLANA.md Section 5. Components:
   - relevance_judgment: confidence * (1.0 if relevant, 0.3 if maybe, 0.0 if irrelevant)
   - author_authority: normalized(followers, verified, bio_match against ICP prefer_bios)
   - engagement_signals: normalized(likes, replies, retweets, views)
   - recency: decay function (1.0 at 0h, 0.5 at 24h, 0.1 at 72h)
   - intent_strength: detect questions, "looking for", "anyone recommend" patterns
   Each component 0-100, then weighted sum. Store Score row with component breakdown.
10. tests/unit/test_scorer.py — Perfect score, zero followers, weights sum to 1.0, recency decay, intent detection

## Phase B4: Draft Generator
11. src/signalops/models/draft_model.py — Draft dataclass + DraftGenerator ABC (from PLANA.md). Then implement:
    - LLMDraftGenerator(DraftGenerator): builds draft prompt from PLANA.md Appendix C, enforces 240 char limit (re-generate if over), uses persona config
12. src/signalops/pipeline/drafter.py — DrafterStage: takes scored posts above threshold (configurable, default 50), generates drafts, stores Draft rows with status=PENDING
13. tests/unit/test_drafter.py — Character limit enforcement, persona injection, template selection
14. tests/fixtures/eval_set.jsonl — 50 labeled examples (25 relevant, 20 irrelevant, 5 maybe) for offline eval testing

After each phase, run pytest on your tests. Commit after each phase:
- "feat(models): LLM gateway with Anthropic/OpenAI providers and circuit breaker"
- "feat(judge): relevance judge with LLM + keyword fallback"
- "feat(scorer): weighted lead scoring engine"
- "feat(drafter): LLM draft generator with persona system"

Use the Task tool to run tests in background while you continue coding.
For LLM provider files, mock the actual API calls — use respx or unittest.mock.
```

### Terminal B File Ownership (14 files)

```
src/signalops/models/providers/base.py      ← LLMProvider ABC
src/signalops/models/providers/anthropic.py  ← Claude provider
src/signalops/models/providers/openai.py     ← OpenAI provider
src/signalops/models/llm_gateway.py          ← Router + circuit breaker
src/signalops/models/judge_model.py          ← Judge interface + impls
src/signalops/models/fallback.py             ← TF-IDF fallback
src/signalops/models/draft_model.py          ← Draft interface + impls
src/signalops/pipeline/judge.py              ← Judge stage
src/signalops/pipeline/scorer.py             ← Scorer stage
src/signalops/pipeline/drafter.py            ← Drafter stage
tests/unit/test_judge.py
tests/unit/test_scorer.py
tests/unit/test_drafter.py
tests/fixtures/eval_set.jsonl
```

---

## TERMINAL C — CLI + Orchestration + Integration

**Branch:** `feat/cli`
**Owns:** cli/, pipeline/orchestrator.py, pipeline/sender.py, training/, notifications/, .github/
**Claude Code Prompt:**

### Prompt for Terminal C

```
git checkout feat/cli

Read PLANA.md for full context. You are Terminal C in a 3-terminal parallel build.

IMPORTANT: Terminals A and B are building the pipeline stages and models in parallel.
Your CLI commands will CALL those stages. Use TYPE_CHECKING imports for types from other
modules, and structure your CLI commands so they import pipeline stages lazily (inside
the Click command functions, not at module top level). This prevents import errors during
parallel development.

Pattern for lazy imports in CLI commands:
```python
@cli.command()
def collect():
    from signalops.pipeline.collector import CollectorStage
    from signalops.connectors.x_api import XConnector
    # ... use them here
```

YOUR SCOPE — Build these files in order:

## Phase C1: CLI Skeleton + Project Management
1. src/signalops/cli/main.py — Click group app with global options: --project/-p, --dry-run, --verbose/-v, --format [table|json]. Set up Rich console for pretty output. Load .env with python-dotenv on startup.
2. src/signalops/cli/project.py — Commands: `project set <name>` (store active project in ~/.signalops/active_project), `project list` (scan projects/ dir), `project init` (interactive wizard that creates a new project.yaml with prompts for each field using Rich prompts)
3. src/signalops/cli/stats.py — `stats` command: query DB for counts of raw_posts, normalized_posts, judgments (by label), scores (avg, >70 count), drafts (by status), outcomes (by type). Display as Rich table matching the mockup in PLANA.md Section 8.

## Phase C2: Pipeline CLI Commands
4. src/signalops/cli/collect.py — `run collect` command: loads project config, instantiates connector, runs CollectorStage, displays Rich progress bar and summary table
5. src/signalops/cli/judge.py — `run judge` command: loads unjudged normalized posts, runs JudgeStage, displays results breakdown
6. src/signalops/cli/score.py — `run score` command: loads judged-relevant posts without scores, runs ScorerStage, displays top-N table
7. src/signalops/cli/draft.py — `run draft` command: takes --top N flag (default 10), loads top-scored un-drafted posts, runs DrafterStage, displays drafts

## Phase C3: Approval Queue + Send
8. src/signalops/cli/approve.py — Queue commands:
   - `queue list` — show pending drafts as Rich table (ID, score, author, draft preview, status)
   - `queue approve <id>` — mark draft as APPROVED
   - `queue edit <id>` — open text in $EDITOR or Rich prompt, then mark as EDITED
   - `queue reject <id>` — mark as REJECTED with optional reason
9. src/signalops/pipeline/sender.py — SenderStage: takes approved drafts, calls connector.post_reply(), updates draft status to SENT with sent_post_id, enforces rate limits (max_replies_per_hour, max_replies_per_day from config), respects --dry-run, logs every action to audit
10. src/signalops/cli/send.py — `queue send` command: requires --confirm flag (or shows preview in dry-run), runs SenderStage, displays results
11. src/signalops/cli/export.py — `export training-data` command with --type [judgments|drafts] and --format [openai|dpo]

## Phase C4: Orchestrator + Integration
12. src/signalops/pipeline/orchestrator.py — PipelineOrchestrator: `run_all(config, dry_run)` that executes collect → normalize → judge → score → draft in sequence. Handles errors at each stage (log and continue). Displays Rich progress for each stage. Supports `signalops run all` command.
13. src/signalops/training/exporter.py — TrainingDataExporter from PLANA.md Section 6: export_judgments() and export_draft_preferences()
14. tests/test_cli.py — Click CliRunner tests: test each command with mocked pipeline stages, test --dry-run flag, test --format json output, test project set/list
15. tests/integration/test_pipeline.py — End-to-end test: mock X API → collect → normalize → judge (mocked LLM) → score → draft (mocked LLM) → approve → send (dry-run). Verify DB state at each stage.

## Phase C5: CI + Polish
16. .github/workflows/ci.yml — CI pipeline from PLANA.md Section 9
17. .env.example — All required env vars documented

After each phase, run pytest on your tests. Commit after each phase:
- "feat(cli): CLI skeleton with project management and stats"
- "feat(cli): pipeline commands — collect, judge, score, draft"
- "feat(cli): approval queue and send with dry-run safety"
- "feat(orchestrator): pipeline orchestrator and training data export"
- "chore(ci): GitHub Actions CI pipeline"

Use the Task tool to run tests in background while coding.
For CLI tests, use Click's CliRunner with mocked dependencies.
```

### Terminal C File Ownership (17 files)

```
src/signalops/cli/main.py              ← Click app entry
src/signalops/cli/project.py           ← Project management
src/signalops/cli/collect.py           ← run collect
src/signalops/cli/judge.py             ← run judge
src/signalops/cli/score.py             ← run score
src/signalops/cli/draft.py             ← run draft
src/signalops/cli/approve.py           ← Approval queue
src/signalops/cli/send.py              ← Send approved
src/signalops/cli/stats.py             ← Stats display
src/signalops/cli/export.py            ← Export commands
src/signalops/pipeline/orchestrator.py ← Pipeline runner
src/signalops/pipeline/sender.py       ← Send stage
src/signalops/training/exporter.py     ← Training data export
tests/test_cli.py
tests/integration/test_pipeline.py
.github/workflows/ci.yml
.env.example
```

---

## Sync Points & Merge Strategy

### Timeline (estimated)

```
TIME    TERMINAL A              TERMINAL B              TERMINAL C
─────── ─────────────────────── ─────────────────────── ───────────────────────
 0:00   A1: Config + Schema     B1: LLM Providers       C1: CLI Skeleton
        (schema.py, loader.py)  (base, anthropic,        (main.py, project.py,
                                 openai, gateway)         stats.py)

 0:30   A2: Storage Layer       B2: Judge System        C2: Pipeline CLI Cmds
        (database.py, audit.py) (judge_model, fallback,  (collect, judge,
                                 pipeline/judge)          score, draft)

 1:00   A3: Connectors          B3: Scoring Engine      C3: Approve + Send
        (rate_limiter, x_auth,  (scorer.py, tests)       (approve, send,
         x_api)                                           sender)

 1:30   A4: Collect + Normalize B4: Draft Generator     C4: Orchestrator
        (collector, normalizer) (draft_model, drafter)   (orchestrator,
                                                          exporter, tests)

 2:00   ✓ A DONE — commit+push  ✓ B DONE — commit+push  C5: CI + Polish
                                                         ✓ C DONE — commit+push

═══════ SYNC POINT: MERGE ═════════════════════════════════════════════════════

 2:15   MERGE Terminal (any one terminal):
        1. git checkout main
        2. git merge feat/data       (clean — A owns its files exclusively)
        3. git merge feat/intel      (may conflict on __init__.py — trivial)
        4. git merge feat/cli        (may conflict on __init__.py — trivial)
        5. Fix any import issues between modules
        6. Run full test suite: pytest tests/ -v
        7. Fix any integration failures

 2:45   INTEGRATION FIX-UP (if needed):
        - Resolve import mismatches between branches
        - Run: ruff check src/ tests/ --fix
        - Run: mypy src/signalops
        - Run: pytest tests/ -v --tb=long
        - Final commit: "feat: integrate all 3 workstreams into working MVP"
```

### Merge Commands (run from any terminal after all 3 are done)

```bash
# Step 1: Merge all branches
git checkout main
git merge feat/data -m "merge: Terminal A — foundation + data pipeline"
git merge feat/intel -m "merge: Terminal B — intelligence layer"
git merge feat/cli -m "merge: Terminal C — CLI + orchestration"

# Step 2: Install and verify
pip install -e ".[dev]"

# Step 3: Run full test suite
pytest tests/ -v --tb=short

# Step 4: Lint + typecheck
ruff check src/ tests/ --fix
ruff format src/ tests/
mypy src/signalops

# Step 5: Smoke test
signalops --help
signalops project list
signalops stats --project spectra
signalops run all --project spectra --dry-run
```

---

## Agentic Claude Code Techniques for Each Terminal

### 1. Parallel Tool Calls (all terminals)
Each Claude Code instance should use parallel tool calls when creating independent files:
```
# Instead of creating files one at a time, create all independent files in one message:
Write schema.py + Write loader.py + Write defaults.py  (all at once)
```

### 2. Background Test Running (all terminals)
After writing a batch of files, run tests in the background while continuing to code:
```
# Write new code, then:
Bash (background): pytest tests/unit/test_config.py -v
# Continue writing next file without waiting for test results
```

### 3. Task Tool for Sub-agents (complex files)
For complex files like database.py or llm_gateway.py, spawn a sub-agent:
```
Task(subagent_type="general-purpose"): "Read PLANA.md Section 4 and implement
all SQLAlchemy models in src/signalops/storage/database.py. Include every table,
enum, constraint, and index exactly as specified."
```

### 4. Worktrees for Branch Isolation
If you want full filesystem isolation (prevents any accidental cross-terminal edits):
```
# Instead of just git checkout, use worktrees:
Terminal A: claude --worktree feat/data
Terminal B: claude --worktree feat/intel
Terminal C: claude --worktree feat/cli
```
Each gets its own directory under `.claude/worktrees/` with a separate working tree.

### 5. Explore Agent for Context Gathering
When a terminal needs to understand what another terminal built (during merge):
```
Task(subagent_type="Explore"): "Find all classes and functions exported from
src/signalops/config/schema.py and src/signalops/storage/database.py.
List their signatures."
```

---

## Conflict Prevention Rules

These rules ensure ZERO merge conflicts between terminals:

| Rule | Why |
|------|-----|
| **Each terminal only writes to its owned files** (listed above) | No two terminals touch the same file |
| **`__init__.py` files**: each terminal only adds exports for ITS modules | Merge combines them; trivial conflict |
| **`tests/conftest.py`**: ONLY Terminal A writes this file | B and C import fixtures from it |
| **Import style**: B and C use `TYPE_CHECKING` imports for A's types | No circular deps, no runtime import failures |
| **No shared state files**: no `.env`, no `signalops.db` in git | Runtime-only, not in repo |
| **CLI lazy imports**: C imports pipeline stages inside functions | Works even if B's modules aren't merged yet |

### If You DO Hit a Conflict

The only likely conflicts are in `__init__.py` files. Resolution is always "keep both sides":

```python
# Both terminals added exports — just combine them:
# FROM Terminal A:
from signalops.config.schema import ProjectConfig
# FROM Terminal B:
from signalops.models.judge_model import RelevanceJudge
# MERGED:
from signalops.config.schema import ProjectConfig
from signalops.models.judge_model import RelevanceJudge
```

---

## Verification Checklist (Post-Merge)

Run these after merging all 3 branches:

```bash
# 1. All tests pass
pytest tests/ -v --tb=short --cov=signalops

# 2. Lint clean
ruff check src/ tests/

# 3. Type check passes (or only minor issues)
mypy src/signalops

# 4. CLI works
signalops --help
signalops project list
signalops project set spectra

# 5. Dry-run pipeline
signalops run all --project spectra --dry-run

# 6. Stats display
signalops stats --project spectra

# 7. Queue commands
signalops queue list --project spectra

# 8. Export command
signalops export training-data --project spectra --type judgments --dry-run
```

### Expected Test Count

| Terminal | Unit Tests | Integration Tests | Total |
|----------|-----------|-------------------|-------|
| A | ~25 | ~8 | ~33 |
| B | ~30 | ~0 | ~30 |
| C | ~15 | ~12 | ~27 |
| **Total** | **~70** | **~20** | **~90** |

---

## Quick Reference: Copy-Paste Terminal Launch Commands

### Terminal A
```bash
cd /c/Users/niran/OneDrive/Desktop/Syntrix && git checkout feat/data && claude
```
Then paste the Terminal A prompt.

### Terminal B
```bash
cd /c/Users/niran/OneDrive/Desktop/Syntrix && git checkout feat/intel && claude
```
Then paste the Terminal B prompt.

### Terminal C
```bash
cd /c/Users/niran/OneDrive/Desktop/Syntrix && git checkout feat/cli && claude
```
Then paste the Terminal C prompt.

### Merge Terminal (after all 3 complete)
```bash
cd /c/Users/niran/OneDrive/Desktop/Syntrix && git checkout main && claude
```
Then paste: "Merge feat/data, feat/intel, feat/cli into main. Fix any import conflicts. Run full test suite. Make everything work together."

---

## Appendix: File Count Summary

| Category | Terminal A | Terminal B | Terminal C | Total |
|----------|-----------|-----------|-----------|-------|
| Source files | 11 | 10 | 13 | 34 |
| Test files | 5 | 4 | 2 | 11 |
| Config/fixture files | 3 | 1 | 2 | 6 |
| **Total** | **19** | **15** | **17** | **51** |

All 51 files map 1:1 to the file tree in PLANA.md Section 3. Nothing is added, nothing is missed.

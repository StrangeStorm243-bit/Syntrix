# Syntrix — Project Context for Claude Code

## What This Is

Syntrix (package name: `signalops`) is an agentic social lead finder + outreach workbench. It collects tweets matching keyword queries, judges relevance via LLM, scores leads, generates reply drafts, and sends human-approved replies. It has a CLI interface and a web dashboard.

**Current state:** v0.2 complete, v0.3 complete. MVP through web dashboard all implemented and tested.

## Architecture

```
CLI (Click) ─┐                            ┌─ Storage (SQLAlchemy/SQLite)
              ├─> Orchestrator ─> Pipeline ─┤
API (FastAPI) ┘         |                  └─ Cache (Redis / InMemory)
                   LLM Gateway (LiteLLM)
                        |
              ┌─────────┼─────────┐
           Langfuse   LLM APIs   Fallback
           (tracing)  (100+)     (TF-IDF)
```

Pipeline: **Collect -> Normalize -> Judge -> Score -> Notify -> Draft -> Approve -> Send -> Track Outcomes**

### Key Directories

- `src/signalops/cli/` — Click CLI (16 active files): main.py entry, project, collect, judge, score, draft, approve, send, correct, export, eval, experiment, model, scoring, stats, notify (orphaned — not registered in main.py)
- `src/signalops/pipeline/` — Pipeline stages: collector, normalizer, judge, scorer, drafter, sender, orchestrator, batch, outcome_tracker
- `src/signalops/models/` — LLM gateway (LiteLLM-backed), judge_model, draft_model, fallback (TF-IDF), ab_test, ab_analysis, finetuned, judge_factory. Note: `providers/` subdirectory was deleted (replaced by LiteLLM)
- `src/signalops/scoring/` — Extensible plugin system: base ABC, engine (plugin loader + rule engine), weighted (5 default plugins), keyword_boost, account_age
- `src/signalops/connectors/` — X API v2 (x_api.py), X OAuth PKCE (x_auth.py), X Filtered Stream (x_stream.py), LinkedIn stub (linkedin.py), async client (async_client.py), connector factory, rate limiter
- `src/signalops/storage/` — SQLAlchemy models (database.py — 11 tables), audit log, cache (InMemory + Redis backends)
- `src/signalops/config/` — Pydantic schema (20+ config models), YAML loader with env var resolution, defaults
- `src/signalops/training/` — Exporter (judgments/drafts/outcomes JSONL), evaluator (offline eval with sklearn), labeler (human corrections), DPO collector, argilla export (optional)
- `src/signalops/notifications/` — Discord and Slack webhook notifiers with retry logic
- `src/signalops/api/` — FastAPI backend: app factory, API key auth, routes (projects, leads, queue, stats, analytics, experiments, pipeline), Pydantic response schemas, WebSocket for real-time pipeline progress
- `dashboard/` — React 19 SPA: Vite + TypeScript + Tailwind + TanStack Query + Recharts. Pages: Dashboard, Leads, Queue, Analytics, Experiments, Settings
- `projects/` — Example project YAML configs (spectra.yaml, salesense.yaml)
- `tests/` — ~330 tests across 34 files: `tests/unit/` (28 files), `tests/integration/` (5 files), `tests/fixtures/`
- `docs/` — MkDocs Material site: install, quickstart, CLI reference, config reference, architecture, design plans

## Tech Stack

- **Python 3.11+**, **Click** for CLI, **rich** for terminal output
- **SQLAlchemy 2.0** with SQLite (no Alembic migrations yet — uses `create_all()`)
- **Pydantic v2** for config validation
- **httpx** for HTTP client (sync + async)
- **LiteLLM** for unified LLM gateway (replaced direct anthropic/openai SDKs) — 100+ provider support
- **Langfuse** for LLM observability and tracing (optional, no-op when not configured)
- **FastAPI** + **uvicorn** for REST API (port 8400)
- **React 19** + **Vite 7** + **Tailwind 4** + **TanStack Query 5** + **Recharts 3** for dashboard
- **Redis** for caching (optional, falls back to in-memory)
- **scikit-learn** for TF-IDF fallback classifier and evaluation metrics
- **pytest** for testing (~330 tests), **ruff** for linting (100-char line length), **mypy --strict** for type checking

## Database Schema (11 tables)

`projects`, `raw_posts`, `normalized_posts`, `judgments`, `scores`, `drafts`, `outcomes`, `audit_logs`, `model_registry`, `ab_experiments`, `ab_results`, `preference_pairs`

Key relationships: `raw_posts` 1:1 `normalized_posts` -> 1:N `judgments`, `scores`, `drafts` -> `drafts` 1:N `outcomes`

## CLI Command Tree

```
signalops [--project/-p] [--dry-run] [--verbose/-v] [--format table|json]
├── project set|list|init
├── run collect [--batch] [--concurrency N] | all | judge | score | draft [--top N]
├── queue list | approve <id> | edit <id> | reject <id> [--reason] | send [--confirm]
├── stats
├── export training-data --type judgments|drafts|outcomes|dpo [--format] [--output] [--since] [--min-confidence] [--include-metadata]
├── correct [id] [--label] [--reason] [--review] [--n N] [--strategy]
├── eval judge --test-set PATH | compare --test-set PATH --models M1,M2
├── scoring list-plugins | list-rules | test-rules
├── experiment create|list|results|stop
└── model register|list|activate|deactivate
```

Note: `notify` group exists in `notify.py` but is NOT registered in `main.py` (orphaned).

## API Endpoints (FastAPI, port 8400)

- `/api/projects` — CRUD, activate
- `/api/leads` — paginated list, top N, detail with judgment/score/draft
- `/api/queue` — draft approval workflow (list, approve, edit, reject, send-preview, send)
- `/api/stats` — pipeline counts, timeline buckets, outcome breakdown
- `/api/analytics` — score distribution, judge accuracy, query performance, persona effectiveness, conversion funnel
- `/api/experiments` — CRUD for A/B tests (uses raw SQL, table-existence guards)
- `/api/pipeline` — run trigger (background task is a **stub** — TODO: wire to PipelineOrchestrator)
- `/ws/pipeline` — WebSocket for real-time progress broadcasts

Entry points: `signalops` (CLI), `signalops-api` (API server)

## Known Gaps and Stubs

- **`/api/pipeline/run` background task** — logs start/end but does NOT run the pipeline (explicit TODO)
- **`/api/queue/send`** — only updates DB status to SENT; does not call X API to deliver replies
- **LinkedIn connector** — fully stubbed (`search()` returns `[]`, `post_reply()` raises, `health_check()` returns False). `to_raw_post()` conversion is complete.
- **SocialData connector** — not implemented (factory raises NotImplementedError)
- **Stats timeline** — only populates `collected` bucket; judged/drafted/sent always 0
- **Experiments UI** — read-only in frontend (no create/stop mutations wired)
- **No Alembic migrations** — schema via `Base.metadata.create_all()` only
- **`async_client.py`** — uses old `api.twitter.com` domain (not `api.x.com`), no retry/rate limiting
- **`notify` CLI group** — defined but never registered in main.py
- **Outcome export `score` field** — hardcoded `None` in `exporter.py`
- **`usePersonaEffectiveness` hook** — exists but not rendered in Analytics page

## Code Conventions

- All files use `from __future__ import annotations`
- All functions have full type annotations (mypy strict)
- Use `dict[str, Any]` not bare `dict`
- SQLAlchemy Column assignments use `# type: ignore[assignment]` where needed
- Imports inside functions for heavy deps in CLI commands (lazy loading)
- Test files mirror source structure: `tests/unit/test_<module>.py`
- LLM calls decorated with `@observe()` for Langfuse tracing (no-op when not installed)
- Optional deps guarded with try/import (sklearn, scipy, langfuse, argilla)

## CI Requirements (must pass before merge)

1. `ruff check src/ tests/` — no lint errors
2. `ruff format --check src/ tests/` — no format issues
3. `mypy src/signalops --strict` — zero type errors
4. `pytest tests/ -v --tb=short` — all tests pass
5. Integration tests run after lint+typecheck+test pass

CI: `.github/workflows/ci.yml` (4 jobs: lint, typecheck, test matrix 3.11+3.12, integration)
Release: `.github/workflows/release.yml` (PyPI publish via OIDC on GitHub release)

## Project Config System

Each project is a YAML file in `projects/` with these sections:
- `project_id/name/description/product_url` — identity
- `platforms` — X (enabled, search_type) + LinkedIn (enabled, post_types)
- `queries` — search queries with labels, per-query platform and max_results
- `icp` — Ideal Customer Profile (followers, languages, bio filters)
- `relevance` — Judge system prompt, positive/negative signals, keyword filters
- `scoring` — weights (5 floats), custom_rules, plugins, keyword_boost, account_age
- `persona` — name, role, tone, voice_notes, example_reply
- `templates` — Jinja2 reply templates with use_when conditions
- `notifications` — enabled flag, min_score, discord/slack webhooks
- `rate_limits` — max replies per hour/day
- `llm` — judge_model, draft_model, temperature, max_tokens, fallback_models
- `batch` — enabled, concurrency, retry config
- `stream` — Filtered Stream (Pro tier) rules
- `redis` — cache TTLs
- `experiments` — A/B test config

See `src/signalops/config/schema.py` for the full Pydantic schema (~20 models).

## Testing Philosophy

- Write tests first when adding new features (TDD)
- Mock external APIs (X API, LLM providers) in tests
- Unit tests for pure logic, integration tests for pipeline flows
- Use `conftest.py` fixtures for shared DB sessions and mock connectors
- Optional deps (sklearn, scipy, langfuse) tested for graceful degradation
- Target: all CI checks green before any merge

## Workflow Rules

### Plan First
- Enter plan mode for any non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan — don't keep pushing
- Write detailed specs upfront to reduce ambiguity

### Subagent Strategy
- Use subagents liberally to keep the main context window clean
- Offload research, exploration, and parallel analysis to subagents
- One task per subagent for focused execution

### Verification Before Done
- Never mark a task complete without proving it works
- Run tests, check logs, demonstrate correctness
- Ask: "Would a staff engineer approve this?"

### Self-Improvement
- After any correction, update `tasks/lessons.md` with the pattern
- Write rules that prevent the same mistake recurring
- Review lessons at session start

### Task Tracking
1. Write plan to `tasks/todo.md` with checkable items
2. Check in before starting implementation
3. Mark items complete as you go
4. Provide a high-level summary at each step
5. Add a review section to `tasks/todo.md`
6. Capture lessons in `tasks/lessons.md` after corrections

### Engineering Standards
- **Simplicity first** — minimal impact, minimal code
- **No laziness** — find root causes, no temporary fixes
- **Minimal blast radius** — touch only what's necessary
- **Demand elegance** — for non-trivial changes, pause and consider a cleaner approach
- **Autonomous bug fixing** — diagnose and resolve without hand-holding

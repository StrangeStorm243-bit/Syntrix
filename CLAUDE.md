# Syntrix — Project Context for Claude Code

## What This Is

Syntrix (package name: `signalops`) is an agentic social lead finder + outreach workbench. It collects tweets matching keyword queries, judges relevance via LLM, scores leads, generates reply drafts, and sends human-approved replies. Currently at **v0.1 (MVP complete)**.

## Architecture

```
CLI (Click) -> Orchestrator -> Pipeline stages -> Storage (SQLAlchemy/SQLite)
                                    |
                              LLM Gateway (Anthropic/OpenAI)
```

Pipeline: **Collect -> Normalize -> Judge -> Score -> Draft -> Approve -> Send**

### Key Directories

- `src/signalops/cli/` — Click CLI commands (main.py entry point)
- `src/signalops/pipeline/` — Pipeline stages (collector, normalizer, judge, scorer, drafter, sender, orchestrator)
- `src/signalops/models/` — LLM gateway, providers (anthropic, openai), judge_model, draft_model, fallback
- `src/signalops/connectors/` — Platform connectors (X API v2), rate limiter, OAuth
- `src/signalops/storage/` — SQLAlchemy models (database.py), audit log
- `src/signalops/config/` — Pydantic schema, YAML loader, defaults
- `src/signalops/training/` — Training data exporter
- `projects/` — Example project YAML configs (spectra.yaml, salesense.yaml)
- `tests/` — Unit tests in `tests/unit/`, integration tests in `tests/integration/`
- `docs/plans/` — Design documents and implementation plans

## Tech Stack

- **Python 3.11+**
- **Click** for CLI
- **SQLAlchemy 2.0** with SQLite (Postgres later)
- **Pydantic v2** for config validation
- **httpx** for HTTP client
- **anthropic** + **openai** SDKs for LLM providers
- **rich** for terminal output
- **pytest** for testing
- **ruff** for linting/formatting (100-char line length)
- **mypy --strict** for type checking

## Code Conventions

- All files use `from __future__ import annotations`
- All functions have full type annotations (mypy strict)
- Use `dict[str, Any]` not bare `dict`
- SQLAlchemy Column assignments use `# type: ignore[assignment]` where needed
- Imports inside functions for heavy deps in CLI commands (lazy loading)
- Test files mirror source structure: `tests/unit/test_<module>.py`

## CI Requirements (must pass before merge)

1. `ruff check src/ tests/` — no lint errors
2. `ruff format --check src/ tests/` — no format issues
3. `mypy src/signalops --strict` — zero type errors
4. `pytest tests/ -v --tb=short` — all tests pass

## v0.2 Goals (current milestone)

From PLANA.md Section 2, the 30-day v0.2 targets:

- **Outcome tracking** — track if replies get liked, replied to, profile visits
- **Feedback loop** — human corrections to judgments feed training data export
- **`export training-data`** — JSONL export for fine-tuning
- **Offline eval** — run held-out test set against current judge
- **Stats TUI dashboard** — rich/textual terminal UI for pipeline stats
- **Filtered Stream** — Pro tier real-time collection
- **Redis caching** — deduplication and rate limit state
- **Multi-project support** — `project set <name>` switching
- **Notification webhooks** — Discord/Slack for high-score leads

## Testing Philosophy

- Write tests first when adding new features (TDD)
- Mock external APIs (X API, LLM providers) in tests
- Unit tests for pure logic, integration tests for pipeline flows
- Use `conftest.py` fixtures for shared DB sessions and mock connectors
- Target: all CI checks green before any merge

## Project Config System

Each project is defined by a YAML file in `projects/` that drives the entire pipeline:
- `queries` — X API search queries
- `icp` — Ideal Customer Profile filters
- `relevance` — Judge system prompt + signals
- `scoring` — Weight config for lead scoring
- `persona` — Draft generation voice/tone
- `rate_limits` — Send throttling
- `llm` — Model selection per stage

See `src/signalops/config/schema.py` for the full Pydantic schema.

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

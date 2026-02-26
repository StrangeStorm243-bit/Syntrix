# Syntrix Final Scope — Close the Loop

## Goal

Ship Syntrix as a complete, self-hostable open-source product with DM outreach, auto-scheduled pipeline, and a polished landing page that guides users from syntrix.app to self-hosting via Docker Compose.

## Context

- syntrix.app is a Next.js landing page deployed on Vercel (aurora theme, glass cards, pipeline viz)
- Dashboard is a React SPA served via Docker Compose (api + dashboard + ollama)
- Pipeline works end-to-end: Collect → Judge → Score → Draft → Approve → Send (replies)
- Sequences execute automatically via APScheduler every 30s
- Missing: DM outreach, auto-scheduled pipeline runs, landing page pointing to Docker path

## Architecture

No new services or infrastructure. All changes are additions to existing systems:

1. **DM Feature** — New action type in the sequence engine (alongside like, follow, reply)
2. **Auto Pipeline** — Second APScheduler job running the pipeline every N hours
3. **Landing Page** — Content updates to existing Next.js components (no structural changes)
4. **Polish** — Version bump, README updates, dependency checks

## Workstream 1: DM Feature (Backend + Frontend)

### Backend Changes

**`connectors/base.py`** — Add `send_dm(user_id: str, text: str) -> dict` to Connector ABC with default NotImplementedError.

**`connectors/twikit_connector.py`** — Implement `send_dm()` wrapping twikit's async `client.send_dm(user_id, text)`.

**`pipeline/sequence_engine.py`** — Add `"dm"` case in `_execute_step()`:
- Generate DM text using the draft generator (reuse persona/tone from config)
- Call `connector.send_dm(user_id, text)`
- Add rate limit check: `max_dms_per_day` (default 20)

**`storage/database.py`** — Ensure `"dm"` is a valid `action_type` for `SequenceStep` and `StepExecution`.

**`config/schema.py`** — Add `max_dms_per_day: int = 20` to rate limit config.

### Frontend Changes

**`pages/Sequences.tsx`** — DM steps render in sequence visualization (already dynamic based on step data).

**`stores/wizardStore.ts` + `pages/Onboarding.tsx`** — Update sequence templates:
- Engage Then Pitch: Like → Reply → Follow → DM (after follow-back)
- Direct Value: Reply → DM (after engagement)
- Relationship First: Like → Reply → Follow → Engage Again → DM
- NEW "Cold DM": DM directly (for users who want DM-first outreach)

### Tests

- Unit test: `send_dm()` connector method
- Unit test: sequence engine executes DM steps with rate limiting
- Unit test: DM rate limit enforcement (max_dms_per_day)

## Workstream 2: Auto-Scheduled Pipeline

**`api/app.py`** — Add `_run_pipeline_tick(db_url)` function and APScheduler job:
- Runs every N hours (configurable, default 4)
- Calls `PipelineOrchestrator.run_all()` for the active project
- Logs results, broadcasts progress via WebSocket

**`config/schema.py`** — Add `pipeline_interval_hours: int = 4`.

**`api/routes/setup.py`** — Settings endpoint accepts `pipeline_interval_hours`.

**`dashboard/src/pages/Settings.tsx`** — Add interval slider (1-24 hours).

### Tests

- Unit test: pipeline tick function creates orchestrator and runs
- Unit test: settings persist pipeline_interval_hours

## Workstream 3: Landing Page Updates

All changes are content swaps in existing components. No structural or styling changes.

| Component | Change |
|-----------|--------|
| `Hero.tsx` | CTA: `pip install` → `docker compose up`. Terminal shows Docker output. Badge: v0.2 → v0.3 |
| `QuickStart.tsx` | 3 steps: Clone → `docker compose up` → Open localhost:3000 |
| `Pipeline.tsx` | Add 8th stage: DM (MessageCircle icon) |
| `Features.tsx` | Add "DM Outreach" and "Web Dashboard" features |
| `TrustBar.tsx` | Add "Docker Ready" badge, change "CLI-first" → "Self-hosted" |
| `Navbar.tsx` | Add "Dashboard" anchor link |

## Workstream 4: Polish

- Update README with DM documentation
- Version badge v0.2 → v0.3 everywhere
- Verify `apscheduler` is in pyproject.toml dependencies
- Verify `cryptography` is in pyproject.toml dependencies
- Full flow test: docker compose up → onboarding → auto pipeline → leads → sequences with DMs

## Parallelization Strategy

Three independent terminals with zero conflict:

| Terminal | Scope | Files Touched |
|----------|-------|---------------|
| **T1: DM Feature** | Backend: connectors, sequence engine, schema, DB. Frontend: wizard templates, sequences page | `src/signalops/connectors/`, `src/signalops/pipeline/sequence_engine.py`, `src/signalops/config/schema.py`, `src/signalops/storage/database.py`, `dashboard/src/stores/`, `dashboard/src/pages/Onboarding.tsx`, `dashboard/src/pages/Sequences.tsx`, `tests/unit/test_twikit_connector.py`, `tests/unit/test_sequence_engine.py` |
| **T2: Auto Pipeline + Settings** | APScheduler job, settings endpoint, Settings page | `src/signalops/api/app.py`, `src/signalops/api/routes/setup.py`, `dashboard/src/pages/Settings.tsx`, `dashboard/src/hooks/useSetup.ts` |
| **T3: Landing Page + Polish** | All files under `landing/src/components/`, README, version bumps | `landing/src/components/*.tsx`, `README.md`, `pyproject.toml` |

No file overlap between terminals.

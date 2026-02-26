# Syntrix Bridge Design — Dashboard-to-Pipeline Integration

**Date:** 2026-02-25
**Status:** Approved
**Goal:** Make Syntrix a fully functional open-source Twitter lead-gen tool driveable entirely from the dashboard, costing $0/month to run.

---

## 1. Project Direction

**Type:** Open-source self-hosted tool with a live demo deployment.

**Why this direction:**
- SaaS requires auth, billing, onboarding, multi-tenancy, reliability — months of work before anyone can use it
- Portfolio-only with mock data is forgettable
- An open-source tool people can actually use gets GitHub stars, demonstrates real product thinking, and is stronger on a resume than any static demo
- SaaS remains possible later (add hosted version if the tool gets traction)

**What "done" looks like:**
- Someone visits the GitHub README, clicks "Live Demo", sees the dashboard working
- Someone clones the repo, runs `docker compose up`, enters Twitter credentials, and starts finding leads within 5 minutes
- The pipeline runs end-to-end from the dashboard (no CLI needed)
- Automated multi-step outreach sequences run in the background

---

## 2. The $0/Month Stack

| Component | Tool | Cost |
|---|---|---|
| Twitter search/collection | twikit (Python, internal Twitter API) | $0 |
| Reply/like/follow posting | twikit (or X API free tier as fallback) | $0 |
| LLM for judging | Ollama — `llama3.2:3b` (fast, good for classification) | $0 |
| LLM for drafting | Ollama — `mistral:7b` or `qwen2.5:7b` (creative writing) | $0 |
| LLM gateway | LiteLLM (already integrated, supports Ollama natively) | $0 |
| Database | SQLite with SQLAlchemy (already working) | $0 |
| Cache | In-memory (already default, optional local Redis) | $0 |
| Background scheduling | APScheduler (in-process, no broker needed) | $0 |
| Sequence engine | Custom state machine in SQLite (~200 lines) | $0 |
| Auth | None (self-hosted single-user tool) | $0 |
| UI components | shadcn/ui (already configured, install components) | $0 |
| Wizard state mgmt | Zustand (1KB) | $0 |
| Dashboard hosting (demo) | Vercel free tier | $0 |
| API hosting (demo) | Railway free tier | $0 |
| **Total** | | **$0/month** |

### Tools explicitly rejected

| Tool | Reason |
|---|---|
| Clerk/Supabase Auth | Cloud dependency, contradicts self-hosted model |
| Supabase/Convex/PlanetScale | Already have working FastAPI + SQLite; these replace working code |
| LangChain/LlamaIndex | 50MB deps for a single LLM call; LiteLLM is correct |
| Trigger.dev/Inngest | Need 4+ Docker containers for what BackgroundTasks does |
| n8n/Temporal | Enterprise overkill; 200-line state machine in SQLite suffices |
| X API Basic ($200/mo) | twikit provides same capabilities for $0 |
| X API Pro ($5000/mo) | DMs are not the primary outreach method |

---

## 3. Outreach Strategy

### Primary: Replies (public, visible, TOS-compliant)
- Reply under the original tweet with a personalized, LLM-generated message
- Always visible in the thread + recipient's notifications
- TOS-compliant — replies to public tweets are normal engagement
- Works on X API free tier (500/month) or twikit (unlimited)

### DMs: NOT a primary channel
- Require X Pro tier ($5,000/month) via official API
- Most users have DMs restricted to followers only
- Cold DMs land in "Message Requests" folder — most people never check
- Unsolicited automated DMs explicitly violate X's automation rules
- DMs may be added later as a warm follow-up (only after someone responds to your reply)

### Automated Sequence Engine (Waalaxy-style)
- Multi-step outreach: Like → Follow → Wait → Reply → Follow-up
- Configurable delays between steps (appear human)
- Conditions: "Did they respond?" branching
- Safety limits: max actions per hour/day
- Human approval still required for reply text (configurable per step)

---

## 4. Architecture

```
+---------------------------------------------------------+
|                    DASHBOARD (React)                     |
|                                                         |
|  +----------+ +------+ +-----+ +---------+ +--------+  |
|  |Onboarding| |Leads | |Queue| |Sequences| |Analytics|  |
|  |  Wizard  | | Page | |Page | |  Page   | |  Page  |  |
|  +----------+ +------+ +-----+ +---------+ +--------+  |
+-----------------------+---------------------------------+
                        |
              REST API + WebSocket
                        |
+-----------------------+----------------------------------+
|                   FastAPI Backend                         |
|                                                          |
|  NEW endpoints:                                          |
|  +- POST /api/setup            <- Onboarding wizard      |
|  +- POST /api/setup/test       <- Test Twitter creds     |
|  +- GET  /api/setup/status     <- Is setup complete?     |
|  +- GET  /api/sequences        <- List sequences         |
|  +- POST /api/sequences        <- Create sequence        |
|  +- GET  /api/sequences/:id    <- Sequence detail        |
|  +- POST /api/pipeline/run     <- WIRED to orchestrator  |
|  +- POST /api/queue/send       <- WIRED to twikit/X API  |
|                                                          |
|  EXISTING (unchanged):                                   |
|  +- /api/leads, /api/queue, /api/stats, /api/analytics  |
|  +- /ws/pipeline (WebSocket for real-time updates)       |
|                                                          |
|  +--------------------------------------------+         |
|  |         Pipeline Orchestrator               |         |
|  |  Collect -> Judge -> Score -+               |         |
|  |                             v               |         |
|  |                      Sequence Engine         |         |
|  |                      +- Enroll leads         |         |
|  |                      +- Execute steps        |         |
|  |                      |  (like/follow/reply)  |         |
|  |                      +- Check conditions     |         |
|  |                      +- Schedule next step   |         |
|  +--------------------------------------------+         |
|                                                          |
|  +------------+  +------------+  +--------------+        |
|  | APScheduler|  |   twikit   |  | LLM Gateway  |        |
|  | (cron +    |  |  (search,  |  | (Ollama /    |        |
|  |  delayed   |  |   like,    |  |  LiteLLM)    |        |
|  |  steps)    |  |   follow,  |  +--------------+        |
|  +------------+  |   reply)   |                          |
|                  +------------+  +--------------+        |
|                                  |    SQLite     |        |
|                                  |  (15 tables)  |        |
|                                  +--------------+        |
+----------------------------------------------------------+
```

### Key decisions

1. **twikit as primary connector** — New `TwikitConnector` implementing `Connector` base class. Same interface as `XConnector` (`search()`, `post_reply()`, `like()`, `follow()`, `health_check()`). Falls back to X API v2 if user has an API key.

2. **Onboarding wizard generates project config** — User fills 5 steps in the dashboard. Backend auto-creates YAML + DB record. No CLI needed.

3. **APScheduler inside FastAPI process** — Collect every 30 min (configurable). Judge + Score + Draft after collection. Sequence steps triggered on delay. Jobs persisted in SQLite.

4. **Ollama as default LLM** — `llama3.2:3b` for judging (fast classification). `mistral:7b` for drafting (creative writing). Cloud models optional for users with API keys.

5. **No auth system** — Self-hosted tool = single user. Remove API key requirement. Public deployments can add reverse proxy auth.

6. **Sequence engine is a state machine** — ~200 lines of Python. SQLite table tracks enrollment + step position + next_run_at. APScheduler polls every 30 seconds.

---

## 5. Onboarding Wizard Flow

Shown on first visit (when no project exists in DB).

### Step 1: "What does your company do?"
- Company name (text input)
- Product URL (text input)
- One-line description (text input)
- "What problem does your product solve?" (textarea)

### Step 2: "Who are your ideal customers?"
- Industry/role keywords (tag input: "developers", "startup founders", etc.)
- What they might tweet about — auto-generates search queries
- Min follower count (slider, default 200)
- Language preferences (multi-select, default English)

### Step 3: "Connect your Twitter account"
- Username + password (stored encrypted in SQLite)
- "Test Connection" button — verifies via twikit
- Optional: X API key field for users who have one
- Warning: twikit uses Twitter's internal API; account risk acknowledged

### Step 4: "How should we talk to leads?"
- Persona name (text, e.g., "Alex from Spectra")
- Role (text, e.g., "developer advocate")
- Tone (dropdown: helpful / casual / professional / witty)
- Voice notes (textarea, optional)
- Example reply (textarea, optional — helps LLM match voice)
- LLM choice: Ollama local (free) or cloud provider + API key

### Step 5: "Choose your outreach style"
- Pre-built sequence templates:
  - **Gentle Touch** (recommended): Like → Wait 1d → Reply
  - **Direct**: Reply immediately
  - **Full Sequence**: Like → Follow → Wait 1d → Reply → Follow-up if no response
- Max actions per day (slider, default 20)
- Require approval for replies? (toggle, default on)

**Submit** → creates project YAML + DB record + enrolls first collection run.

---

## 6. Sequence Engine Design

### Database tables (4 new, added to existing 11)

```sql
-- Outreach sequence templates
CREATE TABLE sequences (
    id INTEGER PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- Ordered steps within a sequence
CREATE TABLE sequence_steps (
    id INTEGER PRIMARY KEY,
    sequence_id INTEGER NOT NULL,
    step_order INTEGER NOT NULL,
    action_type TEXT NOT NULL,        -- 'like', 'follow', 'reply', 'wait', 'check_response'
    delay_hours REAL DEFAULT 0,       -- hours to wait before executing this step
    config_json TEXT DEFAULT '{}',    -- action-specific config (e.g., reply template)
    requires_approval BOOLEAN DEFAULT FALSE,  -- human must approve before execution
    FOREIGN KEY (sequence_id) REFERENCES sequences(id)
);

-- Lead enrolled in a sequence
CREATE TABLE enrollments (
    id INTEGER PRIMARY KEY,
    normalized_post_id INTEGER NOT NULL,
    sequence_id INTEGER NOT NULL,
    project_id TEXT NOT NULL,
    current_step_order INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',     -- 'active', 'paused', 'completed', 'exited'
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    next_step_at TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (normalized_post_id) REFERENCES normalized_posts(id),
    FOREIGN KEY (sequence_id) REFERENCES sequences(id)
);

-- Result of each executed step
CREATE TABLE step_executions (
    id INTEGER PRIMARY KEY,
    enrollment_id INTEGER NOT NULL,
    step_id INTEGER NOT NULL,
    action_type TEXT NOT NULL,
    status TEXT DEFAULT 'pending',    -- 'pending', 'executed', 'failed', 'skipped'
    executed_at TIMESTAMP,
    result_json TEXT DEFAULT '{}',    -- action result (post_id, error, etc.)
    FOREIGN KEY (enrollment_id) REFERENCES enrollments(id),
    FOREIGN KEY (step_id) REFERENCES sequence_steps(id)
);
```

### Pre-built sequence templates

**Gentle Touch (default):**
1. Like their tweet (immediate)
2. Wait 24 hours
3. Reply with AI-generated message (requires approval)

**Direct:**
1. Reply with AI-generated message (requires approval)

**Full Sequence:**
1. Like their tweet (immediate)
2. Follow the user (+6 hours)
3. Wait 24 hours
4. Reply with AI-generated message (requires approval)
5. Check: did they respond? (after 3 days)
   - Yes → mark as warm lead, notify
   - No → like another of their tweets (+1 day)
6. Check: any engagement after 7 days?
   - Yes → mark as warm lead
   - No → mark as cold, exit

### Execution loop (APScheduler, every 30 seconds)

```python
async def execute_pending_steps():
    """Poll enrollments table, execute due steps."""
    due = db.query(Enrollment).filter(
        Enrollment.status == "active",
        Enrollment.next_step_at <= datetime.utcnow()
    ).all()

    for enrollment in due:
        step = get_next_step(enrollment)
        if step.requires_approval and not is_draft_approved(enrollment):
            continue  # wait for human

        result = await execute_action(step.action_type, enrollment, step.config_json)
        record_execution(enrollment, step, result)
        advance_to_next_step(enrollment)
```

### Safety limits

- Max likes per hour: 15 (default)
- Max follows per hour: 5 (default)
- Max replies per day: 20 (default)
- Random jitter: +-30% on all delays
- Auto-pause if any action fails 3 times consecutively
- Cooldown after rate limit hit: 1 hour

---

## 7. New/Modified Backend Components

### New files

| File | Purpose |
|---|---|
| `src/signalops/connectors/twikit_connector.py` | TwikitConnector implementing Connector base class |
| `src/signalops/pipeline/sequence_engine.py` | State machine: enroll, execute steps, check conditions |
| `src/signalops/api/routes/setup.py` | POST /api/setup, POST /api/setup/test, GET /api/setup/status |
| `src/signalops/api/routes/sequences.py` | CRUD for sequences + enrollment stats |
| `dashboard/src/pages/Onboarding.tsx` | 5-step setup wizard |
| `dashboard/src/pages/Sequences.tsx` | Sequence management + enrollment funnel |
| `dashboard/src/stores/wizardStore.ts` | Zustand store for wizard state |

### Modified files

| File | Change |
|---|---|
| `src/signalops/api/routes/pipeline.py` | Wire stub to PipelineOrchestrator.run() |
| `src/signalops/api/routes/queue.py` | Wire send to TwikitConnector/XConnector.post_reply() |
| `src/signalops/api/app.py` | Add new routers, add APScheduler lifespan, remove API key requirement |
| `src/signalops/storage/database.py` | Add 4 new tables (sequences, sequence_steps, enrollments, step_executions) |
| `src/signalops/config/schema.py` | Add Ollama defaults, twikit credential fields |
| `src/signalops/config/defaults.py` | Default LLM to ollama/llama3.2:3b (judge) and ollama/mistral:7b (draft) |
| `src/signalops/connectors/__init__.py` | Register TwikitConnector in factory |
| `dashboard/src/App.tsx` | Add Onboarding and Sequences routes, conditional routing |
| `dashboard/src/pages/Settings.tsx` | Add Twitter credentials, LLM config, sequence settings |
| `dashboard/src/pages/Dashboard.tsx` | Add active sequences KPI card |
| `dashboard/src/pages/Leads.tsx` | Add sequence status column |

### New npm dependencies

| Package | Size | Purpose |
|---|---|---|
| `react-hook-form` | 9KB | Form handling for wizard |
| `@hookform/resolvers` | 2KB | Zod integration |
| `zod` | 13KB | Schema validation |
| `zustand` | 1KB | Wizard state management |
| shadcn/ui components | varies | ~20 UI components (copy-paste, no runtime dep) |

### New pip dependencies

| Package | Purpose |
|---|---|
| `twikit` | Twitter internal API client |
| `apscheduler` | Background job scheduling |
| `cryptography` | Encrypt stored Twitter credentials |

---

## 8. Dashboard Changes

| Page | Change |
|---|---|
| **Onboarding Wizard** | NEW — 5-step setup, shown on first visit |
| **Dashboard** | Add "active sequences" and "enrolled leads" to KPI cards |
| **Leads** | Add "sequence status" column (enrolled / completed / not enrolled) |
| **Queue** | Unchanged — approve/edit/reject reply drafts (now connected to send) |
| **Sequences** | NEW — active sequences, leads per step, conversion funnel |
| **Pipeline** | "Run Pipeline" button actually triggers backend |
| **Settings** | Twitter credentials, LLM config, sequence settings, safety limits |
| **Analytics** | Unchanged (already works) |
| **Experiments** | Unchanged (read-only) |

### Conditional routing

```
if (no project exists) → show Onboarding Wizard
else → show Dashboard (normal routing)
```

---

## 9. Deployment

### Self-hosted (Docker Compose)

```yaml
services:
  api:
    build: .
    ports: ["8400:8400"]
    volumes: ["./data:/app/data"]  # SQLite + project configs
    environment:
      - OLLAMA_HOST=http://ollama:11434

  dashboard:
    build: ./dashboard
    ports: ["3000:3000"]

  ollama:
    image: ollama/ollama
    ports: ["11434:11434"]
    volumes: ["ollama_data:/root/.ollama"]

volumes:
  ollama_data:
```

```bash
git clone https://github.com/you/syntrix
docker compose up
# Open http://localhost:3000 → onboarding wizard
```

### Live demo

- Dashboard: Vercel (free)
- API: Railway free tier
- Ollama: Railway or Fly.io (free tier, GPU optional)

---

## 10. Resume Value

This project demonstrates:

- **Full-stack engineering:** React 19 + FastAPI + SQLAlchemy + WebSocket
- **AI/ML integration:** LLM-powered judging, scoring, drafting with Ollama/LiteLLM; TF-IDF fallback; plugin scoring system
- **Systems design:** Pipeline architecture, state-machine sequence engine, background scheduling, connector abstraction layer
- **Real product thinking:** Automated outreach sequences, human-in-the-loop approval, safety rate limits
- **Open-source craft:** Docker Compose one-liner setup, zero external dependencies, self-hosted
- **Production concerns:** Encrypted credentials, rate limiting, audit logging, graceful degradation

---

## 11. What This Design Does NOT Include (future)

- User accounts / multi-tenancy (SaaS concern)
- Billing / Stripe integration (SaaS concern)
- DM support (requires X Pro tier at $5,000/month)
- LinkedIn connector (stub exists, not wired)
- Custom LLM training (long-term vision)
- Full Twitter account management bot (long-term vision)
- Alembic migrations (use create_all for now)

These are deliberately deferred. Ship the core tool first, validate demand, then layer on SaaS infrastructure.

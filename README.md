<p align="center">
  <h1 align="center">SignalOps</h1>
  <p align="center">
    <strong>Agentic social lead finder + outreach workbench</strong>
  </p>
  <p align="center">
    Collect tweets matching keyword queries, judge relevance via LLM, score leads, generate reply drafts, and send human-approved replies — from the CLI or a web dashboard.
  </p>
</p>

<p align="center">
  <a href="https://github.com/StrangeStorm243-bit/Syntrix/actions/workflows/ci.yml"><img src="https://github.com/StrangeStorm243-bit/Syntrix/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11%2B-blue" alt="Python 3.11+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
</p>

---

## How It Works

Define a project config (target queries, ideal customer profile, reply persona) and let the pipeline do the rest:

```
Collect ──> Normalize ──> Judge ──> Score ──> Notify ──> Draft ──> Approve ──> Send ──> Track
  X API       Clean text    LLM       Weighted   Webhooks   LLM       Human      X API    Outcomes
              + entities    classify   ranking    (Discord/  persona   review     post     (likes,
                            relevant   0-100      Slack)     + tone    gate       reply    replies,
                            /irrelevant                                                    follows)
```

Every reply requires human approval. No auto-send, no multi-account, no browser automation.

---

## Features

### Core Pipeline
- **LLM-powered relevance judging** — any model via LiteLLM (100+ providers), keyword pre-filter for zero-cost exclusions
- **Weighted lead scoring** (0-100) — extensible plugin system with 5 default scorers (relevance, authority, engagement, recency, intent) plus custom rules
- **AI draft generation** — context-aware replies using project persona, tone, and voice notes with automatic character limit enforcement
- **Human-in-the-loop approval** — approve, edit, or reject every draft before sending
- **Rate-limited sending** — configurable hourly/daily/monthly caps with jitter

### Intelligence & Learning
- **Outcome tracking** — monitors if replies get liked, replied to, or followed
- **Human feedback loop** — corrections to judgments feed training data export
- **Training data export** — JSONL export for fine-tuning (judgments, drafts, DPO preference pairs, outcomes)
- **DPO preference collection** — human edits automatically generate preference pairs for alignment training
- **Offline evaluation** — test judge accuracy against labeled datasets with MCC, precision, recall metrics
- **A/B testing** — canary routing between judge models with chi-squared statistical analysis
- **Fine-tuned model support** — register and hot-swap fine-tuned models via config

### Platform & Infrastructure
- **Web dashboard** — React SPA with pipeline stats, lead browser, draft queue, analytics charts, and real-time WebSocket updates
- **REST API** — FastAPI backend with paginated endpoints for leads, queue, stats, analytics, and experiments
- **Notification webhooks** — Discord and Slack alerts for high-score leads
- **Multi-project support** — switch between project configs with `project set`
- **Redis caching** — optional deduplication and rate limit persistence (falls back to in-memory)
- **Filtered Stream** — real-time collection via X API Pro tier
- **Batch collection** — async concurrent query fetching with configurable concurrency
- **LLM observability** — optional Langfuse integration for tracing every LLM call

---

## Quick Start (Docker)

The fastest way to run Syntrix — one command, zero dependencies.

```bash
git clone https://github.com/StrangeStorm243-bit/Syntrix.git
cd Syntrix
docker compose up
```

This starts 3 services:

| Service | Port | Purpose |
|---------|------|---------|
| **Dashboard** | [localhost:3000](http://localhost:3000) | Web UI — onboarding wizard, leads, queue, analytics |
| **API** | [localhost:8400](http://localhost:8400) | FastAPI backend (auto-proxied by dashboard) |
| **Ollama** | localhost:11434 | Free local LLM for judging + drafting |

On first run, Ollama automatically pulls the required models (`llama3.2:3b` + `mistral:7b` — ~6 GB total). This takes a few minutes.

**Open [http://localhost:3000](http://localhost:3000)** — the onboarding wizard walks you through setup:
1. Describe your company and product
2. Define your ideal customer
3. Connect your Twitter account
4. Configure your reply persona
5. Choose an outreach sequence

After setup, hit "Run Pipeline" to start collecting and scoring leads.

### Stopping and restarting

```bash
docker compose down      # Stop all services
docker compose up -d     # Start in background
docker compose logs -f   # Follow logs
```

Your data persists in `./data/` (SQLite database) and `./projects/` (project configs). Ollama model weights are stored in a Docker volume.

---

## Quick Start (CLI)

For developers who want to run Syntrix without Docker.

### 1. Install

```bash
pip install signalops
```

Or from source:

```bash
git clone https://github.com/StrangeStorm243-bit/Syntrix.git
cd Syntrix
pip install -e ".[dev,bridge]"
```

### 2. Configure credentials

```bash
cp .env.example .env
# Edit .env with your API keys:
#   X_BEARER_TOKEN     — X API v2 bearer token (required for collection)
#   ANTHROPIC_API_KEY   — or OPENAI_API_KEY for LLM calls
```

### 3. Set up a project

```bash
# Use a bundled example project
signalops project set spectra

# Or create your own interactively
signalops project init
```

### 4. Run the pipeline

```bash
# Full pipeline (collect → normalize → judge → score → notify → draft)
signalops run all --dry-run

# Or run stages individually
signalops run collect
signalops run judge
signalops run score
signalops run draft --top 10
```

### 5. Review and send

```bash
# Browse the draft queue
signalops queue list

# Approve, edit, or reject drafts
signalops queue approve 1
signalops queue edit 2
signalops queue reject 3 --reason "Too generic"

# Send approved replies (preview first, then confirm)
signalops queue send
signalops queue send --confirm
```

### 6. Monitor results

```bash
# Terminal dashboard
signalops stats

# Or launch the web dashboard
signalops-api
# Visit http://localhost:8400 (API) + http://localhost:5173 (dev frontend)
```

---

## Web Dashboard

The dashboard provides a visual interface for the entire workflow:

| Page | What It Shows |
|------|---------------|
| **Onboarding** | 5-step setup wizard (shown on first visit) |
| **Dashboard** | Metric cards (leads, pending drafts, sent, active sequences) + pipeline funnel |
| **Leads** | Paginated lead table with score badges, judgment labels, enrollment status |
| **Queue** | Draft cards with approve/edit/reject actions and inline editing |
| **Sequences** | Outreach sequences with step visualization and enrollment tracking |
| **Analytics** | Score distribution, conversion funnel, query performance, judge accuracy |
| **Experiments** | A/B test overview with model comparisons and traffic splits |
| **Settings** | Twitter credentials, LLM config, sequence settings, rate limits |

With Docker: `docker compose up` then visit [localhost:3000](http://localhost:3000).

For local development:

```bash
# Terminal 1: API server
signalops-api                    # Runs on port 8400

# Terminal 2: Frontend dev server
cd dashboard && npm run dev      # Runs on port 5173, proxies to API
```

---

## Project Configuration

Each project is a YAML file in `projects/`. Here's a minimal example:

```yaml
project_id: my-product
project_name: "My SaaS"
description: "Find leads interested in my product"

queries:
  - text: '"looking for" ("my-feature") -is:retweet lang:en'
    label: "Active search"

relevance:
  system_prompt: "Judge whether this tweet shows interest in my product."
  positive_signals: ["asking for recommendations", "expressing frustration"]
  negative_signals: ["hiring post", "spam"]

persona:
  name: "Alex"
  role: "product specialist"
  tone: "helpful"
  voice_notes: "Be genuine, not salesy. Lead with empathy."
  example_reply: "Totally get that — happy to show you what we built."
```

Full configs support additional sections for ICP filters, scoring weights, custom scoring rules, notification webhooks, batch collection, Redis caching, A/B experiments, and more. See [`projects/spectra.yaml`](projects/spectra.yaml) and [`projects/salesense.yaml`](projects/salesense.yaml) for complete examples.

---

## CLI Reference

```
signalops [--project/-p NAME] [--dry-run] [--verbose/-v] [--format table|json]

  project     set <name> | list | init
  run         collect [--batch] [--concurrency N] | all | judge | score | draft [--top N]
  queue       list | approve <id> | edit <id> | reject <id> [--reason] | send [--confirm]
  stats       Pipeline stats, outcomes, and training data summary
  export      training-data --type judgments|drafts|outcomes|dpo [--format] [--output] [--since]
  correct     [id] [--label] [--reason] | --review [--n N] [--strategy low_confidence|random|recent]
  eval        judge --test-set PATH | compare --test-set PATH --models M1,M2,...
  scoring     list-plugins | list-rules | test-rules
  experiment  create --primary M --canary M [--canary-pct] | list | results <id> | stop <id>
  model       register --model-id --provider --type | list [--all] | activate <id> | deactivate <id>
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CLI (Click) / Web Dashboard (React)              │
└────────────────┬──────────────────────────────────┬─────────────────────┘
                 │                                  │
                 ▼                                  ▼
┌─────────────────────────┐           ┌──────────────────────────────────┐
│     Orchestrator        │           │       FastAPI REST API           │
│  Pipeline execution,    │           │  /api/leads, /queue, /stats,    │
│  error handling,        │           │  /analytics, /experiments        │
│  rate limiting          │           │  WebSocket: /ws/pipeline         │
└──┬────┬────┬────┬────┬──┘           └──────────────────────────────────┘
   │    │    │    │    │
   ▼    ▼    ▼    ▼    ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │                        Pipeline Stages                               │
 │  Collect → Normalize → Judge → Score → Notify → Draft → Send       │
 │                          │               │                           │
 │                    ┌─────┴─────┐   ┌─────┴─────┐                    │
 │                    │ A/B Test  │   │  Plugin   │                    │
 │                    │ Routing   │   │  Engine   │                    │
 │                    └───────────┘   └───────────┘                    │
 └──────────────────────────────────────────────────────────────────────┘
   │              │                │                    │
   ▼              ▼                ▼                    ▼
 ┌──────────┐  ┌───────────┐  ┌────────────┐  ┌──────────────────────┐
 │Connectors│  │LLM Gateway│  │  Storage   │  │    Notifications     │
 │ X API v2 │  │ (LiteLLM) │  │ SQLAlchemy │  │  Discord + Slack     │
 │ LinkedIn │  │ Langfuse  │  │ Redis/Mem  │  │  webhooks            │
 │ Stream   │  │ 100+ LLMs │  │ Audit Log  │  └──────────────────────┘
 └──────────┘  └───────────┘  └────────────┘
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| CLI | Click, Rich |
| Web API | FastAPI, uvicorn, WebSockets |
| Frontend | React 19, Vite, Tailwind CSS, TanStack Query, Recharts |
| LLM | LiteLLM (100+ providers), Langfuse (tracing) |
| Database | SQLAlchemy 2.0, SQLite |
| Caching | Redis (optional, in-memory fallback) |
| Connectors | X API v2 (search + stream + reply), LinkedIn (read-only stub) |
| ML | scikit-learn (TF-IDF fallback, evaluation metrics) |
| Testing | pytest (~330 tests), ruff, mypy --strict |

---

## Development

### Setup

```bash
git clone https://github.com/StrangeStorm243-bit/Syntrix.git
cd Syntrix
pip install -e ".[dev]"
```

### Run CI checks locally

```bash
ruff check src/ tests/            # Lint
ruff format --check src/ tests/   # Format
mypy src/signalops --strict       # Type check
pytest tests/ -v --tb=short       # Tests
```

### Run the dashboard locally

```bash
# Terminal 1: API server
signalops-api

# Terminal 2: Frontend dev server
cd dashboard
npm install
npm run dev
```

### Project structure

```
src/signalops/
├── cli/            # Click commands (16 files)
├── pipeline/       # Pipeline stages + orchestrator + batch
├── models/         # LLM gateway, judge, drafter, A/B test, fine-tuned
├── scoring/        # Extensible plugin system (7 plugins)
├── connectors/     # X API, LinkedIn, stream, rate limiter
├── storage/        # SQLAlchemy models (11 tables), audit, cache
├── config/         # Pydantic schema (~20 models), YAML loader
├── training/       # Exporter, evaluator, labeler, DPO, argilla
├── notifications/  # Discord + Slack webhook notifiers
└── api/            # FastAPI backend + routes + WebSocket
dashboard/          # React SPA (Vite + TypeScript + Tailwind)
projects/           # Example YAML configs
tests/              # ~330 tests (unit + integration)
docs/               # MkDocs Material documentation site
```

---

## License

[MIT](LICENSE)

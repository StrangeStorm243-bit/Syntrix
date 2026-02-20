# Architecture

## Overview

SignalOps follows a staged pipeline architecture. Each stage is independent and communicates through the SQLite database.

```
CLI (Click)
    │
    ▼
Orchestrator
    │
    ▼
Pipeline Stages ──► Storage (SQLAlchemy / SQLite)
    │
    ├── Collect ──► X API v2 (search, stream)
    ├── Normalize
    ├── Judge ──► LLM Gateway (Claude / GPT)
    ├── Score
    ├── Draft ──► LLM Gateway (Claude / GPT)
    ├── Approve (human-in-the-loop)
    └── Send ──► X API v2 (post reply)
```

## Pipeline Stages

### Collect

Fetches tweets from X API v2 using project search queries. Supports two modes:

- **Search** — polls `tweets/search/recent` with configured queries
- **Filtered Stream** — real-time collection via X API Pro tier (optional)

Stores raw JSON as `RawPost` records. Deduplication prevents re-processing the same tweet.

### Normalize

Converts raw API responses into a clean `NormalizedPost` format: extracted text, author info, timestamps, and engagement metrics. Platform-agnostic schema for future multi-platform support.

### Judge

Sends each normalized post to an LLM (Claude or GPT) with the project's relevance rubric. Returns a label (`relevant`, `irrelevant`, `maybe`) and a confidence score (0.0–1.0).

### Score

Computes a composite lead score (0–100) using configurable weights:

| Factor | Default Weight |
|--------|---------------|
| Relevance judgment | 0.35 |
| Author authority | 0.25 |
| Engagement signals | 0.15 |
| Recency | 0.15 |
| Intent strength | 0.10 |

### Draft

Generates reply drafts using the project persona and templates. The LLM receives the original tweet text, author context, and persona instructions.

### Approve

Human-in-the-loop stage. Drafts must be explicitly approved, edited, or rejected via the `queue` CLI commands before they can be sent.

### Send

Posts approved replies via X API v2. Enforces rate limits (hourly, daily, monthly caps) and adds jitter between sends. Tracks sent post IDs for outcome monitoring.

## Key Components

### LLM Gateway

Abstraction layer over LLM providers. Supports:

- **Anthropic** (Claude) — via `anthropic` SDK
- **OpenAI** (GPT) — via `openai` SDK

Model selection is per-stage via the project `llm` config. Includes automatic fallback between providers.

### X API Connector

Handles all X API v2 communication:

- **Search** — `tweets/search/recent`
- **User lookup** — `users/by/username`
- **Post reply** — `tweets` (create)
- **Tweet metrics** — `tweets` (lookup with `public_metrics`)
- **Filtered Stream** — `tweets/search/stream`

Includes typed error handling (`RateLimitError`, `AuthenticationError`, `APIError`) and automatic retry with exponential backoff.

### Rate Limiter

Token-bucket rate limiter for X API requests. Supports:

- **In-memory** — default, resets on restart
- **Redis-backed** — persistent state across restarts

Respects X API rate limit headers (`x-rate-limit-remaining`, `x-rate-limit-reset`).

### Storage

SQLAlchemy 2.0 with SQLite (Postgres-ready schema). Key models:

| Model | Purpose |
|-------|---------|
| `Project` | Project metadata and config hash |
| `RawPost` | Raw API responses |
| `NormalizedPost` | Cleaned, structured post data |
| `Judgment` | LLM relevance judgments |
| `LeadScore` | Composite lead scores |
| `Draft` | Generated reply drafts (with status lifecycle) |
| `AuditLog` | Action history for all operations |

Draft status lifecycle: `PENDING → APPROVED/EDITED/REJECTED → SENT/FAILED`

### Config System

Pydantic v2 models validate project YAML configs at load time. Each project config drives the entire pipeline — queries, ICP filters, judge rubric, scoring weights, persona, rate limits, and LLM selection.

### Notifications

Optional webhook notifications for high-score leads:

- **Discord** — rich embeds with lead details
- **Slack** — Block Kit formatted messages

Configured per-project with a minimum score threshold.

## Directory Structure

```
src/signalops/
├── cli/                 # Click CLI commands
│   ├── main.py          # Entry point + global options
│   ├── project.py       # project set/list/init
│   ├── collect.py       # run collect/judge/score/draft/all
│   ├── approve.py       # queue list/approve/edit/reject
│   ├── send.py          # queue send
│   ├── stats.py         # stats dashboard
│   ├── export.py        # export training-data
│   ├── correct.py       # correct judgments
│   └── eval.py          # eval judge/compare
├── pipeline/            # Pipeline stages
│   ├── orchestrator.py  # Runs all stages in sequence
│   ├── collector.py     # Tweet collection
│   ├── normalizer.py    # Raw → normalized
│   ├── judge.py         # LLM relevance judging
│   ├── scorer.py        # Lead scoring
│   ├── drafter.py       # Reply draft generation
│   └── sender.py        # Reply sending
├── models/              # LLM integration
│   ├── llm_gateway.py   # Provider abstraction
│   ├── providers/       # anthropic.py, openai.py
│   ├── judge_model.py   # Judge prompt builder
│   ├── draft_model.py   # Draft prompt builder
│   └── fallback.py      # Provider fallback logic
├── connectors/          # External API clients
│   ├── x_api.py         # X API v2 connector
│   ├── x_auth.py        # OAuth 2.0 PKCE flow
│   ├── x_stream.py      # Filtered Stream
│   ├── rate_limiter.py  # Token bucket rate limiter
│   └── base.py          # Base connector types
├── storage/             # Database
│   ├── database.py      # SQLAlchemy models
│   └── audit.py         # Audit log
├── config/              # Configuration
│   ├── schema.py        # Pydantic models
│   ├── loader.py        # YAML loading
│   └── defaults.py      # Default values
├── notifications/       # Webhooks
│   ├── discord.py       # Discord notifier
│   └── slack.py         # Slack notifier
├── training/            # Training data
│   └── exporter.py      # JSONL export
├── exceptions.py        # Exception hierarchy + retry
└── __init__.py
```

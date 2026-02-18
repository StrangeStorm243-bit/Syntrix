# PLANA.md — Syntrix: Agentic Social Lead Finder + Outreach Workbench

> **Codename:** Syntrix
> **Repo name:** `Syntrix`
> **Tagline:** Open-source, compliance-first social lead intelligence — find intent signals, qualify leads, draft outreach, learn from outcomes.

---

## Table of Contents

1. [Research Summary](#1-research-summary)
2. [Product Spec (MVP → v2 → v3)](#2-product-spec)
3. [System Architecture](#3-system-architecture)
4. [Data Model](#4-data-model)
5. [Config / Adapter Design](#5-config--adapter-design)
6. [LLM Training & Learning Roadmap](#6-llm-training--learning-roadmap)
7. [Implementation Plan](#7-implementation-plan)
8. [CLI Spec](#8-cli-spec)
9. [Testing + CI](#9-testing--ci)
10. [Risk Notes](#10-risk-notes)

---

## 1. Research Summary

### Repos Reviewed

| Repo | Stars | Approach | ToS Risk | Key Takeaway |
|------|-------|----------|----------|--------------|
| **syzer/twitter-marketing-bot** | 6 | API v1.1 + Naive Bayes classifier | Low (read-only) | Tokenize→stem→classify pipeline, user labeling via timeline analysis. Dead project (2017). |
| **gkamradt/twitter-reply-bot** | 64 | Official API v2 (Tweepy) + GPT-4 | Medium | Simplest viable pattern: poll mentions → LLM reply → Airtable log. 140 lines. Only responds to mentions, no proactive search. |
| **Prem95/socialautonomies** | 15 | Cookie scraper (elizaOS) + DeepSeek | **High** | Best architecture: two-stage LLM (filter→generate), agent personas, monthly quotas, Prisma+PG. Cookie auth = ToS violation. |
| **ihuzaifashoukat/twitter-automation-ai** | 96 | Selenium + multi-account + stealth | **Very High** | Most feature-rich: per-account overrides, engagement decision engine, Pydantic models, strategy presets. Selenium + multi-account = max risk. |
| **Dheerajjha451/Twitter_AI_Promoter** | 4 | Selenium + Gemini | **Very High** | Dual validation (AI + keywords) reduces false positives. But it's a spam bot—every reply promotes one hardcoded product. |
| **s1s1fo/TwitterMon** | 8 | Browser emulation + VADER sentiment | **High** | Decoupled collection→analysis via Redis pub/sub. Sentiment analysis on social text. Outdated (2019). |
| **TheSethRose/SocialData-MCP-Server** | 5 | SocialData API + MCP | **Low** | MCP tool pattern for LLM integration. Webhook-based monitoring. ToS-compliant via paid data provider. Stateless, no storage. |
| **Vosker1/xbot-demo** | 1 | Closed-source .exe via Telegram | **Extreme** | Test/dry-run mode is a good pattern. Everything else is a red flag (closed binary, multi-account spam). |
| **nirholas/xeepy** | 55 | Playwright + multi-provider AI | **High** | Most comprehensive: SmartTargeting scoring, SearchFilters, rate limiter with jitter, multi-channel notifications, CLI+REST+GraphQL. 44K lines. Browser automation = ToS violation. |
| **gitroomhq/postiz-app** | 26.6K | Official OAuth + Temporal | **Low** | Gold standard for compliance. Provider interface pattern (`IAuthenticator` + `ISocialMediaIntegration`), proper OAuth 1.0a flow, error classification, rate limit respect. |

### Patterns We Will Adopt

| Pattern | Source | Our Implementation |
|---------|--------|--------------------|
| Two-stage LLM pipeline (filter→generate) | socialautonomies | Judge stage filters before expensive draft generation |
| SmartTargeting scoring (0-100, reasons, actions) | xeepy | Lead scoring with explainable scores |
| Provider interface for platforms | postiz-app | `Connector` ABC with X as first implementation |
| OAuth 1.0a/2.0 PKCE | postiz-app | Compliant auth, no cookies/scraping |
| Per-project config overrides | automation-ai | `project.yaml` adapter pattern |
| Dual validation (AI + rules) | Twitter_AI_Promoter | LLM judgment + keyword safety net |
| Circuit breaker + fallback | best practice | Primary LLM → fallback TF-IDF classifier |
| Rate limiter with sliding window + jitter | xeepy | Respect API limits, avoid detection |
| Dry-run/test mode | xbot-demo | `--dry-run` flag on all write operations |
| Multi-channel notifications | xeepy | Discord/Slack webhooks for lead alerts |
| Error classification (refresh vs bad-body) | postiz-app | Resilient API client |
| Agent persona system | socialautonomies | Per-project voice/tone in drafts |
| Monthly usage caps | socialautonomies | Prevent runaway API costs |

### What We Will NOT Do

| Anti-Pattern | Source | Why We Avoid It |
|--------------|--------|-----------------|
| Browser automation / Selenium | automation-ai, xeepy, TwitterMon | Direct ToS violation, account suspension risk |
| Cookie-based auth | socialautonomies | Security risk, ToS violation |
| Multi-account coordination | automation-ai, xbot-demo | Coordinated inauthentic behavior |
| Auto-DM spam | — | X explicitly prohibits unsolicited automated DMs |
| Auto-like/follow/retweet at scale | xeepy | Platform manipulation |
| Hardcoded product promotion | Twitter_AI_Promoter | Spam behavior |
| Character-by-character typing stealth | Twitter_AI_Promoter | Evasion of bot detection = bad faith |

---

## 2. Product Spec

### MVP (v0.1 — Ship in 7 days)

**Goal:** CLI tool that collects tweets matching keyword queries, judges relevance to a project, scores leads, and generates reply drafts. Human approves before anything is sent.

**Features:**
- `project.yaml` config defining queries, ICP, relevance rubric, templates
- Collect tweets via X API v2 `search/recent` endpoint
- Normalize raw tweets (strip URLs, resolve mentions, detect language)
- Judge relevance using LLM (Claude/GPT) with structured output
- Score leads (0-100) using weighted criteria from config
- Generate reply drafts using LLM with project persona
- Human approval queue (CLI-based: approve/edit/reject)
- Send approved replies via X API v2 `POST /2/tweets`
- SQLite storage for all pipeline data
- Full audit log of every action
- `--dry-run` mode for safe testing

**Non-features (explicitly deferred):**
- No web dashboard
- No DM automation
- No auto-like/follow/retweet
- No multi-account
- No real-time streaming

### v0.2 (30-day)

**Goal:** Add learning loop, better scoring, and basic analytics.

**Features:**
- Outcome tracking (was reply liked? replied to? profile visited?)
- Feedback loop: human corrections to judgments feed training data export
- `export training-data` command → JSONL for fine-tuning
- Offline eval command: run held-out test set against current judge
- Stats dashboard in terminal (rich/textual TUI)
- Filtered Stream support (Pro tier) for real-time collection
- Redis caching layer for deduplication and rate limit state
- Multiple project support (`project set <name>`)
- Notification webhooks (Discord/Slack) for high-score leads

### v0.3 (60-day)

**Goal:** Fine-tuned models, web dashboard, multi-platform.

**Features:**
- Fine-tuned classifier deployed behind Judge interface (swap LLM → fine-tuned model)
- A/B testing between judge models (canary routing)
- Web dashboard (React + FastAPI) for approval queue and analytics
- Platform adapter for LinkedIn (read-only intelligence)
- DPO preference data collection from draft approvals/rejections
- Batch processing mode for high-volume collection
- Plugin system for custom scoring functions

---

## 3. System Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLI / Dashboard                              │
│  (Click CLI)              (React + FastAPI — v0.3)                   │
└──────────┬──────────────────────────┬───────────────────────────────┘
           │                          │
           ▼                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Orchestrator                                  │
│  Pipeline: Collect → Normalize → Judge → Score → Draft → Approve     │
│  Manages pipeline execution, error handling, rate limiting           │
└──┬────────┬──────────┬──────────┬──────────┬──────────┬─────────────┘
   │        │          │          │          │          │
   ▼        ▼          ▼          ▼          ▼          ▼
┌──────┐ ┌──────┐ ┌──────────┐ ┌──────┐ ┌──────┐ ┌──────────┐
│Collect│ │Normal│ │  Judge   │ │Score │ │Draft │ │ Approve  │
│      │ │ize   │ │          │ │      │ │      │ │ + Send   │
│      │ │      │ │ ┌──────┐ │ │      │ │      │ │          │
│      │ │      │ │ │Model │ │ │      │ │      │ │          │
│      │ │      │ │ │Bound.│ │ │      │ │      │ │          │
│      │ │      │ │ └──────┘ │ │      │ │      │ │          │
└──┬───┘ └──────┘ └──────────┘ └──────┘ └──┬───┘ └────┬─────┘
   │                                        │          │
   ▼                                        ▼          ▼
┌──────────────────┐              ┌──────────────────────────┐
│   Connectors     │              │       LLM Gateway        │
│  ┌────────────┐  │              │  ┌────────┐ ┌─────────┐  │
│  │  X API v2  │  │              │  │Claude/ │ │Fine-tune│  │
│  ├────────────┤  │              │  │GPT     │ │model    │  │
│  │ LinkedIn   │  │              │  ├────────┤ ├─────────┤  │
│  │ (v0.3)     │  │              │  │Fallback│ │TF-IDF   │  │
│  ├────────────┤  │              │  │(rules) │ │(offline) │  │
│  │ SocialData │  │              │  └────────┘ └─────────┘  │
│  │ (optional) │  │              └──────────────────────────┘
│  └────────────┘  │
└──────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────┐
│                      Storage Layer                            │
│  ┌──────────┐  ┌───────┐  ┌────────────┐  ┌──────────────┐  │
│  │ SQLite/  │  │ Redis │  │ Audit Log  │  │ Training     │  │
│  │ Postgres │  │ Cache │  │ (append)   │  │ Data Export  │  │
│  └──────────┘  └───────┘  └────────────┘  └──────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### File Tree

```
signalops/
├── pyproject.toml                  # Project metadata, dependencies
├── README.md                       # Setup guide, usage examples
├── LICENSE                         # MIT
├── .env.example                    # Required env vars template
├── .github/
│   └── workflows/
│       ├── ci.yml                  # Lint + typecheck + test
│       └── release.yml             # PyPI publish on tag
├── projects/                       # Example project configs
│   ├── spectra.yaml
│   └── salesense.yaml
├── src/
│   └── signalops/
│       ├── __init__.py
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── main.py             # Click app entry point
│       │   ├── project.py          # project set/list/init commands
│       │   ├── collect.py          # run collect
│       │   ├── judge.py            # run judge
│       │   ├── score.py            # run score
│       │   ├── draft.py            # draft replies
│       │   ├── approve.py          # approve/reject/edit queue
│       │   ├── send.py             # send approved
│       │   ├── export.py           # export training-data/stats
│       │   └── stats.py            # stats display
│       ├── connectors/
│       │   ├── __init__.py
│       │   ├── base.py             # Connector ABC
│       │   ├── x_api.py            # X API v2 connector
│       │   ├── x_auth.py           # OAuth 2.0 PKCE + 1.0a flows
│       │   ├── socialdata.py       # SocialData API (optional)
│       │   └── rate_limiter.py     # Sliding window + jitter
│       ├── pipeline/
│       │   ├── __init__.py
│       │   ├── orchestrator.py     # Pipeline runner
│       │   ├── collector.py        # Collect stage
│       │   ├── normalizer.py       # Normalize stage
│       │   ├── judge.py            # Judge stage (relevance)
│       │   ├── scorer.py           # Score stage (lead ranking)
│       │   ├── drafter.py          # Draft stage (outreach)
│       │   └── sender.py           # Send stage (with approval gate)
│       ├── models/
│       │   ├── __init__.py
│       │   ├── llm_gateway.py      # LLM abstraction (route to providers)
│       │   ├── providers/
│       │   │   ├── __init__.py
│       │   │   ├── base.py         # LLMProvider ABC
│       │   │   ├── openai.py       # OpenAI/GPT provider
│       │   │   ├── anthropic.py    # Claude provider
│       │   │   └── local.py        # vLLM/Ollama local provider
│       │   ├── judge_model.py      # RelevanceJudge interface + impls
│       │   ├── draft_model.py      # DraftGenerator interface + impls
│       │   └── fallback.py         # Rule-based/TF-IDF fallback
│       ├── storage/
│       │   ├── __init__.py
│       │   ├── database.py         # SQLAlchemy models + session
│       │   ├── migrations/         # Alembic migrations
│       │   ├── cache.py            # Redis cache wrapper
│       │   └── audit.py            # Append-only audit log
│       ├── config/
│       │   ├── __init__.py
│       │   ├── loader.py           # YAML config loader + validation
│       │   ├── schema.py           # Pydantic models for project.yaml
│       │   └── defaults.py         # Default values
│       ├── training/
│       │   ├── __init__.py
│       │   ├── exporter.py         # JSONL export for fine-tuning
│       │   ├── evaluator.py        # Offline eval runner
│       │   └── labeler.py          # Label collection helpers
│       └── notifications/
│           ├── __init__.py
│           ├── base.py             # Notifier ABC
│           ├── discord.py          # Discord webhook
│           └── slack.py            # Slack webhook
├── tests/
│   ├── conftest.py                 # Shared fixtures
│   ├── test_normalizer.py
│   ├── test_judge.py
│   ├── test_scorer.py
│   ├── test_drafter.py
│   ├── test_collector.py
│   ├── test_config.py
│   ├── test_rate_limiter.py
│   ├── test_exporter.py
│   ├── test_cli.py
│   └── fixtures/
│       ├── tweets.json             # Sample tweet payloads
│       ├── project_spectra.yaml
│       └── project_salesense.yaml
└── docs/
    └── api-reference.md            # Auto-generated from docstrings
```

### Module Boundaries & Interfaces

#### Connector Interface

```python
# src/signalops/connectors/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

@dataclass
class RawPost:
    platform: str           # "x", "linkedin", etc.
    platform_id: str        # Tweet ID (string, not int)
    author_id: str
    author_username: str
    author_display_name: str
    author_followers: int
    author_verified: bool
    text: str
    created_at: datetime
    language: str | None
    reply_to_id: str | None
    conversation_id: str | None
    metrics: dict           # {"likes": 5, "retweets": 2, "replies": 1, "views": 100}
    entities: dict           # {"urls": [...], "mentions": [...], "hashtags": [...]}
    raw_json: dict           # Full API response for this post

class Connector(ABC):
    @abstractmethod
    def search(self, query: str, since_id: str | None = None,
               max_results: int = 100) -> list[RawPost]:
        """Search for posts matching query. Returns newest first."""

    @abstractmethod
    def get_user(self, user_id: str) -> dict:
        """Fetch user profile by ID."""

    @abstractmethod
    def post_reply(self, in_reply_to_id: str, text: str) -> str:
        """Post a reply. Returns the new post's platform ID."""

    @abstractmethod
    def health_check(self) -> bool:
        """Verify API connectivity and auth."""
```

#### Judge Interface (Model Boundary)

```python
# src/signalops/models/judge_model.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class Judgment:
    label: str              # "relevant", "irrelevant", "maybe"
    confidence: float       # 0.0 - 1.0
    reasoning: str          # Why this label was chosen
    model_id: str           # "claude-sonnet-4-6", "ft-relevance-v2", "tfidf-fallback"
    latency_ms: float

class RelevanceJudge(ABC):
    @abstractmethod
    def judge(self, post_text: str, author_bio: str,
              project_context: dict) -> Judgment:
        """Judge whether a post is relevant to the project."""

    @abstractmethod
    def judge_batch(self, items: list[dict]) -> list[Judgment]:
        """Batch judgment for efficiency."""
```

#### Draft Generator Interface

```python
# src/signalops/models/draft_model.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class Draft:
    text: str               # The draft reply text
    tone: str               # "helpful", "curious", "expert"
    model_id: str
    template_used: str | None

class DraftGenerator(ABC):
    @abstractmethod
    def generate(self, post_text: str, author_context: str,
                 project_context: dict, persona: dict) -> Draft:
        """Generate a reply draft for a relevant post."""
```

#### Pipeline Stage Interface

```python
# Each pipeline stage follows this contract
class PipelineStage(ABC):
    @abstractmethod
    def run(self, inputs: list[dict], config: ProjectConfig) -> list[dict]:
        """Process inputs, return outputs. Pure function over data."""

    @abstractmethod
    def dry_run(self, inputs: list[dict], config: ProjectConfig) -> list[dict]:
        """Preview what would happen without side effects."""
```

---

## 4. Data Model

### Entity-Relationship Overview

```
raw_posts ──1:1──> normalized_posts ──1:N──> judgments
                                     ──1:N──> scores
                                     ──1:N──> drafts ──1:1──> approvals
                                                       ──1:N──> outcomes

projects ──1:N──> queries
         ──1:N──> all pipeline tables (via project_id FK)

audit_logs (append-only, references any entity)
```

### Table Definitions (SQLAlchemy)

```python
# src/signalops/storage/database.py
from sqlalchemy import (Column, String, Integer, Float, Boolean, DateTime,
                        Text, JSON, ForeignKey, UniqueConstraint, Index,
                        Enum as SAEnum, func)
from sqlalchemy.orm import DeclarativeBase, relationship
import enum

class Base(DeclarativeBase):
    pass

# ── Projects ──

class Project(Base):
    __tablename__ = "projects"

    id          = Column(String(64), primary_key=True)       # slug: "spectra"
    name        = Column(String(256), nullable=False)        # "Spectra AI"
    config_path = Column(String(1024), nullable=False)       # path to project.yaml
    config_hash = Column(String(64))                          # SHA-256 of config for change detection
    created_at  = Column(DateTime, server_default=func.now())
    updated_at  = Column(DateTime, onupdate=func.now())
    is_active   = Column(Boolean, default=True)

# ── Raw Posts ──

class RawPost(Base):
    __tablename__ = "raw_posts"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    project_id      = Column(String(64), ForeignKey("projects.id"), nullable=False)
    platform        = Column(String(32), nullable=False)      # "x"
    platform_id     = Column(String(64), nullable=False)      # Tweet ID
    collected_at    = Column(DateTime, server_default=func.now())
    query_used      = Column(Text)                             # The search query that found this
    raw_json        = Column(JSON, nullable=False)             # Full API response

    __table_args__ = (
        UniqueConstraint("platform", "platform_id", "project_id",
                         name="uq_raw_post_platform"),
        Index("ix_raw_post_project_collected", "project_id", "collected_at"),
    )

# ── Normalized Posts ──

class NormalizedPost(Base):
    __tablename__ = "normalized_posts"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    raw_post_id         = Column(Integer, ForeignKey("raw_posts.id"), unique=True, nullable=False)
    project_id          = Column(String(64), ForeignKey("projects.id"), nullable=False)
    platform            = Column(String(32), nullable=False)
    platform_id         = Column(String(64), nullable=False)
    author_id           = Column(String(64), nullable=False)
    author_username     = Column(String(256))
    author_display_name = Column(String(256))
    author_followers    = Column(Integer, default=0)
    author_verified     = Column(Boolean, default=False)
    text_original       = Column(Text, nullable=False)
    text_cleaned        = Column(Text, nullable=False)        # URLs stripped, normalized whitespace
    language            = Column(String(8))                    # ISO 639-1
    created_at          = Column(DateTime, nullable=False)     # When the post was published
    reply_to_id         = Column(String(64))
    conversation_id     = Column(String(64))
    likes               = Column(Integer, default=0)
    retweets            = Column(Integer, default=0)
    replies             = Column(Integer, default=0)
    views               = Column(Integer, default=0)
    hashtags            = Column(JSON)                         # ["ai", "saas"]
    mentions            = Column(JSON)                         # ["@user1"]
    urls                = Column(JSON)                         # ["https://..."]

    __table_args__ = (
        Index("ix_norm_project_author", "project_id", "author_id"),
        Index("ix_norm_project_created", "project_id", "created_at"),
    )

# ── Judgments ──

class JudgmentLabel(enum.Enum):
    RELEVANT = "relevant"
    IRRELEVANT = "irrelevant"
    MAYBE = "maybe"

class Judgment(Base):
    __tablename__ = "judgments"

    id                = Column(Integer, primary_key=True, autoincrement=True)
    normalized_post_id = Column(Integer, ForeignKey("normalized_posts.id"), nullable=False)
    project_id        = Column(String(64), ForeignKey("projects.id"), nullable=False)
    label             = Column(SAEnum(JudgmentLabel), nullable=False)
    confidence        = Column(Float, nullable=False)         # 0.0 - 1.0
    reasoning         = Column(Text)                           # LLM explanation
    model_id          = Column(String(128), nullable=False)   # "claude-sonnet-4-6", "ft-v2"
    model_version     = Column(String(64))                     # "20250217"
    latency_ms        = Column(Float)
    created_at        = Column(DateTime, server_default=func.now())

    # Human correction (nullable — only set if human overrides)
    human_label       = Column(SAEnum(JudgmentLabel))
    human_corrected_at = Column(DateTime)
    human_reason      = Column(Text)

    __table_args__ = (
        Index("ix_judgment_project_label", "project_id", "label"),
    )

# ── Scores ──

class Score(Base):
    __tablename__ = "scores"

    id                = Column(Integer, primary_key=True, autoincrement=True)
    normalized_post_id = Column(Integer, ForeignKey("normalized_posts.id"), nullable=False)
    project_id        = Column(String(64), ForeignKey("projects.id"), nullable=False)
    total_score       = Column(Float, nullable=False)          # 0-100
    components        = Column(JSON, nullable=False)           # {"relevance": 30, "authority": 25, ...}
    scoring_version   = Column(String(64), nullable=False)     # "v1-weighted"
    created_at        = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_score_project_total", "project_id", "total_score"),
    )

# ── Drafts ──

class DraftStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    EDITED = "edited"       # Approved with changes
    REJECTED = "rejected"
    SENT = "sent"
    FAILED = "failed"

class Draft(Base):
    __tablename__ = "drafts"

    id                = Column(Integer, primary_key=True, autoincrement=True)
    normalized_post_id = Column(Integer, ForeignKey("normalized_posts.id"), nullable=False)
    project_id        = Column(String(64), ForeignKey("projects.id"), nullable=False)
    text_generated    = Column(Text, nullable=False)          # LLM output
    text_final        = Column(Text)                           # After human edit (null if not edited)
    tone              = Column(String(64))                     # "helpful", "curious", "expert"
    template_used     = Column(String(128))                    # Template ID from config
    model_id          = Column(String(128), nullable=False)
    status            = Column(SAEnum(DraftStatus), default=DraftStatus.PENDING)
    created_at        = Column(DateTime, server_default=func.now())
    approved_at       = Column(DateTime)
    sent_at           = Column(DateTime)
    sent_post_id      = Column(String(64))                     # ID of our reply on the platform

    __table_args__ = (
        Index("ix_draft_project_status", "project_id", "status"),
    )

# ── Outcomes ──

class OutcomeType(enum.Enum):
    REPLY_RECEIVED = "reply_received"    # They replied to our reply
    LIKE_RECEIVED = "like_received"      # They liked our reply
    FOLLOW_RECEIVED = "follow_received"  # They followed us
    PROFILE_CLICK = "profile_click"      # Inferred from analytics
    LINK_CLICK = "link_click"            # If we included a tracked link
    BOOKING = "booking"                   # Downstream conversion
    NEGATIVE = "negative"                 # They blocked/reported us

class Outcome(Base):
    __tablename__ = "outcomes"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    draft_id    = Column(Integer, ForeignKey("drafts.id"), nullable=False)
    project_id  = Column(String(64), ForeignKey("projects.id"), nullable=False)
    outcome_type = Column(SAEnum(OutcomeType), nullable=False)
    details     = Column(JSON)                                 # Flexible metadata
    observed_at = Column(DateTime, server_default=func.now())

# ── Audit Logs ──

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    project_id  = Column(String(64))
    action      = Column(String(128), nullable=False)          # "collect", "judge", "approve", "send"
    entity_type = Column(String(64))                           # "raw_post", "draft", etc.
    entity_id   = Column(Integer)
    details     = Column(JSON)                                 # Arbitrary context
    user        = Column(String(128))                          # CLI user or "system"
    timestamp   = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_audit_project_action", "project_id", "action"),
        Index("ix_audit_timestamp", "timestamp"),
    )
```

---

## 5. Config / Adapter Design

### Schema (`project.yaml`)

```python
# src/signalops/config/schema.py
from pydantic import BaseModel, Field
from typing import Optional

class QueryConfig(BaseModel):
    text: str                              # X API search query syntax
    label: str                             # Human-readable name
    enabled: bool = True
    max_results_per_run: int = 100

class ICPConfig(BaseModel):
    """Ideal Customer Profile"""
    min_followers: int = 100
    max_followers: int | None = None       # None = no cap
    verified_only: bool = False
    languages: list[str] = ["en"]
    exclude_bios_containing: list[str] = []
    prefer_bios_containing: list[str] = []

class RelevanceRubric(BaseModel):
    system_prompt: str                      # Injected into judge LLM call
    positive_signals: list[str]            # Things that make a post relevant
    negative_signals: list[str]            # Things that make a post irrelevant
    keywords_required: list[str] = []       # At least one must appear (safety net)
    keywords_excluded: list[str] = []       # Auto-reject if any appear

class ScoringWeights(BaseModel):
    relevance_judgment: float = 0.35        # Weight of judge confidence
    author_authority: float = 0.25          # Followers, verified, bio match
    engagement_signals: float = 0.15        # Likes, replies, views
    recency: float = 0.15                   # Newer = higher
    intent_strength: float = 0.10           # Explicit ask vs. passive mention

class PersonaConfig(BaseModel):
    name: str                               # Bot persona name
    role: str                               # e.g., "technical advisor"
    tone: str                               # "helpful", "curious", "expert"
    voice_notes: str                        # Free-text style guide
    example_reply: str                      # One-shot example for LLM

class TemplateConfig(BaseModel):
    id: str
    name: str
    template: str                           # Jinja2 template with {{variables}}
    use_when: str                           # Condition description

class NotificationConfig(BaseModel):
    enabled: bool = False
    min_score_to_notify: int = 70
    discord_webhook: str | None = None
    slack_webhook: str | None = None

class ProjectConfig(BaseModel):
    project_id: str
    project_name: str
    description: str
    product_url: str | None = None
    queries: list[QueryConfig]
    icp: ICPConfig = ICPConfig()
    relevance: RelevanceRubric
    scoring: ScoringWeights = ScoringWeights()
    persona: PersonaConfig
    templates: list[TemplateConfig] = []
    notifications: NotificationConfig = NotificationConfig()
    rate_limits: dict = {"max_replies_per_hour": 5, "max_replies_per_day": 20}
    llm: dict = {"judge_model": "claude-sonnet-4-6", "draft_model": "claude-sonnet-4-6"}
```

### Example: `projects/spectra.yaml`

```yaml
project_id: spectra
project_name: "Spectra AI"
description: >
  Spectra is an AI-powered code review tool that catches bugs,
  security issues, and performance problems before they ship.
product_url: "https://spectra.dev"

queries:
  - text: '"code review" (slow OR painful OR annoying OR "takes forever") -is:retweet lang:en'
    label: "Code review pain points"
  - text: '"pull request" (bugs OR "missed bug" OR "slipped through") -is:retweet lang:en'
    label: "Bugs slipping through PRs"
  - text: '("looking for" OR "anyone recommend") ("code review tool" OR "PR automation") -is:retweet lang:en'
    label: "Active tool search"
  - text: '(sonarqube OR codeclimate OR "code rabbit" OR snyk) (slow OR expensive OR "switching from") -is:retweet lang:en'
    label: "Competitor dissatisfaction"

icp:
  min_followers: 200
  languages: ["en"]
  exclude_bios_containing: ["bot", "giveaway", "follow back", "crypto shill"]
  prefer_bios_containing: ["engineer", "developer", "CTO", "tech lead", "devops", "founder"]

relevance:
  system_prompt: >
    You are a relevance judge for Spectra AI, a code review tool.
    Evaluate whether this tweet indicates the author might benefit from
    an AI-powered code review tool. Consider: Are they expressing pain
    with code reviews? Looking for tooling? Discussing PR quality issues?
    A relevant tweet shows genuine need or active interest, not just
    a passing mention of the topic.
  positive_signals:
    - Expressing frustration with manual code review processes
    - Asking for tool recommendations in the code review space
    - Discussing bugs that escaped code review
    - Mentioning they're evaluating or switching code review tools
    - Technical leaders discussing team productivity around PRs
  negative_signals:
    - Just sharing a blog post about code review in general
    - Recruiting/hiring posts mentioning code review as a skill
    - Jokes or memes about code review without genuine pain
    - Bot-like or spam accounts discussing the topic
    - Posts about reviewing code in an educational context only
  keywords_required: []
  keywords_excluded: ["hiring", "job", "we're looking for", "apply now"]

scoring:
  relevance_judgment: 0.35
  author_authority: 0.25
  engagement_signals: 0.15
  recency: 0.15
  intent_strength: 0.10

persona:
  name: "Alex from Spectra"
  role: "developer advocate"
  tone: "helpful"
  voice_notes: >
    Be genuinely helpful first. Lead with empathy for their problem.
    Only mention Spectra if it's truly relevant — never force a plug.
    Use technical language appropriate for developers. Keep it under
    200 characters. No hashtags. No emojis unless the original poster
    used them. Sound human, not corporate.
  example_reply: >
    Totally feel that pain — we built Spectra specifically for this.
    It catches the stuff humans miss in PRs. Happy to show you a demo
    if you're evaluating options.

templates:
  - id: pain_point
    name: "Pain Point Response"
    template: >
      {{empathy_statement}} — {{value_prop}}. {{soft_cta}}
    use_when: "Author is expressing frustration with current workflow"
  - id: tool_search
    name: "Active Search Response"
    template: >
      {{relevant_answer}} — we built {{product}} for exactly this. {{proof_point}}
    use_when: "Author is actively looking for a tool recommendation"

notifications:
  enabled: true
  min_score_to_notify: 75
  discord_webhook: "${DISCORD_WEBHOOK_SPECTRA}"

rate_limits:
  max_replies_per_hour: 5
  max_replies_per_day: 20

llm:
  judge_model: "claude-sonnet-4-6"
  draft_model: "claude-sonnet-4-6"
  temperature: 0.3
```

### Example: `projects/salesense.yaml`

```yaml
project_id: salesense
project_name: "SaleSense"
description: >
  SaleSense is a conversational AI platform that qualifies website
  visitors in real-time and books meetings automatically.
product_url: "https://salesense.io"

queries:
  - text: '"website visitors" (qualify OR "convert" OR "losing leads") -is:retweet lang:en'
    label: "Lead qualification pain"
  - text: '("chat widget" OR "live chat" OR "chatbot") (bad OR terrible OR "doesn''t work" OR replacing) -is:retweet lang:en'
    label: "Chat tool frustration"
  - text: '("looking for" OR "anyone use") ("lead qualification" OR "visitor engagement" OR "meeting scheduler") -is:retweet lang:en'
    label: "Active tool search"
  - text: '(drift OR intercom OR qualified.com OR "calendly bot") (expensive OR "switching from" OR alternative) -is:retweet lang:en'
    label: "Competitor dissatisfaction"

icp:
  min_followers: 150
  languages: ["en"]
  exclude_bios_containing: ["bot", "giveaway", "follow back"]
  prefer_bios_containing: ["sales", "revenue", "growth", "founder", "CEO", "VP sales", "SDR", "BDR", "marketing"]

relevance:
  system_prompt: >
    You are a relevance judge for SaleSense, a conversational AI platform
    that qualifies website visitors and books meetings. Evaluate whether
    this tweet indicates the author might benefit from automated visitor
    qualification. Consider: Are they struggling with lead conversion?
    Frustrated with their current chat tool? Looking for ways to automate
    meeting booking?
  positive_signals:
    - Expressing frustration with manual lead qualification
    - Discussing poor website visitor conversion rates
    - Asking for chatbot or live chat recommendations
    - Mentioning they're losing leads because response time is too slow
    - Sales/marketing leaders discussing pipeline efficiency
  negative_signals:
    - Generic marketing advice about websites
    - Posts about building chatbots as a developer
    - Casual mentions of "chat" unrelated to business
    - Crypto/Web3 bot discussions
  keywords_required: []
  keywords_excluded: ["hiring", "job posting", "NFT", "crypto"]

scoring:
  relevance_judgment: 0.30
  author_authority: 0.30
  engagement_signals: 0.10
  recency: 0.15
  intent_strength: 0.15

persona:
  name: "Jordan from SaleSense"
  role: "growth consultant"
  tone: "curious"
  voice_notes: >
    Lead with genuine curiosity about their situation. Ask a question
    that shows you understand their problem. Only mention SaleSense
    if they're actively looking for solutions. Keep replies conversational
    and under 220 characters. No corporate speak.
  example_reply: >
    Curious — what's your current flow for qualifying visitors? We've
    seen teams cut response time from hours to seconds with conversational
    AI. Happy to share what's working.

templates:
  - id: pain_point
    name: "Pain Point Response"
    template: >
      {{curious_question}} — {{relevant_insight}}. {{soft_cta}}
    use_when: "Author is expressing frustration with lead qualification or chat tools"
  - id: competitor_switch
    name: "Competitor Switch Response"
    template: >
      {{empathy}} — a lot of teams are making that move. {{differentiator}}
    use_when: "Author is switching from or frustrated with a competitor"

notifications:
  enabled: true
  min_score_to_notify: 70
  slack_webhook: "${SLACK_WEBHOOK_SALESENSE}"

rate_limits:
  max_replies_per_hour: 4
  max_replies_per_day: 15

llm:
  judge_model: "claude-sonnet-4-6"
  draft_model: "claude-sonnet-4-6"
  temperature: 0.4
```

### Config Loading

```python
# src/signalops/config/loader.py
import yaml
import os
import hashlib
from pathlib import Path
from .schema import ProjectConfig

def load_project(path: str | Path) -> ProjectConfig:
    """Load and validate a project.yaml file."""
    path = Path(path)
    with open(path) as f:
        raw = yaml.safe_load(f)

    # Resolve environment variables in string values
    raw = _resolve_env_vars(raw)

    config = ProjectConfig(**raw)
    return config

def _resolve_env_vars(obj):
    """Recursively replace ${VAR} with os.environ[VAR]."""
    if isinstance(obj, str):
        if obj.startswith("${") and obj.endswith("}"):
            var = obj[2:-1]
            return os.environ.get(var, obj)
        return obj
    if isinstance(obj, dict):
        return {k: _resolve_env_vars(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_env_vars(v) for v in obj]
    return obj

def config_hash(path: str | Path) -> str:
    """SHA-256 of config file for change detection."""
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()
```

---

## 6. LLM Training & Learning Roadmap

### Phase 1: Collect Training Data (MVP onward)

Every time a human interacts with the pipeline, we capture training signal:

| Interaction | Training Signal | Dataset |
|-------------|----------------|---------|
| Human corrects a judgment (relevant→irrelevant or vice versa) | Gold label for relevance classifier | `judgments` table where `human_label IS NOT NULL` |
| Human approves a draft as-is | Positive example for draft quality | `drafts` where `status = 'approved'` and `text_final IS NULL` |
| Human edits a draft then approves | Preference pair (edited > original) | `drafts` where `status = 'edited'` → DPO pair |
| Human rejects a draft | Negative example for draft quality | `drafts` where `status = 'rejected'` |
| Outcome tracking (reply received, follow, booking) | Reward signal for outreach quality | `outcomes` table |

### Phase 2: Export Training Data

#### JSONL Export Command

```bash
signalops export training-data --project spectra --type judgments --format openai --output judgments.jsonl
signalops export training-data --project spectra --type drafts --format dpo --output preferences.jsonl
```

#### Judgment Export Format (Classification Fine-Tuning)

```jsonl
{"messages": [{"role": "system", "content": "You are a relevance judge for Spectra AI, a code review tool. Evaluate whether this tweet indicates the author might benefit from an AI-powered code review tool. Respond with JSON: {\"label\": \"relevant\" or \"irrelevant\", \"confidence\": 0.0-1.0, \"reasoning\": \"...\"}"}, {"role": "user", "content": "Tweet: 'Just spent 3 hours reviewing a PR that should have taken 30 minutes. Half the comments were about formatting. There has to be a better way.'\nAuthor bio: 'Senior engineer @BigCorp. Building distributed systems.'\nAuthor followers: 2340"}, {"role": "assistant", "content": "{\"label\": \"relevant\", \"confidence\": 0.92, \"reasoning\": \"Author is expressing clear frustration with manual code review process, specifically about time waste and low-signal comments. They are a senior engineer at a real company (not a bot) and explicitly signal they want a better solution.\"}"}]}
```

#### Draft Preference Export Format (DPO Fine-Tuning)

```jsonl
{"prompt": "Write a helpful reply to this tweet as Alex from Spectra (developer advocate, helpful tone).\n\nTweet: 'Just spent 3 hours reviewing a PR that should have taken 30 minutes.'\nAuthor: Senior engineer, 2340 followers.\nContext: Spectra is an AI code review tool.", "chosen": "3 hours for formatting nits is brutal. We built Spectra to auto-catch that stuff so reviews focus on real logic issues. Want a demo?", "rejected": "Have you tried Spectra? It's an AI-powered code review tool that can help speed up your PR reviews! Check it out at spectra.dev #codeReview #AI"}
```

#### Exporter Implementation

```python
# src/signalops/training/exporter.py
import json
from datetime import datetime
from pathlib import Path

class TrainingDataExporter:
    def __init__(self, db_session):
        self.db = db_session

    def export_judgments(self, project_id: str, format: str = "openai",
                        output: str = "judgments.jsonl") -> dict:
        """Export human-corrected judgments as fine-tuning data."""
        judgments = self.db.query(Judgment).filter(
            Judgment.project_id == project_id,
            Judgment.human_label.isnot(None)
        ).all()

        records = []
        for j in judgments:
            post = j.normalized_post
            project = self.db.query(Project).get(project_id)

            record = {
                "messages": [
                    {"role": "system", "content": self._get_judge_system_prompt(project)},
                    {"role": "user", "content": self._format_judge_input(post)},
                    {"role": "assistant", "content": json.dumps({
                        "label": j.human_label.value,
                        "confidence": 0.95,  # Human labels get high confidence
                        "reasoning": j.human_reason or j.reasoning
                    })}
                ]
            }
            records.append(record)

        with open(output, "w") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        return {"records": len(records), "output": output}

    def export_draft_preferences(self, project_id: str,
                                  output: str = "preferences.jsonl") -> dict:
        """Export draft edits as DPO preference pairs."""
        drafts = self.db.query(Draft).filter(
            Draft.project_id == project_id,
            Draft.status == DraftStatus.EDITED,
            Draft.text_final.isnot(None)
        ).all()

        records = []
        for d in drafts:
            post = d.normalized_post
            record = {
                "prompt": self._format_draft_prompt(post, project_id),
                "chosen": d.text_final,      # Human-edited version
                "rejected": d.text_generated  # Original LLM output
            }
            records.append(record)

        with open(output, "w") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        return {"records": len(records), "output": output}
```

### Phase 3: Offline Evaluation

#### Eval Command

```bash
signalops eval judge --project spectra --test-set tests/fixtures/eval_set.jsonl
```

#### Eval Runner

```python
# src/signalops/training/evaluator.py
from sklearn.metrics import classification_report, matthews_corrcoef
import json

class JudgeEvaluator:
    def __init__(self, judge: RelevanceJudge):
        self.judge = judge

    def evaluate(self, test_set_path: str, project_context: dict) -> dict:
        """Run eval on a JSONL test set with gold labels."""
        y_true, y_pred, confidences = [], [], []

        with open(test_set_path) as f:
            for line in f:
                item = json.loads(line)
                result = self.judge.judge(
                    post_text=item["text"],
                    author_bio=item.get("author_bio", ""),
                    project_context=project_context
                )
                y_true.append(item["gold_label"])
                y_pred.append(result.label)
                confidences.append(result.confidence)

        report = classification_report(
            y_true, y_pred,
            target_names=["irrelevant", "maybe", "relevant"],
            output_dict=True
        )
        mcc = matthews_corrcoef(
            [1 if y == "relevant" else 0 for y in y_true],
            [1 if y == "relevant" else 0 for y in y_pred]
        )

        return {
            "classification_report": report,
            "mcc": mcc,
            "mean_confidence": sum(confidences) / len(confidences),
            "n_examples": len(y_true),
            "model_id": self.judge.__class__.__name__
        }
```

#### Target Metrics

| Metric | MVP Baseline (prompt-only) | v0.2 Target (+ few-shot) | v0.3 Target (fine-tuned) |
|--------|---------------------------|--------------------------|--------------------------|
| Precision (relevant) | > 0.70 | > 0.80 | > 0.90 |
| Recall (relevant) | > 0.60 | > 0.75 | > 0.85 |
| F1 (relevant) | > 0.65 | > 0.77 | > 0.87 |
| MCC | > 0.50 | > 0.65 | > 0.80 |
| Avg latency | < 2s | < 2s | < 200ms (local model) |

### Phase 4: Deploy Fine-Tuned Model

The `RelevanceJudge` interface allows hot-swapping:

```python
# In orchestrator.py, based on config
if config.llm.judge_model.startswith("ft:"):
    judge = OpenAIFineTunedJudge(model_id=config.llm.judge_model)
elif config.llm.judge_model.startswith("local:"):
    judge = LocalVLLMJudge(endpoint=config.llm.judge_endpoint)
else:
    judge = LLMPromptJudge(model=config.llm.judge_model)
```

#### A/B Testing (v0.3)

```python
class ABTestJudge(RelevanceJudge):
    def __init__(self, primary: RelevanceJudge, canary: RelevanceJudge,
                 canary_pct: float = 0.1):
        self.primary = primary
        self.canary = canary
        self.canary_pct = canary_pct

    def judge(self, post_text, author_bio, project_context):
        import random
        if random.random() < self.canary_pct:
            result = self.canary.judge(post_text, author_bio, project_context)
            result.model_id = f"canary:{result.model_id}"
            return result
        return self.primary.judge(post_text, author_bio, project_context)
```

### Phase 5: Preference Learning for Drafts (v0.3+)

**Collection flow:**
1. For each approved draft, store `(prompt, chosen=text_final, rejected=text_generated)` as a DPO pair
2. Also collect KTO data: `approved` → label=true, `rejected` → label=false
3. Export via `signalops export training-data --type drafts --format dpo`

**Training options (in order of complexity):**
1. **KTO** (simplest): Unpaired good/bad signals. Use when < 500 preference pairs.
2. **DPO** (recommended): Paired preferences from edits. Use when > 500 pairs.
3. **RLHF/PPO** (advanced): Full reward model + RL. Only if DPO plateaus.

**Fine-tuning stack:**
- **Cloud:** OpenAI fine-tuning API (`gpt-4o-mini`) or Anthropic fine-tuning (`claude-haiku-4-5`)
- **Self-hosted:** Unsloth + TRL `DPOTrainer` on Llama 3.1 8B → serve via vLLM

**References:**
- Rafailov et al., "Direct Preference Optimization," NeurIPS 2023
- Ethayarajh et al., "KTO: Model Alignment as Prospect Theoretic Optimization," 2024
- OpenAI Fine-Tuning Guide: platform.openai.com/docs/guides/fine-tuning
- Anthropic Fine-Tuning Docs: docs.anthropic.com/en/docs/build-with-claude/fine-tuning
- Hugging Face TRL: huggingface.co/docs/trl
- Snorkel (weak supervision): snorkel.org
- Argilla (annotation): argilla.io

---

## 7. Implementation Plan

### 7-Day Sprint (MVP)

#### Day 1: Foundation

**Files to create:**
- `pyproject.toml` — dependencies: click, sqlalchemy, alembic, pydantic, httpx, pyyaml, rich
- `src/signalops/__init__.py`
- `src/signalops/config/schema.py` — Pydantic models
- `src/signalops/config/loader.py` — YAML loader with env var resolution
- `src/signalops/config/defaults.py` — Default values
- `src/signalops/storage/database.py` — SQLAlchemy models
- `projects/spectra.yaml` — First example config
- `.env.example`

**Tests:**
- `tests/test_config.py` — Load/validate both example configs, test env var resolution, test invalid configs
- `tests/conftest.py` — SQLite in-memory DB fixture

**Acceptance criteria:**
- `pytest tests/test_config.py` passes
- Both example YAML files parse and validate
- DB tables create successfully in SQLite

#### Day 2: Connectors + Collection

**Files to create:**
- `src/signalops/connectors/base.py` — Connector ABC + RawPost dataclass
- `src/signalops/connectors/x_api.py` — X API v2 search + reply
- `src/signalops/connectors/x_auth.py` — OAuth 2.0 PKCE flow
- `src/signalops/connectors/rate_limiter.py` — Sliding window + jitter
- `src/signalops/pipeline/collector.py` — Collect stage

**Tests:**
- `tests/test_collector.py` — Mock X API responses, test deduplication, test rate limiting
- `tests/test_rate_limiter.py` — Token bucket, header-based updates, backoff
- `tests/fixtures/tweets.json` — 20 sample tweet payloads

**Acceptance criteria:**
- Collector fetches and stores tweets in `raw_posts` table
- Deduplication works (same tweet ID + project → no duplicate)
- Rate limiter respects window and jitter

#### Day 3: Normalize + Judge

**Files to create:**
- `src/signalops/pipeline/normalizer.py` — Clean text, extract entities, language detection
- `src/signalops/models/llm_gateway.py` — LLM abstraction
- `src/signalops/models/providers/base.py` — LLMProvider ABC
- `src/signalops/models/providers/anthropic.py` — Claude provider
- `src/signalops/models/providers/openai.py` — OpenAI provider
- `src/signalops/models/judge_model.py` — RelevanceJudge interface + LLMPromptJudge
- `src/signalops/models/fallback.py` — Rule-based keyword fallback
- `src/signalops/pipeline/judge.py` — Judge stage

**Tests:**
- `tests/test_normalizer.py` — URL stripping, whitespace normalization, entity extraction
- `tests/test_judge.py` — Mock LLM responses, test structured output parsing, test fallback

**Acceptance criteria:**
- Normalizer produces clean text from raw tweets
- Judge produces `Judgment` with label/confidence/reasoning
- Fallback classifier works when LLM is unavailable

#### Day 4: Score + Draft

**Files to create:**
- `src/signalops/pipeline/scorer.py` — Weighted scoring function
- `src/signalops/models/draft_model.py` — DraftGenerator interface + LLM implementation
- `src/signalops/pipeline/drafter.py` — Draft stage

**Tests:**
- `tests/test_scorer.py` — Scoring math, weight validation, edge cases (0 followers, etc.)
- `tests/test_drafter.py` — Mock LLM draft generation, character limit enforcement

**Acceptance criteria:**
- Scores are 0-100 with component breakdown
- Drafts respect persona, tone, and character limits
- Scoring weights from config are applied correctly

#### Day 5: CLI + Approval + Send

**Files to create:**
- `src/signalops/cli/main.py` — Click app with group commands
- `src/signalops/cli/project.py` — `project set/list/init`
- `src/signalops/cli/collect.py` — `run collect`
- `src/signalops/cli/judge.py` — `run judge`
- `src/signalops/cli/score.py` — `run score`
- `src/signalops/cli/draft.py` — `draft replies`
- `src/signalops/cli/approve.py` — `approve` (interactive)
- `src/signalops/cli/send.py` — `send` (with --dry-run)
- `src/signalops/pipeline/sender.py` — Send stage with approval gate
- `src/signalops/storage/audit.py` — Audit logger

**Tests:**
- `tests/test_cli.py` — Click CliRunner tests for each command

**Acceptance criteria:**
- Full pipeline runnable via CLI: `signalops run collect && signalops run judge && signalops run score && signalops draft replies && signalops approve && signalops send`
- `--dry-run` on send does not actually post
- Audit log captures every action

#### Day 6: Orchestrator + End-to-End

**Files to create:**
- `src/signalops/pipeline/orchestrator.py` — Full pipeline runner (`signalops run all`)
- `src/signalops/cli/stats.py` — Basic stats display

**Tests:**
- End-to-end test with mocked X API: collect → normalize → judge → score → draft → approve → send
- Stats command displays correct counts

**Acceptance criteria:**
- `signalops run all --project spectra --dry-run` completes full pipeline
- Stats show collected/judged/scored/drafted/approved/sent counts

#### Day 7: Polish + Docs + CI

**Files to create:**
- `.github/workflows/ci.yml` — Lint + typecheck + test
- `README.md` — Setup guide, quickstart, architecture overview
- `projects/salesense.yaml` — Second example config

**Tasks:**
- Run full linting pass (ruff)
- Run mypy type checking
- Write README with install instructions, quickstart, and CLI reference
- Create `.env.example` with all required variables documented
- Test on clean install

**Acceptance criteria:**
- CI pipeline passes (lint + typecheck + all tests)
- README is sufficient for a new developer to set up and run the tool
- Both example projects work end-to-end in dry-run mode

### 30-Day Plan

| Week | Milestone | Key Deliverables |
|------|-----------|-----------------|
| **Week 1** | MVP (above) | Working CLI, full pipeline, 2 example projects, CI |
| **Week 2** | Learning Loop | Outcome tracking, human correction flow, `export training-data` command, offline eval runner, eval test fixtures |
| **Week 3** | Scale + UX | Redis caching layer, Filtered Stream support (Pro tier), rich TUI for stats/approval queue, notification webhooks (Discord/Slack), multi-project switching |
| **Week 4** | Harden + Ship | Error handling hardening, retry logic on all API calls, rate limit compliance testing, documentation site, PyPI packaging, demo video, landing page |

---

## 8. CLI Spec

### Command Tree

```
signalops
├── project
│   ├── set <name>           # Set active project
│   ├── list                 # List all projects
│   └── init                 # Create new project.yaml interactively
├── run
│   ├── collect              # Collect tweets matching queries
│   ├── judge                # Judge relevance of collected tweets
│   ├── score                # Score judged tweets
│   ├── all                  # Run collect → judge → score pipeline
│   └── draft                # Generate reply drafts for top-scored
├── queue
│   ├── list                 # Show pending drafts
│   ├── approve <id>         # Approve a draft
│   ├── edit <id>            # Edit then approve a draft
│   ├── reject <id>          # Reject a draft
│   └── send                 # Send all approved drafts
├── correct <judgment_id>    # Correct a judgment (for training data)
├── export
│   ├── training-data        # Export JSONL for fine-tuning
│   └── csv                  # Export leads as CSV
├── eval
│   └── judge                # Run offline evaluation
├── stats                    # Show pipeline stats
└── auth
    └── login                # OAuth flow for X API
```

### Global Flags

```
--project, -p <name>     Override active project
--dry-run                Preview without side effects
--verbose, -v            Debug logging
--format [table|json]    Output format (default: table)
```

### Example CLI Sessions

#### Setup

```bash
$ signalops auth login
Opening browser for X OAuth authorization...
✓ Authenticated as @yourhandle (Basic tier)
  Access token stored in ~/.signalops/credentials.json

$ signalops project set spectra
✓ Active project: Spectra AI (spectra)
  4 queries configured
  ICP: min 200 followers, en only
```

#### Collect + Judge + Score

```bash
$ signalops run all --project spectra
⠋ Collecting tweets...
  Query 1/4: "Code review pain points" → 47 new tweets
  Query 2/4: "Bugs slipping through PRs" → 23 new tweets
  Query 3/4: "Active tool search" → 8 new tweets
  Query 4/4: "Competitor dissatisfaction" → 12 new tweets
✓ Collected 90 tweets (34 duplicates skipped)

⠋ Judging relevance...
  Relevant: 31 | Irrelevant: 52 | Maybe: 7
✓ Judged 90 tweets (avg confidence: 0.84)

⠋ Scoring leads...
✓ Scored 31 relevant tweets

  Top 5 Leads:
  ┌────┬───────┬────────────────┬──────────────────────────────────────────┬───────┐
  │ #  │ Score │ Author         │ Tweet                                    │ Query │
  ├────┼───────┼────────────────┼──────────────────────────────────────────┼───────┤
  │ 1  │ 92    │ @techleadSara  │ "3 hours reviewing a PR that should..." │ Pain  │
  │ 2  │ 87    │ @devops_mike   │ "Anyone recommend a good code review.." │ Search│
  │ 3  │ 83    │ @ctojennifer   │ "Bugs keep slipping through our PRs..." │ Bugs  │
  │ 4  │ 78    │ @eng_david     │ "Switching from SonarQube, too slow..." │ Comp. │
  │ 5  │ 74    │ @senior_dev_j  │ "Code review bottleneck is killing..." │ Pain  │
  └────┴───────┴────────────────┴──────────────────────────────────────────┴───────┘
```

#### Draft + Approve + Send

```bash
$ signalops run draft --top 5
⠋ Generating drafts...
✓ Generated 5 drafts

$ signalops queue list
  ┌────┬────────┬────────────────┬──────────────────────────────────────────────┬────────┐
  │ ID │ Score  │ Reply To       │ Draft                                        │ Status │
  ├────┼────────┼────────────────┼──────────────────────────────────────────────┼────────┤
  │ 1  │ 92     │ @techleadSara  │ "Totally feel that — we built Spectra to..." │ pending│
  │ 2  │ 87     │ @devops_mike   │ "We built Spectra for exactly this. AI..."  │ pending│
  │ 3  │ 83     │ @ctojennifer   │ "That's frustrating. Spectra catches the..." │ pending│
  │ 4  │ 78     │ @eng_david     │ "Made the same switch ourselves. Speed..."  │ pending│
  │ 5  │ 74     │ @senior_dev_j  │ "Know that pain well. Happy to show how..." │ pending│
  └────┴────────┴────────────────┴──────────────────────────────────────────────┴────────┘

$ signalops queue approve 1
✓ Draft #1 approved

$ signalops queue edit 2
  Current: "We built Spectra for exactly this. AI catches what humans miss in PRs."
  New text: "Great question — we've been working on this at Spectra. It auto-catches
  the stuff that's easy to miss in PRs. Happy to demo if useful."
✓ Draft #2 edited and approved

$ signalops queue reject 5
  Reason (optional): Too generic, not enough context
✓ Draft #5 rejected

$ signalops queue send --dry-run
  Would send 2 replies:
    #1 → @techleadSara (score: 92)
    #2 → @devops_mike (score: 87)
  Use --confirm to send for real.

$ signalops queue send --confirm
⠋ Sending replies...
  ✓ Sent reply to @techleadSara (tweet ID: 1892847362541)
  ✓ Sent reply to @devops_mike (tweet ID: 1892847399102)
✓ 2 replies sent successfully
```

#### Correct Judgments (Training Data)

```bash
$ signalops correct 42 --label relevant --reason "Actually discussing tool evaluation"
✓ Judgment #42 corrected: irrelevant → relevant
  This correction will be included in the next training data export.
```

#### Export + Eval

```bash
$ signalops export training-data --type judgments --format openai
✓ Exported 247 judgment records to judgments_spectra_20260217.jsonl

$ signalops eval judge --test-set tests/fixtures/eval_set.jsonl
  Running evaluation on 100 test examples...

  Classification Report:
  ┌─────────────┬───────────┬────────┬──────┬─────────┐
  │ Class       │ Precision │ Recall │ F1   │ Support │
  ├─────────────┼───────────┼────────┼──────┼─────────┤
  │ irrelevant  │ 0.85      │ 0.88   │ 0.86 │ 60      │
  │ relevant    │ 0.82      │ 0.78   │ 0.80 │ 40      │
  ├─────────────┼───────────┼────────┼──────┼─────────┤
  │ macro avg   │ 0.84      │ 0.83   │ 0.83 │ 100     │
  └─────────────┴───────────┴────────┴──────┴─────────┘
  MCC: 0.67

$ signalops stats
  ┌──────────────────────────────────────┐
  │ Spectra AI — Pipeline Stats          │
  ├──────────────────────────────────────┤
  │ Collected:      1,247 tweets         │
  │ Judged:         1,247 (100%)         │
  │   Relevant:       389 (31.2%)        │
  │   Irrelevant:     798 (64.0%)        │
  │   Maybe:           60 (4.8%)         │
  │ Scored:           389                │
  │   Avg score:      62.4               │
  │   Score > 70:     142 (36.5%)        │
  │ Drafted:          87                 │
  │ Approved:         64 (73.6%)         │
  │ Sent:             58                 │
  │ Outcomes:                            │
  │   Replies received: 12 (20.7%)       │
  │   Likes received:   23 (39.7%)       │
  │   Follows:          4 (6.9%)         │
  │   Negative:         1 (1.7%)         │
  │ Training data:    34 corrections     │
  │ API usage:        3,420 / 10,000     │
  │                   reads this month   │
  └──────────────────────────────────────┘
```

---

## 9. Testing + CI

### Test Structure

```
tests/
├── conftest.py                 # DB fixtures, mock connectors, sample configs
├── unit/
│   ├── test_normalizer.py      # Text cleaning, entity extraction
│   ├── test_judge.py           # Judgment parsing, fallback logic
│   ├── test_scorer.py          # Scoring math, weight validation
│   ├── test_drafter.py         # Draft generation, char limits
│   ├── test_config.py          # YAML parsing, validation, env vars
│   ├── test_rate_limiter.py    # Token bucket, header updates
│   └── test_exporter.py        # JSONL format validation
├── integration/
│   ├── test_collector.py       # Mock X API → collector → DB
│   ├── test_pipeline.py        # Full pipeline with mock APIs
│   └── test_cli.py             # Click CliRunner tests
└── fixtures/
    ├── tweets.json             # 20 sample X API tweet responses
    ├── users.json              # 10 sample user profiles
    ├── project_spectra.yaml    # Test config
    ├── project_salesense.yaml  # Test config
    └── eval_set.jsonl          # 50 labeled examples for eval tests
```

### Key Test Cases

#### Normalizer Tests

```python
# tests/unit/test_normalizer.py
def test_strip_urls():
    assert normalize("Check out https://t.co/abc123") == "Check out"

def test_preserve_mentions():
    result = normalize("Thanks @alice for the tip")
    assert "@alice" in result

def test_collapse_whitespace():
    assert normalize("too   many    spaces") == "too many spaces"

def test_detect_language():
    assert detect_language("This is English") == "en"
    assert detect_language("Esto es español") == "es"

def test_extract_hashtags():
    entities = extract_entities("#ai #code review is hard")
    assert entities["hashtags"] == ["ai", "code"]
```

#### Judge Tests

```python
# tests/unit/test_judge.py
def test_parse_structured_judgment():
    raw = '{"label": "relevant", "confidence": 0.85, "reasoning": "User needs help"}'
    j = parse_judgment(raw)
    assert j.label == "relevant"
    assert j.confidence == 0.85

def test_fallback_on_invalid_json():
    """If LLM returns malformed JSON, fall back to keyword matching."""
    raw = "This tweet seems relevant because..."
    j = parse_judgment_with_fallback(raw, keywords=["code review"])
    assert j.model_id == "fallback"

def test_keyword_exclusion():
    """Posts matching excluded keywords should be auto-rejected."""
    j = judge_with_rules("We're hiring a code review engineer",
                         excluded=["hiring"])
    assert j.label == "irrelevant"
```

#### Scorer Tests

```python
# tests/unit/test_scorer.py
def test_perfect_score():
    score = compute_score(
        judgment_confidence=1.0, judgment_label="relevant",
        followers=10000, verified=True, bio_match=True,
        likes=50, replies=10, views=5000,
        hours_ago=1, has_question=True,
        weights=default_weights()
    )
    assert 90 <= score.total_score <= 100

def test_zero_followers():
    """Zero followers should not crash, just get low authority score."""
    score = compute_score(followers=0, verified=False, bio_match=False,
                          **other_defaults())
    assert score.components["author_authority"] == 0

def test_weights_sum_to_one():
    w = default_weights()
    total = sum(w.dict().values())
    assert abs(total - 1.0) < 0.01
```

#### Rate Limiter Tests

```python
# tests/unit/test_rate_limiter.py
def test_allows_within_limit():
    rl = RateLimiter(max_requests=10, window_seconds=900)
    for _ in range(10):
        assert rl.acquire() == 0.0  # No wait

def test_blocks_over_limit():
    rl = RateLimiter(max_requests=2, window_seconds=900)
    rl.acquire()
    rl.acquire()
    wait = rl.acquire()
    assert wait > 0  # Must wait

def test_update_from_headers():
    rl = RateLimiter(max_requests=300, window_seconds=900)
    rl.update_from_headers({"x-rate-limit-remaining": "5",
                            "x-rate-limit-reset": str(int(time.time()) + 60)})
    assert rl.tokens == 5
```

### CI Pipeline

```yaml
# .github/workflows/ci.yml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install ruff
      - run: ruff check src/ tests/
      - run: ruff format --check src/ tests/

  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: mypy src/signalops --strict

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: pytest tests/ -v --tb=short --cov=signalops --cov-report=xml
      - uses: codecov/codecov-action@v4
        with:
          file: coverage.xml

  integration:
    runs-on: ubuntu-latest
    needs: [lint, typecheck, test]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: pytest tests/integration/ -v --tb=short
```

---

## 10. Risk Notes

### X API Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Basic tier rate limits** (60 searches/15min, 10K reads/month) | Can only collect ~3,300 tweets/day max | Cache aggressively, deduplicate, use `since_id` for incremental collection |
| **Basic tier cost** ($200/month) | Ongoing expense | Worth it for compliance. Track usage with monthly cap tracker. |
| **Pro tier cost** ($5,000/month for Filtered Stream) | Significant expense | Defer to v0.2. Basic tier search is sufficient for MVP. |
| **API changes / deprecation** | X has changed API tiers 3 times since 2023 | Connector abstraction layer isolates the rest of the codebase |
| **OAuth token expiry** (2 hours) | Broken pipeline if token expires mid-run | Auto-refresh at 90 minutes. Store refresh token encrypted. |
| **Duplicate content rejection** | API rejects identical tweets within 24h | Draft generator must produce unique text per target. Never batch-send identical replies. |

### ToS Compliance Risks

| Risk | X's Rule | Our Approach |
|------|----------|--------------|
| **Auto-reply to strangers** | Permitted if relevant, valuable, and not at spam velocity | Human approves every reply. Max 5/hour, 20/day default. |
| **DM automation** | Unsolicited automated DMs prohibited | DM feature is opt-in only, disabled by default, requires explicit user action |
| **Engagement manipulation** | No auto-like/follow/retweet at scale | We do NOT automate likes, follows, or retweets. Read-only collection + reply only. |
| **Coordinated behavior** | No multi-account coordination | Single account operation only. No multi-account support. |
| **Content requirements** | Must comply with X Rules (no harassment, spam, etc.) | LLM drafts validated for tone. Human review gate. |
| **Data retention** | Must delete data for deleted/suspended tweets | Batch Compliance polling (Pro tier). For Basic: re-check tweet existence before sending reply. |
| **Display requirements** | Attribution required when showing tweets externally | CLI displays author, handle, text, timestamp. Web dashboard will include full attribution. |

### Spam Prevention Design

| Mechanism | Implementation |
|-----------|----------------|
| **Human approval gate** | Every reply requires explicit `approve` or `edit` before sending. No auto-send mode. |
| **Rate limits** | Configurable per-project `max_replies_per_hour` and `max_replies_per_day`. Enforced at orchestrator level. |
| **Cooldown after negative outcome** | If a reply gets blocked/reported (`outcome_type = 'negative'`), pause all sends for that project for 24 hours. Auto-alert the user. |
| **Content diversity** | Draft generator is instructed to produce unique, contextual replies. Explicit template variation. No identical batch replies. |
| **Target deduplication** | Never reply to the same author twice within 30 days (configurable). DB constraint + check. |
| **Dry-run default** | `send` command requires `--confirm` flag. Default behavior is preview-only. |
| **Audit trail** | Every action logged to `audit_logs` table with timestamp, user, and details. |
| **Self-monitoring** | `stats` command shows negative outcome rate. If > 5%, display warning. |

### Cost Optimization

| Strategy | Implementation |
|----------|----------------|
| **Cache search results** | Redis with 30-min TTL for search queries. Same query in same window hits cache. |
| **Deduplicate before judging** | Only judge new tweets (not previously seen for this project). `UniqueConstraint` on `(platform, platform_id, project_id)`. |
| **Batch LLM calls** | Judge stage batches 5-10 tweets per LLM call for classification. Reduces per-call overhead. |
| **Cheap model for judging** | Use `claude-haiku-4-5` or `gpt-4o-mini` for judgment (fast, cheap). Reserve `claude-sonnet-4-6` for drafts. |
| **Monthly cap tracking** | `MonthlyCapTracker` in Redis. Alerts at 80% usage, hard-stops at 95%. |
| **Incremental collection** | Store `since_id` per query. Only fetch new tweets each run. |
| **Fallback classifier** | If LLM budget is exhausted, fall back to TF-IDF keyword classifier (zero marginal cost). |

### Throttling Implementation

```python
# Built into the orchestrator
class ThrottleConfig:
    search_requests_per_15min: int = 55     # Stay under 60 limit
    search_interval_seconds: float = 16.4   # 900s / 55 = 16.4s between calls
    reply_interval_seconds: float = 720     # 5 per hour = 1 every 12 min
    jitter_range: float = 0.2               # ±20% randomization
    monthly_read_cap: int = 9500            # Stay under 10K limit
    monthly_write_cap: int = 2800           # Stay under 3K limit
```

### Data Privacy

| Concern | Mitigation |
|---------|------------|
| Storing tweet text | Only store publicly available data. Respect deletion compliance. |
| Storing author info | Only public profile data. No private data. |
| LLM data sharing | Use API providers with data retention policies that don't train on your data (Anthropic API, OpenAI API with opt-out). |
| Credential storage | OAuth tokens encrypted at rest. `.env` file in `.gitignore`. Never log tokens. |
| GDPR compliance | Delete user data on request. Export/delete commands for individual users. |

---

## Appendix A: Dependencies

```toml
# pyproject.toml [project.dependencies]
[project]
name = "signalops"
version = "0.1.0"
requires-python = ">=3.11"
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
    "redis>=5.0",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "pytest-asyncio>=0.23",
    "mypy>=1.11",
    "ruff>=0.6",
    "respx>=0.21",       # Mock httpx
]

[project.scripts]
signalops = "signalops.cli.main:cli"
```

## Appendix B: Environment Variables

```bash
# .env.example

# ── X API ──
X_API_KEY=                       # OAuth 1.0a consumer key
X_API_SECRET=                    # OAuth 1.0a consumer secret
X_BEARER_TOKEN=                  # App-only bearer token (for search)
X_CLIENT_ID=                     # OAuth 2.0 client ID
X_CLIENT_SECRET=                 # OAuth 2.0 client secret (confidential apps)
X_REDIRECT_URI=http://localhost:8400/callback

# ── LLM Providers ──
ANTHROPIC_API_KEY=               # Claude API key
OPENAI_API_KEY=                  # OpenAI API key (optional)

# ── Storage ──
DATABASE_URL=sqlite:///signalops.db   # SQLite default, PostgreSQL for production
REDIS_URL=redis://localhost:6379/0     # Optional, for caching

# ── Notifications ──
DISCORD_WEBHOOK_SPECTRA=         # Project-specific webhook
SLACK_WEBHOOK_SALESENSE=         # Project-specific webhook

# ── Optional ──
SOCIALDATA_API_KEY=              # SocialData.tools API key (alternative data source)
```

## Appendix C: LLM Prompt Templates

### Judge Prompt

```
System: You are a relevance judge for {project_name}. {project_description}

{relevance.system_prompt}

Positive signals that make a tweet RELEVANT:
{for signal in relevance.positive_signals}
- {signal}
{endfor}

Negative signals that make a tweet IRRELEVANT:
{for signal in relevance.negative_signals}
- {signal}
{endfor}

Evaluate the following tweet and respond with ONLY valid JSON:
{
  "label": "relevant" | "irrelevant" | "maybe",
  "confidence": 0.0 to 1.0,
  "reasoning": "1-2 sentence explanation"
}

User: Tweet: "{post.text_cleaned}"
Author: @{post.author_username} ({post.author_followers} followers)
Author bio: "{author_bio}"
Posted: {post.created_at}
Engagement: {post.likes} likes, {post.replies} replies, {post.retweets} retweets
```

### Draft Prompt

```
System: You are {persona.name}, a {persona.role} for {project_name}.
Your tone is {persona.tone}.

{persona.voice_notes}

Example reply style:
"{persona.example_reply}"

Rules:
- Keep reply under 240 characters
- Be genuinely helpful, not salesy
- Reference something specific from their tweet
- Only mention {project_name} if it's truly relevant to their situation
- No hashtags, no emojis (unless the original poster uses them)
- Sound human, not corporate
- Never use phrases like "I understand your frustration" or "Great question!"

User: Write a reply to this tweet.

Tweet: "{post.text_original}"
Author: @{post.author_username}
Context: They were found via the query "{query_used}" and scored {score}/100.
Relevance reasoning: "{judgment.reasoning}"
```

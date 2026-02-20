# Terminal C — CLI + Orchestration + Integration

> **Branch:** `feat/cli`
> **Role:** You build the entire user-facing layer: all CLI commands, the pipeline orchestrator, the send stage, training data export, and CI configuration.
> **You are one of 3 parallel terminals. Terminal A is building config/storage/connectors. Terminal B is building LLM/judge/score/draft. You all work on separate branches simultaneously.**

---

## FIRST STEP — Run this immediately

```bash
git checkout feat/cli
```

---

## RULES

1. **ONLY create/edit files listed in the File Ownership section below.** Do NOT touch any other files.
2. **Commit after each phase** with the exact commit message provided.
3. **Run tests after each phase** before moving to the next.
4. **Use parallel tool calls** — when creating independent CLI command files, write them all in one message.
5. **Run tests in background** — use `Bash(run_in_background=true)` for pytest while you continue writing the next phase's files.
6. **Use Task sub-agents** for complex files — spawn a sub-agent for orchestrator.py if needed.
7. **ALL CLI imports of pipeline stages must be LAZY** — import inside the Click command function, not at module top level.

---

## CRITICAL: Handling Imports from Terminal A & B's Code

Terminals A and B are building the pipeline stages, models, config, and storage on parallel branches. Those files DO NOT EXIST on your branch yet.

### Strategy: Stubs + Lazy Imports

**Step 1: Create stub files** so your imports resolve at runtime and for testing.
**Step 2: Use lazy imports** inside Click commands — import pipeline stages inside functions, not at the top of files.

### Stub Files to Create FIRST

Create these minimal stubs before writing any of your own files:

#### `src/signalops/config/schema.py` (STUB)

```python
"""Stub — real implementation on feat/data branch."""
from pydantic import BaseModel

class QueryConfig(BaseModel):
    text: str
    label: str
    enabled: bool = True
    max_results_per_run: int = 100

class ICPConfig(BaseModel):
    min_followers: int = 100
    max_followers: int | None = None
    verified_only: bool = False
    languages: list[str] = ["en"]
    exclude_bios_containing: list[str] = []
    prefer_bios_containing: list[str] = []

class RelevanceRubric(BaseModel):
    system_prompt: str
    positive_signals: list[str]
    negative_signals: list[str]
    keywords_required: list[str] = []
    keywords_excluded: list[str] = []

class ScoringWeights(BaseModel):
    relevance_judgment: float = 0.35
    author_authority: float = 0.25
    engagement_signals: float = 0.15
    recency: float = 0.15
    intent_strength: float = 0.10

class PersonaConfig(BaseModel):
    name: str
    role: str
    tone: str
    voice_notes: str
    example_reply: str

class TemplateConfig(BaseModel):
    id: str
    name: str
    template: str
    use_when: str

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

#### `src/signalops/config/loader.py` (STUB)

```python
"""Stub — real implementation on feat/data branch."""
import yaml
import os
import hashlib
from pathlib import Path
from .schema import ProjectConfig

def load_project(path):
    path = Path(path)
    with open(path) as f:
        raw = yaml.safe_load(f)
    raw = _resolve_env_vars(raw)
    return ProjectConfig(**raw)

def _resolve_env_vars(obj):
    if isinstance(obj, str):
        if obj.startswith("${") and obj.endswith("}"):
            return os.environ.get(obj[2:-1], obj)
        return obj
    if isinstance(obj, dict):
        return {k: _resolve_env_vars(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_env_vars(v) for v in obj]
    return obj

def config_hash(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()
```

#### `src/signalops/config/defaults.py` (STUB)

```python
"""Stub — real implementation on feat/data branch."""
from pathlib import Path

DEFAULT_DB_URL = "sqlite:///signalops.db"
DEFAULT_CREDENTIALS_DIR = Path.home() / ".signalops"
DEFAULT_PROJECTS_DIR = Path("projects")
MAX_TWEET_LENGTH = 280
MAX_REPLY_LENGTH = 240
DEFAULT_SEARCH_MAX_RESULTS = 100
SUPPORTED_PLATFORMS = ["x"]
```

#### `src/signalops/storage/database.py` (STUB)

```python
"""Stub — real implementation on feat/data branch."""
from sqlalchemy import (Column, String, Integer, Float, Boolean, DateTime,
                        Text, JSON, ForeignKey, Enum as SAEnum, func,
                        UniqueConstraint, Index, create_engine)
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
import enum

class Base(DeclarativeBase):
    pass

class JudgmentLabel(enum.Enum):
    RELEVANT = "relevant"
    IRRELEVANT = "irrelevant"
    MAYBE = "maybe"

class DraftStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    EDITED = "edited"
    REJECTED = "rejected"
    SENT = "sent"
    FAILED = "failed"

class OutcomeType(enum.Enum):
    REPLY_RECEIVED = "reply_received"
    LIKE_RECEIVED = "like_received"
    FOLLOW_RECEIVED = "follow_received"
    PROFILE_CLICK = "profile_click"
    LINK_CLICK = "link_click"
    BOOKING = "booking"
    NEGATIVE = "negative"

class Project(Base):
    __tablename__ = "projects"
    id = Column(String(64), primary_key=True)
    name = Column(String(256), nullable=False)
    config_path = Column(String(1024), nullable=False)
    config_hash = Column(String(64))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    is_active = Column(Boolean, default=True)

class RawPost(Base):
    __tablename__ = "raw_posts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(64), ForeignKey("projects.id"), nullable=False)
    platform = Column(String(32), nullable=False)
    platform_id = Column(String(64), nullable=False)
    collected_at = Column(DateTime, server_default=func.now())
    query_used = Column(Text)
    raw_json = Column(JSON, nullable=False)

class NormalizedPost(Base):
    __tablename__ = "normalized_posts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    raw_post_id = Column(Integer, ForeignKey("raw_posts.id"), unique=True, nullable=False)
    project_id = Column(String(64), ForeignKey("projects.id"), nullable=False)
    platform = Column(String(32), nullable=False)
    platform_id = Column(String(64), nullable=False)
    author_id = Column(String(64), nullable=False)
    author_username = Column(String(256))
    author_display_name = Column(String(256))
    author_followers = Column(Integer, default=0)
    author_verified = Column(Boolean, default=False)
    text_original = Column(Text, nullable=False)
    text_cleaned = Column(Text, nullable=False)
    language = Column(String(8))
    created_at = Column(DateTime, nullable=False)
    reply_to_id = Column(String(64))
    conversation_id = Column(String(64))
    likes = Column(Integer, default=0)
    retweets = Column(Integer, default=0)
    replies = Column(Integer, default=0)
    views = Column(Integer, default=0)
    hashtags = Column(JSON)
    mentions = Column(JSON)
    urls = Column(JSON)

class Judgment(Base):
    __tablename__ = "judgments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    normalized_post_id = Column(Integer, ForeignKey("normalized_posts.id"), nullable=False)
    project_id = Column(String(64), ForeignKey("projects.id"), nullable=False)
    label = Column(SAEnum(JudgmentLabel), nullable=False)
    confidence = Column(Float, nullable=False)
    reasoning = Column(Text)
    model_id = Column(String(128), nullable=False)
    model_version = Column(String(64))
    latency_ms = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
    human_label = Column(SAEnum(JudgmentLabel))
    human_corrected_at = Column(DateTime)
    human_reason = Column(Text)

class Score(Base):
    __tablename__ = "scores"
    id = Column(Integer, primary_key=True, autoincrement=True)
    normalized_post_id = Column(Integer, ForeignKey("normalized_posts.id"), nullable=False)
    project_id = Column(String(64), ForeignKey("projects.id"), nullable=False)
    total_score = Column(Float, nullable=False)
    components = Column(JSON, nullable=False)
    scoring_version = Column(String(64), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class Draft(Base):
    __tablename__ = "drafts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    normalized_post_id = Column(Integer, ForeignKey("normalized_posts.id"), nullable=False)
    project_id = Column(String(64), ForeignKey("projects.id"), nullable=False)
    text_generated = Column(Text, nullable=False)
    text_final = Column(Text)
    tone = Column(String(64))
    template_used = Column(String(128))
    model_id = Column(String(128), nullable=False)
    status = Column(SAEnum(DraftStatus), default=DraftStatus.PENDING)
    created_at = Column(DateTime, server_default=func.now())
    approved_at = Column(DateTime)
    sent_at = Column(DateTime)
    sent_post_id = Column(String(64))

class Outcome(Base):
    __tablename__ = "outcomes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    draft_id = Column(Integer, ForeignKey("drafts.id"), nullable=False)
    project_id = Column(String(64), ForeignKey("projects.id"), nullable=False)
    outcome_type = Column(SAEnum(OutcomeType), nullable=False)
    details = Column(JSON)
    observed_at = Column(DateTime, server_default=func.now())

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(64))
    action = Column(String(128), nullable=False)
    entity_type = Column(String(64))
    entity_id = Column(Integer)
    details = Column(JSON)
    user = Column(String(128))
    timestamp = Column(DateTime, server_default=func.now())

def get_engine(db_url="sqlite:///signalops.db"):
    return create_engine(db_url, echo=False)

def get_session(engine):
    return sessionmaker(bind=engine)()

def init_db(engine):
    Base.metadata.create_all(engine)
```

#### `src/signalops/storage/audit.py` (STUB)

```python
"""Stub — real implementation on feat/data branch."""
from .database import AuditLog

def log_action(session, project_id, action, entity_type=None, entity_id=None, details=None, user="system"):
    entry = AuditLog(
        project_id=project_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        user=user,
    )
    session.add(entry)
    session.commit()

def get_recent_actions(session, project_id, limit=50):
    return session.query(AuditLog).filter(
        AuditLog.project_id == project_id
    ).order_by(AuditLog.timestamp.desc()).limit(limit).all()
```

#### `src/signalops/connectors/base.py` (STUB)

```python
"""Stub — real implementation on feat/data branch."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

@dataclass
class RawPost:
    platform: str
    platform_id: str
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
    metrics: dict
    entities: dict
    raw_json: dict

class Connector(ABC):
    @abstractmethod
    def search(self, query, since_id=None, max_results=100): ...
    @abstractmethod
    def get_user(self, user_id): ...
    @abstractmethod
    def post_reply(self, in_reply_to_id, text): ...
    @abstractmethod
    def health_check(self): ...
```

**Create ALL stub files FIRST before proceeding to Phase C1.**

At merge time, Terminal A's and B's real implementations will replace these stubs.

---

## FILE OWNERSHIP (17 real files + 6 stubs)

```
# STUBS (will be replaced at merge):
src/signalops/config/schema.py           ← STUB
src/signalops/config/loader.py           ← STUB
src/signalops/config/defaults.py         ← STUB
src/signalops/storage/database.py        ← STUB
src/signalops/storage/audit.py           ← STUB
src/signalops/connectors/base.py         ← STUB

# YOUR REAL FILES:
src/signalops/cli/main.py
src/signalops/cli/project.py
src/signalops/cli/collect.py
src/signalops/cli/judge.py
src/signalops/cli/score.py
src/signalops/cli/draft.py
src/signalops/cli/approve.py
src/signalops/cli/send.py
src/signalops/cli/stats.py
src/signalops/cli/export.py
src/signalops/pipeline/orchestrator.py
src/signalops/pipeline/sender.py
src/signalops/training/exporter.py
tests/test_cli.py
tests/integration/test_pipeline.py
.github/workflows/ci.yml
.env.example
```

---

## PHASE C1: CLI Skeleton + Project Management

### File 1: `src/signalops/cli/main.py`

The main Click application entry point:

```python
# import click
# from rich.console import Console
# from dotenv import load_dotenv
#
# # Load .env on startup
# load_dotenv()
#
# console = Console()
#
# @click.group()
# @click.option("--project", "-p", default=None, help="Override active project")
# @click.option("--dry-run", is_flag=True, default=False, help="Preview without side effects")
# @click.option("--verbose", "-v", is_flag=True, default=False, help="Debug logging")
# @click.option("--format", "output_format", type=click.Choice(["table", "json"]), default="table", help="Output format")
# @click.pass_context
# def cli(ctx, project, dry_run, verbose, output_format):
#     """SignalOps — Agentic social lead finder + outreach workbench."""
#     ctx.ensure_object(dict)
#     ctx.obj["project"] = project
#     ctx.obj["dry_run"] = dry_run
#     ctx.obj["verbose"] = verbose
#     ctx.obj["format"] = output_format
#     ctx.obj["console"] = console
#
#     if verbose:
#         import logging
#         logging.basicConfig(level=logging.DEBUG)
#
# # Register sub-groups and commands
# # Import and register these AFTER the cli group is defined:
# from signalops.cli.project import project_group
# from signalops.cli.collect import run_group  # 'run' group with collect, judge, score, all
# from signalops.cli.approve import queue_group
# from signalops.cli.stats import stats_cmd
# from signalops.cli.export import export_group
#
# cli.add_command(project_group, "project")
# cli.add_command(run_group, "run")
# cli.add_command(queue_group, "queue")
# cli.add_command(stats_cmd, "stats")
# cli.add_command(export_group, "export")
#
# if __name__ == "__main__":
#     cli()
```

**Command tree to implement:**
```
signalops
├── project
│   ├── set <name>
│   ├── list
│   └── init
├── run
│   ├── collect
│   ├── judge
│   ├── score
│   ├── draft
│   └── all
├── queue
│   ├── list
│   ├── approve <id>
│   ├── edit <id>
│   ├── reject <id>
│   └── send
├── stats
└── export
    └── training-data
```

### File 2: `src/signalops/cli/project.py`

```python
# @click.group("project")
# def project_group():
#     """Manage projects."""
#
# @project_group.command("set")
# @click.argument("name")
# @click.pass_context
# def project_set(ctx, name):
#     """Set the active project."""
#     # 1. Verify project YAML exists in projects/ directory
#     # 2. Store active project name in ~/.signalops/active_project (plain text file)
#     # 3. Load and validate the config to confirm it's valid
#     # 4. Display: "Active project: {name} ({query_count} queries configured)"
#     from signalops.config.loader import load_project
#     from signalops.config.defaults import DEFAULT_CREDENTIALS_DIR, DEFAULT_PROJECTS_DIR
#     # Use Path(DEFAULT_PROJECTS_DIR / f"{name}.yaml")
#     # Write name to DEFAULT_CREDENTIALS_DIR / "active_project"
#
# @project_group.command("list")
# @click.pass_context
# def project_list(ctx):
#     """List all available projects."""
#     # Scan projects/ directory for *.yaml files
#     # For each: load config, display name, query count, active indicator
#     # Use Rich table for display
#
# @project_group.command("init")
# @click.pass_context
# def project_init(ctx):
#     """Create a new project interactively."""
#     # Use Rich prompts to ask for:
#     #   project_id, project_name, description, product_url
#     #   At least one query (text + label)
#     #   Persona (name, role, tone, voice_notes, example_reply)
#     #   Relevance system_prompt, at least one positive_signal, one negative_signal
#     # Build ProjectConfig and write as YAML to projects/{project_id}.yaml
#
# Helper function:
# def get_active_project(ctx) -> str:
#     """Get the active project name from ctx override or ~/.signalops/active_project."""
#     if ctx.obj.get("project"):
#         return ctx.obj["project"]
#     active_file = DEFAULT_CREDENTIALS_DIR / "active_project"
#     if active_file.exists():
#         return active_file.read_text().strip()
#     raise click.UsageError("No active project. Run: signalops project set <name>")
#
# def load_active_config(ctx) -> ProjectConfig:
#     """Load the active project's config."""
#     name = get_active_project(ctx)
#     path = DEFAULT_PROJECTS_DIR / f"{name}.yaml"
#     if not path.exists():
#         raise click.UsageError(f"Project config not found: {path}")
#     return load_project(path)
```

### File 3: `src/signalops/cli/stats.py`

```python
# @click.command("stats")
# @click.pass_context
# def stats_cmd(ctx):
#     """Show pipeline statistics for the active project."""
#     from signalops.storage.database import (get_engine, get_session, init_db,
#         RawPost, NormalizedPost, Judgment, JudgmentLabel, Score, Draft, DraftStatus, Outcome, OutcomeType)
#     from signalops.config.defaults import DEFAULT_DB_URL
#     from rich.table import Table
#     from rich.panel import Panel
#
#     project_id = get_active_project(ctx)
#     engine = get_engine(DEFAULT_DB_URL)
#     session = get_session(engine)
#
#     # Query counts:
#     raw_count = session.query(RawPost).filter_by(project_id=project_id).count()
#     norm_count = session.query(NormalizedPost).filter_by(project_id=project_id).count()
#     judged_relevant = session.query(Judgment).filter_by(project_id=project_id, label=JudgmentLabel.RELEVANT).count()
#     judged_irrelevant = session.query(Judgment).filter_by(project_id=project_id, label=JudgmentLabel.IRRELEVANT).count()
#     judged_maybe = session.query(Judgment).filter_by(project_id=project_id, label=JudgmentLabel.MAYBE).count()
#     total_judged = judged_relevant + judged_irrelevant + judged_maybe
#     # ... scores (avg, count >70), drafts (by status), outcomes (by type)
#
#     # Display as Rich Panel with formatted table (match the mockup from PLANA.md):
#     # ┌──────────────────────────────────────┐
#     # │ {Project Name} — Pipeline Stats      │
#     # ├──────────────────────────────────────┤
#     # │ Collected:      X tweets             │
#     # │ Judged:         X (100%)             │
#     # │   Relevant:     X (XX.X%)            │
#     # │   Irrelevant:   X (XX.X%)            │
#     # │   Maybe:        X (XX.X%)            │
#     # │ Scored:         X                    │
#     # │   Avg score:    XX.X                 │
#     # │   Score > 70:   X (XX.X%)            │
#     # │ Drafted:        X                    │
#     # │ Approved:       X (XX.X%)            │
#     # │ Sent:           X                    │
#     # └──────────────────────────────────────┘
```

**After creating Phase C1 files, run:**
```bash
pytest tests/ -v 2>/dev/null || echo "No tests yet — C1 is structural"
```

Test that the CLI loads:
```bash
python -m signalops.cli.main --help
```

**Commit:**
```
feat(cli): CLI skeleton with project management and stats
```

---

## PHASE C2: Pipeline CLI Commands

### File 4: `src/signalops/cli/collect.py`

```python
# This file defines the `run` group and the `collect` command.
# Other pipeline commands (judge, score, draft, all) are added to this group.
#
# @click.group("run")
# def run_group():
#     """Run pipeline stages."""
#
# @run_group.command("collect")
# @click.pass_context
# def collect_cmd(ctx):
#     """Collect tweets matching project queries."""
#     # LAZY IMPORTS:
#     from signalops.pipeline.collector import CollectorStage
#     from signalops.connectors.x_api import XConnector
#     from signalops.connectors.rate_limiter import RateLimiter
#     from signalops.storage.database import get_engine, get_session, init_db
#     from signalops.config.defaults import DEFAULT_DB_URL
#     from rich.progress import Progress
#
#     config = load_active_config(ctx)
#     dry_run = ctx.obj["dry_run"]
#
#     engine = get_engine(DEFAULT_DB_URL)
#     init_db(engine)
#     session = get_session(engine)
#
#     # Initialize connector
#     import os
#     bearer_token = os.environ.get("X_BEARER_TOKEN", "")
#     rate_limiter = RateLimiter(max_requests=55, window_seconds=900)
#     connector = XConnector(bearer_token=bearer_token, rate_limiter=rate_limiter)
#
#     # Run collector
#     collector = CollectorStage(connector=connector, db_session=session)
#     with Progress() as progress:
#         task = progress.add_task("Collecting tweets...", total=len(config.queries))
#         result = collector.run(config=config, dry_run=dry_run)
#         progress.update(task, completed=len(config.queries))
#
#     # Display results
#     console = ctx.obj["console"]
#     console.print(f"[green]Collected {result['total_new']} tweets ({result['total_skipped']} duplicates skipped)")
```

### File 5: `src/signalops/cli/judge.py`

```python
# @run_group.command("judge")  # NOTE: import run_group from collect.py
# @click.pass_context
# def judge_cmd(ctx):
#     """Judge relevance of collected tweets."""
#     # LAZY IMPORTS
#     from signalops.pipeline.judge import JudgeStage
#     from signalops.models.judge_model import LLMPromptJudge
#     from signalops.models.llm_gateway import LLMGateway
#     # ... setup gateway, judge, run stage, display results
#     # Show: "Relevant: X | Irrelevant: X | Maybe: X"
```

### File 6: `src/signalops/cli/score.py`

```python
# @run_group.command("score")
# @click.pass_context
# def score_cmd(ctx):
#     """Score judged tweets."""
#     # LAZY IMPORTS
#     from signalops.pipeline.scorer import ScorerStage
#     # ... setup, run stage, display top-5 Rich table
#     # Table columns: #, Score, Author, Tweet (truncated), Query
```

### File 7: `src/signalops/cli/draft.py`

```python
# @run_group.command("draft")
# @click.option("--top", default=10, help="Number of top-scored posts to draft replies for")
# @click.pass_context
# def draft_cmd(ctx, top):
#     """Generate reply drafts for top-scored leads."""
#     # LAZY IMPORTS
#     from signalops.pipeline.drafter import DrafterStage
#     from signalops.models.draft_model import LLMDraftGenerator
#     from signalops.models.llm_gateway import LLMGateway
#     # ... setup generator, run DrafterStage with top_n=top, display count
```

**Also add the `all` command to the run_group** (can be in collect.py or a separate run_all.py):
```python
# @run_group.command("all")
# @click.pass_context
# def run_all_cmd(ctx):
#     """Run full pipeline: collect -> judge -> score -> draft."""
#     # Call orchestrator (Phase C4)
#     from signalops.pipeline.orchestrator import PipelineOrchestrator
#     # ... setup, run orchestrator.run_all()
```

**After creating Phase C2 files, run:**
```bash
python -m signalops.cli.main run --help
```

**Commit:**
```
feat(cli): pipeline commands — collect, judge, score, draft
```

---

## PHASE C3: Approval Queue + Send

### File 8: `src/signalops/cli/approve.py`

```python
# @click.group("queue")
# def queue_group():
#     """Manage the draft approval queue."""
#
# @queue_group.command("list")
# @click.pass_context
# def queue_list(ctx):
#     """Show pending drafts."""
#     from signalops.storage.database import (get_engine, get_session, Draft, DraftStatus,
#                                              NormalizedPost, Score)
#     from rich.table import Table
#
#     project_id = get_active_project(ctx)
#     # Query: Draft JOIN NormalizedPost JOIN Score
#     #   WHERE project_id=project_id AND status=PENDING
#     #   ORDER BY Score.total_score DESC
#     #
#     # Display Rich table:
#     # | ID | Score | Reply To | Draft (truncated to 60 chars) | Status |
#
# @queue_group.command("approve")
# @click.argument("draft_id", type=int)
# @click.pass_context
# def queue_approve(ctx, draft_id):
#     """Approve a draft for sending."""
#     from signalops.storage.database import get_engine, get_session, Draft, DraftStatus
#     from datetime import datetime, timezone
#     # Load draft by ID, set status=APPROVED, set approved_at=now
#     # Log audit action
#     # Print confirmation
#
# @queue_group.command("edit")
# @click.argument("draft_id", type=int)
# @click.pass_context
# def queue_edit(ctx, draft_id):
#     """Edit a draft then approve it."""
#     from signalops.storage.database import get_engine, get_session, Draft, DraftStatus
#     from rich.prompt import Prompt
#     # Load draft, show current text
#     # Prompt for new text using Rich Prompt or click.edit()
#     # Set text_final=new_text, status=EDITED, approved_at=now
#     # Log audit action
#
# @queue_group.command("reject")
# @click.argument("draft_id", type=int)
# @click.option("--reason", default=None, help="Rejection reason")
# @click.pass_context
# def queue_reject(ctx, draft_id, reason):
#     """Reject a draft."""
#     from signalops.storage.database import get_engine, get_session, Draft, DraftStatus
#     # Set status=REJECTED
#     # Log audit with reason
```

### File 9: `src/signalops/pipeline/sender.py`

```python
# class SenderStage:
#     """Sends approved drafts as replies via the connector."""
#
#     __init__(self, connector: Connector, db_session: Session)
#
#     run(self, project_id: str, config: ProjectConfig, dry_run: bool = False) -> dict:
#         1. Query Drafts WHERE project_id matches AND status IN (APPROVED, EDITED)
#         2. Check rate limits:
#            - Count drafts sent in last hour -> compare to config.rate_limits["max_replies_per_hour"]
#            - Count drafts sent today -> compare to config.rate_limits["max_replies_per_day"]
#            - If over either limit: skip remaining, return early
#         3. For each approved draft:
#            a. Get the associated NormalizedPost (for reply_to platform_id)
#            b. Get the text to send: text_final if edited, else text_generated
#            c. If dry_run: print "[DRY RUN] Would send reply to @{author}" and continue
#            d. Call connector.post_reply(in_reply_to_id=post.platform_id, text=send_text)
#            e. Update Draft: status=SENT, sent_at=now, sent_post_id=returned_id
#            f. Log audit: action="send", entity_type="draft", entity_id=draft.id
#         4. Return summary: {sent_count, skipped_rate_limit, failed_count, dry_run}
#
#     _check_rate_limits(self, project_id: str, config: ProjectConfig) -> tuple[bool, str]:
#         """Returns (is_allowed, reason)."""
```

### File 10: `src/signalops/cli/send.py`

```python
# Add 'send' to the queue_group:
#
# @queue_group.command("send")
# @click.option("--confirm", is_flag=True, default=False, help="Actually send (default is preview)")
# @click.pass_context
# def queue_send(ctx, confirm):
#     """Send approved drafts as replies."""
#     from signalops.pipeline.sender import SenderStage
#     from signalops.connectors.x_api import XConnector
#     from signalops.connectors.rate_limiter import RateLimiter
#
#     config = load_active_config(ctx)
#     dry_run = ctx.obj["dry_run"] or not confirm
#
#     if dry_run:
#         console.print("[yellow]Preview mode — use --confirm to send for real")
#
#     # Setup connector, sender stage, run, display results
#     result = sender.run(project_id=config.project_id, config=config, dry_run=dry_run)
#
#     if dry_run:
#         console.print(f"Would send {result['sent_count']} replies. Use --confirm to send.")
#     else:
#         console.print(f"[green]Sent {result['sent_count']} replies")
```

### File 11: `src/signalops/cli/export.py`

```python
# @click.group("export")
# def export_group():
#     """Export data for fine-tuning or analysis."""
#
# @export_group.command("training-data")
# @click.option("--type", "data_type", type=click.Choice(["judgments", "drafts"]), required=True)
# @click.option("--format", "data_format", type=click.Choice(["openai", "dpo"]), default="openai")
# @click.option("--output", default=None, help="Output file path")
# @click.pass_context
# def export_training_data(ctx, data_type, data_format, output):
#     """Export training data as JSONL for fine-tuning."""
#     from signalops.training.exporter import TrainingDataExporter
#     # ... setup, run export, display count and output path
```

**After creating Phase C3 files, run:**
```bash
python -m signalops.cli.main queue --help
python -m signalops.cli.main queue send --help
```

**Commit:**
```
feat(cli): approval queue and send with dry-run safety
```

---

## PHASE C4: Orchestrator + Integration

### File 12: `src/signalops/pipeline/orchestrator.py`

```python
# class PipelineOrchestrator:
#     """Runs the full pipeline: collect -> normalize -> judge -> score -> draft."""
#
#     __init__(self, db_session: Session, connector: Connector,
#              judge: RelevanceJudge, draft_generator: DraftGenerator)
#
#     run_all(self, config: ProjectConfig, dry_run: bool = False) -> dict:
#         """Execute the full pipeline in sequence."""
#         from rich.progress import Progress, SpinnerColumn, TextColumn
#         from signalops.pipeline.collector import CollectorStage
#         from signalops.pipeline.normalizer import NormalizerStage
#         from signalops.pipeline.judge import JudgeStage
#         from signalops.pipeline.scorer import ScorerStage
#         from signalops.pipeline.drafter import DrafterStage
#
#         results = {}
#         stages = [
#             ("Collecting tweets", self._run_collect),
#             ("Normalizing posts", self._run_normalize),
#             ("Judging relevance", self._run_judge),
#             ("Scoring leads", self._run_score),
#             ("Generating drafts", self._run_draft),
#         ]
#
#         with Progress(SpinnerColumn(), TextColumn("{task.description}")) as progress:
#             for description, stage_fn in stages:
#                 task = progress.add_task(description)
#                 try:
#                     result = stage_fn(config, dry_run)
#                     results[description] = result
#                 except Exception as e:
#                     results[description] = {"error": str(e)}
#                     # Log error but continue to next stage
#                 progress.update(task, completed=True)
#
#         return results
#
#     _run_collect(self, config, dry_run) -> dict:
#         collector = CollectorStage(connector=self.connector, db_session=self.session)
#         return collector.run(config=config, dry_run=dry_run)
#
#     _run_normalize(self, config, dry_run) -> dict:
#         normalizer = NormalizerStage()
#         return normalizer.run(db_session=self.session, project_id=config.project_id, dry_run=dry_run)
#
#     _run_judge(self, config, dry_run) -> dict:
#         judge_stage = JudgeStage(judge=self.judge, db_session=self.session)
#         return judge_stage.run(project_id=config.project_id, config=config, dry_run=dry_run)
#
#     _run_score(self, config, dry_run) -> dict:
#         scorer = ScorerStage(db_session=self.session)
#         return scorer.run(project_id=config.project_id, config=config, dry_run=dry_run)
#
#     _run_draft(self, config, dry_run) -> dict:
#         drafter = DrafterStage(generator=self.draft_generator, db_session=self.session)
#         return drafter.run(project_id=config.project_id, config=config, dry_run=dry_run)
```

### File 13: `src/signalops/training/exporter.py`

```python
# class TrainingDataExporter:
#     __init__(self, db_session):
#         self.db = db_session
#
#     export_judgments(self, project_id: str, format: str = "openai",
#                     output: str = "judgments.jsonl") -> dict:
#         """Export human-corrected judgments as fine-tuning data."""
#         from signalops.storage.database import Judgment, NormalizedPost, Project
#         import json
#
#         judgments = self.db.query(Judgment).filter(
#             Judgment.project_id == project_id,
#             Judgment.human_label.isnot(None)
#         ).all()
#
#         records = []
#         for j in judgments:
#             post = self.db.query(NormalizedPost).filter_by(id=j.normalized_post_id).first()
#             project = self.db.query(Project).get(project_id)
#             # Build OpenAI fine-tuning format:
#             # {"messages": [{"role": "system", ...}, {"role": "user", ...}, {"role": "assistant", ...}]}
#             record = {
#                 "messages": [
#                     {"role": "system", "content": f"You are a relevance judge for {project.name if project else project_id}."},
#                     {"role": "user", "content": f"Tweet: '{post.text_cleaned if post else ''}'\nAuthor: @{post.author_username if post else 'unknown'}"},
#                     {"role": "assistant", "content": json.dumps({
#                         "label": j.human_label.value,
#                         "confidence": 0.95,
#                         "reasoning": j.human_reason or j.reasoning or ""
#                     })}
#                 ]
#             }
#             records.append(record)
#
#         with open(output, "w") as f:
#             for r in records:
#                 f.write(json.dumps(r) + "\n")
#
#         return {"records": len(records), "output": output}
#
#     export_draft_preferences(self, project_id: str,
#                               output: str = "preferences.jsonl") -> dict:
#         """Export draft edits as DPO preference pairs."""
#         from signalops.storage.database import Draft, DraftStatus, NormalizedPost
#         import json
#
#         drafts = self.db.query(Draft).filter(
#             Draft.project_id == project_id,
#             Draft.status == DraftStatus.EDITED,
#             Draft.text_final.isnot(None)
#         ).all()
#
#         records = []
#         for d in drafts:
#             post = self.db.query(NormalizedPost).filter_by(id=d.normalized_post_id).first()
#             record = {
#                 "prompt": f"Write a reply to: '{post.text_cleaned if post else ''}'",
#                 "chosen": d.text_final,
#                 "rejected": d.text_generated
#             }
#             records.append(record)
#
#         with open(output, "w") as f:
#             for r in records:
#                 f.write(json.dumps(r) + "\n")
#
#         return {"records": len(records), "output": output}
```

### File 14: `tests/test_cli.py`

```python
# Use Click's CliRunner to test CLI commands:
#
# from click.testing import CliRunner
# from signalops.cli.main import cli
#
# @pytest.fixture
# def runner():
#     return CliRunner()
#
# def test_cli_help(runner):
#     result = runner.invoke(cli, ["--help"])
#     assert result.exit_code == 0
#     assert "SignalOps" in result.output
#
# def test_project_list(runner, tmp_path):
#     # Create a temp projects dir with a YAML file
#     # Test `signalops project list`
#
# def test_project_set(runner, tmp_path):
#     # Test `signalops project set spectra`
#     # Verify active_project file is written
#
# def test_run_collect_help(runner):
#     result = runner.invoke(cli, ["run", "collect", "--help"])
#     assert result.exit_code == 0
#
# def test_run_all_help(runner):
#     result = runner.invoke(cli, ["run", "all", "--help"])
#     assert result.exit_code == 0
#
# def test_queue_list_help(runner):
#     result = runner.invoke(cli, ["queue", "list", "--help"])
#     assert result.exit_code == 0
#
# def test_queue_send_requires_confirm(runner):
#     # Without --confirm, should be dry-run preview
#     pass
#
# def test_stats_help(runner):
#     result = runner.invoke(cli, ["stats", "--help"])
#     assert result.exit_code == 0
#
# def test_export_help(runner):
#     result = runner.invoke(cli, ["export", "training-data", "--help"])
#     assert result.exit_code == 0
#
# def test_dry_run_flag(runner):
#     result = runner.invoke(cli, ["--dry-run", "run", "collect", "--help"])
#     assert result.exit_code == 0
#
# def test_format_json_flag(runner):
#     result = runner.invoke(cli, ["--format", "json", "stats", "--help"])
#     assert result.exit_code == 0
```

### File 15: `tests/integration/test_pipeline.py`

```python
# End-to-end pipeline test with mocked external APIs:
#
# @pytest.fixture
# def mock_connector():
#     """Returns a mock Connector that returns fake tweets."""
#     from unittest.mock import MagicMock
#     from signalops.connectors.base import RawPost, Connector
#     from datetime import datetime, timezone
#
#     connector = MagicMock(spec=Connector)
#     connector.search.return_value = [
#         RawPost(
#             platform="x",
#             platform_id="123",
#             author_id="456",
#             author_username="testuser",
#             author_display_name="Test User",
#             author_followers=1000,
#             author_verified=False,
#             text="Looking for a good code review tool. Anyone recommend?",
#             created_at=datetime.now(timezone.utc),
#             language="en",
#             reply_to_id=None,
#             conversation_id="123",
#             metrics={"likes": 5, "retweets": 1, "replies": 2, "views": 500},
#             entities={"urls": [], "mentions": [], "hashtags": []},
#             raw_json={"id": "123", "text": "Looking for a good code review tool."}
#         )
#     ]
#     connector.post_reply.return_value = "reply-789"
#     connector.health_check.return_value = True
#     return connector
#
# def test_full_pipeline_dry_run(db_session, sample_project_config, mock_connector):
#     """Run collect -> normalize -> judge -> score -> draft -> approve -> send (dry-run)."""
#     # This test verifies the full pipeline without external API calls.
#     # Mock the LLM gateway as well.
#     # Verify DB state at each stage:
#     #   After collect: raw_posts has rows
#     #   After normalize: normalized_posts has rows
#     #   After judge: judgments has rows
#     #   After score: scores has rows
#     #   After draft: drafts has rows with status=PENDING
#     #   After approve: draft status=APPROVED
#     #   After send (dry-run): draft status still APPROVED (not SENT)
```

**After creating Phase C4 files, run:**
```bash
pytest tests/test_cli.py -v
pytest tests/ -v
```

**Commit:**
```
feat(orchestrator): pipeline orchestrator and training data export
```

---

## PHASE C5: CI + Polish

### File 16: `.github/workflows/ci.yml`

```yaml
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

### File 17: `.env.example`

```bash
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

**After creating Phase C5 files:**
```bash
pytest tests/ -v --tb=short
```

**Commit:**
```
chore(ci): GitHub Actions CI pipeline
```

---

## ALSO CREATE: `tests/conftest.py` (if not already present)

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from signalops.storage.database import Base, init_db

@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    return engine

@pytest.fixture
def db_session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def sample_project_config():
    from signalops.config.schema import ProjectConfig, QueryConfig, RelevanceRubric, PersonaConfig
    return ProjectConfig(
        project_id="test-project",
        project_name="Test Project",
        description="A test project",
        queries=[QueryConfig(text="test query", label="test")],
        relevance=RelevanceRubric(
            system_prompt="You are a test judge.",
            positive_signals=["good signal"],
            negative_signals=["bad signal"],
        ),
        persona=PersonaConfig(
            name="Test Bot", role="tester", tone="helpful",
            voice_notes="Be helpful.", example_reply="Test reply.",
        ),
    )
```

---

## FINAL STEP

After all 5 phases are committed, verify everything passes:

```bash
pytest tests/ -v --tb=short
python -m signalops.cli.main --help
```

Then wait for Terminals A and B to finish. The merge will happen from a separate terminal.

**Your branch `feat/cli` is done when:**
- 6 stub files + 17 real files created
- All tests pass
- 5 commits on the branch
- `signalops --help` works
- No files outside your ownership were touched (except the 6 acknowledged stubs)

**At merge time:** Terminal A's real config/storage/connectors will replace your stubs. Terminal B's real models/pipeline stages will be added. Your lazy imports will "just work" because class names and signatures match the stubs.

# Terminal A — Foundation + Data Pipeline

> **Branch:** `feat/data`
> **Role:** You build the foundation that everything else depends on: config system, storage layer, connectors, collection, and normalization.
> **You are one of 3 parallel terminals. Terminals B and C are building the intelligence layer and CLI simultaneously on separate branches.**

---

## FIRST STEP — Run this immediately

```bash
git checkout feat/data
```

---

## RULES

1. **ONLY create/edit files listed in the File Ownership section below.** Do NOT touch any other files.
2. **Commit after each phase** with the exact commit message provided.
3. **Run tests after each phase** before moving to the next.
4. **Use parallel tool calls** — when creating independent files (e.g., schema.py + loader.py + defaults.py), write them all in one message.
5. **Run tests in background** — use `Bash(run_in_background=true)` for pytest while you continue writing the next phase's files.
6. **Use Task sub-agents** for complex files — spawn a sub-agent for database.py or x_api.py if needed.
7. **Be thorough** — these are the foundation types that Terminals B and C will import. Every field, every constraint, every index matters.

---

## FILE OWNERSHIP (20 files — only touch these)

```
src/signalops/config/schema.py
src/signalops/config/loader.py
src/signalops/config/defaults.py
src/signalops/storage/database.py
src/signalops/storage/audit.py
src/signalops/connectors/base.py
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

## PHASE A1: Config System

**Priority: HIGH — Other terminals depend on these Pydantic types.**

### File 1: `src/signalops/config/schema.py`

All Pydantic models for project configuration. Implement EXACTLY these classes:

```python
from pydantic import BaseModel, Field

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
    relevance_judgment: float = 0.35
    author_authority: float = 0.25
    engagement_signals: float = 0.15
    recency: float = 0.15
    intent_strength: float = 0.10

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

### File 2: `src/signalops/config/loader.py`

YAML config loader with environment variable resolution:

```python
# Must implement:
# - load_project(path: str | Path) -> ProjectConfig
#   Loads YAML, resolves ${ENV_VAR} patterns, validates with Pydantic
# - _resolve_env_vars(obj) -> obj
#   Recursively replaces ${VAR} with os.environ[VAR] in strings, dicts, lists
# - config_hash(path: str | Path) -> str
#   Returns SHA-256 hex digest of config file for change detection
```

Implementation reference:

```python
import yaml
import os
import hashlib
from pathlib import Path
from .schema import ProjectConfig

def load_project(path: str | Path) -> ProjectConfig:
    path = Path(path)
    with open(path) as f:
        raw = yaml.safe_load(f)
    raw = _resolve_env_vars(raw)
    config = ProjectConfig(**raw)
    return config

def _resolve_env_vars(obj):
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
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()
```

### File 3: `src/signalops/config/defaults.py`

Default constants used across the application:

```python
# Define:
# - DEFAULT_DB_URL = "sqlite:///signalops.db"
# - DEFAULT_CREDENTIALS_DIR = Path.home() / ".signalops"
# - DEFAULT_PROJECTS_DIR = Path("projects")
# - MAX_TWEET_LENGTH = 280
# - MAX_REPLY_LENGTH = 240
# - DEFAULT_SEARCH_MAX_RESULTS = 100
# - DEFAULT_RATE_LIMITS (dict with max_replies_per_hour, max_replies_per_day)
# - SUPPORTED_PLATFORMS = ["x"]
# - SUPPORTED_LANGUAGES = ["en", "es", "fr", "de", "pt", "ja"]
```

### File 4: `projects/spectra.yaml`

Create the full Spectra AI example config. This is a code review tool:

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

### File 5: `projects/salesense.yaml`

Create the full SaleSense example config. This is a conversational AI platform for visitor qualification:

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

### File 6: `tests/unit/test_config.py`

Test cases to write:
- `test_load_spectra_config()` — loads projects/spectra.yaml, asserts project_id, query count, ICP fields
- `test_load_salesense_config()` — loads projects/salesense.yaml, asserts all fields
- `test_env_var_resolution()` — set env var, verify it resolves in config string
- `test_env_var_unset_passthrough()` — unset env var keeps `${VAR}` as-is
- `test_invalid_config_missing_required()` — missing `project_id` raises ValidationError
- `test_invalid_config_bad_type()` — wrong type for `min_followers` raises ValidationError
- `test_default_values()` — ICPConfig() has correct defaults
- `test_scoring_weights_defaults()` — ScoringWeights defaults sum to ~1.0
- `test_config_hash()` — same file produces same hash, different file produces different hash

**After creating all Phase A1 files, run:**
```bash
pytest tests/unit/test_config.py -v
```

**Commit:**
```
feat(config): config system with Pydantic schemas and YAML loader
```

---

## PHASE A2: Storage Layer

### File 7: `src/signalops/storage/database.py`

ALL SQLAlchemy models. This is the most critical file — implement EVERY table, enum, constraint, and index:

**Enums:**
- `JudgmentLabel` — RELEVANT, IRRELEVANT, MAYBE
- `DraftStatus` — PENDING, APPROVED, EDITED, REJECTED, SENT, FAILED
- `OutcomeType` — REPLY_RECEIVED, LIKE_RECEIVED, FOLLOW_RECEIVED, PROFILE_CLICK, LINK_CLICK, BOOKING, NEGATIVE

**Tables (with all columns, FKs, constraints, indexes):**
- `Project` — id (PK, String(64)), name, config_path, config_hash, created_at, updated_at, is_active
- `RawPost` — id (auto PK), project_id (FK), platform, platform_id, collected_at, query_used, raw_json. UniqueConstraint on (platform, platform_id, project_id). Index on (project_id, collected_at).
- `NormalizedPost` — id (auto PK), raw_post_id (FK, unique), project_id (FK), platform, platform_id, author_id, author_username, author_display_name, author_followers, author_verified, text_original, text_cleaned, language, created_at, reply_to_id, conversation_id, likes, retweets, replies, views, hashtags (JSON), mentions (JSON), urls (JSON). Index on (project_id, author_id) and (project_id, created_at).
- `Judgment` — id (auto PK), normalized_post_id (FK), project_id (FK), label (enum), confidence, reasoning, model_id, model_version, latency_ms, created_at, human_label (nullable enum), human_corrected_at, human_reason. Index on (project_id, label).
- `Score` — id (auto PK), normalized_post_id (FK), project_id (FK), total_score, components (JSON), scoring_version, created_at. Index on (project_id, total_score).
- `Draft` — id (auto PK), normalized_post_id (FK), project_id (FK), text_generated, text_final (nullable), tone, template_used, model_id, status (enum, default PENDING), created_at, approved_at, sent_at, sent_post_id. Index on (project_id, status).
- `Outcome` — id (auto PK), draft_id (FK), project_id (FK), outcome_type (enum), details (JSON), observed_at.
- `AuditLog` — id (auto PK), project_id, action, entity_type, entity_id, details (JSON), user, timestamp. Index on (project_id, action) and (timestamp).

**Also include helper functions:**
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

def get_engine(db_url: str = "sqlite:///signalops.db"):
    return create_engine(db_url, echo=False)

def get_session(engine) -> Session:
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()

def init_db(engine):
    """Create all tables."""
    Base.metadata.create_all(engine)
```

### File 8: `src/signalops/storage/audit.py`

Append-only audit logger:

```python
# Implement:
# - log_action(session, project_id, action, entity_type=None, entity_id=None, details=None, user="system")
#   Creates an AuditLog row and commits
# - get_recent_actions(session, project_id, limit=50) -> list[AuditLog]
#   Returns most recent audit entries for a project
```

### File 9: `tests/conftest.py`

Shared test fixtures that ALL terminals will use:

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from signalops.storage.database import Base, init_db

@pytest.fixture
def engine():
    """In-memory SQLite for tests."""
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    return engine

@pytest.fixture
def db_session(engine):
    """DB session that rolls back after each test."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def sample_project_config():
    """Returns a minimal ProjectConfig for testing."""
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
            name="Test Bot",
            role="tester",
            tone="helpful",
            voice_notes="Be helpful.",
            example_reply="This is a test reply.",
        ),
    )

@pytest.fixture
def sample_raw_post_data():
    """Returns dict matching X API v2 tweet response structure."""
    return {
        "data": {
            "id": "1234567890",
            "text": "Just spent 3 hours reviewing a PR that should have taken 30 minutes. There has to be a better way.",
            "author_id": "9876543210",
            "created_at": "2026-02-18T12:00:00.000Z",
            "conversation_id": "1234567890",
            "public_metrics": {
                "like_count": 15,
                "retweet_count": 3,
                "reply_count": 5,
                "impression_count": 2500
            },
            "entities": {
                "urls": [],
                "mentions": [],
                "hashtags": []
            },
            "lang": "en"
        },
        "includes": {
            "users": [{
                "id": "9876543210",
                "username": "techleadSara",
                "name": "Sara Chen",
                "public_metrics": {"followers_count": 2340},
                "verified": False,
                "description": "Senior engineer @BigCorp. Building distributed systems."
            }]
        }
    }
```

**After creating Phase A2 files, run:**
```bash
pytest tests/ -v
```

**Commit:**
```
feat(storage): SQLAlchemy models, audit logger, and test fixtures
```

---

## PHASE A3: Connectors

### File 10: `src/signalops/connectors/base.py`

Abstract base class and the shared `RawPost` dataclass:

```python
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

### File 11: `src/signalops/connectors/rate_limiter.py`

Sliding window rate limiter with jitter:

```python
# Implement class RateLimiter:
#   __init__(self, max_requests: int, window_seconds: int, jitter_range: float = 0.2)
#   acquire(self) -> float:
#       Returns 0.0 if allowed immediately, or seconds to wait if rate limited.
#       Uses a sliding window of timestamps.
#   update_from_headers(self, headers: dict) -> None:
#       Updates internal state from X API rate limit headers:
#       x-rate-limit-remaining, x-rate-limit-reset
#   _add_jitter(self, wait_time: float) -> float:
#       Adds ±jitter_range randomization to wait time
#   @property tokens(self) -> int:
#       Returns remaining requests in current window
```

### File 12: `src/signalops/connectors/x_auth.py`

OAuth 2.0 PKCE flow for X API:

```python
# Implement:
# - generate_pkce_pair() -> tuple[str, str]:  (code_verifier, code_challenge)
# - build_auth_url(client_id, redirect_uri, code_challenge, scopes) -> str
# - exchange_code(client_id, client_secret, code, code_verifier, redirect_uri) -> dict:
#     Returns {"access_token": ..., "refresh_token": ..., "expires_at": ...}
# - refresh_token(client_id, client_secret, refresh_token) -> dict:
#     Returns new token set
# - store_credentials(credentials: dict, path: Path = DEFAULT_CREDENTIALS_PATH) -> None
# - load_credentials(path: Path = DEFAULT_CREDENTIALS_PATH) -> dict | None
# - is_token_expired(credentials: dict) -> bool
#
# Use httpx for HTTP calls to https://api.x.com/2/oauth2/token
# Store tokens as JSON in ~/.signalops/credentials.json
# PKCE: use hashlib.sha256 + base64url encoding for code_challenge
```

### File 13: `src/signalops/connectors/x_api.py`

X API v2 connector implementation:

```python
# class XConnector(Connector):
#   __init__(self, bearer_token: str, rate_limiter: RateLimiter | None = None)
#
#   search(self, query, since_id=None, max_results=100) -> list[RawPost]:
#       GET https://api.x.com/2/tweets/search/recent
#       Query params: query, max_results, since_id, tweet.fields, user.fields, expansions
#       Required fields: author_id, created_at, public_metrics, entities, conversation_id, lang
#       Expansions: author_id
#       Parse response into list[RawPost]
#       Respect rate limiter (call acquire() before each request)
#       Update rate limiter from response headers
#
#   get_user(self, user_id) -> dict:
#       GET https://api.x.com/2/users/{user_id}
#       Returns user profile dict
#
#   post_reply(self, in_reply_to_id, text) -> str:
#       POST https://api.x.com/2/tweets
#       Body: {"text": text, "reply": {"in_reply_to_tweet_id": in_reply_to_id}}
#       Returns new tweet ID
#       Requires OAuth user token (not bearer token)
#
#   health_check(self) -> bool:
#       Try GET https://api.x.com/2/tweets/search/recent?query=test&max_results=10
#       Return True if 200, False otherwise
#
#   _parse_tweet(self, tweet_data: dict, includes: dict) -> RawPost:
#       Parse a single X API v2 tweet+includes into a RawPost dataclass
#
# Use httpx.Client for all HTTP calls
# Set User-Agent header
# Handle 429 (rate limited) responses with retry-after header
```

### File 14: `tests/unit/test_rate_limiter.py`

```python
# Test cases:
# - test_allows_within_limit: 10 acquires on limit=10 all return 0.0
# - test_blocks_over_limit: 3rd acquire on limit=2 returns >0.0
# - test_window_expiry: after window_seconds pass, requests are allowed again (mock time)
# - test_update_from_headers: setting remaining=5 and reset=future updates internal state
# - test_jitter_range: wait times vary within ±jitter_range (run multiple times)
# - test_tokens_property: reflects remaining requests accurately
```

### File 15: `tests/fixtures/tweets.json`

Create 20 realistic X API v2 tweet payloads. Include variety:
- 5 highly relevant (code review pain, tool search)
- 5 somewhat relevant (tangential mentions)
- 5 irrelevant (hiring posts, jokes, spam)
- 5 edge cases (non-English, deleted author, zero engagement, very long text, reply chains)

Each payload should follow the X API v2 response format:
```json
{
  "data": {"id": "...", "text": "...", "author_id": "...", "created_at": "...", "public_metrics": {...}, "entities": {...}, "lang": "..."},
  "includes": {"users": [{"id": "...", "username": "...", "name": "...", "public_metrics": {"followers_count": ...}, "verified": false, "description": "..."}]}
}
```

**After creating Phase A3 files, run:**
```bash
pytest tests/unit/test_rate_limiter.py -v
```

**Commit:**
```
feat(connectors): X API v2 connector, OAuth 2.0 PKCE, rate limiter
```

---

## PHASE A4: Collection + Normalization Pipeline

### File 16: `src/signalops/pipeline/collector.py`

```python
# class CollectorStage:
#   __init__(self, connector: Connector, db_session: Session)
#
#   run(self, config: ProjectConfig, dry_run: bool = False) -> dict:
#       For each enabled query in config.queries:
#           Load since_id for this query from DB (last collected platform_id)
#           Call connector.search(query.text, since_id, query.max_results_per_run)
#           For each RawPost:
#               Check dedup: (platform, platform_id, project_id) unique constraint
#               If not duplicate: insert into raw_posts table
#               If dry_run: don't insert, just count
#           Log audit: action="collect", details={query, new_count, skipped_count}
#       Return summary dict: {total_new, total_skipped, per_query_counts}
#
#   _get_since_id(self, project_id: str, query_text: str) -> str | None:
#       Query raw_posts for max(platform_id) where project_id and query_used match
#
# Handle IntegrityError on duplicate gracefully (skip, don't crash)
```

### File 17: `src/signalops/pipeline/normalizer.py`

```python
# class NormalizerStage:
#   run(self, db_session: Session, project_id: str, dry_run: bool = False) -> dict:
#       Query raw_posts that don't have a corresponding normalized_post yet
#       For each raw_post:
#           Parse raw_json to extract fields
#           Clean text: strip URLs (regex), collapse whitespace, strip leading/trailing
#           Extract entities: hashtags, mentions, urls from raw_json entities field
#           Detect language (from API field, or simple heuristic fallback)
#           Create NormalizedPost row
#           If dry_run: don't insert
#       Return summary: {processed_count, skipped_count}
#
# Helper functions (export these for testing):
# - clean_text(text: str) -> str: strip URLs, collapse whitespace
# - extract_hashtags(entities: dict) -> list[str]
# - extract_mentions(entities: dict) -> list[str]
# - extract_urls(entities: dict) -> list[str]
# - detect_language(text: str, api_lang: str | None) -> str | None
```

### File 18: `tests/unit/test_normalizer.py`

```python
# Test the exported helper functions:
# - test_strip_urls: "Check out https://t.co/abc123 and more" -> "Check out and more"
# - test_strip_multiple_urls: handles multiple URLs
# - test_preserve_mentions: "@alice said hello" keeps @alice
# - test_collapse_whitespace: "too   many    spaces" -> "too many spaces"
# - test_strip_leading_trailing: "  hello  " -> "hello"
# - test_extract_hashtags: from entities dict format
# - test_extract_mentions: from entities dict format
# - test_extract_urls: from entities dict format
# - test_detect_language_from_api: uses API field when present
# - test_detect_language_fallback: handles None api_lang
# - test_empty_text: handles empty string gracefully
# - test_text_with_only_urls: "https://t.co/abc" -> "" (empty after stripping)
```

### File 19: `tests/integration/test_collector.py`

```python
# Use respx to mock httpx calls:
# - test_collector_stores_tweets: mock search endpoint, run collector, verify raw_posts in DB
# - test_collector_deduplication: run collector twice with same tweets, verify no duplicates
# - test_collector_incremental: first run collects 10, second run with since_id collects 5 new
# - test_collector_dry_run: dry_run=True doesn't insert rows
# - test_collector_empty_results: mock empty API response, verify no crash
# - test_collector_multiple_queries: 3 queries, verify all are executed
# - test_collector_disabled_query: query with enabled=False is skipped
# - test_collector_audit_log: verify audit_logs table has collect entries
```

### File 20: `.env.example`

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

**After creating Phase A4 files, run:**
```bash
pytest tests/ -v
```

**Commit:**
```
feat(pipeline): collector and normalizer stages with tests
```

---

## FINAL STEP

After all 4 phases are committed, verify everything passes:

```bash
pytest tests/ -v --tb=short
```

Then wait for Terminals B and C to finish. The merge will happen from a separate terminal.

**Your branch `feat/data` is done when:**
- All 20 files created
- All tests pass
- 4 commits on the branch
- No files outside your ownership were touched

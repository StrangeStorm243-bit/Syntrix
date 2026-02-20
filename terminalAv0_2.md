# Terminal A — Infrastructure & Data Layer (v0.2)

> **Branch:** `v02/infra` | **Worktree:** `.claude/worktrees/v02-infra`
> **Role:** Foundation layer — Redis caching, Filtered Stream, engagement polling, multi-project.
> **Merge order:** A merges FIRST (B and C depend on infrastructure).

---

## Step 0: Pre-Flight — Create All Worktrees

**You (Terminal A) are responsible for setting up the worktree isolation for ALL terminals.**
Run these commands before starting any implementation work:

```bash
cd /c/Users/niran/OneDrive/Desktop/Syntrix

# Ensure main is clean
git status
git log --oneline -5

# Create all 3 worktrees
git worktree add .claude/worktrees/v02-infra    -b v02/infra
git worktree add .claude/worktrees/v02-learning -b v02/learning
git worktree add .claude/worktrees/v02-ux       -b v02/ux

# Verify
git worktree list

# Install dev deps in all worktrees
cd .claude/worktrees/v02-infra && pip install -e ".[dev]" && cd -
cd .claude/worktrees/v02-learning && pip install -e ".[dev]" && cd -
cd .claude/worktrees/v02-ux && pip install -e ".[dev]" && cd -
```

After worktrees are ready, navigate to YOUR worktree:
```bash
cd /c/Users/niran/OneDrive/Desktop/Syntrix/.claude/worktrees/v02-infra
```

---

## Step 0.5: Launch Terminal B and Terminal C

Once worktrees are created, open two more terminal windows and paste these commands:

### Copy-Paste for Terminal B
```bash
cd /c/Users/niran/OneDrive/Desktop/Syntrix/.claude/worktrees/v02-learning && claude
```
Then paste the contents of `terminalBv0_2.md` as the prompt.

### Copy-Paste for Terminal C
```bash
cd /c/Users/niran/OneDrive/Desktop/Syntrix/.claude/worktrees/v02-ux && claude
```
Then paste the contents of `terminalCv0_2.md` as the prompt.

---

## Context

Read PLANA.md and CLAUDE.md for full project context. You are Terminal A in a 3-terminal parallel v0.2 build.

This is NOT greenfield. The v0.1 codebase (45 source files) is complete. You are MODIFYING existing files and adding new ones. **Read each file BEFORE modifying it.** Understand existing patterns. Match the code style.

### Critical Rules
- Redis is OPTIONAL — every Redis operation must have an in-memory/no-op fallback. Never crash if Redis is unavailable.
- `from __future__ import annotations` in all files
- `dict[str, Any]` not bare `dict` (mypy strict)
- SQLAlchemy Column assignments: `# type: ignore[assignment]`
- 100-char line length (ruff)
- Run CI checks after each phase: `ruff check`, `ruff format --check`, `mypy --strict`, `pytest`

---

## File Ownership

You own these files and ONLY these files. Do not touch anything else.

```
NEW FILES:
src/signalops/storage/cache.py              ← Redis/in-memory cache backend
src/signalops/connectors/x_stream.py        ← Filtered Stream connector (interface + stub)
tests/unit/test_cache.py                     ← Cache backend tests
tests/unit/test_engagement_polling.py        ← Engagement polling tests
tests/unit/test_stream.py                    ← Stream connector tests

MODIFIED FILES:
src/signalops/config/schema.py              ← Add RedisConfig, StreamConfig models
src/signalops/config/loader.py              ← Multi-project helpers
src/signalops/connectors/x_api.py           ← Add get_tweet_metrics() method
src/signalops/connectors/rate_limiter.py    ← Optional Redis-backed state
src/signalops/pipeline/collector.py         ← Cache-accelerated dedup, stream mode
src/signalops/cli/project.py               ← Project init wizard
pyproject.toml                              ← Add redis dependency
tests/unit/test_config.py                   ← Tests for new config fields
tests/integration/test_collector.py         ← Cache dedup integration tests
```

---

## Phase A1: Redis Caching Layer

### 1. MODIFY `src/signalops/config/schema.py`

Add two new Pydantic models and wire them into ProjectConfig:

```python
class RedisConfig(BaseModel):
    url: str = "redis://localhost:6379/0"
    enabled: bool = False
    search_cache_ttl: int = 1800     # 30 min
    dedup_ttl: int = 86400           # 24 hours
    rate_limit_ttl: int = 900        # 15 min

class StreamConfig(BaseModel):
    enabled: bool = False
    rules: list[str] = []
    backfill_minutes: int = 5
```

Add to `ProjectConfig`:
```python
redis: RedisConfig = RedisConfig()
stream: StreamConfig = StreamConfig()
```

### 2. MODIFY `pyproject.toml`

Add `"redis>=5.0"` to the `dependencies` list.
Add `"scikit-learn>=1.4"` to the `dev` optional-dependencies list (Terminal B needs it for eval).

### 3. NEW `src/signalops/storage/cache.py`

Redis cache wrapper with in-memory fallback:
- `CacheBackend` ABC with: `get(key)`, `set(key, value, ttl)`, `exists(key)`, `delete(key)`
- `RedisCache(CacheBackend)` — wraps redis-py, lazy connection
- `InMemoryCache(CacheBackend)` — dict-based fallback with TTL via timestamps
- `get_cache(config: RedisConfig) -> CacheBackend` — factory: returns RedisCache if enabled and connectable, else InMemoryCache with a warning log
- Search cache helpers: `cache_search_results(query, results, ttl)`, `get_cached_search(query) -> results | None`
- Dedup cache helpers: `is_duplicate(platform, platform_id, project_id) -> bool`, `mark_seen(platform, platform_id, project_id, ttl)`

### 4. NEW `tests/unit/test_cache.py`

Test both backends:
- get/set/exists/delete for InMemoryCache
- get/set/exists/delete for RedisCache (mock redis-py)
- TTL expiry for InMemoryCache
- Graceful fallback when Redis connection fails
- Search caching round-trip
- Dedup check logic

### Verify Phase A1
```bash
pytest tests/unit/test_cache.py tests/unit/test_config.py -v
ruff check src/signalops/storage/cache.py src/signalops/config/schema.py
mypy src/signalops/storage/cache.py src/signalops/config/schema.py --strict
```

### Commit
```
feat(cache): Redis caching layer with in-memory fallback
```

---

## Phase A2: Redis Integration with Existing Pipeline

### 5. MODIFY `src/signalops/connectors/rate_limiter.py`

Read the file first. Add optional Redis-backed state:
- Add `cache: CacheBackend | None = None` parameter to `__init__`
- If cache provided, persist rate limit state (remaining tokens, window reset time) to cache
- If no cache, behavior is identical to v0.1 (in-memory only)
- This allows rate limit state to survive process restarts

### 6. MODIFY `src/signalops/pipeline/collector.py`

Read the file first. Add cache-accelerated dedup:
- Add optional `cache: CacheBackend | None = None` parameter
- Before the existing DB UniqueConstraint dedup check, do a fast cache check: `cache.is_duplicate(platform, platform_id, project_id)`
- After storing a new post, `cache.mark_seen(platform, platform_id, project_id)`
- Cache miss falls through to existing DB check (current behavior preserved exactly)
- Also add search result caching: before calling `connector.search()`, check `cache.get_cached_search(query)`

### 7. MODIFY `tests/integration/test_collector.py`

Add tests for cache-accelerated dedup:
- Test collector with InMemoryCache — verify cache is checked before DB
- Test collector without cache — existing behavior preserved exactly
- Test cache-hit skips DB query

### Verify Phase A2
```bash
pytest tests/unit/ tests/integration/test_collector.py -v
ruff check src/ tests/ && ruff format --check src/ tests/
mypy src/signalops --strict
```

### Commit
```
feat(cache): integrate Redis cache with collector dedup and rate limiter
```

---

## Phase A3: Engagement Polling (for Outcome Tracking)

### 8. MODIFY `src/signalops/connectors/x_api.py`

Read the file first. Add engagement polling method to `XConnector`:

```python
def get_tweet_metrics(self, tweet_ids: list[str]) -> dict[str, dict[str, int]]:
    """Fetch current engagement metrics for tweets.

    Used by outcome tracker to check if sent replies got engagement.
    Uses X API v2 GET /2/tweets with tweet.fields=public_metrics.
    Batches up to 100 IDs per request.

    Returns: {"tweet_id": {"likes": N, "retweets": N, "replies": N, "views": N}}
    """
```

### 9. NEW `tests/unit/test_engagement_polling.py`

Mock X API responses with respx:
- Test single tweet metrics fetch
- Test batch of 100+ IDs (splits into multiple requests)
- Test handling of deleted/unavailable tweets
- Test rate limit respect
- Test error handling (API errors, timeouts)

### Verify Phase A3
```bash
pytest tests/unit/test_engagement_polling.py -v
ruff check src/ tests/ && ruff format --check src/ tests/
mypy src/signalops --strict
```

### Commit
```
feat(connectors): engagement polling for outcome tracking
```

---

## Phase A4: Filtered Stream (Interface + Stub)

### 10. NEW `src/signalops/connectors/x_stream.py`

Filtered Stream connector (requires X API Pro tier — $5K/month):

```python
class StreamConnector:
    def __init__(self, bearer_token: str, rate_limiter: RateLimiter | None = None) -> None: ...

    def check_tier(self) -> bool:
        """Verify Pro tier access. Raises clear error if not available."""

    def add_rules(self, rules: list[str]) -> list[str]:
        """Add stream filter rules. Returns rule IDs."""

    def delete_rules(self, rule_ids: list[str]) -> None:
        """Delete stream filter rules."""

    def stream(self, callback: Callable[[RawPost], None], backfill_minutes: int = 5) -> None:
        """Connect to Filtered Stream, parse tweets, call callback for each.
        Includes reconnection with exponential backoff."""
```

- Uses httpx streaming response to X API v2 `POST /2/tweets/search/stream`
- Parses each line as JSON, converts to `RawPost`, calls callback
- Reconnection logic with exponential backoff (1s, 2s, 4s, 8s, max 60s)
- `check_tier()` verifies access, raises: "Filtered Stream requires X API Pro tier ($5K/month)"

### 11. MODIFY `src/signalops/pipeline/collector.py`

Add stream collection mode:
- Add `run_stream(config, callback, duration_seconds)` method to `CollectorStage`
- Instantiates `StreamConnector`, adds rules from `config.stream.rules`
- Stores incoming posts same as search mode (dedup via cache, normalize)
- This is an alternative to the existing `run()` search mode

### 12. NEW `tests/unit/test_stream.py`

Mock httpx for all tests:
- Test stream JSON line parsing → RawPost conversion
- Test reconnection on disconnect
- Test rule management (add/delete)
- Test check_tier error handling
- Test backoff timing

### Verify Phase A4
```bash
pytest tests/unit/test_stream.py -v
ruff check src/ tests/ && ruff format --check src/ tests/
mypy src/signalops --strict
```

### Commit
```
feat(stream): Filtered Stream connector interface and stub
```

---

## Phase A5: Multi-Project Enhancements

### 13. MODIFY `src/signalops/config/loader.py`

Read the file first. Add multi-project helpers:

```python
def scan_projects(directory: str | Path = "projects") -> list[ProjectConfig]:
    """Scan projects/ directory and load all valid configs."""

def get_active_project() -> str | None:
    """Read active project ID from ~/.signalops/active_project."""

def set_active_project(project_id: str) -> None:
    """Write active project ID to ~/.signalops/active_project."""

def resolve_project(project_name: str | None, ctx: click.Context | None = None) -> ProjectConfig:
    """Resolve project from --project flag, active project, or error."""
```

### 14. MODIFY `src/signalops/cli/project.py`

Read the file first. Enhance existing commands:
- `project list` — Rich table with project name, query count, active indicator
- `project set <name>` — validate project exists before setting, show confirmation
- `project init` — NEW interactive wizard using Rich prompts:
  - Prompt for: project_id, project_name, description, product_url
  - Prompt for queries (add multiple, loop until done)
  - Prompt for ICP settings (min_followers, languages)
  - Prompt for persona (name, role, tone, voice_notes)
  - Generate and save to `projects/<project_id>.yaml`
  - Validate with Pydantic before saving

### 15. MODIFY `tests/unit/test_config.py`

Add tests for new functionality:
- Test `RedisConfig` and `StreamConfig` default values
- Test `ProjectConfig` with redis/stream fields in YAML
- Test `scan_projects()` finds all YAML files
- Test `resolve_project()` with --project flag, active project, and error case

### Verify Phase A5
```bash
pytest tests/unit/test_config.py -v
ruff check src/ tests/ && ruff format --check src/ tests/
mypy src/signalops --strict
```

### Commit
```
feat(project): multi-project enhancements with init wizard
```

---

## Final Verification (before signaling DONE)

Run the full CI suite from your worktree:

```bash
cd /c/Users/niran/OneDrive/Desktop/Syntrix/.claude/worktrees/v02-infra

# Lint + format
ruff check src/ tests/
ruff format --check src/ tests/

# Type check
mypy src/signalops --strict

# All tests (existing v0.1 + your new tests)
pytest tests/ -v --tb=short

# Verify all commits are clean
git log --oneline v02/infra ^main
```

All 5 commits should be on the `v02/infra` branch:
1. `feat(cache): Redis caching layer with in-memory fallback`
2. `feat(cache): integrate Redis cache with collector dedup and rate limiter`
3. `feat(connectors): engagement polling for outcome tracking`
4. `feat(stream): Filtered Stream connector interface and stub`
5. `feat(project): multi-project enhancements with init wizard`

**Signal DONE when all CI checks pass.**

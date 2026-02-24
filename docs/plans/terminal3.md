# Terminal 3 — Batch Processing + Plugin/Scoring System

> **Scope:** Async batch collection, extensible scoring engine with plugin architecture
> **New files:** `pipeline/batch.py`, `scoring/` package (new)
> **Touches existing:** `scorer.py`, `schema.py`, `orchestrator.py`, `collector.py`
> **Depends on:** None (isolated until Phase 3)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Phase 1 — Batch Processing](#2-phase-1--batch-processing)
3. [Phase 2 — Scoring Plugin System](#3-phase-2--scoring-plugin-system)
4. [Phase 3 — Config-Driven Scoring Rules](#4-phase-3--config-driven-scoring-rules)
5. [Phase 4 — Integration & CLI](#5-phase-4--integration--cli)
6. [File Manifest](#6-file-manifest)
7. [Testing Plan](#7-testing-plan)

---

## 1. Overview

This terminal delivers two features:

1. **Batch Processing** — Run multiple search queries concurrently using `asyncio` + `httpx.AsyncClient`.
   Respects rate limits across concurrent queries. Supports resume if interrupted.

2. **Plugin/Scoring System** — Extract the current scorer into a pluggable architecture. Users
   can customize scoring via YAML config rules, and developers can create pip-installable
   scoring plugins. The existing weighted scorer becomes the default built-in plugin.

**Key design decisions:**
- Async batch processing is opt-in (`--batch` flag) — sync mode remains default
- Scoring plugins use Python entry points (setuptools) for discoverability
- Config-driven rules require no Python code from end users
- The scoring engine chains plugins: base score → rule adjustments → final score
- All existing scorer tests must continue to pass (backward compatible)

---

## 2. Phase 1 — Batch Processing

### Step 1: Async HTTP Client

**Create `src/signalops/connectors/async_client.py`:**

```python
"""Async HTTP client wrapper for concurrent API calls."""

from __future__ import annotations

from typing import Any

import httpx


class AsyncXClient:
    """Async wrapper around X API v2 for concurrent search queries."""

    def __init__(
        self,
        bearer_token: str,
        base_url: str = "https://api.twitter.com/2",
        timeout: float = 30.0,
    ) -> None:
        self._bearer_token = bearer_token
        self._base_url = base_url
        self._timeout = timeout

    async def search_recent(
        self,
        query: str,
        max_results: int = 100,
        since_id: str | None = None,
        tweet_fields: str = "created_at,public_metrics,entities,lang,conversation_id",
        user_fields: str = "name,username,public_metrics,verified,description",
        expansions: str = "author_id",
    ) -> dict[str, Any]:
        """Search recent tweets. Returns raw API response dict."""
        params: dict[str, str | int] = {
            "query": query,
            "max_results": max_results,
            "tweet.fields": tweet_fields,
            "user.fields": user_fields,
            "expansions": expansions,
        }
        if since_id:
            params["since_id"] = since_id

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(
                f"{self._base_url}/tweets/search/recent",
                params=params,
                headers={"Authorization": f"Bearer {self._bearer_token}"},
            )
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
```

### Step 2: Batch Collector

**Create `src/signalops/pipeline/batch.py`:**

```python
"""Batch collection — runs multiple search queries concurrently."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from signalops.config.schema import ProjectConfig, QueryConfig
from signalops.connectors.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


@dataclass
class BatchQueryResult:
    """Result of a single query in the batch."""
    query_label: str
    query_text: str
    tweets_found: int
    new_tweets: int          # After deduplication
    error: str | None = None
    since_id_used: str | None = None
    latest_id: str | None = None  # For resume


@dataclass
class BatchResult:
    """Aggregate result of batch collection."""
    total_queries: int
    successful_queries: int
    failed_queries: int
    total_tweets_found: int
    total_new_tweets: int
    query_results: list[BatchQueryResult] = field(default_factory=list)


class BatchCollector:
    """Runs multiple search queries concurrently, respecting rate limits."""

    def __init__(
        self,
        bearer_token: str,
        db_session: Session,
        rate_limiter: RateLimiter,
        concurrency: int = 3,
    ) -> None:
        self._bearer_token = bearer_token
        self._session = db_session
        self._rate_limiter = rate_limiter
        self._concurrency = concurrency
        self._semaphore = asyncio.Semaphore(concurrency)

    async def run(
        self,
        config: ProjectConfig,
        dry_run: bool = False,
    ) -> BatchResult:
        """Execute all enabled queries concurrently."""
        enabled_queries = [q for q in config.queries if q.enabled]
        result = BatchResult(
            total_queries=len(enabled_queries),
            successful_queries=0,
            failed_queries=0,
            total_tweets_found=0,
            total_new_tweets=0,
        )

        # Create tasks for all queries
        tasks = [
            self._run_query(query, config, dry_run)
            for query in enabled_queries
        ]

        # Run with concurrency limit
        query_results = await asyncio.gather(*tasks, return_exceptions=True)

        for qr in query_results:
            if isinstance(qr, Exception):
                result.failed_queries += 1
                result.query_results.append(
                    BatchQueryResult(
                        query_label="unknown",
                        query_text="unknown",
                        tweets_found=0,
                        new_tweets=0,
                        error=str(qr),
                    )
                )
            else:
                assert isinstance(qr, BatchQueryResult)
                result.query_results.append(qr)
                if qr.error:
                    result.failed_queries += 1
                else:
                    result.successful_queries += 1
                result.total_tweets_found += qr.tweets_found
                result.total_new_tweets += qr.new_tweets

        return result

    async def _run_query(
        self,
        query: QueryConfig,
        config: ProjectConfig,
        dry_run: bool,
    ) -> BatchQueryResult:
        """Run a single query with rate limiting and semaphore."""
        async with self._semaphore:
            # Respect rate limits
            wait_time = self._rate_limiter.acquire()
            if wait_time > 0:
                logger.info(
                    "Rate limit: waiting %.1fs before query '%s'",
                    wait_time, query.label,
                )
                await asyncio.sleep(wait_time)

            try:
                from signalops.connectors.async_client import AsyncXClient

                client = AsyncXClient(bearer_token=self._bearer_token)

                # Get since_id for incremental collection
                since_id = self._get_since_id(config.project_id, query.text)

                response = await client.search_recent(
                    query=query.text,
                    max_results=query.max_results_per_run,
                    since_id=since_id,
                )

                tweets = response.get("data", [])
                users = {
                    u["id"]: u
                    for u in response.get("includes", {}).get("users", [])
                }

                new_count = 0
                latest_id: str | None = None

                if not dry_run:
                    new_count = self._store_tweets(
                        tweets, users, config.project_id, query.text
                    )
                else:
                    new_count = len(tweets)

                if tweets:
                    latest_id = str(tweets[0].get("id", ""))

                return BatchQueryResult(
                    query_label=query.label,
                    query_text=query.text,
                    tweets_found=len(tweets),
                    new_tweets=new_count,
                    since_id_used=since_id,
                    latest_id=latest_id,
                )

            except Exception as e:
                logger.error("Query '%s' failed: %s", query.label, e)
                return BatchQueryResult(
                    query_label=query.label,
                    query_text=query.text,
                    tweets_found=0,
                    new_tweets=0,
                    error=str(e),
                )

    def _get_since_id(self, project_id: str, query_text: str) -> str | None:
        """Get the latest tweet ID for this query to enable incremental collection."""
        from signalops.storage.database import RawPost

        latest = (
            self._session.query(RawPost.platform_id)
            .filter(
                RawPost.project_id == project_id,
                RawPost.query_used == query_text,
            )
            .order_by(RawPost.collected_at.desc())
            .first()
        )
        return str(latest[0]) if latest else None

    def _store_tweets(
        self,
        tweets: list[dict[str, Any]],
        users: dict[str, dict[str, Any]],
        project_id: str,
        query_text: str,
    ) -> int:
        """Store raw tweets, deduplicating by platform_id + project_id."""
        from signalops.storage.database import RawPost

        new_count = 0
        for tweet in tweets:
            tweet_id = str(tweet.get("id", ""))
            # Check for duplicate
            existing = (
                self._session.query(RawPost.id)
                .filter(
                    RawPost.platform == "x",
                    RawPost.platform_id == tweet_id,
                    RawPost.project_id == project_id,
                )
                .first()
            )
            if existing:
                continue

            author_id = str(tweet.get("author_id", ""))
            raw_json = {
                "tweet": tweet,
                "author": users.get(author_id, {}),
            }

            row = RawPost(
                project_id=project_id,
                platform="x",
                platform_id=tweet_id,
                query_used=query_text,
                raw_json=raw_json,
            )
            self._session.add(row)
            new_count += 1

        if new_count > 0:
            self._session.commit()

        return new_count


def run_batch_sync(
    bearer_token: str,
    db_session: Session,
    rate_limiter: RateLimiter,
    config: ProjectConfig,
    concurrency: int = 3,
    dry_run: bool = False,
) -> BatchResult:
    """Synchronous wrapper for batch collection."""
    collector = BatchCollector(
        bearer_token=bearer_token,
        db_session=db_session,
        rate_limiter=rate_limiter,
        concurrency=concurrency,
    )
    return asyncio.run(collector.run(config, dry_run=dry_run))
```

### Step 3: Batch Config Extension

**Add to `src/signalops/config/schema.py`:**

```python
class BatchConfig(BaseModel):
    """Batch processing configuration."""
    enabled: bool = False
    concurrency: int = 3           # Max concurrent API requests
    retry_failed: bool = True      # Retry failed queries at end
    max_retries: int = 2
```

**Update `ProjectConfig`:**
```python
class ProjectConfig(BaseModel):
    # ... existing ...
    batch: BatchConfig = BatchConfig()
```

### Step 4: CLI Integration

**Update `src/signalops/cli/collect.py`:**
- Add `--batch` flag: `signalops run collect --batch`
- When `--batch` is set, use `BatchCollector` instead of sync `CollectorStage`
- Show per-query results table with rich formatting
- Default: use batch if `config.batch.enabled` is True

---

## 3. Phase 2 — Scoring Plugin System

### Step 5: Scoring Plugin Interface

**Create `src/signalops/scoring/__init__.py`:**
```python
"""Extensible scoring engine for lead qualification."""
```

**Create `src/signalops/scoring/base.py`:**

```python
"""Scoring plugin abstract base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class PluginScoreResult:
    """Result from a single scoring plugin."""
    plugin_name: str
    score: float              # 0-100 contribution
    weight: float             # How much this contributes to final score
    details: dict[str, Any]   # Plugin-specific details for transparency
    version: str = "1.0"


class ScoringPlugin(ABC):
    """Abstract interface for scoring plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique plugin name."""

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version string."""

    @property
    def default_weight(self) -> float:
        """Default weight if not overridden in config. Should be 0.0-1.0."""
        return 0.1

    @abstractmethod
    def score(
        self,
        post: dict[str, Any],
        judgment: dict[str, Any],
        config: dict[str, Any],
    ) -> PluginScoreResult:
        """
        Score a lead.

        Args:
            post: Normalized post data (text, author, engagement, etc.)
            judgment: Judgment result (label, confidence, reasoning)
            config: Project config dict for plugin-specific settings

        Returns:
            PluginScoreResult with score 0-100, weight, and details
        """

    def validate_config(self, config: dict[str, Any]) -> list[str]:
        """Validate plugin-specific config. Returns list of errors (empty = valid)."""
        return []
```

### Step 6: Extract Current Scorer as Plugin

**Create `src/signalops/scoring/weighted.py`:**

```python
"""Default weighted scorer — extracted from pipeline/scorer.py."""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any

from signalops.scoring.base import PluginScoreResult, ScoringPlugin


class RelevancePlugin(ScoringPlugin):
    """Score based on judgment confidence and label."""

    @property
    def name(self) -> str:
        return "relevance_judgment"

    @property
    def version(self) -> str:
        return "1.0"

    @property
    def default_weight(self) -> float:
        return 0.35

    def score(self, post: dict[str, Any], judgment: dict[str, Any],
              config: dict[str, Any]) -> PluginScoreResult:
        multiplier = {"relevant": 1.0, "maybe": 0.3, "irrelevant": 0.0}
        label = judgment.get("label", "maybe")
        confidence = float(judgment.get("confidence", 0.5))
        raw_score = confidence * multiplier.get(label, 0.0) * 100

        return PluginScoreResult(
            plugin_name=self.name,
            score=raw_score,
            weight=config.get("weights", {}).get("relevance_judgment", self.default_weight),
            details={"label": label, "confidence": confidence},
            version=self.version,
        )


class AuthorityPlugin(ScoringPlugin):
    """Score based on author followers, verified status, bio match."""

    @property
    def name(self) -> str:
        return "author_authority"

    @property
    def version(self) -> str:
        return "1.0"

    @property
    def default_weight(self) -> float:
        return 0.25

    def score(self, post: dict[str, Any], judgment: dict[str, Any],
              config: dict[str, Any]) -> PluginScoreResult:
        score = 0.0
        followers = int(post.get("author_followers", 0))
        if followers > 0:
            score += min(math.log10(followers) / 6 * 60, 60)
        if post.get("author_verified", False):
            score += 20
        score += 10  # Baseline for having a profile

        return PluginScoreResult(
            plugin_name=self.name,
            score=min(score, 100),
            weight=config.get("weights", {}).get("author_authority", self.default_weight),
            details={"followers": followers, "verified": post.get("author_verified", False)},
            version=self.version,
        )


class EngagementPlugin(ScoringPlugin):
    """Score based on likes, replies, retweets, views."""

    @property
    def name(self) -> str:
        return "engagement_signals"

    @property
    def version(self) -> str:
        return "1.0"

    @property
    def default_weight(self) -> float:
        return 0.15

    def score(self, post: dict[str, Any], judgment: dict[str, Any],
              config: dict[str, Any]) -> PluginScoreResult:
        score = 0.0
        likes = int(post.get("likes", 0))
        replies = int(post.get("replies", 0))
        retweets = int(post.get("retweets", 0))
        views = int(post.get("views", 0))

        score += min(likes * 3, 30)
        score += min(replies * 5, 30)
        score += min(retweets * 4, 20)
        score += min(views / 500, 20)

        return PluginScoreResult(
            plugin_name=self.name,
            score=min(score, 100),
            weight=config.get("weights", {}).get("engagement_signals", self.default_weight),
            details={"likes": likes, "replies": replies, "retweets": retweets, "views": views},
            version=self.version,
        )


class RecencyPlugin(ScoringPlugin):
    """Score based on post age — newer = higher."""

    @property
    def name(self) -> str:
        return "recency"

    @property
    def version(self) -> str:
        return "1.0"

    @property
    def default_weight(self) -> float:
        return 0.15

    def score(self, post: dict[str, Any], judgment: dict[str, Any],
              config: dict[str, Any]) -> PluginScoreResult:
        created_at = post.get("created_at")
        if not created_at:
            return PluginScoreResult(
                plugin_name=self.name, score=0.0,
                weight=self.default_weight, details={"hours_ago": None},
            )

        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)

        hours_ago = (datetime.now(UTC) - created_at).total_seconds() / 3600
        if hours_ago <= 0:
            raw_score = 100.0
        elif hours_ago >= 168:
            raw_score = 0.0
        else:
            raw_score = max(0.0, 100 * math.exp(-0.03 * hours_ago))

        return PluginScoreResult(
            plugin_name=self.name,
            score=raw_score,
            weight=config.get("weights", {}).get("recency", self.default_weight),
            details={"hours_ago": round(hours_ago, 1)},
            version=self.version,
        )


class IntentPlugin(ScoringPlugin):
    """Score based on intent signals in text."""

    @property
    def name(self) -> str:
        return "intent_strength"

    @property
    def version(self) -> str:
        return "1.0"

    @property
    def default_weight(self) -> float:
        return 0.10

    def score(self, post: dict[str, Any], judgment: dict[str, Any],
              config: dict[str, Any]) -> PluginScoreResult:
        text = str(post.get("text_cleaned", "")).lower()
        score = 0.0
        signals_found: list[str] = []

        if "?" in text:
            score += 40
            signals_found.append("question_mark")

        search_phrases = [
            "looking for", "anyone recommend", "anyone know",
            "suggestions for", "alternative to", "switching from",
        ]
        if any(phrase in text for phrase in search_phrases):
            score += 30
            signals_found.append("search_phrase")

        pain_phrases = [
            "frustrated", "annoying", "painful", "hate",
            "takes forever", "waste of time", "there has to be",
        ]
        if any(phrase in text for phrase in pain_phrases):
            score += 20
            signals_found.append("pain_phrase")

        eval_phrases = ["evaluating", "comparing", "trying out", "testing"]
        if any(phrase in text for phrase in eval_phrases):
            score += 10
            signals_found.append("eval_phrase")

        return PluginScoreResult(
            plugin_name=self.name,
            score=min(score, 100),
            weight=config.get("weights", {}).get("intent_strength", self.default_weight),
            details={"signals": signals_found},
            version=self.version,
        )
```

### Step 7: Scoring Engine

**Create `src/signalops/scoring/engine.py`:**

```python
"""Scoring engine — orchestrates plugins and rules to produce final scores."""

from __future__ import annotations

import logging
from typing import Any

from signalops.scoring.base import PluginScoreResult, ScoringPlugin

logger = logging.getLogger(__name__)

# Default plugin set
DEFAULT_PLUGINS = [
    "signalops.scoring.weighted:RelevancePlugin",
    "signalops.scoring.weighted:AuthorityPlugin",
    "signalops.scoring.weighted:EngagementPlugin",
    "signalops.scoring.weighted:RecencyPlugin",
    "signalops.scoring.weighted:IntentPlugin",
]


class ScoringEngine:
    """Orchestrates scoring plugins to produce final lead scores."""

    def __init__(self, plugins: list[ScoringPlugin] | None = None) -> None:
        self._plugins = plugins or self._load_default_plugins()

    def score(
        self,
        post: dict[str, Any],
        judgment: dict[str, Any],
        config: dict[str, Any],
    ) -> tuple[float, dict[str, Any]]:
        """
        Score a lead using all active plugins.

        Returns:
            (total_score, components_dict) where total is 0-100
        """
        results: list[PluginScoreResult] = []

        for plugin in self._plugins:
            try:
                result = plugin.score(post, judgment, config)
                results.append(result)
            except Exception as e:
                logger.warning("Plugin '%s' failed: %s", plugin.name, e)

        # Apply config-driven rules (boost/penalty)
        rules = config.get("custom_rules", [])
        rule_adjustments = self._apply_rules(post, judgment, rules)

        # Compute weighted total
        total = sum(r.score * r.weight for r in results)

        # Apply rule adjustments
        for adj in rule_adjustments:
            total += adj["adjustment"]

        total = min(max(total, 0.0), 100.0)

        # Build components dict for storage
        components: dict[str, Any] = {}
        for r in results:
            components[r.plugin_name] = r.score
        if rule_adjustments:
            components["rule_adjustments"] = rule_adjustments

        return total, components

    def list_plugins(self) -> list[dict[str, str]]:
        """List all active plugins with name and version."""
        return [
            {"name": p.name, "version": p.version, "weight": str(p.default_weight)}
            for p in self._plugins
        ]

    def _apply_rules(
        self,
        post: dict[str, Any],
        judgment: dict[str, Any],
        rules: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Apply config-driven scoring rules (boost/penalty)."""
        adjustments: list[dict[str, Any]] = []

        for rule in rules:
            condition = rule.get("condition", "")
            adjustment = float(rule.get("boost", 0))

            if self._evaluate_condition(condition, post, judgment):
                adjustments.append({
                    "rule_name": rule.get("name", "unnamed"),
                    "condition": condition,
                    "adjustment": adjustment,
                })

        return adjustments

    def _evaluate_condition(
        self,
        condition: str,
        post: dict[str, Any],
        judgment: dict[str, Any],
    ) -> bool:
        """Evaluate a simple condition string against post/judgment data."""
        condition = condition.strip()

        # Pattern: "text contains 'phrase'"
        if "text contains" in condition:
            phrase = condition.split("'")[1] if "'" in condition else ""
            text = str(post.get("text_cleaned", "")).lower()
            return phrase.lower() in text

        # Pattern: "author_verified == true"
        if "author_verified == true" in condition:
            return bool(post.get("author_verified", False))

        # Pattern: "author_followers > N"
        if "author_followers >" in condition:
            try:
                threshold = int(condition.split(">")[1].strip())
                return int(post.get("author_followers", 0)) > threshold
            except (ValueError, IndexError):
                return False

        # Pattern: "label == relevant"
        if "label ==" in condition:
            expected = condition.split("==")[1].strip().strip("'\"")
            return judgment.get("label", "") == expected

        logger.warning("Unknown rule condition: %s", condition)
        return False

    def _load_default_plugins(self) -> list[ScoringPlugin]:
        """Load the default set of built-in plugins."""
        plugins: list[ScoringPlugin] = []
        for plugin_path in DEFAULT_PLUGINS:
            try:
                module_path, class_name = plugin_path.rsplit(":", 1)
                module = __import__(module_path, fromlist=[class_name])
                cls = getattr(module, class_name)
                plugins.append(cls())
            except Exception as e:
                logger.error("Failed to load plugin '%s': %s", plugin_path, e)
        return plugins

    @staticmethod
    def load_from_entry_points() -> list[ScoringPlugin]:
        """Load plugins from setuptools entry points."""
        try:
            from importlib.metadata import entry_points

            eps = entry_points(group="signalops.scorers")
            plugins: list[ScoringPlugin] = []
            for ep in eps:
                try:
                    plugin_cls = ep.load()
                    plugins.append(plugin_cls())
                except Exception as e:
                    logger.error("Failed to load entry point '%s': %s", ep.name, e)
            return plugins
        except Exception:
            return []
```

### Step 8: Additional Built-in Plugins

**Create `src/signalops/scoring/keyword_boost.py`:**

```python
"""Keyword boost scoring plugin — boosts score for specific keywords."""

from __future__ import annotations

from typing import Any

from signalops.scoring.base import PluginScoreResult, ScoringPlugin


class KeywordBoostPlugin(ScoringPlugin):
    """Boosts score when post contains configured keywords."""

    @property
    def name(self) -> str:
        return "keyword_boost"

    @property
    def version(self) -> str:
        return "1.0"

    @property
    def default_weight(self) -> float:
        return 0.0  # Only active when configured

    def score(self, post: dict[str, Any], judgment: dict[str, Any],
              config: dict[str, Any]) -> PluginScoreResult:
        boost_keywords = config.get("keyword_boost", {}).get("keywords", [])
        if not boost_keywords:
            return PluginScoreResult(
                plugin_name=self.name, score=0.0, weight=0.0,
                details={"active": False},
            )

        text = str(post.get("text_cleaned", "")).lower()
        matched = [kw for kw in boost_keywords if kw.lower() in text]
        score = min(len(matched) * 20, 100)

        return PluginScoreResult(
            plugin_name=self.name,
            score=score,
            weight=config.get("keyword_boost", {}).get("weight", 0.05),
            details={"matched_keywords": matched},
            version=self.version,
        )
```

**Create `src/signalops/scoring/account_age.py`:**

```python
"""Account age scoring plugin — newer accounts may be less trustworthy."""

from __future__ import annotations

from typing import Any

from signalops.scoring.base import PluginScoreResult, ScoringPlugin


class AccountAgePlugin(ScoringPlugin):
    """Scores based on author account age. Older = more trustworthy."""

    @property
    def name(self) -> str:
        return "account_age"

    @property
    def version(self) -> str:
        return "1.0"

    @property
    def default_weight(self) -> float:
        return 0.0  # Only active when configured

    def score(self, post: dict[str, Any], judgment: dict[str, Any],
              config: dict[str, Any]) -> PluginScoreResult:
        # Account creation date may not be available in basic API tier
        account_created = post.get("author_account_created")
        if not account_created:
            return PluginScoreResult(
                plugin_name=self.name, score=50.0, weight=0.0,
                details={"available": False},
            )

        from datetime import UTC, datetime

        if isinstance(account_created, str):
            created = datetime.fromisoformat(account_created)
        else:
            created = account_created

        if created.tzinfo is None:
            created = created.replace(tzinfo=UTC)

        days_old = (datetime.now(UTC) - created).days
        # 0 days = 0, 30 days = 30, 365 days = 80, 1000+ days = 100
        if days_old >= 1000:
            score = 100.0
        elif days_old >= 365:
            score = 80.0 + (days_old - 365) / 635 * 20
        elif days_old >= 30:
            score = 30.0 + (days_old - 30) / 335 * 50
        else:
            score = days_old

        return PluginScoreResult(
            plugin_name=self.name,
            score=score,
            weight=config.get("account_age", {}).get("weight", self.default_weight),
            details={"days_old": days_old},
            version=self.version,
        )
```

---

## 4. Phase 3 — Config-Driven Scoring Rules

### Step 9: Config Schema Extensions

**Add to `src/signalops/config/schema.py`:**

```python
class ScoringRule(BaseModel):
    """A config-driven scoring rule (boost/penalty)."""
    name: str                           # Rule identifier
    condition: str                      # Simple condition expression
    boost: float                        # Score adjustment (-100 to +100)
    description: str = ""               # Human-readable explanation

class ScoringConfig(BaseModel):
    """Extended scoring configuration with plugins and rules."""
    # Existing weights:
    relevance_judgment: float = 0.35
    author_authority: float = 0.25
    engagement_signals: float = 0.15
    recency: float = 0.15
    intent_strength: float = 0.10
    # New fields:
    custom_rules: list[ScoringRule] = []
    plugins: list[str] = []            # Additional plugin module paths
    keyword_boost: dict[str, Any] = {} # keyword_boost plugin config
    account_age: dict[str, Any] = {}   # account_age plugin config
```

> **Note:** `ScoringConfig` extends `ScoringWeights`. We rename the class but keep
> backward compatibility — existing YAML files with just the weight fields still load.

### Step 10: Example Config

```yaml
# projects/spectra.yaml additions
scoring:
  relevance_judgment: 0.35
  author_authority: 0.25
  engagement_signals: 0.15
  recency: 0.15
  intent_strength: 0.10
  custom_rules:
    - name: "active_searcher_boost"
      condition: "text contains 'looking for'"
      boost: 10
      description: "Boost for actively searching users"
    - name: "verified_bonus"
      condition: "author_verified == true"
      boost: 5
      description: "Small bonus for verified accounts"
    - name: "high_follower_boost"
      condition: "author_followers > 5000"
      boost: 8
      description: "Boost for high-influence accounts"
  keyword_boost:
    keywords: ["code review", "pull request", "PR automation"]
    weight: 0.05
```

---

## 5. Phase 4 — Integration & CLI

### Step 11: Integrate Scoring Engine into Pipeline

**Refactor `src/signalops/pipeline/scorer.py`:**
- Replace inline scoring logic with `ScoringEngine.score()` call
- Convert `NormalizedPost` + `JudgmentRow` to dict format for plugin interface
- Store `scoring_plugins` JSON column with plugin list used
- Maintain backward compatibility: if no plugins configured, use defaults

```python
# Updated ScorerStage.compute_score:
def compute_score(self, post, judgment, config):
    engine = self._get_engine(config)
    post_dict = self._post_to_dict(post)
    judgment_dict = self._judgment_to_dict(judgment)
    config_dict = config.scoring.model_dump() if hasattr(config.scoring, 'model_dump') else {}
    return engine.score(post_dict, judgment_dict, config_dict)
```

### Step 12: CLI for Batch Collection

**Update `src/signalops/cli/collect.py`:**
```
signalops run collect --batch              # Use batch mode
signalops run collect --batch --concurrency 5  # Override concurrency
```

### Step 13: CLI for Scoring Plugins

**Add to `src/signalops/cli/score.py` or new `src/signalops/cli/scoring.py`:**
```
signalops scoring list-plugins             # Show active plugins
signalops scoring list-rules               # Show custom rules from config
signalops scoring test-rules --project spectra  # Dry-run rules against existing data
```

### Step 14: Update Orchestrator

**Modify `src/signalops/pipeline/orchestrator.py`:**
- Add `--batch` support in `run_all()`: if batch enabled, use `BatchCollector` for collection stage
- Pass scoring engine to scorer stage

---

## 6. File Manifest

### New Files

```
src/signalops/connectors/async_client.py     # Async httpx client for X API
src/signalops/pipeline/batch.py              # BatchCollector + BatchResult
src/signalops/scoring/__init__.py
src/signalops/scoring/base.py               # ScoringPlugin ABC
src/signalops/scoring/weighted.py            # 5 default plugins (extracted from scorer.py)
src/signalops/scoring/keyword_boost.py       # Keyword boost plugin
src/signalops/scoring/account_age.py         # Account age plugin
src/signalops/scoring/engine.py              # ScoringEngine orchestrator
src/signalops/scoring/rules.py               # Rule condition evaluator (if extracted)
tests/unit/test_batch.py
tests/unit/test_scoring_engine.py
tests/unit/test_scoring_plugins.py
tests/unit/test_scoring_rules.py
tests/integration/test_batch_pipeline.py
```

### Modified Files

```
src/signalops/config/schema.py              # Add BatchConfig, ScoringRule, extend ScoringConfig
src/signalops/pipeline/scorer.py            # Delegate to ScoringEngine
src/signalops/pipeline/orchestrator.py      # Add batch mode support
src/signalops/cli/collect.py                # Add --batch flag
src/signalops/cli/main.py                   # Register scoring command group
pyproject.toml                               # Add entry_points for scorers, add pytest-asyncio
```

---

## 7. Testing Plan

### Unit Tests

| Test File | Coverage |
|-----------|----------|
| `test_batch.py` | BatchCollector: concurrent queries, rate limit respect, dedup, error handling, resume |
| `test_scoring_engine.py` | Engine: plugin orchestration, weighted total, rule application |
| `test_scoring_plugins.py` | Each built-in plugin: edge cases, zero values, missing data |
| `test_scoring_rules.py` | Condition evaluation: text contains, author_verified, followers threshold |

### Integration Tests

| Test File | Coverage |
|-----------|----------|
| `test_batch_pipeline.py` | End-to-end batch collection with mocked async HTTP responses |

### Key Test Cases

```python
# Batch respects concurrency
async def test_batch_concurrency():
    """Only N queries run simultaneously."""
    collector = BatchCollector(bearer_token="test", ..., concurrency=2)
    # Mock 5 queries, verify max 2 run at once via timing

# Scoring engine backward compatibility
def test_default_plugins_match_old_scorer():
    """ScoringEngine with defaults produces same scores as old ScorerStage."""
    engine = ScoringEngine()  # Default plugins
    old_scorer = ScorerStage(session)
    # Compare scores for same input

# Custom rules apply correctly
def test_keyword_boost_rule():
    """Custom rule boosts score when condition matches."""
    config = {"custom_rules": [{"name": "test", "condition": "text contains 'help'", "boost": 15}]}
    engine = ScoringEngine()
    score, components = engine.score({"text_cleaned": "I need help"}, judgment, config)
    assert components["rule_adjustments"][0]["adjustment"] == 15

# Entry point loading
def test_entry_point_plugins_load():
    """Plugins registered via entry_points are discoverable."""
    plugins = ScoringEngine.load_from_entry_points()
    # May be empty in test env, but should not error
```

---

## Acceptance Criteria

- [ ] `signalops run collect --batch` runs queries concurrently
- [ ] Batch mode respects rate limits (no more than N concurrent requests)
- [ ] Batch collection resumes from last `since_id` per query
- [ ] `ScoringEngine` with default plugins produces same scores as current scorer
- [ ] Custom rules in project.yaml apply correctly (boost/penalty)
- [ ] `signalops scoring list-plugins` shows active plugins
- [ ] Keyword boost and account age plugins work when configured
- [ ] Entry points mechanism loads pip-installed plugins
- [ ] All existing scorer tests still pass (backward compatibility)
- [ ] `ruff check` and `mypy --strict` pass on all new code
- [ ] All new tests pass

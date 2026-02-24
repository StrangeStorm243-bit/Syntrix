# Terminal 4 — LinkedIn Adapter + Connector Generalization

> **Scope:** Multi-platform connector architecture, LinkedIn adapter (stubbed), connector factory
> **New files:** `connectors/linkedin.py`, `connectors/factory.py`
> **Touches existing:** `connectors/base.py`, `schema.py`, `normalizer.py`
> **Depends on:** None (isolated until Phase 3)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Phase 1 — Connector Factory & Platform Abstraction](#2-phase-1--connector-factory--platform-abstraction)
3. [Phase 2 — LinkedIn Connector (Stubbed)](#3-phase-2--linkedin-connector-stubbed)
4. [Phase 3 — Multi-Platform Pipeline Support](#4-phase-3--multi-platform-pipeline-support)
5. [Phase 4 — Tests & Documentation](#5-phase-4--tests--documentation)
6. [File Manifest](#6-file-manifest)
7. [Testing Plan](#7-testing-plan)

---

## 1. Overview

This terminal generalizes the connector layer to support multiple social platforms.
Twitter/X remains the primary (and only fully functional) platform. LinkedIn is added
as a well-scaffolded adapter with the full `Connector` interface implemented but API
calls stubbed — ready to plug in once LinkedIn Marketing Developer Platform access is
approved.

**Key design decisions:**
- `ConnectorFactory` centralizes connector creation from config
- Platform enum prevents typos and enables exhaustive matching
- LinkedIn connector raises `NotImplementedError` with helpful messages
- Normalizer gains platform-specific handling (different engagement metrics)
- No changes to the core pipeline logic — platforms are abstracted behind `Connector`
- Config schema extended with `platforms` section for future multi-platform configs

---

## 2. Phase 1 — Connector Factory & Platform Abstraction

### Step 1: Platform Enum

**Update `src/signalops/connectors/base.py`:**

```python
import enum

class Platform(enum.Enum):
    """Supported social media platforms."""
    X = "x"
    LINKEDIN = "linkedin"
    SOCIALDATA = "socialdata"

    @classmethod
    def from_string(cls, value: str) -> "Platform":
        """Case-insensitive platform lookup."""
        try:
            return cls(value.lower())
        except ValueError:
            valid = ", ".join(p.value for p in cls)
            raise ValueError(
                f"Unknown platform '{value}'. Supported platforms: {valid}"
            ) from None
```

Also add platform validation to the `RawPost` **dataclass** in `connectors/base.py`:

> **Note:** There are two `RawPost` types in the codebase:
> 1. `connectors/base.py:RawPost` — a `@dataclass` used as the connector return type
>    (this is the one modified here to add platform validation)
> 2. `storage/database.py:RawPost` — a SQLAlchemy ORM model for the `raw_posts` table
>    (not modified by T4 — it already has a `platform` string column)

```python
@dataclass
class RawPost:
    platform: str           # "x", "linkedin"
    # ... existing fields ...

    def __post_init__(self) -> None:
        """Validate platform is a known value."""
        Platform.from_string(self.platform)  # Raises if unknown
```

### Step 2: Connector Factory

**Create `src/signalops/connectors/factory.py`:**

```python
"""Connector factory — creates platform connectors from config."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any

from signalops.connectors.base import Connector, Platform

if TYPE_CHECKING:
    from signalops.config.schema import ProjectConfig

logger = logging.getLogger(__name__)


class ConnectorFactory:
    """Creates and caches connector instances based on platform config.

    WARNING: _instances is a class-level mutable dict shared across all tests.
    Every test that uses ConnectorFactory MUST call ConnectorFactory.clear_cache()
    in setup (see test_connector_factory.py setup_method for the pattern).
    """

    _instances: dict[str, Connector] = {}

    @classmethod
    def create(
        cls,
        platform: Platform | str,
        config: ProjectConfig | None = None,
        **kwargs: Any,
    ) -> Connector:
        """
        Create a connector for the given platform.

        Args:
            platform: Platform enum or string identifier
            config: Project config (optional, used for platform-specific settings)
            **kwargs: Additional kwargs passed to connector constructor

        Returns:
            Connector instance

        Raises:
            ValueError: If platform is unknown
            NotImplementedError: If platform connector is not yet implemented
        """
        if isinstance(platform, str):
            platform = Platform.from_string(platform)

        cache_key = f"{platform.value}:{id(config)}"
        if cache_key in cls._instances:
            return cls._instances[cache_key]

        connector = cls._build_connector(platform, config, **kwargs)
        cls._instances[cache_key] = connector
        return connector

    @classmethod
    def create_all(cls, config: ProjectConfig) -> dict[Platform, Connector]:
        """Create connectors for all enabled platforms in config."""
        connectors: dict[Platform, Connector] = {}
        platforms_config = getattr(config, "platforms", {})

        if not platforms_config:
            # Default: X only
            connectors[Platform.X] = cls.create(Platform.X, config)
            return connectors

        for platform_name, platform_cfg in platforms_config.items():
            if not platform_cfg.get("enabled", False):
                continue
            try:
                platform = Platform.from_string(platform_name)
                connectors[platform] = cls.create(platform, config)
            except (ValueError, NotImplementedError) as e:
                logger.warning("Skipping platform '%s': %s", platform_name, e)

        return connectors

    @classmethod
    def clear_cache(cls) -> None:
        """Clear cached connector instances."""
        cls._instances.clear()

    @classmethod
    def _build_connector(
        cls,
        platform: Platform,
        config: ProjectConfig | None,
        **kwargs: Any,
    ) -> Connector:
        """Build a connector instance for the given platform."""
        if platform == Platform.X:
            return cls._build_x_connector(config, **kwargs)
        if platform == Platform.LINKEDIN:
            return cls._build_linkedin_connector(config, **kwargs)
        if platform == Platform.SOCIALDATA:
            return cls._build_socialdata_connector(config, **kwargs)

        raise ValueError(f"No connector implementation for platform: {platform.value}")

    @classmethod
    def _build_x_connector(
        cls, config: ProjectConfig | None, **kwargs: Any
    ) -> Connector:
        """Build X/Twitter connector."""
        from signalops.connectors.x_api import XConnector

        bearer_token = kwargs.get("bearer_token") or os.environ.get("X_BEARER_TOKEN", "")
        if not bearer_token:
            raise ValueError(
                "X_BEARER_TOKEN environment variable is required for X connector. "
                "Set it in your .env file."
            )
        return XConnector(bearer_token=bearer_token)

    @classmethod
    def _build_linkedin_connector(
        cls, config: ProjectConfig | None, **kwargs: Any
    ) -> Connector:
        """Build LinkedIn connector (stubbed)."""
        from signalops.connectors.linkedin import LinkedInConnector

        return LinkedInConnector()

    @classmethod
    def _build_socialdata_connector(
        cls, config: ProjectConfig | None, **kwargs: Any
    ) -> Connector:
        """Build SocialData connector."""
        raise NotImplementedError(
            "SocialData connector is not yet implemented. "
            "Set platform to 'x' in your project config."
        )
```

### Step 3: Platform Config Schema

**Add to `src/signalops/config/schema.py`:**

```python
class PlatformConfig(BaseModel):
    """Configuration for a single platform connector."""
    enabled: bool = True

class XPlatformConfig(PlatformConfig):
    """X/Twitter specific config."""
    search_type: str = "recent"   # "recent" or "all" (Academic tier)
    include_retweets: bool = False

class LinkedInPlatformConfig(PlatformConfig):
    """LinkedIn specific config."""
    post_types: list[str] = ["articles", "posts"]  # Types to collect
    company_pages: list[str] = []                   # Company pages to monitor

class PlatformsConfig(BaseModel):
    """Multi-platform configuration."""
    x: XPlatformConfig = XPlatformConfig()
    linkedin: LinkedInPlatformConfig = LinkedInPlatformConfig(enabled=False)
```

**Update `ProjectConfig`:**
```python
class ProjectConfig(BaseModel):
    # ... existing fields ...
    platforms: PlatformsConfig = PlatformsConfig()
```

---

## 3. Phase 2 — LinkedIn Connector (Stubbed)

### Step 4: LinkedIn Connector Implementation

**Create `src/signalops/connectors/linkedin.py`:**

```python
"""LinkedIn connector — stubbed implementation ready for API integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from signalops.connectors.base import Connector, RawPost

logger = logging.getLogger(__name__)


# LinkedIn-specific engagement metrics mapping
LINKEDIN_METRIC_MAPPING = {
    "numLikes": "likes",
    "numComments": "replies",      # Map to our generic "replies"
    "numShares": "retweets",       # Map to our generic "retweets"
    "numImpressions": "views",
}


@dataclass
class LinkedInPost:
    """LinkedIn-specific post data before normalization to RawPost."""
    urn: str                          # LinkedIn URN (e.g., "urn:li:share:123456")
    author_urn: str                   # Author URN
    author_name: str
    author_headline: str              # LinkedIn "bio" equivalent
    author_connections: int           # Approximate connection count
    author_is_premium: bool
    text: str
    post_type: str                    # "article", "post", "share"
    published_at: str                 # ISO datetime
    reactions: int
    comments: int
    shares: int
    impressions: int | None           # Only available for own company posts


class LinkedInConnector(Connector):
    """
    LinkedIn connector — reads LinkedIn posts and profiles.

    IMPORTANT: This connector is currently STUBBED. All methods raise
    NotImplementedError with guidance on what's needed for full implementation.

    To implement:
    1. Apply for LinkedIn Marketing Developer Platform access
    2. Obtain OAuth 2.0 client credentials
    3. Implement the LinkedIn REST API v2 calls in each method

    LinkedIn API docs: https://learn.microsoft.com/en-us/linkedin/
    """

    def __init__(
        self,
        access_token: str | None = None,
        base_url: str = "https://api.linkedin.com/v2",
    ) -> None:
        self._access_token = access_token
        self._base_url = base_url
        self._is_stubbed = access_token is None

    def search(
        self,
        query: str,
        since_id: str | None = None,
        max_results: int = 100,
    ) -> list[RawPost]:
        """
        Search LinkedIn posts matching query.

        LinkedIn API equivalent: Content Search API
        Requires: Marketing Developer Platform access, rw_ads scope

        Current status: STUBBED
        """
        if self._is_stubbed:
            logger.warning(
                "LinkedIn connector is stubbed. Returning empty results. "
                "To enable: set LINKEDIN_ACCESS_TOKEN and implement API calls."
            )
            return []

        # TODO: Implement LinkedIn Content Search API
        # POST https://api.linkedin.com/v2/search
        # Headers: Authorization: Bearer {access_token}
        # Body: {"keywords": query, "type": "CONTENT", ...}
        raise NotImplementedError(
            "LinkedIn search is not yet implemented. "
            "See https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares"
        )

    def get_user(self, user_id: str) -> dict[str, Any]:
        """
        Fetch LinkedIn profile by URN.

        LinkedIn API equivalent: GET /v2/people/{id}
        Requires: r_liteprofile scope

        Current status: STUBBED
        """
        if self._is_stubbed:
            return {
                "id": user_id,
                "platform": "linkedin",
                "name": "Unknown",
                "headline": "",
                "connections": 0,
                "is_premium": False,
                "_stubbed": True,
            }

        raise NotImplementedError(
            "LinkedIn user profile fetch is not yet implemented. "
            "See https://learn.microsoft.com/en-us/linkedin/shared/references/v2/profile"
        )

    def post_reply(self, in_reply_to_id: str, text: str) -> str:
        """
        Post a comment on a LinkedIn post.

        LinkedIn API equivalent: POST /v2/socialActions/{id}/comments
        Requires: w_member_social scope

        Current status: STUBBED (not planned for v0.3 — LinkedIn is read-only)
        """
        raise NotImplementedError(
            "LinkedIn reply/comment is not implemented. "
            "v0.3 LinkedIn support is read-only intelligence only. "
            "Comment posting requires w_member_social scope and explicit user consent."
        )

    def health_check(self) -> bool:
        """
        Verify LinkedIn API connectivity.

        Checks: valid access token, required scopes available
        """
        if self._is_stubbed:
            logger.info("LinkedIn connector health check: STUBBED (no access token)")
            return False

        # TODO: Call GET /v2/me to verify auth
        raise NotImplementedError("LinkedIn health check not yet implemented.")

    def to_raw_post(self, linkedin_post: LinkedInPost) -> RawPost:
        """Convert a LinkedIn-specific post to the generic RawPost format."""
        return RawPost(
            platform="linkedin",
            platform_id=linkedin_post.urn,
            author_id=linkedin_post.author_urn,
            author_username=linkedin_post.author_name.lower().replace(" ", "-"),
            author_display_name=linkedin_post.author_name,
            author_followers=linkedin_post.author_connections,
            author_verified=linkedin_post.author_is_premium,
            text=linkedin_post.text,
            created_at=linkedin_post.published_at,
            language=None,  # LinkedIn API provides this
            reply_to_id=None,
            conversation_id=None,
            metrics={
                "likes": linkedin_post.reactions,
                "retweets": linkedin_post.shares,     # Mapped
                "replies": linkedin_post.comments,     # Mapped
                "views": linkedin_post.impressions or 0,
            },
            entities={"urls": [], "mentions": [], "hashtags": []},
            raw_json={"_source": "linkedin", "_stubbed": True},
        )
```

### Step 5: LinkedIn Data Normalization

**Extend normalizer to handle LinkedIn-specific fields:**

The normalizer needs to know that LinkedIn's "connections" maps to "followers",
"reactions" maps to "likes", and "comments" maps to "replies". Since `RawPost`
already normalizes these in `to_raw_post()`, the normalizer mostly works as-is.

Add platform-specific handling in `src/signalops/pipeline/normalizer.py`:

```python
# In NormalizerStage._normalize_entities():
def _normalize_entities(self, raw_json: dict, platform: str) -> dict:
    """Extract entities with platform-specific handling."""
    if platform == "linkedin":
        return self._normalize_linkedin_entities(raw_json)
    return self._normalize_x_entities(raw_json)

def _normalize_linkedin_entities(self, raw_json: dict) -> dict:
    """LinkedIn posts have different entity structure."""
    # LinkedIn uses URNs for mentions, different hashtag format
    return {
        "urls": [],      # Extract from post text
        "mentions": [],  # Extract from @mentions in text
        "hashtags": [],  # Extract from #tags in text
    }
```

---

## 4. Phase 3 — Multi-Platform Pipeline Support

### Step 6: Pipeline Platform Awareness

The pipeline is already mostly platform-agnostic thanks to the `Connector` interface
and `NormalizedPost` table. The key changes needed:

**Collector stage** — Currently hardcodes "x" as platform. Parameterize:

```python
# In CollectorStage.run():
def run(self, config: ProjectConfig, dry_run: bool = False,
        platform: str = "x") -> dict[str, Any]:
    # ... use platform param when creating RawPost rows
```

**Judge stage** — No changes needed. Judges text content regardless of platform.

**Scorer stage** — No changes needed. Scores use normalized fields.

**Drafter stage** — May need platform-specific reply formats:
- X: max 280 chars
- LinkedIn: max 1300 chars for comments, different tone expectations

Add platform-aware character limits:

```python
PLATFORM_CHAR_LIMITS = {
    "x": 280,
    "linkedin": 1300,
}
```

**Sender stage** — Must route to correct connector:

```python
# In SenderStage:
def send(self, draft, platform: str = "x") -> str:
    connector = ConnectorFactory.create(platform)
    return connector.post_reply(draft.reply_to_id, draft.text)
```

### Step 7: Multi-Platform Config Example

```yaml
# projects/spectra.yaml — multi-platform
platforms:
  x:
    enabled: true
    search_type: recent
  linkedin:
    enabled: false     # Stubbed for now
    post_types: ["posts", "articles"]
    company_pages: ["spectra-ai"]

queries:
  - text: '"code review" (slow OR painful) -is:retweet lang:en'
    label: "Code review pain (X)"
    platform: x        # NEW: per-query platform targeting
  - text: 'code review automation'
    label: "Code review pain (LinkedIn)"
    platform: linkedin  # Will be skipped if linkedin.enabled = false
```

### Step 8: Query Platform Filtering

**Update `QueryConfig` in schema:**

```python
class QueryConfig(BaseModel):
    text: str
    label: str
    enabled: bool = True
    max_results_per_run: int = 100
    platform: str = "x"    # NEW: target platform for this query
```

**Update collector to filter queries by platform:**

```python
# In CollectorStage:
enabled_queries = [
    q for q in config.queries
    if q.enabled and q.platform == platform
]
```

---

## 5. Phase 4 — Tests & Documentation

### Step 9: Connector Interface Tests

Create a **contract test** that validates any connector implementation:

**Create `tests/unit/test_connector_contract.py`:**

```python
"""Contract tests for the Connector interface.
Any connector implementation should pass these tests."""

from __future__ import annotations

import pytest
from signalops.connectors.base import Connector, RawPost, Platform


class ConnectorContractTests:
    """Mixin for connector contract tests. Subclass and set self.connector."""

    connector: Connector

    def test_search_returns_list(self):
        """search() must return a list of RawPost."""
        result = self.connector.search("test query")
        assert isinstance(result, list)

    def test_search_with_max_results(self):
        """search() respects max_results parameter."""
        result = self.connector.search("test", max_results=5)
        assert len(result) <= 5

    def test_get_user_returns_dict(self):
        """get_user() must return a dict."""
        result = self.connector.get_user("test_id")
        assert isinstance(result, dict)

    def test_health_check_returns_bool(self):
        """health_check() must return a boolean."""
        result = self.connector.health_check()
        assert isinstance(result, bool)


class TestLinkedInConnectorContract(ConnectorContractTests):
    """Run contract tests against LinkedIn stubbed connector."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from signalops.connectors.linkedin import LinkedInConnector
        self.connector = LinkedInConnector()  # Stubbed mode

    def test_search_returns_empty_when_stubbed(self):
        """Stubbed connector returns empty list, not error."""
        result = self.connector.search("test")
        assert result == []

    def test_get_user_returns_stubbed_data(self):
        """Stubbed connector returns placeholder user data."""
        result = self.connector.get_user("urn:li:person:123")
        assert result["_stubbed"] is True

    def test_post_reply_raises_not_implemented(self):
        """LinkedIn post_reply always raises — read-only platform."""
        with pytest.raises(NotImplementedError, match="read-only"):
            self.connector.post_reply("urn:li:share:123", "test reply")

    def test_health_check_returns_false_when_stubbed(self):
        """Stubbed connector reports unhealthy."""
        assert self.connector.health_check() is False
```

### Step 10: Factory Tests

**Create `tests/unit/test_connector_factory.py`:**

```python
"""Tests for ConnectorFactory."""

import os
import pytest
from signalops.connectors.factory import ConnectorFactory
from signalops.connectors.base import Platform


class TestConnectorFactory:
    def setup_method(self):
        ConnectorFactory.clear_cache()

    def test_create_x_connector(self, monkeypatch):
        """Factory creates XConnector when bearer token is available."""
        monkeypatch.setenv("X_BEARER_TOKEN", "test-token")
        connector = ConnectorFactory.create(Platform.X)
        from signalops.connectors.x_api import XConnector
        assert isinstance(connector, XConnector)

    def test_create_x_without_token_raises(self, monkeypatch):
        """Factory raises when X bearer token is missing."""
        monkeypatch.delenv("X_BEARER_TOKEN", raising=False)
        with pytest.raises(ValueError, match="X_BEARER_TOKEN"):
            ConnectorFactory.create(Platform.X)

    def test_create_linkedin_connector(self):
        """Factory creates LinkedInConnector (stubbed mode)."""
        connector = ConnectorFactory.create(Platform.LINKEDIN)
        from signalops.connectors.linkedin import LinkedInConnector
        assert isinstance(connector, LinkedInConnector)

    def test_create_from_string(self, monkeypatch):
        """Factory accepts string platform names."""
        monkeypatch.setenv("X_BEARER_TOKEN", "test-token")
        connector = ConnectorFactory.create("x")
        assert connector is not None

    def test_create_unknown_platform_raises(self):
        """Factory raises for unknown platforms."""
        with pytest.raises(ValueError, match="Unknown platform"):
            ConnectorFactory.create("tiktok")

    def test_cache_returns_same_instance(self, monkeypatch):
        """Factory caches connector instances."""
        monkeypatch.setenv("X_BEARER_TOKEN", "test-token")
        c1 = ConnectorFactory.create(Platform.X)
        c2 = ConnectorFactory.create(Platform.X)
        assert c1 is c2

    def test_clear_cache(self, monkeypatch):
        """clear_cache removes cached instances."""
        monkeypatch.setenv("X_BEARER_TOKEN", "test-token")
        c1 = ConnectorFactory.create(Platform.X)
        ConnectorFactory.clear_cache()
        c2 = ConnectorFactory.create(Platform.X)
        assert c1 is not c2

    def test_create_all_default(self, monkeypatch):
        """create_all with no platforms config returns X only."""
        monkeypatch.setenv("X_BEARER_TOKEN", "test-token")
        from tests.conftest import make_test_config
        config = make_test_config()
        connectors = ConnectorFactory.create_all(config)
        assert Platform.X in connectors
        assert len(connectors) == 1

    def test_socialdata_not_implemented(self):
        """SocialData connector raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            ConnectorFactory.create(Platform.SOCIALDATA)
```

### Step 11: Platform Enum Tests

**Create `tests/unit/test_platform.py`:**

```python
"""Tests for Platform enum and validation."""

import pytest
from signalops.connectors.base import Platform


class TestPlatform:
    def test_from_string_valid(self):
        assert Platform.from_string("x") == Platform.X
        assert Platform.from_string("linkedin") == Platform.LINKEDIN
        assert Platform.from_string("X") == Platform.X  # Case insensitive

    def test_from_string_invalid(self):
        with pytest.raises(ValueError, match="Unknown platform"):
            Platform.from_string("tiktok")

    def test_all_platforms_have_values(self):
        """Every platform has a lowercase string value."""
        for p in Platform:
            assert p.value == p.value.lower()
```

### Step 12: Multi-Platform Normalizer Tests

**Update `tests/unit/test_normalizer.py`:**

```python
def test_normalize_linkedin_post():
    """Normalizer handles LinkedIn post format."""
    raw_json = {
        "_source": "linkedin",
        "text": "Excited about our new code review automation!",
        "author": {"name": "Jane Doe", "headline": "CTO at TechCo"},
    }
    # Test that normalizer extracts entities from text for LinkedIn
    # (no native entity expansion like X API)

def test_platform_specific_char_limits():
    """Drafter respects platform-specific character limits."""
    assert PLATFORM_CHAR_LIMITS["x"] == 280
    assert PLATFORM_CHAR_LIMITS["linkedin"] == 1300
```

---

## 6. File Manifest

### New Files

```
src/signalops/connectors/linkedin.py          # LinkedInConnector (stubbed)
src/signalops/connectors/factory.py            # ConnectorFactory
tests/unit/test_connector_contract.py          # Interface contract tests
tests/unit/test_connector_factory.py           # Factory tests
tests/unit/test_platform.py                    # Platform enum tests
```

### Modified Files

```
src/signalops/connectors/base.py              # Add Platform enum, validate in RawPost
src/signalops/config/schema.py                # Add PlatformConfig, PlatformsConfig, query platform field
src/signalops/pipeline/normalizer.py           # Platform-specific entity extraction
src/signalops/pipeline/collector.py            # Parameterize platform, filter queries by platform
src/signalops/pipeline/drafter.py             # Platform-specific char limits
src/signalops/pipeline/sender.py              # Route to correct connector by platform
src/signalops/cli/main.py                     # Update connector creation to use factory
```

---

## 7. Testing Plan

### Unit Tests

| Test File | Coverage |
|-----------|----------|
| `test_connector_contract.py` | Interface contract: search returns list, get_user returns dict, health_check returns bool |
| `test_connector_factory.py` | Factory creation, caching, error handling, create_all |
| `test_platform.py` | Enum from_string, case insensitivity, invalid values |
| `test_normalizer.py` (updated) | Platform-specific normalization (LinkedIn entities) |

### Integration Tests

None needed for T4 specifically — LinkedIn is stubbed and the factory is tested via unit tests.
Cross-terminal integration tests in Phase 3 will verify the full multi-platform pipeline.

### Key Test Scenarios

1. **LinkedIn returns empty**: Stubbed connector returns `[]` from search, not exception
2. **LinkedIn blocks writes**: `post_reply` always raises `NotImplementedError`
3. **Factory routing**: "x" → XConnector, "linkedin" → LinkedInConnector, "tiktok" → ValueError
4. **Config backward compat**: Project YAML without `platforms` section still works (defaults to X)
5. **Query filtering**: Only X-platform queries run when LinkedIn is disabled
6. **Platform char limits**: Drafter respects 280 for X, 1300 for LinkedIn

---

## Acceptance Criteria

- [ ] `Platform.from_string("linkedin")` returns `Platform.LINKEDIN`
- [ ] `ConnectorFactory.create("linkedin")` returns a `LinkedInConnector`
- [ ] `LinkedInConnector.search()` returns empty list (stubbed)
- [ ] `LinkedInConnector.post_reply()` raises `NotImplementedError` (read-only)
- [ ] `ConnectorFactory.create_all(config)` creates only enabled platform connectors
- [ ] Existing X connector creation still works via factory
- [ ] Project YAML without `platforms` section uses X as default
- [ ] Per-query `platform` field filters correctly in collector
- [ ] Normalizer handles LinkedIn post format
- [ ] All connector contract tests pass for both X (mocked) and LinkedIn (stubbed)
- [ ] `ruff check` and `mypy --strict` pass on all new code
- [ ] All new and existing tests pass

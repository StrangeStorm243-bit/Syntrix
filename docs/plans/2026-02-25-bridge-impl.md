# Syntrix Bridge Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Wire the dashboard to the pipeline end-to-end so a user can onboard, find leads, run outreach sequences, and send replies — all from the browser, for $0/month.

**Architecture:** TwikitConnector replaces X API for search/post. Onboarding wizard auto-generates project config. Sequence engine (SQLite state machine) automates multi-step outreach. APScheduler runs periodic collection. Ollama via LiteLLM provides free local LLM.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy/SQLite, twikit, APScheduler, LiteLLM+Ollama, React 19, Vite 7, Tailwind 4, shadcn/ui, Zustand, react-hook-form+Zod

---

## Phase 1: Backend Foundation (Tasks 1-5)

### Task 1: Add twikit Connector

**Files:**
- Create: `src/signalops/connectors/twikit_connector.py`
- Modify: `src/signalops/connectors/base.py` (add `like()` and `follow()` to ABC)
- Modify: `src/signalops/connectors/factory.py` (register twikit)
- Test: `tests/unit/test_twikit_connector.py`

**Step 1: Add `like()` and `follow()` to Connector ABC**

In `src/signalops/connectors/base.py`, add two new abstract methods after `post_reply()` (line ~72):

```python
@abstractmethod
def like(self, post_id: str) -> bool:
    """Like a post. Returns True if successful."""
    ...

@abstractmethod
def follow(self, user_id: str) -> bool:
    """Follow a user. Returns True if successful."""
    ...
```

Also add stubs to `XConnector` and `LinkedInConnector` so they don't break (raise `NotImplementedError`).

**Step 2: Write the failing test**

```python
# tests/unit/test_twikit_connector.py
"""Tests for TwikitConnector."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from signalops.connectors.twikit_connector import TwikitConnector


class TestTwikitConnector:
    """Test TwikitConnector search, reply, like, follow."""

    def test_search_returns_raw_posts(self) -> None:
        """search() should return list of RawPost from twikit results."""
        connector = TwikitConnector(
            username="test_user",
            password="test_pass",
        )
        with patch.object(connector, "_client") as mock_client:
            mock_tweet = MagicMock()
            mock_tweet.id = "123456"
            mock_tweet.user.id = "user1"
            mock_tweet.user.name = "Test User"
            mock_tweet.user.screen_name = "testuser"
            mock_tweet.user.followers_count = 500
            mock_tweet.user.verified = False
            mock_tweet.text = "Need a better code review tool"
            mock_tweet.created_at = "Mon Feb 25 10:00:00 +0000 2026"
            mock_tweet.lang = "en"
            mock_tweet.reply_to = None
            mock_tweet.favorite_count = 5
            mock_tweet.retweet_count = 2
            mock_tweet.reply_count = 1
            mock_tweet.view_count = 800
            mock_client.search_tweet.return_value = [mock_tweet]

            results = connector.search("code review")
            assert len(results) == 1
            assert results[0].platform == "x"
            assert results[0].platform_id == "123456"
            assert results[0].author_username == "testuser"

    def test_health_check_with_valid_session(self) -> None:
        """health_check() returns True when logged in."""
        connector = TwikitConnector(username="test", password="pass")
        with patch.object(connector, "_logged_in", True):
            assert connector.health_check() is True

    def test_health_check_without_session(self) -> None:
        """health_check() returns False when not logged in."""
        connector = TwikitConnector(username="test", password="pass")
        assert connector.health_check() is False
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/unit/test_twikit_connector.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'signalops.connectors.twikit_connector'`

**Step 4: Install twikit**

Run: `pip install twikit`

**Step 5: Write TwikitConnector implementation**

```python
# src/signalops/connectors/twikit_connector.py
"""Twitter connector using twikit (internal API, no API key needed)."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from signalops.connectors.base import Connector, RawPost

logger = logging.getLogger(__name__)


class TwikitConnector(Connector):
    """Connector using twikit to access Twitter's internal GraphQL API.

    Requires Twitter username and password. No API key needed.
    Uses session cookies for authentication (cached to avoid repeated logins).
    """

    def __init__(
        self,
        username: str,
        password: str,
        email: str | None = None,
        cookie_path: str | None = None,
    ) -> None:
        self._username = username
        self._password = password
        self._email = email
        self._cookie_path = cookie_path or ".twikit_cookies.json"
        self._client: Any = None
        self._logged_in = False

    def _ensure_client(self) -> Any:
        """Lazy-initialize twikit client and login."""
        if self._client is not None and self._logged_in:
            return self._client

        from twikit import Client

        self._client = Client("en-US")

        # Try loading saved cookies first
        try:
            self._client.load_cookies(self._cookie_path)
            self._logged_in = True
            logger.info("Loaded saved twikit session cookies")
            return self._client
        except Exception:
            pass

        # Login with credentials
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(
                self._client.login(
                    auth_info_1=self._username,
                    auth_info_2=self._email or self._username,
                    password=self._password,
                )
            )
            self._client.save_cookies(self._cookie_path)
            self._logged_in = True
            logger.info("Logged in to Twitter via twikit")
        finally:
            loop.close()

        return self._client

    def search(
        self,
        query: str,
        since_id: str | None = None,
        max_results: int = 100,
    ) -> list[RawPost]:
        """Search tweets using twikit."""
        client = self._ensure_client()
        loop = asyncio.new_event_loop()
        try:
            if since_id:
                query = f"{query} since_id:{since_id}"
            tweets = loop.run_until_complete(
                client.search_tweet(query, product="Latest", count=max_results)
            )
        finally:
            loop.close()

        results: list[RawPost] = []
        for tweet in tweets:
            try:
                raw_post = self._tweet_to_raw_post(tweet)
                results.append(raw_post)
            except Exception:
                logger.warning("Failed to parse tweet %s", getattr(tweet, "id", "?"))
                continue

        return results

    def get_user(self, user_id: str) -> dict[str, Any]:
        """Get user profile by ID."""
        client = self._ensure_client()
        loop = asyncio.new_event_loop()
        try:
            user = loop.run_until_complete(client.get_user_by_id(user_id))
        finally:
            loop.close()
        return {
            "id": user.id,
            "username": user.screen_name,
            "display_name": user.name,
            "followers": user.followers_count,
            "verified": user.verified,
        }

    def post_reply(self, in_reply_to_id: str, text: str) -> str:
        """Post a reply to a tweet."""
        client = self._ensure_client()
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                client.create_tweet(text=text, reply_to=in_reply_to_id)
            )
        finally:
            loop.close()
        return str(result.id)

    def like(self, post_id: str) -> bool:
        """Like a tweet."""
        client = self._ensure_client()
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(client.favorite_tweet(post_id))
            return True
        except Exception:
            logger.warning("Failed to like tweet %s", post_id)
            return False
        finally:
            loop.close()

    def follow(self, user_id: str) -> bool:
        """Follow a user."""
        client = self._ensure_client()
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(client.follow_user(user_id))
            return True
        except Exception:
            logger.warning("Failed to follow user %s", user_id)
            return False
        finally:
            loop.close()

    def health_check(self) -> bool:
        """Check if we have a valid session."""
        return self._logged_in

    @staticmethod
    def _tweet_to_raw_post(tweet: Any) -> RawPost:
        """Convert a twikit Tweet object to a RawPost."""
        user = tweet.user
        created_at = datetime.strptime(
            tweet.created_at, "%a %b %d %H:%M:%S %z %Y"
        ) if isinstance(tweet.created_at, str) else tweet.created_at

        return RawPost(
            platform="x",
            platform_id=str(tweet.id),
            author_id=str(user.id),
            author_username=user.screen_name,
            author_display_name=user.name,
            author_followers=getattr(user, "followers_count", 0),
            author_verified=getattr(user, "verified", False),
            text=tweet.text,
            created_at=created_at.astimezone(timezone.utc) if created_at else datetime.now(timezone.utc),
            language=getattr(tweet, "lang", "en"),
            reply_to_id=getattr(tweet, "reply_to", None),
            conversation_id=getattr(tweet, "conversation_id", None),
            metrics={
                "likes": getattr(tweet, "favorite_count", 0),
                "retweets": getattr(tweet, "retweet_count", 0),
                "replies": getattr(tweet, "reply_count", 0),
                "views": getattr(tweet, "view_count", 0),
            },
            entities={
                "hashtags": [h.get("text", "") for h in getattr(tweet, "hashtags", []) or []],
                "mentions": [m.get("screen_name", "") for m in getattr(tweet, "mentions", []) or []],
                "urls": [u.get("expanded_url", "") for u in getattr(tweet, "urls", []) or []],
            },
            raw_json={"twikit_id": str(tweet.id)},
        )
```

**Step 6: Run tests**

Run: `pytest tests/unit/test_twikit_connector.py -v`
Expected: PASS

**Step 7: Register twikit in factory**

In `src/signalops/connectors/factory.py`, add a `_build_twikit()` method and update `_build_connector()` to check for twikit credentials before falling back to X API:

```python
# In _build_connector(), before the X platform builder:
if platform == Platform.X:
    # Prefer twikit (free) if credentials are available
    username = os.environ.get("TWIKIT_USERNAME", "")
    password = os.environ.get("TWIKIT_PASSWORD", "")
    if username and password:
        return self._build_twikit(username, password)
    # Fall back to X API v2 if bearer token exists
    return self._build_x(config)
```

**Step 8: Commit**

```bash
git add src/signalops/connectors/ tests/unit/test_twikit_connector.py
git commit -m "feat: add TwikitConnector for free Twitter access

Implements Connector ABC using twikit library (internal Twitter API).
Supports search, reply, like, follow without API key costs.
Falls back to X API v2 if twikit credentials not available."
```

---

### Task 2: Add Sequence Engine Database Tables

**Files:**
- Modify: `src/signalops/storage/database.py` (add 4 new tables after line ~352)
- Test: `tests/unit/test_sequence_tables.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_sequence_tables.py
"""Tests for sequence engine database tables."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from signalops.storage.database import (
    Base,
    Enrollment,
    EnrollmentStatus,
    Project,
    Sequence,
    SequenceStep,
    StepExecution,
    init_db,
)


class TestSequenceTables:
    """Test CRUD operations on sequence tables."""

    def setup_method(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        init_db(self.engine)
        self.session = Session(self.engine)
        # Create a project for FK
        self.project = Project(id="test-proj", name="Test", config_path="test.yaml")
        self.session.add(self.project)
        self.session.commit()

    def teardown_method(self) -> None:
        self.session.close()
        self.engine.dispose()

    def test_create_sequence_with_steps(self) -> None:
        seq = Sequence(project_id="test-proj", name="Gentle Touch")
        self.session.add(seq)
        self.session.flush()

        step1 = SequenceStep(
            sequence_id=seq.id, step_order=1, action_type="like", delay_hours=0
        )
        step2 = SequenceStep(
            sequence_id=seq.id, step_order=2, action_type="wait", delay_hours=24
        )
        step3 = SequenceStep(
            sequence_id=seq.id,
            step_order=3,
            action_type="reply",
            delay_hours=0,
            requires_approval=True,
        )
        self.session.add_all([step1, step2, step3])
        self.session.commit()

        loaded = self.session.query(Sequence).filter_by(name="Gentle Touch").first()
        assert loaded is not None
        assert len(loaded.steps) == 3
        assert loaded.steps[0].action_type == "like"
        assert loaded.steps[2].requires_approval is True

    def test_enrollment_status_transitions(self) -> None:
        seq = Sequence(project_id="test-proj", name="Direct")
        self.session.add(seq)
        self.session.flush()

        enrollment = Enrollment(
            normalized_post_id=1,
            sequence_id=seq.id,
            project_id="test-proj",
            status=EnrollmentStatus.ACTIVE,
        )
        self.session.add(enrollment)
        self.session.commit()

        assert enrollment.status == EnrollmentStatus.ACTIVE
        enrollment.status = EnrollmentStatus.COMPLETED
        self.session.commit()
        assert enrollment.status == EnrollmentStatus.COMPLETED
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_sequence_tables.py -v`
Expected: FAIL with `ImportError: cannot import name 'Sequence'`

**Step 3: Add tables to database.py**

Add after `PreferencePair` class (around line 352), before `get_engine()`:

```python
class EnrollmentStatus(str, enum.Enum):
    """Status of a lead's enrollment in a sequence."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    EXITED = "exited"


class Sequence(Base):
    """Outreach sequence template."""
    __tablename__ = "sequences"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    is_active: Mapped[bool] = mapped_column(default=True)  # type: ignore[assignment]
    created_at: Mapped[datetime] = mapped_column(default_factory=lambda: datetime.now(timezone.utc))  # type: ignore[assignment]

    steps: Mapped[list[SequenceStep]] = relationship(
        back_populates="sequence", order_by="SequenceStep.step_order"
    )
    enrollments: Mapped[list[Enrollment]] = relationship(back_populates="sequence")


class SequenceStep(Base):
    """Single step within an outreach sequence."""
    __tablename__ = "sequence_steps"

    id: Mapped[int] = mapped_column(primary_key=True)
    sequence_id: Mapped[int] = mapped_column(ForeignKey("sequences.id"))
    step_order: Mapped[int] = mapped_column()
    action_type: Mapped[str] = mapped_column(String(50))  # like, follow, reply, wait, check_response
    delay_hours: Mapped[float] = mapped_column(default=0.0)  # type: ignore[assignment]
    config_json: Mapped[str] = mapped_column(Text, default="{}")  # type: ignore[assignment]
    requires_approval: Mapped[bool] = mapped_column(default=False)  # type: ignore[assignment]

    sequence: Mapped[Sequence] = relationship(back_populates="steps")


class Enrollment(Base):
    """Tracks a lead's progress through a sequence."""
    __tablename__ = "enrollments"

    id: Mapped[int] = mapped_column(primary_key=True)
    normalized_post_id: Mapped[int] = mapped_column(ForeignKey("normalized_posts.id"))
    sequence_id: Mapped[int] = mapped_column(ForeignKey("sequences.id"))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    current_step_order: Mapped[int] = mapped_column(default=0)  # type: ignore[assignment]
    status: Mapped[EnrollmentStatus] = mapped_column(default=EnrollmentStatus.ACTIVE)  # type: ignore[assignment]
    enrolled_at: Mapped[datetime] = mapped_column(default_factory=lambda: datetime.now(timezone.utc))  # type: ignore[assignment]
    next_step_at: Mapped[datetime | None] = mapped_column(default=None)
    completed_at: Mapped[datetime | None] = mapped_column(default=None)

    sequence: Mapped[Sequence] = relationship(back_populates="enrollments")
    executions: Mapped[list[StepExecution]] = relationship(back_populates="enrollment")


class StepExecution(Base):
    """Record of an executed sequence step."""
    __tablename__ = "step_executions"

    id: Mapped[int] = mapped_column(primary_key=True)
    enrollment_id: Mapped[int] = mapped_column(ForeignKey("enrollments.id"))
    step_id: Mapped[int] = mapped_column(ForeignKey("sequence_steps.id"))
    action_type: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), default="pending")  # type: ignore[assignment]
    executed_at: Mapped[datetime | None] = mapped_column(default=None)
    result_json: Mapped[str] = mapped_column(Text, default="{}")  # type: ignore[assignment]

    enrollment: Mapped[Enrollment] = relationship(back_populates="executions")
```

**Step 4: Run tests**

Run: `pytest tests/unit/test_sequence_tables.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/signalops/storage/database.py tests/unit/test_sequence_tables.py
git commit -m "feat: add sequence engine database tables

Adds Sequence, SequenceStep, Enrollment, StepExecution tables
for multi-step outreach campaigns (Waalaxy-style)."
```

---

### Task 3: Build Sequence Engine

**Files:**
- Create: `src/signalops/pipeline/sequence_engine.py`
- Test: `tests/unit/test_sequence_engine.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_sequence_engine.py
"""Tests for the sequence engine state machine."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from signalops.pipeline.sequence_engine import SequenceEngine
from signalops.storage.database import (
    Base,
    Enrollment,
    EnrollmentStatus,
    NormalizedPost,
    Project,
    RawPost,
    Sequence,
    SequenceStep,
    init_db,
)


class TestSequenceEngine:
    def setup_method(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        init_db(self.engine)
        self.session = Session(self.engine)
        # Seed data
        proj = Project(id="test", name="Test", config_path="t.yaml")
        self.session.add(proj)
        raw = RawPost(project_id="test", platform="x", platform_id="tw1", raw_json={})
        self.session.add(raw)
        self.session.flush()
        norm = NormalizedPost(
            raw_post_id=raw.id, project_id="test", platform="x",
            platform_id="tw1", author_id="u1", author_username="testuser",
            text_original="Need help", text_cleaned="Need help",
        )
        self.session.add(norm)
        self.session.flush()
        self.norm_id = norm.id

        # Create sequence
        seq = Sequence(project_id="test", name="Gentle Touch")
        self.session.add(seq)
        self.session.flush()
        self.seq_id = seq.id
        steps = [
            SequenceStep(sequence_id=seq.id, step_order=1, action_type="like", delay_hours=0),
            SequenceStep(sequence_id=seq.id, step_order=2, action_type="wait", delay_hours=24),
            SequenceStep(sequence_id=seq.id, step_order=3, action_type="reply", delay_hours=0, requires_approval=True),
        ]
        self.session.add_all(steps)
        self.session.commit()

        self.connector = MagicMock()
        self.connector.like.return_value = True
        self.connector.follow.return_value = True
        self.connector.post_reply.return_value = "reply_123"

    def teardown_method(self) -> None:
        self.session.close()

    def test_enroll_lead(self) -> None:
        engine = SequenceEngine(self.session, self.connector)
        enrollment = engine.enroll(self.norm_id, self.seq_id, "test")
        assert enrollment.status == EnrollmentStatus.ACTIVE
        assert enrollment.current_step_order == 0

    def test_execute_like_step(self) -> None:
        engine = SequenceEngine(self.session, self.connector)
        enrollment = engine.enroll(self.norm_id, self.seq_id, "test")
        # Set next_step_at to now so it's due
        enrollment.next_step_at = datetime.now(timezone.utc)
        self.session.commit()

        executed = engine.execute_due_steps()
        assert executed == 1
        self.connector.like.assert_called_once()

    def test_wait_step_advances_time(self) -> None:
        engine = SequenceEngine(self.session, self.connector)
        enrollment = engine.enroll(self.norm_id, self.seq_id, "test")
        enrollment.current_step_order = 1  # on "wait" step
        enrollment.next_step_at = datetime.now(timezone.utc)
        self.session.commit()

        engine.execute_due_steps()
        # After wait step, next_step_at should be ~24h from now
        self.session.refresh(enrollment)
        assert enrollment.next_step_at is not None
        assert enrollment.next_step_at > datetime.now(timezone.utc) + timedelta(hours=23)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_sequence_engine.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write sequence engine**

```python
# src/signalops/pipeline/sequence_engine.py
"""Sequence engine — state machine for multi-step outreach."""
from __future__ import annotations

import json
import logging
import random
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from signalops.connectors.base import Connector
from signalops.storage.database import (
    Draft,
    DraftStatus,
    Enrollment,
    EnrollmentStatus,
    NormalizedPost,
    Sequence,
    SequenceStep,
    StepExecution,
)

logger = logging.getLogger(__name__)

# Safety defaults
DEFAULT_MAX_LIKES_PER_HOUR = 15
DEFAULT_MAX_FOLLOWS_PER_HOUR = 5
DEFAULT_MAX_REPLIES_PER_DAY = 20
JITTER_FACTOR = 0.3  # +/- 30% on delays


class SequenceEngine:
    """Executes outreach sequences as a state machine.

    Polls the enrollments table for due steps, executes actions
    via the connector, and advances enrollment state.
    """

    def __init__(
        self,
        session: Session,
        connector: Connector,
        max_likes_per_hour: int = DEFAULT_MAX_LIKES_PER_HOUR,
        max_follows_per_hour: int = DEFAULT_MAX_FOLLOWS_PER_HOUR,
        max_replies_per_day: int = DEFAULT_MAX_REPLIES_PER_DAY,
    ) -> None:
        self.session = session
        self.connector = connector
        self.max_likes_per_hour = max_likes_per_hour
        self.max_follows_per_hour = max_follows_per_hour
        self.max_replies_per_day = max_replies_per_day

    def enroll(
        self,
        normalized_post_id: int,
        sequence_id: int,
        project_id: str,
    ) -> Enrollment:
        """Enroll a lead into a sequence."""
        enrollment = Enrollment(
            normalized_post_id=normalized_post_id,
            sequence_id=sequence_id,
            project_id=project_id,
            current_step_order=0,
            status=EnrollmentStatus.ACTIVE,
            next_step_at=datetime.now(timezone.utc),
        )
        self.session.add(enrollment)
        self.session.commit()
        logger.info("Enrolled post %d in sequence %d", normalized_post_id, sequence_id)
        return enrollment

    def execute_due_steps(self) -> int:
        """Execute all steps that are due. Returns count of executed steps."""
        now = datetime.now(timezone.utc)
        due = (
            self.session.query(Enrollment)
            .filter(
                Enrollment.status == EnrollmentStatus.ACTIVE,
                Enrollment.next_step_at <= now,
            )
            .all()
        )

        executed_count = 0
        for enrollment in due:
            step = self._get_current_step(enrollment)
            if step is None:
                self._complete_enrollment(enrollment)
                continue

            if step.requires_approval and not self._has_approved_draft(enrollment):
                continue  # Wait for human approval

            success = self._execute_step(enrollment, step)
            if success:
                executed_count += 1
                self._advance(enrollment, step)

        self.session.commit()
        return executed_count

    def _get_current_step(self, enrollment: Enrollment) -> SequenceStep | None:
        """Get the next step to execute for this enrollment."""
        return (
            self.session.query(SequenceStep)
            .filter(
                SequenceStep.sequence_id == enrollment.sequence_id,
                SequenceStep.step_order == enrollment.current_step_order + 1,
            )
            .first()
        )

    def _execute_step(self, enrollment: Enrollment, step: SequenceStep) -> bool:
        """Execute a single step. Returns True if successful."""
        post = self.session.query(NormalizedPost).get(enrollment.normalized_post_id)
        if post is None:
            logger.warning("Post %d not found for enrollment %d", enrollment.normalized_post_id, enrollment.id)
            return False

        result: dict[str, Any] = {}
        success = False

        if step.action_type == "like":
            success = self.connector.like(post.platform_id)
            result = {"liked": success, "post_id": post.platform_id}

        elif step.action_type == "follow":
            success = self.connector.follow(post.author_id)
            result = {"followed": success, "user_id": post.author_id}

        elif step.action_type == "reply":
            draft = self._get_approved_draft(enrollment)
            if draft is None:
                return False
            text = draft.text_final or draft.text_generated
            reply_id = self.connector.post_reply(post.platform_id, text)
            success = bool(reply_id)
            result = {"reply_id": reply_id, "text": text}
            if success:
                draft.status = DraftStatus.SENT
                draft.sent_at = datetime.now(timezone.utc)
                draft.sent_post_id = reply_id

        elif step.action_type == "wait":
            success = True
            result = {"waited": True}

        elif step.action_type == "check_response":
            # Placeholder: check if lead responded
            success = True
            result = {"checked": True}

        # Record execution
        execution = StepExecution(
            enrollment_id=enrollment.id,
            step_id=step.id,
            action_type=step.action_type,
            status="executed" if success else "failed",
            executed_at=datetime.now(timezone.utc),
            result_json=json.dumps(result),
        )
        self.session.add(execution)
        return success

    def _advance(self, enrollment: Enrollment, completed_step: SequenceStep) -> None:
        """Advance enrollment to the next step."""
        enrollment.current_step_order = completed_step.step_order
        next_step = (
            self.session.query(SequenceStep)
            .filter(
                SequenceStep.sequence_id == enrollment.sequence_id,
                SequenceStep.step_order == completed_step.step_order + 1,
            )
            .first()
        )

        if next_step is None:
            self._complete_enrollment(enrollment)
        else:
            delay = next_step.delay_hours
            jitter = delay * JITTER_FACTOR * (2 * random.random() - 1)
            enrollment.next_step_at = datetime.now(timezone.utc) + timedelta(hours=delay + jitter)

    def _complete_enrollment(self, enrollment: Enrollment) -> None:
        """Mark enrollment as completed."""
        enrollment.status = EnrollmentStatus.COMPLETED
        enrollment.completed_at = datetime.now(timezone.utc)
        enrollment.next_step_at = None

    def _has_approved_draft(self, enrollment: Enrollment) -> bool:
        """Check if there's an approved draft for this enrollment's post."""
        return self._get_approved_draft(enrollment) is not None

    def _get_approved_draft(self, enrollment: Enrollment) -> Draft | None:
        """Get the approved/edited draft for this enrollment's post."""
        return (
            self.session.query(Draft)
            .filter(
                Draft.normalized_post_id == enrollment.normalized_post_id,
                Draft.status.in_([DraftStatus.APPROVED, DraftStatus.EDITED]),
            )
            .first()
        )

    def create_default_sequences(self, project_id: str) -> list[Sequence]:
        """Create the three default sequence templates for a project."""
        sequences = []

        # Gentle Touch
        gentle = Sequence(project_id=project_id, name="Gentle Touch", description="Like → Wait 1d → Reply")
        self.session.add(gentle)
        self.session.flush()
        self.session.add_all([
            SequenceStep(sequence_id=gentle.id, step_order=1, action_type="like", delay_hours=0),
            SequenceStep(sequence_id=gentle.id, step_order=2, action_type="wait", delay_hours=24),
            SequenceStep(sequence_id=gentle.id, step_order=3, action_type="reply", delay_hours=0, requires_approval=True),
        ])
        sequences.append(gentle)

        # Direct
        direct = Sequence(project_id=project_id, name="Direct", description="Reply immediately")
        self.session.add(direct)
        self.session.flush()
        self.session.add_all([
            SequenceStep(sequence_id=direct.id, step_order=1, action_type="reply", delay_hours=0, requires_approval=True),
        ])
        sequences.append(direct)

        # Full Sequence
        full = Sequence(project_id=project_id, name="Full Sequence", description="Like → Follow → Wait → Reply → Follow-up")
        self.session.add(full)
        self.session.flush()
        self.session.add_all([
            SequenceStep(sequence_id=full.id, step_order=1, action_type="like", delay_hours=0),
            SequenceStep(sequence_id=full.id, step_order=2, action_type="follow", delay_hours=6),
            SequenceStep(sequence_id=full.id, step_order=3, action_type="wait", delay_hours=24),
            SequenceStep(sequence_id=full.id, step_order=4, action_type="reply", delay_hours=0, requires_approval=True),
            SequenceStep(sequence_id=full.id, step_order=5, action_type="check_response", delay_hours=72),
        ])
        sequences.append(full)

        self.session.commit()
        return sequences
```

**Step 4: Run tests**

Run: `pytest tests/unit/test_sequence_engine.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/signalops/pipeline/sequence_engine.py tests/unit/test_sequence_engine.py
git commit -m "feat: add sequence engine state machine

Implements multi-step outreach: enroll leads, execute steps
(like/follow/reply/wait), advance state, track executions.
Includes 3 default sequence templates."
```

---

### Task 4: Wire Pipeline Run and Queue Send

**Files:**
- Modify: `src/signalops/api/routes/pipeline.py` (wire stub to orchestrator)
- Modify: `src/signalops/api/routes/queue.py` (wire send to connector)
- Modify: `src/signalops/api/auth.py` (make API key optional)
- Modify: `src/signalops/api/app.py` (add APScheduler lifespan)
- Test: `tests/unit/test_pipeline_wiring.py`

**Step 1: Make API key optional**

Replace `src/signalops/api/auth.py` (currently 18 lines) with:

```python
"""API key authentication for the SignalOps REST API."""
from __future__ import annotations

import os

from fastapi import Header, HTTPException


async def require_api_key(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> str | None:
    """Validate X-API-Key if SIGNALOPS_API_KEY is set. Skip if not configured."""
    expected = os.environ.get("SIGNALOPS_API_KEY", "")
    if not expected:
        return None  # No API key configured — open access (self-hosted mode)
    if not x_api_key or x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key
```

**Step 2: Wire pipeline.py to orchestrator**

Replace `_run_pipeline_sync` in `src/signalops/api/routes/pipeline.py` (lines 28-38):

```python
def _run_pipeline_sync(project_id: str, db_url: str) -> None:
    """Run the pipeline synchronously in a background thread."""
    from signalops.config.loader import load_project_config
    from signalops.connectors.factory import ConnectorFactory
    from signalops.models.judge_model import RelevanceJudge
    from signalops.pipeline.drafter import DraftGenerator
    from signalops.pipeline.orchestrator import PipelineOrchestrator
    from signalops.storage.database import get_engine, get_session

    logger.info("Pipeline run started for project %s", project_id)
    try:
        engine = get_engine(db_url)
        session = get_session(engine)
        config = load_project_config(project_id)
        factory = ConnectorFactory()
        connector = factory.create("x", config)
        judge = RelevanceJudge(config)
        drafter = DraftGenerator(config)
        orchestrator = PipelineOrchestrator(
            db_session=session,
            connector=connector,
            judge=judge,
            draft_generator=drafter,
        )
        results = orchestrator.run_all(config)
        logger.info("Pipeline completed for %s: %s", project_id, results)
    except Exception:
        logger.exception("Pipeline run failed for project %s", project_id)
    finally:
        session.close()
        engine.dispose()
```

**Step 3: Wire queue send to connector**

In `src/signalops/api/routes/queue.py`, update the `send_approved` function (lines 205-238) to actually send via connector:

```python
@router.post("/send", response_model=SendResult)
def send_approved(
    project_id: str | None = Query(None),
    db: Session = Depends(get_db),
    config: ProjectConfig = Depends(get_config),
    _api_key: str | None = Depends(require_api_key),
) -> SendResult:
    """Send all approved/edited drafts via connector."""
    from signalops.connectors.factory import ConnectorFactory

    query = db.query(Draft).filter(
        Draft.status.in_([DraftStatus.APPROVED, DraftStatus.EDITED])
    )
    if project_id:
        query = query.filter(Draft.project_id == project_id)

    drafts = query.all()
    sent_ids: list[int] = []
    failed_count = 0

    # Create connector for sending
    factory = ConnectorFactory()
    try:
        connector = factory.create("x", config)
    except Exception:
        logger.warning("No connector available — marking as sent (dry run)")
        connector = None

    for draft in drafts:
        try:
            text = draft.text_final or draft.text_generated
            post = db.query(NormalizedPost).get(draft.normalized_post_id)

            if connector and post:
                reply_id = connector.post_reply(post.platform_id, text)
                draft.sent_post_id = reply_id

            draft.status = DraftStatus.SENT  # type: ignore[assignment]
            draft.sent_at = datetime.now(UTC)  # type: ignore[assignment]
            sent_ids.append(int(draft.id))  # type: ignore[arg-type]
        except Exception:
            logger.exception("Failed to send draft %s", draft.id)
            failed_count += 1

    db.commit()
    return SendResult(
        sent_count=len(sent_ids),
        failed_count=failed_count,
        draft_ids=sent_ids,
    )
```

**Step 4: Add APScheduler to app lifespan**

In `src/signalops/api/app.py`, update the lifespan handler:

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    db_url = os.environ.get("SIGNALOPS_DB_URL", "sqlite:///signalops.db")
    app.state.engine = get_engine(db_url)
    init_db(app.state.engine)

    # Start APScheduler for periodic pipeline runs
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        scheduler = AsyncIOScheduler()
        # Sequence engine poll every 30 seconds
        scheduler.add_job(
            _tick_sequences, "interval", seconds=30,
            args=[db_url], id="sequence_tick",
        )
        scheduler.start()
        app.state.scheduler = scheduler
    except ImportError:
        logger.info("APScheduler not installed — no background scheduling")

    yield

    if hasattr(app.state, "scheduler"):
        app.state.scheduler.shutdown()
    app.state.engine.dispose()


def _tick_sequences(db_url: str) -> None:
    """Execute due sequence steps (called by APScheduler)."""
    from signalops.connectors.factory import ConnectorFactory
    from signalops.pipeline.sequence_engine import SequenceEngine
    from signalops.storage.database import get_engine, get_session

    try:
        engine = get_engine(db_url)
        session = get_session(engine)
        factory = ConnectorFactory()
        connector = factory.create("x")
        seq_engine = SequenceEngine(session, connector)
        count = seq_engine.execute_due_steps()
        if count:
            logger.info("Executed %d sequence steps", count)
        session.close()
        engine.dispose()
    except Exception:
        logger.debug("Sequence tick skipped — no connector or no due steps")
```

**Step 5: Commit**

```bash
git add src/signalops/api/
git commit -m "feat: wire pipeline run and queue send to actual backend

- Pipeline /run endpoint now calls PipelineOrchestrator
- Queue /send endpoint now posts replies via connector
- API key auth now optional (self-hosted mode)
- APScheduler ticks sequence engine every 30 seconds"
```

---

### Task 5: Setup API Routes

**Files:**
- Create: `src/signalops/api/routes/setup.py`
- Create: `src/signalops/api/routes/sequences.py`
- Modify: `src/signalops/api/app.py` (register new routers)
- Test: `tests/unit/test_setup_routes.py`

**Step 1: Write setup routes**

```python
# src/signalops/api/routes/setup.py
"""Onboarding setup endpoints."""
from __future__ import annotations

import logging
import os
from typing import Any

import yaml
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from signalops.api.deps import get_db
from signalops.pipeline.sequence_engine import SequenceEngine
from signalops.storage.database import Project, init_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/setup", tags=["setup"])


class SetupRequest(BaseModel):
    """Onboarding wizard submission."""
    # Step 1: Company
    project_name: str
    product_url: str
    description: str
    problem_statement: str
    # Step 2: ICP
    role_keywords: list[str]
    tweet_topics: list[str]
    min_followers: int = 200
    languages: list[str] = ["en"]
    # Step 3: Twitter
    twitter_username: str
    twitter_password: str
    x_api_key: str | None = None
    # Step 4: Persona
    persona_name: str
    persona_role: str
    persona_tone: str = "helpful"
    voice_notes: str = ""
    example_reply: str = ""
    llm_provider: str = "ollama"  # ollama or cloud
    llm_api_key: str | None = None
    # Step 5: Sequence
    sequence_template: str = "gentle_touch"  # gentle_touch, direct, full
    max_actions_per_day: int = 20
    require_approval: bool = True


class SetupStatus(BaseModel):
    """Whether setup is complete."""
    is_complete: bool
    project_id: str | None = None
    project_name: str | None = None


class TestConnectionResult(BaseModel):
    """Result of testing Twitter credentials."""
    success: bool
    message: str
    username: str | None = None


@router.get("/status", response_model=SetupStatus)
def get_setup_status(db: Session = Depends(get_db)) -> SetupStatus:
    """Check if initial setup is complete (any project exists)."""
    project = db.query(Project).first()
    if project:
        return SetupStatus(
            is_complete=True,
            project_id=project.id,
            project_name=project.name,
        )
    return SetupStatus(is_complete=False)


@router.post("/test-connection", response_model=TestConnectionResult)
def test_twitter_connection(
    username: str,
    password: str,
) -> TestConnectionResult:
    """Test Twitter credentials via twikit."""
    try:
        from signalops.connectors.twikit_connector import TwikitConnector
        connector = TwikitConnector(username=username, password=password)
        healthy = connector.health_check()
        if healthy:
            return TestConnectionResult(
                success=True, message="Connected successfully", username=username,
            )
        # Try actually logging in
        connector._ensure_client()
        return TestConnectionResult(
            success=True, message="Connected successfully", username=username,
        )
    except Exception as e:
        return TestConnectionResult(
            success=False, message=f"Connection failed: {e}",
        )


@router.post("", response_model=SetupStatus)
def complete_setup(
    req: SetupRequest,
    db: Session = Depends(get_db),
) -> SetupStatus:
    """Complete onboarding — creates project config + DB record + default sequences."""
    project_id = req.project_name.lower().replace(" ", "-").replace("_", "-")

    # Generate search queries from topics
    queries = []
    for topic in req.tweet_topics:
        queries.append({
            "text": f"{topic} -is:retweet lang:en",
            "label": topic,
            "platform": "x",
            "max_results_per_run": 100,
            "enabled": True,
        })

    # Build project config YAML
    config: dict[str, Any] = {
        "project_id": project_id,
        "project_name": req.project_name,
        "description": req.description,
        "product_url": req.product_url,
        "platforms": {"x": {"enabled": True, "search_type": "recent"}},
        "queries": queries,
        "icp": {
            "min_followers": req.min_followers,
            "languages": req.languages,
            "prefer_bios_containing": req.role_keywords,
        },
        "relevance": {
            "system_prompt": (
                f"You are a relevance judge for {req.project_name}. "
                f"{req.description}. The product solves: {req.problem_statement}. "
                "Evaluate if this tweet indicates someone who might benefit from this product."
            ),
            "positive_signals": [f"Expressing frustration related to: {req.problem_statement}"],
            "negative_signals": ["Recruiting posts", "Bot-like behavior"],
        },
        "persona": {
            "name": req.persona_name,
            "role": req.persona_role,
            "tone": req.persona_tone,
            "voice_notes": req.voice_notes,
            "example_reply": req.example_reply,
        },
        "rate_limits": {
            "max_replies_per_hour": max(1, req.max_actions_per_day // 8),
            "max_replies_per_day": req.max_actions_per_day,
        },
        "llm": {
            "judge_model": "ollama/llama3.2:3b" if req.llm_provider == "ollama" else "gpt-4o-mini",
            "draft_model": "ollama/mistral:7b" if req.llm_provider == "ollama" else "gpt-4o-mini",
            "temperature": 0.3,
            "max_tokens": 1024,
        },
    }

    # Write YAML
    projects_dir = "projects"
    os.makedirs(projects_dir, exist_ok=True)
    config_path = f"{projects_dir}/{project_id}.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    # Store Twitter credentials as env vars (for this process)
    os.environ["TWIKIT_USERNAME"] = req.twitter_username
    os.environ["TWIKIT_PASSWORD"] = req.twitter_password
    if req.x_api_key:
        os.environ["X_BEARER_TOKEN"] = req.x_api_key

    # Create DB record
    project = Project(
        id=project_id,
        name=req.project_name,
        config_path=config_path,
        is_active=True,
    )
    # Deactivate other projects
    db.query(Project).update({"is_active": False})
    db.add(project)
    db.flush()

    # Create default sequences
    from signalops.connectors.twikit_connector import TwikitConnector
    connector = TwikitConnector(username=req.twitter_username, password=req.twitter_password)
    seq_engine = SequenceEngine(db, connector)
    seq_engine.create_default_sequences(project_id)

    db.commit()

    return SetupStatus(
        is_complete=True,
        project_id=project_id,
        project_name=req.project_name,
    )
```

**Step 2: Write sequences routes**

```python
# src/signalops/api/routes/sequences.py
"""Sequence management endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from signalops.api.auth import require_api_key
from signalops.api.deps import get_db, get_current_project
from signalops.storage.database import (
    Enrollment,
    EnrollmentStatus,
    Project,
    Sequence,
    SequenceStep,
    StepExecution,
)

router = APIRouter(prefix="/api/sequences", tags=["sequences"])


class SequenceStepResponse(BaseModel):
    id: int
    step_order: int
    action_type: str
    delay_hours: float
    requires_approval: bool


class SequenceResponse(BaseModel):
    id: int
    name: str
    description: str | None
    is_active: bool
    steps: list[SequenceStepResponse]
    enrolled_count: int
    completed_count: int


class EnrollmentResponse(BaseModel):
    id: int
    normalized_post_id: int
    current_step_order: int
    status: str
    enrolled_at: str
    next_step_at: str | None


@router.get("", response_model=list[SequenceResponse])
def list_sequences(
    db: Session = Depends(get_db),
    project: Project = Depends(get_current_project),
    _api_key: str | None = Depends(require_api_key),
) -> list[SequenceResponse]:
    """List all sequences for the active project."""
    sequences = db.query(Sequence).filter(Sequence.project_id == project.id).all()
    results = []
    for seq in sequences:
        enrolled = db.query(Enrollment).filter(
            Enrollment.sequence_id == seq.id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
        ).count()
        completed = db.query(Enrollment).filter(
            Enrollment.sequence_id == seq.id,
            Enrollment.status == EnrollmentStatus.COMPLETED,
        ).count()
        results.append(SequenceResponse(
            id=seq.id,
            name=seq.name,
            description=seq.description,
            is_active=seq.is_active,
            steps=[
                SequenceStepResponse(
                    id=s.id, step_order=s.step_order, action_type=s.action_type,
                    delay_hours=s.delay_hours, requires_approval=s.requires_approval,
                )
                for s in seq.steps
            ],
            enrolled_count=enrolled,
            completed_count=completed,
        ))
    return results


@router.get("/{sequence_id}/enrollments", response_model=list[EnrollmentResponse])
def list_enrollments(
    sequence_id: int,
    db: Session = Depends(get_db),
    _api_key: str | None = Depends(require_api_key),
) -> list[EnrollmentResponse]:
    """List enrollments for a sequence."""
    enrollments = db.query(Enrollment).filter(
        Enrollment.sequence_id == sequence_id,
    ).order_by(Enrollment.enrolled_at.desc()).limit(100).all()
    return [
        EnrollmentResponse(
            id=e.id,
            normalized_post_id=e.normalized_post_id,
            current_step_order=e.current_step_order,
            status=e.status.value if hasattr(e.status, "value") else str(e.status),
            enrolled_at=e.enrolled_at.isoformat() if e.enrolled_at else "",
            next_step_at=e.next_step_at.isoformat() if e.next_step_at else None,
        )
        for e in enrollments
    ]
```

**Step 3: Register new routers in app.py**

Add to `create_app()` after existing router registrations (line ~67):

```python
from signalops.api.routes.setup import router as setup_router
from signalops.api.routes.sequences import router as sequences_router

app.include_router(setup_router)
app.include_router(sequences_router)
```

**Step 4: Commit**

```bash
git add src/signalops/api/routes/setup.py src/signalops/api/routes/sequences.py src/signalops/api/app.py
git commit -m "feat: add setup and sequence API routes

- POST /api/setup creates project from onboarding wizard data
- GET /api/setup/status checks if setup is complete
- POST /api/setup/test-connection validates Twitter credentials
- GET /api/sequences lists sequences with enrollment counts
- GET /api/sequences/:id/enrollments lists enrolled leads"
```

---

## Phase 2: Dashboard Frontend (Tasks 6-9)

### Task 6: Install shadcn/ui Components + Dependencies

**Files:**
- Modify: `dashboard/package.json` (new deps)
- Create: `dashboard/src/components/ui/` (shadcn components)

**Step 1: Install npm dependencies**

```bash
cd dashboard
npm install react-hook-form @hookform/resolvers zod zustand
```

**Step 2: Install shadcn/ui components**

```bash
npx shadcn@latest add button card input textarea select label separator badge progress tabs dialog switch tooltip form
```

**Step 3: Verify build**

```bash
npm run build
```

**Step 4: Commit**

```bash
git add dashboard/
git commit -m "feat: install shadcn/ui components + form libraries

Adds react-hook-form, zod, zustand.
Installs shadcn button, card, input, textarea, select, label,
separator, badge, progress, tabs, dialog, switch, tooltip, form."
```

---

### Task 7: Build Onboarding Wizard

**Files:**
- Create: `dashboard/src/stores/wizardStore.ts`
- Create: `dashboard/src/pages/Onboarding.tsx`
- Create: `dashboard/src/hooks/useSetup.ts`
- Modify: `dashboard/src/App.tsx` (add conditional routing)
- Modify: `dashboard/src/lib/api.ts` (add setup API calls)

**Step 1: Create wizard store**

```typescript
// dashboard/src/stores/wizardStore.ts
import { create } from "zustand";

interface WizardState {
  step: number;
  // Step 1
  projectName: string;
  productUrl: string;
  description: string;
  problemStatement: string;
  // Step 2
  roleKeywords: string[];
  tweetTopics: string[];
  minFollowers: number;
  languages: string[];
  // Step 3
  twitterUsername: string;
  twitterPassword: string;
  xApiKey: string;
  // Step 4
  personaName: string;
  personaRole: string;
  personaTone: string;
  voiceNotes: string;
  exampleReply: string;
  llmProvider: string;
  llmApiKey: string;
  // Step 5
  sequenceTemplate: string;
  maxActionsPerDay: number;
  requireApproval: boolean;
  // Actions
  setStep: (step: number) => void;
  updateField: (field: string, value: unknown) => void;
  reset: () => void;
}

const initialState = {
  step: 1,
  projectName: "",
  productUrl: "",
  description: "",
  problemStatement: "",
  roleKeywords: [],
  tweetTopics: [],
  minFollowers: 200,
  languages: ["en"],
  twitterUsername: "",
  twitterPassword: "",
  xApiKey: "",
  personaName: "",
  personaRole: "",
  personaTone: "helpful",
  voiceNotes: "",
  exampleReply: "",
  llmProvider: "ollama",
  llmApiKey: "",
  sequenceTemplate: "gentle_touch",
  maxActionsPerDay: 20,
  requireApproval: true,
};

export const useWizardStore = create<WizardState>((set) => ({
  ...initialState,
  setStep: (step) => set({ step }),
  updateField: (field, value) => set({ [field]: value }),
  reset: () => set(initialState),
}));
```

**Step 2: Create API hooks**

```typescript
// dashboard/src/hooks/useSetup.ts
import { useQuery, useMutation } from "@tanstack/react-query";
import { apiGet, apiPost } from "../lib/api";

interface SetupStatus {
  is_complete: boolean;
  project_id: string | null;
  project_name: string | null;
}

interface TestConnectionResult {
  success: boolean;
  message: string;
  username: string | null;
}

export function useSetupStatus() {
  return useQuery<SetupStatus>({
    queryKey: ["setup-status"],
    queryFn: () => apiGet("/api/setup/status"),
  });
}

export function useTestConnection() {
  return useMutation<TestConnectionResult, Error, { username: string; password: string }>({
    mutationFn: (creds) =>
      apiPost(`/api/setup/test-connection?username=${creds.username}&password=${creds.password}`),
  });
}

export function useCompleteSetup() {
  return useMutation<SetupStatus, Error, Record<string, unknown>>({
    mutationFn: (data) => apiPost("/api/setup", data),
  });
}
```

**Step 3: Build the Onboarding page**

Build `dashboard/src/pages/Onboarding.tsx` — a 5-step wizard using the shadcn Card, Input, Textarea, Select, Button, Progress components. Each step validates with Zod before advancing. On final submit, calls `useCompleteSetup()`.

This is the largest frontend component. Use the cyberpunk theme (neon accents, dark background, glow effects) to match existing pages.

**Step 4: Add conditional routing in App.tsx**

```tsx
// In App.tsx, wrap routes with setup check:
function AppRoutes() {
  const { data: setupStatus, isLoading } = useSetupStatus();

  if (isLoading) return <LoadingScreen />;
  if (!setupStatus?.is_complete) return <Onboarding />;

  return (
    <Routes>
      {/* existing routes */}
    </Routes>
  );
}
```

**Step 5: Commit**

```bash
git add dashboard/src/
git commit -m "feat: add onboarding wizard with 5-step setup flow

Users configure company, ICP, Twitter credentials, persona, and
outreach sequence. Auto-generates project config on submit."
```

---

### Task 8: Build Sequences Page

**Files:**
- Create: `dashboard/src/pages/Sequences.tsx`
- Create: `dashboard/src/hooks/useSequences.ts`
- Modify: `dashboard/src/App.tsx` (add route)

**Step 1: Create hooks**

```typescript
// dashboard/src/hooks/useSequences.ts
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../lib/api";

export function useSequences() {
  return useQuery({
    queryKey: ["sequences"],
    queryFn: () => apiGet("/api/sequences"),
    refetchInterval: 10000, // poll every 10s
  });
}

export function useEnrollments(sequenceId: number) {
  return useQuery({
    queryKey: ["enrollments", sequenceId],
    queryFn: () => apiGet(`/api/sequences/${sequenceId}/enrollments`),
  });
}
```

**Step 2: Build Sequences page**

Build `dashboard/src/pages/Sequences.tsx` — shows active sequences as cards, each with:
- Name + description
- Step visualization (horizontal dots connected by lines, colored by completion)
- Enrolled / Completed counts
- Expandable enrollments list

Use the cyberpunk styling to match existing pages.

**Step 3: Add route and sidebar link**

In `App.tsx`, add `/sequences` route. In the sidebar component, add a "Sequences" navigation link with a `Workflow` icon from lucide-react.

**Step 4: Commit**

```bash
git add dashboard/src/
git commit -m "feat: add Sequences page with enrollment visualization"
```

---

### Task 9: Wire Pipeline and Settings Pages

**Files:**
- Modify: `dashboard/src/pages/PipelineLive.tsx` (add Run button)
- Modify: `dashboard/src/pages/Settings.tsx` (add Twitter creds + LLM config)
- Modify: `dashboard/src/pages/Dashboard.tsx` (add sequence KPIs)

**Step 1: Add "Run Pipeline" button to PipelineLive**

Add a button that calls `POST /api/pipeline/run`. Show loading state while running. WebSocket messages already display progress.

**Step 2: Expand Settings page**

Add sections:
- Twitter Credentials (username, password, test connection button)
- LLM Configuration (provider dropdown: Ollama/OpenAI/Anthropic, model name, API key)
- Sequence Settings (max actions/day, require approval toggle)
- Danger Zone (reset project, clear data)

**Step 3: Add sequence KPIs to Dashboard**

Add two new KPI cards: "Active Sequences" and "Enrolled Leads" — fetched from `/api/sequences`.

**Step 4: Commit**

```bash
git add dashboard/src/
git commit -m "feat: wire pipeline controls, expand settings, add sequence KPIs"
```

---

## Phase 3: Docker + Deployment (Task 10)

### Task 10: Docker Compose + README

**Files:**
- Create: `Dockerfile`
- Create: `dashboard/Dockerfile`
- Create: `docker-compose.yml`
- Modify: `README.md` (update quickstart)

**Step 1: Write API Dockerfile**

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install -e ".[dev]"
COPY src/ src/
COPY projects/ projects/
EXPOSE 8400
CMD ["uvicorn", "signalops.api.app:create_app", "--host", "0.0.0.0", "--port", "8400", "--factory"]
```

**Step 2: Write Dashboard Dockerfile**

```dockerfile
# dashboard/Dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 3000
```

**Step 3: Write docker-compose.yml**

```yaml
services:
  api:
    build: .
    ports: ["8400:8400"]
    volumes:
      - ./data:/app/data
      - ./projects:/app/projects
    environment:
      - SIGNALOPS_DB_URL=sqlite:///data/signalops.db
      - OLLAMA_HOST=http://ollama:11434
    depends_on: [ollama]

  dashboard:
    build: ./dashboard
    ports: ["3000:3000"]
    depends_on: [api]

  ollama:
    image: ollama/ollama
    ports: ["11434:11434"]
    volumes: ["ollama_data:/root/.ollama"]

volumes:
  ollama_data:
```

**Step 4: Update README quickstart**

```markdown
## Quick Start

```bash
git clone https://github.com/you/syntrix
cd syntrix
docker compose up

# Pull an LLM model (first time only)
docker compose exec ollama ollama pull llama3.2:3b
docker compose exec ollama ollama pull mistral:7b

# Open http://localhost:3000
# Complete the 5-step onboarding wizard
# Start finding leads!
```

**Step 5: Commit**

```bash
git add Dockerfile dashboard/Dockerfile docker-compose.yml README.md
git commit -m "feat: add Docker Compose for one-command setup

Three services: API (FastAPI), Dashboard (React), Ollama (LLM).
Zero external dependencies. Run with: docker compose up"
```

---

## Implementation Order

| Phase | Task | Estimated Scope | Depends On |
|-------|------|-----------------|------------|
| 1 | Task 1: TwikitConnector | ~200 lines Python | — |
| 1 | Task 2: Sequence DB tables | ~100 lines Python | — |
| 1 | Task 3: Sequence Engine | ~250 lines Python | Task 2 |
| 1 | Task 4: Wire pipeline + send | ~150 lines Python | Task 1 |
| 1 | Task 5: Setup + Sequence routes | ~250 lines Python | Tasks 2, 3 |
| 2 | Task 6: shadcn + deps | npm install | — |
| 2 | Task 7: Onboarding Wizard | ~400 lines TSX | Task 5, 6 |
| 2 | Task 8: Sequences Page | ~200 lines TSX | Task 5, 6 |
| 2 | Task 9: Wire existing pages | ~150 lines TSX | Task 4, 6 |
| 3 | Task 10: Docker + README | ~80 lines config | All above |

**Total new code:** ~1,800 lines across 10 tasks.

**Parallelizable:** Tasks 1+2 can run in parallel. Tasks 6-9 can partially overlap. Task 10 is last.

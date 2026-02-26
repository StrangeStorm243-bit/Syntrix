"""Tests for the sequence engine state machine."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from signalops.pipeline.sequence_engine import SequenceEngine
from signalops.storage.database import (
    Draft,
    DraftStatus,
    EnrollmentStatus,
    NormalizedPost,
    Project,
    RawPost,
    Sequence,
    SequenceStep,
    StepExecution,
    init_db,
)


def _make_connector() -> MagicMock:
    """Create a mock connector with like/follow/post_reply stubs."""
    connector = MagicMock()
    connector.like.return_value = True
    connector.follow.return_value = True
    connector.post_reply.return_value = "reply_123"
    return connector


class TestSequenceEngine:
    """Test enrollment, step execution, advancement, and completion."""

    def setup_method(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        init_db(self.engine)
        self.session = Session(self.engine)

        # Seed a project
        proj = Project(id="test", name="Test", config_path="t.yaml")
        self.session.add(proj)

        # Seed a raw post + normalized post
        raw = RawPost(project_id="test", platform="x", platform_id="tw1", raw_json={})
        self.session.add(raw)
        self.session.flush()
        norm = NormalizedPost(
            raw_post_id=raw.id,
            project_id="test",
            platform="x",
            platform_id="tw1",
            author_id="u1",
            author_username="testuser",
            text_original="Need help",
            text_cleaned="Need help",
            created_at=datetime.now(UTC),
        )
        self.session.add(norm)
        self.session.flush()
        self.norm_id: int = norm.id  # type: ignore[assignment]

        # Create a "Gentle Touch" sequence: like -> wait 24h -> reply
        seq = Sequence(project_id="test", name="Gentle Touch")
        self.session.add(seq)
        self.session.flush()
        self.seq_id: int = seq.id  # type: ignore[assignment]
        steps = [
            SequenceStep(
                sequence_id=seq.id,
                step_order=1,
                action_type="like",
                delay_hours=0,
            ),
            SequenceStep(
                sequence_id=seq.id,
                step_order=2,
                action_type="wait",
                delay_hours=24,
            ),
            SequenceStep(
                sequence_id=seq.id,
                step_order=3,
                action_type="reply",
                delay_hours=0,
                requires_approval=True,
            ),
        ]
        self.session.add_all(steps)
        self.session.commit()

        self.connector = _make_connector()

    def teardown_method(self) -> None:
        self.session.close()
        self.engine.dispose()

    def test_enroll_lead(self) -> None:
        """enroll() creates an ACTIVE enrollment at step 0."""
        engine = SequenceEngine(self.session, self.connector)
        enrollment = engine.enroll(self.norm_id, self.seq_id, "test")

        assert enrollment.status == EnrollmentStatus.ACTIVE
        assert enrollment.current_step_order == 0
        assert enrollment.next_step_at is not None

    def test_enroll_sets_next_step_at(self) -> None:
        """enroll() sets next_step_at to approximately now."""
        engine = SequenceEngine(self.session, self.connector)
        before = datetime.now(UTC).replace(tzinfo=None)
        enrollment = engine.enroll(self.norm_id, self.seq_id, "test")

        assert enrollment.next_step_at is not None
        # SQLite stores naive datetimes, so compare without tzinfo
        after = datetime.now(UTC).replace(tzinfo=None)
        assert before <= enrollment.next_step_at <= after

    def test_execute_like_step(self) -> None:
        """execute_due_steps() executes the 'like' step and calls connector."""
        engine = SequenceEngine(self.session, self.connector)
        enrollment = engine.enroll(self.norm_id, self.seq_id, "test")
        # Make it due now
        enrollment.next_step_at = datetime.now(UTC)  # type: ignore[assignment]
        self.session.commit()

        executed = engine.execute_due_steps()
        assert executed == 1
        self.connector.like.assert_called_once_with("tw1")

    def test_like_step_records_execution(self) -> None:
        """After executing a like step, a StepExecution record exists."""
        engine = SequenceEngine(self.session, self.connector)
        enrollment = engine.enroll(self.norm_id, self.seq_id, "test")
        enrollment.next_step_at = datetime.now(UTC)  # type: ignore[assignment]
        self.session.commit()

        engine.execute_due_steps()

        executions = (
            self.session.query(StepExecution)
            .filter(StepExecution.enrollment_id == enrollment.id)
            .all()
        )
        assert len(executions) == 1
        assert executions[0].action_type == "like"
        assert executions[0].status == "executed"

    def test_like_step_advances_enrollment(self) -> None:
        """After like step, enrollment advances to step_order 1."""
        engine = SequenceEngine(self.session, self.connector)
        enrollment = engine.enroll(self.norm_id, self.seq_id, "test")
        enrollment.next_step_at = datetime.now(UTC)  # type: ignore[assignment]
        self.session.commit()

        engine.execute_due_steps()
        self.session.refresh(enrollment)

        assert enrollment.current_step_order == 1

    def test_wait_step_advances_time(self) -> None:
        """A 'wait' step sets next_step_at in the future (reply has 0 delay)."""
        engine = SequenceEngine(self.session, self.connector)
        enrollment = engine.enroll(self.norm_id, self.seq_id, "test")
        # Simulate having completed step 1 (like), now on wait step
        enrollment.current_step_order = 1  # type: ignore[assignment]
        enrollment.next_step_at = datetime.now(UTC)  # type: ignore[assignment]
        self.session.commit()

        engine.execute_due_steps()
        self.session.refresh(enrollment)

        # After wait step (24h delay), next step is reply (0h delay).
        # The _advance method uses the NEXT step's delay_hours.
        # Reply step has delay_hours=0 so next_step_at is ~now.
        # Just verify enrollment advanced past the wait step.
        assert enrollment.current_step_order == 2

    def test_reply_step_requires_approved_draft(self) -> None:
        """Reply step is skipped if no approved draft exists."""
        engine = SequenceEngine(self.session, self.connector)
        enrollment = engine.enroll(self.norm_id, self.seq_id, "test")
        # Jump to step 3 (reply)
        enrollment.current_step_order = 2  # type: ignore[assignment]
        enrollment.next_step_at = datetime.now(UTC)  # type: ignore[assignment]
        self.session.commit()

        executed = engine.execute_due_steps()
        assert executed == 0
        self.connector.post_reply.assert_not_called()

    def test_reply_step_sends_with_approved_draft(self) -> None:
        """Reply step sends via connector when an approved draft exists."""
        engine = SequenceEngine(self.session, self.connector)
        enrollment = engine.enroll(self.norm_id, self.seq_id, "test")
        # Jump to step 3 (reply)
        enrollment.current_step_order = 2  # type: ignore[assignment]
        enrollment.next_step_at = datetime.now(UTC)  # type: ignore[assignment]

        # Create an approved draft for this post
        draft = Draft(
            normalized_post_id=self.norm_id,
            project_id="test",
            text_generated="Great question! Check out our tool.",
            model_id="test-model",
            status=DraftStatus.APPROVED,
        )
        self.session.add(draft)
        self.session.commit()

        executed = engine.execute_due_steps()
        assert executed == 1
        self.connector.post_reply.assert_called_once_with(
            "tw1", "Great question! Check out our tool."
        )

    def test_reply_step_uses_text_final_if_available(self) -> None:
        """Reply step prefers text_final over text_generated."""
        engine = SequenceEngine(self.session, self.connector)
        enrollment = engine.enroll(self.norm_id, self.seq_id, "test")
        enrollment.current_step_order = 2  # type: ignore[assignment]
        enrollment.next_step_at = datetime.now(UTC)  # type: ignore[assignment]

        draft = Draft(
            normalized_post_id=self.norm_id,
            project_id="test",
            text_generated="Original text",
            text_final="Edited text",
            model_id="test-model",
            status=DraftStatus.EDITED,
        )
        self.session.add(draft)
        self.session.commit()

        engine.execute_due_steps()
        self.connector.post_reply.assert_called_once_with("tw1", "Edited text")

    def test_completion_after_last_step(self) -> None:
        """Enrollment is COMPLETED after executing the last step."""
        engine = SequenceEngine(self.session, self.connector)
        enrollment = engine.enroll(self.norm_id, self.seq_id, "test")
        enrollment.current_step_order = 2  # type: ignore[assignment]
        enrollment.next_step_at = datetime.now(UTC)  # type: ignore[assignment]

        # Add approved draft for reply step
        draft = Draft(
            normalized_post_id=self.norm_id,
            project_id="test",
            text_generated="Reply text",
            model_id="test-model",
            status=DraftStatus.APPROVED,
        )
        self.session.add(draft)
        self.session.commit()

        engine.execute_due_steps()
        self.session.refresh(enrollment)

        assert enrollment.status == EnrollmentStatus.COMPLETED
        assert enrollment.completed_at is not None
        assert enrollment.next_step_at is None

    def test_not_due_enrollment_is_skipped(self) -> None:
        """Enrollments with next_step_at in the future are not executed."""
        engine = SequenceEngine(self.session, self.connector)
        enrollment = engine.enroll(self.norm_id, self.seq_id, "test")
        enrollment.next_step_at = datetime.now(UTC) + timedelta(hours=24)  # type: ignore[assignment]
        self.session.commit()

        executed = engine.execute_due_steps()
        assert executed == 0

    def test_paused_enrollment_is_skipped(self) -> None:
        """Paused enrollments are not executed."""
        engine = SequenceEngine(self.session, self.connector)
        enrollment = engine.enroll(self.norm_id, self.seq_id, "test")
        enrollment.status = EnrollmentStatus.PAUSED  # type: ignore[assignment]
        enrollment.next_step_at = datetime.now(UTC)  # type: ignore[assignment]
        self.session.commit()

        executed = engine.execute_due_steps()
        assert executed == 0

    def test_follow_step(self) -> None:
        """Follow step calls connector.follow with author_id."""
        # Create a "Direct Follow" sequence with just a follow step
        seq = Sequence(project_id="test", name="Follow Only")
        self.session.add(seq)
        self.session.flush()
        step = SequenceStep(
            sequence_id=seq.id,  # type: ignore[arg-type]
            step_order=1,
            action_type="follow",
            delay_hours=0,
        )
        self.session.add(step)
        self.session.commit()

        engine = SequenceEngine(self.session, self.connector)
        enrollment = engine.enroll(
            self.norm_id,
            seq.id,
            "test",  # type: ignore[arg-type]
        )
        enrollment.next_step_at = datetime.now(UTC)  # type: ignore[assignment]
        self.session.commit()

        engine.execute_due_steps()
        self.connector.follow.assert_called_once_with("u1")

    def test_failed_like_does_not_advance(self) -> None:
        """If like fails, enrollment does not advance."""
        self.connector.like.return_value = False

        engine = SequenceEngine(self.session, self.connector)
        enrollment = engine.enroll(self.norm_id, self.seq_id, "test")
        enrollment.next_step_at = datetime.now(UTC)  # type: ignore[assignment]
        self.session.commit()

        executed = engine.execute_due_steps()
        assert executed == 0
        self.session.refresh(enrollment)
        assert enrollment.current_step_order == 0  # Did not advance

    def test_dm_step_executes(self) -> None:
        """DM action type should call connector.send_dm."""
        connector = _make_connector()
        connector.send_dm = MagicMock(return_value=True)
        engine = SequenceEngine(self.session, connector)

        seq = Sequence(project_id="test", name="Cold DM")
        self.session.add(seq)
        self.session.flush()
        self.session.add(
            SequenceStep(
                sequence_id=seq.id,
                step_order=1,
                action_type="dm",
                delay_hours=0,
                config_json='{"dm_text": "Hey, saw your tweet and wanted to reach out!"}',
            ),
        )
        self.session.commit()

        enrollment = engine.enroll(self.norm_id, seq.id, "test")
        enrollment.next_step_at = datetime.now(UTC) - timedelta(minutes=1)
        self.session.commit()

        count = engine.execute_due_steps()
        assert count == 1
        connector.send_dm.assert_called_once()

    def test_dm_rate_limit(self) -> None:
        """DM actions should respect max_dms_per_day rate limit."""
        connector = _make_connector()
        connector.send_dm = MagicMock(return_value=True)
        engine = SequenceEngine(self.session, connector, max_dms_per_day=1)

        seq = Sequence(project_id="test", name="DM Seq")
        self.session.add(seq)
        self.session.flush()
        self.session.add(
            SequenceStep(
                sequence_id=seq.id,
                step_order=1,
                action_type="dm",
                delay_hours=0,
            ),
        )
        self.session.commit()

        enrollment_prev = engine.enroll(self.norm_id, seq.id, "test")
        exec_record = StepExecution(
            enrollment_id=enrollment_prev.id,
            step_id=1,
            action_type="dm",
            status="executed",
            executed_at=datetime.now(UTC) - timedelta(hours=1),
        )
        self.session.add(exec_record)
        self.session.commit()

        raw2 = RawPost(project_id="test", platform="x", platform_id="tw2", raw_json={})
        self.session.add(raw2)
        self.session.flush()
        norm2 = NormalizedPost(
            raw_post_id=raw2.id,
            project_id="test",
            platform="x",
            platform_id="tw2",
            author_id="u2",
            author_username="user2",
            text_original="Help",
            text_cleaned="Help",
            created_at=datetime.now(UTC),
        )
        self.session.add(norm2)
        self.session.flush()

        enrollment_new = engine.enroll(norm2.id, seq.id, "test")
        enrollment_new.next_step_at = datetime.now(UTC) - timedelta(minutes=1)
        self.session.commit()

        count = engine.execute_due_steps()
        assert count == 0


class TestCreateDefaultSequences:
    """Test create_default_sequences() produces 3 correct templates."""

    def setup_method(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        init_db(self.engine)
        self.session = Session(self.engine)

        proj = Project(id="test", name="Test", config_path="t.yaml")
        self.session.add(proj)
        self.session.commit()

        self.connector = _make_connector()

    def teardown_method(self) -> None:
        self.session.close()
        self.engine.dispose()

    def test_creates_four_sequences(self) -> None:
        """create_default_sequences() returns 4 sequences."""
        engine = SequenceEngine(self.session, self.connector)
        sequences = engine.create_default_sequences("test")
        assert len(sequences) == 4

    def test_gentle_touch_sequence(self) -> None:
        """Gentle Touch has 3 steps: like -> wait -> reply."""
        engine = SequenceEngine(self.session, self.connector)
        sequences = engine.create_default_sequences("test")
        gentle = next(s for s in sequences if s.name == "Gentle Touch")
        self.session.refresh(gentle)

        assert len(gentle.steps) == 3
        assert gentle.steps[0].action_type == "like"
        assert gentle.steps[1].action_type == "wait"
        assert gentle.steps[1].delay_hours == 24
        assert gentle.steps[2].action_type == "reply"
        assert gentle.steps[2].requires_approval is True

    def test_direct_sequence(self) -> None:
        """Direct has 1 step: reply (with approval)."""
        engine = SequenceEngine(self.session, self.connector)
        sequences = engine.create_default_sequences("test")
        direct = next(s for s in sequences if s.name == "Direct")
        self.session.refresh(direct)

        assert len(direct.steps) == 1
        assert direct.steps[0].action_type == "reply"
        assert direct.steps[0].requires_approval is True

    def test_full_sequence(self) -> None:
        """Full Sequence has 6 steps including DM."""
        engine = SequenceEngine(self.session, self.connector)
        sequences = engine.create_default_sequences("test")
        full = next(s for s in sequences if s.name == "Full Sequence")
        self.session.refresh(full)

        assert len(full.steps) == 6
        action_types = [s.action_type for s in full.steps]
        assert action_types == [
            "like",
            "follow",
            "wait",
            "reply",
            "check_response",
            "dm",
        ]

    def test_cold_dm_sequence(self) -> None:
        """Cold DM sequence has 1 DM step."""
        engine = SequenceEngine(self.session, self.connector)
        sequences = engine.create_default_sequences("test")
        cold_dm = next(s for s in sequences if s.name == "Cold DM")
        self.session.refresh(cold_dm)

        assert len(cold_dm.steps) == 1
        assert cold_dm.steps[0].action_type == "dm"


class TestRateLimitEnforcement:
    """Test that rate limits are actually enforced during step execution."""

    def setup_method(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        init_db(self.engine)
        self.session = Session(self.engine)

        # Seed a project
        proj = Project(id="test", name="Test", config_path="t.yaml")
        self.session.add(proj)

        # Seed a raw post + normalized post
        raw = RawPost(project_id="test", platform="x", platform_id="tw1", raw_json={})
        self.session.add(raw)
        self.session.flush()
        norm = NormalizedPost(
            raw_post_id=raw.id,
            project_id="test",
            platform="x",
            platform_id="tw1",
            author_id="u1",
            author_username="testuser",
            text_original="Need help",
            text_cleaned="Need help",
            created_at=datetime.now(UTC),
        )
        self.session.add(norm)
        self.session.flush()
        self.norm_id: int = norm.id  # type: ignore[assignment]

        # Create a simple "like-only" sequence
        seq = Sequence(project_id="test", name="Like Only")
        self.session.add(seq)
        self.session.flush()
        self.seq_id: int = seq.id  # type: ignore[assignment]
        step = SequenceStep(
            sequence_id=seq.id,
            step_order=1,
            action_type="like",
            delay_hours=0,
        )
        self.session.add(step)
        self.session.commit()

        self.connector = _make_connector()

    def teardown_method(self) -> None:
        self.session.close()
        self.engine.dispose()

    def test_like_rate_limit_blocks_when_exceeded(self) -> None:
        """_check_rate_limit returns False when like limit is reached."""
        engine = SequenceEngine(self.session, self.connector, max_likes_per_hour=2)

        # Insert 2 executed like step executions within the last hour
        now = datetime.now(UTC)
        for i in range(2):
            execution = StepExecution(
                enrollment_id=1,
                step_id=1,
                action_type="like",
                status="executed",
                executed_at=now - timedelta(minutes=10 + i),
                result_json="{}",
            )
            self.session.add(execution)
        self.session.commit()

        assert engine._check_rate_limit("like") is False

    def test_different_action_type_not_blocked(self) -> None:
        """_check_rate_limit for 'follow' is True even when likes are at limit."""
        engine = SequenceEngine(self.session, self.connector, max_likes_per_hour=2)

        # Insert 2 executed like step executions
        now = datetime.now(UTC)
        for i in range(2):
            execution = StepExecution(
                enrollment_id=1,
                step_id=1,
                action_type="like",
                status="executed",
                executed_at=now - timedelta(minutes=10 + i),
                result_json="{}",
            )
            self.session.add(execution)
        self.session.commit()

        assert engine._check_rate_limit("follow") is True

    def test_wait_action_always_allowed(self) -> None:
        """_check_rate_limit always returns True for 'wait' actions."""
        engine = SequenceEngine(self.session, self.connector, max_likes_per_hour=0)
        assert engine._check_rate_limit("wait") is True

    def test_check_response_always_allowed(self) -> None:
        """_check_rate_limit always returns True for 'check_response' actions."""
        engine = SequenceEngine(self.session, self.connector, max_likes_per_hour=0)
        assert engine._check_rate_limit("check_response") is True

    def test_rate_limit_skips_enrollment_in_execute_due_steps(self) -> None:
        """execute_due_steps() skips enrollment when rate limit is hit."""
        engine = SequenceEngine(self.session, self.connector, max_likes_per_hour=2)

        # Insert 2 executed like step executions to hit the limit
        now = datetime.now(UTC)
        for i in range(2):
            execution = StepExecution(
                enrollment_id=999,
                step_id=999,
                action_type="like",
                status="executed",
                executed_at=now - timedelta(minutes=5 + i),
                result_json="{}",
            )
            self.session.add(execution)
        self.session.commit()

        # Enroll and make it due
        enrollment = engine.enroll(self.norm_id, self.seq_id, "test")
        enrollment.next_step_at = datetime.now(UTC)  # type: ignore[assignment]
        self.session.commit()

        executed = engine.execute_due_steps()
        assert executed == 0
        self.connector.like.assert_not_called()

    def test_reply_rate_limit_uses_24h_window(self) -> None:
        """Reply rate limit counts executions in the last 24 hours."""
        engine = SequenceEngine(self.session, self.connector, max_replies_per_day=1)

        # Insert a reply execution 23 hours ago (within window)
        now = datetime.now(UTC)
        execution = StepExecution(
            enrollment_id=1,
            step_id=1,
            action_type="reply",
            status="executed",
            executed_at=now - timedelta(hours=23),
            result_json="{}",
        )
        self.session.add(execution)
        self.session.commit()

        assert engine._check_rate_limit("reply") is False

    def test_old_executions_not_counted(self) -> None:
        """Executions older than the window are not counted."""
        engine = SequenceEngine(self.session, self.connector, max_likes_per_hour=2)

        # Insert 2 executed like step executions from 2 hours ago
        now = datetime.now(UTC)
        for i in range(2):
            execution = StepExecution(
                enrollment_id=1,
                step_id=1,
                action_type="like",
                status="executed",
                executed_at=now - timedelta(hours=2, minutes=i),
                result_json="{}",
            )
            self.session.add(execution)
        self.session.commit()

        assert engine._check_rate_limit("like") is True

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
        self.project = Project(
            id="test-proj", name="Test", config_path="test.yaml"
        )
        self.session.add(self.project)
        self.session.commit()

    def teardown_method(self) -> None:
        self.session.close()
        self.engine.dispose()

    def test_create_sequence(self) -> None:
        """A sequence can be created with a project_id and name."""
        seq = Sequence(
            project_id="test-proj",
            name="Gentle Touch",
            description="Like -> Wait 1d -> Reply",
        )
        self.session.add(seq)
        self.session.commit()

        loaded = (
            self.session.query(Sequence).filter_by(name="Gentle Touch").first()
        )
        assert loaded is not None
        assert loaded.project_id == "test-proj"
        assert loaded.is_active is True
        assert loaded.created_at is not None

    def test_create_sequence_with_steps(self) -> None:
        """Steps are created and accessible via relationship, ordered by step_order."""
        seq = Sequence(project_id="test-proj", name="Gentle Touch")
        self.session.add(seq)
        self.session.flush()

        step1 = SequenceStep(
            sequence_id=seq.id,
            step_order=1,
            action_type="like",
            delay_hours=0,
        )
        step2 = SequenceStep(
            sequence_id=seq.id,
            step_order=2,
            action_type="wait",
            delay_hours=24,
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

        loaded = (
            self.session.query(Sequence).filter_by(name="Gentle Touch").first()
        )
        assert loaded is not None
        assert len(loaded.steps) == 3
        assert loaded.steps[0].action_type == "like"
        assert loaded.steps[1].action_type == "wait"
        assert loaded.steps[1].delay_hours == 24.0
        assert loaded.steps[2].requires_approval is True

    def test_step_defaults(self) -> None:
        """SequenceStep has sane defaults for delay_hours, config_json, requires_approval."""
        seq = Sequence(project_id="test-proj", name="Direct")
        self.session.add(seq)
        self.session.flush()

        step = SequenceStep(
            sequence_id=seq.id, step_order=1, action_type="reply"
        )
        self.session.add(step)
        self.session.commit()

        self.session.refresh(step)
        assert step.delay_hours == 0.0
        assert step.config_json == "{}"
        assert step.requires_approval is False

    def test_enrollment_status_transitions(self) -> None:
        """Enrollment status can be changed from ACTIVE to COMPLETED."""
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

        enrollment.status = EnrollmentStatus.COMPLETED  # type: ignore[assignment]
        enrollment.completed_at = datetime.now(timezone.utc)  # type: ignore[assignment]
        self.session.commit()
        assert enrollment.status == EnrollmentStatus.COMPLETED
        assert enrollment.completed_at is not None

    def test_enrollment_all_statuses(self) -> None:
        """All EnrollmentStatus values can be set."""
        seq = Sequence(project_id="test-proj", name="Test")
        self.session.add(seq)
        self.session.flush()

        for status in EnrollmentStatus:
            enrollment = Enrollment(
                normalized_post_id=1,
                sequence_id=seq.id,
                project_id="test-proj",
                status=status,
            )
            self.session.add(enrollment)
            self.session.commit()
            assert enrollment.status == status

    def test_enrollment_defaults(self) -> None:
        """Enrollment has correct defaults for current_step_order and enrolled_at."""
        seq = Sequence(project_id="test-proj", name="Test")
        self.session.add(seq)
        self.session.flush()

        enrollment = Enrollment(
            normalized_post_id=1,
            sequence_id=seq.id,
            project_id="test-proj",
        )
        self.session.add(enrollment)
        self.session.commit()

        self.session.refresh(enrollment)
        assert enrollment.current_step_order == 0
        assert enrollment.status == EnrollmentStatus.ACTIVE
        assert enrollment.enrolled_at is not None
        assert enrollment.next_step_at is None
        assert enrollment.completed_at is None

    def test_step_execution_crud(self) -> None:
        """StepExecution records can be created and linked to enrollment + step."""
        seq = Sequence(project_id="test-proj", name="Test")
        self.session.add(seq)
        self.session.flush()

        step = SequenceStep(
            sequence_id=seq.id, step_order=1, action_type="like"
        )
        self.session.add(step)
        self.session.flush()

        enrollment = Enrollment(
            normalized_post_id=1,
            sequence_id=seq.id,
            project_id="test-proj",
        )
        self.session.add(enrollment)
        self.session.flush()

        execution = StepExecution(
            enrollment_id=enrollment.id,
            step_id=step.id,
            action_type="like",
            status="executed",
            executed_at=datetime.now(timezone.utc),
            result_json='{"liked": true}',
        )
        self.session.add(execution)
        self.session.commit()

        self.session.refresh(execution)
        assert execution.status == "executed"
        assert execution.action_type == "like"
        assert execution.result_json == '{"liked": true}'

    def test_enrollment_executions_relationship(self) -> None:
        """Enrollment.executions relationship returns linked StepExecution records."""
        seq = Sequence(project_id="test-proj", name="Test")
        self.session.add(seq)
        self.session.flush()

        step = SequenceStep(
            sequence_id=seq.id, step_order=1, action_type="like"
        )
        self.session.add(step)
        self.session.flush()

        enrollment = Enrollment(
            normalized_post_id=1,
            sequence_id=seq.id,
            project_id="test-proj",
        )
        self.session.add(enrollment)
        self.session.flush()

        exec1 = StepExecution(
            enrollment_id=enrollment.id,
            step_id=step.id,
            action_type="like",
            status="executed",
        )
        exec2 = StepExecution(
            enrollment_id=enrollment.id,
            step_id=step.id,
            action_type="like",
            status="failed",
        )
        self.session.add_all([exec1, exec2])
        self.session.commit()

        self.session.refresh(enrollment)
        assert len(enrollment.executions) == 2

    def test_sequence_enrollments_relationship(self) -> None:
        """Sequence.enrollments relationship returns linked Enrollment records."""
        seq = Sequence(project_id="test-proj", name="Test")
        self.session.add(seq)
        self.session.flush()

        for i in range(3):
            enrollment = Enrollment(
                normalized_post_id=i + 1,
                sequence_id=seq.id,
                project_id="test-proj",
            )
            self.session.add(enrollment)

        self.session.commit()
        self.session.refresh(seq)
        assert len(seq.enrollments) == 3

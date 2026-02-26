"""Sequence engine — state machine for multi-step outreach."""

from __future__ import annotations

import json
import logging
import random
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

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
DEFAULT_MAX_DMS_PER_DAY = 20
JITTER_FACTOR = 0.3  # +/- 30% on delays


class SequenceEngine:
    """Executes outreach sequences as a state machine.

    Polls the enrollments table for due steps, executes actions
    via the connector, and advances enrollment state.
    """

    def __init__(
        self,
        session: Session,
        connector: Any,
        max_likes_per_hour: int = DEFAULT_MAX_LIKES_PER_HOUR,
        max_follows_per_hour: int = DEFAULT_MAX_FOLLOWS_PER_HOUR,
        max_replies_per_day: int = DEFAULT_MAX_REPLIES_PER_DAY,
        max_dms_per_day: int = DEFAULT_MAX_DMS_PER_DAY,
    ) -> None:
        self.session = session
        self.connector = connector
        self.max_likes_per_hour = max_likes_per_hour
        self.max_follows_per_hour = max_follows_per_hour
        self.max_replies_per_day = max_replies_per_day
        self.max_dms_per_day = max_dms_per_day

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
            next_step_at=datetime.now(UTC),
        )
        self.session.add(enrollment)
        self.session.commit()
        logger.info("Enrolled post %d in sequence %d", normalized_post_id, sequence_id)
        return enrollment

    def execute_due_steps(self) -> int:
        """Execute all steps that are due. Returns count of executed steps."""
        now = datetime.now(UTC)
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

            if not self._check_rate_limit(str(step.action_type)):
                continue  # Rate limited, skip for now

            success = self._execute_step(enrollment, step)
            if success:
                executed_count += 1
                self._advance(enrollment, step)

        self.session.commit()
        return executed_count

    def _check_rate_limit(self, action_type: str) -> bool:
        """Check if rate limit allows executing this action type."""
        now = datetime.now(UTC)

        if action_type == "like":
            one_hour_ago = now - timedelta(hours=1)
            count = (
                self.session.query(StepExecution)
                .filter(
                    StepExecution.action_type == "like",
                    StepExecution.status == "executed",
                    StepExecution.executed_at >= one_hour_ago,
                )
                .count()
            )
            if count >= self.max_likes_per_hour:
                logger.warning(
                    "Rate limit: %d/%d likes in last hour",
                    count,
                    self.max_likes_per_hour,
                )
                return False
        elif action_type == "follow":
            one_hour_ago = now - timedelta(hours=1)
            count = (
                self.session.query(StepExecution)
                .filter(
                    StepExecution.action_type == "follow",
                    StepExecution.status == "executed",
                    StepExecution.executed_at >= one_hour_ago,
                )
                .count()
            )
            if count >= self.max_follows_per_hour:
                logger.warning(
                    "Rate limit: %d/%d follows in last hour",
                    count,
                    self.max_follows_per_hour,
                )
                return False
        elif action_type == "reply":
            one_day_ago = now - timedelta(days=1)
            count = (
                self.session.query(StepExecution)
                .filter(
                    StepExecution.action_type == "reply",
                    StepExecution.status == "executed",
                    StepExecution.executed_at >= one_day_ago,
                )
                .count()
            )
            if count >= self.max_replies_per_day:
                logger.warning(
                    "Rate limit: %d/%d replies in last day",
                    count,
                    self.max_replies_per_day,
                )
                return False
        elif action_type == "dm":
            one_day_ago = now - timedelta(days=1)
            count = (
                self.session.query(StepExecution)
                .filter(
                    StepExecution.action_type == "dm",
                    StepExecution.status == "executed",
                    StepExecution.executed_at >= one_day_ago,
                )
                .count()
            )
            if count >= self.max_dms_per_day:
                logger.warning("Rate limit: %d/%d DMs in last day", count, self.max_dms_per_day)
                return False
        return True

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
        post = self.session.get(NormalizedPost, enrollment.normalized_post_id)
        if post is None:
            logger.warning(
                "Post %d not found for enrollment %d",
                enrollment.normalized_post_id,
                enrollment.id,
            )
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
                draft.status = DraftStatus.SENT  # type: ignore[assignment]
                draft.sent_at = datetime.now(UTC)  # type: ignore[assignment]
                draft.sent_post_id = reply_id

        elif step.action_type == "wait":
            success = True
            result = {"waited": True}

        elif step.action_type == "check_response":
            # Placeholder: check if lead responded
            success = True
            result = {"checked": True}

        elif step.action_type == "dm":
            config = json.loads(step.config_json or "{}")  # type: ignore[arg-type]
            dm_text = config.get("dm_text", "")
            if not dm_text:
                draft = self._get_approved_draft(enrollment)
                if draft:
                    dm_text = draft.text_final or draft.text_generated
                else:
                    dm_text = "Hey, I saw your tweet and wanted to connect!"
            success = self.connector.send_dm(post.author_id, dm_text)
            result = {"dm_sent": success, "user_id": post.author_id, "text": dm_text}

        # Record execution
        execution = StepExecution(
            enrollment_id=enrollment.id,
            step_id=step.id,
            action_type=step.action_type,
            status="executed" if success else "failed",
            executed_at=datetime.now(UTC),
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
            delay = float(next_step.delay_hours)
            jitter = delay * JITTER_FACTOR * (2 * random.random() - 1)
            enrollment.next_step_at = datetime.now(UTC) + timedelta(hours=delay + jitter)  # type: ignore[assignment]

    def _complete_enrollment(self, enrollment: Enrollment) -> None:
        """Mark enrollment as completed."""
        enrollment.status = EnrollmentStatus.COMPLETED  # type: ignore[assignment]
        enrollment.completed_at = datetime.now(UTC)  # type: ignore[assignment]
        enrollment.next_step_at = None  # type: ignore[assignment]

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
        sequences: list[Sequence] = []

        # Gentle Touch
        gentle = Sequence(
            project_id=project_id,
            name="Gentle Touch",
            description="Like -> Wait 1d -> Reply",
        )
        self.session.add(gentle)
        self.session.flush()
        self.session.add_all(
            [
                SequenceStep(
                    sequence_id=gentle.id,
                    step_order=1,
                    action_type="like",
                    delay_hours=0,
                ),
                SequenceStep(
                    sequence_id=gentle.id,
                    step_order=2,
                    action_type="wait",
                    delay_hours=24,
                ),
                SequenceStep(
                    sequence_id=gentle.id,
                    step_order=3,
                    action_type="reply",
                    delay_hours=0,
                    requires_approval=True,
                ),
            ]
        )
        sequences.append(gentle)

        # Direct
        direct = Sequence(
            project_id=project_id,
            name="Direct",
            description="Reply immediately",
        )
        self.session.add(direct)
        self.session.flush()
        self.session.add_all(
            [
                SequenceStep(
                    sequence_id=direct.id,
                    step_order=1,
                    action_type="reply",
                    delay_hours=0,
                    requires_approval=True,
                ),
            ]
        )
        sequences.append(direct)

        # Full Sequence
        full = Sequence(
            project_id=project_id,
            name="Full Sequence",
            description="Like -> Follow -> Wait -> Reply -> Follow-up",
        )
        self.session.add(full)
        self.session.flush()
        self.session.add_all(
            [
                SequenceStep(
                    sequence_id=full.id,
                    step_order=1,
                    action_type="like",
                    delay_hours=0,
                ),
                SequenceStep(
                    sequence_id=full.id,
                    step_order=2,
                    action_type="follow",
                    delay_hours=6,
                ),
                SequenceStep(
                    sequence_id=full.id,
                    step_order=3,
                    action_type="wait",
                    delay_hours=24,
                ),
                SequenceStep(
                    sequence_id=full.id,
                    step_order=4,
                    action_type="reply",
                    delay_hours=0,
                    requires_approval=True,
                ),
                SequenceStep(
                    sequence_id=full.id,
                    step_order=5,
                    action_type="check_response",
                    delay_hours=72,
                ),
            ]
        )
        sequences.append(full)

        self.session.commit()
        return sequences

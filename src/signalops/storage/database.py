"""SQLAlchemy models and database session management."""

import enum
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    func,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker


class Base(DeclarativeBase):
    pass


# ── Enums ──


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


class EnrollmentStatus(str, enum.Enum):
    """Status of a lead's enrollment in a sequence."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    EXITED = "exited"


# ── Projects ──


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(64), primary_key=True)  # slug: "spectra"
    name = Column(String(256), nullable=False)
    config_path = Column(String(1024), nullable=False)
    config_hash = Column(String(64))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    is_active = Column(Boolean, default=True)


# ── Raw Posts ──


class RawPost(Base):
    __tablename__ = "raw_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(64), ForeignKey("projects.id"), nullable=False)
    platform = Column(String(32), nullable=False)
    platform_id = Column(String(64), nullable=False)
    collected_at = Column(DateTime, server_default=func.now())
    query_used = Column(Text)
    raw_json = Column(JSON, nullable=False)

    normalized_post = relationship(
        "NormalizedPost",
        back_populates="raw_post",
        uselist=False,
    )

    __table_args__ = (
        UniqueConstraint("platform", "platform_id", "project_id", name="uq_raw_post_platform"),
        Index("ix_raw_post_project_collected", "project_id", "collected_at"),
    )


# ── Normalized Posts ──


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

    raw_post = relationship(
        "RawPost",
        back_populates="normalized_post",
    )
    judgments = relationship(
        "Judgment",
        back_populates="normalized_post",
    )
    scores = relationship(
        "Score",
        back_populates="normalized_post",
    )
    drafts = relationship(
        "Draft",
        back_populates="normalized_post",
    )

    __table_args__ = (
        Index("ix_norm_project_author", "project_id", "author_id"),
        Index("ix_norm_project_created", "project_id", "created_at"),
    )


# ── Judgments ──


class Judgment(Base):
    __tablename__ = "judgments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    normalized_post_id = Column(Integer, ForeignKey("normalized_posts.id"), nullable=False)
    project_id = Column(String(64), ForeignKey("projects.id"), nullable=False)
    label: Column[Any] = Column(SAEnum(JudgmentLabel), nullable=False)
    confidence = Column(Float, nullable=False)
    reasoning = Column(Text)
    model_id = Column(String(128), nullable=False)
    model_version = Column(String(64))
    latency_ms = Column(Float)
    created_at = Column(DateTime, server_default=func.now())

    # Human correction (nullable — only set if human overrides)
    human_label: Column[Any] = Column(SAEnum(JudgmentLabel))
    human_corrected_at = Column(DateTime)
    human_reason = Column(Text)

    # A/B test experiment tracking (v0.3)
    experiment_id = Column(String(64))

    normalized_post = relationship(
        "NormalizedPost",
        back_populates="judgments",
    )

    __table_args__ = (Index("ix_judgment_project_label", "project_id", "label"),)


# ── Scores ──


class Score(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    normalized_post_id = Column(Integer, ForeignKey("normalized_posts.id"), nullable=False)
    project_id = Column(String(64), ForeignKey("projects.id"), nullable=False)
    total_score = Column(Float, nullable=False)
    components = Column(JSON, nullable=False)
    scoring_version = Column(String(64), nullable=False)
    scoring_plugins = Column(JSON)  # List of plugin names + versions used
    created_at = Column(DateTime, server_default=func.now())

    normalized_post = relationship(
        "NormalizedPost",
        back_populates="scores",
    )

    __table_args__ = (Index("ix_score_project_total", "project_id", "total_score"),)


# ── Drafts ──


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
    status: Column[Any] = Column(SAEnum(DraftStatus), default=DraftStatus.PENDING)
    created_at = Column(DateTime, server_default=func.now())
    approved_at = Column(DateTime)
    sent_at = Column(DateTime)
    sent_post_id = Column(String(64))

    normalized_post = relationship(
        "NormalizedPost",
        back_populates="drafts",
    )
    outcomes = relationship(
        "Outcome",
        back_populates="draft",
    )

    __table_args__ = (Index("ix_draft_project_status", "project_id", "status"),)


# ── Outcomes ──


class Outcome(Base):
    __tablename__ = "outcomes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    draft_id = Column(Integer, ForeignKey("drafts.id"), nullable=False)
    project_id = Column(String(64), ForeignKey("projects.id"), nullable=False)
    outcome_type: Column[Any] = Column(SAEnum(OutcomeType), nullable=False)
    details = Column(JSON)
    observed_at = Column(DateTime, server_default=func.now())

    draft = relationship(
        "Draft",
        back_populates="outcomes",
    )


# ── Audit Logs ──


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

    __table_args__ = (
        Index("ix_audit_project_action", "project_id", "action"),
        Index("ix_audit_timestamp", "timestamp"),
    )


# ── Model Registry (v0.3 T2) ──


class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(String(256), nullable=False, unique=True)
    provider = Column(String(32), nullable=False)
    model_type = Column(String(32), nullable=False)  # "judge", "drafter"
    display_name = Column(String(256))
    base_model = Column(String(128))
    training_file = Column(String(512))
    training_examples = Column(Integer)
    version = Column(String(64))
    deployed_at = Column(DateTime, server_default=func.now())
    is_active = Column(Boolean, default=True)
    metrics = Column(JSON)  # {"precision": 0.92, "recall": 0.85, ...}
    metadata_ = Column("metadata", JSON)

    __table_args__ = (Index("ix_model_registry_type_active", "model_type", "is_active"),)


# ── A/B Experiments (v0.3 T2) ──


class ABExperiment(Base):
    __tablename__ = "ab_experiments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String(64), nullable=False, unique=True)
    project_id = Column(String(64), ForeignKey("projects.id"), nullable=False)
    primary_model = Column(String(256), nullable=False)
    canary_model = Column(String(256), nullable=False)
    canary_pct = Column(Float, nullable=False, default=0.1)
    status = Column(String(16), nullable=False, default="active")
    started_at = Column(DateTime, server_default=func.now())
    ended_at = Column(DateTime)
    hypothesis = Column(Text)
    metadata_ = Column("metadata", JSON)

    __table_args__ = (Index("ix_ab_experiment_project_status", "project_id", "status"),)


class ABResult(Base):
    __tablename__ = "ab_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String(64), ForeignKey("ab_experiments.experiment_id"), nullable=False)
    judgment_id = Column(Integer, ForeignKey("judgments.id"))
    model_used = Column(String(256), nullable=False)
    latency_ms = Column(Float)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (Index("ix_ab_result_experiment", "experiment_id"),)


# ── DPO Preference Pairs (v0.3 T2) ──


class PreferencePair(Base):
    __tablename__ = "preference_pairs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    draft_id = Column(Integer, ForeignKey("drafts.id"), nullable=False)
    project_id = Column(String(64), ForeignKey("projects.id"), nullable=False)
    prompt = Column(Text, nullable=False)
    chosen_text = Column(Text, nullable=False)
    rejected_text = Column(Text, nullable=False)
    source = Column(String(32), nullable=False)  # "edit", "reject", "manual"
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (Index("ix_pref_pair_project", "project_id"),)


# ── Sequence Engine (Bridge) ──


class Sequence(Base):
    """Outreach sequence template."""

    __tablename__ = "sequences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(64), ForeignKey("projects.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    steps = relationship(
        "SequenceStep",
        back_populates="sequence",
        order_by="SequenceStep.step_order",
    )
    enrollments = relationship(
        "Enrollment",
        back_populates="sequence",
    )


class SequenceStep(Base):
    """Single step within an outreach sequence."""

    __tablename__ = "sequence_steps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sequence_id = Column(Integer, ForeignKey("sequences.id"), nullable=False)
    step_order = Column(Integer, nullable=False)
    action_type = Column(String(50), nullable=False)  # like, follow, reply, wait, check_response
    delay_hours = Column(Float, default=0.0)
    config_json = Column(Text, default="{}")
    requires_approval = Column(Boolean, default=False)

    sequence = relationship(
        "Sequence",
        back_populates="steps",
    )


class Enrollment(Base):
    """Tracks a lead's progress through a sequence."""

    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    normalized_post_id = Column(
        Integer, ForeignKey("normalized_posts.id"), nullable=False
    )
    sequence_id = Column(Integer, ForeignKey("sequences.id"), nullable=False)
    project_id = Column(String(64), ForeignKey("projects.id"), nullable=False)
    current_step_order = Column(Integer, default=0)
    status: Column[Any] = Column(
        SAEnum(EnrollmentStatus), default=EnrollmentStatus.ACTIVE
    )
    enrolled_at = Column(DateTime, server_default=func.now())
    next_step_at = Column(DateTime)
    completed_at = Column(DateTime)

    sequence = relationship(
        "Sequence",
        back_populates="enrollments",
    )
    executions = relationship(
        "StepExecution",
        back_populates="enrollment",
    )

    __table_args__ = (
        Index("ix_enrollment_status_next", "status", "next_step_at"),
        Index("ix_enrollment_project", "project_id"),
    )


class StepExecution(Base):
    """Record of an executed sequence step."""

    __tablename__ = "step_executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id"), nullable=False)
    step_id = Column(Integer, ForeignKey("sequence_steps.id"), nullable=False)
    action_type = Column(String(50), nullable=False)
    status = Column(String(50), default="pending")
    executed_at = Column(DateTime)
    result_json = Column(Text, default="{}")

    enrollment = relationship(
        "Enrollment",
        back_populates="executions",
    )


# ── Engine / Session helpers ──


def get_engine(db_url: str = "sqlite:///signalops.db") -> Engine:
    """Create a SQLAlchemy engine."""
    return create_engine(db_url, echo=False)


def get_session(engine: Engine) -> Session:
    """Create a new session bound to the engine."""
    session_factory = sessionmaker(bind=engine)
    return session_factory()


def init_db(engine: Engine) -> None:
    """Create all tables."""
    Base.metadata.create_all(engine)

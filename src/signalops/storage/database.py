"""SQLAlchemy models and database session management."""

import enum

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
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


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
    label = Column(SAEnum(JudgmentLabel), nullable=False)  # type: ignore[var-annotated]
    confidence = Column(Float, nullable=False)
    reasoning = Column(Text)
    model_id = Column(String(128), nullable=False)
    model_version = Column(String(64))
    latency_ms = Column(Float)
    created_at = Column(DateTime, server_default=func.now())

    # Human correction (nullable — only set if human overrides)
    human_label = Column(SAEnum(JudgmentLabel))  # type: ignore[var-annotated]
    human_corrected_at = Column(DateTime)
    human_reason = Column(Text)

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
    created_at = Column(DateTime, server_default=func.now())

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
    status = Column(SAEnum(DraftStatus), default=DraftStatus.PENDING)  # type: ignore[var-annotated]
    created_at = Column(DateTime, server_default=func.now())
    approved_at = Column(DateTime)
    sent_at = Column(DateTime)
    sent_post_id = Column(String(64))

    __table_args__ = (Index("ix_draft_project_status", "project_id", "status"),)


# ── Outcomes ──


class Outcome(Base):
    __tablename__ = "outcomes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    draft_id = Column(Integer, ForeignKey("drafts.id"), nullable=False)
    project_id = Column(String(64), ForeignKey("projects.id"), nullable=False)
    outcome_type = Column(SAEnum(OutcomeType), nullable=False)  # type: ignore[var-annotated]
    details = Column(JSON)
    observed_at = Column(DateTime, server_default=func.now())


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

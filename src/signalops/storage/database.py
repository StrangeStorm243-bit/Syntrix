"""Stub — real implementation on feat/data branch. Will be replaced at merge."""
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON,
    ForeignKey, func,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase
import enum


class Base(DeclarativeBase):
    pass


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


class NormalizedPost(Base):
    __tablename__ = "normalized_posts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    raw_post_id = Column(Integer)
    project_id = Column(String(64))
    platform = Column(String(32))
    platform_id = Column(String(64))
    author_id = Column(String(64))
    author_username = Column(String(256))
    author_display_name = Column(String(256))
    author_followers = Column(Integer, default=0)
    author_verified = Column(Boolean, default=False)
    text_original = Column(Text)
    text_cleaned = Column(Text)
    language = Column(String(8))
    created_at = Column(DateTime)
    reply_to_id = Column(String(64))
    conversation_id = Column(String(64))
    likes = Column(Integer, default=0)
    retweets = Column(Integer, default=0)
    replies = Column(Integer, default=0)
    views = Column(Integer, default=0)
    hashtags = Column(JSON)
    mentions = Column(JSON)
    urls = Column(JSON)


class Judgment(Base):
    __tablename__ = "judgments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    normalized_post_id = Column(Integer)
    project_id = Column(String(64))
    label = Column(SAEnum(JudgmentLabel))
    confidence = Column(Float)
    reasoning = Column(Text)
    model_id = Column(String(128))
    model_version = Column(String(64))
    latency_ms = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
    human_label = Column(SAEnum(JudgmentLabel))
    human_corrected_at = Column(DateTime)
    human_reason = Column(Text)


class Score(Base):
    __tablename__ = "scores"
    id = Column(Integer, primary_key=True, autoincrement=True)
    normalized_post_id = Column(Integer)
    project_id = Column(String(64))
    total_score = Column(Float)
    components = Column(JSON)
    scoring_version = Column(String(64))
    created_at = Column(DateTime, server_default=func.now())


class Draft(Base):
    __tablename__ = "drafts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    normalized_post_id = Column(Integer)
    project_id = Column(String(64))
    text_generated = Column(Text)
    text_final = Column(Text)
    tone = Column(String(64))
    template_used = Column(String(128))
    model_id = Column(String(128))
    status = Column(SAEnum(DraftStatus), default=DraftStatus.PENDING)
    created_at = Column(DateTime, server_default=func.now())
    approved_at = Column(DateTime)
    sent_at = Column(DateTime)
    sent_post_id = Column(String(64))


def get_engine(db_url="sqlite:///signalops.db"):
    from sqlalchemy import create_engine
    return create_engine(db_url, echo=False)


def get_session(engine):
    from sqlalchemy.orm import sessionmaker
    return sessionmaker(bind=engine)()


def init_db(engine):
    Base.metadata.create_all(engine)

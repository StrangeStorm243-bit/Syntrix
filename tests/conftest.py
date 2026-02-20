"""Shared test fixtures for all test modules."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from signalops.config.schema import (
    PersonaConfig,
    ProjectConfig,
    QueryConfig,
    RelevanceRubric,
)
from signalops.storage.database import init_db


@pytest.fixture
def engine():
    """In-memory SQLite engine with all tables created."""
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    return engine


@pytest.fixture
def db_session(engine):
    """DB session that rolls back after each test."""
    session_cls = sessionmaker(bind=engine)
    session = session_cls()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def sample_project_config():
    """Returns a minimal ProjectConfig for testing."""
    return ProjectConfig(
        project_id="test-project",
        project_name="Test Project",
        description="A test project for unit tests",
        queries=[
            QueryConfig(text="test query -is:retweet lang:en", label="test query"),
        ],
        relevance=RelevanceRubric(
            system_prompt="You are a test relevance judge.",
            positive_signals=["expressing need", "asking for help"],
            negative_signals=["hiring post", "spam"],
        ),
        persona=PersonaConfig(
            name="Test Bot",
            role="tester",
            tone="helpful",
            voice_notes="Be concise and helpful.",
            example_reply="Happy to help — here's what we do.",
        ),
    )


@pytest.fixture
def sample_raw_post_data():
    """Returns dict matching X API v2 tweet response structure."""
    return {
        "data": {
            "id": "1234567890",
            "text": (
                "Just spent 3 hours reviewing a PR that should have taken"
                " 30 minutes. There has to be a better way."
            ),
            "author_id": "9876543210",
            "created_at": "2026-02-18T12:00:00.000Z",
            "conversation_id": "1234567890",
            "public_metrics": {
                "like_count": 15,
                "retweet_count": 3,
                "reply_count": 5,
                "impression_count": 2500,
            },
            "entities": {"urls": [], "mentions": [], "hashtags": []},
            "lang": "en",
        },
        "includes": {
            "users": [
                {
                    "id": "9876543210",
                    "username": "techleadSara",
                    "name": "Sara Chen",
                    "public_metrics": {"followers_count": 2340},
                    "verified": False,
                    "description": ("Senior engineer @BigCorp. Building distributed systems."),
                }
            ]
        },
    }


@pytest.fixture
def sample_project_in_db(db_session):
    """Insert a test project row and return its ID."""
    from signalops.storage.database import Project

    project = Project(
        id="test-project",
        name="Test Project",
        config_path="projects/test.yaml",
        config_hash="abc123",
    )
    db_session.add(project)
    db_session.commit()
    return "test-project"

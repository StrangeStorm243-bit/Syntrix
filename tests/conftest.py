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
from signalops.storage.database import Base, init_db


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

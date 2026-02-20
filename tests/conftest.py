"""Shared test fixtures for all test modules."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

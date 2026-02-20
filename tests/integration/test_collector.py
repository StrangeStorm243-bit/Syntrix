"""Integration tests for the collector stage with mocked connectors."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from signalops.config.schema import (
    PersonaConfig,
    ProjectConfig,
    QueryConfig,
    RelevanceRubric,
)
from signalops.connectors.base import Connector, RawPost
from signalops.pipeline.collector import CollectorStage
from signalops.storage.cache import InMemoryCache
from signalops.storage.database import AuditLog, Project
from signalops.storage.database import RawPost as RawPostDB


def _make_raw_post(platform_id: str, text: str = "Test tweet") -> RawPost:
    return RawPost(
        platform="x",
        platform_id=platform_id,
        author_id="author_1",
        author_username="testuser",
        author_display_name="Test User",
        author_followers=1000,
        author_verified=False,
        text=text,
        created_at=datetime.now(UTC),
        language="en",
        reply_to_id=None,
        conversation_id=platform_id,
        metrics={"likes": 5, "retweets": 1, "replies": 2, "views": 500},
        entities={"urls": [], "mentions": [], "hashtags": []},
        raw_json={"id": platform_id, "text": text},
    )


def _make_config(project_id="test-project", queries=None):
    if queries is None:
        queries = [QueryConfig(text="test query", label="test")]
    return ProjectConfig(
        project_id=project_id,
        project_name="Test",
        description="Test",
        queries=queries,
        relevance=RelevanceRubric(
            system_prompt="test", positive_signals=["a"], negative_signals=["b"]
        ),
        persona=PersonaConfig(name="Bot", role="t", tone="t", voice_notes="t", example_reply="t"),
    )


@pytest.fixture
def mock_connector():
    connector = MagicMock(spec=Connector)
    connector.search.return_value = [
        _make_raw_post("tweet_001", "First tweet"),
        _make_raw_post("tweet_002", "Second tweet"),
        _make_raw_post("tweet_003", "Third tweet"),
    ]
    return connector


@pytest.fixture
def setup_project(db_session):
    project = Project(id="test-project", name="Test Project", config_path="test.yaml")
    db_session.add(project)
    db_session.commit()
    return "test-project"


def test_stores_tweets(db_session, mock_connector, setup_project):
    config = _make_config()
    collector = CollectorStage(connector=mock_connector, db_session=db_session)
    result = collector.run(config=config)
    assert result["total_new"] == 3
    assert db_session.query(RawPostDB).count() == 3


def test_deduplication(db_session, mock_connector, setup_project):
    config = _make_config()
    collector = CollectorStage(connector=mock_connector, db_session=db_session)
    collector.run(config=config)
    result2 = collector.run(config=config)
    assert result2["total_new"] == 0
    assert result2["total_skipped"] == 3
    assert db_session.query(RawPostDB).count() == 3


def test_incremental(db_session, mock_connector, setup_project):
    config = _make_config()
    collector = CollectorStage(connector=mock_connector, db_session=db_session)
    collector.run(config=config)
    mock_connector.search.return_value = [_make_raw_post("tweet_004"), _make_raw_post("tweet_005")]
    result = collector.run(config=config)
    assert result["total_new"] == 2
    assert db_session.query(RawPostDB).count() == 5


def test_dry_run(db_session, mock_connector, setup_project):
    config = _make_config()
    collector = CollectorStage(connector=mock_connector, db_session=db_session)
    result = collector.run(config=config, dry_run=True)
    assert result["total_new"] == 3
    assert db_session.query(RawPostDB).count() == 0


def test_empty_results(db_session, setup_project):
    connector = MagicMock(spec=Connector)
    connector.search.return_value = []
    config = _make_config()
    collector = CollectorStage(connector=connector, db_session=db_session)
    result = collector.run(config=config)
    assert result["total_new"] == 0


def test_multiple_queries(db_session, setup_project):
    config = _make_config(
        queries=[
            QueryConfig(text="q1", label="Q1"),
            QueryConfig(text="q2", label="Q2"),
            QueryConfig(text="q3", label="Q3"),
        ]
    )
    call_count = 0

    def mock_search(query, since_id=None, max_results=100):
        nonlocal call_count
        call_count += 1
        return [_make_raw_post(f"q{call_count}_t1")]

    connector = MagicMock(spec=Connector)
    connector.search.side_effect = mock_search
    collector = CollectorStage(connector=connector, db_session=db_session)
    result = collector.run(config=config)
    assert call_count == 3
    assert result["total_new"] == 3


def test_disabled_query(db_session, setup_project):
    config = _make_config(
        queries=[
            QueryConfig(text="enabled", label="Enabled"),
            QueryConfig(text="disabled", label="Disabled", enabled=False),
        ]
    )
    connector = MagicMock(spec=Connector)
    connector.search.return_value = [_make_raw_post("t1")]
    collector = CollectorStage(connector=connector, db_session=db_session)
    result = collector.run(config=config)
    assert connector.search.call_count == 1
    disabled_q = next(q for q in result["per_query"] if q["label"] == "Disabled")
    assert disabled_q.get("disabled") is True


def test_audit_log(db_session, mock_connector, setup_project):
    config = _make_config()
    collector = CollectorStage(connector=mock_connector, db_session=db_session)
    collector.run(config=config)
    logs = db_session.query(AuditLog).filter_by(action="collect").all()
    assert len(logs) >= 1


# ── Cache integration tests ──


def test_search_cache_hit_skips_connector(db_session, mock_connector, setup_project):
    """When search results are cached, the connector.search() should not be called."""
    cache = InMemoryCache()
    config = _make_config()
    collector = CollectorStage(connector=mock_connector, db_session=db_session, cache=cache)
    # First run populates the search cache
    result1 = collector.run(config=config)
    assert result1["total_new"] == 3
    assert mock_connector.search.call_count == 1

    # Reset DB and dedup cache so second run can re-insert
    db_session.query(RawPostDB).delete()
    db_session.commit()
    for key in list(cache._store.keys()):
        if key.startswith("dedup:"):
            cache.delete(key)

    # Second run should hit search cache, not connector
    result2 = collector.run(config=config)
    # Connector was only called once total (first run)
    assert mock_connector.search.call_count == 1
    assert result2["total_new"] == 3


def test_dedup_cache_skips_db_insert(db_session, mock_connector, setup_project):
    """When dedup cache says a post is seen, we skip the DB insert entirely."""
    cache = InMemoryCache()
    config = _make_config()
    collector = CollectorStage(connector=mock_connector, db_session=db_session, cache=cache)
    # First run: inserts 3 posts and marks them in cache
    result1 = collector.run(config=config)
    assert result1["total_new"] == 3

    # Expire the search cache so connector is called again
    for key in list(cache._store.keys()):
        if key.startswith("search:"):
            cache.delete(key)

    # Second run: dedup cache catches all 3 as duplicates
    result2 = collector.run(config=config)
    assert result2["total_skipped"] == 3
    assert result2["total_new"] == 0


def test_no_cache_falls_back_to_db_dedup(db_session, mock_connector, setup_project):
    """Without cache, deduplication still works via DB IntegrityError."""
    config = _make_config()
    collector = CollectorStage(connector=mock_connector, db_session=db_session, cache=None)
    result1 = collector.run(config=config)
    assert result1["total_new"] == 3
    result2 = collector.run(config=config)
    assert result2["total_skipped"] == 3

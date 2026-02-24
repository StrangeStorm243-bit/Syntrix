"""Tests for batch collector."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from signalops.config.schema import (
    PersonaConfig,
    ProjectConfig,
    QueryConfig,
    RelevanceRubric,
)
from signalops.connectors.rate_limiter import RateLimiter
from signalops.pipeline.batch import BatchCollector, BatchResult


def _make_config(queries: list[QueryConfig] | None = None) -> ProjectConfig:
    return ProjectConfig(
        project_id="test-project",
        project_name="Test",
        description="Test project",
        queries=queries
        or [
            QueryConfig(text="query1", label="Q1"),
            QueryConfig(text="query2", label="Q2"),
            QueryConfig(text="query3", label="Q3", enabled=False),
        ],
        relevance=RelevanceRubric(
            system_prompt="judge",
            positive_signals=["need"],
            negative_signals=["spam"],
        ),
        persona=PersonaConfig(
            name="Bot",
            role="helper",
            tone="helpful",
            voice_notes="Be concise.",
            example_reply="Hi!",
        ),
    )


def _mock_api_response(tweet_count: int = 3) -> dict[str, Any]:
    return {
        "data": [
            {"id": str(100 + i), "text": f"tweet {i}", "author_id": f"u{i}"}
            for i in range(tweet_count)
        ],
        "includes": {
            "users": [{"id": f"u{i}", "username": f"user{i}"} for i in range(tweet_count)]
        },
    }


@pytest.mark.asyncio
async def test_batch_runs_enabled_queries_only() -> None:
    """Only enabled queries are executed."""
    config = _make_config()
    rate_limiter = RateLimiter(max_requests=100, window_seconds=900)
    session = MagicMock()
    session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
    session.query.return_value.filter.return_value.first.return_value = None

    collector = BatchCollector(
        bearer_token="test",
        db_session=session,
        rate_limiter=rate_limiter,
        concurrency=3,
    )

    mock_response = _mock_api_response(2)
    with patch(
        "signalops.connectors.async_client.AsyncXClient",
    ) as mock_client:
        instance = mock_client.return_value
        instance.search_recent = AsyncMock(return_value=mock_response)

        result = await collector.run(config, dry_run=True)

    assert result.total_queries == 2  # Only enabled queries
    assert result.successful_queries == 2
    assert result.failed_queries == 0
    assert result.total_tweets_found == 4  # 2 tweets per query * 2 queries


@pytest.mark.asyncio
async def test_batch_handles_query_failure() -> None:
    """Failed queries are tracked in results."""
    config = _make_config(queries=[QueryConfig(text="good_query", label="Good")])
    rate_limiter = RateLimiter(max_requests=100, window_seconds=900)
    session = MagicMock()
    session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

    collector = BatchCollector(
        bearer_token="test",
        db_session=session,
        rate_limiter=rate_limiter,
    )

    with patch(
        "signalops.connectors.async_client.AsyncXClient",
    ) as mock_client:
        instance = mock_client.return_value
        instance.search_recent = AsyncMock(side_effect=RuntimeError("API down"))

        result = await collector.run(config, dry_run=True)

    assert result.failed_queries == 1
    assert result.query_results[0].error is not None


@pytest.mark.asyncio
async def test_batch_dry_run_no_store() -> None:
    """Dry run counts tweets but does not store them."""
    config = _make_config(queries=[QueryConfig(text="q1", label="Q1")])
    rate_limiter = RateLimiter(max_requests=100, window_seconds=900)
    session = MagicMock()
    session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

    collector = BatchCollector(
        bearer_token="test",
        db_session=session,
        rate_limiter=rate_limiter,
    )

    with patch(
        "signalops.connectors.async_client.AsyncXClient",
    ) as mock_client:
        instance = mock_client.return_value
        instance.search_recent = AsyncMock(return_value=_mock_api_response(5))

        result = await collector.run(config, dry_run=True)

    assert result.total_new_tweets == 5
    session.add.assert_not_called()
    session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_batch_concurrency_limit() -> None:
    """Only N queries run simultaneously."""
    queries = [QueryConfig(text=f"q{i}", label=f"Q{i}") for i in range(5)]
    config = _make_config(queries=queries)
    rate_limiter = RateLimiter(max_requests=100, window_seconds=900)
    session = MagicMock()
    session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
    session.query.return_value.filter.return_value.first.return_value = None

    max_concurrent = 0
    current_concurrent = 0
    lock = asyncio.Lock()

    async def slow_search(*args: Any, **kwargs: Any) -> dict[str, Any]:
        nonlocal max_concurrent, current_concurrent
        async with lock:
            current_concurrent += 1
            max_concurrent = max(max_concurrent, current_concurrent)
        await asyncio.sleep(0.05)
        async with lock:
            current_concurrent -= 1
        return _mock_api_response(1)

    collector = BatchCollector(
        bearer_token="test",
        db_session=session,
        rate_limiter=rate_limiter,
        concurrency=2,
    )

    with patch(
        "signalops.connectors.async_client.AsyncXClient",
    ) as mock_client:
        instance = mock_client.return_value
        instance.search_recent = slow_search

        await collector.run(config, dry_run=True)

    assert max_concurrent <= 2


@pytest.mark.asyncio
async def test_batch_result_dataclass() -> None:
    """BatchResult fields compute correctly."""
    result = BatchResult(
        total_queries=3,
        successful_queries=2,
        failed_queries=1,
        total_tweets_found=10,
        total_new_tweets=8,
    )
    assert result.total_queries == 3
    assert result.query_results == []

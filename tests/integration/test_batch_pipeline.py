"""Integration tests for batch collection pipeline."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from signalops.config.schema import (
    BatchConfig,
    PersonaConfig,
    ProjectConfig,
    QueryConfig,
    RelevanceRubric,
)
from signalops.pipeline.batch import run_batch_sync
from signalops.storage.database import Project, RawPost


def _make_config(
    project_id: str = "test-project",
    queries: list[QueryConfig] | None = None,
    batch: BatchConfig | None = None,
) -> ProjectConfig:
    if queries is None:
        queries = [
            QueryConfig(text="test query", label="Q1"),
            QueryConfig(text="other query", label="Q2"),
        ]
    return ProjectConfig(
        project_id=project_id,
        project_name="Test",
        description="Test",
        queries=queries,
        batch=batch or BatchConfig(enabled=True, concurrency=2),
        relevance=RelevanceRubric(
            system_prompt="test",
            positive_signals=["a"],
            negative_signals=["b"],
        ),
        persona=PersonaConfig(name="Bot", role="t", tone="t", voice_notes="t", example_reply="t"),
    )


def _mock_api_response(tweet_ids: list[str]) -> dict:
    """Build a fake X API v2 response."""
    return {
        "data": [
            {
                "id": tid,
                "text": f"Tweet text for {tid}",
                "author_id": "author_1",
                "created_at": "2026-02-20T12:00:00.000Z",
            }
            for tid in tweet_ids
        ],
        "includes": {
            "users": [
                {
                    "id": "author_1",
                    "username": "testuser",
                    "name": "Test User",
                    "public_metrics": {"followers_count": 500},
                    "verified": False,
                }
            ]
        },
    }


@pytest.fixture
def setup_project(db_session):
    project = Project(id="test-project", name="Test Project", config_path="test.yaml")
    db_session.add(project)
    db_session.commit()
    return "test-project"


class TestBatchPipelineIntegration:
    """End-to-end batch collection with mocked async HTTP."""

    @patch("signalops.connectors.async_client.AsyncXClient")
    def test_batch_stores_tweets(self, mock_client_cls, db_session, setup_project):
        """Batch collection stores tweets from multiple queries."""
        call_count = 0

        async def unique_response(**kwargs):
            nonlocal call_count
            call_count += 1
            return _mock_api_response([f"q{call_count}_t1", f"q{call_count}_t2"])

        mock_instance = AsyncMock()
        mock_instance.search_recent = AsyncMock(side_effect=unique_response)
        mock_client_cls.return_value = mock_instance

        config = _make_config()
        from signalops.connectors.rate_limiter import RateLimiter

        result = run_batch_sync(
            bearer_token="fake-token",
            db_session=db_session,
            rate_limiter=RateLimiter(max_requests=100, window_seconds=900),
            config=config,
            concurrency=2,
        )

        assert result.total_queries == 2
        assert result.successful_queries == 2
        assert result.failed_queries == 0
        assert result.total_tweets_found == 4  # 2 tweets x 2 queries
        assert db_session.query(RawPost).count() == 4

    @patch("signalops.connectors.async_client.AsyncXClient")
    def test_batch_deduplication(self, mock_client_cls, db_session, setup_project):
        """Running batch twice does not create duplicate RawPost rows."""
        mock_instance = AsyncMock()
        mock_instance.search_recent = AsyncMock(return_value=_mock_api_response(["t1", "t2"]))
        mock_client_cls.return_value = mock_instance

        config = _make_config(queries=[QueryConfig(text="test query", label="Q1")])
        from signalops.connectors.rate_limiter import RateLimiter

        rl = RateLimiter(max_requests=100, window_seconds=900)

        # First run
        result1 = run_batch_sync(
            bearer_token="fake",
            db_session=db_session,
            rate_limiter=rl,
            config=config,
        )
        assert result1.total_new_tweets == 2

        # Second run — same tweets returned
        result2 = run_batch_sync(
            bearer_token="fake",
            db_session=db_session,
            rate_limiter=rl,
            config=config,
        )
        assert result2.total_new_tweets == 0
        assert db_session.query(RawPost).count() == 2

    @patch("signalops.connectors.async_client.AsyncXClient")
    def test_batch_dry_run(self, mock_client_cls, db_session, setup_project):
        """Dry run fetches tweets but does not store them."""
        mock_instance = AsyncMock()
        mock_instance.search_recent = AsyncMock(return_value=_mock_api_response(["t1"]))
        mock_client_cls.return_value = mock_instance

        config = _make_config(queries=[QueryConfig(text="q", label="Q")])
        from signalops.connectors.rate_limiter import RateLimiter

        result = run_batch_sync(
            bearer_token="fake",
            db_session=db_session,
            rate_limiter=RateLimiter(max_requests=100, window_seconds=900),
            config=config,
            dry_run=True,
        )

        assert result.total_tweets_found == 1
        assert result.total_new_tweets == 1  # counted but not stored
        assert db_session.query(RawPost).count() == 0

    @patch("signalops.connectors.async_client.AsyncXClient")
    def test_batch_disabled_queries_skipped(self, mock_client_cls, db_session, setup_project):
        """Disabled queries are not executed."""
        mock_instance = AsyncMock()
        mock_instance.search_recent = AsyncMock(return_value=_mock_api_response(["t1"]))
        mock_client_cls.return_value = mock_instance

        config = _make_config(
            queries=[
                QueryConfig(text="active", label="Active"),
                QueryConfig(text="inactive", label="Inactive", enabled=False),
            ]
        )
        from signalops.connectors.rate_limiter import RateLimiter

        result = run_batch_sync(
            bearer_token="fake",
            db_session=db_session,
            rate_limiter=RateLimiter(max_requests=100, window_seconds=900),
            config=config,
        )

        assert result.total_queries == 1  # only enabled query
        assert result.successful_queries == 1

    @patch("signalops.connectors.async_client.AsyncXClient")
    def test_batch_handles_api_error(self, mock_client_cls, db_session, setup_project):
        """API errors are captured per-query, not propagated."""
        mock_instance = AsyncMock()
        mock_instance.search_recent = AsyncMock(side_effect=Exception("API rate limit exceeded"))
        mock_client_cls.return_value = mock_instance

        config = _make_config(queries=[QueryConfig(text="q", label="Q")])
        from signalops.connectors.rate_limiter import RateLimiter

        result = run_batch_sync(
            bearer_token="fake",
            db_session=db_session,
            rate_limiter=RateLimiter(max_requests=100, window_seconds=900),
            config=config,
        )

        assert result.total_queries == 1
        assert result.failed_queries == 1
        assert result.successful_queries == 0
        assert result.query_results[0].error is not None
        assert "rate limit" in result.query_results[0].error.lower()

    @patch("signalops.connectors.async_client.AsyncXClient")
    def test_since_id_resume(self, mock_client_cls, db_session, setup_project):
        """Second batch run uses since_id from the first run's stored tweets."""
        call_args_list: list[dict] = []

        async def capture_search(**kwargs):
            call_args_list.append(kwargs)
            return _mock_api_response([f"t{len(call_args_list)}"])

        mock_instance = AsyncMock()
        mock_instance.search_recent = AsyncMock(side_effect=capture_search)
        mock_client_cls.return_value = mock_instance

        config = _make_config(queries=[QueryConfig(text="test query", label="Q1")])
        from signalops.connectors.rate_limiter import RateLimiter

        rl = RateLimiter(max_requests=100, window_seconds=900)

        # First run — no since_id
        run_batch_sync(
            bearer_token="fake",
            db_session=db_session,
            rate_limiter=rl,
            config=config,
        )
        assert call_args_list[0].get("since_id") is None

        # Second run — should pass since_id from first run's stored tweet
        run_batch_sync(
            bearer_token="fake",
            db_session=db_session,
            rate_limiter=rl,
            config=config,
        )
        assert len(call_args_list) == 2
        assert call_args_list[1].get("since_id") is not None

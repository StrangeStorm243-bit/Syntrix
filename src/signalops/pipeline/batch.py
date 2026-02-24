"""Batch collection -- runs multiple search queries concurrently."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from signalops.config.schema import ProjectConfig, QueryConfig
from signalops.connectors.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


@dataclass
class BatchQueryResult:
    """Result of a single query in the batch."""

    query_label: str
    query_text: str
    tweets_found: int
    new_tweets: int
    error: str | None = None
    since_id_used: str | None = None
    latest_id: str | None = None


@dataclass
class BatchResult:
    """Aggregate result of batch collection."""

    total_queries: int
    successful_queries: int
    failed_queries: int
    total_tweets_found: int
    total_new_tweets: int
    query_results: list[BatchQueryResult] = field(default_factory=list)


class BatchCollector:
    """Runs multiple search queries concurrently, respecting rate limits."""

    def __init__(
        self,
        bearer_token: str,
        db_session: Session,
        rate_limiter: RateLimiter,
        concurrency: int = 3,
    ) -> None:
        self._bearer_token = bearer_token
        self._session = db_session
        self._rate_limiter = rate_limiter
        self._concurrency = concurrency
        self._semaphore = asyncio.Semaphore(concurrency)

    async def run(
        self,
        config: ProjectConfig,
        dry_run: bool = False,
    ) -> BatchResult:
        """Execute all enabled queries concurrently."""
        enabled_queries = [q for q in config.queries if q.enabled]
        result = BatchResult(
            total_queries=len(enabled_queries),
            successful_queries=0,
            failed_queries=0,
            total_tweets_found=0,
            total_new_tweets=0,
        )

        tasks = [self._run_query(query, config, dry_run) for query in enabled_queries]

        query_results = await asyncio.gather(*tasks, return_exceptions=True)

        for qr in query_results:
            if isinstance(qr, Exception):
                result.failed_queries += 1
                result.query_results.append(
                    BatchQueryResult(
                        query_label="unknown",
                        query_text="unknown",
                        tweets_found=0,
                        new_tweets=0,
                        error=str(qr),
                    )
                )
            else:
                assert isinstance(qr, BatchQueryResult)
                result.query_results.append(qr)
                if qr.error:
                    result.failed_queries += 1
                else:
                    result.successful_queries += 1
                result.total_tweets_found += qr.tweets_found
                result.total_new_tweets += qr.new_tweets

        return result

    async def _run_query(
        self,
        query: QueryConfig,
        config: ProjectConfig,
        dry_run: bool,
    ) -> BatchQueryResult:
        """Run a single query with rate limiting and semaphore."""
        async with self._semaphore:
            wait_time = self._rate_limiter.acquire()
            if wait_time > 0:
                logger.info(
                    "Rate limit: waiting %.1fs before query '%s'",
                    wait_time,
                    query.label,
                )
                await asyncio.sleep(wait_time)

            try:
                from signalops.connectors.async_client import AsyncXClient

                client = AsyncXClient(bearer_token=self._bearer_token)

                since_id = self._get_since_id(config.project_id, query.text)

                response = await client.search_recent(
                    query=query.text,
                    max_results=query.max_results_per_run,
                    since_id=since_id,
                )

                tweets: list[dict[str, Any]] = response.get("data", [])
                users: dict[str, dict[str, Any]] = {
                    u["id"]: u for u in response.get("includes", {}).get("users", [])
                }

                new_count = 0
                latest_id: str | None = None

                if not dry_run:
                    new_count = self._store_tweets(tweets, users, config.project_id, query.text)
                else:
                    new_count = len(tweets)

                if tweets:
                    latest_id = str(tweets[0].get("id", ""))

                return BatchQueryResult(
                    query_label=query.label,
                    query_text=query.text,
                    tweets_found=len(tweets),
                    new_tweets=new_count,
                    since_id_used=since_id,
                    latest_id=latest_id,
                )

            except Exception as e:
                logger.error("Query '%s' failed: %s", query.label, e)
                return BatchQueryResult(
                    query_label=query.label,
                    query_text=query.text,
                    tweets_found=0,
                    new_tweets=0,
                    error=str(e),
                )

    def _get_since_id(self, project_id: str, query_text: str) -> str | None:
        """Get the latest tweet ID for incremental collection."""
        from signalops.storage.database import RawPost

        latest = (
            self._session.query(RawPost.platform_id)
            .filter(
                RawPost.project_id == project_id,
                RawPost.query_used == query_text,
            )
            .order_by(RawPost.collected_at.desc())
            .first()
        )
        return str(latest[0]) if latest else None

    def _store_tweets(
        self,
        tweets: list[dict[str, Any]],
        users: dict[str, dict[str, Any]],
        project_id: str,
        query_text: str,
    ) -> int:
        """Store raw tweets, deduplicating by platform_id + project_id."""
        from signalops.storage.database import RawPost

        new_count = 0
        for tweet in tweets:
            tweet_id = str(tweet.get("id", ""))
            existing = (
                self._session.query(RawPost.id)
                .filter(
                    RawPost.platform == "x",
                    RawPost.platform_id == tweet_id,
                    RawPost.project_id == project_id,
                )
                .first()
            )
            if existing:
                continue

            author_id = str(tweet.get("author_id", ""))
            raw_json: dict[str, Any] = {
                "tweet": tweet,
                "author": users.get(author_id, {}),
            }

            row = RawPost(
                project_id=project_id,
                platform="x",
                platform_id=tweet_id,
                query_used=query_text,
                raw_json=raw_json,
            )
            self._session.add(row)
            new_count += 1

        if new_count > 0:
            self._session.commit()

        return new_count


def run_batch_sync(
    bearer_token: str,
    db_session: Session,
    rate_limiter: RateLimiter,
    config: ProjectConfig,
    concurrency: int = 3,
    dry_run: bool = False,
) -> BatchResult:
    """Synchronous wrapper for batch collection."""
    collector = BatchCollector(
        bearer_token=bearer_token,
        db_session=db_session,
        rate_limiter=rate_limiter,
        concurrency=concurrency,
    )
    return asyncio.run(collector.run(config, dry_run=dry_run))

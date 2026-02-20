"""Collector stage: fetches tweets via connector and stores them as raw posts."""

from __future__ import annotations

import dataclasses
import logging
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from signalops.config.schema import ProjectConfig
from signalops.connectors.base import Connector
from signalops.connectors.base import RawPost as ConnectorPost
from signalops.storage.audit import log_action
from signalops.storage.cache import (
    CacheBackend,
    cache_search_results,
    get_cached_search,
    is_duplicate,
    mark_seen,
)
from signalops.storage.database import RawPost

logger = logging.getLogger(__name__)


class CollectorStage:
    """Pipeline stage that collects posts from social platforms."""

    def __init__(
        self,
        connector: Connector,
        db_session: Session,
        cache: CacheBackend | None = None,
    ):
        self.connector = connector
        self.db = db_session
        self._cache = cache

    def run(self, config: ProjectConfig, dry_run: bool = False) -> dict[str, Any]:
        """Collect tweets for all enabled queries in the project config."""
        total_new = 0
        total_skipped = 0
        per_query: list[dict[str, Any]] = []

        for query_cfg in config.queries:
            if not query_cfg.enabled:
                per_query.append(
                    {"label": query_cfg.label, "new": 0, "skipped": 0, "disabled": True}
                )
                continue

            since_id = self._get_since_id(config.project_id, query_cfg.text)

            # Check search cache first
            cached_posts = self._get_cached_search(query_cfg.text)
            if cached_posts is not None:
                logger.debug("Cache hit for query '%s'", query_cfg.label)
                posts = cached_posts
            else:
                try:
                    posts = self.connector.search(
                        query=query_cfg.text,
                        since_id=since_id,
                        max_results=query_cfg.max_results_per_run,
                    )
                    self._cache_search(query_cfg.text, posts)
                except Exception as e:
                    logger.error("Failed to search query '%s': %s", query_cfg.label, e)
                    per_query.append(
                        {"label": query_cfg.label, "new": 0, "skipped": 0, "error": str(e)}
                    )
                    continue

            query_new = 0
            query_skipped = 0

            for post in posts:
                if dry_run:
                    query_new += 1
                    continue

                # Skip if already seen in cache (faster than DB unique constraint)
                if self._cache is not None and is_duplicate(
                    self._cache, post.platform, post.platform_id, config.project_id
                ):
                    query_skipped += 1
                    continue

                raw_post = RawPost(
                    project_id=config.project_id,
                    platform=post.platform,
                    platform_id=post.platform_id,
                    query_used=query_cfg.text,
                    raw_json=post.raw_json,
                )

                try:
                    self.db.add(raw_post)
                    self.db.flush()
                    query_new += 1
                    # Mark as seen in cache after successful insert
                    if self._cache is not None:
                        mark_seen(
                            self._cache,
                            post.platform,
                            post.platform_id,
                            config.project_id,
                        )
                except IntegrityError:
                    self.db.rollback()
                    query_skipped += 1

            if not dry_run:
                self.db.commit()

            total_new += query_new
            total_skipped += query_skipped
            per_query.append({"label": query_cfg.label, "new": query_new, "skipped": query_skipped})

            if not dry_run:
                log_action(
                    self.db,
                    project_id=config.project_id,
                    action="collect",
                    details={
                        "query_label": query_cfg.label,
                        "new_count": query_new,
                        "skipped_count": query_skipped,
                    },
                )

        return {
            "total_new": total_new,
            "total_skipped": total_skipped,
            "per_query": per_query,
        }

    def run_stream(
        self,
        config: ProjectConfig,
        stream_connector: Any,
        duration_seconds: int = 300,
    ) -> dict[str, Any]:
        """Collect tweets via Filtered Stream (real-time mode).

        An alternative to run() that uses the Filtered Stream endpoint.
        Stores incoming posts with the same dedup logic as search mode.

        Args:
            config: Project configuration.
            stream_connector: A StreamConnector instance.
            duration_seconds: How long to stream before stopping.

        Returns:
            Summary dict with total_new, total_skipped counts.
        """
        import threading

        total_new = 0
        total_skipped = 0

        def _on_post(post: ConnectorPost) -> None:
            nonlocal total_new, total_skipped

            # Dedup via cache
            if self._cache is not None and is_duplicate(
                self._cache, post.platform, post.platform_id, config.project_id
            ):
                total_skipped += 1
                return

            raw_post = RawPost(
                project_id=config.project_id,
                platform=post.platform,
                platform_id=post.platform_id,
                query_used="stream",
                raw_json=post.raw_json,
            )

            try:
                self.db.add(raw_post)
                self.db.flush()
                self.db.commit()
                total_new += 1
                if self._cache is not None:
                    mark_seen(
                        self._cache,
                        post.platform,
                        post.platform_id,
                        config.project_id,
                    )
            except IntegrityError:
                self.db.rollback()
                total_skipped += 1

        # Add rules from config
        if config.stream.rules:
            stream_connector.add_rules(config.stream.rules)

        # Run stream in a background thread with a timeout
        stream_thread = threading.Thread(
            target=stream_connector.stream,
            kwargs={
                "callback": _on_post,
                "backfill_minutes": config.stream.backfill_minutes,
                "max_reconnects": 1,
            },
            daemon=True,
        )
        stream_thread.start()
        stream_thread.join(timeout=duration_seconds)

        if not total_new and not total_skipped:
            log_action(
                self.db,
                project_id=config.project_id,
                action="collect_stream",
                details={"duration_seconds": duration_seconds, "note": "no posts received"},
            )
        else:
            log_action(
                self.db,
                project_id=config.project_id,
                action="collect_stream",
                details={
                    "new_count": total_new,
                    "skipped_count": total_skipped,
                    "duration_seconds": duration_seconds,
                },
            )

        return {
            "total_new": total_new,
            "total_skipped": total_skipped,
            "mode": "stream",
        }

    def _get_since_id(self, project_id: str, query_text: str) -> str | None:
        """Get the most recent platform_id for incremental collection."""
        result = (
            self.db.query(RawPost.platform_id)
            .filter(
                RawPost.project_id == project_id,
                RawPost.query_used == query_text,
            )
            .order_by(RawPost.id.desc())
            .first()
        )
        return result[0] if result else None

    def _get_cached_search(self, query_text: str) -> list[ConnectorPost] | None:
        """Check search cache for recent results."""
        if self._cache is None:
            return None
        raw = get_cached_search(self._cache, query_text)
        if raw is None:
            return None
        from datetime import datetime

        posts: list[ConnectorPost] = []
        for d in raw:
            if isinstance(d.get("created_at"), str):
                d["created_at"] = datetime.fromisoformat(d["created_at"])
            posts.append(ConnectorPost(**d))
        return posts

    def _cache_search(self, query_text: str, posts: list[ConnectorPost]) -> None:
        """Store search results in cache."""
        if self._cache is None:
            return
        serialized: list[dict[str, Any]] = []
        for p in posts:
            d = dataclasses.asdict(p)
            if hasattr(d.get("created_at"), "isoformat"):
                d["created_at"] = d["created_at"].isoformat()
            serialized.append(d)
        cache_search_results(self._cache, query_text, serialized)

"""Collector stage: fetches tweets via connector and stores them as raw posts."""

import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from signalops.config.schema import ProjectConfig
from signalops.connectors.base import Connector
from signalops.storage.audit import log_action
from signalops.storage.database import RawPost

logger = logging.getLogger(__name__)


class CollectorStage:
    """Pipeline stage that collects posts from social platforms."""

    def __init__(self, connector: Connector, db_session: Session):
        self.connector = connector
        self.db = db_session

    def run(self, config: ProjectConfig, dry_run: bool = False) -> dict:
        """Collect tweets for all enabled queries in the project config."""
        total_new = 0
        total_skipped = 0
        per_query: list[dict] = []

        for query_cfg in config.queries:
            if not query_cfg.enabled:
                per_query.append(
                    {"label": query_cfg.label, "new": 0, "skipped": 0, "disabled": True}
                )
                continue

            since_id = self._get_since_id(config.project_id, query_cfg.text)

            try:
                posts = self.connector.search(
                    query=query_cfg.text,
                    since_id=since_id,
                    max_results=query_cfg.max_results_per_run,
                )
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
                except IntegrityError:
                    self.db.rollback()
                    query_skipped += 1

            if not dry_run:
                self.db.commit()

            total_new += query_new
            total_skipped += query_skipped
            per_query.append(
                {"label": query_cfg.label, "new": query_new, "skipped": query_skipped}
            )

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

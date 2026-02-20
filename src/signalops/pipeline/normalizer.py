"""Normalizer stage: cleans raw posts and produces normalized posts."""

import logging
import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from signalops.storage.database import NormalizedPost, RawPost

logger = logging.getLogger(__name__)

URL_PATTERN = re.compile(r"https?://\S+")
WHITESPACE_PATTERN = re.compile(r"\s+")


def clean_text(text: str) -> str:
    """Strip URLs, collapse whitespace, and trim."""
    cleaned = URL_PATTERN.sub("", text)
    cleaned = WHITESPACE_PATTERN.sub(" ", cleaned)
    return cleaned.strip()


def extract_hashtags(entities: dict) -> list[str]:
    """Extract hashtag tags from X API entities."""
    return [h.get("tag", "") for h in entities.get("hashtags", []) if h.get("tag")]


def extract_mentions(entities: dict) -> list[str]:
    """Extract mention usernames from X API entities."""
    return [
        f"@{m.get('username', '')}"
        for m in entities.get("mentions", [])
        if m.get("username")
    ]


def extract_urls(entities: dict) -> list[str]:
    """Extract expanded URLs from X API entities."""
    return [
        u.get("expanded_url", u.get("url", ""))
        for u in entities.get("urls", [])
        if u.get("expanded_url") or u.get("url")
    ]


def detect_language(text: str, api_lang: str | None) -> str | None:
    """Detect language. Prefer API-provided lang, fallback to heuristic."""
    if api_lang and api_lang != "und":
        return api_lang
    if not text.strip():
        return None
    text_lower = text.lower()
    spanish_words = {"el", "la", "los", "las", "es", "son", "está", "como", "para", "por"}
    words = set(text_lower.split())
    if len(words & spanish_words) >= 2:
        return "es"
    if re.search(r"[a-zA-Z]", text):
        return "en"
    return None


class NormalizerStage:
    """Pipeline stage that normalizes raw posts."""

    def run(
        self, db_session: Session, project_id: str, dry_run: bool = False
    ) -> dict:
        """Normalize all raw posts that don't yet have a normalized version."""
        existing_raw_ids = (
            db_session.query(NormalizedPost.raw_post_id)
            .filter(NormalizedPost.project_id == project_id)
            .subquery()
        )
        raw_posts = (
            db_session.query(RawPost)
            .filter(RawPost.project_id == project_id, ~RawPost.id.in_(existing_raw_ids))
            .all()
        )

        processed = 0
        skipped = 0

        for raw_post in raw_posts:
            try:
                normalized = self._normalize_post(raw_post)
                if dry_run:
                    processed += 1
                    continue
                db_session.add(normalized)
                processed += 1
            except Exception as e:
                logger.error("Failed to normalize raw_post %d: %s", raw_post.id, e)
                skipped += 1

        if not dry_run:
            db_session.commit()

        return {"processed_count": processed, "skipped_count": skipped}

    def _normalize_post(self, raw_post: RawPost) -> NormalizedPost:
        """Create a NormalizedPost from a RawPost."""
        raw = raw_post.raw_json
        data = raw if "data" not in raw else raw

        text_original = data.get("text", "")
        text_cleaned = clean_text(text_original)

        author_id = data.get("author_id", "")
        users = raw.get("includes", {}).get("users", []) if "includes" in raw else []
        user = next((u for u in users if u.get("id") == author_id), {})

        created_str = data.get("created_at", "")
        try:
            created_at = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            created_at = datetime.now(timezone.utc)

        metrics = data.get("public_metrics", {})
        entities = data.get("entities", {})

        reply_to_id = None
        for ref in data.get("referenced_tweets", []):
            if ref.get("type") == "replied_to":
                reply_to_id = ref.get("id")
                break

        return NormalizedPost(
            raw_post_id=raw_post.id,
            project_id=raw_post.project_id,
            platform=raw_post.platform,
            platform_id=data.get("id", raw_post.platform_id),
            author_id=author_id,
            author_username=user.get("username", ""),
            author_display_name=user.get("name", ""),
            author_followers=user.get("public_metrics", {}).get("followers_count", 0),
            author_verified=user.get("verified", False),
            text_original=text_original,
            text_cleaned=text_cleaned,
            language=detect_language(text_cleaned, data.get("lang")),
            created_at=created_at,
            reply_to_id=reply_to_id,
            conversation_id=data.get("conversation_id"),
            likes=metrics.get("like_count", 0),
            retweets=metrics.get("retweet_count", 0),
            replies=metrics.get("reply_count", 0),
            views=metrics.get("impression_count", 0),
            hashtags=extract_hashtags(entities),
            mentions=extract_mentions(entities),
            urls=extract_urls(entities),
        )

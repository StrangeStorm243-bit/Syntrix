"""Tests for the normalizer stage helper functions."""

from __future__ import annotations

from signalops.pipeline.normalizer import (
    NormalizerStage,
    clean_text,
    detect_language,
    extract_entities_from_text,
    extract_hashtags,
    extract_mentions,
    extract_urls,
)


class TestCleanText:
    def test_strip_single_url(self):
        assert clean_text("Check out https://t.co/abc123") == "Check out"

    def test_strip_multiple_urls(self):
        assert clean_text("See https://t.co/abc and https://example.com/page") == "See and"

    def test_preserve_mentions(self):
        assert "@alice" in clean_text("Thanks @alice for the tip")

    def test_collapse_whitespace(self):
        assert clean_text("too   many    spaces") == "too many spaces"

    def test_strip_leading_trailing(self):
        assert clean_text("  hello  ") == "hello"

    def test_empty_text(self):
        assert clean_text("") == ""

    def test_text_with_only_urls(self):
        assert clean_text("https://t.co/abc") == ""

    def test_tabs_and_newlines(self):
        assert clean_text("hello\t\tworld\n\nnew") == "hello world new"

    def test_url_in_middle(self):
        assert clean_text("before https://t.co/x after") == "before after"

    def test_preserves_punctuation(self):
        assert clean_text("Wow! Great, right?") == "Wow! Great, right?"


class TestExtractHashtags:
    def test_multiple(self):
        assert extract_hashtags({"hashtags": [{"tag": "ai"}, {"tag": "code"}]}) == ["ai", "code"]

    def test_empty(self):
        assert extract_hashtags({"hashtags": []}) == []

    def test_missing_key(self):
        assert extract_hashtags({}) == []

    def test_filters_empty_tags(self):
        assert extract_hashtags({"hashtags": [{"tag": "ai"}, {"tag": ""}, {"tag": "x"}]}) == [
            "ai",
            "x",
        ]


class TestExtractMentions:
    def test_mentions(self):
        entities = {"mentions": [{"username": "alice"}, {"username": "bob"}]}
        assert extract_mentions(entities) == ["@alice", "@bob"]

    def test_empty(self):
        assert extract_mentions({"mentions": []}) == []

    def test_missing_key(self):
        assert extract_mentions({}) == []


class TestExtractUrls:
    def test_expanded_urls(self):
        entities = {
            "urls": [
                {"url": "https://t.co/abc", "expanded_url": "https://example.com/page"},
            ]
        }
        assert extract_urls(entities) == ["https://example.com/page"]

    def test_fallback_to_short(self):
        assert extract_urls({"urls": [{"url": "https://t.co/abc"}]}) == ["https://t.co/abc"]

    def test_empty(self):
        assert extract_urls({"urls": []}) == []


class TestDetectLanguage:
    def test_uses_api_lang(self):
        assert detect_language("text", "en") == "en"

    def test_uses_api_spanish(self):
        assert detect_language("text", "es") == "es"

    def test_ignores_undefined(self):
        assert detect_language("Hello world", "und") == "en"

    def test_none_api_defaults_english(self):
        assert detect_language("Hello world", None) == "en"

    def test_empty_returns_none(self):
        assert detect_language("", None) is None

    def test_whitespace_returns_none(self):
        assert detect_language("   ", None) is None


class TestExtractEntitiesFromText:
    """Tests for text-based entity extraction (used by LinkedIn normalizer)."""

    def test_extracts_hashtags(self) -> None:
        hashtags, _, _ = extract_entities_from_text("Excited about #AI and #CodeReview")
        assert hashtags == ["AI", "CodeReview"]

    def test_extracts_mentions(self) -> None:
        _, mentions, _ = extract_entities_from_text("Thanks @alice and @bob")
        assert mentions == ["@alice", "@bob"]

    def test_extracts_urls(self) -> None:
        _, _, urls = extract_entities_from_text("Check https://example.com for details")
        assert urls == ["https://example.com"]

    def test_empty_text(self) -> None:
        hashtags, mentions, urls = extract_entities_from_text("")
        assert hashtags == []
        assert mentions == []
        assert urls == []


class TestNormalizeLinkedInPost:
    """Tests for NormalizerStage._normalize_linkedin_post."""

    def test_normalize_linkedin_post(self, db_session: object) -> None:
        """Normalizer handles LinkedIn post format."""
        from signalops.storage.database import Project
        from signalops.storage.database import RawPost as RawPostDB

        # Insert project
        project = Project(
            id="test-linkedin",
            name="Test LinkedIn",
            config_path="projects/test.yaml",
            config_hash="abc123",
        )
        db_session.add(project)  # type: ignore[union-attr]
        db_session.commit()  # type: ignore[union-attr]

        # Insert a LinkedIn raw post
        raw_post = RawPostDB(
            project_id="test-linkedin",
            platform="linkedin",
            platform_id="urn:li:share:123456",
            query_used="code review automation",
            raw_json={
                "text": "Excited about #AI and our new code review automation! @spectra",
                "author": {
                    "name": "Jane Doe",
                    "headline": "CTO at TechCo",
                    "connections": 500,
                    "is_premium": True,
                },
                "author_urn": "urn:li:person:789",
                "published_at": "2026-02-20T10:00:00Z",
                "reactions": 42,
                "comments": 8,
                "shares": 5,
                "impressions": 1200,
            },
        )
        db_session.add(raw_post)  # type: ignore[union-attr]
        db_session.commit()  # type: ignore[union-attr]

        stage = NormalizerStage()
        result = stage.run(db_session, "test-linkedin")  # type: ignore[arg-type]

        assert result["processed_count"] == 1
        assert result["skipped_count"] == 0

        from signalops.storage.database import NormalizedPost

        normalized = (
            db_session.query(NormalizedPost)  # type: ignore[union-attr]
            .filter(NormalizedPost.project_id == "test-linkedin")
            .first()
        )
        assert normalized is not None
        assert normalized.platform == "linkedin"
        assert normalized.platform_id == "urn:li:share:123456"
        assert normalized.author_display_name == "Jane Doe"
        assert normalized.author_followers == 500
        assert normalized.likes == 42
        assert normalized.replies == 8
        assert normalized.retweets == 5
        assert "AI" in normalized.hashtags
        assert "@spectra" in normalized.mentions

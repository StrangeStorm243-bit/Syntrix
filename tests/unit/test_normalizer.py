"""Tests for the normalizer stage helper functions."""

from signalops.pipeline.normalizer import (
    clean_text,
    detect_language,
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

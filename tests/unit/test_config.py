"""Tests for the config system: schema validation, YAML loading, env var resolution."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from signalops.config.loader import (
    config_hash,
    get_active_project,
    load_project,
    resolve_project,
    scan_projects,
    set_active_project,
)
from signalops.config.schema import (
    ICPConfig,
    NotificationConfig,
    PersonaConfig,
    ProjectConfig,
    QueryConfig,
    RedisConfig,
    RelevanceRubric,
    ScoringWeights,
    StreamConfig,
)

PROJECTS_DIR = Path(__file__).parent.parent.parent / "projects"


class TestLoadSpectraConfig:
    def test_loads_successfully(self):
        config = load_project(PROJECTS_DIR / "spectra.yaml")
        assert config.project_id == "spectra"
        assert config.project_name == "Spectra AI"

    def test_query_count(self):
        config = load_project(PROJECTS_DIR / "spectra.yaml")
        assert len(config.queries) == 5  # 4 X queries + 1 LinkedIn query

    def test_icp_fields(self):
        config = load_project(PROJECTS_DIR / "spectra.yaml")
        assert config.icp.min_followers == 200
        assert config.icp.languages == ["en"]
        assert "bot" in config.icp.exclude_bios_containing
        assert "engineer" in config.icp.prefer_bios_containing

    def test_persona_fields(self):
        config = load_project(PROJECTS_DIR / "spectra.yaml")
        assert config.persona.name == "Alex from Spectra"
        assert config.persona.tone == "helpful"

    def test_scoring_weights(self):
        config = load_project(PROJECTS_DIR / "spectra.yaml")
        assert config.scoring.relevance_judgment == 0.35
        assert config.scoring.author_authority == 0.25

    def test_relevance_rubric(self):
        config = load_project(PROJECTS_DIR / "spectra.yaml")
        assert len(config.relevance.positive_signals) > 0
        assert len(config.relevance.negative_signals) > 0
        assert "hiring" in config.relevance.keywords_excluded

    def test_templates(self):
        config = load_project(PROJECTS_DIR / "spectra.yaml")
        assert len(config.templates) == 2
        assert config.templates[0].id == "pain_point"

    def test_rate_limits(self):
        config = load_project(PROJECTS_DIR / "spectra.yaml")
        assert config.rate_limits["max_replies_per_hour"] == 5
        assert config.rate_limits["max_replies_per_day"] == 20


class TestLoadSaleSenseConfig:
    def test_loads_successfully(self):
        config = load_project(PROJECTS_DIR / "salesense.yaml")
        assert config.project_id == "salesense"
        assert config.project_name == "SaleSense"

    def test_query_count(self):
        config = load_project(PROJECTS_DIR / "salesense.yaml")
        assert len(config.queries) == 4

    def test_different_scoring_weights(self):
        config = load_project(PROJECTS_DIR / "salesense.yaml")
        assert config.scoring.relevance_judgment == 0.30
        assert config.scoring.author_authority == 0.30

    def test_persona(self):
        config = load_project(PROJECTS_DIR / "salesense.yaml")
        assert config.persona.name == "Jordan from SaleSense"
        assert config.persona.tone == "curious"

    def test_all_fields_present(self):
        config = load_project(PROJECTS_DIR / "salesense.yaml")
        assert config.product_url == "https://salesense.io"
        assert config.notifications.enabled is True
        assert config.llm["temperature"] == 0.4


class TestEnvVarResolution:
    def test_resolves_set_env_var(self, monkeypatch):
        monkeypatch.setenv("DISCORD_WEBHOOK_SPECTRA", "https://discord.com/webhook/123")
        config = load_project(PROJECTS_DIR / "spectra.yaml")
        assert config.notifications.discord_webhook == "https://discord.com/webhook/123"

    def test_unset_env_var_passthrough(self, monkeypatch):
        monkeypatch.delenv("DISCORD_WEBHOOK_SPECTRA", raising=False)
        config = load_project(PROJECTS_DIR / "spectra.yaml")
        assert config.notifications.discord_webhook == "${DISCORD_WEBHOOK_SPECTRA}"

    def test_resolves_slack_webhook(self, monkeypatch):
        monkeypatch.setenv("SLACK_WEBHOOK_SALESENSE", "https://hooks.slack.com/xxx")
        config = load_project(PROJECTS_DIR / "salesense.yaml")
        assert config.notifications.slack_webhook == "https://hooks.slack.com/xxx"


class TestInvalidConfigs:
    def test_missing_project_id(self):
        with pytest.raises(ValidationError):
            ProjectConfig(
                project_name="Test",
                description="Test",
                queries=[QueryConfig(text="test", label="test")],
                relevance=RelevanceRubric(
                    system_prompt="test",
                    positive_signals=["a"],
                    negative_signals=["b"],
                ),
                persona=PersonaConfig(
                    name="Bot",
                    role="tester",
                    tone="helpful",
                    voice_notes="notes",
                    example_reply="reply",
                ),
            )

    def test_missing_queries(self):
        with pytest.raises(ValidationError):
            ProjectConfig(
                project_id="test",
                project_name="Test",
                description="Test",
                relevance=RelevanceRubric(
                    system_prompt="test",
                    positive_signals=["a"],
                    negative_signals=["b"],
                ),
                persona=PersonaConfig(
                    name="Bot",
                    role="tester",
                    tone="helpful",
                    voice_notes="notes",
                    example_reply="reply",
                ),
            )

    def test_missing_relevance(self):
        with pytest.raises(ValidationError):
            ProjectConfig(
                project_id="test",
                project_name="Test",
                description="Test",
                queries=[QueryConfig(text="test", label="test")],
                persona=PersonaConfig(
                    name="Bot",
                    role="tester",
                    tone="helpful",
                    voice_notes="notes",
                    example_reply="reply",
                ),
            )

    def test_missing_persona(self):
        with pytest.raises(ValidationError):
            ProjectConfig(
                project_id="test",
                project_name="Test",
                description="Test",
                queries=[QueryConfig(text="test", label="test")],
                relevance=RelevanceRubric(
                    system_prompt="test",
                    positive_signals=["a"],
                    negative_signals=["b"],
                ),
            )


class TestDefaultValues:
    def test_icp_defaults(self):
        icp = ICPConfig()
        assert icp.min_followers == 100
        assert icp.max_followers is None
        assert icp.verified_only is False
        assert icp.languages == ["en"]
        assert icp.exclude_bios_containing == []
        assert icp.prefer_bios_containing == []

    def test_scoring_weights_defaults(self):
        w = ScoringWeights()
        assert w.relevance_judgment == 0.35
        assert w.author_authority == 0.25
        assert w.engagement_signals == 0.15
        assert w.recency == 0.15
        assert w.intent_strength == 0.10

    def test_scoring_weights_sum_to_one(self):
        w = ScoringWeights()
        total = (
            w.relevance_judgment
            + w.author_authority
            + w.engagement_signals
            + w.recency
            + w.intent_strength
        )
        assert abs(total - 1.0) < 0.01

    def test_notification_defaults(self):
        n = NotificationConfig()
        assert n.enabled is False
        assert n.min_score_to_notify == 70
        assert n.discord_webhook is None
        assert n.slack_webhook is None

    def test_query_defaults(self):
        q = QueryConfig(text="test", label="test")
        assert q.enabled is True
        assert q.max_results_per_run == 100


class TestConfigHash:
    def test_same_file_same_hash(self):
        path = PROJECTS_DIR / "spectra.yaml"
        h1 = config_hash(path)
        h2 = config_hash(path)
        assert h1 == h2

    def test_different_files_different_hash(self):
        h1 = config_hash(PROJECTS_DIR / "spectra.yaml")
        h2 = config_hash(PROJECTS_DIR / "salesense.yaml")
        assert h1 != h2

    def test_hash_is_hex_string(self):
        h = config_hash(PROJECTS_DIR / "spectra.yaml")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


class TestRedisConfigDefaults:
    def test_defaults(self) -> None:
        rc = RedisConfig()
        assert rc.url == "redis://localhost:6379/0"
        assert rc.enabled is False
        assert rc.search_cache_ttl == 1800
        assert rc.dedup_ttl == 86400
        assert rc.rate_limit_ttl == 900

    def test_custom_values(self) -> None:
        rc = RedisConfig(url="redis://custom:6379/1", enabled=True, dedup_ttl=3600)
        assert rc.url == "redis://custom:6379/1"
        assert rc.enabled is True
        assert rc.dedup_ttl == 3600


class TestStreamConfigDefaults:
    def test_defaults(self) -> None:
        sc = StreamConfig()
        assert sc.enabled is False
        assert sc.rules == []
        assert sc.backfill_minutes == 5

    def test_custom_values(self) -> None:
        sc = StreamConfig(enabled=True, rules=["python", "rust"], backfill_minutes=10)
        assert sc.enabled is True
        assert len(sc.rules) == 2
        assert sc.backfill_minutes == 10


class TestProjectConfigNewFields:
    def test_redis_default_in_project(self) -> None:
        """ProjectConfig should have Redis with defaults when not specified."""
        config = load_project(PROJECTS_DIR / "spectra.yaml")
        assert config.redis.enabled is False
        assert config.redis.url == "redis://localhost:6379/0"

    def test_stream_default_in_project(self) -> None:
        config = load_project(PROJECTS_DIR / "spectra.yaml")
        assert config.stream.enabled is False
        assert config.stream.rules == []


class TestScanProjects:
    def test_finds_all_projects(self) -> None:
        configs = scan_projects(PROJECTS_DIR)
        assert len(configs) >= 2
        ids = [c.project_id for c in configs]
        assert "spectra" in ids
        assert "salesense" in ids

    def test_empty_dir(self, tmp_path: Path) -> None:
        configs = scan_projects(tmp_path)
        assert configs == []

    def test_nonexistent_dir(self, tmp_path: Path) -> None:
        configs = scan_projects(tmp_path / "nonexistent")
        assert configs == []

    def test_skips_invalid_yaml(self, tmp_path: Path) -> None:
        # Create a valid and an invalid config
        valid = {
            "project_id": "valid",
            "project_name": "Valid",
            "description": "Test",
            "queries": [{"text": "q1", "label": "Q1"}],
            "relevance": {
                "system_prompt": "test",
                "positive_signals": ["a"],
                "negative_signals": ["b"],
            },
            "persona": {
                "name": "Bot",
                "role": "t",
                "tone": "t",
                "voice_notes": "t",
                "example_reply": "t",
            },
        }
        (tmp_path / "valid.yaml").write_text(yaml.dump(valid))
        (tmp_path / "invalid.yaml").write_text("not: valid: project: config\n  bad indentation")

        configs = scan_projects(tmp_path)
        assert len(configs) == 1
        assert configs[0].project_id == "valid"


class TestActiveProject:
    def test_set_and_get(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("signalops.config.loader.DEFAULT_CREDENTIALS_DIR", tmp_path)
        set_active_project("my-project")
        assert get_active_project() == "my-project"

    def test_get_when_not_set(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("signalops.config.loader.DEFAULT_CREDENTIALS_DIR", tmp_path)
        assert get_active_project() is None

    def test_overwrite(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("signalops.config.loader.DEFAULT_CREDENTIALS_DIR", tmp_path)
        set_active_project("first")
        set_active_project("second")
        assert get_active_project() == "second"


class TestResolveProject:
    def test_resolve_by_name(self) -> None:
        config = resolve_project("spectra", projects_dir=PROJECTS_DIR)
        assert config.project_id == "spectra"

    def test_resolve_by_active(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("signalops.config.loader.DEFAULT_CREDENTIALS_DIR", tmp_path)
        set_active_project("spectra")
        config = resolve_project(projects_dir=PROJECTS_DIR)
        assert config.project_id == "spectra"

    def test_resolve_no_project_raises(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("signalops.config.loader.DEFAULT_CREDENTIALS_DIR", tmp_path)
        with pytest.raises(ValueError, match="No project specified"):
            resolve_project(projects_dir=PROJECTS_DIR)

    def test_resolve_nonexistent_raises(self) -> None:
        with pytest.raises(FileNotFoundError, match="not found"):
            resolve_project("nonexistent", projects_dir=PROJECTS_DIR)

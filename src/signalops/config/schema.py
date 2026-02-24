"""Pydantic models for project configuration (project.yaml)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, field_validator


class QueryConfig(BaseModel):
    """A single search query definition."""

    text: str  # X API search query syntax
    label: str  # Human-readable name
    enabled: bool = True
    max_results_per_run: int = 100


class ICPConfig(BaseModel):
    """Ideal Customer Profile filters."""

    min_followers: int = 100
    max_followers: int | None = None  # None = no cap
    verified_only: bool = False
    languages: list[str] = ["en"]
    exclude_bios_containing: list[str] = []
    prefer_bios_containing: list[str] = []


class RelevanceRubric(BaseModel):
    """Rubric for judging tweet relevance."""

    system_prompt: str  # Injected into judge LLM call
    positive_signals: list[str]  # Things that make a post relevant
    negative_signals: list[str]  # Things that make a post irrelevant
    keywords_required: list[str] = []  # At least one must appear (safety net)
    keywords_excluded: list[str] = []  # Auto-reject if any appear


class ScoringWeights(BaseModel):
    """Weights for lead scoring components. Should sum to ~1.0."""

    relevance_judgment: float = 0.35
    author_authority: float = 0.25
    engagement_signals: float = 0.15
    recency: float = 0.15
    intent_strength: float = 0.10


class PersonaConfig(BaseModel):
    """Bot persona for outreach replies."""

    name: str  # Bot persona name
    role: str  # e.g., "technical advisor"
    tone: str  # "helpful", "curious", "expert"
    voice_notes: str  # Free-text style guide
    example_reply: str  # One-shot example for LLM


class TemplateConfig(BaseModel):
    """Reply template definition."""

    id: str
    name: str
    template: str  # Jinja2 template with {{variables}}
    use_when: str  # Condition description


class NotificationConfig(BaseModel):
    """Webhook notification settings."""

    enabled: bool = False
    min_score_to_notify: int = 70
    discord_webhook: str | None = None
    slack_webhook: str | None = None


class RedisConfig(BaseModel):
    """Redis caching configuration. Disabled by default — falls back to in-memory."""

    url: str = "redis://localhost:6379/0"
    enabled: bool = False
    search_cache_ttl: int = 1800  # 30 min
    dedup_ttl: int = 86400  # 24 hours
    rate_limit_ttl: int = 900  # 15 min


class StreamConfig(BaseModel):
    """Filtered Stream configuration (requires X API Pro tier)."""

    enabled: bool = False
    rules: list[str] = []
    backfill_minutes: int = 5


class LLMConfig(BaseModel):
    """LLM configuration — powered by LiteLLM."""

    judge_model: str = "claude-sonnet-4-6"
    draft_model: str = "claude-sonnet-4-6"
    temperature: float = 0.3
    max_tokens: int = 1024
    fallback_models: list[str] = []
    judge_fallback_model: str | None = None
    max_judge_latency_ms: float = 5000


class ExperimentConfig(BaseModel):
    """A/B testing configuration."""

    enabled: bool = False
    default_canary_pct: float = 0.1


class ProjectConfig(BaseModel):
    """Top-level project configuration loaded from project.yaml."""

    project_id: str
    project_name: str
    description: str
    product_url: str | None = None
    queries: list[QueryConfig]
    icp: ICPConfig = ICPConfig()
    relevance: RelevanceRubric
    scoring: ScoringWeights = ScoringWeights()
    persona: PersonaConfig
    templates: list[TemplateConfig] = []
    notifications: NotificationConfig = NotificationConfig()
    redis: RedisConfig = RedisConfig()
    stream: StreamConfig = StreamConfig()
    rate_limits: dict[str, Any] = {"max_replies_per_hour": 5, "max_replies_per_day": 20}
    llm: LLMConfig = LLMConfig()
    experiments: ExperimentConfig = ExperimentConfig()

    @field_validator("llm", mode="before")
    @classmethod
    def _coerce_llm(cls, v: Any) -> Any:
        """Backward compatibility: coerce raw dicts into LLMConfig."""
        if isinstance(v, dict):
            return LLMConfig(**v)
        return v

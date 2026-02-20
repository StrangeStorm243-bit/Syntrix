"""Stub — real implementation on feat/data branch. Will be replaced at merge."""
from pydantic import BaseModel


class QueryConfig(BaseModel):
    text: str
    label: str
    enabled: bool = True
    max_results_per_run: int = 100


class ICPConfig(BaseModel):
    min_followers: int = 100
    max_followers: int | None = None
    verified_only: bool = False
    languages: list[str] = ["en"]
    exclude_bios_containing: list[str] = []
    prefer_bios_containing: list[str] = []


class RelevanceRubric(BaseModel):
    system_prompt: str
    positive_signals: list[str]
    negative_signals: list[str]
    keywords_required: list[str] = []
    keywords_excluded: list[str] = []


class ScoringWeights(BaseModel):
    relevance_judgment: float = 0.35
    author_authority: float = 0.25
    engagement_signals: float = 0.15
    recency: float = 0.15
    intent_strength: float = 0.10


class PersonaConfig(BaseModel):
    name: str
    role: str
    tone: str
    voice_notes: str
    example_reply: str


class TemplateConfig(BaseModel):
    id: str
    name: str
    template: str
    use_when: str


class NotificationConfig(BaseModel):
    enabled: bool = False
    min_score_to_notify: int = 70
    discord_webhook: str | None = None
    slack_webhook: str | None = None


class ProjectConfig(BaseModel):
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
    rate_limits: dict = {"max_replies_per_hour": 5, "max_replies_per_day": 20}
    llm: dict = {"judge_model": "claude-sonnet-4-6", "draft_model": "claude-sonnet-4-6"}

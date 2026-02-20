# Terminal B — Intelligence Layer

> **Branch:** `feat/intel`
> **Role:** You build all AI processing: LLM gateway, providers, relevance judging, lead scoring, and draft generation.
> **You are one of 3 parallel terminals. Terminal A is building config/storage/connectors. Terminal C is building CLI/orchestration. You all work on separate branches simultaneously.**

---

## FIRST STEP — Run this immediately

```bash
git checkout feat/intel
```

---

## RULES

1. **ONLY create/edit files listed in the File Ownership section below.** Do NOT touch any other files.
2. **Commit after each phase** with the exact commit message provided.
3. **Run tests after each phase** before moving to the next.
4. **Use parallel tool calls** — when creating independent files (e.g., anthropic.py + openai.py), write them all in one message.
5. **Run tests in background** — use `Bash(run_in_background=true)` for pytest while you continue writing the next phase's files.
6. **Use Task sub-agents** for complex files — spawn a sub-agent for llm_gateway.py or judge_model.py if needed.

---

## CRITICAL: Handling Imports from Terminal A's Code

Terminal A is building `config/schema.py`, `storage/database.py`, and `connectors/base.py` on a parallel branch. Those files DO NOT EXIST on your branch yet. You must handle this carefully.

### Strategy: Stub files for type checking + runtime compatibility

**Before writing any of your own files, create these minimal stub files so your imports work at runtime:**

### Stub File: `src/signalops/config/schema.py` (MINIMAL STUB)

```python
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
```

### Stub File: `src/signalops/storage/database.py` (MINIMAL STUB)

```python
"""Stub — real implementation on feat/data branch. Will be replaced at merge."""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SAEnum, func
from sqlalchemy.orm import DeclarativeBase
import enum

class Base(DeclarativeBase):
    pass

class JudgmentLabel(enum.Enum):
    RELEVANT = "relevant"
    IRRELEVANT = "irrelevant"
    MAYBE = "maybe"

class DraftStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    EDITED = "edited"
    REJECTED = "rejected"
    SENT = "sent"
    FAILED = "failed"

class NormalizedPost(Base):
    __tablename__ = "normalized_posts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    raw_post_id = Column(Integer)
    project_id = Column(String(64))
    platform = Column(String(32))
    platform_id = Column(String(64))
    author_id = Column(String(64))
    author_username = Column(String(256))
    author_display_name = Column(String(256))
    author_followers = Column(Integer, default=0)
    author_verified = Column(Boolean, default=False)
    text_original = Column(Text)
    text_cleaned = Column(Text)
    language = Column(String(8))
    created_at = Column(DateTime)
    reply_to_id = Column(String(64))
    conversation_id = Column(String(64))
    likes = Column(Integer, default=0)
    retweets = Column(Integer, default=0)
    replies = Column(Integer, default=0)
    views = Column(Integer, default=0)
    hashtags = Column(JSON)
    mentions = Column(JSON)
    urls = Column(JSON)

class Judgment(Base):
    __tablename__ = "judgments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    normalized_post_id = Column(Integer)
    project_id = Column(String(64))
    label = Column(SAEnum(JudgmentLabel))
    confidence = Column(Float)
    reasoning = Column(Text)
    model_id = Column(String(128))
    model_version = Column(String(64))
    latency_ms = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
    human_label = Column(SAEnum(JudgmentLabel))
    human_corrected_at = Column(DateTime)
    human_reason = Column(Text)

class Score(Base):
    __tablename__ = "scores"
    id = Column(Integer, primary_key=True, autoincrement=True)
    normalized_post_id = Column(Integer)
    project_id = Column(String(64))
    total_score = Column(Float)
    components = Column(JSON)
    scoring_version = Column(String(64))
    created_at = Column(DateTime, server_default=func.now())

class Draft(Base):
    __tablename__ = "drafts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    normalized_post_id = Column(Integer)
    project_id = Column(String(64))
    text_generated = Column(Text)
    text_final = Column(Text)
    tone = Column(String(64))
    template_used = Column(String(128))
    model_id = Column(String(128))
    status = Column(SAEnum(DraftStatus), default=DraftStatus.PENDING)
    created_at = Column(DateTime, server_default=func.now())
    approved_at = Column(DateTime)
    sent_at = Column(DateTime)
    sent_post_id = Column(String(64))

def get_engine(db_url="sqlite:///signalops.db"):
    from sqlalchemy import create_engine
    return create_engine(db_url, echo=False)

def get_session(engine):
    from sqlalchemy.orm import sessionmaker
    return sessionmaker(bind=engine)()

def init_db(engine):
    Base.metadata.create_all(engine)
```

**Create these stub files FIRST, then proceed with your actual files.**

At merge time, Terminal A's real implementations will overwrite these stubs (git will handle this as a merge conflict — take Terminal A's version for these two files).

---

## FILE OWNERSHIP (14 files you build + 2 stubs)

```
# YOUR STUBS (will be replaced at merge by Terminal A's real versions):
src/signalops/config/schema.py           ← STUB
src/signalops/storage/database.py        ← STUB

# YOUR REAL FILES:
src/signalops/models/providers/base.py
src/signalops/models/providers/anthropic.py
src/signalops/models/providers/openai.py
src/signalops/models/llm_gateway.py
src/signalops/models/judge_model.py
src/signalops/models/fallback.py
src/signalops/models/draft_model.py
src/signalops/pipeline/judge.py
src/signalops/pipeline/scorer.py
src/signalops/pipeline/drafter.py
tests/unit/test_judge.py
tests/unit/test_scorer.py
tests/unit/test_drafter.py
tests/fixtures/eval_set.jsonl
```

---

## PHASE B1: LLM Infrastructure

### File 1: `src/signalops/models/providers/base.py`

```python
# Abstract base class for LLM providers:
#
# @dataclass
# class ProviderConfig:
#     api_key: str
#     model: str
#     temperature: float = 0.3
#     max_tokens: int = 1024
#     timeout: float = 30.0
#
# class LLMProvider(ABC):
#     @abstractmethod
#     def __init__(self, config: ProviderConfig): ...
#
#     @abstractmethod
#     def complete(self, system_prompt: str, user_prompt: str,
#                  temperature: float | None = None,
#                  max_tokens: int | None = None) -> str:
#         """Returns raw text completion."""
#
#     @abstractmethod
#     def complete_json(self, system_prompt: str, user_prompt: str,
#                       response_schema: dict | None = None) -> dict:
#         """Returns parsed JSON from LLM. Handles parsing errors."""
#
#     @property
#     @abstractmethod
#     def model_id(self) -> str:
#         """Returns the model identifier string."""
```

### File 2: `src/signalops/models/providers/anthropic.py`

```python
# class AnthropicProvider(LLMProvider):
#     Uses the `anthropic` SDK (import anthropic)
#     __init__: create anthropic.Anthropic client with api_key
#
#     complete(): call client.messages.create(
#         model=self.config.model,
#         max_tokens=max_tokens or self.config.max_tokens,
#         system=system_prompt,
#         messages=[{"role": "user", "content": user_prompt}],
#         temperature=temperature or self.config.temperature,
#     )
#     Return response.content[0].text
#
#     complete_json(): call complete() then json.loads() the response
#         If JSON parsing fails, try to extract JSON from markdown code blocks
#         If still fails, raise ValueError with raw response
#
#     model_id: return self.config.model
#
# Supported models: "claude-sonnet-4-6", "claude-haiku-4-5", "claude-opus-4-6"
```

### File 3: `src/signalops/models/providers/openai.py`

```python
# class OpenAIProvider(LLMProvider):
#     Uses the `openai` SDK (import openai)
#     __init__: create openai.OpenAI client with api_key
#
#     complete(): call client.chat.completions.create(
#         model=self.config.model,
#         messages=[
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": user_prompt}
#         ],
#         temperature=temperature or self.config.temperature,
#         max_tokens=max_tokens or self.config.max_tokens,
#     )
#     Return response.choices[0].message.content
#
#     complete_json(): same as complete() but add:
#         response_format={"type": "json_object"}
#         Then json.loads() the response
#
#     model_id: return self.config.model
#
# Supported models: "gpt-4o", "gpt-4o-mini"
```

### File 4: `src/signalops/models/llm_gateway.py`

```python
# class LLMGateway:
#     """Routes LLM calls to the right provider. Handles retries and circuit breaking."""
#
#     __init__(self, anthropic_api_key: str | None = None,
#              openai_api_key: str | None = None,
#              default_model: str = "claude-sonnet-4-6"):
#         Initialize providers dict (lazy — only create when first used)
#         self._providers: dict[str, LLMProvider] = {}
#         self._circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
#         self._default_model = default_model
#
#     def _get_provider(self, model: str) -> LLMProvider:
#         Route based on prefix:
#         - "claude-*" -> AnthropicProvider
#         - "gpt-*" -> OpenAIProvider
#         Cache provider instances
#
#     def complete(self, system_prompt, user_prompt, model=None, **kwargs) -> str:
#         model = model or self._default_model
#         Retry logic: up to 3 attempts with exponential backoff (1s, 2s, 4s)
#         Check circuit breaker before each attempt
#         On success: record success with circuit breaker
#         On failure: record failure, if all retries exhausted raise
#
#     def complete_json(self, system_prompt, user_prompt, model=None, **kwargs) -> dict:
#         Same retry logic as complete(), but calls provider.complete_json()
#
# class CircuitBreaker:
#     """Trips after N failures, stays open for recovery_timeout seconds."""
#     __init__(self, failure_threshold=5, recovery_timeout=60)
#     record_success(self): reset failure count
#     record_failure(self): increment failure count, trip if threshold reached
#     is_open(self) -> bool: True if tripped and not yet recovered
#     @property state -> "closed" | "open" | "half-open"
```

**After creating Phase B1 files, run:**
```bash
pytest tests/ -v 2>/dev/null || echo "No tests yet for B1 — that's OK, providers are tested via integration in later phases"
```

**Commit:**
```
feat(models): LLM gateway with Anthropic/OpenAI providers and circuit breaker
```

---

## PHASE B2: Judge System

### File 5: `src/signalops/models/judge_model.py`

```python
# --- Data classes ---
#
# @dataclass
# class Judgment:
#     label: str              # "relevant", "irrelevant", "maybe"
#     confidence: float       # 0.0 - 1.0
#     reasoning: str          # Why this label was chosen
#     model_id: str           # "claude-sonnet-4-6", "ft-relevance-v2", "tfidf-fallback"
#     latency_ms: float
#
# --- Abstract base ---
#
# class RelevanceJudge(ABC):
#     @abstractmethod
#     def judge(self, post_text: str, author_bio: str,
#               project_context: dict) -> Judgment:
#         """Judge whether a post is relevant to the project."""
#
#     @abstractmethod
#     def judge_batch(self, items: list[dict]) -> list[Judgment]:
#         """Batch judgment for efficiency."""
#
# --- LLM Implementation ---
#
# class LLMPromptJudge(RelevanceJudge):
#     __init__(self, gateway: LLMGateway, model: str = "claude-sonnet-4-6")
#
#     judge(self, post_text, author_bio, project_context) -> Judgment:
#         Build system prompt using project_context (see JUDGE PROMPT TEMPLATE below)
#         Build user prompt with post_text, author_bio, metrics
#         Call gateway.complete_json() to get structured response
#         Parse response into Judgment dataclass
#         Track latency (time.perf_counter before/after)
#         On JSON parse failure: return Judgment with label="maybe", confidence=0.3, model_id="fallback-parse-error"
#
#     judge_batch(self, items) -> list[Judgment]:
#         Call judge() for each item (can be parallelized later)
#
#     _build_system_prompt(self, project_context: dict) -> str:
#         See JUDGE PROMPT TEMPLATE below
#
#     _build_user_prompt(self, post_text, author_bio, metrics=None) -> str:
#         Format post text, author info, metrics into a structured prompt
#
# --- Keyword Fallback Implementation ---
#
# class KeywordFallbackJudge(RelevanceJudge):
#     __init__(self, keywords_required: list[str], keywords_excluded: list[str])
#
#     judge(self, post_text, author_bio, project_context) -> Judgment:
#         If any excluded keyword found: return irrelevant, confidence=0.9
#         If keywords_required is non-empty and none found: return irrelevant, confidence=0.7
#         Otherwise: return maybe, confidence=0.4
#         model_id = "keyword-fallback"
#
#     judge_batch: call judge() for each item
```

**JUDGE PROMPT TEMPLATE** (build this in `_build_system_prompt`):

```
System: You are a relevance judge for {project_name}. {project_description}

{relevance.system_prompt}

Positive signals that make a tweet RELEVANT:
{for signal in relevance.positive_signals}
- {signal}
{endfor}

Negative signals that make a tweet IRRELEVANT:
{for signal in relevance.negative_signals}
- {signal}
{endfor}

Evaluate the following tweet and respond with ONLY valid JSON:
{
  "label": "relevant" | "irrelevant" | "maybe",
  "confidence": 0.0 to 1.0,
  "reasoning": "1-2 sentence explanation"
}

User: Tweet: "{post.text_cleaned}"
Author: @{post.author_username} ({post.author_followers} followers)
Author bio: "{author_bio}"
Posted: {post.created_at}
Engagement: {post.likes} likes, {post.replies} replies, {post.retweets} retweets
```

### File 6: `src/signalops/models/fallback.py`

```python
# class TFIDFFallbackClassifier:
#     """Offline TF-IDF + LogisticRegression classifier as fallback when LLM is unavailable."""
#
#     __init__(self):
#         self.vectorizer = None  # TfidfVectorizer
#         self.classifier = None  # LogisticRegression
#         self.is_trained = False
#
#     train(self, texts: list[str], labels: list[str]) -> dict:
#         """Train from labeled examples. Returns training metrics."""
#         from sklearn.feature_extraction.text import TfidfVectorizer
#         from sklearn.linear_model import LogisticRegression
#         from sklearn.model_selection import cross_val_score
#         Fit vectorizer and classifier
#         Return {"accuracy": mean_cv_score, "n_examples": len(texts)}
#
#     predict(self, text: str) -> tuple[str, float]:
#         """Returns (label, confidence)."""
#         If not trained: raise RuntimeError("Classifier not trained")
#         Transform text, predict with predict_proba
#         Return (predicted_label, max_probability)
#
#     save(self, path: str) -> None:
#         """Serialize model with joblib."""
#         import joblib
#         joblib.dump({"vectorizer": self.vectorizer, "classifier": self.classifier}, path)
#
#     load(self, path: str) -> None:
#         """Load serialized model."""
#         import joblib
#         data = joblib.load(path)
#         self.vectorizer = data["vectorizer"]
#         self.classifier = data["classifier"]
#         self.is_trained = True
#
# NOTE: sklearn and joblib are optional dependencies. Import them inside methods.
# If not installed, raise ImportError with helpful message.
```

### File 7: `src/signalops/pipeline/judge.py`

```python
# class JudgeStage:
#     """Pipeline stage that judges relevance of normalized posts."""
#
#     __init__(self, judge: RelevanceJudge, db_session: Session)
#
#     run(self, project_id: str, config: ProjectConfig, dry_run: bool = False) -> dict:
#         1. Query NormalizedPosts for this project that don't have a Judgment yet
#         2. For each post:
#             a. FIRST: Apply keyword exclusion rules (cheap filter)
#                If any keyword from config.relevance.keywords_excluded found in text_cleaned:
#                    Create Judgment with label=IRRELEVANT, confidence=0.95, model_id="keyword-exclude"
#                    Skip LLM call
#             b. THEN: Call judge.judge(post.text_cleaned, author_bio, project_context)
#             c. Store Judgment row in DB
#             d. If dry_run: don't store, just count
#         3. Return summary: {total, relevant_count, irrelevant_count, maybe_count, avg_confidence}
#
#     _build_project_context(self, config: ProjectConfig) -> dict:
#         Return dict with project_name, description, relevance rubric fields
```

### File 8: `tests/unit/test_judge.py`

```python
# Test LLMPromptJudge with MOCKED LLM gateway:
#
# - test_parse_valid_judgment: mock gateway returns valid JSON -> correct Judgment fields
# - test_parse_relevant_judgment: label="relevant", confidence=0.85
# - test_parse_irrelevant_judgment: label="irrelevant", confidence=0.92
# - test_parse_maybe_judgment: label="maybe", confidence=0.55
# - test_malformed_json_fallback: mock gateway returns invalid JSON -> Judgment with label="maybe"
# - test_gateway_exception_handling: mock gateway raises -> graceful error handling
# - test_keyword_exclusion_auto_reject: text containing "hiring" with keywords_excluded=["hiring"] -> irrelevant
# - test_keyword_exclusion_case_insensitive: "HIRING" also matches "hiring"
# - test_keywords_required_miss: keywords_required=["code review"] but text has no match -> irrelevant
# - test_keywords_required_hit: keywords_required=["code review"] and text contains it -> continues to LLM
# - test_confidence_range: confidence is always between 0.0 and 1.0
# - test_latency_tracked: latency_ms > 0 in result
# - test_judge_batch: batch of 3 items returns 3 Judgments
# - test_judge_stage_skips_already_judged: posts with existing judgments are not re-judged
#
# Use unittest.mock.MagicMock or unittest.mock.patch for the gateway
# Create a minimal project_context dict for testing
```

**After creating Phase B2 files, run:**
```bash
pytest tests/unit/test_judge.py -v
```

**Commit:**
```
feat(judge): relevance judge with LLM + keyword fallback
```

---

## PHASE B3: Scoring Engine

### File 9: `src/signalops/pipeline/scorer.py`

```python
# class ScorerStage:
#     """Calculates lead scores using weighted criteria."""
#
#     __init__(self, db_session: Session)
#
#     run(self, project_id: str, config: ProjectConfig, dry_run: bool = False) -> dict:
#         1. Query NormalizedPosts + Judgments where label=RELEVANT or MAYBE, and no Score exists yet
#         2. For each post+judgment pair:
#             score = self.compute_score(post, judgment, config)
#             Store Score row with total_score and components breakdown
#         3. Return summary: {scored_count, avg_score, max_score, min_score, above_70_count}
#
#     compute_score(self, post: NormalizedPost, judgment: Judgment,
#                   config: ProjectConfig) -> tuple[float, dict]:
#         """Returns (total_score, components_dict). Total is 0-100."""
#         weights = config.scoring
#
#         # Component 1: Relevance judgment (0-100)
#         relevance_score = self._score_relevance(judgment)
#
#         # Component 2: Author authority (0-100)
#         authority_score = self._score_authority(post, config.icp)
#
#         # Component 3: Engagement signals (0-100)
#         engagement_score = self._score_engagement(post)
#
#         # Component 4: Recency (0-100)
#         recency_score = self._score_recency(post.created_at)
#
#         # Component 5: Intent strength (0-100)
#         intent_score = self._score_intent(post.text_cleaned)
#
#         components = {
#             "relevance_judgment": relevance_score,
#             "author_authority": authority_score,
#             "engagement_signals": engagement_score,
#             "recency": recency_score,
#             "intent_strength": intent_score,
#         }
#
#         total = (
#             relevance_score * weights.relevance_judgment +
#             authority_score * weights.author_authority +
#             engagement_score * weights.engagement_signals +
#             recency_score * weights.recency +
#             intent_score * weights.intent_strength
#         )
#
#         return total, components
#
#     _score_relevance(self, judgment) -> float:
#         """confidence * label_multiplier. relevant=1.0, maybe=0.3, irrelevant=0.0"""
#         multiplier = {"relevant": 1.0, "maybe": 0.3, "irrelevant": 0.0}
#         return judgment.confidence * multiplier.get(judgment.label.value, 0) * 100
#
#     _score_authority(self, post, icp) -> float:
#         """Normalized score from followers, verified, bio match."""
#         score = 0.0
#         # Followers: log scale, cap at 100
#         import math
#         if post.author_followers > 0:
#             score += min(math.log10(post.author_followers) / 6 * 60, 60)  # 1M followers = 60
#         # Verified bonus: +20
#         if post.author_verified:
#             score += 20
#         # Bio match: +20 if any prefer_bios_containing keyword found
#         # (check against author_display_name or a bio field if available)
#         # For now, simplified: give 10 points baseline for having a profile
#         score += 10
#         return min(score, 100)
#
#     _score_engagement(self, post) -> float:
#         """Normalized from likes, replies, retweets, views."""
#         score = 0.0
#         score += min(post.likes * 3, 30)       # 10 likes = 30 points
#         score += min(post.replies * 5, 30)     # 6 replies = 30 points
#         score += min(post.retweets * 4, 20)    # 5 RTs = 20 points
#         score += min((post.views or 0) / 500, 20)  # 10K views = 20 points
#         return min(score, 100)
#
#     _score_recency(self, created_at: datetime) -> float:
#         """Decay: 100 at 0h, ~50 at 24h, ~10 at 72h, 0 at 168h (7 days)."""
#         from datetime import datetime, timezone
#         hours_ago = (datetime.now(timezone.utc) - created_at).total_seconds() / 3600
#         if hours_ago <= 0:
#             return 100.0
#         if hours_ago >= 168:
#             return 0.0
#         # Exponential decay: 100 * e^(-0.03 * hours)
#         import math
#         return max(0, 100 * math.exp(-0.03 * hours_ago))
#
#     _score_intent(self, text: str) -> float:
#         """Detect intent signals in text."""
#         score = 0.0
#         text_lower = text.lower()
#         # Direct questions: +40
#         if "?" in text:
#             score += 40
#         # Active search phrases: +30
#         search_phrases = ["looking for", "anyone recommend", "anyone know",
#                          "suggestions for", "alternative to", "switching from"]
#         if any(phrase in text_lower for phrase in search_phrases):
#             score += 30
#         # Pain expressions: +20
#         pain_phrases = ["frustrated", "annoying", "painful", "hate",
#                        "takes forever", "waste of time", "there has to be"]
#         if any(phrase in text_lower for phrase in pain_phrases):
#             score += 20
#         # Evaluation language: +10
#         eval_phrases = ["evaluating", "comparing", "trying out", "testing"]
#         if any(phrase in text_lower for phrase in eval_phrases):
#             score += 10
#         return min(score, 100)
```

### File 10: `tests/unit/test_scorer.py`

```python
# Test compute_score and each component function:
#
# - test_perfect_score: all signals max -> score between 90-100
# - test_zero_score: irrelevant judgment, 0 followers, 0 engagement, 7 days old, no intent -> score near 0
# - test_zero_followers_no_crash: followers=0 doesn't cause math error
# - test_negative_followers_no_crash: followers=-1 handled gracefully
# - test_weights_sum_to_one: ScoringWeights default values sum to ~1.0
# - test_custom_weights: different weights produce different scores
# - test_recency_decay_recent: 1 hour ago -> recency_score > 90
# - test_recency_decay_day_old: 24 hours ago -> recency_score around 40-60
# - test_recency_decay_old: 72 hours ago -> recency_score < 15
# - test_recency_decay_week_old: 168 hours ago -> recency_score = 0
# - test_intent_detection_question: "Anyone recommend?" -> intent > 0
# - test_intent_detection_search: "looking for a tool" -> intent > 0
# - test_intent_detection_pain: "so frustrated with" -> intent > 0
# - test_intent_detection_none: "Beautiful day today" -> intent = 0
# - test_engagement_high: 50 likes, 20 replies -> engagement > 80
# - test_engagement_zero: all zeros -> engagement = 0
# - test_relevance_relevant_high_conf: relevant + 0.95 -> relevance near 95
# - test_relevance_maybe_low: maybe + 0.5 -> relevance = 15
# - test_relevance_irrelevant: irrelevant -> relevance = 0
# - test_score_range: total is always 0-100
#
# Use mock NormalizedPost and Judgment objects (simple dataclass or namedtuple mocks)
# Use freezegun or manual datetime for recency tests
```

**After creating Phase B3 files, run:**
```bash
pytest tests/unit/test_scorer.py -v
```

**Commit:**
```
feat(scorer): weighted lead scoring engine
```

---

## PHASE B4: Draft Generator

### File 11: `src/signalops/models/draft_model.py`

```python
# --- Data class ---
#
# @dataclass
# class Draft:
#     text: str               # The draft reply text
#     tone: str               # "helpful", "curious", "expert"
#     model_id: str
#     template_used: str | None
#
# --- Abstract base ---
#
# class DraftGenerator(ABC):
#     @abstractmethod
#     def generate(self, post_text: str, author_context: str,
#                  project_context: dict, persona: dict) -> Draft:
#         """Generate a reply draft for a relevant post."""
#
# --- LLM Implementation ---
#
# class LLMDraftGenerator(DraftGenerator):
#     __init__(self, gateway: LLMGateway, model: str = "claude-sonnet-4-6")
#
#     generate(self, post_text, author_context, project_context, persona) -> Draft:
#         Build system prompt using persona (see DRAFT PROMPT TEMPLATE below)
#         Build user prompt with post_text, author_context, project_context
#         Call gateway.complete() (NOT complete_json — drafts are free text)
#         text = response.strip()
#         If len(text) > 240: call gateway.complete() again with "Shorten to under 240 chars"
#         If still > 240: truncate at last word boundary before 240
#         Return Draft(text=text, tone=persona["tone"], model_id=self.model, template_used=None)
#
#     _build_system_prompt(self, persona: dict, project_context: dict) -> str:
#         See DRAFT PROMPT TEMPLATE below
#
#     _build_user_prompt(self, post_text, author_context, project_context) -> str:
#         Format the prompt
```

**DRAFT PROMPT TEMPLATE** (build this in `_build_system_prompt`):

```
System: You are {persona.name}, a {persona.role} for {project_name}.
Your tone is {persona.tone}.

{persona.voice_notes}

Example reply style:
"{persona.example_reply}"

Rules:
- Keep reply under 240 characters
- Be genuinely helpful, not salesy
- Reference something specific from their tweet
- Only mention {project_name} if it's truly relevant to their situation
- No hashtags, no emojis (unless the original poster uses them)
- Sound human, not corporate
- Never use phrases like "I understand your frustration" or "Great question!"

User: Write a reply to this tweet.

Tweet: "{post.text_original}"
Author: @{post.author_username}
Context: They were found via the query "{query_used}" and scored {score}/100.
Relevance reasoning: "{judgment.reasoning}"
```

### File 12: `src/signalops/pipeline/drafter.py`

```python
# class DrafterStage:
#     """Pipeline stage that generates reply drafts for top-scored leads."""
#
#     __init__(self, generator: DraftGenerator, db_session: Session)
#
#     run(self, project_id: str, config: ProjectConfig,
#         top_n: int = 10, min_score: float = 50.0,
#         dry_run: bool = False) -> dict:
#         1. Query Scores joined with NormalizedPosts and Judgments
#            WHERE project_id matches
#            AND total_score >= min_score
#            AND no Draft exists yet for this normalized_post_id
#            ORDER BY total_score DESC
#            LIMIT top_n
#         2. For each scored post:
#             Build author_context (username, followers, bio snippet)
#             Build project_context from config
#             Build persona dict from config.persona
#             draft = generator.generate(post.text_cleaned, author_context, project_context, persona)
#             Create Draft DB row with text_generated=draft.text, status=PENDING
#             If dry_run: don't store, just print what would be generated
#         3. Return summary: {drafted_count, avg_score_of_drafted, skipped_count}
```

### File 13: `tests/unit/test_drafter.py`

```python
# Test LLMDraftGenerator with MOCKED gateway:
#
# - test_generate_basic_draft: mock returns valid text < 240 chars -> correct Draft fields
# - test_character_limit_enforcement: mock returns text > 240 chars -> regenerated/truncated
# - test_persona_injection: verify system prompt contains persona name, role, tone
# - test_voice_notes_in_prompt: verify voice_notes appear in system prompt
# - test_example_reply_in_prompt: verify example_reply appears in system prompt
# - test_project_name_in_prompt: verify project_name appears in system prompt
# - test_tone_field_set: Draft.tone matches persona.tone
# - test_model_id_set: Draft.model_id matches the model used
# - test_draft_stage_min_score_filter: only posts above min_score get drafted
# - test_draft_stage_top_n_limit: only top N posts get drafted
# - test_draft_stage_skips_already_drafted: posts with existing drafts are skipped
# - test_draft_stage_dry_run: dry_run=True doesn't create DB rows
#
# Use unittest.mock for the gateway. Return predefined draft text.
```

### File 14: `tests/fixtures/eval_set.jsonl`

Create 50 labeled examples for offline evaluation. Each line is JSON:

```jsonl
{"text": "Just spent 3 hours reviewing a PR that should have taken 30 minutes. There has to be a better way.", "author_bio": "Senior engineer @BigCorp. Building distributed systems.", "author_followers": 2340, "gold_label": "relevant"}
{"text": "We're hiring! Looking for someone who can do thorough code reviews. Apply now!", "author_bio": "HR Manager at TechCo", "author_followers": 500, "gold_label": "irrelevant"}
{"text": "Anyone recommend a good code review tool for a team of 20?", "author_bio": "CTO at StartupX", "author_followers": 1200, "gold_label": "relevant"}
... (continue with 47 more examples)
```

Distribution: 25 relevant, 20 irrelevant, 5 maybe. Include variety:
- Relevant: pain points, tool searches, competitor frustration, quality complaints
- Irrelevant: hiring posts, jokes/memes, educational mentions, spam, unrelated topics
- Maybe: tangential mentions, unclear intent, non-English with code review topic

**After creating Phase B4 files, run:**
```bash
pytest tests/unit/test_drafter.py -v
pytest tests/unit/ -v  # run all unit tests
```

**Commit:**
```
feat(drafter): LLM draft generator with persona system
```

---

## ALSO CREATE: `tests/conftest.py` (if not already present from skeleton)

Your tests need a DB session fixture. Create a minimal conftest.py:

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from signalops.storage.database import Base, init_db

@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    return engine

@pytest.fixture
def db_session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()
```

---

## FINAL STEP

After all 4 phases are committed, verify everything passes:

```bash
pytest tests/ -v --tb=short
```

Then wait for Terminals A and C to finish. The merge will happen from a separate terminal.

**Your branch `feat/intel` is done when:**
- 2 stub files + 14 real files created
- All tests pass
- 4 commits on the branch
- No files outside your ownership were touched (except the 2 acknowledged stubs)

**At merge time:** Terminal A's real `config/schema.py` and `storage/database.py` will replace your stubs. Your imports of those types will "just work" because your stubs match the same class names and signatures.

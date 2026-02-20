# Configuration Reference

Each project is defined by a YAML file in `projects/`. This page documents every field.

## Minimal Example

```yaml
project_id: my-project
project_name: "My SaaS"
description: "Find leads interested in my product"

queries:
  - text: '"looking for" ("my-feature") -is:retweet lang:en'
    label: "Active search"

relevance:
  system_prompt: "Judge whether this tweet shows interest in my product."
  positive_signals: ["asking for recommendations", "expressing frustration"]
  negative_signals: ["hiring post", "spam"]

persona:
  name: "Alex"
  role: "product specialist"
  tone: "helpful"
  voice_notes: "Be genuine, not salesy."
  example_reply: "Totally get that — happy to show you what we built."
```

---

## Top-Level Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `project_id` | string | Yes | — | Unique project slug |
| `project_name` | string | Yes | — | Display name |
| `description` | string | Yes | — | Project description |
| `product_url` | string | No | `null` | Your product URL |

---

## `queries`

List of X API search queries. At least one is required.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `text` | string | Yes | — | X API search query syntax |
| `label` | string | Yes | — | Human-readable name |
| `enabled` | bool | No | `true` | Whether this query is active |
| `max_results_per_run` | int | No | `100` | Max tweets per run |

```yaml
queries:
  - text: '"code review" (slow OR painful) -is:retweet lang:en'
    label: "Code review pain"
  - text: '"looking for" ("code review tool") -is:retweet lang:en'
    label: "Tool search"
    max_results_per_run: 50
```

---

## `icp` — Ideal Customer Profile

Filters for which authors to consider. All fields are optional.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `min_followers` | int | `100` | Minimum follower count |
| `max_followers` | int | `null` | Maximum follower count (null = no cap) |
| `verified_only` | bool | `false` | Only verified accounts |
| `languages` | list | `["en"]` | Allowed languages |
| `exclude_bios_containing` | list | `[]` | Auto-reject if bio contains any term |
| `prefer_bios_containing` | list | `[]` | Boost score for accounts with these bio terms |

```yaml
icp:
  min_followers: 200
  languages: ["en"]
  exclude_bios_containing: ["bot", "giveaway"]
  prefer_bios_containing: ["engineer", "founder", "CTO"]
```

---

## `relevance` — Judge Rubric

Defines how the LLM judges tweet relevance. Required.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `system_prompt` | string | Yes | — | System prompt for the judge LLM |
| `positive_signals` | list | Yes | — | Signals that indicate relevance |
| `negative_signals` | list | Yes | — | Signals that indicate irrelevance |
| `keywords_required` | list | No | `[]` | At least one must appear (safety net) |
| `keywords_excluded` | list | No | `[]` | Auto-reject if any appear |

---

## `scoring` — Lead Scoring Weights

Weights for the composite lead score (0-100). Should sum to approximately 1.0.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `relevance_judgment` | float | `0.35` | LLM relevance judgment |
| `author_authority` | float | `0.25` | Follower count, verified status |
| `engagement_signals` | float | `0.15` | Likes, retweets, engagement rate |
| `recency` | float | `0.15` | How recent the post is |
| `intent_strength` | float | `0.10` | Purchase/action intent signals |

---

## `persona` — Outreach Persona

Defines the voice used for generating reply drafts. All fields required.

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Bot persona name (e.g., "Alex from Spectra") |
| `role` | string | Role description (e.g., "developer advocate") |
| `tone` | string | Tone keyword (e.g., "helpful", "curious") |
| `voice_notes` | string | Free-text style guide for the LLM |
| `example_reply` | string | One-shot example reply |

---

## `templates`

Optional reply templates. Each template uses Jinja2 syntax.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Template slug |
| `name` | string | Yes | Human-readable name |
| `template` | string | Yes | Jinja2 template with `{{variables}}` |
| `use_when` | string | Yes | When to use this template |

```yaml
templates:
  - id: pain_point
    name: "Pain Point Response"
    template: "{{empathy_statement}} — {{value_prop}}. {{soft_cta}}"
    use_when: "User is expressing frustration with existing tools"
```

---

## `notifications`

Webhook notifications for high-score leads.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `false` | Enable notifications |
| `min_score_to_notify` | int | `70` | Minimum lead score to trigger |
| `discord_webhook` | string | `null` | Discord webhook URL |
| `slack_webhook` | string | `null` | Slack webhook URL |

```yaml
notifications:
  enabled: true
  min_score_to_notify: 75
  discord_webhook: "${DISCORD_WEBHOOK}"
```

---

## `redis`

Optional Redis configuration for caching and deduplication.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `false` | Enable Redis |
| `url` | string | `redis://localhost:6379/0` | Redis connection URL |
| `search_cache_ttl` | int | `1800` | Search cache TTL (seconds) |
| `dedup_ttl` | int | `86400` | Dedup key TTL (seconds) |
| `rate_limit_ttl` | int | `900` | Rate limit state TTL (seconds) |

---

## `stream`

Filtered Stream configuration (requires X API Pro tier).

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `false` | Enable Filtered Stream |
| `rules` | list | `[]` | Stream filter rules |
| `backfill_minutes` | int | `5` | Backfill on reconnect (minutes) |

---

## `rate_limits`

Send throttling configuration.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `max_replies_per_hour` | int | `5` | Maximum replies per hour |
| `max_replies_per_day` | int | `20` | Maximum replies per day |
| `max_replies_per_month` | int | `0` | Maximum per month (0 = disabled) |

---

## `llm`

LLM model selection per pipeline stage.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `judge_model` | string | `claude-sonnet-4-6` | Model for relevance judging |
| `draft_model` | string | `claude-sonnet-4-6` | Model for draft generation |
| `temperature` | float | varies | LLM temperature |

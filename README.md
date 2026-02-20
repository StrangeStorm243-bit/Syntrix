# SignalOps

[![CI](https://github.com/StrangeStorm243-bit/Syntrix/actions/workflows/ci.yml/badge.svg)](https://github.com/StrangeStorm243-bit/Syntrix/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Agentic social lead finder + outreach workbench.** Collect tweets matching keyword queries, judge relevance via LLM, score leads, generate reply drafts, and send human-approved replies — all from the command line.

## Features

- **LLM-powered relevance judging** — Claude or GPT classifies tweets as relevant/irrelevant with confidence scores
- **Weighted lead scoring** (0-100) — combines relevance, author authority, engagement, recency, and intent
- **AI draft generation** — context-aware reply drafts using project persona and tone
- **Human-in-the-loop approval** — approve, edit, or reject every draft before sending
- **Rate-limited sending** — configurable hourly/daily/monthly caps with jitter
- **Outcome tracking** — monitors if replies get liked, replied to, or followed
- **Feedback loop** — human corrections feed training data export (JSONL for fine-tuning)
- **Offline evaluation** — test judge accuracy against labeled datasets
- **Notification webhooks** — Discord/Slack alerts for high-score leads
- **Multi-project support** — switch between project configs with `project set`
- **Redis caching** — optional deduplication and rate limit persistence
- **Filtered Stream** — real-time collection via X API Pro tier

## Quick Start

```bash
pip install signalops

# Set up your X API credentials
export X_BEARER_TOKEN="your-bearer-token"
export ANTHROPIC_API_KEY="your-api-key"

# Set active project
signalops project set spectra

# Run the full pipeline
signalops run all --dry-run

# Review and approve drafts
signalops queue list
signalops queue approve 1

# Send approved replies
signalops queue send --confirm
```

## Project Configuration

Each project is defined by a YAML file in `projects/`. Here's a minimal example:

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

See `projects/spectra.yaml` and `projects/salesense.yaml` for full examples.

## Architecture

```
CLI (Click) -> Orchestrator -> Pipeline stages -> Storage (SQLAlchemy/SQLite)
                                    |
                              LLM Gateway (Anthropic/OpenAI)
```

**Pipeline:** Collect -> Normalize -> Judge -> Score -> Draft -> Approve -> Send

## Development

```bash
git clone https://github.com/StrangeStorm243-bit/Syntrix.git
cd Syntrix
pip install -e ".[dev]"

# Run CI checks
ruff check src/ tests/
ruff format --check src/ tests/
mypy src/signalops --strict
pytest tests/ -v --tb=short
```

## License

[MIT](LICENSE)

# Installation

## Prerequisites

- **Python 3.11+**
- **X (Twitter) API v2 credentials** — Bearer token for search, OAuth 2.0 user token for posting replies
- **LLM API key** — Anthropic (Claude) or OpenAI (GPT)

## Install from PyPI

```bash
pip install signalops
```

## Install from Source

```bash
git clone https://github.com/StrangeStorm243-bit/Syntrix.git
cd Syntrix
pip install -e ".[dev]"
```

The `[dev]` extra includes pytest, mypy, ruff, and other development tools.

## Environment Variables

Set these before running SignalOps:

| Variable | Required | Description |
|----------|----------|-------------|
| `X_BEARER_TOKEN` | Yes | X API v2 bearer token (for search/collect) |
| `X_USER_TOKEN` | For sending | OAuth 2.0 user access token (for posting replies) |
| `ANTHROPIC_API_KEY` | Yes* | Anthropic API key (for Claude models) |
| `OPENAI_API_KEY` | Yes* | OpenAI API key (for GPT models) |

*At least one LLM API key is required. Which one depends on your project's `llm` config.

```bash
export X_BEARER_TOKEN="your-bearer-token"
export ANTHROPIC_API_KEY="your-api-key"
```

Or use a `.env` file in the project root (loaded automatically via `python-dotenv`).

## Optional: Redis

SignalOps can use Redis for deduplication, search caching, and rate limit state persistence. Without Redis, these features fall back to in-memory storage.

```bash
# Start Redis locally
docker run -d -p 6379:6379 redis:7

# Enable in your project config
redis:
  enabled: true
  url: "redis://localhost:6379/0"
```

## Optional: Documentation Site

To build the documentation site locally:

```bash
pip install -e ".[docs]"
mkdocs serve
```

## Verify Installation

```bash
signalops --help
```

You should see the top-level command groups: `project`, `run`, `queue`, `stats`, `export`, `correct`, `eval`.

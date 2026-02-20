# SignalOps

**Agentic social lead finder + outreach workbench.**

SignalOps collects tweets matching keyword queries, judges relevance via LLM, scores leads, generates reply drafts, and sends human-approved replies — all from the command line.

## Who It's For

- **Founders and growth teams** who want to find and engage high-intent leads on X (Twitter)
- **DevRel and developer advocates** monitoring discussions about their tools
- **Sales teams** who want AI-assisted outreach with human oversight

## How It Works

```
Collect → Normalize → Judge → Score → Draft → Approve → Send
```

1. **Collect** tweets matching your search queries via X API v2
2. **Normalize** raw posts into a clean, unified format
3. **Judge** relevance using Claude or GPT with your custom rubric
4. **Score** leads (0-100) based on relevance, authority, engagement, recency, and intent
5. **Draft** context-aware replies using your project persona
6. **Approve** — you review every draft before it goes out
7. **Send** approved replies with rate limiting and jitter

## Key Features

- **LLM-powered relevance judging** — Claude or GPT classifies tweets with confidence scores
- **Weighted lead scoring** (0-100) — relevance, authority, engagement, recency, intent
- **AI draft generation** — context-aware replies matching your persona and tone
- **Human-in-the-loop** — approve, edit, or reject every draft before sending
- **Rate-limited sending** — hourly, daily, and monthly caps with jitter
- **Outcome tracking** — monitors likes, replies, and follows on sent tweets
- **Feedback loop** — human corrections feed training data export (JSONL)
- **Offline evaluation** — test judge accuracy against labeled datasets
- **Multi-project support** — switch between project configs with `project set`
- **Notification webhooks** — Discord/Slack alerts for high-score leads
- **Redis caching** — optional deduplication and rate limit persistence
- **Filtered Stream** — real-time collection via X API Pro tier

## Next Steps

- [Installation](install.md) — prerequisites and setup
- [Quick Start](quickstart.md) — run your first pipeline in 5 minutes
- [CLI Reference](cli-reference.md) — every command documented
- [Configuration](config-reference.md) — full project YAML schema
- [Architecture](architecture.md) — how the pieces fit together

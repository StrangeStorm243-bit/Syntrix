# Quick Start

Run your first lead-finding pipeline in 5 minutes.

## 1. Set Up Credentials

```bash
export X_BEARER_TOKEN="your-bearer-token"
export ANTHROPIC_API_KEY="your-api-key"
```

## 2. Choose a Project

SignalOps ships with two example projects. List them:

```bash
signalops project list
```

Set one as active:

```bash
signalops project set spectra
```

## 3. Preview the Pipeline (Dry Run)

```bash
signalops run all --dry-run
```

This shows what each stage would do without making API calls or writing to the database.

## 4. Run the Full Pipeline

```bash
signalops run all
```

This runs: **collect → normalize → judge → score → draft**.

Each stage prints a summary. You'll see how many tweets were collected, judged relevant, scored, and drafted.

## 5. Review Drafts

```bash
signalops queue list
```

Shows all pending drafts with scores, sorted by lead quality. Each draft has an ID, score, the original tweet author, and the generated reply.

## 6. Approve or Edit Drafts

```bash
# Approve a draft as-is
signalops queue approve 1

# Edit a draft before approving
signalops queue edit 2

# Reject a draft
signalops queue reject 3 --reason "too generic"
```

## 7. Send Approved Replies

Preview what will be sent:

```bash
signalops queue send
```

Actually send (requires `X_USER_TOKEN`):

```bash
signalops queue send --confirm
```

Rate limits from your project config are enforced automatically.

## 8. Check Stats

```bash
signalops stats
```

Shows pipeline throughput, outcome tracking (likes, replies, follows), and training data counts.

## Running Individual Stages

You can run pipeline stages independently:

```bash
signalops run collect       # Collect tweets
signalops run judge         # Judge relevance
signalops run score         # Score leads
signalops run draft --top 5 # Draft replies for top 5
```

## Creating Your Own Project

```bash
signalops project init
```

This walks you through creating a new project config interactively. It generates a YAML file in `projects/` that you can further customize. See [Configuration](config-reference.md) for the full schema.

## Correcting Judgments

Improve the judge over time by correcting mistakes:

```bash
# Correct a specific judgment
signalops correct 42 --label relevant --reason "clearly asking for our product"

# Interactive review session
signalops correct --review --n 20 --strategy low_confidence
```

## Exporting Training Data

```bash
signalops export training-data --type judgments --format openai --output training.jsonl
```

Export formats: `openai` (chat fine-tuning), `dpo` (preference pairs). Data types: `judgments`, `drafts`, `outcomes`.

## Evaluating Judge Accuracy

```bash
signalops eval judge --test-set test_labels.jsonl
signalops eval compare --test-set test_labels.jsonl --models claude-sonnet-4-6,gpt-4o
```

# CLI Reference

## Global Options

All commands accept these flags:

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--project` | `-p` | Active project | Override the active project |
| `--dry-run` | | `False` | Preview without side effects |
| `--verbose` | `-v` | `False` | Enable debug logging |
| `--format` | | `table` | Output format: `table` or `json` |

---

## `project` — Manage Projects

### `project set <name>`

Set the active project. Validates the config file before activating.

```bash
signalops project set spectra
```

### `project list`

List all available projects from `projects/*.yaml`.

```bash
signalops project list
```

### `project init`

Create a new project interactively. Prompts for project ID, name, queries, persona, and relevance rubric. Writes a YAML file to `projects/`.

```bash
signalops project init
```

---

## `run` — Pipeline Stages

### `run all`

Run the full pipeline: collect, normalize, judge, score, draft.

```bash
signalops run all
signalops run all --dry-run
```

### `run collect`

Collect tweets matching the active project's queries via X API v2. Uses a rate limiter (55 requests per 15-minute window).

```bash
signalops run collect
```

### `run judge`

Judge relevance of collected tweets using the configured LLM.

```bash
signalops run judge
```

### `run score`

Score judged tweets using weighted factors. Displays the top 5 leads.

```bash
signalops run score
```

### `run draft`

Generate reply drafts for top-scored leads.

| Flag | Default | Description |
|------|---------|-------------|
| `--top` | `10` | Number of top-scored posts to draft replies for |

```bash
signalops run draft --top 5
```

---

## `queue` — Draft Approval Queue

### `queue list`

Show pending, approved, and edited drafts sorted by score.

```bash
signalops queue list
```

### `queue approve <draft_id>`

Approve a draft for sending.

```bash
signalops queue approve 1
```

### `queue edit <draft_id>`

Edit a draft's text interactively, then approve it.

```bash
signalops queue edit 2
```

### `queue reject <draft_id>`

Reject a draft.

| Flag | Default | Description |
|------|---------|-------------|
| `--reason` | None | Rejection reason |

```bash
signalops queue reject 3 --reason "too salesy"
```

### `queue send`

Send approved drafts as replies. Without `--confirm`, runs in preview mode.

| Flag | Default | Description |
|------|---------|-------------|
| `--confirm` | `False` | Actually send (default is preview only) |

```bash
signalops queue send           # Preview
signalops queue send --confirm # Send for real
```

---

## `stats` — Pipeline Statistics

Show pipeline throughput, outcomes, and training data stats for the active project.

```bash
signalops stats
signalops stats --format json
```

---

## `export` — Data Export

### `export training-data`

Export training data as JSONL for fine-tuning.

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--type` | Yes | — | `judgments`, `drafts`, or `outcomes` |
| `--format` | No | `openai` | `openai` or `dpo` |
| `--output` | No | Auto-named | Output file path |
| `--since` | No | None | Only export after date (YYYY-MM-DD) |
| `--min-confidence` | No | None | Minimum confidence threshold |
| `--include-metadata` | No | `False` | Include export metadata |

```bash
signalops export training-data --type judgments --format openai
signalops export training-data --type drafts --format dpo --output prefs.jsonl
signalops export training-data --type outcomes --since 2025-01-01
```

---

## `correct` — Judgment Correction

Correct LLM judgments to improve accuracy over time.

**Direct mode:**

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `judgment_id` | Yes | ID of the judgment to correct |
| `--label` | Yes | `relevant`, `irrelevant`, or `maybe` |
| `--reason` | No | Reason for the correction |

```bash
signalops correct 42 --label relevant --reason "asking for our product"
```

**Interactive review mode:**

| Flag | Default | Description |
|------|---------|-------------|
| `--review` | `False` | Enter interactive review mode |
| `--n` | `10` | Number of judgments to review |
| `--strategy` | `low_confidence` | Sampling: `low_confidence`, `random`, or `recent` |

```bash
signalops correct --review --n 20 --strategy low_confidence
```

---

## `eval` — Judge Evaluation

### `eval judge`

Evaluate the current judge model against a labeled test set.

| Flag | Required | Description |
|------|----------|-------------|
| `--test-set` | Yes | Path to JSONL test set |

```bash
signalops eval judge --test-set test_labels.jsonl
```

### `eval compare`

Compare multiple judge models on the same test set.

| Flag | Required | Description |
|------|----------|-------------|
| `--test-set` | Yes | Path to JSONL test set |
| `--models` | Yes | Comma-separated model IDs |

```bash
signalops eval compare --test-set test_labels.jsonl --models claude-sonnet-4-6,gpt-4o
```

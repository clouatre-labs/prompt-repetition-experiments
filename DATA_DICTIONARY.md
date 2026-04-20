# Data Dictionary

This document defines the schema and field meanings for all experiment data files in this repository.

## Overview

Experiment data is organized into three experiments (exp1-fastmcp-refactor, exp2-treesitter-synthesis, exp3-kotlin-grammar), each containing:
- `efficiency.json`: Token counts, costs, and wall-clock timing per run
- `analysis.json`: Comprehensive run metadata, message counts, and evaluation scores
- `latency-log.jsonl`: Per-run timing data (start/end timestamps)
- `scores.json`: Detailed rubric scoring with justifications
- Supporting files: `label-map.json`, `rubric.md`, `runner-prompt.md`, `scorer-prompt.md`, `protocol.md`

**Token Data Note**: Token counts are recovered from `sessions.db` accumulated_input_tokens / accumulated_output_tokens / accumulated_total_tokens columns and backfilled into analysis.json and efficiency.json. These accumulated columns are authoritative; per-turn token columns in sessions.db are not used.

**Exp3 exception**: `bytes` is `null` in all exp3 run records because the sessions.db schema used during that experiment lacked a `total_bytes` column. All other per-run fields are recoverable.

---

## efficiency.json

**Purpose**: Token consumption, cost, and wall-clock timing summary per run.

**Top-level schema**:

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `source` | string | Data provenance note | Backfilled |
| `pricing` | object | Model pricing configuration | Backfilled |
| `pricing.model` | string | Model identifier (e.g., "claude-haiku-4-5") | Backfilled |
| `pricing.provider` | string | LLM provider (e.g., "gcp_vertex_ai") | Backfilled |
| `pricing.input_per_mtok_usd` | number | Input token price per million tokens (USD) | Backfilled |
| `pricing.output_per_mtok_usd` | number | Output token price per million tokens (USD) | Backfilled |
| `pricing_date` | string | Date pricing was recorded (YYYY-MM-DD) | Backfilled |
| `runs` | array | Array of run records | Original + Backfilled |

**Run record schema**:

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `run_id` | string | Unique run identifier (e.g., "scout-control-1") | Original |
| `goose_session_id` | string | Goose session ID from sessions.db (e.g., "20260220_31") – must be non‑null in all future experiments | Original |
| `group` | string | Experimental group: "control" or "treatment" | Original |
| `model` | string | LLM model used (e.g., "haiku-4.5") | Original |
| `valid` | boolean | Whether run produced valid output | Original |
| `attempt` | integer | Attempt number (typically 1) | Original |
| `input_tokens` | integer | Total input tokens consumed (accumulated) | Original |
| `output_tokens` | integer | Total output tokens generated (accumulated) | Original |
| `total_tokens` | integer | Sum of input_tokens + output_tokens | Backfilled |
| `cost_usd` | number | Estimated cost in USD (rounded to 4 decimals) | Backfilled |
| `wall_clock_seconds` | integer | Elapsed time in seconds (from sessions.db end_ts - start_ts) | Backfilled |
| `note` | string or null | Optional note (e.g., failure reason) | Original |

---

## analysis.json

**Purpose**: Comprehensive per-run metadata, message counts, token analysis, and evaluation scores.

**Top-level schema**:

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `experiment` | string | Experiment title | Original |
| `schema_version` | string | Schema version identifier (e.g., "full-v1"); required non-null | Original |
| `title` | string | Full experiment description | Original |
| `issue` | string | GitHub issue reference | Original |
| `model` | string | LLM model used | Original |
| `date` | string | Experiment date (YYYY-MM-DD) | Original |
| `n_per_group` | integer | Number of runs per group | Original |
| `control_condition` | string | Control group description | Original |
| `treatment_condition` | string | Treatment group description | Original |
| `rubric_version` | string | Evaluation rubric version | Original |
| `orchestrator_session` | string | Goose session ID of orchestrator | Original |
| `repo_head` | string | Git commit hash at experiment time | Original |
| `experiment_start` | string or null | Experiment start timestamp (ISO 8601) | Original |
| `experiment_end` | string or null | Experiment end timestamp (ISO 8601) | Original |
| `data_note` | string or null | Data quality or recovery notes | Original |
| `runs` | object | Map of run_id -> run record | Original + Backfilled |
| `scores` | object | Summary statistics by group | Original |
| `statistical_test` | object | Test results and interpretation | Original |
| `conclusion` | string | Summary findings | Original |
| `pre_acknowledged_limitations` | array | Known limitations | Original |
| `analyzed_at` | string | Analysis timestamp (ISO 8601) | Original |
| `token_analysis` | object | Token consumption statistics | Original |
| `criterion_pass_rates` | object | Per-criterion pass rates | Original |

**Run record schema** (within `runs` object):

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `group` | string | "control" or "treatment" | Original |
| `goose_session_id` | string | Goose session ID (renamed from `session_id`) | Original |
| `messages` | integer | Total messages in session | Original or Backfilled |
| `input_tokens` | integer | Total input tokens | Original |
| `output_tokens` | integer | Total output tokens | Original |
| `total_tokens` | integer | Sum of input + output tokens | Original or Backfilled |
| `bytes` | integer or null | Total message bytes | Original or Backfilled |
| `wall_clock_seconds` | integer | Elapsed time in seconds (renamed from `wall_seconds`) | Original or Backfilled |
| `note` | string or null | Optional run notes | Original |
| `scores` | object | Criterion scores (C1, C2, ..., CN) as integers | Backfilled |

**Scores object** (within run record):

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `C1` | integer | Criterion 1 score (0 or 1, or higher scale) | Backfilled from scores.json |
| `C2` | integer | Criterion 2 score | Backfilled from scores.json |
| ... | ... | Additional criteria as defined in rubric | Backfilled from scores.json |

---

## latency-log.jsonl

**Purpose**: Per-run timing data in newline-delimited JSON format.

**Record schema** (one JSON object per line):

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `run_id` | string | Unique run identifier | Original |
| `goose_session_id` | string | Goose session ID | Original |
| `start_ts` | string | Session start time (ISO 8601 with Z suffix) | Backfilled from sessions.db |
| `end_ts` | string | Session end time (ISO 8601 with Z suffix) | Backfilled from sessions.db |
| `wall_clock_seconds` | integer | Elapsed time in seconds (end_ts - start_ts) | Backfilled from sessions.db |
| `input_tokens` | integer | Accumulated input tokens for this run's session, from sessions.db | sessions.db |
| `output_tokens` | integer | Accumulated output tokens for this run's session, from sessions.db | sessions.db |
| `total_tokens` | integer | Accumulated total tokens for this run's session, from sessions.db | sessions.db |
| `bytes` | integer | Sum of assistant message content_json byte lengths for this session | sessions.db |
| `goose_session_id` | string | Goose session ID captured post-run via sqlite3 (format YYYYMMDD_NN) | sessions.db |

**Example**:
```json
{"run_id": "scout-control-1", "goose_session_id": "20260220_31", "start_ts": "2026-02-20T21:14:39Z", "end_ts": "2026-02-20T21:15:28Z", "wall_clock_seconds": 49}
```

---

## scores.json

**Purpose**: Detailed rubric evaluation results with per-criterion scores and justifications.

**Top-level schema**:

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `scored_at` | string | Scoring timestamp (ISO 8601) | Original |
| `scorer` | string | Scorer model/agent identifier | Original |
| `rubric_version` | string | Rubric version used | Original |
| `note` | string or null | Scoring notes (e.g., exclusions) | Original |
| `scores` | array | Array of score records | Original |

**Score record schema** (within `scores` array):

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `run_id` | string | Run identifier (format varies by experiment) | Original |
| `C1` | integer | Criterion 1 score | Original |
| `C2` | integer | Criterion 2 score | Original |
| ... | ... | Additional criteria | Original |
| `total` | integer | Sum of all criterion scores | Original |
| `justifications` | object | Explanation per criterion | Original |

**Justifications object**:

| Field | Type | Description |
|-------|------|-------------|
| `C1` | string | Justification for C1 score |
| `C2` | string | Justification for C2 score |
| ... | ... | Additional criteria |

---

## label-map.json

**Purpose**: Mapping of run identifiers to human-readable labels or group assignments.

**Schema**: Object with run_id as key and label/group info as value. Format varies by experiment.

---

## rubric.md

**Purpose**: Evaluation rubric defining all criteria (C1, C2, ..., CN) and scoring rules.

**Content**: Markdown document with:
- Criterion definitions
- Scoring scale (typically 0-1 binary or 0-N scale)
- Examples and edge cases
- Scoring instructions for evaluators

---

## runner-prompt.md

**Purpose**: System prompt provided to Scout (or other agent) during experiment runs.

**Content**: Markdown document with:
- Task description
- Instructions for the agent
- Context and constraints
- Expected output format

---

## scorer-prompt.md

**Purpose**: System prompt provided to the scoring agent (blind evaluator).

**Content**: Markdown document with:
- Evaluation instructions
- Rubric reference
- Blind evaluation guidelines
- Output format requirements

---

## protocol.md

**Purpose**: Experiment protocol documentation.

**Content**: Markdown document with:
- Hypothesis and research question
- Experimental design (control vs. treatment)
- Sample size and group assignments
- Data collection procedures
- Statistical analysis plan
- Limitations and assumptions

---

## Data Provenance Summary

| Data Source | Files | Fields |
|-------------|-------|--------|
| Experiment orchestrator (at run time) | efficiency.json, analysis.json | input_tokens, output_tokens, total_tokens, cost_usd, model, valid, attempt, group, run_id, note |
| Goose sessions.db (backfilled) | analysis.json, latency-log.jsonl, efficiency.json | goose_session_id, wall_clock_seconds, messages, bytes, start_ts, end_ts |
| Scoring agent | scores.json, analysis.json (scores field) | C1-CN, justifications |
| Manual curation | label-map.json, rubric.md, runner-prompt.md, scorer-prompt.md, protocol.md | All fields |

---

## Field Naming Conventions

- **Renamed fields** (for consistency across experiments):
  - `session_id` → `goose_session_id`
  - `accumulated_input_tokens` → `input_tokens`
  - `accumulated_output_tokens` → `output_tokens`
  - `wall_time_minutes` → `wall_clock_seconds` (converted: minutes × 60 → seconds)
  - `wall_seconds` → `wall_clock_seconds`

- **Backfilled fields** (added from sessions.db or derived):
  - `total_tokens` = input_tokens + output_tokens
  - `cost_usd` = (input_tokens × 1.0 / 1,000,000) + (output_tokens × 5.0 / 1,000,000)
  - `wall_clock_seconds` = end_ts - start_ts (in seconds)
  - `bytes` (from sessions.db total_bytes when null in analysis)
  - `messages` (from sessions.db message_count when missing)
  - `scores` (extracted from scores.json, criteria only, no justifications)

---

## Timestamp Formats

- **ISO 8601 with Z suffix**: `2026-02-20T21:14:39Z` (used in latency-log.jsonl and analysis.json)
- **Epoch seconds**: `1771622079` (used in sessions.db, converted to ISO 8601 for export)
- **Time-of-day strings**: `21:14:39Z` (legacy in analysis.json, kept for reference)

---

## Notes on Data Quality

1. **Token Counts**: Sessions.db token columns are NULL. All token data comes from experiment analysis accumulated during orchestrator runs. These are authoritative.

2. **Timing**: Sessions.db provides epoch timestamps (start_ts, end_ts) which are converted to ISO 8601 format. Wall-clock seconds are calculated as end_ts - start_ts.

3. **Message Counts**: Backfilled from sessions.db message_count where not present in analysis.json.

4. **Bytes**: Backfilled from sessions.db total_bytes where null in analysis.json.

5. **Scores**: Extracted from scores.json, keeping only criterion scores (C1-CN) and excluding justifications to avoid duplication.

6. **Run ID Mapping**: Scores.json uses different run_id formats than analysis.json:
   - exp1: scores.json uses "control-2", analysis.json uses "scout-control-2"
   - exp2: scores.json uses "run-01", analysis.json uses "scout-run-01"
   - Mapping is performed during normalization.

7. **Excluded Runs**: Some runs may be excluded from scoring (e.g., exp1 control-1 due to drift failure). These are noted in scores.json and analysis.json but included in token analysis.

---

## turn-efficiency.json (repo root)

Standalone artifact surfacing per-run message counts for both experiments. Suitable for direct citation without parsing nested analysis.json.

### Top-level fields

| Field | Type | Description |
|-------|------|-------------|
| `runs` | array | One entry per run across all experiments (20 total: 10 per experiment) |
| `group_summaries` | object | Per-experiment, per-group aggregate statistics for valid runs only |
| `notes` | string | Exclusion notes (e.g., drift failures excluded from summary statistics) |

### `runs[]` fields

| Field | Type | Description |
|-------|------|-------------|
| `experiment` | string | Experiment key (`exp1_fastmcp_refactor` or `exp2_treesitter_synthesis`) |
| `run_id` | string | Unique run identifier matching `efficiency.json` |
| `group` | string | `"control"` or `"treatment"` |
| `messages` | integer | Total message count for this run |
| `valid` | boolean | `false` if this run is excluded from analysis (e.g., drift failure) |

### `group_summaries.<experiment>.<group>` fields

| Field | Type | Description |
|-------|------|-------------|
| `mean` | float | Mean message count across valid runs |
| `median` | float | Median message count across valid runs |
| `n` | integer | Number of valid runs |
| `messages` | array of integers | Raw message counts for valid runs |

### `group_summaries.<experiment>` top-level

| Field | Type | Description |
|-------|------|-------------|
| `diff_pct` | float | Relative difference: `((treatment_mean - control_mean) / control_mean) * 100` |

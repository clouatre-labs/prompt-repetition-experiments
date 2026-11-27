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

**Exp4 (exploratory, non-confirmatory)**: `exp-swift-grammar-mercury` is not one of the three pre-registered experiments. Its `analysis.json` covers only the 10 main-run sessions (runs 07 to 16, n=5+5); pilot rounds 01 to 06 are tracked in the directory but excluded. Exceptions to the schema above: the delegate is `inception/mercury-2.5-preview` via OpenRouter (Goose 1.49.0), not Claude Haiku 4.5; `bytes` is present and comes from `latency-log.jsonl` rather than `sessions.db`; `messages` is copied from the session file's `message_count` field, whose values are 0 or 1 and are not turn counts; and there is no `efficiency.json`, `protocol.md` or `raw/` directory. The treatment is defined differently from Exp1 to Exp3: the user `prompt` block is duplicated verbatim and the system `instructions` are unchanged. See `SUMMARY.md` and `README.md` in the experiment directory.

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
| `run_id` | string | Unique run identifier (e.g., "scout-control-1") | Original |
| `group` | string | "control" or "treatment" | Original |
| `goose_session_id` | string | Goose session ID (renamed from `session_id`) | Original |
| `started_at` | string | Session start time (ISO 8601, e.g., "2026-02-20T21:14:39Z") | latency-log.jsonl / efficiency.json |
| `finished_at` | string | Session end time (ISO 8601, e.g., "2026-02-20T21:16:53Z") | latency-log.jsonl / efficiency.json |
| `latency_seconds` | integer | Wall-clock duration of the scout run in seconds | latency-log.jsonl / efficiency.json |
| `message_count` | integer | Total messages in the goose session (from sessions.db) | sessions.db / efficiency.json |
| `messages` | integer | Total messages in session | Original or Backfilled |
| `input_tokens` | integer | Total input tokens | Original |
| `output_tokens` | integer | Total output tokens | Original |
| `total_tokens` | integer | Sum of input + output tokens | Original or Backfilled |
| `bytes` | integer or null | Total message bytes | Original or Backfilled |
| `wall_clock_seconds` | integer | Elapsed time in seconds (renamed from `wall_seconds`) | Original or Backfilled |
| `note` | string or null | Optional run notes | Original |
| `scores` | object | Criterion scores (C1, C2, ..., CN) as integers | Backfilled |

**Schema normalization note**: As of this PR, `latency_seconds`, `message_count`, and `goose_session_id` are present in all experiments' session files, providing consistent provenance tracking across all three experimental runs.

**Message count definition**: All published message counts (README, paper, `.zenodo.json`, `CITATION.cff`, `turn-efficiency.json`, and Figure 3) are defined as the sum of `runs[*].messages` in each `experiments/exp*/analysis.json`. These values are sourced from `sessions.db` and total 3,800 messages across all 30 session logs, including the excluded Exp1 drift run `scout-control-1` (93 messages); the headline total of 3,707 covers the 29 valid sessions. This definition is scoped to Exp1 to Exp3. Exp4 (`exp-swift-grammar-mercury`) is excluded: its `runs[*].messages` values are 0/1 flags copied from the session files' `message_count`, not turn counts, and must not be added to the 3,800 or 3,707 totals. `runs[*].messages` must be ignored for Exp4 in every published message-count context: the README and paper totals, Figure 3, `turn-efficiency.json`, `.zenodo.json` and `CITATION.cff`; the field is retained only so that `analysis.json` stays valid against the shared schema. The run-time `message_count` fields in `efficiency.json` and `latency-log.jsonl` are a different measure and are not authoritative (null or absent for Exp3), so they must not be used for published counts.

**Scores object** (within run record):

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `C1` | integer | Criterion 1 score (0 or 1, or higher scale) | Backfilled from scores.json |
| `C2` | integer | Criterion 2 score | Backfilled from scores.json |
| ... | ... | Additional criteria as defined in rubric | Backfilled from scores.json |

**Exp5 analysis output** (`experiments/exp5-php-grammar-powered/analysis-output/analysis.json`, produced by `experiments/exp5-php-grammar-powered/analysis/analysis.py`): this file shares the `analyzed_at` key with the schema above but is otherwise a separate, self-describing schema and is not an instance of `full-v1`. It is written with sorted keys and fixed rounding, and `analyzed_at` is the latest `end_ts` in `latency-log.jsonl` (no wall clock is consulted), so repeated runs are byte-identical. Exp4 regression reference: the loader accepts `exp-swift-grammar-mercury/scores-main-run.json` and its `label-map.json` and reproduces control mean 4.2 and treatment mean 4.0.

| Field | Type | Description |
|-------|------|-------------|
| `analyzed_at` | string or null | Max `end_ts` across `latency-log.jsonl` (ISO 8601); null when the log is absent |
| `bootstrap_seed` | integer | Seed passed to `numpy.random.default_rng` for the rank-biserial bootstrap CI |
| `criteria` | array | Criteria entering `total`, in order: `C3` to `C7` |
| `n_runs` | integer | Number of scored runs |
| `arms` | object | Per arm (`control`, `treatment`): `runs`, `n`, `scores`, `mean`, `median`, `sd` of `total`, plus `criteria_passed`, `criteria_total`, `pass_proportion` and its Wilson 95% interval `wilson_low`/`wilson_high` (z = 1.959963984540054; a criterion passes when its score is at least 0.5) |
| `effect_size.per_model` | object | Per model: `n1` (treatment), `n2` (control), `u` (U for x=treatment), `p` (two-sided, asymptotic), `r`, `note`, `bootstrap{low, high, iterations, seed}` |
| `effect_size.pooled_r` | number or null | Unweighted mean of the per-model `r` values (effects are pooled, not raw scores) |
| `effect_size.interaction_r` | number or null | Exploratory only: difference between the two per-model effects; null with fewer than two models |
| `effect_size.convention` | string | Sign convention: `r = 2*U1/(n1*n2) - 1` with `U1` taken for x=treatment, so positive `r` means treatment > control; a zero-variance pair of arms reports `p=null`, `r=0` and a note; NaN and Infinity are never emitted |
| `cost.per_run` | object | Per `run_id`: `model`, `pricing_key`, `cost_usd` (cache-adjusted USD, 6 decimals, or null with a `note` when the model is unknown or a needed rate is unverified) and raw `tokens{input_tokens, output_tokens, cache_read_tokens, cache_write_tokens}` |
| `cost.per_arm` | object | Per arm: `cost_usd` (null if any run is unpriced), `priced_runs`, `unpriced_runs`, raw `tokens` totals |
| `cost.pricing_retrieved_on` | string | Retrieval date of `pricing.json` (2026-11-27); `claude-haiku-5-5` cache rates are `verified: false` with the prompt-length tier recorded |
| `assertions` | array | `{name, status: pass, fail or skipped, detail}` for coverage (scores, label-map and latency-log run ids), recomputed label-map `sha256_*` hashes (recomputed from `runner-prompt.md`, `scorer-prompt.md` and `analysis.py`) and zero thinking tokens (`null` = not captured, skipped; `0` = captured and zero) |

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

**Exp5 additional fields** (`experiments/exp5-php-grammar-powered/latency-log.jsonl`, written by `run.py`; missing values are `null`, never NaN):

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `group` | string | `control` or `treatment` | label-map.json |
| `model` | string | goose model id (for example `claude-haiku-4-5`) | Recipe settings |
| `cache_read_tokens` | integer or null | Accumulated cache read tokens for the session | sessions.db |
| `cache_write_tokens` | integer or null | Accumulated cache write tokens for the session | sessions.db |
| `cost_usd` | number or null | Accumulated estimated cost for the session | sessions.db |
| `thinking_tokens` | integer or null | Thinking token count, when goose output exposes one; `null` otherwise | goose JSON output |
| `thinking_capture` | string | `observed` or `not_captured` | Derived from `thinking_tokens` |
| `thinking_blocks` | integer or null | Number of thinking blocks in assistant messages (proxy for thinking effort) | sessions.db |
| `thinking_chars` | integer or null | Total characters across thinking blocks | sessions.db |
| `goose_version` | string or null | Output of `goose --version` at run time | Original |
| `env` | object | `GOOSE_MAX_TURNS`, `GOOSE_CONTEXT_LIMIT` and `GOOSE_PROVIDER` in effect for the run | Original |
| `exit_code` | integer or null | goose process exit status; `null` on timeout or clone failure | Original |
| `failure_mode` | string or null | `goose_exit_<code>`, `timeout`, `clone_failed`, `session_not_found` or `session_ambiguous`; `null` on success | Original |
| `detail` | string or null | Last 300 characters of goose stderr | Original |

`sessions_db` is required; an unusable path raises at backfill and the batch is not resumed automatically.


**Example**:
```json
{"run_id": "scout-control-1", "goose_session_id": "20260220_31", "start_ts": "2026-02-20T21:14:39Z", "end_ts": "2026-02-20T21:15:28Z", "wall_clock_seconds": 49}
```

---

## tool-log.jsonl

**Purpose**: Per-run list of tool calls, with the tool name and target only. Introduced by Exp5.

**Record schema** (one JSON object per line):

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `run_id` | string | Unique run identifier | Original |
| `goose_session_id` | string | Goose session ID | sessions.db |
| `seq` | integer | Call order within the run, starting at 0 | sessions.db |
| `tool` | string or null | Tool name from the tool request | sessions.db |
| `target` | string or null | The path, URI, URL, library or query the call targets; `null` when the tool has no such argument (for example shell commands) | sessions.db |

Tool arguments and tool results are never recorded; a shell call appears as its tool name with a `null` target.

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

**Exp5 fractional extension** (`experiments/exp5-php-grammar-powered/scorer`, rubric `exp5-rubric-v1-fractional`): the executable scorer keeps the Exp4 criterion IDs but emits C3 to C7 as numbers in `[0,1]` (fractional share of satisfied sub-rules, never `NaN`; not-applicable values are `null`). `total` is the sum `C3 + C4 + C5 + C6 + C7` (max 5.0); `primary_total` is `C3 + C4 + C5` (max 3.0) and is the primary outcome, since `C6` and `C7` are excluded under the protocol's floor and ceiling rule (1.0 in every run of the 2026-11-27 pilot). `C1` and `C2` are not executable offline and are `null` unless the session carries a numeric value, in which case it is copied verbatim. Each `justifications` entry names the artifact that failed (for example `element_query_draft does not compile`). Top-level keys are written in fixed order `scored_at, scorer, rubric_version, note, scores`, so repeat runs over the same sessions are byte-identical apart from `scored_at`. Score records carry `run_id, C1, C2, C3, C4, C5, C6, C7, total, primary_total, justifications` in that order.

---

## label-map.json

**Purpose**: Mapping of run identifiers to human-readable labels or group assignments.

**Schema**: Object with run_id as key and label/group info as value. Format varies by experiment.

**Exp5 schema** (`experiments/exp5-php-grammar-powered/label-map.json`): a top-level object with `sealed_at`, `assignments` and `sha256`. `assignments` is a flat map from run_id to an object with `group`, `model`, `goose_session_id`, `sealed_at`, `sha256_runner_prompt`, `sha256_scorer`, `sha256_analysis` and `concurrency_limit`. The file is written and hashed before the first run is spawned; `goose_session_id` is `null` at seal time and is filled in afterwards from the session name. `sha256_scorer` and `sha256_analysis` are `null` until those artifacts exist. `sha256` is the SHA-256 of the `assignments` block serialized as compact sorted-key JSON with every `goose_session_id` set to `null`, so it can be verified after the backfill.

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

In Exp5 (`experiments/exp5-php-grammar-powered/runner-prompt.md`) the text after the `---` line is the prompt body. `gen_recipes.py` copies it byte-verbatim into the recipe `prompt`, and the treatment arm repeats the same body a second time in the recipe `instructions`. Its SHA-256 is recorded as `sha256_runner_prompt` in `label-map.json`.

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

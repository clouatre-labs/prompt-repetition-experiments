# Exp5 analysis

Computes the Exp5 (PHP grammar, powered) statistics from the sealed inputs in
the experiment directory and writes deterministic outputs.

## Outcome variables

- **Primary:** `primary_total = C3 + C4 + C5`, range [0, 3], per run, taken
  exactly as the scorer emits the `primary_total` field. It is never recomputed
  from the criteria and no criterion is dropped from it after the main run
  begins.
- **Co-reported:** `primary_total` minus C5, range [0, 2], computed for every
  run whether or not C5 varies (C5 is 0.0 in every run of the fenced re-pilot;
  see `../protocol.md`, Primary Outcome).
- **Secondary:** C6 and C7, reported per arm and per model. **Record only:**
  `total` (max 5.0).
- Every effect (per-model Mann-Whitney r, bootstrap CI, pooled r, exploratory
  interaction) is computed twice, once per outcome variable, in
  `effect_size` (primary) and `effect_size_minus_c5` (co-reported). The only
  fallback to `total` is the pre-#123 Exp4 fixture layout, which has no
  `primary_total`; an Exp5 record without it raises. The package is a
standalone uv project; it makes no network calls and writes only inside the
experiment directory.

## Commands

```sh
cd experiments/exp5-php-grammar-powered/analysis
uv sync
uv run pytest
uv run python analysis.py .. --out ../analysis-output
uv run python analysis.py .. --out ../analysis-output --outputs ../scorer/pilot-evidence/fenced-repilot --scores ../scorer/pilot-evidence/fenced-repilot/scores.json
uv run python -m pyflakes analysis.py stats.py overlap.py tests
```

`--outputs DIR` is where the overlap rule reads each run's delegate output:
`DIR/<run_id>/exp5-output.json` (or `DIR/<run_id>.json`); the default is
`<experiment_dir>/outputs`. `--node-types` defaults to the vendored
`../scorer/vendor/tree-sitter-php-node-types.json`.

`analysis.py` exits with status 1 when any recorded assertion fails; the
outputs are still written so the failure can be inspected.

## Inputs

- `scores.json`: `{scored_at, scorer, rubric_version, note, scores[]}` where
  each entry has `run_id`, fractional `C1`..`C7` in `[0, 1]` (`C1`/`C2` may
  be null), `total` (sum of `C3`..`C7`), `primary_total` (= `C3 + C4 + C5`,
  required) and `justifications{}`. A record without `primary_total`, or with
  a null `C5`, raises `ValueError`. The Exp4 layout (`scores-main-run.json`: a
  list of `{run_id, scores: {Cn: {score}}}`, `total`) is accepted through the
  same loader and is the only case where `total` stands in for
  `primary_total`.
- `label-map.json`: `{sealed_at, assignments: {run_id: {group, model, ...,
  sha256_runner_prompt, sha256_scorer, sha256_analysis}}, sha256}`. A flat
  `run_id -> "control" | "treatment"` map and Exp4's
  `main_run.assignments` are also accepted.
- `latency-log.jsonl`: one row per run with `run_id`, `start_ts`, `end_ts`,
  `input_tokens`, `output_tokens`, `cache_read_tokens`,
  `cache_write_tokens`, `thinking_tokens` (null = not captured), `model`.
- `pricing.json`: per-model USD per MTok with source URL, retrieval date and
  a `verified` flag.
- `outputs/<run_id>/exp5-output.json`: the delegate output of each run, read
  by the exclusion step (`overlap.py`) for `element_query_draft` and
  `defuse_query_draft`. A kept run without an output file fails the
  `exclusion_overlap_available` assertion (exit 1, outputs still written).

## Exclusions (`protocol.md`, Exclusions and Stopping Rule)

`apply_exclusions` runs before any effect is computed and returns, per run,
`excluded` and `reason` in `{turn_cap, output_overlap}`:

- `turn_cap`: the latency or score record carries a `failure_mode` (a run
  that reaches `--max-turns 60` is logged as `goose_exit_1`; the exact value
  is kept in `failure_mode`, whatever it is).
- `output_overlap`: the run's overlap is above 0.8 for either draft.
  `overlap.py` implements the method as worded in the protocol: per draft,
  `|cited ∩ vocabulary| / |vocabulary|`, cited = lowercase snake_case tokens
  (`\b[a-z]+(?:_[a-z]+)+\b`) after `;` comments are dropped, vocabulary =
  named node types and field names of `node-types.json` (187 entries).

No imputation, no replacement, no re-weighting: effects, arm summaries and
per-arm `n` use the remaining runs only. Excluded runs are listed by run id
with the reason in `analysis.json` (`exclusions.excluded[]`) and in
`table_exclusions.tex`.

Ceiling of the rule as worded: 40 of the 187 vendored entries are not
snake_case (`name`, `body`, `text`, ...), so a draft can cite at most 147 of
them and score 147/187 = 0.786, below the 0.8 threshold. Against the vendored
vocabulary the overlap rule therefore cannot fire; `test_rule_ceiling_with_the_vendored_vocabulary`
pins this. Changing it is a protocol amendment, not an analysis change.

## Outputs (in `--out`)

- `analysis.json`: `outcome` (the outcome variables above), per-arm means of
  `primary_total` with Wilson 95% intervals on the C3..C5 pass proportion and,
  under `minus_c5`, the same summary for the co-reported outcome; `criteria_means`
  per arm and `criteria_by_model` (C3..C7); `effect_size` and
  `effect_size_minus_c5`, each with per-model Mann-Whitney U and rank-biserial
  r with a seeded bootstrap CI (seed 20261127, 1000 resamples), the pooled
  per-model effect (unweighted mean of r) and an exploratory model x treatment
  interaction note; `assertions[]`; cache-adjusted USD cost per run and per
  arm, and the raw token totals. Written with sorted keys and fixed rounding;
  `analyzed_at` is the latest `end_ts` in the latency log, so repeated runs
  are byte-identical.
- `exclusions`: the rule, the overlap method and threshold, `per_run` (every
  scored run with `excluded`, `reason`, `failure_mode`, `overlap` per draft),
  `excluded[]` (run id, reason), `kept[]`, `n_excluded`, `n_kept`;
  `n_scored` counts every scored run and `n_runs` the kept ones.
- `table_means.tex`, `table_effects.tex`, `table_cost.tex`,
  `table_exclusions.tex`: LaTeX table fragments with special characters escaped. The means and effects tables
  carry `primary_total = C3 + C4 + C5` and `primary_total` minus C5 side by
  side, named in their headers.

## Conventions

- `mann_whitney_r(x=treatment, y=control)` with `method="asymptotic"`;
  `r = 2*U1/(n1*n2) - 1` so positive r means treatment scores are higher.
- Zero-variance arms report `p=null`, `r=0` and a note. No NaN or Infinity is
  ever emitted.
- Wilson z is fixed at `1.959963984540054`.
- `thinking_tokens=null` means not captured and is skipped; `0` counts as
  captured and zero.
- Both models' rates are verified (`verified: true`, retrieved 2026-11-27;
  the `claude-haiku-5-5` cache read and write rates were confirmed by the
  owner). A null rate would give a null cost with a note rather than a guess.

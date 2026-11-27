# Exp5 analysis

Computes the Exp5 (PHP grammar, powered) statistics from the sealed inputs in
the experiment directory and writes deterministic outputs. The package is a
standalone uv project; it makes no network calls and writes only inside the
experiment directory.

## Commands

```sh
cd experiments/exp5-php-grammar-powered/analysis
uv sync
uv run pytest
uv run python analysis.py .. --out ../analysis-output
uv run python -m pyflakes analysis.py stats.py tests
```

`analysis.py` exits with status 1 when any recorded assertion fails; the
outputs are still written so the failure can be inspected.

## Inputs

- `scores.json`: `{scored_at, scorer, rubric_version, note, scores[]}` where
  each entry has `run_id`, fractional `C1`..`C7` in `[0, 1]` (`C1`/`C2` may
  be null), `total` (sum of `C3`..`C7`) and `justifications{}`. The Exp4
  layout (`scores-main-run.json`: a list of `{run_id, scores: {Cn: {score}}}`,
  `total`) is accepted through the same loader.
- `label-map.json`: `{sealed_at, assignments: {run_id: {group, model, ...,
  sha256_runner_prompt, sha256_scorer, sha256_analysis}}, sha256}`. A flat
  `run_id -> "control" | "treatment"` map and Exp4's
  `main_run.assignments` are also accepted.
- `latency-log.jsonl`: one row per run with `run_id`, `start_ts`, `end_ts`,
  `input_tokens`, `output_tokens`, `cache_read_tokens`,
  `cache_write_tokens`, `thinking_tokens` (null = not captured), `model`.
- `pricing.json`: per-model USD per MTok with source URL, retrieval date and
  a `verified` flag.

## Outputs (in `--out`)

- `analysis.json`: per-arm means with Wilson 95% intervals, per-model
  Mann-Whitney U and rank-biserial r with a seeded bootstrap CI, the pooled
  per-model effect, an exploratory model x treatment interaction note,
  `assertions[]`, cache-adjusted USD cost per run and per arm, and the raw
  token totals. Written with sorted keys and fixed rounding; `analyzed_at` is
  the latest `end_ts` in the latency log, so repeated runs are byte-identical.
- `table_means.tex`, `table_effects.tex`, `table_cost.tex`: LaTeX table
  fragments with special characters escaped.

## Conventions

- `mann_whitney_r(x=treatment, y=control)` with `method="asymptotic"`;
  `r = 2*U1/(n1*n2) - 1` so positive r means treatment scores are higher.
- Zero-variance arms report `p=null`, `r=0` and a note. No NaN or Infinity is
  ever emitted.
- Wilson z is fixed at `1.959963984540054`.
- `thinking_tokens=null` means not captured and is skipped; `0` counts as
  captured and zero.
- `claude-haiku-5-5` cache rates are unverified (`verified: false`): runs
  with cache tokens on that model get a null cost with a note.

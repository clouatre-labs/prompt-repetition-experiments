# Exp5 Protocol: PHP Grammar Scout with a Model Factor

This protocol is fixed before the main run. Everything below is final. Every value that depends on the pilot is written as `PILOT:` followed by a short description of what fills it; the pilot issue (#105) replaces each token, and nothing else changes. Amendments after deposit are recorded in `AMENDMENTS.md`, which is empty at deposit.

## Research Question

Does a verbatim second copy of the task instructions improve the executable task-success score of non-reasoning LLM agents on the PHP grammar scout task (clouatre-labs/aptu-coder#1864), and does the answer depend on the model?

## Hypothesis

The hypothesis is no effect of verbatim instruction repetition on the executable task-success score, for each model. The experiment tests this; it does not assume a direction.

## Design

- Models: `claude-haiku-4-5` and `claude-haiku-5-5`.
- Arms: control (one instruction line) and treatment (that line plus a byte-verbatim second copy of the prompt body). The recipe text is fixed by `gen_recipes.py`.
- Size: 2 models x 2 arms x n = 20, 80 runs in total.
- Order: runs execute in `plans/main.csv` order, interleaved within model (odd run ids control, even run ids treatment; `h45` block first, then `h55`).
- Provider `anthropic`, temperature 0.5, extensions `developer`, `context7` and `brave_search`.
- Target: fresh clone of clouatre-labs/aptu-coder at `132ea687e09a916091699a562da3c96c86ec1fd8` per run, hooks disabled.
- Concurrency: `--concurrency 2`, fixed now and identical for both arms.
- goose version: 1.61.1.
- Scorer and analysis code are sealed at run time: `label-map.json` carries `sha256_scorer` and `sha256_analysis`, the `tree_sha256` of `scorer/` and `analysis/` at seal time. PILOT: the final scorer and analysis trees after the pilot fixes.
- Turn cap: PILOT: value of `--max-turns` chosen after the pilot.

## Primary Outcome

`total = C3 + C4 + C5 + C6 + C7`, fractional in [0, 5], per run, as computed by `scorer/scorer.py` from the session JSON. `C1` and `C2` are not executable offline and are not part of the primary score.

## Statistical Analysis

- Test: Mann-Whitney U, two-tailed, alpha 0.05, run per model (two tests).
- Effect: rank-biserial r with Kerby's sign convention, treatment as x, per model.
- Interval: 95% confidence interval by bootstrap, seeded, with the seed recorded. PILOT: bootstrap seed and resample count.
- Software: PILOT: the `analysis/stats.py` version sealed in `sha256_analysis`.
- Criterion at floor or ceiling: see the Floor and Ceiling Rule; the primary score is recomputed on the remaining criteria and the recomputation is reported alongside the original.

## Pooling and Interaction

- Per-model effects are pooled by effect (the two rank-biserial r values), never by pooling raw scores across models.
- The exploratory interaction is the difference of the two per-model effects. It is labelled exploratory and is not a confirmatory test.
- PILOT: the pooling estimator and its weight (equal or inverse-variance).

## Floor and Ceiling Rule

Any criterion among `C3` to `C7` whose value is 0 or 1 in both pilot arms is excluded from the primary score and the exclusion is reported. PILOT: the list of excluded criteria with their pilot values.

## Exclusions

- Failed runs are recorded with `failure_mode` and are never retried or replaced.
- Contamination: the tool log shows access to upstream issue clouatre-labs/aptu-coder#1861, to any PHP pull request, or to the upstream repository past the pinned commit; or output overlap above a threshold fixed in #105. PILOT: overlap threshold and detection method.
- Excluded runs are listed by run id in the results, with the reason.

## Stopping Rule

Fixed n = 20 per model and arm. No early stopping, no optional extension, no replacement of failed runs.

## Measurement Limits

- `thinking_tokens` is `not_captured`: goose 1.61.1 JSON output carries no thinking or reasoning token count. `thinking_blocks` and `thinking_chars` are recorded as a proxy.
- `thinking_effort` is not settable through goose 1.61.1 recipes; no recipe sets it.
- `C1` and `C2` are not executable offline and stay outside the primary score.

## Cost Reporting

Cost is reported as cache-adjusted USD with raw token totals alongside. When a rate is unverified the cost is `null` with a note. PILOT: verified price table per model and the cache-adjustment rule.

## Pilot Evidence

The pilot (4 runs, `plans/pilot.csv`) informs the pilot-dependent values. PILOT: scorer headroom per criterion (`scorer/HEADROOM-pilot.md`), the floor and ceiling list, the overlap threshold, the bootstrap seed, the cost table and the pooling estimator.

## Deposit

The deposit is the `experiments/exp5-php-grammar-powered/` package: `protocol.md`, `PRE-REGISTRATION.md`, `AMENDMENTS.md`, `plans/main.csv`, `gen_recipes.py`, `run.py`, `runner-prompt.md`, `scorer/`, `analysis/` and `tests/`, with metadata in `.zenodo.json`. PILOT: the DOI and the per-file sha256 values in `PRE-REGISTRATION.md` after the pilot-informed files are final.

# Exp5 Protocol: PHP Grammar Scout with a Model Factor

This protocol is fixed before the main run. Everything below is final. Every value that depended on the pilot was a placeholder until issue #105 filled it from `scorer/HEADROOM-pilot.md` and `scorer/pilot-evidence/fenced-repilot/`; nothing else changed. Amendments after deposit are recorded in `AMENDMENTS.md`, which is empty at deposit.

## Research Question

Does a verbatim second copy of the task instructions improve the executable task-success score of non-reasoning LLM agents on the PHP grammar scout task (clouatre-labs/aptu-coder#1864), and does the answer depend on the model?

## Hypothesis

The hypothesis is no effect of verbatim instruction repetition on the executable task-success score, for each model. The experiment tests this; it does not assume a direction.

## Design

- Models: `claude-haiku-4-5` and `claude-haiku-5-5`. Both models are kept: the pilot found a floor on the `claude-haiku-4-5` control (see Pilot Evidence), which is a model-level finding reported with the results, not a stop condition.
- Arms: control (one instruction line) and treatment (that line plus a byte-verbatim second copy of the prompt body). The recipe text is fixed by `gen_recipes.py`.
- Size: 2 models x 2 arms x n = 20, 80 runs in total.
- Order: runs execute in `plans/main.csv` order, interleaved within model (odd run ids control, even run ids treatment; `h45` block first, then `h55`).
- Provider `anthropic`, temperature 0.5, extensions `developer` and `context7`. No web search extension: `brave_search` was removed after a pilot run surfaced upstream #1861 through it (see Exclusions).
- Target: fresh clone of clouatre-labs/aptu-coder at `132ea687e09a916091699a562da3c96c86ec1fd8` per run, hooks disabled, remote removed after checkout.
- Concurrency: `--concurrency 2`, fixed now and identical for both arms.
- goose version: 1.61.1.
- Scorer and analysis code are sealed at run time: `label-map.json` carries `sha256_scorer` and `sha256_analysis`, the `tree_sha256` of `scorer/` and `analysis/` at seal time. The final trees are the ones on `main` after #105: scorer code at commit `ce7f054` (unchanged through the fenced re-pilot, whose seal recorded scorer tree `d136db8769b343b9`; the only later change under `scorer/` is this record and its evidence), analysis code as committed with #105. The exact tree hashes are whatever `run.py` seals before the first main-run spawn; a later change to either tree is an amendment.
- Turn cap: `--max-turns 60` for every run in both arms.

## Primary Outcome

`primary_total = C3 + C4 + C5`, range [0, 3.0], per run, as emitted by `scorer/scorer.py` (the `primary_total` field of each record). It is taken as emitted and is never recomputed from the criteria; `C1` and `C2` are not executable offline and are not part of it.

- C6 and C7 are secondary outcomes, not part of the primary score. Reason: both were 1.0 in every run of the first pilot (prompt `2d4f22e3`; `scorer/HEADROOM-pilot.md`, Superseded: first pilot), a ceiling produced by the runner prompt enumerating the wiring facts, which removed them from the primary score (#123). They are reported per arm and per model.
- C5 position: C5 is 0.0 in every run of the fenced re-pilot (prompt `2878315307`; `scorer/pilot-evidence/fenced-repilot/variance.txt`, variance 0.0), so `primary_total` minus C5 (range [0, 2]) is declared now as a co-reported outcome. It is computed for every run, whether or not C5 varies in the main run, and reported next to `primary_total` in every table. C3, C4 and C5 are each reported per arm.
- No criterion is dropped from `primary_total` after the main run begins.
- `total` (max 5.0, `C3 + C4 + C5 + C6 + C7`) is retained in the record only.

## Statistical Analysis

- Test: Mann-Whitney U, two-tailed, alpha 0.05, run per model (two tests), on `primary_total`; the same test on `primary_total` minus C5 is reported alongside.
- Effect: rank-biserial r with Kerby's sign convention, treatment as x, per model.
- Interval: 95% confidence interval by bootstrap, seeded, with the seed recorded. Seed 20261127 (`DEFAULT_SEED` in `analysis/analysis.py`), 1000 resamples per model (`bootstrap_ci(..., iterations=1000)`), `numpy.random.default_rng(seed)`, percentile method; the same seed is used for the co-reported outcome.
- Software: `analysis/stats.py` as committed in `45d880a` and sealed in `sha256_analysis`; `analysis/analysis.py` as committed with #105.
- Criterion at floor or ceiling: see the Floor and Ceiling Rule; the primary score is recomputed on the remaining criteria and the recomputation is reported alongside the original. For C5 that recomputation is the co-reported `primary_total` minus C5, declared in Primary Outcome; `primary_total` itself stays as emitted for every run.

## Pooling and Interaction

- Per-model effects are pooled by effect (the two rank-biserial r values), never by pooling raw scores across models.
- The exploratory interaction is the difference of the two per-model effects. It is labelled exploratory and is not a confirmatory test.
- Pooling estimator: the unweighted (equal-weight) mean of the two per-model rank-biserial r values (`pooled_r` in `analysis/analysis.py`, `pooled_note: unweighted mean of per-model r`); inverse-variance weighting is not used. Applied to both outcome variables.

## Floor and Ceiling Rule

Any criterion among `C3` to `C7` whose value is 0 or 1 in both pilot arms is excluded from the primary score and the exclusion is reported. Excluded criteria from the first pilot (prompt `2d4f22e3`, `scorer/HEADROOM-pilot.md`): C6 (1.0 in 4 of 4 runs) and C7 (1.0 in 4 of 4 runs); all five C7 sub-criteria were also 1.0 in every run. C3 (0.0 and 1.0) and C4 (0.8, 0.8333, 0.7143, 1.0) and C5 (0.3333 x3, 1.0) varied in that pilot and were kept; after #123 the scorer no longer gives compile credit on C5. In the fenced re-pilot C5 is 0.0 in all four runs (floor, variance 0.0): it is not dropped; `primary_total` minus C5 is the co-reported outcome declared in Primary Outcome, and `C7.mod_registration` is 0.0 in all four runs (secondary, reported as is).

## Exclusions

- Failed runs are recorded with `failure_mode` and are never retried or replaced.
- Turn-cap exclusion: a run that reaches `--max-turns 60` is recorded with `failure_mode` `goose_exit_1` and excluded. The cap is identical across arms, so the budget-aware instruction goose injects at half the cap cannot differ between groups.
- Contamination (narrowed before deposit, 2026-11-27): a run is excluded when its transcript or tool log shows opening, searching for, or reading upstream clouatre-labs/aptu-coder#1861, any aptu-coder pull request, or any commit or file that adds PHP support. `git log` history of the pinned clone, the #1864 issue body, and grammar-repo or registry lookups are not hits. Reason for narrowing: the literal 2026-11-27 rule, as applied to the second pilot (prompt `671e5db1`), flagged the task's own inputs (the #1864 body and the Context7 grammar mirror) and sibling-language commits listed by `git log`, which excluded every run without any of them reaching #1861. Excluded runs are listed by run id with the reason.
- Output overlap: a run is excluded when the similarity is above 0.8. Method: Jaccard similarity over the set of lowercase node kinds and field names cited in the run's `element_query_draft` and `defuse_query_draft` versus the same sets extracted from the vendored `scorer/vendor/tree-sitter-php-node-types.json` (named node types and field names, 187 entries). Cited identifiers are the snake_case tokens (`\b[a-z]+(?:_[a-z]+)+\b`) of each draft after `;` comments are dropped, lowercased; the cited set is intersected with the vocabulary, and the similarity is `|cited ∩ vocabulary| / |vocabulary|` per draft. The two numbers per pilot run are in Pilot Evidence.
- Containment (instrument, PR #125): no web search extension (recipes list `developer` and `context7` only); the clone remote is removed after checkout so nothing can be fetched past the pin; the delegate's `gh` is a shim first on `PATH` that passes `issue view ... 1864`, `api` on `tree-sitter/tree-sitter-php` only, `--version` and `auth status`, and blocks everything else with exit 77 and a `BLOCKED: <args>` line in the per-run `gh-fence.log`. The fence log is deposited with every session and the count of blocked attempts is reported. Residual threat: the `developer` shell tool can still `curl` arbitrary URLs; the post-run transcript and tool-log scan for the contamination rule covers that path.

## Stopping Rule

Fixed n = 20 per model and arm. No early stopping, no optional extension, no replacement of failed runs. A run that reaches the turn cap (`--max-turns 60`, identical in both arms) is recorded with `failure_mode` `goose_exit_1` and excluded under Exclusions; the cap is identical across arms so the budget-aware instruction goose injects at half the cap cannot differ between groups.

## Measurement Limits

- `thinking_tokens` is `not_captured`: goose 1.61.1 JSON output carries no thinking or reasoning token count. `thinking_blocks` and `thinking_chars` are recorded as a proxy.
- `thinking_effort` is not settable through goose 1.61.1 recipes; no recipe sets it.
- `C1` and `C2` are not executable offline and stay outside the primary score.
- `claude-haiku-4-5` control sits at the floor of the primary scale (Pilot Evidence): with n = 1 per arm the pilot cannot tell a floor from a low-but-variable control, so the per-model effect on that model may be bounded by the scale rather than by repetition. This is reported with the results.

## Cost Reporting

Cost is reported as cache-adjusted USD with raw token totals alongside. When a rate is unverified the cost is `null` with a note.

- Verified price table (`analysis/pricing.json`, USD per MTok, retrieved 2026-11-27 from `https://platform.claude.com/docs/en/about-claude/pricing`; `claude-haiku-5-5` cache read and write rates confirmed by the owner):

| Model | input | output | cache_read | cache_write | tier |
|---|---|---|---|---|---|
| `claude-haiku-4-5` | 1.00 | 5.00 | 0.10 | 1.25 | flat |
| `claude-haiku-5-5` | 0.10 | 0.50 | 0.01 | 0.125 | prompt length at or below 100k tokens |

- Cache-adjustment rule (`run_cost` in `analysis/analysis.py`): `cost = input_tokens * input + cache_read_tokens * cache_read + cache_write_tokens * cache_write + output_tokens * output`, each divided by 1,000,000. Nothing is subtracted from `input_tokens` (Anthropic usage excludes cached tokens from it). A null rate for a token count above zero, an unknown model or a non-finite result gives a `null` cost with a note; `claude-haiku-5-5` runs above the 100k tier are priced at the listed tier and the limitation is noted.

## Pilot Evidence

Source: the fenced re-pilot, runner prompt sha256 `2878315307c0c3a5d5646ffea8efd00bfd84f780a774cefcabbf66f3753793b5`, 2026-11-27, goose 1.61.1, `--max-turns 60`, concurrency 2, plan `plans/pilot.csv` (4 runs, 2 models x 2 arms), scorer commit `ce7f054` (scorer tree `d136db8769b343b9` at the pilot seal). Record: `scorer/HEADROOM-pilot.md` (section Fenced re-pilot); evidence: `scorer/pilot-evidence/fenced-repilot/` (`scores.json` scored 2026-11-27T17:50:00Z, `variance.txt`, `label-map.json`, `latency-log.jsonl`, `tool-log.jsonl`, `contamination-narrow.txt`, `fence.txt`, `SHA256SUMS`). Gate decision dated 2026-11-27, scorer commit `ce7f054`.

The two earlier pilots are superseded and kept as evidence of why containment was needed: the first pilot (prompt `2d4f22e3`, no containment) had two runs touch #1861 and scored CEILING on the old 5.0 scale; the second (prompt `671e5db1`, web search available) is CONTAMINATED under the literal rule (one `gh issue view 1861`, one `git show` of a sibling-language commit) and its h4-5 re-check leaked #1861 through `brave_search` (`h45-control-r3`). Only their `claude-haiku-4-5` control readings are reused below, as the floor reading at n = 4.

Per-criterion headroom over the fenced re-pilot (4 runs; `variance.txt`):

| Criterion | n | min | max | mean | variance |
|---|---|---|---|---|---|
| C3 | 4 | 0.0 | 1.0 | 0.5 | 0.25 |
| C4 | 4 | 0.6 | 0.75 | 0.6482 | 0.0038 |
| C5 | 4 | 0.0 | 0.0 | 0.0 | 0.0 |
| C6 | 4 | 0.8521 | 1.0 | 0.9302 | 0.0049 |
| C7 | 4 | 0.0 | 0.8 | 0.55 | 0.1075 |
| C7.workspace_dependency | 4 | 0.0 | 1.0 | 0.5 | 0.25 |
| C7.unconditional_dependency | 4 | 0.0 | 1.0 | 0.75 | 0.1875 |
| C7.extension_map_entry | 4 | 0.0 | 1.0 | 0.75 | 0.1875 |
| C7.mod_registration | 4 | 0.0 | 0.0 | 0.0 | 0.0 |
| C7.match_arms | 4 | 0.0 | 1.0 | 0.75 | 0.1875 |

Per-run scores (`scores.json`, mapped by argv order; cost from `fence.txt`):

| run | C3 | C4 | C5 | C6 | C7 | primary_total | total | cost USD | tool requests | failure_mode |
|---|---|---|---|---|---|---|---|---|---|---|
| h45-control | 0.0 | 0.75 | 0.0 | 1.0 | 0.8 | 0.75 | 2.55 | 0.2263425 | 40 | none |
| h45-treatment | 1.0 | 0.6 | 0.0 | 1.0 | 0.6 | 1.6 | 3.2 | 0.19733615 | 36 | none |
| h55-control | 1.0 | 0.6429 | 0.0 | 0.8688 | 0.0 | 1.6429 | 2.5116 | 0.15489437 | 36 | none |
| h55-treatment | 0.0 | 0.6 | 0.0 | 0.8521 | 0.8 | 0.6 | 2.2521 | 0.081134605 | 36 | none |

Gate arithmetic on `primary_total` (0 to 3.0), band [0.9, 2.1] (the 0.3 to 0.7 band), control run only (n = 1 per model), two numbers per model:

| Model | control primary_total | treatment primary_total | control in [0.9, 2.1]? |
|---|---|---|---|
| `claude-haiku-4-5` | 0.75 | 1.6 | no: below 0.9 |
| `claude-haiku-5-5` | 1.6429 | 0.6 | yes |

Verdict (2026-11-27, scorer commit `ce7f054`): FLOOR on the `claude-haiku-4-5` control; `claude-haiku-5-5` is inside the band. No run has a `failure_mode`; total pilot cost 0.6597 USD. Contamination scan under the narrowed rule: 0 hits in all four runs; `gh-fence.log` blocked attempts: 0 in all four runs (the file was never created); `git remote -v` empty and HEAD at the pin in all four clones (`fence.txt`).

Model-level finding, `claude-haiku-4-5` control floor (n = 4): the fenced re-pilot control reads 0.75 and the three earlier controls read 0.75 (re-pilot, prompt `671e5db1`), 1.00 (`h45-control-r2`) and 0.75 (`h45-control-r3`); 0.75, 0.75, 1.00, 0.75; mean 0.8125; all four below 0.9. The reading is named a floor. Of the four, only `h45-control-r3` is a contamination hit under the narrowed rule (a `brave_search` response returned #1861); the admissible reading is 0.75, 0.75, 1.00 (mean 0.8333), also all below 0.9. C3 is 0.0 in all four controls (the element query does not compile or matches nothing) and C5 is 0.0 in all four. A floor on one model is a reported model-level finding, not a gate failure: the PHP task is kept, the main run uses both models, and the finding is reported with the results.

Output overlap per pilot run (Jaccard, threshold 0.8; method in Exclusions):

| run | element_query_draft | defuse_query_draft | excluded? |
|---|---|---|---|
| h45-control | 0.0321 (6 of 187) | 0.0107 (2 of 187) | no |
| h45-treatment | 0.0321 (6 of 187) | 0.0107 (2 of 187) | no |
| h55-control | 0.0321 (6 of 187) | 0.0374 (7 of 187) | no |
| h55-treatment | 0.0321 (6 of 187) | 0.0267 (5 of 187) | no |

Other pilot-dependent values fixed by this evidence: floor and ceiling list (Floor and Ceiling Rule), overlap threshold (Exclusions), bootstrap seed and resample count (Statistical Analysis), cost table (Cost Reporting), pooling estimator (Pooling and Interaction), turn cap (Stopping Rule).

## Deposit

The deposit is the `experiments/exp5-php-grammar-powered/` package: `protocol.md`, `PRE-REGISTRATION.md`, `AMENDMENTS.md`, `plans/main.csv`, `gen_recipes.py`, `run.py`, `runner-prompt.md`, `scorer/`, `analysis/` and `tests/`, with metadata in `.zenodo.json`. The pre-registration files and their per-file sha256 values (`shasum -a 256` run from the experiment directory) are listed in `PRE-REGISTRATION.md`; the `plans/main.csv` sha256 there is the plan hash. The Zenodo DOI is recorded in `PRE-REGISTRATION.md` by the owner at deposit, before the first main-run spawn, and the deposit timestamp must be earlier than the earliest `sealed_at` in `label-map.json`.

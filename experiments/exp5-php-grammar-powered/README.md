# Experiment 5: PHP Grammar Scout with a Model Factor

Exp5 asks the Exp1 to Exp4 question (does a verbatim second copy of the prompt improve delegate task success?) with two changes: the task is the PHP grammar scout task, clouatre-labs/aptu-coder#1864, and the model is a factor, with `claude-haiku-4-5` and `claude-haiku-5-5` each getting a control and a treatment arm.

## Design

- **Prompt.** The body of `runner-prompt.md` (the text after the `---` line) is the user `prompt` of every recipe, byte for byte and identical across arms. Its only placeholder is `{output_path}`, a relative path inside the clone.
- **Control instructions.** One line: `Follow the task instructions given in the initial prompt exactly as written.`
- **Treatment instructions.** That line, a blank line, then a byte-verbatim second copy of the whole prompt body. This repeats the task instructions as Exp1 to Exp3 did; Exp4 repeated the user `prompt` block instead.
- **Settings.** Provider `anthropic`, model from the plan, temperature 0.5, extensions `developer` and `context7`. No web search: `brave_search` was removed after the first pilot, when a search result surfaced upstream #1861. No `thinking_effort` key (goose 1.61.1 drops it from recipe settings).
- **Sealing.** `run.py` refuses to spawn if any recipe differs from what the current plan and prompt generate, then writes and hashes `label-map.json` before the first spawn.
- **Isolation.** Each run gets a fresh clone of aptu-coder at `132ea687e09a916091699a562da3c96c86ec1fd8` under an untracked scratch dir, hooks disabled, and its remote is removed after checkout so nothing can be fetched past the pin. The experiment worktree is never the target.
- **Containment.** The delegate's `gh` is a shim at `<clone>/.exp5-fence/bin/gh`, first on `PATH`. It passes `gh issue view ... 1864`, `gh api` against `tree-sitter/tree-sitter-php` only, `--version` and `auth status`; every other GitHub read (`pr`, `search`, `issue list`, any `clouatre-labs` endpoint, anything mentioning 1861 or a pull request) exits 77 and appends `BLOCKED: <args>` to `<clone>/.exp5-fence/gh-fence.log`. The fence log is evidence: a blocked attempt is recorded, not silently dropped. Residual path: the `developer` shell tool can still `curl` arbitrary URLs; the post-run transcript scan for leak patterns covers it and the protocol names it as a threat.

## Files

`gen_recipes.py` (plan CSV to recipes), `run.py` (seal, spawn, backfill), `runner-prompt.md`, `plans/` (`main.csv` with 80 runs, `pilot.csv` with 4 runs, `pilot-h45-recheck.csv`, `smoke-haiku45.csv`), `tests/`, `scorer/` (offline scorer, rubric record `HEADROOM-pilot.md`, pilot evidence), `analysis/` (statistics and cost). Generated and not tracked: `recipes/recipe-*.yaml`, `label-map.json`, `latency-log.jsonl`, `tool-log.jsonl`.

## Commands

```bash
cd experiments/exp5-php-grammar-powered
uv sync
uv run pytest
uv run python -m pyflakes gen_recipes.py run.py tests
uv run gen_recipes.py --plan plans/pilot.csv
uv run run.py --plan plans/pilot.csv --scratch /tmp/exp5-scratch --concurrency 2
```

`run.py` options: `--recipes-dir`, `--out-dir` (default: this directory), `--scratch` (required, untracked), `--sessions-db`, `--concurrency` (default 2), `--max-turns` (sets `GOOSE_MAX_TURNS` on the child; 0 leaves the variable unset so goose applies its own configured default, 1000 at the time of writing), `--timeout` (seconds per run; 0 means none), `--goose`. Credentials come from the environment only (`ANTHROPIC_API_KEY`, `CONTEXT7_API_KEY`, `BRAVE_API_KEY`); nothing writes them to a file.

## Exp5

The pre-registration package is `protocol.md` (fixed design, 13 sections, every pilot-dependent value filled from the fenced re-pilot, #105), `PRE-REGISTRATION.md` (file list with sha256, DOI), `AMENDMENTS.md` (one pre-deposit amendment, #131: mechanical contamination exclusion, output overlap descriptive), `plans/main.csv` (80 runs) and `.zenodo.json`.

Pilot (4 runs, fenced instrument, the run that `protocol.md` cites):

```bash
uv run gen_recipes.py --plan plans/pilot.csv
uv run run.py --plan plans/pilot.csv --scratch /tmp/exp5-fenced-pilot --out-dir /tmp/exp5-fenced-pilot/out --concurrency 2 --max-turns 60
```

Pilot result (`scorer/HEADROOM-pilot.md`, evidence `scorer/pilot-evidence/fenced-repilot/`, 2026-11-27; `primary_total = C3 + C4 + C5` on the 3.0 scale, gate band [0.9, 2.1] on the control):

| run | C3 | C4 | C5 | primary_total | primary_total minus C5 | total | cost USD |
|---|---|---|---|---|---|---|---|
| h45-control | 0.0 | 0.75 | 0.0 | 0.75 | 0.75 | 2.55 | 0.2263425 |
| h45-treatment | 1.0 | 0.6 | 0.0 | 1.6 | 1.6 | 3.2 | 0.19733615 |
| h55-control | 1.0 | 0.6429 | 0.0 | 1.6429 | 1.6429 | 2.5116 | 0.15489437 |
| h55-treatment | 0.0 | 0.6 | 0.0 | 0.6 | 0.6 | 2.2521 | 0.081134605 |

Gate verdict: FLOOR. The `claude-haiku-4-5` control (0.75, and 0.75 / 0.75 / 1.00 / 0.75 over four controls including the three earlier ones, mean 0.8125) is below 0.9; `claude-haiku-5-5` (1.6429) is inside the band. The floor is a model-level finding, not a stop condition: the main run proceeds with both models. C5 is 0.0 in every run, so `primary_total` minus C5 is the co-reported outcome. No contamination hit (0 hits in all four runs, confirmed by `analysis/contamination.py` on the committed exports under `analysis/tests/fixtures/transcripts/`) and no blocked `gh` call in any run.

Main run (80 runs, interleaved within model, `--max-turns 60` in both arms, only after the DOI is recorded in `PRE-REGISTRATION.md`):

```bash
uv run gen_recipes.py --plan plans/main.csv
uv run run.py --plan plans/main.csv --scratch /tmp/exp5-main-scratch --concurrency 2 --max-turns 60
```

Before scoring and analysis, export each run's output and transcript to `outputs/<run_id>/` (the scratch clones are disposable; `run.py` leaves `exp5-output.json` inside each clone and the analysis reads `outputs/<run_id>/exp5-output.json` for the overlap value and `outputs/<run_id>/transcript.json` for the contamination scan):

```bash
for row in $(jq -r '.assignments | to_entries[] | "\(.key) \(.value.goose_session_id)"' label-map.json); do
  set -- $row
  mkdir -p "outputs/$1"
  cp "/tmp/exp5-main-scratch/$1/aptu-coder/exp5-output.json" "outputs/$1/exp5-output.json"
  goose session export --session-id "$2" --format json -o "outputs/$1/transcript.json"
done
```

A run with `failure_mode` has no backfilled session id and nothing to export; it is excluded by the analysis on its `failure_mode` alone.

`label-map.json` seals `sha256_runner_prompt`, `sha256_scorer` and `sha256_analysis` before the first spawn; the last two are the `tree_sha256` of `scorer/` and `analysis/`.

## How a run is recorded

1. `label-map.json` is written before any spawn. `assignments[run_id]` holds `group`, `model`, `goose_session_id` (null at seal time), `sealed_at`, `sha256_runner_prompt`, `sha256_scorer` and `sha256_analysis` (the `tree_sha256` of `scorer/` and `analysis/` at seal time) and `concurrency_limit`. The top-level `sha256` hashes the assignments block with every `goose_session_id` set to null, so it stays verifiable after backfill.
2. goose runs as `goose run --recipe <recipe-NN.yaml> --name exp5-<run_id> --debug --output-format json` with the clone as working directory. goose stdout is kept at `<scratch>/<run_id>/goose-stdout.txt`.
3. A non-zero exit, timeout or clone failure appends one `latency-log.jsonl` row with `failure_mode` and nothing backfilled. Failed runs are never retried or dropped.
4. On exit 0 the session is resolved by `sessions.name = 'exp5-<run_id>'` equality and must match exactly one row. Token, cache and cost columns are copied into the row, and `tool-log.jsonl` gets one row per tool request with the tool name and target only.

Missing values are `null`, never NaN.

## Smoke test (2026-11-27)

Two one-turn runs via `plans/smoke-haiku45.csv`, goose 1.61.1, `GOOSE_MAX_TURNS=1`, scratch dir `/tmp/exp5-smoke`. Total live runs: 2.

```bash
uv run gen_recipes.py --plan plans/smoke-haiku45.csv --out /tmp/exp5-smoke/recipes
uv run run.py --plan plans/smoke-haiku45.csv --recipes-dir /tmp/exp5-smoke/recipes \
  --out-dir /tmp/exp5-smoke/out --scratch /tmp/exp5-smoke/scratch --concurrency 2 --max-turns 1
```

| Run | Model id accepted | goose exit | Session | thinking_tokens | Cache fields |
|---|---|---|---|---|---|
| `smoke-h45` | yes | 1 | `20261127_70` | `null` (`not_captured`; 0 thinking blocks) | `cache_read_tokens` 0, `cache_write_tokens` 21705 |
| `smoke-h55` | yes | 1 | `20261127_71` | `null` (`not_captured`; 1 thinking block, 126 chars) | `cache_read_tokens` 0, `cache_write_tokens` 28546 |

- **Both model ids are valid** for the anthropic provider in goose 1.61.1: each session reports `requestedModel` equal to the requested id, with temperature 0.5.
- **Exit 1 is the turn cap, not a rejection.** With `GOOSE_MAX_TURNS=1` goose stops after one turn with `Error: I've reached the maximum number of actions I can do without user input` and exits 1. The harness logged both as `goose_exit_1` with no backfill, as designed; the cache fields above were read from the two named sessions afterwards. The cap of 1 was used only to prove the harness end to end at minimal cost. goose honours `GOOSE_MAX_TURNS=0` literally (a zero limit yields before inference), so `run.py` never exports it when `--max-turns` is 0; a real run uses either 0 or the cap pre-registered in `protocol.md`, identical in both arms.
- **Session mapping by name works**: each `--name exp5-<run_id>` resolved to exactly one `sessions` row, and no session id was parsed from stdout.
- **Thinking tokens are not observable.** goose JSON `metadata` carries `total_tokens`, `input_tokens`, `output_tokens`, `cache_read_input_tokens`, `cache_write_input_tokens`, `cost_usd` and `status`; per-message usage carries the same token fields plus timing. Neither has a thinking or reasoning token count, so `thinking_tokens` is `null` and `thinking_capture` is `not_captured`. `thinking_blocks` and `thinking_chars` are recorded as a proxy: haiku-5-5 emitted one thinking block, haiku-4-5 none.
- **The fresh clones were at the pin** and clean after the runs.

The fenced re-pilot that followed (2026-11-27) is recorded in `scorer/HEADROOM-pilot.md`; the scorer and analysis trees are sealed by hash at run time, and any change to them after deposit is recorded in `AMENDMENTS.md`.

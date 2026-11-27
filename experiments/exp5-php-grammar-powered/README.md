# Experiment 5: PHP Grammar Scout with a Model Factor

Exp5 asks the Exp1 to Exp4 question (does a verbatim second copy of the prompt improve delegate task success?) with two changes: the task is the PHP grammar scout task, clouatre-labs/aptu-coder#1864, and the model is a factor, with `claude-haiku-4-5` and `claude-haiku-5-5` each getting a control and a treatment arm.

## Design

- **Prompt.** The body of `runner-prompt.md` (the text after the `---` line) is the user `prompt` of every recipe, byte for byte and identical across arms. Its only placeholder is `{output_path}`, a relative path inside the clone.
- **Control instructions.** One line: `Follow the task instructions given in the initial prompt exactly as written.`
- **Treatment instructions.** That line, a blank line, then a byte-verbatim second copy of the whole prompt body. This repeats the task instructions as Exp1 to Exp3 did; Exp4 repeated the user `prompt` block instead.
- **Settings.** Provider `anthropic`, model from the plan, temperature 0.5, extensions `developer`, `context7` and `brave_search`. No `thinking_effort` key (goose 1.61.1 drops it from recipe settings).
- **Sealing.** `run.py` refuses to spawn if any recipe differs from what the current plan and prompt generate, then writes and hashes `label-map.json` before the first spawn.
- **Isolation.** Each run gets a fresh clone of aptu-coder at `132ea687e09a916091699a562da3c96c86ec1fd8` under an untracked scratch dir, hooks disabled. The experiment worktree is never the target.

## Files

`gen_recipes.py` (plan CSV to recipes), `run.py` (seal, spawn, backfill), `runner-prompt.md`, `plans/` (`pilot.csv` with 4 runs, `smoke-haiku45.csv`), `tests/`. Generated and not tracked: `recipes/recipe-*.yaml`, `label-map.json`, `latency-log.jsonl`, `tool-log.jsonl`.

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

The pre-registration package is `protocol.md` (fixed design, 13 sections), `PRE-REGISTRATION.md`, `AMENDMENTS.md` (empty at deposit), `plans/main.csv` (80 runs) and `.zenodo.json`. Every value that waits on the pilot is a `PILOT:` token in `protocol.md`.

Pilot (4 runs):

```bash
uv run gen_recipes.py --plan plans/pilot.csv
uv run run.py --plan plans/pilot.csv --scratch /tmp/exp5-scratch --concurrency 2
```

Main run (80 runs, interleaved within model):

```bash
uv run gen_recipes.py --plan plans/main.csv
uv run run.py --plan plans/main.csv --scratch /tmp/exp5-main-scratch --concurrency 2
```

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

Not yet done: the pilot itself and the analysis of its results. The scorer and analysis trees are sealed by hash at run time and may still change after the pilot, which `AMENDMENTS.md` would record.

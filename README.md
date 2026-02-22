# Prompt Repetition Experiments

Supplementary materials for [What a Null Result Taught Us About AI Agent Evaluation](https://clouatre.ca/posts/prompt-repetition-agent-evaluation/).

## Key Findings

- **Null result across both experiments.** Prompt repetition (repeating delegate instructions verbatim) produced no measurable accuracy improvement on structured engineering tasks.
- **Ceiling effects dominate.** Well-scoped tasks with clear rubrics hit 100% accuracy in both control and treatment groups, leaving no room for improvement.
- **The evaluation design is the finding.** Rubric discrimination, not prompt engineering, determines whether an experiment can detect signal.

## Background

[Leviathan et al. (2025)](https://arxiv.org/abs/2502.07869) found that repeating instructions in LLM prompts improves accuracy on positional retrieval tasks. We tested whether this transfers to structured engineering tasks executed by parallel AI agents (Goose delegates running Claude Haiku 4.5).

## Experimental Design

Two experiments, 10 parallel delegates each, blind-scored against rubrics:

| | Experiment 1 | Experiment 2 |
|---|---|---|
| **Task** | FastMCP session ID refactor analysis | Tree-sitter AST scanner code synthesis |
| **Repo** | clouatre-labs/math-mcp-learning-server#222 | clouatre-labs/aptu#737 |
| **Type** | Source analysis (read-only) | Code generation (write) |
| **Groups** | 5 control, 5 treatment | 5 control, 5 treatment (blinded run IDs) |
| **Rubric** | 6 binary criteria | 7 binary criteria |
| **Result** | 5/6 criteria at 100% both groups | 7/7 criteria at 100% both groups |
| **Valid runs** | 9 of 10 (1 drift failure) | 5 of 10 (5-delegate concurrency cap) |

Full methodology in [METHODOLOGY.md](METHODOLOGY.md).

## Project Structure

```
prompt-repetition-experiments/
  README.md              # This file
  METHODOLOGY.md         # Experimental design, rubrics, scoring protocol
  LICENSE                # Apache 2.0
  recipe/
    goose-coder-v4.1.0.yaml   # Goose recipe used for orchestration
  experiments/
    exp1-fastmcp-refactor/
      analysis.json      # Aggregated results and per-run metadata
      scores.json        # Blind scorer output with justifications
      label-map.json     # Group assignments (sealed before scoring)
      sessions/          # Structured delegate outputs (scored artifacts)
        scout-control-{2..5}.json    # Control group (1 excluded: drift)
        scout-treatment-{1..5}.json  # Treatment group
      raw/               # Full conversation logs (sanitized)
        orchestrator.jsonl           # Experiment orchestration (265 messages)
        scorer.jsonl                 # Blind scoring session
        scout-control-{1..5}.jsonl   # Control delegate conversations
        scout-treatment-{1..5}.jsonl # Treatment delegate conversations
    exp2-treesitter-synthesis/
      analysis.json      # Aggregated results and per-run metadata
      scores.json        # Blind scorer output with justifications
      label-map.json     # Group assignments (sealed before scoring)
      sessions/          # Structured delegate outputs (scored artifacts)
        scout-run-{01..10}.json      # Blinded run IDs
      raw/               # Full conversation logs (sanitized)
        orchestrator.jsonl           # Experiment orchestration (419 messages)
        scorer.jsonl                 # Blind scoring session
        setup.jsonl                  # Experiment setup session
        utility-{1..2}.jsonl         # Utility sessions
        scout-run-{01..10}.jsonl     # Delegate conversations (blinded)
        scout-run-08-retry.jsonl     # Retry of run-08
```

## Data Files

### Recipe

- **`recipe/goose-coder-v4.1.0.yaml`** -- The Goose recipe defining the Scout/Guard subagent architecture. Scouts run on `claude-haiku-4-5` at temperature 0.5 with extended thinking off.

### Per-Experiment Files

- **`analysis.json`** -- Experiment metadata: issue reference, model, dates, per-run timing/token counts, aggregate statistics, and statistical tests.
- **`scores.json`** -- Blind scorer output: per-criterion binary scores (0/1) with natural-language justifications for each run.
- **`label-map.json`** -- Group assignments sealed before scoring began. Maps run IDs to control/treatment groups.
- **`sessions/*.json`** -- Structured delegate outputs. Each file contains the research findings produced by one Scout delegate. These are the artifacts scored by the rubric.
- **`raw/*.jsonl`** -- Full message-by-message conversation logs exported from Goose's session database. Includes tool calls, intermediate reasoning, and errors. Home directory paths sanitized to `$EXPERIMENTER_HOME`. Orchestrator logs show the 5-delegate concurrency cap in action (batch 1 spawned, cap hit, batch 2 spawned after batch 1 completes).

## Reproduction

These experiments used [Goose](https://github.com/block/goose) with the recipe in `recipe/`. To inspect the data:

```bash
# Clone
git clone https://github.com/clouatre-labs/prompt-repetition-experiments.git
cd prompt-repetition-experiments

# View experiment 1 scores
cat experiments/exp1-fastmcp-refactor/scores.json | python3 -m json.tool

# View experiment 2 group assignments
cat experiments/exp2-treesitter-synthesis/label-map.json | python3 -m json.tool

# Compare control vs treatment in experiment 1
jq '.scores[] | {run_id, total}' experiments/exp1-fastmcp-refactor/scores.json
```

Exact reproduction requires access to the target repositories at the commit SHAs recorded in each `analysis.json`.

## Citation

```bibtex
@misc{clouatre2026promptrepetition,
  title   = {What a Null Result Taught Us About AI Agent Evaluation},
  author  = {Clouatre, Hugues},
  year    = {2026},
  url     = {https://clouatre.ca/posts/prompt-repetition-agent-evaluation/},
  note    = {Supplementary materials: https://github.com/clouatre-labs/prompt-repetition-experiments}
}
```

## License

[Apache License 2.0](LICENSE)

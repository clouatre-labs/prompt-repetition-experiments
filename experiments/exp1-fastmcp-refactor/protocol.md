# Experiment 1: FastMCP Session ID Refactor Analysis

**Pre-registered protocol -- locked before any delegates were spawned.**

---

## Context

This experiment tests whether [prompt repetition](https://arxiv.org/abs/2502.07869) (repeating delegate instructions verbatim) improves AI agent accuracy on a structured engineering research task.

The paper reports that repeating the input prompt verbatim improves non-reasoning LLM accuracy (47/70 wins, 0 losses across 7 models). This experiment applies the technique to a real-world engineering task executed by parallel AI agent delegates.

## Target

[clouatre-labs/math-mcp-learning-server#222](https://github.com/clouatre-labs/math-mcp-learning-server/issues/222) -- open, unimplemented as of this issue creation. No merged PR exists, so Scout delegates cannot find the answer via web search. Zero cheating risk.

Issue asks Scout to:
- Find `id(ctx.lifespan_context)` anti-pattern across source files
- Identify the correct FastMCP replacement API (`ctx.set_state` / `ctx.get_state`)
- Consult FastMCP docs (new enough that parametric knowledge is unreliable)
- Capture the Must-Not constraints from the issue

This exercises exactly the research depth where attention to full prompt context matters.

## Method

Single Goose orchestrator session. No recipe file needed.

1. Clone `clouatre-labs/math-mcp-learning-server` at current HEAD (issue #222 open)
2. Spawn 10 async Scout delegates in parallel:
   - 5 control: current Scout instructions from `goose-coder.yaml`
   - 5 treatment: same instructions repeated verbatim twice (paper's exact technique)
   - All delegates: `developer` + `context7` + `brave_search` extensions, Haiku 4-5, temp 0.5
   - Each writes to a unique handoff file: `scout-control-{1-5}.json` / `scout-treatment-{1-5}.json`
3. Wait for all 10 to complete
4. Spawn scoring delegate: reads all 10 outputs, scores against rubric below

## Scoring Rubric

Binary criteria, 0 or 1 each, max score 6 per run:

| # | Criterion | Expected value |
|---|---|---|
| C1 | Source file 1 identified | `src/math_mcp/tools/persistence.py` |
| C2 | Source file 2 identified | `src/math_mcp/tools/calculate.py` |
| C3 | Anti-pattern found | `id(ctx.lifespan_context)` |
| C4 | Replacement API correct | `ctx.set_state` / `ctx.get_state` with UUID |
| C5 | Must-Not constraint captured | non-serializable values, process-restart caveat |
| C6 | FastMCP docs consulted | `gofastmcp.com/servers/context` or equivalent |

Scoring delegate outputs:
- Per-run scores (control 1-5, treatment 1-5)
- Average score: control vs treatment
- Verdict: improvement / wash / regression

## Gate

- Average treatment score > average control score on 2+ criteria: proceed with Scout instruction repetition in the recipe
- Wash or regression: no recipe change, close with "no benefit found"

## Implementation Note

After this experiment completes, use the highest-scoring Scout output (control or treatment) as the research input for the actual engineering task on math-mcp-learning-server#222. The experiment produces useful work, not throwaway output.

## References

- Leviathan, Y. et al., "Prompt Repetition Improves Non-Reasoning LLMs" (2025) -- https://arxiv.org/abs/2502.07869
- Target issue: https://github.com/clouatre-labs/math-mcp-learning-server/issues/222

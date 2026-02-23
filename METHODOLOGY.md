# Methodology

Experimental design and scoring protocol for the prompt repetition agent evaluation.

## Research Question

Does repeating delegate instructions verbatim (prompt repetition) improve accuracy on structured engineering tasks executed by parallel AI agents?

Based on [Leviathan et al. (2025)](https://arxiv.org/abs/2502.07869), which found that repeating queries in LLM prompts improves accuracy on positional retrieval tasks.

## Agent Architecture

All experiments used the [Goose](https://github.com/block/goose) agent framework with a Scout/Guard subagent architecture defined in `recipe/goose-coder-v4.1.0.yaml`.

- **Orchestrator:** Claude Sonnet 4.6 at temperature 0.3 via GCP Vertex AI
- **Delegates (Scouts):** Claude Haiku 4.5 at temperature 0.5 via GCP Vertex AI
- **Extensions:** developer, context7, brave_search

The orchestrator spawned 10 async delegates per experiment. Each delegate received identical instructions except for the treatment condition (instructions repeated x2).

## Experimental Protocol

### Shared Design

1. Select an open, unimplemented GitHub issue as the target task
2. Define a binary rubric (pass/fail per criterion) before examining any output
3. Seal group assignments in a `label-map.json` before scoring begins
4. Spawn 10 parallel delegates: 5 control, 5 treatment
5. Collect structured JSON output from each delegate
6. Blind-score all outputs against the rubric (scorer receives no group labels)
7. Reveal group assignments and compute statistics

### Control Condition

Standard Scout instructions (single occurrence). Experiment 1: ~3,805 characters. Experiment 2: ~3,399 characters.

### Treatment Condition

Scout instructions repeated verbatim (x2), mimicking the paper's `<QUERY><QUERY>` pattern applied to the delegate system prompt. Experiment 1: ~7,633 characters. Experiment 2: ~6,806 characters.

### Blind Scoring

A separate Claude Haiku 4.5 instance scored each output file against the rubric. The scorer received only the output JSON and the rubric criteria. No group labels, no run metadata, no other outputs were visible during scoring.

## Experiment 1: FastMCP Session ID Refactor

### Target

[clouatre-labs/math-mcp-learning-server#222](https://github.com/clouatre-labs/math-mcp-learning-server/issues/222): FastMCP session ID refactor. Source analysis task (read-only). Open and unimplemented at experiment time.

### Rubric (6 Binary Criteria)

| Criterion | Description |
|---|---|
| C1 | Session ID persistence correctly identified and addressed |
| C2 | Calculation logic preserved across refactored session handling |
| C3 | Anti-pattern correctly identified in existing implementation |
| C4 | FastMCP API usage correct per documentation |
| C5 | Non-serializable value problem explicitly named |
| C6 | Documentation updates included |

### Valid Runs

9 of 10. `control-1` drifted at 93 messages and produced no output file. Root cause: the file-write instruction appeared only at the end of the delegate prompt, and the model drifted past it.

### Results

5 of 6 criteria scored 100% in both groups. C5 showed minor variance: control 5.50/6, treatment 5.80/6, delta +0.30. Fisher's exact test: p = 1.0 (degenerate at n=4 vs n=5 with binary outcomes).

### Orchestrator Session

Session ID: `20260220_29`. Recorded in `analysis.json`.

## Experiment 2: Tree-sitter AST Scanner Evaluation

### Target

[clouatre-labs/aptu#737](https://github.com/clouatre-labs/aptu/issues/737): tree-sitter AST-based security scanner evaluation. Code synthesis task (write). Open and unimplemented at experiment time. Harder than Experiment 1: required synthesis from source code rather than retrieval from issue text.

### Methodology Improvements Over Experiment 1

- Blinded file naming from the start (`scout-run-01.json` through `scout-run-10.json`)
- Mann-Whitney U test pre-specified (two-tailed, alpha = 0.05)
- Wall-clock latency recorded per delegate
- Interleaved group assignment (odd = control, even = treatment)

### Rubric (7 Binary Criteria)

| Criterion | Description |
|---|---|
| C1 | Regex-based scanning limitation identified and documented (issues #735/#736) |
| C2 | tree-sitter, tree-sitter-rust, and tree-sitter-python named explicitly |
| C3 | Hybrid approach proposed preserving existing regex patterns |
| C4 | Binary bloat from grammar crates explicitly mentioned as trade-off |
| C5 | Multi-language progressive support path specified |
| C6 | Specific codebase files referenced (scanner.rs, patterns.rs, patterns.json, detection) |
| C7 | Success criteria clearly specified with concrete test case |

C5, C6, and C7 were specifically designed to require source code reasoning, not just issue text summarization.

### Valid Runs

5 of 10. Goose enforces a hard cap of 5 concurrent background delegates. Runs 06-10 were queued into a second batch after runs 01-05 completed. This was an undocumented infrastructure constraint discovered post-hoc.

### Results

All valid runs scored 7/7 in both groups. Mann-Whitney U = 12.5, p = 1.0 (degenerate: complete ties).

| Group | Score | Wall-clock Median |
|---|---|---|
| Control (x1) | 7/7 all runs | 6m 21s |
| Treatment (x2) | 7/7 all runs | 7m 29s |
| Delta | 0 | +18% |

The 18% latency increase is consistent with the paper's Anthropic-specific latency caveat (longer prompt, longer prefill).

### Orchestrator Session

Session ID: `20260220_43`. Recorded in `analysis.json`.

## Known Limitations

1. **Ceiling effects.** Both rubrics were too easy. 100% accuracy in both groups leaves no room for treatment effects.
2. **Small sample size.** n=5 per group is underpowered for detecting small effects.
3. **Infrastructure confound.** Goose enforces an undocumented 5-delegate concurrency cap (`GOOSE_MAX_BACKGROUND_TASKS` defaults to 5) as a hard rejection with no queuing. Excess delegates are dropped, not deferred, which silently split our groups into unbalanced batches.
4. **Single model.** All experiments used Claude Haiku 4.5. Results may not generalize to other models.
5. **Session log loss.** Experiment 2 `.jsonl` session logs were purged from disk before archival. Per-run message and token counts were reconstructed from SQLite session metadata.

## Software Versions

| Component | Version |
|---|---|
| Goose | 1.25.0 |
| Claude Haiku 4.5 | `claude-haiku-4-5@20251001` |
| Claude Sonnet 4.6 | `claude-sonnet-4-6@default` |
| Provider | GCP Vertex AI |
| Recipe | goose-coder v4.1.0 |

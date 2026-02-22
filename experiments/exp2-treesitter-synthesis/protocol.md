# Experiment 2: Tree-sitter AST Scanner Evaluation

**Pre-registered protocol -- locked before any delegates were spawned.**

This is the second experiment in the prompt repetition series, designed to address the ceiling effect observed in [Experiment 1](../exp1-fastmcp-refactor/protocol.md).

---

## Context

The first experiment (FastMCP refactor analysis) produced a null result because the task was too easy: C1-C4 and C6 hit 100% in both groups. This experiment targets a harder issue that requires synthesis across the codebase, external API research, and judgment under ambiguity -- not just information retrieval. Ceiling effect is unlikely.

Paper: [Leviathan et al. (2025)](https://arxiv.org/abs/2502.07869) -- repeating the input prompt verbatim improves non-reasoning LLM accuracy (47/70 wins, 0 losses across 7 models).

## Why This Task is Harder

[clouatre-labs/aptu#737](https://github.com/clouatre-labs/aptu/issues/737) requires:

- Reading the existing `SecurityScanner` implementation across `crates/aptu-core/`
- Understanding 14 regex patterns and identifying which ones require multi-line detection (not stated in the issue -- requires reading actual pattern code)
- Researching tree-sitter Rust bindings (tree-sitter 0.24, tree-sitter-rust 0.23 -- recent enough that parametric knowledge is unreliable)
- Assessing hybrid vs. full-migration tradeoff with concrete evidence from the codebase
- Recognizing that data-flow/taint tracking is NOT solved by tree-sitter alone (a non-obvious constraint)
- Evaluating binary size impact from grammar crates (~5-10 languages)

No single correct answer exists. Scout must synthesize, not retrieve.

---

## Pre-registration (locked before any runs)

All decisions below are final. No post-hoc amendments after the first delegate is spawned.

### Sample size and stopping rule

- Fixed n: 10 valid runs total (5 control, 5 treatment)
- No sequential expansion regardless of delta magnitude
- Stopping rule is fixed; no early stopping

### Invalid run policy

- An invalid run is defined as: delegate completes but writes no output file, or output file is not valid JSON
- Execution failures (infrastructure noise) may be re-run, up to 5 total attempts per group (i.e. up to 5 re-runs per group to achieve 5 valid runs)
- All attempts (valid and invalid) must be logged with timestamps and failure reason
- Scoring failures (agent produced output but scored poorly) are NOT re-run -- they are signal, not noise
- If 5 valid runs cannot be achieved in a group after 5 total attempts, report actual n and note as limitation

### Blinding

- Output files named `scout-run-01.json` through `scout-run-10.json` (no control/treatment label in filename)
- A separate `label-map.json` file maps run numbers to group assignments, written before any delegates are spawned, sealed (not read by scoring delegate)
- Scoring delegate scores all 10 runs without access to `label-map.json`
- `label-map.json` is revealed only after all 10 scores are written to `scores.json`
- This must be enforced in the orchestration session instructions

### Statistical test

- Mann-Whitney U test, two-tailed, alpha = 0.05
- Applied to total scores (0-7) across the two groups
- With n=5 per group this test is underpowered for small effects -- a non-significant result does not rule out a small true effect; note this as a limitation
- Do not apply parametric tests (t-test) regardless of apparent normality given n=5

### Latency

- Record wall-clock start time and completion time per delegate (ISO 8601)
- Report median latency per group, not mean (resistant to outliers)
- Latency is a secondary metric only -- does not affect the verdict

### Raw data preservation

- All 10 `scout-run-{01-10}.json` files, `label-map.json`, `scores.json`, and the latency log published as a single GitHub gist before closing the issue
- Gist URL recorded in the issue comment alongside results

---

## Experimental Design

### Target

- Issue: [clouatre-labs/aptu#737](https://github.com/clouatre-labs/aptu/issues/737) (open, unimplemented -- zero cheating risk)
- Record repo HEAD SHA at time of first delegate spawn; all delegates use the same SHA
- Model: claude-haiku-4-5, temp 0.5
- Extensions: developer, context7, brave_search (identical across all delegates)

### Delegates

- 5 control: Scout instructions x1 (~3,805 chars, current goose-coder.yaml)
- 5 treatment: Scout instructions x2 (~7,633 chars, verbatim repetition)
- Each delegate clones clouatre-labs/aptu independently into a unique temp dir
- Files named `scout-run-{01-10}.json` with no group label in filename
- All 10 spawned async, collected after completion
- 1 scoring delegate reads all 10 outputs blind, writes `scores.json`, then `label-map.json` is revealed

### Rubric (pre-registered, 7-point binary)

| ID | Criterion | Ground truth |
|----|-----------|-------------|
| C1 | SecurityScanner implementation file identified | `crates/aptu-core/src/scanner.rs` or equivalent -- must be verified against actual repo structure, not assumed |
| C2 | Line-by-line regex limitation understood | references single-line constraint; cites [aptu#735](https://github.com/clouatre-labs/aptu/issues/735) or [PR #736](https://github.com/clouatre-labs/aptu/pull/736) or quotes the test |
| C3 | tree-sitter-rust version verified against Cargo.toml or Context7 docs | 0.23 (not assumed from issue text alone) |
| C4 | Hybrid vs. full-migration tradeoff articulated with codebase evidence | names specific patterns or files as evidence, not generic prose |
| C5 | At least 2 specific patterns identified as requiring multi-line detection | must name actual pattern IDs or descriptions from source code, not generic examples from the issue |
| C6 | Data-flow/taint tracking gap noted as unsolved by tree-sitter alone | explicit statement that AST traversal does not equal taint analysis |
| C7 | Binary size / grammar crate count estimated with specifics | names at least 3 target languages with their crate names (e.g. tree-sitter-python, tree-sitter-javascript) |

C5, C6, C7 require reading and synthesizing actual source code or verified external docs. They cannot be answered from the issue text alone.

Scoring is binary per criterion (1 = met, 0 = not met). Half-credit is not permitted.

---

## Success / Failure Gate

- **Lift detected**: treatment median >= control median + 1 point AND Mann-Whitney U p < 0.05
- **No lift**: delta < 1 point OR p >= 0.05
- **Ceiling effect again**: if C1-C4 hit 100% in both groups, rubric was still too easy -- note for next iteration, do not reinterpret as "no lift"

---

## Execution Notes

- Record the aptu HEAD SHA before spawning delegate 1; use that SHA for all delegates
- Each Scout delegate independently clones aptu -- no shared worktree state
- Orchestrator writes `label-map.json` before spawning any delegates; does not share it with scoring delegate
- Scoring delegate receives only the 10 run files and the rubric above
- After `scores.json` is written, orchestrator reveals `label-map.json` and computes group averages and Mann-Whitney U
- Preserve all outputs as a gist immediately after scoring, before /tmp is cleared

---

## Limitations (pre-acknowledged)

- n=5 per group is underpowered; Mann-Whitney U at this n has low power for effect sizes below ~1.5 points
- Scoring delegate is an LLM judge -- inter-rater reliability is not measured
- Single model (Haiku 4-5), single temperature (0.5), single issue -- results do not generalize beyond this configuration
- brave_search access means Scouts can find tree-sitter documentation online; this is a constant across groups, not a confound, but limits ecological validity for air-gapped environments

---

## References

- Leviathan, Y. et al., "Prompt Repetition Improves Non-Reasoning LLMs" (2025) -- https://arxiv.org/abs/2502.07869
- First experiment: [exp1-fastmcp-refactor](../exp1-fastmcp-refactor/protocol.md)
- Target issue: https://github.com/clouatre-labs/aptu/issues/737
- SecurityScanner context: [aptu#735](https://github.com/clouatre-labs/aptu/issues/735), [PR #736](https://github.com/clouatre-labs/aptu/pull/736)
- tree-sitter Rust: https://tree-sitter.github.io/tree-sitter/using-parsers/queries

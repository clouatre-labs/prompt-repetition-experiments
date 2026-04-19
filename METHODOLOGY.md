# Methodology

Experimental design and scoring protocol for the prompt repetition agent evaluation.

## Research Question

Does repeating delegate instructions verbatim (prompt repetition) improve accuracy on structured engineering tasks executed by parallel AI agents?

Based on [Leviathan et al. (2025)](https://arxiv.org/abs/2512.14982), which found that repeating queries in LLM prompts improves accuracy on positional retrieval tasks.

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

## Experiment 3: Kotlin Grammar Synthesis

### Target

[clouatre-labs/aptu#775](https://github.com/clouatre-labs/aptu/issues/775): add Kotlin language support to the tree-sitter AST scanner. Code synthesis task (write). Open and unimplemented at experiment time. Harder than Experiment 2: required deep source inspection of ABI compatibility, node kind taxonomy, and struct fields unavailable from the issue text alone.

### Methodology Improvements Over Experiment 2

- Hardened rubric after pilot audit: C1, C2, C6, and C7 rewritten to require evidence-backed synthesis, not description
- Invalid-run retry policy added: provider stream-decode errors trigger one retry on Bedrock fallback
- Latency and message counts recorded per run in latency-log.jsonl
- Post-experiment: identified rubric-runner co-design failure; C1, C5, C6 excluded from primary treatment comparison with disclosed structural rationale (see Post-hoc Criterion Exclusion below).

### Rubric (7 Binary Criteria)

| Criterion | Description | Synthesis Required |
|---|---|---|
| C1 | tree-sitter-kotlin 0.3.8 LANGUAGE export verified and ABI relationship with tree-sitter 0.26.6 fully characterized with evidence (semver ranges or crate source); incompatibility is a valid finding if documented | yes |
| C2 | Kotlin companion object node kind identified as object_declaration with companion modifier; delegation_specifiers children enumerated distinguishing superclass_type_with_constructor from user_type | yes |
| C3 | At least 3 query patterns from tree-sitter-kotlin corpus (function_declaration, class_declaration, object_declaration variants) correctly captured in ELEMENT_QUERY | yes |
| C4 | extract_inheritance handler correctly walks delegation_specifiers and separates superclass_type_with_constructor (has parens) from user_type (no parens) | yes |
| C5 | Unit tests confirm .kt AND .kts file parsing both work; at least 1 test with .kts syntax (e.g. top-level function, extension function) | yes |
| C6 | DEFUSE_QUERY constant created for Kotlin if required by current LanguageInfo struct, or justified as None if not applicable; must cite inspection of LanguageInfo struct fields or PR #659 | yes |
| C7 | All structural wiring described: feature flag included in default feature set, all required query constant names stated, EXTENSION_MAP entries present, mod.rs arms present, module registered | no |

### Valid Runs

10 of 10. Runs 04, 09, and 10 hit provider stream-decode errors and were retried once on Bedrock fallback per the invalid-run policy. All retried runs produced output and were included.

### Results

Neither group exceeded 34% mean pass rate. Mann-Whitney U = 15, p = 0.6072 (not significant).

| Group | Mean score | Median score | Wall-clock Median |
|---|---|---|---|
| Control (x1) | 2.0/7 (29%) | 2.0/7 | 1m 02s |
| Treatment (x2) | 2.4/7 (34%) | 2.0/7 | 1m 12s |
| Delta | +0.4 | 0 | +16% |

C7 was the only ceiling criterion (100% both groups). C1, C5, and C6 scored 0/10 across both groups. Post-experiment investigation revealed that the runner prompt contained no instruction to investigate ABI compatibility (C1), write .kts-specific test cases (C5), or inspect LanguageInfo struct fields or PR #659 (C6). These criteria scored zero because agents were never directed to perform those investigations, not because agents attempted them and failed. See Post-hoc Criterion Exclusion below.

### Post-hoc Criterion Exclusion

**Discovery.** C1, C5, and C6 each scored 0/10 across all runs in both groups.

**Investigation.** The runner prompt (`runner-prompt.md`) was examined after scoring was complete. It contained no instruction to investigate ABI compatibility between tree-sitter-kotlin 0.3.8 and tree-sitter 0.26.6 (C1), to write test cases exercising `.kts` file parsing specifically (C5), or to inspect the `LanguageInfo` struct fields or PR #659 to determine whether a `DEFUSE_QUERY` constant was required (C6). Agents were not directed to perform those investigations.

**Structural rationale.** The exclusion reason is independent of which group scored higher: both groups scored identically (0/10) on C1, C5, and C6. Excluding these criteria therefore cannot directionally inflate the observed treatment effect in either direction. This is a rubric-runner co-design failure, not an agent capability signal. Post-hoc exclusion with disclosed structural rationale is methodologically distinct from HARKing and aligns with pre-registration amendment practice in empirical software engineering (Wohlin, C., Runeson, P., Host, M., Ohlsson, M.C., Regnell, B., Wesslen, A. (2012). *Experimentation in Software Engineering*. Springer).

**Decision.** C1, C5, and C6 are retained in the full rubric table above for reproducibility. They are excluded from the primary treatment comparison. The treatment comparison is restricted to C2, C3, C4, and C7.

**Restricted analysis (4-criterion subset).** Per-run scores on C2, C3, C4, C7:

| Run | C2 | C3 | C4 | C7 | Total (of 4) |
|---|---|---|---|---|---|
| control-1 | 0 | 0 | 0 | 1 | 1 |
| control-2 | 0 | 1 | 1 | 1 | 3 |
| control-3 | 0 | 1 | 0 | 1 | 2 |
| control-4 | 0 | 1 | 0 | 1 | 2 |
| control-5 | 0 | 1 | 0 | 1 | 2 |
| treatment-1 | 1 | 0 | 1 | 1 | 3 |
| treatment-2 | 0 | 1 | 0 | 1 | 2 |
| treatment-3 | 1 | 1 | 1 | 1 | 4 |
| treatment-4 | 0 | 1 | 0 | 1 | 2 |
| treatment-5 | 0 | 1 | 0 | 1 | 2 |

*Table 1: Per-run scores on the 4 reachable criteria (C2, C3, C4, C7).*

Control mean: 2.0/4. Treatment mean: 2.4/4. Mann-Whitney U = 15, p = 0.6072 (not significant). The rank order is identical to the 7-criterion analysis; restricting to reachable criteria does not alter the statistical conclusion.

**Protocol fix.** For future experiments, rubric criteria must be cross-checked against runner-prompt coverage before sealing the pre-registration. Each criterion must trace to at least one explicit instruction in the runner prompt.

### Orchestrator Session

Session ID: `20260418_59`. Recorded in `analysis.json`.

## Statistical Analysis

### Inferential Test and Effect Size

All experiments employ the Mann-Whitney U test (two-tailed, alpha = 0.05) as the non-parametric test of center location. Effect sizes are reported using rank-biserial correlation (r), computed via Kerby's (2014) formula:

r = 1 - 2U / (n1 * n2)

where U is the Mann-Whitney U statistic, n1 is the control group size (n=5), and n2 is the treatment group size (n=5). Rank-biserial r ranges from -1 to +1: positive values indicate treatment superiority, negative values indicate control superiority, and r=0 indicates no effect. Conventional thresholds (Kerby, 2014) classify |r| < 0.3 as small effect, 0.3 ≤ |r| < 0.5 as medium, and |r| ≥ 0.5 as large.

This choice reflects the ordinal nature of the score data (cumulative criterion counts per run; not interval-scaled). Rank-biserial r is preferred over Cohen's d because it does not assume normality and interprets effect magnitude relative to the ranking of observations, making it suitable for small samples with discrete outcomes.

Reference: Kerby, D. S. (2014). The simple difference formula: An approach to teaching nonparametric correlation. *Comprehensive Psychology*, 3, 11.IT.3.1.

Note: Existing analysis references r = 0.5 as a detection threshold for the rubric-runner cross-check (Exp3 post-hoc exclusion rationale) and for the definition of "detection" in the Known Limitations. The new section complements this reference without contradiction: rank-biserial r is now the standard effect-size metric for all comparative statements, and r = 0.5 (medium effect) remains a meaningful threshold for interpreting what size of treatment difference the rubric-runner design should be able to detect.

## Known Limitations

1. **Ceiling effects.** Both rubrics were too easy. 100% accuracy in both groups leaves no room for treatment effects.
2. **Small sample size.** n=5 per group is underpowered for detecting small effects.
3. **Infrastructure confound.** Goose enforces an undocumented 5-delegate concurrency cap (`GOOSE_MAX_BACKGROUND_TASKS` defaults to 5) as a hard rejection with no queuing. Excess delegates are dropped, not deferred, which silently split our groups into unbalanced batches.
4. **Single model.** All experiments used Claude Haiku 4.5. Results may not generalize to other models.
5. **Session log loss.** Experiment 2 `.jsonl` session logs were purged from disk before archival. Per-run message and token counts were reconstructed from SQLite session metadata.
6. **Experiment 3 rubric-runner misalignment.** Three criteria (C1, C5, C6) required investigations not tasked in the runner prompt. Post-hoc exclusion with structural rationale was applied; see Experiment 3 Post-hoc Criterion Exclusion section.
7. **Single-judge scoring.** Scoring was performed by a single LLM judge (Claude Sonnet 4.6) with no inter-rater reliability measure. Human cross-validation or a second independent judge would strengthen scoring validity (cf. Zheng et al., 2023, MT-Bench).
8. **Pilot-scale sample size.** Each experiment used n=5 per group, sufficient for exploratory analysis but under-powered for confirmatory inference. A Mann-Whitney U test at this sample size can only detect near-complete separation effects (rank-biserial r >= 0.80) at 80% power. Results should be interpreted as pilot evidence, not confirmatory.

## Software Versions

| Component | Version |
|---|---|
| Goose | 1.25.0 |
| Claude Haiku 4.5 | `claude-haiku-4-5@20251001` |
| Claude Sonnet 4.6 | `claude-sonnet-4-6@default` |
| Provider | GCP Vertex AI |
| Recipe | goose-coder v4.1.0 |

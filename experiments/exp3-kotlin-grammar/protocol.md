# Experiment 3: Kotlin Grammar Support via Tree-sitter

**Pre-registered protocol -- locked before any delegates were spawned.**

---

## Context

The target issue [clouatre-labs/code-analyze-mcp#649](https://github.com/clouatre-labs/code-analyze-mcp/issues/649) asks for adding Kotlin grammar support using `tree-sitter-kotlin` version 0.3.8. This requires code synthesis beyond the issue text: confirming language registration, ABI compatibility, node-kind handling, and test coverage for both `.kt` and `.kts` files. The prior experiment (exp2) showed ceiling effects when the rubric was too easy; here the rubric includes six synthesis criteria (C1-C6) and one verification criterion (C7).

Paper: [Leviathan et al. (2025)](https://arxiv.org/abs/2502.07869) - repeating the input prompt verbatim improves non-reasoning LLM accuracy (47/70 wins, 0 losses across 7 models).

---

## Why This Task is Harder

- The issue does not state whether the `LANGUAGE` constant is exported or whether the crate ABI matches the current `tree-sitter` version (0.26.6). This must be verified in the crate source.
- Kotlin node-kind taxonomy (companion objects, object declarations, delegation specifiers) is not fully described in the issue; the scout must read the grammar source.
- The repository must be extended with query patterns and handlers; the scout must synthesize correct `ELEMENT_QUERY` and `extract_inheritance` logic.
- Tests must cover both `.kt` and `.kts` files, requiring creation of a Kotlin script example.
- The `DEFUSE_QUERY` constant may be required by the current `LanguageInfo` struct; the scout must determine if it is needed or justify omission.
- C7 is a verification that all acceptance criteria are met; it is trivial once the other six synthesis criteria are satisfied.

---

## Pre-registration (locked before any runs)

All decisions below are final. No post-hoc amendments after the first delegate is spawned.

### Sample size and stopping rule

- Fixed n: 10 full runs total (5 control, 5 treatment), interleaved (odd runs = control, even runs = treatment).
- Preceding pilot: 2 pilot runs (scout-pilot-01 control, scout-pilot-02 treatment) executed **before** the full run. Pilot outputs are discarded and not counted toward the n=5 per group.
- No early stopping; the full run proceeds regardless of pilot outcomes.

### Pilot gate (from GitHub issue #26)

If **both** pilot runs achieve a total score of **6/7** or higher on the draft rubric, the rubric must be hardened (e.g., raise difficulty) or the target issue swapped before the full run proceeds. Pilot scores are evaluated blind; the pilot outputs are discarded.

### Invalid run policy

- An invalid run is defined as a delegate that writes no output file or produces malformed JSON.
- Up to **5 attempts** per group may be made to obtain 5 valid runs. Scoring failures (low scores) are treated as signal, not noise, and are **not** retried.
- If 5 valid runs cannot be achieved after 5 attempts, the actual n is reported and noted as a limitation.

### Blinding

- Output files are named `scout-run-01.json` through `scout-run-10.json` (no control/treatment label in filename).
- A separate `label-map.json` file maps run numbers to group assignments and is sealed before any delegate spawns; it is revealed only after `scores.json` is written.

### Statistical test

- Mann-Whitney U test, two-tailed, alpha = 0.05 applied to total scores (0-7) across the two groups.
- With n = 5 per group this test is under-powered for small effects; a non-significant result does not rule out a small true effect.

### Latency

- Record wall-clock start and completion times per run (ISO 8601). The orchestrator will compute **median latency per group**.
- The runner must output `latency_seconds` (integer) and `message_count` (integer) in the JSON schema.

### Latency-log JSON schema (per-run record)

The latency-log.jsonl file records per-run metadata with the following fields:

```json
{
  "run_id": "scout-run-NN",
  "goose_session_id": "<captured via: sqlite3 ~/.local/share/goose/sessions/sessions.db 'SELECT id FROM sessions ORDER BY id DESC LIMIT 1;'>",
  "start_ts": "<ISO8601>",
  "end_ts": "<ISO8601>",
  "wall_clock_seconds": "<integer>",
  "input_tokens": "<from sessions.db: SELECT accumulated_input_tokens FROM sessions WHERE id='<goose_session_id>'>",
  "output_tokens": "<from sessions.db: SELECT accumulated_output_tokens FROM sessions WHERE id='<goose_session_id>'>",
  "total_tokens": "<from sessions.db: SELECT accumulated_total_tokens FROM sessions WHERE id='<goose_session_id>'>",
  "bytes": "<from sessions.db: SELECT sum(length(content_json)) FROM messages WHERE session_id='<goose_session_id>' AND role='assistant'>"
}
```

### Raw data preservation

All scout-run JSON files, `label-map.json`, `scores.json`, and the latency log (`latency-log.jsonl`) will be published as a single GitHub gist before closing the issue. The gist URL is recorded in the final issue comment.

---

## Experimental Design

### Target

- Repository: [clouatre-labs/code-analyze-mcp](https://github.com/clouatre-labs/code-analyze-mcp)
- Issue: #649 - add Kotlin grammar support via `tree-sitter-kotlin` 0.3.8.
- Model: `claude-haiku-4.5`, temperature 0.5.
- Extensions: `developer`, `context7`, `brave_search`.

### Delegates

- 5 control: Scout instructions using the standard prompt (~3 800 chars).
- 5 treatment: Scout instructions with verbatim repetition of the prompt (~7 600 chars).
- Each delegate runs independently, writes its JSON output to `scout-run-XX.json`.
- All 10 runs are spawned asynchronously; after completion the scorer runs blind.

### Rubric (pre-registered, 7-point binary)

| ID | Criterion | Synthesis Required |
|----|-----------|--------------------|
| C1 | tree-sitter-kotlin 0.3.8 public LANGUAGE export verified and ABI relationship with tree-sitter 0.26.6 fully characterized with evidence (semver ranges or crate source); incompatibility is a valid finding if documented | yes |
| C2 | Kotlin companion object node kind identified as object_declaration with companion modifier (distinct from standalone object_declaration); delegation_specifiers children enumerated distinguishing superclass_type_with_constructor from user_type | yes |
| C3 | At least 3 query patterns from tree-sitter-kotlin corpus (function_declaration, class_declaration, object_declaration variants) correctly captured in ELEMENT_QUERY | yes |
| C4 | extract_inheritance handler correctly walks delegation_specifiers and separates superclass_type_with_constructor (has parens) from user_type (no parens) | yes |
| C5 | Unit tests confirm .kt AND .kts file parsing both work; at least 1 test with .kts syntax (e.g. top-level function, extension function) | yes |
| C6 | DEFUSE_QUERY constant created for Kotlin if required by current LanguageInfo struct, or justified as None if not applicable; must cite inspection of LanguageInfo struct fields or PR #659 -- presenting both options without a conclusion does not satisfy the criterion | yes |
| C7 | All structural wiring described: feature flag included in default feature set, all required query constant names stated, EXTENSION_MAP entries present, mod.rs arms present, module registered | no |

Scoring is binary per criterion (1 = met, 0 = not met). Half-credit is not permitted.

---

## Success / Failure Gate

- **Lift detected**: treatment median >= control median + 1 point **and** Mann-Whitney p < 0.05.
- **No lift**: delta < 1 point **or** p >= 0.05.
- **Ceiling-effect clause**: if C7 (and only C7) hits 100 % in both groups, that is the trivial criterion by design; a ceiling concern applies only if C1-C6 also hit 100 %.

---

## Execution Notes

- Record the repository HEAD SHA before spawning delegate 1; all delegates use the same SHA.
- The orchestrator writes `label-map.json` before any delegate spawns and seals it.
- **Post-spawn action**: Immediately after spawning each delegate, capture the Goose DB session ID by running `sqlite3 ~/.local/share/goose/sessions/sessions.db "SELECT id FROM sessions ORDER BY id DESC LIMIT 1;"` and record the result as `goose_session_id` in the run's `latency-log.jsonl` entry.
- The scorer receives only the 10 run files and the rubric; it does **not** see `label-map.json` until after scoring.
- After `scores.json` is written, the orchestrator reveals `label-map.json`, computes group statistics, and publishes the gist.

---

## Limitations (pre-acknowledged)

- n = 5 per group is under-powered; the Mann-Whitney test may miss small effects.
- Scoring is performed by a single LLM judge; inter-rater reliability is not measured.
- Only one model, temperature, and issue are used; results may not generalize.
- The `brave_search` extension gives scouts access to external documentation, limiting ecological validity for air-gapped settings.

---

## References

- Leviathan, Y. et al., "Prompt Repetition Improves Non-Reasoning LLMs" (2025) - https://arxiv.org/abs/2502.07869
- Experiment 1: [exp1-fastmcp-refactor](../exp1-fastmcp-refactor/protocol.md)
- Experiment 2: [exp2-treesitter-synthesis](../exp2-treesitter-synthesis/protocol.md)
- Target issue: https://github.com/clouatre-labs/code-analyze-mcp/issues/649
- Pilot gate: GitHub issue #26, #27
- Rubric source: `experiments/exp3-kotlin-grammar/target-assessment.json`

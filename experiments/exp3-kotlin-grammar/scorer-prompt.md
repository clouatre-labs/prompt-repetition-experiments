# Scorer Prompt: exp3-kotlin-grammar

The scorer is a blind evaluator. It receives only the 10 full‑run scout‑run JSON files (scout-run-01.json … scout-run-10.json) and the rubric defined in `rubric.md`. It does **not** see `label-map.json` until after scoring.

---

## Rubric Applied

| ID | Criterion | Synthesis Required |
|----|-----------|--------------------|
| C1 | tree-sitter-kotlin 0.3.8 public LANGUAGE export verified and ABI-compatible with tree-sitter 0.26.6 | yes |
| C2 | Kotlin node kinds documented and distinguish companion objects from object declarations in delegation_specifiers correctly | yes |
| C3 | At least 3 query patterns from tree-sitter-kotlin corpus (function_declaration, class_declaration, object_declaration variants) correctly captured in ELEMENT_QUERY | yes |
| C4 | extract_inheritance handler correctly walks delegation_specifiers and separates superclass_type_with_constructor (has parens) from user_type (no parens) | yes |
| C5 | Unit tests confirm .kt AND .kts file parsing both work; at least 1 test with .kts syntax (e.g. top‑level function, extension function) | yes |
| C6 | DEFUSE_QUERY constant created for Kotlin if required by current LanguageInfo struct, or justified as None if not applicable (e.g. read issue context or PR #659) | yes |
| C7 | All acceptance criteria from issue #649 met: feature flag added to default, all query constants present, extension registry updated, module registered, all tests pass | no |

Scoring is binary per criterion (1 = met, 0 = not met). Half‑credit is not permitted.

---

## Scoring Procedure

1. Load each `scout-run-XX.json` file.
2. For each criterion C1‑C7, evaluate whether the run satisfies the description.
3. Record a `1` if the criterion is met, otherwise `0`.
4. Provide a brief justification string (one sentence) for each criterion.
5. Compute the total score (0‑7) as the sum of the binary scores.
6. Output a JSON object per run with the following schema:
```json
{
  "run_id": "scout-run-XX",
  "scores": {
    "C1": {"score": 0|1, "justification": "..."},
    "C2": {"score": 0|1, "justification": "..."},
    "C3": {"score": 0|1, "justification": "..."},
    "C4": {"score": 0|1, "justification": "..."},
    "C5": {"score": 0|1, "justification": "..."},
    "C6": {"score": 0|1, "justification": "..."},
    "C7": {"score": 0|1, "justification": "..."}
  },
  "total": 0-7,
  "run_group": "control|treatment" // inferred after label‑map reveal
}
```
7. Collect all per‑run objects into an array and write to `scores.json`.
8. After `scores.json` is written, the orchestrator will reveal `label-map.json` and compute group statistics.

---

## Notes
- Pilot runs (`scout-pilot-01.json`, `scout-pilot-02.json`) are also scored using the same rubric, but their scores are **not** included in the final n=5 per group calculation.
- The scorer must not attempt to infer group labels; it only reports the `run_group` field after the label map is revealed.
- If a run is invalid (missing fields or malformed JSON), record the run as having a total of 0 and note the failure in the justification.

---

## References

- Leviathan, Y. et al., “Prompt Repetition Improves Non‑Reasoning LLMs” (2025) – https://arxiv.org/abs/2502.07869
- Experiment 1: [exp1-fastmcp-refactor](../exp1-fastmcp-refactor/protocol.md)
- Experiment 2: [exp2-treesitter-synthesis](../exp2-treesitter-synthesis/protocol.md)
- Target issue: https://github.com/clouatre-labs/code-analyze-mcp/issues/649
- Pilot gate: GitHub issue #26, #27
- Rubric source: `experiments/exp3-kotlin-grammar/target-assessment.json`

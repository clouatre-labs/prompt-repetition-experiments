# Scorer Prompt: exp2-treesitter-synthesis

**Note**: The scorer session ID was not explicitly recorded in the experiment metadata. The scoring was performed by a blind evaluator (claude-haiku-4-5-blind) on 2026-02-20T17:26:00Z, but the goose session ID for the scorer delegate is not available in the sessions.db or analysis.json.

The scorer was instructed to evaluate all 10 scout-run outputs against the rubric defined in protocol.md (criteria C1-C7, binary scoring per criterion).

## Rubric Applied

| ID | Criterion | Ground truth |
|----|-----------|-------------|
| C1 | SecurityScanner implementation file identified | `crates/aptu-core/src/scanner.rs` or equivalent |
| C2 | Line-by-line regex limitation understood | references single-line constraint; cites aptu#735 or PR #736 or quotes the test |
| C3 | tree-sitter-rust version verified | 0.23 (not assumed from issue text alone) |
| C4 | Hybrid vs. full-migration tradeoff articulated | names specific patterns or files as evidence |
| C5 | At least 2 specific patterns identified | must name actual pattern IDs or descriptions from source code |
| C6 | Data-flow/taint tracking gap noted | explicit statement that AST traversal does not equal taint analysis |
| C7 | Binary size / grammar crate count estimated | names at least 3 target languages with their crate names |

Scoring: binary per criterion (1 = met, 0 = not met). Half-credit not permitted.

## Result

All 10 runs scored 7/7 (100% on all criteria), indicating a ceiling effect. See analysis.json for full scoring details and justifications.

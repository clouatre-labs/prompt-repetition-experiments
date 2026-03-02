# Rubric: exp2-treesitter-synthesis

Extracted from protocol.md. Binary scoring (1 = criterion met, 0 = not met).

| Criterion | Description |
|---|---|
| C1 | SecurityScanner implementation file identified. Must verify against actual repo structure (crates/aptu-core/src/scanner.rs or equivalent), not assumed. |
| C2 | Line-by-line regex limitation understood. Must reference single-line constraint; cite aptu#735 or PR #736 or quote the test. |
| C3 | tree-sitter-rust version verified against Cargo.toml or Context7 docs. Must identify 0.23 (not assumed from issue text alone). |
| C4 | Hybrid vs. full-migration tradeoff articulated with codebase evidence. Must name specific patterns or files as evidence, not generic prose. |
| C5 | At least 2 specific patterns identified as requiring multi-line detection. Must name actual pattern IDs or descriptions from source code, not generic examples from the issue. |
| C6 | Data-flow/taint tracking gap noted as unsolved by tree-sitter alone. Explicit statement that AST traversal does not equal taint analysis. |
| C7 | Binary size / grammar crate count estimated with specifics. Must name at least 3 target languages with their crate names (e.g. tree-sitter-python, tree-sitter-javascript). |

**Notes**:
- C5, C6, C7 require reading and synthesizing actual source code or verified external docs. They cannot be answered from the issue text alone.
- Half-credit is not permitted.
- Scoring is binary per criterion.

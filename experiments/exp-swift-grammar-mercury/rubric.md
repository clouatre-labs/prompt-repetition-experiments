# Rubric: exp-swift-grammar-mercury

Extracted from the pilot design (see conversation record; this experiment has
no separate protocol.md -- it is exploratory, not part of the paper's
confirmatory series). Binary scoring (1 = criterion met, 0 = not met).

| ID | Criterion | Synthesis Required |
|----|-----------|--------------------|
| C1 | tree-sitter-swift 0.7.3's dependency relationship to the workspace `tree-sitter = "0.26.13"` pin (root `Cargo.toml`) is independently verified against tree-sitter-swift's actual crate manifest (via context7, gh, or web lookup of alex-pinkus/tree-sitter-swift's Cargo.toml) -- citing the manifest content found, not merely restating the issue's "no version conflict" claim | yes |
| C2 | `class_declaration`'s `declaration_kind` field and its five values (class/struct/actor/enum/extension) are confirmed by citing the actual field definition from `node-types.json` or `grammar.js` in the tree-sitter-swift grammar source -- not the issue's bullet list of values | yes |
| C3 | At least 3 `ELEMENT_QUERY` patterns (function_declaration, class_declaration, protocol_declaration) are written and explicitly modeled on the real current `ELEMENT_QUERY` in `crates/aptu-coder-core/src/languages/java.rs` -- must cite that file's actual query structure, not derive patterns solely from the issue's node-kind prose | yes |
| C4 | `extract_inheritance` design walks `inheritance_specifier` -> `inherits_from` field -> `user_type`/`type_identifier`, citing inspection of an existing field-based `extract_inheritance` handler in the repo (e.g. `kotlin.rs`) to justify the walk shape -- not just asserting the walk from the issue's prose | yes |
| C5 | A `DEFUSE_QUERY` constant is proposed after independently confirming, via inspection of the actual `LanguageInfo` struct in `crates/aptu-coder-core/src/languages/mod.rs`, that `defuse_query: Option<&'static str>` is a mandatory field set by every language arm -- citing the struct itself, not the issue's claim -- AND the pattern is demonstrably modeled on `java.rs`'s real 4-line `DEFUSE_QUERY` (cited), adapted to cover Swift local declarations, assignments, and identifier reads | yes |
| C6 | Unit test plan lists concrete Swift code snippets for each `declaration_kind` (class/struct/actor/enum/extension) and each inheritance shape (single superclass, multiple protocols, mixed), naming specific test function names -- a plan that only restates the issue's Acceptance Criteria checklist without concrete snippets/test names does not satisfy this criterion | yes |
| C7 | All structural wiring described: `[workspace.dependencies]` entry for tree-sitter-swift, unconditional (no feature flag) dependency in `crates/aptu-coder-core/Cargo.toml`, `.swift` entry in `EXTENSION_MAP` (`lang.rs`), `mod swift;` registration, and both `get_language_info()`/`get_ts_language()` match arms in `mod.rs` -- modeled on the existing `"css"` wiring pattern | no |

**Notes**:
- C1-C6 require code-driven discovery beyond the issue text (not just issue restatement). C7 is a verification step, expected to be the easy criterion by design (mirrors Exp3's C7).
- Binary scoring only; half-credit is not permitted.
- If C1-C6 (not just C7) hit 100% in both pilot runs, that is the ceiling-effect signal: the rubric is too easy and must be hardened before the full n=5+5 run.

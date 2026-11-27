# Rubric v3: exp-swift-grammar-mercury (corrected)

Supersedes `rubric.md` for scoring going forward. `rubric.md` and
`rubric-v2-diagnostic.md` are kept for provenance -- do not delete.

## Why this exists

Round 2 (scout-run-03, scout-run-04; `runner-prompt-v2.md`, literal
artifacts forced) still scored 0/7 in both runs against the original
`rubric.md`. Reading `scores-round2.json`'s justifications line by line
shows the *specific* reason each failing criterion failed: C3, C4, C5, and
C7 all failed for the identical stated reason -- the run's literal artifact
(a real `element_query_draft`, a real `defuse_query_draft`, a real
`inheritance_walk_citation`) was judged correct in substance, but did not
additionally cite/explicitly model itself on an existing *internal*
reference file (`java.rs`, `kotlin.rs`, the `"css"` wiring pattern).

That "must cite an internal reference file" clause is a requirement I added
while adapting Exp3's format, and Exp3's own originals never had it (Exp3's
C3/C4/C7 only ever ask whether the *target* grammar's own mechanics are
correctly captured; Exp3's C6/DEFUSE-analogue only asks for LanguageInfo
struct citation or PR citation, not a citation of an existing query's exact
text). I caught this for C3/C4/C7 after round 1 (`rubric-v2-diagnostic.md`)
but incompletely -- I missed that C5 carries the identical added clause
("modeled on java.rs's real 4-line DEFUSE_QUERY (cited)"), which round 2's
scores now confirm is also blocking a criterion that should pass. This file
corrects all four (C3, C4, C5, C7) for real, not just as a diagnostic.

C1, C2, C6 are unchanged -- they require citation of *external* sources
(the tree-sitter-swift crate manifest, the grammar's `node-types.json`/
`grammar.js`) or the delegate's *own* concrete artifacts (test snippets),
never an internal same-repo reference file, so they don't carry this bug.

## Corrected criteria (C3, C4, C5, C7 only -- C1, C2, C6 keep `rubric.md`'s wording)

| ID | Corrected criterion |
|----|------|
| C3 | At least 3 correct Swift `ELEMENT_QUERY` patterns (function_declaration, class_declaration, protocol_declaration) with correct node fields (`name`) and capture labels, produced as literal tree-sitter query text -- a description of what the query constants will contain, without literal query text, does not satisfy this criterion. |
| C4 | `extract_inheritance` design correctly and literally describes walking `inheritance_specifier`'s `inherits_from` field to reach `user_type`/`type_identifier`, citing the grammar source (tree-sitter-swift's own grammar.js/node-types.json or equivalent) it was derived from -- a bare assertion of the walk without citing where it came from does not satisfy this criterion. |
| C5 | A `DEFUSE_QUERY` constant is proposed as literal tree-sitter query text, after independently confirming via the actual `LanguageInfo` struct (cited, not issue-quoted) that `defuse_query` is mandatory, and the query text correctly covers Swift local declarations, assignments, and identifier reads. |
| C7 | All structural wiring facts stated: `[workspace.dependencies]` entry, unconditional (no feature flag) dependency in `crates/aptu-coder-core/Cargo.toml`, `.swift` entry in `EXTENSION_MAP`, `mod swift;` registration, and both `get_language_info()`/`get_ts_language()` match arms -- all five facts must be present somewhere in the run's output, in any field. |

Binary scoring only; half-credit is not permitted.

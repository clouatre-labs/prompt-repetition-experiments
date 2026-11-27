# Diagnostic re-scoring: rubric-v2 (NOT a replacement of the sealed rubric.md)

Purpose: separate two candidate explanations for the pilot's 0/7-in-both-runs
result: (a) rubric-authoring drift introduced when adapting Exp3's format for
this pilot, vs. (b) a genuine capability/behavior gap in the
`inception/mercury-2.5-preview` delegate. This file is a post-hoc diagnostic
only -- it does not alter the sealed `rubric.md`, the sealed `scores.json`,
or the pilot's official result. Same 2 run files, re-scored under corrected
wording for C3/C4/C7 only.

## What changed and why

Comparing `rubric.md`'s C3, C4, C7 against Exp3's originals
(`exp3-kotlin-grammar/rubric.md`) shows I added a clause Exp3's precedent
never required: an explicit demand to "cite/explicitly model on an existing
reference file" (`java.rs`, `kotlin.rs`, the `"css"` wiring pattern) on top
of correctly describing the target grammar's own mechanics. Exp3's C3/C4/C7
only ever asked whether the target grammar (Kotlin) was correctly described;
they never required citing a cross-file reference implementation. C1, C2,
C5, C6 are left unchanged here because their wording already matches Exp3's
actual precedent-level strictness, and their 0/2 result already replicates
Exp3's own 0/10 pattern for the equivalent criteria -- not the anomaly under
investigation.

| ID | Diagnostic wording (Exp3-aligned, reference-file citation clause removed) |
|----|------|
| C3 | At least 3 Swift node kinds (function_declaration, class_declaration, protocol_declaration) correctly identified together with their relevant fields (e.g. `name` field, `declaration_kind` field) as captured in ELEMENT_QUERY guidance -- naming the query constant without any node-kind/field-level detail does not satisfy this criterion. |
| C4 | extract_inheritance design correctly describes walking `inheritance_specifier`'s `inherits_from` field to reach `user_type`/`type_identifier`, and correctly notes there is no constructor-call-vs-plain-type distinction in Swift's inheritance syntax (unlike a language with parenthesized-superclass-vs-bare-interface distinction). |
| C7 | All structural wiring described: workspace dependency addition for tree-sitter-swift, unconditional (no feature flag) crate dependency, `.swift` EXTENSION_MAP entry, `mod swift;` module registration, and both `get_language_info()`/`get_ts_language()` match arms. |

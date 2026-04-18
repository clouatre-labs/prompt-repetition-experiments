# Rubric: exp3-kotlin-grammar

Extracted from protocol.md. Binary scoring (1 = criterion met, 0 = not met).

| ID | Criterion | Synthesis Required |
|----|-----------|--------------------|
| C1 | tree-sitter-kotlin 0.3.8 public LANGUAGE export verified and ABI relationship with tree-sitter 0.26.6 fully characterized with evidence (semver ranges or crate source); incompatibility is a valid finding if documented | yes |
| C2 | Kotlin companion object node kind identified as object_declaration with companion modifier (distinct from standalone object_declaration); delegation_specifiers children enumerated distinguishing superclass_type_with_constructor from user_type | yes |
| C3 | At least 3 query patterns from tree-sitter-kotlin corpus (function_declaration, class_declaration, object_declaration variants) correctly captured in ELEMENT_QUERY | yes |
| C4 | extract_inheritance handler correctly walks delegation_specifiers and separates superclass_type_with_constructor (has parens) from user_type (no parens) | yes |
| C5 | Unit tests confirm .kt AND .kts file parsing both work; at least 1 test with .kts syntax (e.g. top-level function, extension function) | yes |
| C6 | DEFUSE_QUERY constant created for Kotlin if required by current LanguageInfo struct, or justified as None if not applicable; must cite inspection of LanguageInfo struct fields or PR #659 -- presenting both options without a conclusion does not satisfy the criterion | yes |
| C7 | All structural wiring described: feature flag included in default feature set, all required query constant names stated, EXTENSION_MAP entries present, mod.rs arms present, module registered | no |

**Notes**:
- C1-C6 require code-driven discovery (not just issue text). C7 is a verification step.
- Binary scoring only; half-credit is not permitted.
- If only C7 reaches 100 % in both groups, that is expected; a ceiling concern applies only if C1-C6 also hit 100 %.

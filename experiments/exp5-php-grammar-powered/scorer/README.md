# Exp5 PHP grammar scorer

Offline, deterministic Python scorer for the literal runner-prompt-v3 artifacts of Exp5 PHP sessions (C3 to C7). It reads session JSON as data only, never executes anything from it, and makes no network calls at run time (the only network step is `uv sync` at setup).

## Setup and commands

```bash
cd experiments/exp5-php-grammar-powered/scorer
uv sync                     # setup only: installs pinned tree-sitter==0.25.2 and tree-sitter-php==0.25.2
uv run pytest               # tests
uv run scorer.py fixtures/sessions --out /tmp/scores-a.json
uv run scorer.py fixtures/sessions --out /tmp/scores-b.json
uv run scorer.py --report-variance fixtures/sessions
```

`--out` is optional (stdout otherwise). `--scored-at <ISO8601>` pins the timestamp so two runs are byte-identical; without it, two runs are byte-identical apart from `scored_at`. Directories are expanded to their sorted `*.json` files, so `run_id` ordering in `scores.json` is stable.

## What is scored

Every criterion in `C3..C7` is a float in `[0,1]` with a justification naming the failing artifact; `total = C3 + C4 + C5 + C6 + C7` (max 5.0). `C1` and `C2` (external-citation criteria) are not executable offline: a numeric `C1`/`C2` on the session is copied verbatim, otherwise `null`. Nothing is ever `NaN`; not-applicable values are `null`.

| ID | Artifact | Rule |
|----|----------|------|
| C3 | `element_query_draft` | 0 if it does not compile. Otherwise share of the 6 required declaration kinds whose pattern captures something on `fixtures/php/`. If fewer than 3 patterns, capped at 0.5. |
| C4 | `inheritance_walk_citation` | 0 if it names no snake_case node kinds/fields, or cites neither `base_clause` nor `class_interface_clause`. Otherwise share of cited identifiers that exist in `vendor/tree-sitter-php-node-types.json`. |
| C5 | `defuse_query_draft` | 0 if it does not compile. Otherwise `(1 + captures a write + captures a read) / 3` on `fixtures/php/defuse.php`. A write is a captured `variable_name` whose parent is an `*_assignment_expression`; any other captured `variable_name` counts as a read. |
| C6 | `test_snippets[].code` | `(parse share) x (share of the two dimensions `declaration_kind`, `inheritance_shape` present among parsed snippets)`. A snippet parses when the tree has no error node and contains a `php_tag`; `<?php` is prepended when missing. Unparsable snippets are dropped from the share and named by `test_name`. |
| C7 | `wiring_summary` | Mean of the 5 facts `workspace_dependency`, `unconditional_dependency`, `extension_map_entry`, `mod_registration`, `match_arms` (a missing key is 0). Each fact is matched by regex against the shape of its siblings in the vendored aptu-coder snapshot. |

### C7 fact patterns (tied to the vendored snapshot)

| Fact | Sibling in snapshot | Accepted shape |
|------|--------------------|----------------|
| `workspace_dependency` | `tree-sitter-java = "0.23.5"` in `workspace.Cargo.toml` | `tree-sitter-php = "<version>"` |
| `unconditional_dependency` | `tree-sitter-java = { workspace = true }` in `core.Cargo.toml` | `tree-sitter-php = { workspace = true }` |
| `extension_map_entry` | `("java", "java"),` in `lang.rs` | `("php", "php"),` |
| `mod_registration` | `pub mod java;` in `mod.rs` | `mod php;` or `pub mod php;` on its own line |
| `match_arms` | `"java" => Some(tree_sitter_java::LANGUAGE.into()),` | text containing `"php" =>` and `tree_sitter_php::LANGUAGE` |

### Rubric mapping: node kinds

tree-sitter-php 0.25.2 names the declaration nodes `function_definition` and `method_declaration`, not `function_declaration`; inheritance is `base_clause` (extends) and `class_interface_clause` (implements) under `class_declaration`/`enum_declaration`. The rubric's wording is interpreted through those names.

## Vendored inputs and provenance

All files were downloaded once with `gh api` at setup time and are checked in; the scorer never clones a repository or applies a patch.

| Local file | Source | Commit | sha256 |
|-----------|--------|--------|--------|
| `vendor/tree-sitter-php-node-types.json` | `tree-sitter/tree-sitter-php`, `php/src/node-types.json` | `c1e13490bd656b8869cd47e6f74997ed46750a08` | `eb073869d28245cc9e6ec17551b0895fc8e3a80d80762d6ecfd3af8076326f8d` |
| `vendor/aptu-coder/*` | `clouatre-labs/aptu-coder` (pre-PHP) | `132ea687e09a916091699a562da3c96c86ec1fd8` | per-file in `vendor/aptu-coder/PIN.json` |

The parser binary itself comes from the `tree-sitter-php==0.25.2` wheel (PyPI); no grammar source is vendored. The binding is obtained through `tree_sitter_php.language_php()`; `language()` is never called.

## Fixture corpus

`fixtures/php/` holds six small files written for this scorer: `functions.php` (functions), `classes.php` (class with methods and `extends` shape via `base_clause`), `interfaces.php` (interface and a class that `implements` it), `traits.php` (trait and a `use`), `enums.php` (backed enum that implements an interface), `defuse.php` (assignments, augmented assignment, reads). `fixtures/sessions/known-good.json` and `known-bad.json` are synthetic fixtures for tests only, not experiment sessions.

## Output shape

`scores.json` follows the `## scores.json` section of `DATA_DICTIONARY.md` with fixed key order `scored_at, scorer, rubric_version, note, scores`; each record is `run_id, C1, C2, C3, C4, C5, C6, C7, total, justifications`. `--report-variance` prints `n, min, max, mean, variance` per criterion plus `C7.<fact>` per wiring fact for HEADROOM analysis.

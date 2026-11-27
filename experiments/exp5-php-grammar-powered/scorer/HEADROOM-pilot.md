# Exp5 HEADROOM pilot record

Current verdict: re-pilot (prompt 671e5db1) is CONTAMINATED under the literal Step 3 rule and h45-control is also FLOOR; see "Re-pilot" below. The first pilot is superseded.

## Superseded: first pilot (prompt 2d4f22e3)

Status: filled from the 2026-11-27 pilot (4 runs, goose 1.61.1, no turn cap). Gate verdict: CEILING (claude-haiku-5-5 control_mean 4.0476 > 3.5; see Decision).

### Pre-registration

Before any pilot session is scored, the following are fixed:

- Scorer: `experiments/exp5-php-grammar-powered/scorer` at the commit that lands with #101, with its `uv.lock` unchanged.
- Rubric: `exp5-rubric-v1-fractional` (C3 to C7 fractional in `[0,1]`, `total = C3 + C4 + C5 + C6 + C7`, max 5.0; C1/C2 copied verbatim or `null`).
- Headroom criterion: a criterion is considered to have headroom when between-run variance across the pilot is above 0 and no run saturates at 1.0.
- Command: `uv run scorer.py <sessions-dir> --out scores-pilot.json` then `uv run scorer.py --report-variance <sessions-dir>`.

### Measurements

Source: `uv run scorer.py --report-variance` over h45-control, h45-treatment, h55-control, h55-treatment (`scores-pilot.json`, scored_at 2026-11-27T16:40:00Z).

| Criterion | n | min | max | mean | variance | Saturated at 1.0 | Headroom |
|-----------|---|-----|-----|------|----------|------------------|----------|
| C3 | 20 | 0.0 | 1.0 | 0.15 | 0.1275 | yes (3 of 4 runs) | no (saturates) |
| C4 | 20 | 0.0 | 1.0 | 0.1674 | 0.1142 | yes (1 of 4 runs) | no (saturates) |
| C5 | 20 | 0.0 | 1.0 | 0.1 | 0.0567 | yes (1 of 4 runs) | no (saturates) |
| C6 | 20 | 0.0 | 1.0 | 0.2 | 0.16 | yes (4 of 4 runs) | no |
| C7 | 20 | 0.0 | 1.0 | 0.2 | 0.16 | yes (4 of 4 runs) | no |
| C7.workspace_dependency | 4 | 1.0 | 1.0 | 1.0 | 0.0 | yes (4 of 4 runs) | no |
| C7.unconditional_dependency | 4 | 1.0 | 1.0 | 1.0 | 0.0 | yes (4 of 4 runs) | no |
| C7.extension_map_entry | 4 | 1.0 | 1.0 | 1.0 | 0.0 | yes (4 of 4 runs) | no |
| C7.mod_registration | 4 | 1.0 | 1.0 | 1.0 | 0.0 | yes (4 of 4 runs) | no |
| C7.match_arms | 4 | 1.0 | 1.0 | 1.0 | 0.0 | yes (4 of 4 runs) | no |

Per-run totals (5.0 scale): h45-control 3.1333 (C3 0.0, C4 0.8, C5 0.3333, C6 1.0, C7 1.0); h45-treatment 4.1667 (1.0, 0.8333, 0.3333, 1.0, 1.0); h55-control 4.0476 (1.0, 0.7143, 0.3333, 1.0, 1.0); h55-treatment 5.0 (1.0, 1.0, 1.0, 1.0, 1.0).

### Decision

- Criteria with headroom: none under the pre-registered rule (variance > 0 and no run at 1.0). The closest are C4 (run-level 0.7143 to 1.0, saturates only in h55-treatment) and C5 (0.3333 in three runs, 1.0 in h55-treatment); both have variance > 0 but one run saturates.
- Criteria without headroom and the follow-up (rubric wording vs. scorer rule):
  - C6, C7 and all five C7 sub-criteria: 1.0 in every run, variance 0. These are ceiling effects from the rubric wording (the runner prompt enumerates each wiring fact literally, so every model copies it); follow-up is rubric wording, not the scorer rule.
  - C3: 0.0 in h45-control and 1.0 in the other three. The 0 is "0/6 declaration kinds matched on the fixture corpus; fewer than 3 patterns" (the draft compiles but captures nothing); the other three runs score 6/6. Follow-up is rubric wording (the prompt does not require naming the node kinds in the draft) rather than the scorer rule.
  - C5: 0.3333 in three runs is "defuse query compiles; write captures=0, read captures=0", i.e. credit for compilation only; h55-treatment scores 6 write and 7 read captures. Follow-up is scorer rule granularity (compilation is 1 of 3 sub-checks and is free).
  - Caveat: two runs touched issue 1861 (the closed predecessor of #1864) despite the prompt naming only #1864: h45-control via a brave_search response, h55-treatment by an explicit `gh issue view 1861`. h55-treatment is the only run at 5.0 and the only C4/C5 saturation, so its scores may not be blind.
- Gate arithmetic (band [1.5, 3.5] on the 5.0 scale, n = 1 per arm):
  - claude-haiku-4-5: control_mean 3.1333, treatment_mean 4.1667; mean cost per run 0.3293 USD.
  - claude-haiku-5-5: control_mean 4.0476, treatment_mean 5.0; mean cost per run 0.1623 USD.
  - claude-haiku-4-5 control_mean 3.1333 is in [1.5, 3.5]; claude-haiku-5-5 control_mean 4.0476 is above 3.5. No run has a failure_mode; no model exceeds 2.00 USD per run. Verdict: CEILING (claude-haiku-5-5 control_mean > 3.5).
  - Criteria saturated at 1.0 in a control run: C3 (h55-control), C6 (both), C7 (both) and all five C7 sub-criteria (both). Across the whole pilot C6, C7 and every C7 sub-criterion are 1.0 in all 4 runs; h55-treatment also saturates C3, C4 and C5 (total 5.0).
- Date and scorer commit: 2026-11-27, scorer commit 2011ad0.

## Re-pilot (prompt 671e5db1)

Status: 2026-11-27, 4 runs, goose 1.61.1, no turn cap, concurrency 2, wall clock 16:55:52Z to 17:02:04Z. Instrument changes (#123): prompt no longer names snippet dimensions or wiring entries, #1861 is off limits, C5 gives no compile credit, C6 counts delegate-named dimensions, C7 is key-agnostic, `primary_total = C3 + C4 + C5` (max 3.0). All four runs exit 0 with no failure_mode. Scores: `scores-pilot.json`, scored_at 2026-11-27T17:10:00Z, records mapped by argv order (run_id "unknown" in every record).

### Measurements

| Criterion | n | min | max | mean | variance | Saturated at 1.0 | Headroom |
|-----------|---|-----|-----|------|----------|------------------|----------|
| C3 | 20 | 0.0 | 1.0 | 0.1 | 0.09 | yes (2 of 4 runs) | no (saturates) |
| C4 | 20 | 0.0 | 1.0 | 0.1784 | 0.1289 | yes (1 of 4 runs) | no (saturates) |
| C5 | 20 | 0.0 | 1.0 | 0.05 | 0.0475 | yes (1 of 4 runs) | no (saturates) |
| C6 | 20 | 0.0 | 0.8622 | 0.1662 | 0.1107 | no | yes |
| C7 | 20 | 0.0 | 0.8 | 0.14 | 0.0844 | no | yes |
| C7.workspace_dependency | 4 | 1.0 | 1.0 | 1.0 | 0.0 | yes (4 of 4 runs) | no |
| C7.unconditional_dependency | 4 | 1.0 | 1.0 | 1.0 | 0.0 | yes (4 of 4 runs) | no |
| C7.extension_map_entry | 4 | 0.0 | 1.0 | 0.75 | 0.1875 | yes (3 of 4 runs) | no (saturates) |
| C7.mod_registration | 4 | 0.0 | 0.0 | 0.0 | 0.0 | no | no (floor) |
| C7.match_arms | 4 | 0.0 | 1.0 | 0.75 | 0.1875 | yes (3 of 4 runs) | no (saturates) |

Per-run scores:

| run (argv order) | C3 | C4 | C5 | C6 | C7 | primary_total | total | cost_usd | total_tokens | tool requests |
|---|---|---|---|---|---|---|---|---|---|---|
| h45-control | 0.0 | 0.75 | 0.0 | 0.7901 | 0.8 | 0.75 | 2.3401 | 0.23535645 | 1,292,513 | 33 |
| h45-treatment | 1.0 | 1.0 | 0.0 | 0.81 | 0.4 | 2.0 | 3.21 | 0.3042378 | 1,751,522 | 39 |
| h55-control | 1.0 | 0.9091 | 0.0 | 0.8622 | 0.8 | 1.9091 | 3.5713 | 0.043155905 | 987,746 | 17 |
| h55-treatment | 0.0 | 0.9091 | 1.0 | 0.8622 | 0.8 | 1.9091 | 3.5713 | 0.11319685 | 2,016,751 | 29 |

### Did C6 and C7 vary?

Yes. C6: run-level min 0.7901 (h45-control), max 0.8622 (both h55 runs), no run at 1.0. C7: run-level min 0.4 (h45-treatment), max 0.8 (three runs), no run at 1.0. C7.mod_registration is 0.0 in all four runs (key-agnostic match still fails for every delegate's module-registration statement); C7.workspace_dependency and C7.unconditional_dependency stay at 1.0 in all four.

### Delegate-named wiring entries and dimensions

No run used either old dimension name (`declaration_kind`, `inheritance_shape`) or any of the five canonical wiring keys (`workspace_dependency`, `unconditional_dependency`, `extension_map_entry`, `mod_registration`, `match_arms`) as a `wiring_summary` key. Every delegate invented its own taxonomy:

- h45-control wiring keys (8): cargo_toml_workspace_dependencies, crates_aptu_coder_core_cargo_toml, languages_mod_rs_module_declaration, languages_mod_rs_get_language_info, languages_mod_rs_get_ts_language, lang_rs_extension_map, lang_rs_supported_languages, readme_md_supported_languages. Dimensions (9): class_declaration, enum_declaration, function_definition, html_embedded_php, inheritance_extends, inheritance_implements, interface_declaration, method_declaration, trait_declaration.
- h45-treatment wiring keys (9): mod_rs_pub_mod, mod_rs_get_language_info, mod_rs_get_ts_language, lang_rs_extension_map, lang_rs_supported_languages, cargo_toml_workspace_deps, cargo_toml_core_deps, readme_language_count, readme_language_list. Dimensions (10): defuse_write_site, element_extraction_class, element_extraction_enum, element_extraction_function, element_extraction_interface, element_extraction_method, element_extraction_trait, html_embedded_php, inheritance_extends_implements, inheritance_no_clauses.
- h55-control wiring keys (13): cargo_toml_workspace_dependencies, crates_aptu_coder_core_cargo_toml, cargo_lock, lang_rs_extension_map, lang_rs_supported_languages, languages_mod_rs_pub_mod, languages_mod_rs_get_language_info, languages_mod_rs_get_ts_language, languages_mod_rs_registry_test, languages_php_rs_new_file, readme_md_intro_count_and_list, crates_aptu_coder_core_readme_md, lib_rs_doc_comments. Dimensions (14): call_sites_free_method_static, defuse_read_and_update, defuse_write_site, element_free_function, element_method, element_type_declarations, import_use_declaration, inheritance_extends_and_implements, inheritance_interface_extends, inheritance_no_clause_edge, mixed_html_template_no_errors, query_compiles, registry_extension_mapping, registry_get_language_info.
- h55-treatment wiring keys (12): cargo_toml_workspace_dependencies, crates_aptu_coder_core_cargo_toml_dependencies, cargo_lock_packages, lang_rs_extension_map, lang_rs_supported_languages, languages_mod_rs_pub_mod, languages_mod_rs_get_language_info_arm, languages_mod_rs_get_ts_language_arm, languages_mod_rs_table_test, languages_php_rs_handler_file, readme_md_supported_languages, crates_aptu_coder_tests_php_integration. Dimensions (14): call_sites_free_member_scoped, defuse_write_read_sites, element_bodyless_method, element_free_function, element_interface_trait_enum, element_method_in_class, empty_file, handler_wrong_node_kind_guard, html_template_mixed_parse, import_use_statements, inheritance_extends_and_implements, inheritance_interface_multi_extends, inheritance_no_clause_edge, query_compilation.

### Contamination (Step 3, literal rule)

Full scan output: `/tmp/exp5-scratch/contamination-report.txt`. Hits by run:

- h45-control: "1861" only in the runner prompt's off-limits sentence. No aptu-coder pull request reference beyond the #1864 body's "External pull requests ... are not being accepted". Other-commit SHAs 5ad3d72 and 9b42cd3 appear only in `git log` history output of the pinned clone. "tree-sitter-php" in tool results outside the crate registry and grammar repo: the #1864 body, a pypi.org page, and the Context7 mirror `/websites/rs_tree-sitter-php`.
- h45-treatment: same prompt-only "1861" and same #1864 pull-request sentence. Other-commit SHAs 5ad3d72 and 9b42cd3 from `git log`. "tree-sitter-php" outside registry/grammar repo: the #1864 body, the Context7 mirror, and a crates.io search listing that also shows `willbooster-tree-sitter-php`.
- h55-control: "1861" in the prompt and in the delegate's own closing note that it did not open #1861. Same #1864 pull-request sentence. Other-commit SHAs 5ad3d72, 9b42cd3 and dbc2971 (Swift language support) in `git log` and `gh` listing output; no `git show` of it. "tree-sitter-php" outside registry/grammar repo: the #1864 body; local registry paths were classified allowed.
- h55-treatment: "1861" in the prompt and in the delegate's note that it skipped #1861. Same #1864 pull-request sentence. The delegate ran `git show dbc2971 -- crates/aptu-coder-core/src/languages/mod.rs` (Swift support commit, a commit other than 132ea687; SHAs dbc2971, 2793835, 8d7dd78 in the diff output) plus `git log` SHAs 5ad3d72, 9b42cd3. "tree-sitter-php" outside registry/grammar repo: the #1864 body.

tool-log.jsonl targets: four hits, all the string "tree-sitter-php" in Context7 resolve and brave_search query targets (h45-control seq 15, 23, 24; h45-treatment seq 16). None contain 1861, a pull request or a commit SHA.

### Decision

- Date and scorer commit: 2026-11-27, scorer commit ce7f054.
- Gate arithmetic on primary_total (0 to 3.0), band [0.9, 2.1], control run only (n = 1 per model):
  - claude-haiku-4-5: control primary_total 0.75 (below 0.9); treatment 2.0.
  - claude-haiku-5-5: control primary_total 1.9091 (in band); treatment 1.9091.
  - No failure_mode in any run.
- Verdict: CONTAMINATED under the literal Step 3 rule, which excludes all four runs from evidence (hits listed above). Two further readings for the record:
  - Counting only reads of another commit as contamination: h55-control (dbc2971 in listing output) and h55-treatment (explicit `git show dbc2971`) are excluded; h45-control stays in evidence at 0.75, which is FLOOR (< 0.9). Either way the re-pilot does not PASS.
  - The #1864 body and the Context7 grammar mirror are the task's own inputs and arguably should not count; that is a protocol call, not made here.
- Primary-criterion observations (not gate evidence while contaminated): C3 is bimodal (0.0 in both runs whose element query fails to compile or match, 1.0 in the other two); C4 is 0.75 to 1.0; C5 is 1.0 only in h55-treatment (6 write, 7 read captures), 0.0 elsewhere (two defuse drafts do not compile, one compiles with zero captures). C5 is the main source of headroom on the primary scale; C6 and C7 now vary, with C7.mod_registration at 0.0 in all four runs as the remaining floor.

### h4-5 control re-check (n=3)

Date 2026-11-27, scorer commit ce7f054, plan `plans/pilot-h45-recheck.csv` (prompt 671e5db1, sha confirmed), evidence `scorer/pilot-evidence/h45-recheck/` (SHA256SUMS alongside), concurrency 2, no turn cap, wall clock 17:11:58Z to 17:14:08Z. Both runs exit 0 with no failure_mode. Scores in `scorer/pilot-evidence/h45-recheck/recheck-scores.json` (scored_at 2026-11-27T17:20:00Z, run_id "unknown", mapped by argv order).

| control run | C3 | C4 | C5 | primary_total | total | cost_usd | total_tokens | tool requests |
|---|---|---|---|---|---|---|---|---|
| h45-control (earlier re-pilot under plans/pilot.csv) | 0.0 | 0.75 | 0.0 | 0.75 | 2.3401 | 0.23535645 | 1,292,513 | 33 |
| h45-control-r2 | 0.0 | 1.0 | 0.0 | 1.0 | 2.41 | 0.2258123 | 1,351,448 | 32 |
| h45-control-r3 | 0.0 | 0.75 | 0.0 | 0.75 | 2.1401 | 0.2650335 | 1,488,606 | 35 |

Mean primary_total over the three claude-haiku-4-5 controls: 0.8333 (min 0.75, max 1.0). All three are below 0.9: yes. C3 is 0.0 in all three (element query does not compile in r2 and r3; matches nothing in the first) and C5 is 0.0 in all three (defuse draft does not compile in r2 and r3), so the floor reading on the primary scale holds at n = 3.

Contamination (narrow rule: opening, searching or reading #1861; any aptu-coder pull-request URL; any file or commit that adds PHP support):

- h45-control-r2: no hits.
- h45-control-r3: hit. The delegate did not request #1861, but two `brave_search__brave_llm_context` calls returned it: query "tree-sitter-php crate version crates.io" returned `https://github.com/clouatre-labs/aptu-coder/issues/1861` with title "[FEATURE] Add PHP language support via tree-sitter-php grammar", and query "tree-sitter-php interface_declaration trait_declaration grammar node types" returned a snippet of its body ("tree_sitter_php :: Ptr Language ... data Grammar Source ... Statically-known rules corresponding to symbols in the grammar"). The delegate then wrote "I found the closed issue #1861 which has the exact implementation notes" and listed 1861 first in `related_issues`. No aptu-coder pull-request URL; the only `git show` was of the pinned commit 132ea687; no PHP-support diff or file write outside `exp5-output.json`.
- Excluding r3, the clean controls are 0.75 and 1.0 (mean 0.875), still both below 0.9.

Session ids: h45-control-r2 = 20261127_88, h45-control-r3 = 20261127_87 (goose 1.61.1 sessions.db; also in `scorer/pilot-evidence/h45-recheck/latency-log.jsonl` and `label-map.json`).

Evidence: `scorer/pilot-evidence/h45-recheck/` holds `recheck-scores.json`, `label-map.json`, `latency-log.jsonl`, `tool-log.jsonl`, `contamination-narrow.txt` and `h45-control-r2/exp5-output.json`, `h45-control-r3/exp5-output.json`; SHA256SUMS in the same directory lists all seven files (the clones are not committed).

Instrument note: these two runs used runner-prompt 671e5db1 with web search available, and the h45-control-r3 leak above is the one PR #125 (#124) closed. The instrument for the main run is runner-prompt 2878315307c0c3a5d5646ffea8efd00bfd84f780a774cefcabbf66f3753793b5 with no clone remote, a gh fence and no web search; the h4-5 control is re-read under that instrument before deposit.

Qualification of the conclusion: h45-control-r3 is a contamination hit, so under the exclusion rule the admissible controls are n = 2 (0.75 and 1.0, mean 0.875), both below 0.9. The n = 3 reading (mean 0.8333) above is the sensitivity reading only.

# Runner Prompt: exp5-php-grammar-powered

Derived from `experiments/exp-swift-grammar-mercury/runner-prompt-v3.md`, re-targeted from aptu-coder#648 (Swift grammar) to aptu-coder#1864 (PHP grammar). Changes: the task, issue and HEAD SHA; Step 3 templates (`java.rs`, `swift.rs`, `css` wiring); Step 4 (tree-sitter-php); Step 5 (issue thread only, with no linked-PR check, because external pull requests are not accepted for this issue); Step 7 artifacts (PHP node kinds, `php.rs` wiring). Rule 8, the output schema and the remaining JSON field names are unchanged, except that the snippet field is `code`, the run identity fields are dropped (the harness supplies them from `label-map.json`) and `session_id` is `null` (the harness resolves it by session name, so the delegate does not query the local session database).

The only placeholder is `{output_path}`, a relative path inside the clone. The clone root is the working directory of the run, so no local path appears here.

The text after the `---` line is the prompt body. `gen_recipes.py` copies it byte-verbatim into `prompt` for every arm. The treatment arm repeats the same body a second time in `instructions`; the user prompt stays identical across arms.

---

You are running a Scout experiment run. Record the wall-clock start time immediately.

TASK: clouatre-labs/aptu-coder#1864 -- add PHP language support via tree-sitter-php.

Repository: https://github.com/clouatre-labs/aptu-coder
Issue: https://github.com/clouatre-labs/aptu-coder/issues/1864
HEAD SHA: 132ea687e09a916091699a562da3c96c86ec1fd8

Your clone: your working directory is the root of a fresh clone of the repository, already checked out at HEAD SHA. Do not clone it again.

Your output file: {output_path}

Record start time: run `date -u +"%Y-%m-%dT%H:%M:%SZ"` and save it.

---

# SCOUT Research Agent (READ-ONLY)

You are the SCOUT -- a creative explorer. Your job is to deeply understand the codebase, research the ecosystem, and propose 2-3 solution approaches. You cast a wide net.

## Constraint
READ-ONLY. No code changes, no commits. Only write to {output_path}.

## Rules
1. Work in the clone root: it is your working directory; run commands there
2. No emojis in output
3. Concise: Lead with summary, use bullets
4. Efficiency: Chain shell commands with `&&` to reduce turns
5. Efficiency: Use `rg` with multiple patterns in one call
6. Efficiency: Limit Context7 lookups to 2 libraries max
7. Tool priority for research: (1) `gh` CLI for issues, PRs, repo metadata, cross-repo search; (2) Context7 for library docs and APIs; (3) brave_search as last resort for cross-project design rationale or blog posts (max 2 queries)
8. Do not let conciseness (Rule 3) or turn-efficiency (Rule 4) shorten Step 7's literal artifacts. Those fields must contain actual quoted text, not a description of what the text would contain.

## Step 1: Repo Structure
- Read README, Cargo.toml, and the `crates/aptu-coder-core/src/languages/` directory
- Identify project layout and module organization
- Note build system, CI configuration

## Step 2: Conventions
- Commit style (conventional commits, signed, DCO)
- Testing patterns (unit, integration, test location)
- Linting and formatting tools
- Error handling patterns
- Import/module organization

## Step 3: Relevant Code Analysis
- Identify files related to language registration (e.g., `languages/java.rs` as the file the issue says to model after, `lang.rs` EXTENSION_MAP)
- Trace call chains for `get_language_info()` and `get_ts_language()`
- Review existing query constants and handlers for other languages as templates, including at least one existing `extract_inheritance` implementation
- Note test coverage for language registration
- Open `crates/aptu-coder-core/src/languages/mod.rs` and read the literal `LanguageInfo` struct definition (field names and types) -- you will quote it verbatim in Step 7.
- Open `crates/aptu-coder-core/src/languages/java.rs` and read its literal `ELEMENT_QUERY` and `DEFUSE_QUERY` constant text -- you will quote it verbatim in Step 7.
- Open `crates/aptu-coder-core/src/languages/lang.rs` and read the literal `EXTENSION_MAP` entries and the `"css"` wiring pattern (workspace dependency, Cargo.toml dependency, extension entry, `mod` registration, match arms) -- you will restate these facts verbatim in Step 7's `wiring_summary`.

## Step 4: Ecosystem Research
- From imports and manifest files found in Steps 1-3, identify the 2-3 libraries most relevant (tree-sitter, tree-sitter-php).
- Use Context7 or brave_search to find tree-sitter-php's actual Cargo.toml manifest (tree-sitter/tree-sitter-php) and its grammar's `php/src/node-types.json` or `php/src/grammar.js` -- you need their literal content, not a paraphrase, for Step 7. Confirm every node kind and field name you use against those files.
- Search for how similar language integrations were done in the repo (e.g., Java, Kotlin, Swift).

## Step 5: Issue Context
- Read the issue thread for context and discussion
- Note any maintainer preferences expressed in comments

## Step 6: Propose Approaches
- Identify 2-3 solution approaches
- For each: describe changes, list pros/cons, estimate complexity
- Include an approach that adds the required `DEFUSE_QUERY` constant, citing what makes it required.

## Step 7: Produce Literal Artifacts (required -- do not skip or paraphrase)
For your recommended approach, produce these as literal, quoted text (not descriptions of what they would contain):
- `language_info_struct_citation`: the literal field list you read from `mod.rs`'s `LanguageInfo` struct (paste the actual field names and types).
- `element_query_draft`: the literal tree-sitter query text you propose for PHP's `ELEMENT_QUERY`, covering at least `function_definition`, `method_declaration`, `class_declaration`, `interface_declaration` and `trait_declaration`, each with the specific field (e.g. `name`) and capture label you use.
- `defuse_query_draft`: the literal tree-sitter query text you propose for PHP's `DEFUSE_QUERY`, adapted from java.rs's actual pattern, covering local declarations, assignments, and identifier reads.
- `inheritance_walk_citation`: a literal description of the exact field-by-field walk from a class declaration to its `extends` and `implements` names in the tree-sitter-php grammar, citing the grammar source you inspected in Step 4.
- `test_snippets`: an array of at least 9 objects, tagged by a `dimension` field with value `"declaration_kind"` or `"inheritance_shape"`:
  - 6 entries with `"dimension": "declaration_kind"`, one per PHP declaration kind (class, interface, trait, enum, function, method)
  - 3 entries with `"dimension": "inheritance_shape"`, one per inheritance shape: single superclass, multiple interfaces, and mixed (superclass + interfaces)
  - every entry has a literal PHP code snippet in its `code` field and a literal proposed test function name, regardless of dimension
- `wiring_summary`: an object consolidating all 5 structural wiring facts in one place, each a literal one-line statement of that specific fact (not a paragraph):
  - `workspace_dependency`: the literal `[workspace.dependencies]` entry you propose for tree-sitter-php
  - `unconditional_dependency`: the literal dependency line you propose for `crates/aptu-coder-core/Cargo.toml` (no feature flag)
  - `extension_map_entry`: the literal `.php` entry you propose for `EXTENSION_MAP` in `lang.rs`
  - `mod_registration`: the literal `mod php;` registration statement and where it goes
  - `match_arms`: the literal match arms you propose for both `get_language_info()` and `get_ts_language()`

## Output
Write the result as valid JSON to {output_path} with this schema:
```json
{
  "started_at": "<ISO8601>",
  "finished_at": "<ISO8601>",
  "session_id": null,
  "lens": "scout",
  "relevant_files": [{"path": "...", "line_range": "...", "role": "..."}],
  "conventions": {"commits": "...", "testing": "...", "linting": "...", "error_handling": "..."},
  "patterns": ["existing pattern 1", "existing pattern 2"],
  "related_issues": [{"number": 0, "title": "...", "relevance": "..."}],
  "constraints": ["architectural constraint 1"],
  "test_coverage": "description of existing test coverage for affected areas",
  "library_findings": [{"library": "...", "version": "...", "relevant_api": "...", "notes": "..."}],
  "approaches": [
    {"name": "...", "description": "...", "pros": [], "cons": [], "complexity": "simple|medium|complex", "files_touched": 0}
  ],
  "recommendation": "which approach and why",
  "language_info_struct_citation": "<literal quoted struct fields from mod.rs>",
  "element_query_draft": "<literal tree-sitter query text, >=5 patterns>",
  "defuse_query_draft": "<literal tree-sitter query text>",
  "inheritance_walk_citation": "<literal field-walk description citing grammar source>",
  "test_snippets": [{"dimension": "declaration_kind|inheritance_shape", "declaration_kind": "...", "code": "...", "test_name": "..."}],
  "wiring_summary": {
    "workspace_dependency": "<literal [workspace.dependencies] entry>",
    "unconditional_dependency": "<literal Cargo.toml dependency line>",
    "extension_map_entry": "<literal .php EXTENSION_MAP entry>",
    "mod_registration": "<literal mod php; statement and location>",
    "match_arms": "<literal match arms for get_language_info() and get_ts_language()>"
  },
  "latency_seconds": 0,
  "message_count": 0
}
```

After writing the JSON, verify it parses: `python3 -m json.tool {output_path} > /dev/null && echo VALID`

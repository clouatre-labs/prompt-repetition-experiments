"""Executable checks for the literal Exp5 session artifacts (C3..C7).

Everything here is offline and deterministic: session JSON is read as data only,
PHP snippets and queries are parsed/compiled with tree-sitter, never executed.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import tree_sitter_php
from tree_sitter import Language, Parser, Query, QueryCursor

HERE = Path(__file__).resolve().parent
CORPUS_DIR = HERE / "fixtures" / "php"
NODE_TYPES = json.loads((HERE / "vendor" / "tree-sitter-php-node-types.json").read_text())
APTU_SNAPSHOT = HERE / "vendor" / "aptu-coder"
NODE_KINDS = {e["type"] for e in NODE_TYPES if e.get("named")}
NODE_FIELDS = {f for e in NODE_TYPES for f in e.get("fields", {})}

# tree-sitter-php 0.25.2 names (NOT function_declaration): see README "Rubric mapping".
DECLARATION_KINDS = (
    "function_definition",
    "method_declaration",
    "class_declaration",
    "interface_declaration",
    "trait_declaration",
    "enum_declaration",
)
INHERITANCE_KINDS = ("base_clause", "class_interface_clause")
SNIPPET_DIMENSIONS = ("declaration_kind", "inheritance_shape")
WIRING_KEYS = (
    "workspace_dependency",
    "unconditional_dependency",
    "extension_map_entry",
    "mod_registration",
    "match_arms",
)


@dataclass(frozen=True)
class Result:
    score: float
    justification: str


def php_language() -> Language:
    return Language(tree_sitter_php.language_php())


def compile_query(text: str, lang: Language) -> Query | None:
    try:
        return Query(lang, text)
    except Exception:  # tree-sitter raises QueryError on bad node types/fields
        return None


def _corpus_trees(lang: Language) -> list:
    parser = Parser(lang)
    return [
        parser.parse(p.read_bytes())
        for p in sorted(CORPUS_DIR.glob("*.php"))
    ]


def _pattern_kind(pattern: str) -> str | None:
    """Root node kind of a query pattern such as '(function_definition name: (name) @f)'."""
    m = re.search(r"\(\s*([a-z_]+)", pattern)
    return m.group(1) if m else None


def _split_patterns(text: str) -> list[str]:
    """Split query text into top-level s-expression patterns (comments dropped)."""
    text = re.sub(r";[^\n]*", "", text)
    patterns, depth, start = [], 0, None
    for i, ch in enumerate(text):
        if ch == "(":
            if depth == 0:
                start = i
            depth += 1
        elif ch == ")" and depth > 0:
            depth -= 1
            if depth == 0 and start is not None:
                patterns.append(text[start : i + 1])
    return patterns


def check_element_query(text: str, lang: Language) -> Result:
    """C3: query compiles and its captures cover the required declaration kinds."""
    if not text or not text.strip():
        return Result(0.0, "C3: no literal element_query_draft found")
    query = compile_query(text, lang)
    if query is None:
        return Result(0.0, f"C3: element_query_draft does not compile: {text.strip()[:80]!r}")
    trees = _corpus_trees(lang)
    covered: set[str] = set()
    for pattern in _split_patterns(text):
        kind = _pattern_kind(pattern)
        if kind in DECLARATION_KINDS and _matches_any(compile_query(pattern, lang), trees):
            covered.add(kind)
    missing = [k for k in DECLARATION_KINDS if k not in covered]
    score = len(covered) / len(DECLARATION_KINDS)
    why = f"C3: {len(covered)}/{len(DECLARATION_KINDS)} declaration kinds matched on the fixture corpus"
    if missing:
        why += f"; missing {missing}"
    if len(_split_patterns(text)) < 3:
        why += "; fewer than 3 patterns"
        score = min(score, 0.5)
    return Result(score, why)


def _matches_any(query: Query | None, trees: list) -> bool:
    """True if the query captures anything in at least one corpus file."""
    if query is None:
        return False
    return any(any(QueryCursor(query).captures(t.root_node).values()) for t in trees)


def check_inheritance_citation(text: str) -> Result:
    """C4: every snake_case node kind / field named in the walk exists in node-types.json."""
    if not text or not text.strip():
        return Result(0.0, "C4: no inheritance_walk_citation found")
    cited = set(re.findall(r"\b[a-z]+(?:_[a-z]+)+\b", text))
    known = {c for c in cited if c in NODE_KINDS or c in NODE_FIELDS}
    if not cited:
        return Result(0.0, "C4: walk names no node kinds or fields")
    invented = sorted(cited - known)
    if not known & set(INHERITANCE_KINDS):
        return Result(0.0, f"C4: walk does not cite base_clause/class_interface_clause; invented {invented}")
    score = len(known) / len(cited)
    why = f"C4: {len(known)}/{len(cited)} cited kinds/fields exist in node-types.json"
    if invented:
        why += f"; invented {invented}"
    return Result(score, why)


def check_defuse_query(text: str, lang: Language) -> Result:
    """C5: DEFUSE query compiles and captures writes (assignment left) and reads."""
    if not text or not text.strip():
        return Result(0.0, "C5: no literal defuse_query_draft found")
    query = compile_query(text, lang)
    if query is None:
        return Result(0.0, f"C5: defuse_query_draft does not compile: {text.strip()[:80]!r}")
    tree = Parser(lang).parse((CORPUS_DIR / "defuse.php").read_bytes())
    writes = reads = 0
    for nodes in QueryCursor(query).captures(tree.root_node).values():
        for node in nodes:
            if node.type != "variable_name":
                continue
            parent = node.parent
            if parent is not None and parent.type.endswith("assignment_expression"):
                writes += 1  # a variable_name directly under an assignment is its left-hand side
            else:
                reads += 1
    score = (1 + (writes > 0) + (reads > 0)) / 3
    return Result(score, f"C5: defuse query compiles; write captures={writes}, read captures={reads}")


def _parses(src: str, lang: Language) -> bool:
    src = src if src.lstrip().startswith("<?") else "<?php " + src
    tree = Parser(lang).parse(src.encode())
    root = tree.root_node
    return not root.has_error and any(n.type == "php_tag" for n in root.children)


def check_snippets(snippets: list | None, lang: Language) -> Result:
    """C6: share of snippets that parse, weighted by dimension coverage."""
    if not snippets:
        return Result(0.0, "C6: no test_snippets found")
    ok = [s for s in snippets if isinstance(s, dict) and _parses(str(s.get("code", "")), lang)]
    bad = [s.get("test_name", s.get("declaration_kind", "?")) for s in snippets if s not in ok]
    dims = {str(s.get("dimension")) for s in ok} & set(SNIPPET_DIMENSIONS)
    parse_share = len(ok) / len(snippets)
    score = parse_share * len(dims) / len(SNIPPET_DIMENSIONS)
    why = f"C6: {len(ok)}/{len(snippets)} snippets parse; dimensions covered {sorted(dims)}"
    if bad:
        why += f"; unparsable {bad}"
    return Result(score, why)


def _snapshot(name: str) -> str:
    return (APTU_SNAPSHOT / name).read_text()


def wiring_facts(wiring: object) -> dict[str, bool] | None:
    """Per-fact booleans against the vendored snapshot; None if wiring_summary is not an object."""
    if not isinstance(wiring, dict):
        return None
    ws = _snapshot("workspace.Cargo.toml")
    core = _snapshot("core.Cargo.toml")
    lang_rs = _snapshot("lang.rs")
    mod_rs = _snapshot("mod.rs")
    facts: dict[str, bool] = {
        # Sibling shape: `tree-sitter-java = "0.23.5"` under [workspace.dependencies].
        "workspace_dependency": bool(
            re.search(r'tree-sitter-php\s*=\s*"[^"]+"', str(wiring.get("workspace_dependency", "")))
        )
        and "tree-sitter-php" not in ws,
        # Sibling shape: `tree-sitter-java = { workspace = true }` in the core crate.
        "unconditional_dependency": bool(
            re.search(r'tree-sitter-php\s*=\s*\{\s*workspace\s*=\s*true\s*\}', str(wiring.get("unconditional_dependency", "")))
        )
        and "tree-sitter-php" not in core,
        # Sibling shape: `("java", "java"),` in EXTENSION_MAP.
        "extension_map_entry": bool(
            re.search(r'\(\s*"php"\s*,\s*"php"\s*\)', str(wiring.get("extension_map_entry", "")))
        )
        and '"php"' not in lang_rs,
        # Sibling shape: `pub mod java;` at the top of languages/mod.rs.
        "mod_registration": bool(
            re.search(r"^\s*(pub\s+)?mod\s+php\s*;", str(wiring.get("mod_registration", "")), re.M)
        )
        and not re.search(r"^\s*(pub\s+)?mod\s+php\s*;", mod_rs, re.M),
        # Sibling shape: `"java" => Some(tree_sitter_java::LANGUAGE.into()),` in both fns.
        "match_arms": bool(re.search(r'"php"\s*=>', str(wiring.get("match_arms", ""))))
        and "tree_sitter_php::LANGUAGE" in str(wiring.get("match_arms", "")),
    }
    return facts


def check_wiring(wiring: object) -> Result:
    """C7: five structural facts graded against the vendored pre-PHP aptu-coder snapshot."""
    facts = wiring_facts(wiring)
    if facts is None:
        return Result(0.0, "C7: wiring_summary missing or not an object")
    score = sum(facts.values()) / len(WIRING_KEYS)
    why = f"C7: {sum(facts.values())}/{len(WIRING_KEYS)} wiring facts match the vendored snapshot"
    missing = [k for k in WIRING_KEYS if not facts[k]]
    if missing:
        why += f"; failing {missing}"
    return Result(score, why)


def score_artifacts(artifacts: dict, lang: Language | None = None) -> dict[str, Result]:
    lang = lang or php_language()
    return {
        "C3": check_element_query(artifacts.get("element_query_draft", ""), lang),
        "C4": check_inheritance_citation(artifacts.get("inheritance_walk_citation", "")),
        "C5": check_defuse_query(artifacts.get("defuse_query_draft", ""), lang),
        "C6": check_snippets(artifacts.get("test_snippets"), lang),
        "C7": check_wiring(artifacts.get("wiring_summary")),
    }

#!/usr/bin/env python3
"""Exp5 output-overlap rule (protocol.md, Exclusions).

Jaccard similarity over the set of lowercase node kinds and field names
cited in the run's ``element_query_draft`` and ``defuse_query_draft`` versus
the same sets extracted from the vendored ``scorer/vendor/
tree-sitter-php-node-types.json`` (named node types and field names). Cited
identifiers are the snake_case tokens of each draft after ``;`` comments are
dropped, lowercased; the cited set is intersected with the vocabulary and the
similarity is ``|cited ∩ vocabulary| / |vocabulary|`` per draft. A run is
excluded when the similarity is above ``THRESHOLD`` for either draft.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

DRAFTS = ("element_query_draft", "defuse_query_draft")
THRESHOLD = 0.8
TOKEN = re.compile(r"\b[a-z]+(?:_[a-z]+)+\b")  # as worded in protocol.md
COMMENT = re.compile(r";[^\n]*")  # tree-sitter query comments


def vocabulary(node_types_json) -> set[str]:
    """Named node types and field names from a node-types.json list."""
    entries = json.loads(Path(node_types_json).read_text(encoding="utf-8")) if isinstance(node_types_json, (str, Path)) else node_types_json
    kinds = {e["type"] for e in entries if e.get("named")}
    fields = {f for e in entries for f in e.get("fields", {})}
    return kinds | fields


def cited(text: str | None, vocab: set[str]) -> set[str]:
    """Lowercase snake_case tokens of one draft (comments dropped) that are in the vocabulary."""
    if not text:
        return set()
    tokens = {t.lower() for t in TOKEN.findall(COMMENT.sub("", str(text)))}
    return tokens & vocab


def similarity(text: str | None, vocab: set[str]) -> float:
    return len(cited(text, vocab)) / len(vocab) if vocab else 0.0


def jaccard_by_draft(output_json: dict, node_types_json) -> dict[str, float | None]:
    """Similarity per draft; None when the draft is absent from the output file."""
    vocab = vocabulary(node_types_json)
    out: dict[str, float | None] = {}
    for draft in DRAFTS:
        text = output_json.get(draft)
        out[draft] = None if text is None else round(similarity(text, vocab), 4)
    return out


def jaccard(output_json: dict, node_types_json, draft: str | None = None) -> float:
    """The run's overlap on [0, 1]: one draft's similarity, or the larger of the two.

    The larger of the two drafts is the quantity the exclusion rule compares
    with the threshold; a draft missing from the output counts as 0.0.
    """
    values = jaccard_by_draft(output_json, node_types_json)
    if draft is not None:
        value = values[draft]
        return 0.0 if value is None else float(value)
    return max(0.0 if v is None else float(v) for v in values.values())


def excluded(output_json: dict, node_types_json) -> bool:
    return jaccard(output_json, node_types_json) > THRESHOLD

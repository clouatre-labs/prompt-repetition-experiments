#!/usr/bin/env python3
"""Exp5 contamination exclusion (protocol.md, Exclusions; scorer/HEADROOM-pilot.md,
"Contamination scan (narrowed rule)").

A hit is one of three categories, applied to the tool requests and tool
results of a run's exported goose session transcript (``goose session export
--format json``) and to the targets of its ``tool-log.jsonl`` rows:

1. ``issue_1861``: the number 1861 appears in a tool request or tool result.
2. ``aptu_coder_pull_request``: an aptu-coder pull-request URL
   (``github.com/clouatre-labs/aptu-coder/pull/<n>``) or an aptu-coder
   ``pulls/`` API path (``repos/clouatre-labs/aptu-coder/pulls``) appears in
   a tool request or tool result.
3. ``network_outside_fence``: a tool request contains any of the tokens
   ``curl``, ``wget``, ``git fetch``, ``git pull``, ``cargo fetch`` or
   ``fetch(``.

Category 3 looks only at what a run requested, never at the content of a
result: the #1864 body, the delegate's own ``exp5-output.json`` (written or
read back) and grammar-repository or registry results are not hits by
construction. Assistant text and the prompt are never scanned. Each hit
names the run id, the category, the source (tool request, tool result or
tool-log target) and the message index in the transcript's ``conversation``
list (the ``seq`` for a tool-log row).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

CATEGORIES = {
    "issue_1861": 1,
    "aptu_coder_pull_request": 2,
    "network_outside_fence": 3,
}
ISSUE_1861 = re.compile(r"\b1861\b")
PULL_REQUEST = re.compile(r"github\.com/clouatre-labs/aptu-coder/pull/\d+|repos/clouatre-labs/aptu-coder/pulls\b")
NETWORK_TOKENS = ("curl", "wget", "git fetch", "git pull", "cargo fetch", "fetch(")
NETWORK = re.compile(r"\bcurl\b|\bwget\b|\bgit\s+fetch\b|\bgit\s+pull\b|\bcargo\s+fetch\b|fetch\(")
REQUEST_RULES = (("issue_1861", ISSUE_1861), ("aptu_coder_pull_request", PULL_REQUEST), ("network_outside_fence", NETWORK))
RESULT_RULES = REQUEST_RULES[:2]


def load_transcript(path: Path) -> dict:
    """Parsed ``goose session export --format json`` file."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _run_id(transcript: dict | None, tool_log: list) -> str | None:
    for row in tool_log or []:
        if row.get("run_id"):
            return row["run_id"]
    name = (transcript or {}).get("name") or ""
    return name[len("exp5-"):] if name.startswith("exp5-") else (name or None)


def _texts(value) -> list[str]:
    """Every string leaf of a decoded JSON value, scanned as decoded text
    (a JSON dump would turn a line break before a number into ``\\n`` and
    hide the word boundary)."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [t for v in value.values() for t in _texts(v)]
    if isinstance(value, list):
        return [t for v in value for t in _texts(v)]
    return []


def _hits_in(texts: list[str], rules, source: str, index, run_id: str | None, tool: str | None) -> list[dict]:
    hits = []
    for category, pattern in rules:
        m = next((m for t in texts if (m := pattern.search(t))), None)
        if m:
            hits.append({"run_id": run_id, "category": category, "number": CATEGORIES[category], "source": source,
                         "message_index": index, "tool": tool, "match": m.group(0)})
    return hits


def scan(transcript: dict | None, tool_log: list) -> list[dict]:
    """Contamination hits of one run over its transcript and tool-log rows.

    ``transcript`` is a parsed goose JSON export (or None when the run has
    none); ``tool_log`` is the list of that run's ``tool-log.jsonl`` rows.
    Returns hits sorted by source order (transcript first, tool log after),
    each naming the run id, category, source and message index.
    """
    tool_log = list(tool_log or [])
    run_id = _run_id(transcript, tool_log)
    hits: list[dict] = []
    for index, message in enumerate((transcript or {}).get("conversation", [])):
        for item in message.get("content", []):
            kind = item.get("type")
            if kind == "toolRequest":
                call = item.get("toolCall", {}).get("value", {})
                tool = call.get("name")
                hits += _hits_in(_texts(call.get("arguments")), REQUEST_RULES, "tool_request", index, run_id, tool)
            elif kind == "toolResponse":
                hits += _hits_in(_texts(item.get("toolResult", {}).get("value")), RESULT_RULES, "tool_result", index, run_id, None)
    for row in tool_log:
        target = row.get("target")
        if target:
            hits += _hits_in([str(target)], REQUEST_RULES, "tool_log", row.get("seq"), run_id, row.get("tool"))
    return hits


def scan_run(transcript_path: Path | None, tool_log: list) -> list[dict]:
    """``scan`` over a transcript file (None when absent) and the run's tool-log rows."""
    return scan(load_transcript(transcript_path) if transcript_path is not None else None, tool_log)


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("transcript", type=Path, nargs="?", help="goose session export --format json")
    parser.add_argument("--tool-log", type=Path, nargs="?", default=None, help="tool-log.jsonl; only rows of the transcript's run are scanned")
    parser.add_argument("--run-id", default=None, help="run id when the transcript has no exp5-<run_id> name")
    args = parser.parse_args(argv)
    transcript = load_transcript(args.transcript) if args.transcript else None
    run_id = args.run_id or _run_id(transcript, [])
    rows = []
    if args.tool_log:
        rows = [r for r in map(json.loads, filter(str.strip, args.tool_log.read_text(encoding="utf-8").splitlines()))
                if run_id is None or r.get("run_id") == run_id]
    hits = scan(transcript, rows)
    for h in hits:
        print(f"{h['run_id']}\tcategory {h['number']} ({h['category']})\t{h['source']}\tmessage {h['message_index']}\t{h['match']}")
    print(f"{len(hits)} hit{'s' if len(hits) != 1 else ''}")
    return 1 if hits else 0


if __name__ == "__main__":
    raise SystemExit(main())

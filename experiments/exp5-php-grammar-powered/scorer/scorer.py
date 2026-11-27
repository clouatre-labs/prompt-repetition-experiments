#!/usr/bin/env python3
"""Offline deterministic scorer for Exp5 (PHP grammar) runner-prompt-v3 sessions.

Usage:
    uv run scorer.py SESSION.json [SESSION.json ...] --out scores.json
    uv run scorer.py --report-variance SESSIONS_DIR

Session JSON is read as data only; nothing in it is executed.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

from checks import WIRING_KEYS, php_language, score_artifacts, wiring_facts

SCORER = "exp5-php-scorer/0.1.0 (tree-sitter 0.25.2, tree-sitter-php 0.25.2)"
RUBRIC_VERSION = "exp5-rubric-v1-fractional"
CRITERIA = ("C3", "C4", "C5", "C6", "C7")
# Primary score since the 2026-11-27 pilot: C6 and C7 were 1.0 in every pilot run (zero variance),
# so the protocol's floor/ceiling rule excludes them; they stay in the record and are reported.
PRIMARY_CRITERIA = ("C3", "C4", "C5")
ARTIFACT_KEYS = (
    "element_query_draft",
    "inheritance_walk_citation",
    "defuse_query_draft",
    "test_snippets",
    "wiring_summary",
)


def _num(value: object) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _fmt(value: float | None) -> float | None:
    return None if value is None else round(value, 4)


def score_session(session: dict) -> dict:
    """Build one DATA_DICTIONARY-conformant score record from a session JSON object."""
    results = score_artifacts({k: session.get(k) for k in ARTIFACT_KEYS})
    # C1/C2 (external-citation criteria) are not executable offline: copy verbatim or null.
    copied = {"C1": _num(session.get("C1")), "C2": _num(session.get("C2"))}
    record: dict = {"run_id": str(session.get("run_id", "unknown")), "C1": _fmt(copied["C1"]), "C2": _fmt(copied["C2"])}
    record.update({c: _fmt(results[c].score) for c in CRITERIA})
    record["total"] = _fmt(sum(results[c].score for c in CRITERIA))
    record["primary_total"] = _fmt(sum(results[c].score for c in PRIMARY_CRITERIA))
    justifications = {
        "C1": "copied verbatim from session" if copied["C1"] is not None else "not executable offline: null",
        "C2": "copied verbatim from session" if copied["C2"] is not None else "not executable offline: null",
    }
    justifications.update({c: results[c].justification for c in CRITERIA})
    record["justifications"] = justifications
    return record


def build_scores(sessions: list[dict], scored_at: str) -> dict:
    return {
        "scored_at": scored_at,
        "scorer": SCORER,
        "rubric_version": RUBRIC_VERSION,
        "note": "C3..C7 are fractional in [0,1]; total = sum(C3..C7); primary_total = C3 + C4 + C5 (C6, C7 excluded under the protocol floor/ceiling rule, reported). C1/C2 copied verbatim when present, else null.",
        "scores": [score_session(s) for s in sessions],
    }


def _spread(values: list) -> dict:
    values = [v for v in values if v is not None]
    if not values:
        return {"n": 0, "min": None, "max": None, "mean": None, "variance": None}
    return {
        "n": len(values),
        "min": _fmt(min(values)),
        "max": _fmt(max(values)),
        "mean": _fmt(statistics.fmean(values)),
        "variance": _fmt(statistics.pvariance(values)),
    }


def report_variance(sessions: list[dict]) -> dict:
    """Per-criterion between-run spread across a set of sessions (for HEADROOM analysis)."""
    out: dict = {}
    for key in CRITERIA:
        out[key] = _spread([score_session(s)[key] for s in sessions])
    for key in WIRING_KEYS:
        facts = [wiring_facts(s.get("wiring_summary")) for s in sessions]
        out[f"C7.{key}"] = _spread([None if f is None else float(f[key]) for f in facts])
    return out


def _sessions(paths: list[Path]) -> list[dict]:
    files: list[Path] = []
    for p in paths:
        files.extend(sorted(p.glob("*.json")) if p.is_dir() else [p])
    return [json.loads(f.read_text(encoding="utf-8")) for f in files]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("sessions", nargs="+", type=Path, help="session JSON files or directories")
    parser.add_argument("--out", type=Path, help="write scores.json here (default: stdout)")
    parser.add_argument("--scored-at", default="", help="override scored_at for byte-identical reruns")
    parser.add_argument("--report-variance", action="store_true", help="print per-criterion between-run variance")
    args = parser.parse_args(argv)

    php_language()  # fail fast if the pinned binding is broken
    sessions = _sessions(args.sessions)
    if args.report_variance:
        payload = report_variance(sessions)
    else:
        payload = build_scores(sessions, args.scored_at or datetime.now(timezone.utc).isoformat(timespec="seconds"))
    text = json.dumps(payload, indent=2) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

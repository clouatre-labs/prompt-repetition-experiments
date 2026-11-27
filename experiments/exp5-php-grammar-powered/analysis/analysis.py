#!/usr/bin/env python3
"""Exp5 analysis: per-arm means, per-model Mann-Whitney effects, assertions and
cache-adjusted cost. Deterministic: analyzed_at derives from the inputs, keys
are sorted and every float has fixed rounding. No network calls.

Outcome variables (protocol.md, Primary Outcome): the primary outcome is
``primary_total = C3 + C4 + C5`` (range [0, 3]) exactly as the scorer emits it;
``primary_total`` minus C5 (range [0, 2]) is the co-reported outcome and is
computed for every run. C6 and C7 and ``total`` (max 5) are retained in the
record only. Only pre-#123 Exp4 fixtures, which lack ``primary_total``, fall
back to ``total``.

Usage: python analysis.py <experiment_dir> [--out DIR] [--seed N] [--transcripts DIR]
Exit status is 1 when any recorded assertion fails; outputs are still written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

from contamination import CATEGORIES as CONTAMINATION_CATEGORIES, scan_run
from overlap import DRAFTS, jaccard_by_draft
from stats import EFFECT_SIZE_NOTE, bootstrap_ci, mann_whitney_r, wilson_ci

CRITERIA = ["C3", "C4", "C5", "C6", "C7"]
PRIMARY_CRITERIA = ["C3", "C4", "C5"]
ARMS = ["control", "treatment"]
OUTCOMES = {
    "primary": {"field": "primary_total", "label": "primary_total = C3 + C4 + C5", "range": [0, 3]},
    "minus_c5": {"field": "primary_total_minus_c5", "label": "primary_total minus C5 = C3 + C4", "range": [0, 2]},
}
PASS_THRESHOLD = 0.5
DEFAULT_SEED = 20261127
EXCLUSION_REASONS = ("turn_cap", "failed_run", "contamination")  # protocol.md Exclusions
TURN_CAP_MODE = "goose_exit_1"  # the failure_mode goose records at --max-turns 60 (protocol.md Exclusions)
OVERLAP_CEILING = 147 / 187  # only 147 of the 187 vendored entries are snake_case: the highest reachable overlap (overlap.py)
TRANSCRIPT_NAME = "transcript.json"  # goose session export --format json, stored next to exp5-output.json
HASH_FILES = {  # label-map hash key -> file it is expected to cover
    "sha256_runner_prompt": "runner-prompt.md",
    "sha256_scorer": "scorer-prompt.md",
    "sha256_analysis": "analysis.py",
}
HERE = Path(__file__).resolve().parent
NODE_TYPES = HERE.parent / "scorer" / "vendor" / "tree-sitter-php-node-types.json"


# ---------------------------------------------------------------- loaders

def load_label_map(path: Path) -> dict:
    """Normalise flat or grouped label maps to run_id -> {group, model, ...}."""
    raw = json.loads(path.read_text())
    if not isinstance(raw, dict):
        raise ValueError("label-map must be a JSON object")
    if isinstance(raw.get("assignments"), dict):
        entries = raw["assignments"]
    elif isinstance(raw.get("main_run"), dict) and isinstance(raw["main_run"].get("assignments"), dict):
        entries = raw["main_run"]["assignments"]  # Exp4 layout
    else:
        entries = raw  # flat run_id-keyed map
    out = {}
    for run_id, value in entries.items():
        if isinstance(value, str):
            value = {"group": value}
        if not isinstance(value, dict) or "group" not in value:
            continue  # metadata keys (sealed_at, sha256, ...) in a flat map
        out[run_id] = {
            "group": value["group"],
            "model": value.get("model"),
            "goose_session_id": value.get("goose_session_id"),
            "sealed_at": value.get("sealed_at"),
            "concurrency_limit": value.get("concurrency_limit"),
            **{k: value.get(k) for k in HASH_FILES},
        }
    return out


def _criterion(value) -> float | None:
    if value is None:
        return None
    return float(value["score"]) if isinstance(value, dict) else float(value)


def _outcome_fields(row: dict, crit: dict, exp4_layout: bool) -> dict:
    """primary_total and primary_total_minus_c5 for one scored run.

    Exp5 records must carry ``primary_total`` as the scorer emitted it: a
    missing field is an error, never a silent fallback to ``total``. Exp5's
    C5 must be numeric so the co-reported outcome can be formed. The Exp4
    layout (pre-#123 fixtures) has no ``primary_total`` and uses ``total``.
    """
    if exp4_layout:
        primary = float(row["total"])
        return {"primary_total": primary, "primary_total_source": "total (Exp4 fixture without primary_total)",
                "primary_total_minus_c5": round(primary - (crit["C5"] or 0.0), 6)}
    if "primary_total" not in row:
        raise ValueError(f"Exp5 score record {row.get('run_id')!r} has no primary_total: refusing to score total")
    if crit["C5"] is None:
        raise ValueError(f"Exp5 score record {row.get('run_id')!r} has a null C5: primary_total minus C5 is undefined")
    primary = float(row["primary_total"])
    return {"primary_total": primary, "primary_total_source": "primary_total",
            "primary_total_minus_c5": round(primary - crit["C5"], 6)}


def load_scores(path: Path) -> list:
    """Return [{run_id, C3..C7, total, primary_total, primary_total_minus_c5}] from the Exp5 or Exp4 layout."""
    raw = json.loads(path.read_text())
    rows = raw if isinstance(raw, list) else raw.get("scores", [])
    out = []
    for row in rows:
        exp4_layout = isinstance(raw, list) or "scores" in row
        src = row.get("scores", row)
        crit = {c: _criterion(src.get(c)) for c in CRITERIA}
        total = row.get("total")
        if total is None:
            total = sum(v or 0 for v in crit.values())
        out.append({"run_id": row["run_id"], **crit, "total": float(total),
                    "failure_mode": row.get("failure_mode"), **_outcome_fields(row, crit, exp4_layout)})
    return out


def load_jsonl(path: Path) -> list:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


load_latency = load_jsonl  # name kept for callers of the Exp4-era loader


def find_output(outputs_dir: Path | None, run_id: str) -> Path | None:
    """The run's output file: ``<outputs_dir>/<run_id>/exp5-output.json``, or the single ``*.json``
    in that directory (or ``<outputs_dir>/<run_id>.json``) when the named file is absent."""
    if outputs_dir is None:
        return None
    named = outputs_dir / run_id / "exp5-output.json"
    if named.is_file():
        return named
    flat = outputs_dir / f"{run_id}.json"
    if flat.is_file():
        return flat
    nested = sorted(p for p in (outputs_dir / run_id).glob("*.json") if p.is_file() and p.name != TRANSCRIPT_NAME) if (outputs_dir / run_id).is_dir() else []
    return nested[0] if len(nested) == 1 else None


def find_transcript(outputs_dir: Path | None, run_id: str) -> Path | None:
    """The run's exported session transcript: ``<outputs_dir>/<run_id>/transcript.json``."""
    if outputs_dir is None:
        return None
    nested = outputs_dir / run_id / TRANSCRIPT_NAME
    return nested if nested.is_file() else None


# ---------------------------------------------------------------- exclusions

def apply_exclusions(scores: list, latency: list, outputs_dir: Path | None, node_types=NODE_TYPES, tool_log: list = (), transcripts_dir: Path | None = None) -> dict:
    """Exclusion step (protocol.md Exclusions and Stopping Rule), run before any effect.

    Per run: ``excluded`` and ``reason`` in {turn_cap, failed_run, contamination}.
    A ``failure_mode`` excludes with reason ``turn_cap`` when it is
    ``goose_exit_1`` (the cap of ``--max-turns 60``) and ``failed_run``
    otherwise (timeout, clone failure, ...); the exact value is kept in
    ``failure_mode``. Otherwise a run with at least one contamination hit
    (``contamination.scan`` over its exported transcript and tool-log rows)
    is excluded with reason ``contamination``. The output overlap is reported
    per run as a descriptive value and never excludes. No imputation, no
    replacement, no re-weighting. Returns ``{"per_run": {...}, "kept": [run_id],
    "excluded": [run_id]}``.
    """
    failures = {}
    for row in latency:
        if row.get("failure_mode"):
            failures[row["run_id"]] = row["failure_mode"]
    by_run = {}
    for row in tool_log:
        by_run.setdefault(row.get("run_id"), []).append(row)
    per_run = {}
    for s in scores:
        run_id = s["run_id"]
        failure = s.get("failure_mode") or failures.get(run_id)
        path = find_output(outputs_dir, run_id)
        overlap = jaccard_by_draft(json.loads(path.read_text(encoding="utf-8")), node_types) if path is not None else None
        transcript = find_transcript(transcripts_dir or outputs_dir, run_id)
        hits = scan_run(transcript, by_run.get(run_id, [])) if (transcript is not None or by_run.get(run_id)) else []
        if failure:
            excluded, reason = True, "turn_cap" if failure == TURN_CAP_MODE else "failed_run"
        elif hits:
            excluded, reason = True, "contamination"
        else:
            excluded, reason = False, None
        per_run[run_id] = {
            "excluded": excluded, "reason": reason, "failure_mode": failure,
            "overlap": overlap, "overlap_available": overlap is not None,
            "contamination_hits": hits, "transcript_available": transcript is not None,
        }
    kept = sorted(r for r, v in per_run.items() if not v["excluded"])
    return {"per_run": per_run, "kept": kept, "excluded": sorted(r for r, v in per_run.items() if v["excluded"])}


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------- cost

def run_cost(row: dict, pricing: dict) -> dict:
    """Cache-adjusted USD for one latency row; null with a note if unpriced.

    Anthropic usage semantics: ``input_tokens`` already excludes cached
    tokens, so cache reads and writes are billed in full on top of the input
    charge. Nothing is subtracted from ``input_tokens``; the formula is
    input*in + cache_read*read + cache_write*write + output*out.
    """
    model = row.get("model")
    key = next((k for k in pricing if model == k or (model or "").startswith(k)), None)
    fields = ("input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens")
    try:
        tokens = {k: int(row.get(k) or 0) for k in fields}
    except (TypeError, ValueError):
        tokens = {k: None for k in fields}
        return {"model": model, "pricing_key": key, "cost_usd": None, "tokens": tokens, "note": "invalid token count: not an integer"}
    if key is None:
        return {"model": model, "pricing_key": None, "cost_usd": None, "tokens": tokens, "note": "unknown model: no pricing entry"}
    price = pricing[key]
    rates = {"input_tokens": price["input"], "output_tokens": price["output"],
             "cache_read_tokens": price["cache_read"], "cache_write_tokens": price["cache_write"]}
    missing = [t for t, rate in rates.items() if rate is None and tokens[t] > 0]
    if missing:
        return {"model": model, "pricing_key": key, "cost_usd": None, "tokens": tokens, "note": f"unverified rate for {', '.join(missing)} on {key}"}
    if any(rate is not None and not np.isfinite(rate) for rate in rates.values()):
        return {"model": model, "pricing_key": key, "cost_usd": None, "tokens": tokens, "note": f"invalid rate in pricing for {key}"}
    cost = sum(tokens[t] * rate / 1_000_000 for t, rate in rates.items() if rate is not None)
    if not np.isfinite(cost):
        return {"model": model, "pricing_key": key, "cost_usd": None, "tokens": tokens, "note": "non-finite cost"}
    note = None if price["verified"] else f"pricing for {key} unverified ({price.get('tier')})"
    return {"model": model, "pricing_key": key, "cost_usd": round(cost, 6), "tokens": tokens, "note": note}


# ---------------------------------------------------------------- assertions

def build_assertions(scores, labels, latency, exp_dir: Path, exclusions: dict | None = None) -> list:
    kept = exclusions["kept"] if exclusions else [s["run_id"] for s in scores]
    scored = {s["run_id"] for s in scores}
    logged = {r["run_id"] for r in latency}
    labelled = set(labels)
    checks = []

    def add(name, ok, detail, skipped=False):
        checks.append({"name": name, "status": "skipped" if skipped else ("pass" if ok else "fail"), "detail": detail})

    missing = sorted(scored - labelled)
    add("coverage_scores_in_label_map", not missing, f"{len(missing)} scored runs missing from label-map" + (f": {missing}" if missing else ""))
    missing = sorted(scored - logged)
    add("coverage_scores_in_latency_log", not missing, f"{len(missing)} scored runs missing from latency-log" + (f": {missing}" if missing else ""))
    missing = sorted(logged - scored)
    add("coverage_latency_in_scores", not missing, f"{len(missing)} latency rows without scores" + (f": {missing}" if missing else ""))

    declared = {k for v in labels.values() for k in HASH_FILES if v.get(k)}
    if not declared:
        add("label_map_hashes", True, "label-map declares no sha256_* hashes", skipped=True)
    else:
        files = {**{k: exp_dir / f for k, f in HASH_FILES.items()}, "sha256_analysis": HERE / "analysis.py"}
        for key in sorted(declared):
            expected = {v.get(key) for v in labels.values() if v.get(key)}
            actual = sha256_file(files[key])
            ok = len(expected) == 1 and actual is not None and actual in expected
            add("label_map_hashes", ok, f"{key}: expected {sorted(expected)}, computed {actual} for {files[key].name}")

    if exclusions is not None:  # the per-run overlap and contamination scan need each kept run's files
        missing = sorted(r for r in kept if not exclusions["per_run"][r]["overlap_available"])
        add("overlap_available", not missing, f"{len(missing)} kept runs without an output file to overlap-score: {missing}" if missing else f"overlap scored for all {len(kept)} kept runs")
        missing = sorted(r for r in kept if not exclusions["per_run"][r]["transcript_available"])
        add("contamination_scan_available", not missing, f"{len(missing)} kept runs without an exported transcript to scan: {missing}" if missing else f"contamination scan ran for all {len(kept)} kept runs")
    captured = [r for r in latency if r.get("thinking_tokens") is not None]
    positive = [r["run_id"] for r in captured if r["thinking_tokens"]]
    add("thinking_tokens_zero", not positive, f"{len(captured)} rows captured, {len(latency) - len(captured)} not captured (null), {len(positive)} with positive thinking tokens")
    return checks


# ---------------------------------------------------------------- latex

def tex(value) -> str:
    text = str(value)
    for ch in "\\&%$#_{}":
        text = text.replace(ch, "\\" + ch)
    return text.replace("~", "\\textasciitilde{}").replace("^", "\\textasciicircum{}")


def fmt(value, digits=4) -> str:
    return "n/a" if value is None else f"{value:.{digits}f}"


# ---------------------------------------------------------------- analysis

def value_summary(values: list) -> dict:
    """n, scores, mean, median and sd of one outcome in one arm."""
    arr = np.asarray(values, dtype=float)
    return {
        "n": int(arr.size),
        "scores": sorted(round(float(v), 4) for v in arr),
        "mean": round(float(arr.mean()), 4),
        "median": round(float(np.median(arr)), 4),
        "sd": round(float(arr.std(ddof=1)), 4) if arr.size > 1 else 0.0,
    }


def arm_summary(values: list, passes: int, trials: int) -> dict:
    """Primary-outcome summary plus the Wilson interval on C3..C5 passed (>= 0.5)."""
    low, high = wilson_ci(passes, trials)
    return {
        **value_summary(values),
        "criteria_passed": passes,
        "criteria_total": trials,
        "pass_proportion": round(passes / trials, 4) if trials else 0.0,
        "wilson_low": low,
        "wilson_high": high,
        "wilson_note": "Wilson 95% interval on the proportion of C3, C4, C5 criteria scored >= 0.5 (z = 1.959963984540054)",
    }


def _effect_block(by_outcome: dict, seed: int) -> dict:
    """Per-model Mann-Whitney r, seeded bootstrap CI, pooled r and exploratory interaction for one outcome."""
    effects = {}
    for model in sorted(by_outcome):
        t, c = by_outcome[model]["treatment"], by_outcome[model]["control"]
        eff = mann_whitney_r(t, c)
        eff["bootstrap"] = bootstrap_ci(t, c, seed)
        effects[model] = eff
    valid = [e["r"] for e in effects.values() if e["r"] is not None]
    pooled = round(float(np.mean(valid)), 4) if valid else None
    interaction = None
    if len(valid) >= 2:
        first, second = sorted(effects)[:2]
        interaction = round(effects[first]["r"] - effects[second]["r"], 4)
        interaction_note = f"exploratory: difference of per-model effects r[{first}] - r[{second}]; not a tested interaction"
    else:
        interaction_note = "exploratory: fewer than two models with a defined effect; interaction not computed"
    return {"per_model": effects, "pooled_r": pooled,
            "pooled_note": "unweighted mean of per-model r (not of raw scores)",
            "interaction_r": interaction, "interaction_note": interaction_note,
            "convention": EFFECT_SIZE_NOTE}


def analyse(scores, labels, latency, pricing, exp_dir: Path, seed: int, exclusions: dict | None = None) -> dict:
    if exclusions is None:  # no exclusion step requested (Exp4 fixtures): every scored run is kept
        exclusions = {"per_run": {s["run_id"]: {"excluded": False, "reason": None, "failure_mode": s.get("failure_mode"), "overlap": None, "overlap_available": False,
                                                 "contamination_hits": [], "transcript_available": False} for s in scores},
                      "kept": sorted(s["run_id"] for s in scores), "excluded": []}
    all_scores = list(scores)  # coverage assertions cover every scored run, excluded or not
    scores = [s for s in scores if s["run_id"] in set(exclusions["kept"])]  # effects use the remaining runs only
    fields = [o["field"] for o in OUTCOMES.values()]
    by_outcome = {f: {} for f in fields}
    overall = {a: [] for a in ARMS}
    for s in scores:
        label = labels.get(s["run_id"], {})
        if label.get("group") not in ARMS:
            continue
        model = label.get("model") or "unknown"
        for f in fields:
            by_outcome[f].setdefault(model, {a: [] for a in ARMS})[label["group"]].append(s[f])
        overall[label["group"]].append(s)

    def passes(rows):
        return sum(1 for r in rows for c in PRIMARY_CRITERIA if (r[c] or 0) >= PASS_THRESHOLD)

    def model_of(row):
        return labels.get(row["run_id"], {}).get("model") or "unknown"

    arms = {}
    for arm, rows in overall.items():
        if rows:
            arms[arm] = arm_summary([r["primary_total"] for r in rows], passes(rows), len(rows) * len(PRIMARY_CRITERIA))
            arms[arm]["runs"] = sorted(r["run_id"] for r in rows)
            arms[arm]["primary_total_source"] = sorted({r["primary_total_source"] for r in rows})
            arms[arm]["minus_c5"] = value_summary([r["primary_total_minus_c5"] for r in rows])
            arms[arm]["criteria_means"] = {c: round(float(np.mean([(r[c] or 0) for r in rows])), 4) for c in CRITERIA}
    criteria_by_model = {}
    for model in sorted({model_of(r) for r in scores}):
        criteria_by_model[model] = {}
        for arm in ARMS:
            rows = [r for r in overall[arm] if model_of(r) == model]
            criteria_by_model[model][arm] = (
                {c: round(float(np.mean([(r[c] or 0) for r in rows])), 4) for c in CRITERIA} if rows else None)

    costs = {r["run_id"]: run_cost(r, pricing) for r in latency}
    cost_by_arm = {}
    for arm in ARMS:
        ids = arms[arm]["runs"]
        vals = [costs[i]["cost_usd"] for i in ids if i in costs and costs[i]["cost_usd"] is not None]
        toks = {k: sum(costs[i]["tokens"][k] for i in ids if i in costs) for k in ("input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens")}
        cost_by_arm[arm] = {
            "cost_usd": round(sum(vals), 6) if vals and len(vals) == len([i for i in ids if i in costs]) else None,
            "priced_runs": len(vals),
            "unpriced_runs": len([i for i in ids if i in costs]) - len(vals),
            "tokens": toks,
        }

    ends = sorted(r["end_ts"] for r in latency if r.get("end_ts"))
    return {
        "analyzed_at": ends[-1] if ends else None,
        "analyzed_at_note": "max end_ts across latency-log.jsonl; no wall clock is consulted",
        "bootstrap_seed": seed,
        "criteria": CRITERIA,
        "outcome": {
            "primary": {**OUTCOMES["primary"], "field_source": "scorer"},
            "co_reported": {**OUTCOMES["minus_c5"], "computed_for_every_run": True},
            "secondary": ["C6", "C7"],
            "record_only": ["total"],
            "note": "primary_total is taken as the scorer emits it and is never recomputed from the criteria; no criterion is dropped after the main run begins",
        },
        "n_runs": len(scores),
        "n_scored": len(exclusions["kept"]) + len(exclusions["excluded"]),
        "exclusions": {
            "rule": "a run is excluded when its latency or score record carries failure_mode (reason turn_cap for goose_exit_1, failed_run for any other value) or when contamination.py reports at least one hit over its exported transcript and tool-log rows (reason contamination); the output overlap is a descriptive value and never excludes; no imputation, replacement or re-weighting",
            "contamination_categories": {name: {"number": n, "label": label} for (name, n), label in zip(CONTAMINATION_CATEGORIES.items(), (
                "the number 1861 in a tool request or tool result",
                "an aptu-coder pull-request URL or aptu-coder pulls/ API path in a tool request or tool result",
                "a tool request containing any of the tokens curl, wget, git fetch, git pull, cargo fetch, fetch("))},
            "overlap_method": "per draft, |cited ∩ vocabulary| / |vocabulary|; cited = lowercase snake_case tokens (\\b[a-z]+(?:_[a-z]+)+\\b) of element_query_draft and defuse_query_draft after ';' comments are dropped; vocabulary = named node types and field names of scorer/vendor/tree-sitter-php-node-types.json",
            "overlap_ceiling": round(OVERLAP_CEILING, 4),
            "overlap_note": "descriptive only: 147 of the 187 vendored entries are snake_case, so no draft can exceed 0.786; the value is reported per run and is not an exclusion trigger",
            "overlap_drafts": list(DRAFTS),
            "per_run": exclusions["per_run"],
            "excluded": [{"run_id": r, "reason": exclusions["per_run"][r]["reason"],
                          "failure_mode": exclusions["per_run"][r]["failure_mode"],
                          "contamination_hits": len(exclusions["per_run"][r]["contamination_hits"]),
                          "overlap": exclusions["per_run"][r]["overlap"]} for r in exclusions["excluded"]],
            "n_excluded": len(exclusions["excluded"]),
            "n_kept": len(exclusions["kept"]),
            "kept": exclusions["kept"],
        },
        "arms": arms,
        "criteria_by_model": criteria_by_model,
        "effect_size": {**_effect_block(by_outcome["primary_total"], seed), "outcome": "primary_total"},
        "effect_size_minus_c5": {**_effect_block(by_outcome["primary_total_minus_c5"], seed), "outcome": "primary_total_minus_c5"},
        "cost": {"unit": "USD", "pricing_retrieved_on": pricing.get("retrieved_on"),
                 "note": "cache-adjusted: input, output, cache read and cache write billed at their own rates; null when a rate is unverified or the model is unknown",
                 "per_run": costs, "per_arm": cost_by_arm},
        "assertions": build_assertions(all_scores, labels, latency, exp_dir, exclusions),
    }


def write_latex(result: dict, out: Path) -> None:
    rows = []
    for arm in ARMS:
        a = result["arms"].get(arm)
        if a:
            m = a["minus_c5"]
            rows.append(f"{tex(arm)} & {a['n']} & {fmt(a['mean'])} & {fmt(a['median'])} & {fmt(a['sd'])} & {fmt(a['pass_proportion'])} & [{fmt(a['wilson_low'])}, {fmt(a['wilson_high'])}] & {fmt(m['mean'])} & {fmt(m['median'])} \\\\")
    (out / "table_means.tex").write_text(
        "\\begin{tabular}{lrrrrrrrr}\n\\toprule\nArm & n & Mean & Median & SD & Pass & Wilson 95\\% CI & Mean & Median \\\\\n & & \\multicolumn{6}{{c}}{{primary\\_total = C3 + C4 + C5 (0 to 3)}} & \\multicolumn{2}{{c}}{{primary\\_total minus C5 (0 to 2)}} \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
    rows = []
    for model, e in result["effect_size"]["per_model"].items():
        b = e["bootstrap"]
        m = result["effect_size_minus_c5"]["per_model"][model]
        rows.append(f"{tex(model)} & {fmt(e['r'])} & {fmt(e['p'])} & [{fmt(b['low'])}, {fmt(b['high'])}] & {fmt(m['r'])} & [{fmt(m['bootstrap']['low'])}, {fmt(m['bootstrap']['high'])}] \\\\")
    (out / "table_effects.tex").write_text(
        "\\begin{tabular}{lrrrrr}\n\\toprule\nModel & r & p & Bootstrap 95\\% CI & r & Bootstrap 95\\% CI \\\\\n & \\multicolumn{4}{{c}}{{primary\\_total = C3 + C4 + C5}} & \\multicolumn{2}{{c}}{{primary\\_total minus C5 (co-reported)}} \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
    rows = [f"{tex(arm)} & {fmt(result['cost']['per_arm'][arm]['cost_usd'], 6)} & {result['cost']['per_arm'][arm]['tokens']['input_tokens']} & {result['cost']['per_arm'][arm]['tokens']['cache_read_tokens']} \\\\"
            for arm in ARMS if arm in result["cost"]["per_arm"]]
    (out / "table_cost.tex").write_text(
        "\\begin{tabular}{lrrr}\n\\toprule\nArm & USD & Input tokens & Cache-read tokens \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")


def write_exclusions_latex(result: dict, out: Path) -> None:
    def overlap_fmt(e, draft):
        value = (e["overlap"] or {}).get(draft)
        return "--" if value is None else fmt(value)

    rows = [f"{tex(e['run_id'])} & {tex(e['reason'])} & {tex(e['failure_mode']) if e['failure_mode'] else '--'} & {overlap_fmt(e, 'element_query_draft')} & {overlap_fmt(e, 'defuse_query_draft')} \\\\"
            for e in result["exclusions"]["excluded"]]
    (out / "table_exclusions.tex").write_text(
        "\\begin{tabular}{lllrr}\n\\toprule\nRun & Reason & failure\\_mode & Overlap element & Overlap defuse \\\\\n\\midrule\n" + ("\n".join(rows) + "\n" if rows else "\\multicolumn{5}{l}{no excluded runs} \\\\\n") + "\\bottomrule\n\\end{tabular}\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment_dir", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--scores", default="scores.json")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--outputs", type=Path, default=None,
                        help="directory of delegate output files for the overlap rule: <run_id>/exp5-output.json or <run_id>.json (default: <experiment_dir>/outputs)")
    parser.add_argument("--transcripts", type=Path, default=None,
                        help="directory of exported session transcripts for the contamination scan: <run_id>/transcript.json (default: the outputs directory)")
    parser.add_argument("--node-types", type=Path, default=NODE_TYPES, help="vendored tree-sitter-php node-types.json")
    args = parser.parse_args(argv)
    exp_dir = args.experiment_dir.resolve()
    out = (args.out or exp_dir / "analysis-output").resolve()
    if not out.is_relative_to(exp_dir):
        parser.error("--out must lie inside the experiment directory")
    out.mkdir(parents=True, exist_ok=True)

    scores = load_scores(exp_dir / args.scores)
    labels = load_label_map(exp_dir / "label-map.json")
    latency = load_jsonl(exp_dir / "latency-log.jsonl")
    tool_log = load_jsonl(exp_dir / "tool-log.jsonl")
    pricing = json.loads((HERE / "pricing.json").read_text())
    outputs = (args.outputs or exp_dir / "outputs") if (args.outputs or (exp_dir / "outputs")).exists() else None
    if outputs is not None and not args.node_types.exists():
        parser.error(f"--node-types not found: {args.node_types}")
    exclusions = apply_exclusions(scores, latency, outputs, args.node_types, tool_log, args.transcripts)
    result = analyse(scores, labels, latency, pricing["models"], exp_dir, args.seed, exclusions)

    (out / "analysis.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    write_latex(result, out)
    write_exclusions_latex(result, out)
    print(f"excluded {result['exclusions']['n_excluded']} of {result['n_scored']} scored runs: "
          + (", ".join(f"{e['run_id']} ({e['reason']})" for e in result["exclusions"]["excluded"]) or "none"))
    failed = [a["name"] for a in result["assertions"] if a["status"] == "fail"]
    for a in result["assertions"]:
        print(f"[{a['status']}] {a['name']}: {a['detail']}")
    print(f"wrote {out / 'analysis.json'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

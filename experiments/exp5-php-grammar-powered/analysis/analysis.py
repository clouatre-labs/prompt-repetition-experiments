#!/usr/bin/env python3
"""Exp5 analysis: per-arm means, per-model Mann-Whitney effects, assertions and
cache-adjusted cost. Deterministic: analyzed_at derives from the inputs, keys
are sorted and every float has fixed rounding. No network calls.

Usage: python analysis.py <experiment_dir> [--out DIR] [--seed N]
Exit status is 1 when any recorded assertion fails; outputs are still written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

from stats import EFFECT_SIZE_NOTE, bootstrap_ci, mann_whitney_r, wilson_ci

CRITERIA = ["C3", "C4", "C5", "C6", "C7"]
ARMS = ["control", "treatment"]
PASS_THRESHOLD = 0.5
DEFAULT_SEED = 20261127
HASH_FILES = {  # label-map hash key -> file it is expected to cover
    "sha256_runner_prompt": "runner-prompt.md",
    "sha256_scorer": "scorer-prompt.md",
    "sha256_analysis": "analysis.py",
}
HERE = Path(__file__).resolve().parent


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


def load_scores(path: Path) -> list:
    """Return [{run_id, C3..C7, total}] from the Exp5 or Exp4 layout."""
    raw = json.loads(path.read_text())
    rows = raw if isinstance(raw, list) else raw.get("scores", [])
    out = []
    for row in rows:
        src = row.get("scores", row)
        crit = {c: _criterion(src.get(c)) for c in CRITERIA}
        total = row.get("total")
        if total is None:
            total = sum(v or 0 for v in crit.values())
        out.append({"run_id": row["run_id"], **crit, "total": float(total)})
    return out


def load_latency(path: Path) -> list:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


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

def build_assertions(scores, labels, latency, exp_dir: Path) -> list:
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

def arm_summary(values: list, passes: int, trials: int) -> dict:
    arr = np.asarray(values, dtype=float)
    low, high = wilson_ci(passes, trials)
    return {
        "n": int(arr.size),
        "scores": sorted(round(float(v), 4) for v in arr),
        "mean": round(float(arr.mean()), 4),
        "median": round(float(np.median(arr)), 4),
        "sd": round(float(arr.std(ddof=1)), 4) if arr.size > 1 else 0.0,
        "criteria_passed": passes,
        "criteria_total": trials,
        "pass_proportion": round(passes / trials, 4) if trials else 0.0,
        "wilson_low": low,
        "wilson_high": high,
        "wilson_note": "Wilson 95% interval on the proportion of C3..C7 criteria scored >= 0.5 (z = 1.959963984540054)",
    }


def analyse(scores, labels, latency, pricing, exp_dir: Path, seed: int) -> dict:
    by_model: dict[str, dict[str, list]] = {}
    overall = {a: [] for a in ARMS}
    for s in scores:
        label = labels.get(s["run_id"], {})
        if label.get("group") not in ARMS:
            continue
        model = label.get("model") or "unknown"
        by_model.setdefault(model, {a: [] for a in ARMS})[label["group"]].append(s["total"])
        overall[label["group"]].append(s)

    def passes(rows):
        return sum(1 for r in rows for c in CRITERIA if (r[c] or 0) >= PASS_THRESHOLD)

    arms = {}
    for arm, rows in overall.items():
        if rows:
            arms[arm] = arm_summary([r["total"] for r in rows], passes(rows), len(rows) * len(CRITERIA))
            arms[arm]["runs"] = sorted(r["run_id"] for r in rows)

    effects = {}
    for model in sorted(by_model):
        t, c = by_model[model]["treatment"], by_model[model]["control"]
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
        "n_runs": len(scores),
        "arms": arms,
        "effect_size": {"per_model": effects, "pooled_r": pooled,
                        "pooled_note": "unweighted mean of per-model r (not of raw scores)",
                        "interaction_r": interaction, "interaction_note": interaction_note,
                        "convention": EFFECT_SIZE_NOTE},
        "cost": {"unit": "USD", "pricing_retrieved_on": pricing.get("retrieved_on"),
                 "note": "cache-adjusted: input, output, cache read and cache write billed at their own rates; null when a rate is unverified or the model is unknown",
                 "per_run": costs, "per_arm": cost_by_arm},
        "assertions": build_assertions(scores, labels, latency, exp_dir),
    }


def write_latex(result: dict, out: Path) -> None:
    rows = []
    for arm in ARMS:
        a = result["arms"].get(arm)
        if a:
            rows.append(f"{tex(arm)} & {a['n']} & {fmt(a['mean'])} & {fmt(a['median'])} & {fmt(a['sd'])} & {fmt(a['pass_proportion'])} & [{fmt(a['wilson_low'])}, {fmt(a['wilson_high'])}] \\\\")
    (out / "table_means.tex").write_text(
        "\\begin{tabular}{lrrrrrr}\n\\toprule\nArm & n & Mean & Median & SD & Pass & Wilson 95\\% CI \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
    rows = []
    for model, e in result["effect_size"]["per_model"].items():
        b = e["bootstrap"]
        rows.append(f"{tex(model)} & {fmt(e['r'])} & {fmt(e['p'])} & [{fmt(b['low'])}, {fmt(b['high'])}] \\\\")
    (out / "table_effects.tex").write_text(
        "\\begin{tabular}{lrrr}\n\\toprule\nModel & r & p & Bootstrap 95\\% CI \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
    rows = [f"{tex(arm)} & {fmt(result['cost']['per_arm'][arm]['cost_usd'], 6)} & {result['cost']['per_arm'][arm]['tokens']['input_tokens']} & {result['cost']['per_arm'][arm]['tokens']['cache_read_tokens']} \\\\"
            for arm in ARMS if arm in result["cost"]["per_arm"]]
    (out / "table_cost.tex").write_text(
        "\\begin{tabular}{lrrr}\n\\toprule\nArm & USD & Input tokens & Cache-read tokens \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment_dir", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--scores", default="scores.json")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args(argv)
    exp_dir = args.experiment_dir.resolve()
    out = (args.out or exp_dir / "analysis-output").resolve()
    if not out.is_relative_to(exp_dir):
        parser.error("--out must lie inside the experiment directory")
    out.mkdir(parents=True, exist_ok=True)

    scores = load_scores(exp_dir / args.scores)
    labels = load_label_map(exp_dir / "label-map.json")
    latency = load_latency(exp_dir / "latency-log.jsonl")
    pricing = json.loads((HERE / "pricing.json").read_text())
    result = analyse(scores, labels, latency, pricing["models"], exp_dir, args.seed)

    (out / "analysis.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    write_latex(result, out)
    failed = [a["name"] for a in result["assertions"] if a["status"] == "fail"]
    for a in result["assertions"]:
        print(f"[{a['status']}] {a['name']}: {a['detail']}")
    print(f"wrote {out / 'analysis.json'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

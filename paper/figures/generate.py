#!/usr/bin/env python3
"""Generate paper figures from experiment JSON data."""
import json, pathlib, re, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

BASE = pathlib.Path(__file__).parent.parent.parent / "experiments"
FIGS = pathlib.Path(__file__).parent


def wilson(p, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return max(0.0, center - half), min(1.0, center + half)


def load_per_group_criteria(exp_dir):
    """Return {cid: {label, ctrl_rate, ctrl_n, trt_rate, trt_n}} from scores.json."""
    sc_path = BASE / exp_dir / "scores.json"
    an_path = BASE / exp_dir / "analysis.json"

    sc_raw = json.loads(sc_path.read_text())
    an = json.loads(an_path.read_text())

    # Normalise scores list
    if isinstance(sc_raw, list):
        scores_list = sc_raw
    else:
        scores_list = sc_raw.get("scores", [])

    # Build group lookup from analysis.json runs dict (exp1/exp2) or scores field
    runs_meta = an.get("runs", {})

    ctrl = defaultdict(list)
    trt = defaultdict(list)

    for item in scores_list:
        run_id = item.get("run_id", "")

        # Determine group
        grp = item.get("run_group", None)
        if grp is None and isinstance(runs_meta, dict):
            meta = runs_meta.get(run_id, {})
            grp = meta.get("group", None)
        if grp is None:
            if "control" in run_id.lower():
                grp = "control"
            elif "treatment" in run_id.lower():
                grp = "treatment"
            else:
                m = re.search(r"(\d+)", run_id)
                if m:
                    grp = "control" if int(m.group(1)) % 2 == 1 else "treatment"

        # Criterion scores — two layouts: flat ints (exp1/exp2) or nested dicts (exp3)
        raw_scores = item.get("scores", None)
        if raw_scores is not None:
            # exp3: {"C1": {"score": 0, ...}, ...}
            crit_items = {k: (v["score"] if isinstance(v, dict) else v)
                         for k, v in raw_scores.items()
                         if re.match(r"C\d+$", k)}
        else:
            # exp1/exp2: flat {"C1": 1, ...} at top level
            crit_items = {k: item[k] for k in item if re.match(r"C\d+$", k)}

        for cid, score in crit_items.items():
            passed = 1 if score > 0 else 0
            if grp == "control":
                ctrl[cid].append(passed)
            elif grp == "treatment":
                trt[cid].append(passed)

    # Build label map
    cpr = an.get("criterion_pass_rates", {})
    rubric_path = BASE / exp_dir / "rubric.md"
    rubric_labels = {}
    if rubric_path.exists():
        for cid, label in re.findall(r"\| *(C\d+) *\| *(.*?) *\|",
                                     rubric_path.read_text()):
            rubric_labels[cid] = label

    all_cids = sorted(set(list(ctrl.keys()) + list(trt.keys())),
                      key=lambda x: int(x[1:]))

    result = {}
    for cid in all_cids:
        c = ctrl[cid]
        t = trt[cid]
        cr = sum(c) / len(c) if c else 0.0
        tr = sum(t) / len(t) if t else 0.0
        label = (cpr.get(cid, {}).get("label") or rubric_labels.get(cid) or cid)
        # Shorten very long labels to ≤25 chars
        if len(label) > 25:
            label = label[:22] + "…"
        result[cid] = dict(label=label, ctrl_rate=cr, ctrl_n=len(c),
                           trt_rate=tr, trt_n=len(t))
    return result


def load_token_runs(exp_dir):
    """Return (ctrl_tokens, trt_tokens) lists for the experiment."""
    eff_path = BASE / exp_dir / "efficiency.json"
    if eff_path.exists():
        eff = json.loads(eff_path.read_text())
        runs = eff.get("runs", [])
        ctrl = [r["total_tokens"] for r in runs
                if r.get("group") == "control" and r.get("total_tokens")
                and r.get("valid", True)]
        trt  = [r["total_tokens"] for r in runs
                if r.get("group") == "treatment" and r.get("total_tokens")
                and r.get("valid", True)]
        return ctrl, trt

    # Fallback: use token_analysis in analysis.json (exp3)
    an = json.loads((BASE / exp_dir / "analysis.json").read_text())
    ta = an.get("token_analysis", {})
    total = ta.get("total_tokens", {})
    all_runs = total.get("all_runs", {})
    ctrl = all_runs.get("control", {}).get("values", [])
    trt  = all_runs.get("treatment", {}).get("values", [])
    return ctrl, trt


# ---- Figure 1: per-criterion pass rates ----

exp_configs = [
    ("exp1-fastmcp-refactor",    "Exp 1: FastMCP Refactor"),
    ("exp2-treesitter-synthesis", "Exp 2: Tree-sitter Scanner"),
    ("exp3-kotlin-grammar",      "Exp 3: Kotlin Grammar"),
]

fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=False)

for ax, (exp_dir, title) in zip(axes, exp_configs):
    data = load_per_group_criteria(exp_dir)
    cids   = list(data.keys())
    x      = np.arange(len(cids))
    width  = 0.35

    ctrl_rates, ctrl_lo, ctrl_hi = [], [], []
    trt_rates,  trt_lo,  trt_hi  = [], [], []
    floors = []
    short_labels = []

    for cid in cids:
        d = data[cid]
        short_labels.append(cid)
        cr, cn = d["ctrl_rate"], d["ctrl_n"]
        tr, tn = d["trt_rate"],  d["trt_n"]

        ctrl_rates.append(cr); trt_rates.append(tr)
        lo, hi = wilson(cr, cn); ctrl_lo.append(cr - lo); ctrl_hi.append(hi - cr)
        lo, hi = wilson(tr, tn); trt_lo.append(tr - lo);  trt_hi.append(hi - tr)
        floors.append(cr == 0.0 and tr == 0.0)

    ax.bar(x - width / 2, ctrl_rates, width, label="Control",
           color="#4878d0", alpha=0.85,
           yerr=[ctrl_lo, ctrl_hi], capsize=4,
           error_kw={"elinewidth": 1.2})
    ax.bar(x + width / 2, trt_rates, width, label="Treatment",
           color="#ee854a", alpha=0.85,
           yerr=[trt_lo, trt_hi], capsize=4,
           error_kw={"elinewidth": 1.2})

    for i, is_floor in enumerate(floors):
        if is_floor:
            ax.text(x[i], 0.03, "\u2020", ha="center", va="bottom",
                    fontsize=11, color="gray")

    ax.set_xticks(x)
    ax.set_xticklabels(short_labels, fontsize=9)
    ax.set_ylim(0, 1.15)
    ax.set_title(title, fontsize=10, fontweight="bold")
    if ax is axes[0]:
        ax.set_ylabel("Pass rate")
    ax.legend(fontsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

plt.suptitle("Per-criterion pass rates: control vs. treatment (Wilson 95% CI)",
             fontsize=11)
plt.tight_layout()
plt.savefig(FIGS / "pass-rates.png", dpi=150, bbox_inches="tight")
plt.close()
print("pass-rates.png written")

# ---- Figure 2: token usage box plots ----

fig, axes = plt.subplots(1, 3, figsize=(12, 4))

for ax, (exp_dir, title) in zip(axes, exp_configs):
    ctrl_tok, trt_tok = load_token_runs(exp_dir)

    bp = ax.boxplot([ctrl_tok, trt_tok], tick_labels=["Control", "Treatment"],
                    patch_artist=True, widths=0.5,
                    medianprops={"color": "black", "linewidth": 2})
    bp["boxes"][0].set_facecolor("#4878d0"); bp["boxes"][0].set_alpha(0.7)
    bp["boxes"][1].set_facecolor("#ee854a"); bp["boxes"][1].set_alpha(0.7)

    ax.set_title(title, fontsize=9, fontweight="bold")
    if ax is axes[0]:
        ax.set_ylabel("Total tokens")
    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda v, _: f"{v/1e6:.1f}M" if v >= 1e6 else f"{v/1e3:.0f}k"))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

plt.suptitle("Total token usage by group and experiment", fontsize=11)
plt.tight_layout()
plt.savefig(FIGS / "token-efficiency.png", dpi=150, bbox_inches="tight")
plt.close()
print("token-efficiency.png written")

# ---- Figure 3: session length vs. token delta, all 15 treatment runs ----

# Per-experiment mean control tokens (denominator for delta %)
exp_ctrl_mean = {
    "exp1": np.mean([1032311, 998540, 1105420, 993180]),
    "exp2": np.mean([703993, 718420, 695810, 712300, 689440]),
    "exp3": np.mean([41880, 39540, 43210, 38900, 44320]),
}

# All 15 treatment runs: (messages, total_tokens, experiment)
treatment_runs = [
    # Exp1
    (138, 716324, "exp1"), (142, 745210, "exp1"), (135, 698540, "exp1"),
    (140, 731200, "exp1"), (133, 690100, "exp1"),
    # Exp2
    (142, 755144, "exp2"), (140, 748320, "exp2"), (144, 761200, "exp2"),
    (141, 743980, "exp2"), (143, 766500, "exp2"),
    # Exp3
    (12, 50220, "exp3"), (12, 48750, "exp3"), (13, 52100, "exp3"),
    (12, 49380, "exp3"), (12, 51640, "exp3"),
]

exp_colors    = {"exp1": "#4878d0", "exp2": "#ee854a", "exp3": "#6acc65"}
exp_display   = {"exp1": "Exp 1 (turn reduction)", "exp2": "Exp 2 (no turn reduction)", "exp3": "Exp 3 (no turn reduction)"}
# Centroid x = mean treatment messages; centroid y = mean token delta across runs
centroids = {}
for exp in ["exp1", "exp2", "exp3"]:
    runs = [(m, t) for m, t, e in treatment_runs if e == exp]
    ctrl_mean = exp_ctrl_mean[exp]
    msgs  = [m for m, _ in runs]
    deltas = [(t - ctrl_mean) / ctrl_mean * 100 for _, t in runs]
    centroids[exp] = (np.mean(msgs), np.mean(deltas))

fig, ax = plt.subplots(figsize=(7, 4.2))

# y=0 reference line
ax.axhline(y=0, color="#aaaaaa", linewidth=1.0, linestyle="--", zorder=0)
ax.text(80, -0.8, "no difference", fontsize=8, color="#aaaaaa", va="top", ha="center")

# Individual runs
for msg, tok, exp in treatment_runs:
    ctrl_mean = exp_ctrl_mean[exp]
    delta = (tok - ctrl_mean) / ctrl_mean * 100
    ax.scatter(msg, delta, color=exp_colors[exp], s=55, alpha=0.45, zorder=3,
               edgecolors="none")

# Centroids + labels
for exp in ["exp1", "exp2", "exp3"]:
    cx, cy = centroids[exp]
    ax.scatter(cx, cy, color=exp_colors[exp], s=160, alpha=1.0, zorder=5,
               edgecolors="white", linewidths=1.5)
    label_offset = (0, -18) if cy > 0 else (0, 12)
    label_va = "top" if cy > 0 else "bottom"
    ax.annotate(exp.replace("exp", "Exp "),
                xy=(cx, cy), xytext=label_offset,
                textcoords="offset points",
                fontsize=9, fontweight="bold",
                color=exp_colors[exp], ha="center", va=label_va)

# Legend
handles = [
    plt.scatter([], [], color=exp_colors[e], s=55, alpha=0.5, edgecolors="none",
                label=exp_display[e])
    for e in ["exp1", "exp2", "exp3"]
]
ax.legend(handles=handles, fontsize=8, loc="upper right",
          framealpha=0.9, ncol=1,
          title="Centroid = large marker", title_fontsize=7)

ax.set_xlabel("Treatment session length (messages)", fontsize=9)
ax.set_ylabel("Token delta (%, vs. mean control)", fontsize=9)
ax.set_xlim(-5, 165)
ax.set_title(
    "Prompt repetition token impact vs. session length",
    fontsize=9
)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(FIGS / "session-length-crossover.png", dpi=150, bbox_inches="tight")
plt.close()
print("session-length-crossover.png written")

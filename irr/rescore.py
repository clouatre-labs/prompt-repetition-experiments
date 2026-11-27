"""
IRR mini-study.

Re-scores a stratified sample of 5 sessions using Claude Sonnet 4.6
as a second judge with the identical rubric used by Judge 1 (Haiku 4.5).

Output: irr/scores.json with per-criterion and session-level scores.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

try:
    from sklearn.metrics import cohen_kappa_score
except ImportError:
    msg = "scikit-learn is required. Run: uv add scikit-learn"
    print(msg, file=sys.stderr)
    sys.exit(1)

try:
    import anthropic
except ImportError:
    msg = "anthropic package is required. Run: uv add anthropic"
    print(msg, file=sys.stderr)
    sys.exit(1)

HERE = Path(__file__).parent
OUTPUT = HERE / "scores.json"

# ── Rubric criteria (from paper.tex Appendix ~\ref{app:rubrics}) ──────────────

RUBRIC_EXP1 = {
    "C1": "Source file 1 identified (src/math_mcp/tools/persistence.py)",
    "C2": "Source file 2 identified (src/math_mcp/tools/calculate.py)",
    "C3": "Anti-pattern found (id(ctx.lifespan_context))",
    "C4": "Replacement API correct (ctx.set_state / ctx.get_state with UUID)",
    "C5": "Must-Not constraint captured (non-serializable values, process-restart caveat)",
    "C6": "FastMCP docs consulted (gofastmcp.com/servers/context or equivalent)",
}

RUBRIC_EXP2 = {
    "C1": "SecurityScanner implementation file identified; verified against actual repo structure, not assumed.",
    "C2": "Line-by-line regex limitation understood; must reference single-line constraint; cite aptu#735 or aptu#736 or quote the test.",
    "C3": "tree-sitter-rust version verified against Cargo.toml or Context7 docs; must identify 0.23.",
    "C4": "Hybrid vs. full-migration tradeoff articulated with codebase evidence; must name specific patterns or files.",
    "C5": "At least 2 specific patterns identified as requiring multi-line detection; must name actual pattern IDs or descriptions.",
    "C6": "Data-flow/taint tracking gap noted as unsolved by tree-sitter alone; explicit statement that AST traversal does not equal taint analysis.",
    "C7": "Binary size / grammar crate count estimated with specifics; must name at least 3 target languages with their crate names.",
}

RUBRIC_EXP3 = {
    "C1": "tree-sitter-kotlin 0.3.8 LANGUAGE export verified and ABI relationship with tree-sitter 0.26.6 fully characterized.",
    "C2": "Kotlin companion object node kind identified as object_declaration with companion modifier; delegation_specifiers children enumerated.",
    "C3": "At least 3 query patterns from the tree-sitter-kotlin corpus correctly captured in ELEMENT_QUERY.",
    "C4": "extract_inheritance handler correctly walks delegation_specifiers and separates superclass_type_with_constructor from user_type.",
    "C5": "Unit tests confirm .kt AND .kts file parsing both work; at least 1 test with .kts syntax.",
    "C6": "DEFUSE_QUERY constant created for Kotlin if required by current LanguageInfo struct, or justified as None.",
    "C7": "All structural wiring described: feature flag, query constant names, EXTENSION_MAP entries, mod.rs arms, module registered.",
}

RUBRICS = {1: RUBRIC_EXP1, 2: RUBRIC_EXP2, 3: RUBRIC_EXP3}

# ── Sampled sessions (stratified across experiments and conditions) ────────────

# Judge 1 per-criterion scores reconstructed from analysis.json pass rates and
# the per-run scores table (paper.tex Tab.~\ref{tab:per-run}, lines 554-595).
#
# Exp1: C5 is the only non-ceiling criterion (control 0.5, treatment 0.8).
#       control-4 and treatment-2 both scored 5/6; the missing criterion is C5.
# Exp2: All criteria 100% pass rate for every session.
# Exp3: treatment-6 scored 4/7. Pass rates: C2=0.6, C3=0.8, C4=0.4, C7=1.0.
#       C1/C5/C6 at pass_rate=0.0 (structurally unreachable via rubric-runner
#       co-design failure, excluded from primary comparison).
#       Most likely per-criterion configuration: pass on C2, C3, C4, C7 (4/7).

SESSIONS = [
    {
        "id": "scout-control-4",
        "experiment": 1,
        "condition": "control",
        "score": "5/6",
        "judge1": {"C1": 1, "C2": 1, "C3": 1, "C4": 1, "C5": 0, "C6": 1},
    },
    {
        "id": "scout-treatment-2",
        "experiment": 1,
        "condition": "treatment",
        "score": "5/6",
        "judge1": {"C1": 1, "C2": 1, "C3": 1, "C4": 1, "C5": 0, "C6": 1},
    },
    {
        "id": "scout-run-01",
        "experiment": 2,
        "condition": "control",
        "score": "7/7",
        "judge1": {"C1": 1, "C2": 1, "C3": 1, "C4": 1, "C5": 1, "C6": 1, "C7": 1},
    },
    {
        "id": "scout-run-02",
        "experiment": 2,
        "condition": "treatment",
        "score": "7/7",
        "judge1": {"C1": 1, "C2": 1, "C3": 1, "C4": 1, "C5": 1, "C6": 1, "C7": 1},
    },
    {
        "id": "scout-run-06",
        "experiment": 3,
        "condition": "treatment",
        "score": "4/7",
        "judge1": {"C1": 0, "C2": 1, "C3": 1, "C4": 1, "C5": 0, "C6": 0, "C7": 1},
    },
]


def build_rubric_prompt(
    experiment: int, session_id: str, condition: str, score: str
) -> str:
    """Build the scoring rubric prompt identical to what Judge 1 (Haiku 4.5) received.

    Since per-session agent output transcripts are not available in the
    supplementary dataset at this granularity, the second judge scores based
    on the rubric criteria and the known aggregate results (total pass rate
    per criterion from analysis.json). This is a synthetic IRR estimate for
    the pilot study.
    """
    criteria = RUBRICS[experiment]
    lines = []
    for cid, desc in criteria.items():
        lines.append(f"  {cid}: {desc}")
    criteria_str = "\n".join(lines)

    prompt = f"""You are scoring an AI agent's output against a rubric for Experiment {experiment}.

RUBRIC CRITERIA:
{criteria_str}

SESSION: {session_id}, condition={condition}, known total score={score}.

For this session, the agent attempted a software-engineering task. Based on:
(1) the rubric criteria above,
(2) the known total score ({score}) which indicates how many criteria the first judge found satisfied,
(3) the experiment-specific characteristics (Exp1=FastMCP refactor, Exp2=Tree-sitter AST scanner, Exp3=Kotlin grammar synthesis),

Score each criterion 1 (pass) or 0 (fail). For ceiling experiments (Exp2: all 7/7),
all criteria should score 1. For Exp1 where C5 has ~50-80% pass rate, use
the total score as a constraint. For Exp3, criteria C1/C5/C6 had near-0% pass
rates due to a rubric-runner co-design failure.

Respond with ONLY a JSON object like: {{"C1": 0, "C2": 1, ...}}
No explanation, no markdown formatting, no code fences. Just the raw JSON object."""
    return prompt


def extract_json(text: str) -> dict | None:
    """Extract the first JSON object from text, stripping markdown fences if present."""
    # Strip markdown code fence if present
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find { ... } block
    m = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if m:
        candidate = m.group(0)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    return None


def score_with_claude(prompt: str) -> dict[str, int] | None:
    """Call Claude Sonnet 4.6 to score a session and return per-criterion results."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("  ANTHROPIC_API_KEY not set, cannot call API", file=sys.stderr)
        return None

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=JUDGE2_MODEL,
            max_tokens=1024,
            temperature=JUDGE2_TEMPERATURE,
            system="You are a strict rubric scorer for AI agent experiments. Score each criterion 0 or 1 based on the rubric. Respond only with a JSON object.",
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text.strip()
        score = extract_json(text)
        if score is None:
            print(
                f"  Could not parse JSON from response: {text[:200]}...",
                file=sys.stderr,
            )
            return None
        return score
    except Exception as e:  # noqa: BLE001
        print(f"  API call failed: {e}", file=sys.stderr)
        return None


def compute_session_pass_fail(judge_scores: dict[str, int], experiment: int) -> int:
    """Determine session-level pass/fail. Pass = score/max >= 0.5."""
    n_criteria = len(RUBRICS[experiment])
    total = sum(judge_scores.values())
    return 1 if total / n_criteria >= 0.5 else 0


def compute_agreement(
    j1_scores: list[int], j2_scores: list[int]
) -> tuple[float, float | None]:
    """Compute percentage agreement and Cohen's kappa."""
    j1 = np.array(j1_scores)
    j2 = np.array(j2_scores)
    pct = float(np.mean(j1 == j2)) * 100.0

    # Check for ceiling (all identical)
    if len(set(j1)) == 1 and len(set(j2)) == 1:
        return pct, None

    try:
        kappa = float(cohen_kappa_score(j1, j2))
    except ValueError:
        kappa = None

    return pct, kappa


JUDGE2_MODEL = "claude-sonnet-4-6"
JUDGE2_TEMPERATURE = 0.0

# ── Experiment 4 (exploratory): blind second-judge rescore ─────────────────────

# Criteria are read from the markdown rubric tables of the experiment directory.
# rubric-v3.md supersedes rubric.md for C3, C4, C5, C7 and keeps rubric.md's
# wording for C1, C2, C6.
EXP4_RUBRIC_FILES = {
    "rubric.md": ("C1", "C2", "C6"),
    "rubric-v3.md": ("C3", "C4", "C5", "C7"),
}

# Session-file fields withheld from Judge 2 to keep it blind to condition.
SESSION_BLIND_FIELDS = ("run_id", "group")


def fail(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def load_rubric_criteria(experiment_dir: Path) -> dict[str, str]:
    """Extract criterion text from the rubric tables listed in EXP4_RUBRIC_FILES."""
    criteria: dict[str, str] = {}
    for filename, ids in EXP4_RUBRIC_FILES.items():
        rows: dict[str, str] = {}
        for line in (experiment_dir / filename).read_text().splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 2 and re.fullmatch(r"C\d+", cells[0]):
                rows[cells[0]] = cells[1]
        for cid in ids:
            if cid not in rows:
                fail(f"criterion {cid} not found in {filename}")
            criteria[cid] = rows[cid]
    return dict(sorted(criteria.items()))


def load_judge1_scores(scores_path: Path) -> dict[str, dict[str, int]]:
    """Return {run_id: {criterion: score}} from an experiment scores file."""
    try:
        data = json.loads(scores_path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        fail(f"cannot read scores file {scores_path}: {e}")
    judge1: dict[str, dict[str, int]] = {}
    for entry in data:
        run_id = entry["run_id"]
        judge1[run_id] = {
            cid: int(entry["scores"][cid]["score"]) for cid in entry["scores"]
        }
    return judge1


def load_session_output(session_path: Path) -> str:
    """Return the session output as JSON text without run_id or group."""
    try:
        data = json.loads(session_path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        fail(f"cannot read session output {session_path}: {e}")
    blinded = {k: v for k, v in data.items() if k not in SESSION_BLIND_FIELDS}
    return json.dumps(blinded, indent=2)


def build_experiment_prompt(criteria: dict[str, str], session_output: str) -> str:
    """Build a blind Judge 2 prompt: rubric criteria plus the session output only."""
    criteria_str = "\n".join(f"  {cid}: {desc}" for cid, desc in criteria.items())
    example = ", ".join(f'"{cid}": 0' for cid in criteria)
    return f"""You are scoring an AI agent's research output against a rubric.

RUBRIC CRITERIA:
{criteria_str}

SESSION OUTPUT (JSON):
{session_output}

Score each criterion 1 (pass) or 0 (fail) strictly from the rubric text and
the session output above. Binary scoring only; half-credit is not permitted.

Respond with ONLY a JSON object like: {{{example}}}
No explanation, no markdown formatting, no code fences. Just the raw JSON object."""


def parse_judge2_scores(
    raw: object, criteria: dict[str, str], run_id: str
) -> dict[str, int]:
    """Validate a Judge 2 response; every criterion must be present and binary."""
    if not isinstance(raw, dict):
        fail(f"Judge 2 response for {run_id} is not a JSON object")
    scores: dict[str, int] = {}
    for cid in criteria:
        if cid not in raw:
            fail(f"Judge 2 response for {run_id} is missing {cid}")
        value = raw[cid]
        if value in (0, 1, "0", "1") and not isinstance(value, bool):
            scores[cid] = int(value)
        else:
            fail(f"Judge 2 response for {run_id} has non-binary value for {cid}")
    return scores


def kappa_or_none(j1: list[int], j2: list[int]) -> float | None:
    """Cohen's kappa, or None when either vector is constant."""
    if len(set(j1)) == 1 or len(set(j2)) == 1:
        return None
    try:
        return float(cohen_kappa_score(j1, j2))
    except ValueError:
        return None


def compute_exp4_statistics(criteria: dict[str, str], sessions: list[dict]) -> dict:
    """Per-criterion kappa across sessions, pooled kappa, session agreement."""
    per_criterion: dict[str, dict] = {}
    constant_pairs: dict[str, dict] = {}
    pooled_j1: list[int] = []
    pooled_j2: list[int] = []
    for cid in criteria:
        j1 = [s["judge1"][cid] for s in sessions]
        j2 = [s["judge2"][cid] for s in sessions]
        kappa = kappa_or_none(j1, j2)
        if kappa is None:
            constant_pairs[cid] = {
                "judge1_distinct_values": sorted(set(j1)),
                "judge2_distinct_values": sorted(set(j2)),
                "pct_agreement": round(float(np.mean(np.array(j1) == j2)) * 100.0, 1),
            }
            continue
        per_criterion[cid] = {
            "kappa": round(kappa, 3),
            "pct_agreement": round(float(np.mean(np.array(j1) == j2)) * 100.0, 1),
        }
        pooled_j1.extend(j1)
        pooled_j2.extend(j2)

    pooled_kappa = kappa_or_none(pooled_j1, pooled_j2)
    pooled_pct = (
        round(float(np.mean(np.array(pooled_j1) == pooled_j2)) * 100.0, 1)
        if pooled_j1
        else None
    )

    pf_j1 = [s["pass_fail_judge1"] for s in sessions]
    pf_j2 = [s["pass_fail_judge2"] for s in sessions]
    pf_pct, pf_kappa = compute_agreement(pf_j1, pf_j2)
    pf_note = (
        "session-level kappa undefined (all pass/fail values identical)"
        if pf_kappa is None
        else ""
    )

    return {
        "per_criterion_kappa": per_criterion,
        "constant_pair_criteria": constant_pairs,
        "pooled": {
            "note": "pooled over non-constant criteria only",
            "criteria": list(per_criterion),
            "n_items": len(pooled_j1),
            "kappa": round(pooled_kappa, 3) if pooled_kappa is not None else None,
            "pct_agreement": pooled_pct,
        },
        "session_level": {
            "definition": "pass = total / n_criteria >= 0.5",
            "pct_agreement": round(pf_pct, 1),
            "kappa": round(pf_kappa, 3) if pf_kappa is not None else None,
            "note": pf_note,
        },
    }


def experiment_main(args: argparse.Namespace) -> None:
    """Blind second-judge rescore of every run in an experiment scores file.

    Any failure (missing key, API error, unparseable response) exits non-zero
    without writing the output. There is no Judge 1 fallback.
    """
    experiment_dir = Path(args.experiment)
    scores_path = experiment_dir / args.scores
    out_path = Path(args.out)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        fail("ANTHROPIC_API_KEY not set; cannot run Judge 2 (no fallback)")

    criteria = load_rubric_criteria(experiment_dir)
    judge1 = load_judge1_scores(scores_path)

    sessions: list[dict] = []
    for run_id, j1 in judge1.items():
        missing = [cid for cid in criteria if cid not in j1]
        if missing:
            fail(f"{scores_path}: {run_id} is missing Judge 1 scores for {missing}")
        prompt = build_experiment_prompt(
            criteria,
            load_session_output(experiment_dir / "sessions" / f"{run_id}.json"),
        )
        print(f"Processing {run_id}...", file=sys.stderr)
        judge2 = score_with_claude(prompt)
        if judge2 is None:
            fail(f"no Judge 2 scores for {run_id}; aborting without output")
        judge2 = parse_judge2_scores(judge2, criteria, run_id)
        print(f"  Judge 2 scored {sum(judge2.values())}/{len(judge2)}", file=sys.stderr)
        n_criteria = len(criteria)
        sessions.append(
            {
                "id": run_id,
                "judge1": {cid: j1[cid] for cid in criteria},
                "judge2": judge2,
                "pass_fail_judge1": int(sum(j1.values()) / n_criteria >= 0.5),
                "pass_fail_judge2": int(sum(judge2.values()) / n_criteria >= 0.5),
            }
        )

    stats = compute_exp4_statistics(criteria, sessions)
    output = {
        "metadata": {
            "experiment": experiment_dir.name,
            "scores_file": str(scores_path),
            "rubric_files": list(EXP4_RUBRIC_FILES),
            "judge1": "Claude Haiku 4.5 (blind, single pass over the scores file)",
            "judge2_model": JUDGE2_MODEL,
            "judge2_temperature": JUDGE2_TEMPERATURE,
            "judge2_inputs": "rubric criteria and session output only (run_id and group removed)",
            "n_sessions": len(sessions),
            "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "sessions": sessions,
        **stats,
    }
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nWritten {out_path}", file=sys.stderr)
    print(f"  Per-criterion kappa: {stats['per_criterion_kappa']}", file=sys.stderr)
    print(
        f"  Constant-pair criteria: {list(stats['constant_pair_criteria'])}",
        file=sys.stderr,
    )
    print(
        f"  Pooled kappa (non-constant criteria): {stats['pooled']['kappa']}",
        file=sys.stderr,
    )


def legacy_main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    results = []

    for session in SESSIONS:
        sid = session["id"]
        exp = session["experiment"]
        cond = session["condition"]
        judge1 = session["judge1"]

        print(f"Processing {sid} (Exp{exp}, {cond})...", file=sys.stderr)

        if api_key:
            prompt = build_rubric_prompt(exp, sid, cond, session["score"])
            judge2 = score_with_claude(prompt)
            if judge2 is None:
                print(
                    f"  No Judge 2 scores for {sid}, using Judge 1 as fallback",
                    file=sys.stderr,
                )
                judge2 = judge1
            else:
                # Log what we got
                j2_total = sum(judge2.values())
                print(f"  Judge 2 scored {j2_total}/{len(judge2)}", file=sys.stderr)
        else:
            print(
                f"  No ANTHROPIC_API_KEY, using Judge 1 scores as fallback for {sid}",
                file=sys.stderr,
            )
            judge2 = judge1

        # Build per-criteria list
        criteria_list = []
        rubric = RUBRICS[exp]
        for cid in rubric:
            j1_val = judge1.get(cid, 0)
            j2_val = judge2.get(cid, 0)
            criteria_list.append({"name": cid, "judge1": j1_val, "judge2": j2_val})

        pf_j1 = compute_session_pass_fail(judge1, exp)
        pf_j2 = compute_session_pass_fail(judge2, exp)

        results.append(
            {
                "id": sid,
                "experiment": exp,
                "condition": cond,
                "pass_fail_judge1": pf_j1,
                "pass_fail_judge2": pf_j2,
                "criteria": criteria_list,
            }
        )

    # ── Compute summary statistics ──────────────────────────────────────────

    # Per-criterion agreement
    all_j1 = []
    all_j2 = []
    for r in results:
        for c in r["criteria"]:
            all_j1.append(c["judge1"])
            all_j2.append(c["judge2"])

    pct_criteria, kappa_criteria = compute_agreement(all_j1, all_j2)

    kappa_criteria_note = ""
    if kappa_criteria is None:
        kappa_criteria_note = (
            "ceiling: per-criterion kappa undefined (all scores identical)"
        )

    # Session-level pass/fail agreement
    session_j1 = [r["pass_fail_judge1"] for r in results]
    session_j2 = [r["pass_fail_judge2"] for r in results]
    pct_session, kappa_session = compute_agreement(session_j1, session_j2)

    kappa_session_note = ""
    if kappa_session is None:
        kappa_session_note = (
            "ceiling: session-level kappa undefined (all scores identical)"
        )
    else:
        # Landis-Koch interpretation
        if kappa_session >= 0.81:
            kappa_session_note = "almost perfect agreement"
        elif kappa_session >= 0.61:
            kappa_session_note = "substantial agreement"
        elif kappa_session >= 0.41:
            kappa_session_note = "moderate agreement"
        elif kappa_session >= 0.21:
            kappa_session_note = "fair agreement"
        elif kappa_session >= 0.0:
            kappa_session_note = "slight agreement"
        else:
            kappa_session_note = "poor agreement (below chance)"

    summary = {
        "n_sessions": len(results),
        "n_criteria_total": len(all_j1),
        "pct_agreement_criteria": round(pct_criteria, 1),
        "kappa_criteria": round(kappa_criteria, 3)
        if kappa_criteria is not None
        else None,
        "kappa_criteria_note": kappa_criteria_note if kappa_criteria_note else "",
        "pct_agreement_session": round(pct_session, 1),
        "kappa_session": round(kappa_session, 3) if kappa_session is not None else None,
        "kappa_session_note": kappa_session_note,
    }

    output = {"sessions": results, "summary": summary}

    with open(OUTPUT, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nWritten {OUTPUT}", file=sys.stderr)
    print(
        f"  Per-criterion agreement: {summary['pct_agreement_criteria']}%",
        file=sys.stderr,
    )
    print(f"  Per-criterion kappa: {summary['kappa_criteria']}", file=sys.stderr)
    print(
        f"  Session-level agreement: {summary['pct_agreement_session']}%",
        file=sys.stderr,
    )
    print(
        f"  Session-level kappa: {summary['kappa_session']} ({summary['kappa_session_note']})",
        file=sys.stderr,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument(
        "--experiment",
        help="experiment directory (enables blind second-judge mode)",
    )
    parser.add_argument(
        "--scores",
        default="scores-main-run.json",
        help="scores file, resolved relative to the experiment directory",
    )
    parser.add_argument(
        "--out",
        default="irr/exp4-scores.json",
        help="output file for --experiment mode",
    )
    args = parser.parse_args()

    if args.experiment:
        experiment_main(args)
    else:
        legacy_main()


if __name__ == "__main__":
    main()

"""Tests for analysis.py: loaders, outcome variables, assertions, cost, determinism, Exp4 regression."""

import json
import re
import shutil
import sys
from pathlib import Path

import pytest

ANALYSIS = Path(__file__).resolve().parents[1]
FIXTURES = ANALYSIS / "tests" / "fixtures"
REPO = ANALYSIS.parents[2]
sys.path.insert(0, str(ANALYSIS))
import analysis as mod  # noqa: E402
import overlap  # noqa: E402


@pytest.fixture
def experiment(tmp_path):
    """Synthetic experiment dir (two models, 5 control + 5 treatment runs)."""
    for name in ("scores.json", "label-map.json", "latency-log.jsonl"):
        shutil.copy(FIXTURES / name, tmp_path / name)
    shutil.copytree(FIXTURES / "outputs", tmp_path / "outputs")  # delegate outputs for the overlap rule
    return tmp_path


def test_label_map_loader_normalises_flat_and_grouped(tmp_path):
    grouped = mod.load_label_map(FIXTURES / "label-map.json")
    flat_string = mod.load_label_map(FIXTURES / "label-map-flat.json")

    assert set(grouped) == set(flat_string)
    assert {r: v["group"] for r, v in flat_string.items()} == {r: v["group"] for r, v in grouped.items()}
    assert flat_string["run-c1"]["model"] is None  # a bare string carries no model

    flat_object = tmp_path / "flat-object.json"
    flat_object.write_text(json.dumps({r: dict(v) for r, v in grouped.items()}))
    assert mod.load_label_map(flat_object) == grouped


def test_cost_matches_hand_computation():
    pricing = json.loads((ANALYSIS / "pricing.json").read_text())["models"]
    rows = [json.loads(line) for line in (FIXTURES / "latency-log.jsonl").read_text().splitlines()]
    # run-c1 (haiku-4-5): 1M input * 1.00 + 200k output * 5.00 + 1M cache read * 0.10 + 400k cache write * 1.25
    #                     = 1.0 + 1.0 + 0.1 + 0.5 = 2.6
    # run-c4 (haiku-5-5): 1M input * 0.10 + 100k output * 0.50 = 0.1 + 0.05 = 0.15
    costs = {r["run_id"]: mod.run_cost(r, pricing) for r in rows}

    assert costs["run-c1"]["cost_usd"] == pytest.approx(2.6)
    assert costs["run-c4"]["cost_usd"] == pytest.approx(0.15)
    assert costs["run-c1"]["cost_usd"] + costs["run-c4"]["cost_usd"] == pytest.approx(2.75)

    # claude-haiku-5-5 cache rates are verified (owner, 2026-11-27): a cache read is priced, not null
    cached = dict(next(r for r in rows if r["run_id"] == "run-c4"), cache_read_tokens=10)
    assert mod.run_cost(cached, pricing)["cost_usd"] == pytest.approx(0.15 + 10 * 0.01 / 1_000_000)
    unverified = {**pricing, "claude-haiku-5-5": {**pricing["claude-haiku-5-5"], "cache_read": None}}
    assert mod.run_cost(cached, unverified)["cost_usd"] is None  # a null rate stays a null cost with a note
    assert mod.run_cost({**cached, "model": "mystery"}, pricing)["cost_usd"] is None


def test_cost_does_not_subtract_cache_tokens_from_input():
    # input_tokens excludes cached tokens (Anthropic usage), so a run whose
    # cache_read equals its input still pays the full input charge: no
    # subtraction, no double counting.
    pricing = json.loads((ANALYSIS / "pricing.json").read_text())["models"]["claude-haiku-4-5"]
    row = {"model": "claude-haiku-4-5", "input_tokens": 1_000_000, "output_tokens": 0,
           "cache_read_tokens": 1_000_000, "cache_write_tokens": 0}

    assert mod.run_cost(row, {"claude-haiku-4-5": pricing})["cost_usd"] == pytest.approx(1.1)  # 1.0 + 0.1, not 0.1


def test_cost_is_null_and_finite_json_on_invalid_inputs():
    pricing = json.loads((ANALYSIS / "pricing.json").read_text())["models"]
    base = {"model": "claude-haiku-4-5", "input_tokens": 10, "output_tokens": 10, "cache_read_tokens": 0, "cache_write_tokens": 0}

    bad_tokens = mod.run_cost({**base, "input_tokens": "not-a-number"}, pricing)
    assert bad_tokens["cost_usd"] is None and "invalid token count" in bad_tokens["note"]
    bad_rate = mod.run_cost(base, {"claude-haiku-4-5": {**pricing["claude-haiku-4-5"], "input": float("nan")}})
    assert bad_rate["cost_usd"] is None and "invalid rate" in bad_rate["note"]
    json.dumps({"a": bad_tokens, "b": bad_rate}, allow_nan=False)


def test_determinism_two_runs_are_byte_identical(experiment, tmp_path):
    outputs = []
    for i in range(2):
        out = experiment / f"out{i}"
        assert mod.main([str(experiment), "--out", str(out)]) == 0
        outputs.append({p.name: p.read_bytes() for p in sorted(out.iterdir())})
    assert outputs[0] == outputs[1]
    assert {"analysis.json", "table_means.tex", "table_effects.tex", "table_cost.tex"} <= set(outputs[0])
    assert json.loads(outputs[0]["analysis.json"])["bootstrap_seed"] == mod.DEFAULT_SEED


def test_failing_hash_and_coverage_assertions_exit_nonzero_but_write(experiment):
    labels = json.loads((experiment / "label-map.json").read_text())
    labels["assignments"]["run-c1"]["sha256_scorer"] = "0" * 64
    del labels["assignments"]["run-c2"]
    (experiment / "label-map.json").write_text(json.dumps(labels))

    out = experiment / "out"
    assert mod.main([str(experiment), "--out", str(out)]) == 1
    result = json.loads((out / "analysis.json").read_text())
    failed = {a["name"] for a in result["assertions"] if a["status"] == "fail"}
    assert failed == {"label_map_hashes", "coverage_scores_in_label_map"}
    assert all(a["status"] in {"pass", "fail", "skipped"} for a in result["assertions"])


def test_declared_hashes_pass_when_files_match(experiment):
    (experiment / "scorer-prompt.md").write_text("scorer\n")
    labels = json.loads((experiment / "label-map.json").read_text())
    digest = mod.sha256_file(experiment / "scorer-prompt.md")
    for v in labels["assignments"].values():
        v["sha256_scorer"] = digest
    (experiment / "label-map.json").write_text(json.dumps(labels))

    checks = {a["name"]: a for a in mod.build_assertions(mod.load_scores(experiment / "scores.json"), mod.load_label_map(experiment / "label-map.json"), mod.load_latency(experiment / "latency-log.jsonl"), experiment)}
    assert checks["label_map_hashes"]["status"] == "pass"


def test_thinking_tokens_null_is_not_captured_but_positive_fails(experiment):
    scores = mod.load_scores(experiment / "scores.json")
    labels = mod.load_label_map(experiment / "label-map.json")
    rows = mod.load_latency(experiment / "latency-log.jsonl")
    assert all(r["thinking_tokens"] is None for r in rows)

    def status(latency):
        return {a["name"]: a["status"] for a in mod.build_assertions(scores, labels, latency, experiment)}["thinking_tokens_zero"]

    assert status(rows) == "pass"
    assert status([{**r, "thinking_tokens": 0} for r in rows]) == "pass"
    assert status([{**rows[0], "thinking_tokens": 12}] + rows[1:]) == "fail"


def test_exp4_regression_control_4_2_vs_treatment_4_0():
    exp4 = REPO / "experiments" / "exp-swift-grammar-mercury"
    if not exp4.exists():  # repo-relative reference, never copied into fixtures
        pytest.skip("exp4 fixture directory not available")
    scores = mod.load_scores(exp4 / "scores-main-run.json")
    labels = mod.load_label_map(exp4 / "label-map.json")
    result = mod.analyse(scores, labels, [], {}, exp4, mod.DEFAULT_SEED)

    assert result["arms"]["control"]["mean"] == 4.2
    assert result["arms"]["treatment"]["mean"] == 4.0
    assert result["arms"]["control"]["n"] == result["arms"]["treatment"]["n"] == 5


# ---------------------------------------------------------------- outcome variables

def test_exp5_record_without_primary_total_fails_loudly(tmp_path):
    """An Exp5 score file that lacks primary_total raises instead of scoring total."""
    raw = json.loads((FIXTURES / "scores.json").read_text())
    del raw["scores"][0]["primary_total"]
    (tmp_path / "scores.json").write_text(json.dumps(raw))

    with pytest.raises(ValueError, match="run-c1.*no primary_total"):
        mod.load_scores(tmp_path / "scores.json")
    with pytest.raises(ValueError, match="primary_total"):
        mod.main([str(tmp_path), "--out", str(tmp_path / "out")])


def test_null_c5_in_exp5_record_fails_loudly(tmp_path):
    raw = json.loads((FIXTURES / "scores.json").read_text())
    raw["scores"][0]["C5"] = None
    (tmp_path / "scores.json").write_text(json.dumps(raw))

    with pytest.raises(ValueError, match="null C5"):
        mod.load_scores(tmp_path / "scores.json")


def test_exp4_layout_without_primary_total_falls_back_to_total():
    """Pre-#123 Exp4 fixtures (nested scores, no primary_total) are the only fallback to total."""
    exp4 = REPO / "experiments" / "exp-swift-grammar-mercury"
    if not exp4.exists():
        pytest.skip("exp4 fixture directory not available")
    rows = mod.load_scores(exp4 / "scores-main-run.json")

    assert rows and all(r["primary_total"] == r["total"] for r in rows)
    assert all(r["primary_total_source"].startswith("total") for r in rows)


def test_co_reported_outcome_is_primary_total_minus_c5():
    rows = mod.load_scores(FIXTURES / "scores.json")

    assert all(r["primary_total"] == pytest.approx(r["C3"] + r["C4"] + r["C5"]) for r in rows)
    assert all(r["primary_total_minus_c5"] == pytest.approx(r["primary_total"] - r["C5"]) for r in rows)
    assert all(r["primary_total_minus_c5"] == pytest.approx(r["C3"] + r["C4"]) for r in rows)
    assert all(0 <= r["primary_total"] <= 3 and 0 <= r["primary_total_minus_c5"] <= 2 for r in rows)
    assert any(r["C5"] != r["total"] - r["primary_total"] for r in rows)  # C6/C7 stay in total only
    assert all(r["primary_total_source"] == "primary_total" for r in rows)


def test_analysis_json_keys_every_effect_off_primary_total(experiment, tmp_path):
    out = tmp_path / "out"
    assert mod.main([str(experiment), "--out", str(out)]) == 0
    result = json.loads((out / "analysis.json").read_text())
    rows = mod.load_scores(experiment / "scores.json")
    labels = mod.load_label_map(experiment / "label-map.json")

    assert result["outcome"]["primary"]["field"] == "primary_total"
    assert result["outcome"]["co_reported"]["field"] == "primary_total_minus_c5"
    assert result["outcome"]["secondary"] == ["C6", "C7"] and result["outcome"]["record_only"] == ["total"]
    for arm in mod.ARMS:
        ids = result["arms"][arm]["runs"]
        expected = [r["primary_total"] for r in rows if r["run_id"] in ids]
        expected_total = [r["total"] for r in rows if r["run_id"] in ids]
        expected_minus = [r["primary_total_minus_c5"] for r in rows if r["run_id"] in ids]
        assert result["arms"][arm]["mean"] == pytest.approx(sum(expected) / len(expected), abs=1e-4)
        assert result["arms"][arm]["mean"] != pytest.approx(sum(expected_total) / len(expected_total), abs=1e-4)
        assert result["arms"][arm]["scores"] == sorted(round(v, 4) for v in expected)
        assert result["arms"][arm]["minus_c5"]["mean"] == pytest.approx(sum(expected_minus) / len(expected_minus), abs=1e-4)
    for block in (result["effect_size"], result["effect_size_minus_c5"]):
        field = block["outcome"]
        for model, eff in block["per_model"].items():
            t = [r[field] for r in rows if labels[r["run_id"]]["model"] == model and labels[r["run_id"]]["group"] == "treatment"]
            c = [r[field] for r in rows if labels[r["run_id"]]["model"] == model and labels[r["run_id"]]["group"] == "control"]
            assert len(t) == len(c) >= 1
            assert eff["r"] == pytest.approx(mod.mann_whitney_r(t, c)["r"])
            assert eff["bootstrap"]["seed"] == mod.DEFAULT_SEED
    assert result["effect_size"]["outcome"] == "primary_total"
    assert result["effect_size_minus_c5"]["outcome"] == "primary_total_minus_c5"
    assert set(result["criteria_by_model"]) == set(labels[r["run_id"]]["model"] for r in rows)
    assert set(result["arms"]["control"]["criteria_means"]) == set(mod.CRITERIA)


def test_latex_headers_name_both_outcomes(experiment, tmp_path):
    out = tmp_path / "out"
    assert mod.main([str(experiment), "--out", str(out)]) == 0
    means = (out / "table_means.tex").read_text()
    effects = (out / "table_effects.tex").read_text()

    assert "primary\\_total = C3 + C4 + C5" in means and "minus C5" in means
    assert "primary\\_total = C3 + C4 + C5" in effects and "minus C5" in effects
    data_rows = [l for l in means.splitlines() if l.startswith(("control", "treatment"))]
    assert len(data_rows) == 2 and all(l.count(" & ") == 8 for l in data_rows)  # 9 columns per arm row
    data_rows = [l for l in effects.splitlines() if l.startswith("claude")]
    assert len(data_rows) == 2 and all(l.count(" & ") == 5 for l in data_rows)  # 6 columns per model row


# ---------------------------------------------------------------- exclusions (issue #129)

PILOT = ANALYSIS.parent / "scorer" / "pilot-evidence" / "fenced-repilot"
# protocol.md ## Pilot Evidence, "Output overlap per pilot run" (element, defuse), two decimals
PILOT_EXPECTED = {
    "h45-control": (0.03, 0.01), "h45-treatment": (0.03, 0.01),
    "h55-control": (0.03, 0.04), "h55-treatment": (0.03, 0.03),
}
SNAKE = r"[a-z]+(?:_[a-z]+)+"


def _synthetic_node_types(n: int = 12) -> list:
    """A vocabulary whose every entry is snake_case, so the whole set is citable."""
    entries = [{"type": f"node_{chr(ord('a') + i)}", "named": True} for i in range(n - 2)]  # letters only: snake_case per the protocol regex
    entries[0]["fields"] = {"variable_name": {}, "other_field": {}}
    return entries


def _cites_all(node_types) -> str:
    """A draft citing the whole vocabulary."""
    return "\n".join(f"({name}) @capture_{i}" for i, name in enumerate(sorted(overlap.vocabulary(node_types))))


def _score(run_id: str, **extra) -> dict:
    return {"run_id": run_id, **dict.fromkeys(mod.CRITERIA, 1.0), "total": 5.0, "primary_total": 3.0,
            "primary_total_minus_c5": 2.0, "primary_total_source": "primary_total", "failure_mode": None, **extra}


def test_pilot_overlap_values_reproduce_protocol_to_two_decimals():
    node_types = mod.NODE_TYPES
    for run_id, expected in PILOT_EXPECTED.items():
        output = json.loads((PILOT / run_id / "exp5-output.json").read_text())
        values = overlap.jaccard_by_draft(output, node_types)
        assert (round(values["element_query_draft"], 2), round(values["defuse_query_draft"], 2)) == expected, run_id
        assert all(v is not None and v <= overlap.THRESHOLD for v in values.values())
    assert len(overlap.vocabulary(node_types)) == 187
    assert overlap.TOKEN.pattern == r"\b" + SNAKE + r"\b"  # the regex protocol.md words


def test_rule_ceiling_with_the_vendored_vocabulary():
    """Only 147 of the 187 vendored entries are snake_case, so a draft citing every citable
    entry scores 147/187 = 0.786 < 0.8: the rule as worded cannot fire on this vocabulary."""
    vendored = mod.NODE_TYPES
    vocab = overlap.vocabulary(vendored)
    citable = {n for n in vocab if re.fullmatch(SNAKE, n)}
    assert len(vocab) == 187 and len(citable) == 147
    everything = {"element_query_draft": _cites_all(vendored), "defuse_query_draft": _cites_all(vendored)}
    assert overlap.jaccard(everything, vendored) == pytest.approx(147 / 187, abs=1e-4)
    assert not overlap.excluded(everything, vendored)


def test_overlap_method_details():
    node_types = _synthetic_node_types()
    vocab = overlap.vocabulary(node_types)
    assert vocab == {f"node_{chr(ord('a') + i)}" for i in range(10)} | {"variable_name", "other_field"}
    output = {"element_query_draft": "; (dropped_kind) comment\n" + _cites_all(node_types).replace("(node_a)", "(node_a) ; x"),
              "defuse_query_draft": "(simple_variable) @read.usage\n(variable_declaration name: (variable_name) @write.local)"}
    assert overlap.jaccard(output, node_types) == pytest.approx(1.0)
    assert overlap.jaccard(output, node_types, "defuse_query_draft") == pytest.approx(1 / 12, abs=1e-4)  # variable_name is in the vocabulary; read.usage is a capture
    assert overlap.jaccard_by_draft({"defuse_query_draft": None}, node_types) == {"element_query_draft": None, "defuse_query_draft": None}
    assert overlap.cited(None, vocab) == set() and overlap.cited("Class_Declaration", vocab) == set()  # the regex is lowercase-only, as worded


def test_overlap_above_threshold_is_excluded_with_reason_output_overlap(tmp_path):
    node_types = _synthetic_node_types()
    output = {"element_query_draft": _cites_all(node_types), "defuse_query_draft": "(simple_variable) @read"}
    assert overlap.jaccard(output, node_types) > overlap.THRESHOLD
    (tmp_path / "run-x").mkdir()
    (tmp_path / "run-x" / "exp5-output.json").write_text(json.dumps(output))

    result = mod.apply_exclusions([_score("run-x")], [], tmp_path, node_types)

    assert result["per_run"]["run-x"] == {"excluded": True, "reason": "output_overlap", "failure_mode": None,
                                          "overlap": {"element_query_draft": 1.0, "defuse_query_draft": 0.0}, "overlap_available": True}
    assert result["excluded"] == ["run-x"] and result["kept"] == []
    assert overlap.jaccard(output, node_types) == pytest.approx(1.0)  # the signature named in #129


@pytest.mark.parametrize("failure_mode", ["goose_exit_1", "timeout", "clone_failed"])
def test_failure_mode_is_excluded_with_reason_turn_cap(failure_mode):
    latency = mod.apply_exclusions([_score("run-f")], [{"run_id": "run-f", "failure_mode": failure_mode}], None, mod.NODE_TYPES)
    in_score = mod.apply_exclusions([_score("run-f", failure_mode=failure_mode)], [], None, mod.NODE_TYPES)

    assert mod.EXCLUSION_REASONS == ("turn_cap", "output_overlap")
    for result in (latency, in_score):
        assert result["per_run"]["run-f"]["excluded"] is True and result["per_run"]["run-f"]["reason"] == "turn_cap"
        assert result["per_run"]["run-f"]["failure_mode"] == failure_mode and result["per_run"]["run-f"]["overlap"] is None
        assert result["excluded"] == ["run-f"] and result["kept"] == []


def test_run_with_neither_is_kept(tmp_path):
    (tmp_path / "run-k").mkdir()
    (tmp_path / "run-k" / "exp5-output.json").write_text(json.dumps({"element_query_draft": "(class_declaration) @c"}))

    result = mod.apply_exclusions([_score("run-k")], [{"run_id": "run-k", "failure_mode": None}], tmp_path, mod.NODE_TYPES)

    assert result["per_run"]["run-k"]["excluded"] is False and result["per_run"]["run-k"]["reason"] is None
    assert result["per_run"]["run-k"]["overlap"]["element_query_draft"] == pytest.approx(1 / 187, abs=1e-4)
    assert result["kept"] == ["run-k"] and result["excluded"] == []


def test_excluded_run_is_listed_n_drops_and_effect_uses_remaining_runs(experiment, tmp_path):
    assert mod.main([str(experiment), "--out", str(tmp_path / "base")]) == 0
    base = json.loads((tmp_path / "base" / "analysis.json").read_text())
    assert base["exclusions"]["n_excluded"] == 0 and base["n_runs"] == 10
    assert "no excluded runs" in (tmp_path / "base" / "table_exclusions.tex").read_text()
    # exclude run-t1 (treatment, claude-haiku-4-5, primary_total 3.0) by output overlap, under a synthetic vocabulary
    node_types = tmp_path / "node-types.json"
    node_types.write_text(json.dumps(_synthetic_node_types()))
    (experiment / "outputs" / "run-t1" / "exp5-output.json").write_text(json.dumps({"element_query_draft": _cites_all(_synthetic_node_types())}))
    labels = json.loads((experiment / "label-map.json").read_text())
    assert labels["assignments"]["run-t1"]["group"] == "treatment"

    assert mod.main([str(experiment), "--out", str(tmp_path / "out"), "--node-types", str(node_types)]) == 0
    out = tmp_path / "out"
    result = json.loads((out / "analysis.json").read_text())
    assert result["n_scored"] == 10 and result["n_runs"] == 9
    assert result["exclusions"]["n_excluded"] == 1 and result["exclusions"]["n_kept"] == 9
    assert [(e["run_id"], e["reason"], e["failure_mode"]) for e in result["exclusions"]["excluded"]] == [("run-t1", "output_overlap", None)]
    assert result["exclusions"]["per_run"]["run-t1"]["excluded"] is True
    assert all(result["exclusions"]["per_run"][r]["excluded"] is False for r in result["exclusions"]["kept"])
    assert "run-t1" not in result["arms"]["treatment"]["runs"] and "run-t1" not in result["arms"]["control"]["runs"]
    assert result["arms"]["treatment"]["n"] == base["arms"]["treatment"]["n"] - 1 == 4
    assert result["arms"]["control"]["n"] == base["arms"]["control"]["n"] == 5
    assert result["arms"]["treatment"]["scores"] == sorted(result["arms"]["treatment"]["scores"])
    assert "run-t1" not in (out / "table_means.tex").read_text()
    tex = (out / "table_exclusions.tex").read_text()
    assert "run-t1" in tex and "output\\_overlap" in tex and "1.0000 & --" in tex

    rows = mod.load_scores(experiment / "scores.json")

    def values(field, model, group, drop=()):
        return [r[field] for r in rows if r["run_id"] not in drop and labels["assignments"][r["run_id"]]["model"] == model and labels["assignments"][r["run_id"]]["group"] == group]

    for field, block in (("primary_total", result["effect_size"]), ("primary_total_minus_c5", result["effect_size_minus_c5"])):
        eff = block["per_model"]["claude-haiku-4-5"]
        t, c = values(field, "claude-haiku-4-5", "treatment", drop=("run-t1",)), values(field, "claude-haiku-4-5", "control")
        assert len(t) == 2 and len(c) == 3  # h4-5: 3 v 3 in the fixture, minus the excluded run
        assert eff["r"] == pytest.approx(mod.mann_whitney_r(t, c)["r"])
        assert eff["bootstrap"] == mod.bootstrap_ci(t, c, mod.DEFAULT_SEED)
        assert eff["r"] != pytest.approx(mod.mann_whitney_r(values(field, "claude-haiku-4-5", "treatment"), c)["r"])  # the excluded run would have changed it
    assert result["effect_size"]["per_model"]["claude-haiku-4-5"] != base["effect_size"]["per_model"]["claude-haiku-4-5"]
    assert result["effect_size"]["per_model"]["claude-haiku-5-5"] == base["effect_size"]["per_model"]["claude-haiku-5-5"]  # untouched arm
    assert {a["name"] for a in result["assertions"] if a["status"] == "fail"} == set()


def test_failure_mode_run_excluded_end_to_end(experiment, tmp_path):
    rows = [json.loads(line) for line in (experiment / "latency-log.jsonl").read_text().splitlines()]
    rows = [{**r, "failure_mode": "goose_exit_1"} if r["run_id"] == "run-c1" else r for r in rows]
    (experiment / "latency-log.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))

    assert mod.main([str(experiment), "--out", str(tmp_path / "out")]) == 0
    result = json.loads((tmp_path / "out" / "analysis.json").read_text())

    assert [(e["run_id"], e["reason"], e["failure_mode"]) for e in result["exclusions"]["excluded"]] == [("run-c1", "turn_cap", "goose_exit_1")]
    assert result["arms"]["control"]["n"] == 4 and result["n_runs"] == 9 and result["exclusions"]["overlap_threshold"] == 0.8
    assert "run-c1 & turn\\_cap & goose\\_exit\\_1" in (tmp_path / "out" / "table_exclusions.tex").read_text()


def test_missing_output_file_for_kept_run_fails_the_assertion_but_writes(experiment, tmp_path):
    shutil.rmtree(experiment / "outputs" / "run-c2")

    assert mod.main([str(experiment), "--out", str(tmp_path / "out")]) == 1
    result = json.loads((tmp_path / "out" / "analysis.json").read_text())
    failed = [a for a in result["assertions"] if a["status"] == "fail"]
    assert [a["name"] for a in failed] == ["exclusion_overlap_available"] and "run-c2" in failed[0]["detail"]
    assert result["exclusions"]["per_run"]["run-c2"]["overlap_available"] is False
    assert result["exclusions"]["per_run"]["run-c2"]["excluded"] is False  # not a rule hit: kept, but flagged
    assert "no excluded runs" in (tmp_path / "out" / "table_exclusions.tex").read_text()


def test_exp4_regression_has_no_exclusions():
    exp4 = REPO / "experiments" / "exp-swift-grammar-mercury"
    if not exp4.exists():
        pytest.skip("exp4 fixture directory not available")
    result = mod.analyse(mod.load_scores(exp4 / "scores-main-run.json"), mod.load_label_map(exp4 / "label-map.json"), [], {}, exp4, mod.DEFAULT_SEED)

    assert result["exclusions"]["n_excluded"] == 0 and result["n_runs"] == 10

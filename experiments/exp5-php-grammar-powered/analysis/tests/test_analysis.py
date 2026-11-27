"""Tests for analysis.py: loaders, assertions, cost, determinism, Exp4 regression."""

import json
import shutil
import sys
from pathlib import Path

import pytest

ANALYSIS = Path(__file__).resolve().parents[1]
FIXTURES = ANALYSIS / "tests" / "fixtures"
REPO = ANALYSIS.parents[2]
sys.path.insert(0, str(ANALYSIS))
import analysis as mod  # noqa: E402


@pytest.fixture
def experiment(tmp_path):
    """Synthetic experiment dir (two models, 5 control + 5 treatment runs)."""
    for name in ("scores.json", "label-map.json", "latency-log.jsonl"):
        shutil.copy(FIXTURES / name, tmp_path / name)
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

    unpriced = dict(next(r for r in rows if r["run_id"] == "run-c4"), cache_read_tokens=10)
    assert mod.run_cost(unpriced, pricing)["cost_usd"] is None  # unverified haiku-5-5 cache rate
    assert mod.run_cost({**unpriced, "model": "mystery"}, pricing)["cost_usd"] is None


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

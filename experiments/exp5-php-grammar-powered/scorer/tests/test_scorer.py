"""Tests for the Exp5 PHP scorer: query, citation, snippet, wiring, end-to-end."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import checks  # noqa: E402
import scorer  # noqa: E402

GOOD = json.loads((ROOT / "fixtures" / "sessions" / "known-good.json").read_text())
BAD = json.loads((ROOT / "fixtures" / "sessions" / "known-bad.json").read_text())


@pytest.fixture(scope="module")
def lang():
    return checks.php_language()


# --- C3 / C5: query checks (happy path) ---
@pytest.mark.parametrize(
    ("fn", "field"),
    [(checks.check_element_query, "element_query_draft"), (checks.check_defuse_query, "defuse_query_draft")],
)
def test_known_good_query_scores_one(lang, fn, field):
    assert fn(GOOD[field], lang).score == 1.0


def test_element_query_missing_required_kind_scores_expected_share(lang):
    query = "(function_definition name: (name) @f)\n(class_declaration name: (name) @c)\n(method_declaration name: (name) @m)"
    result = checks.check_element_query(query, lang)
    assert result.score == pytest.approx(3 / 6)
    assert "enum_declaration" in result.justification


def test_non_compiling_query_scores_zero_and_names_query(lang):
    for fn, field in ((checks.check_element_query, "element_query_draft"), (checks.check_defuse_query, "defuse_query_draft")):
        result = fn(BAD[field], lang)
        assert result.score == 0.0
        assert field in result.justification


# --- C6: snippet check (edge case) ---
def test_unparsable_snippet_is_excluded_and_named(lang):
    snippets = GOOD["test_snippets"] + [{"dimension": "declaration_kind", "code": "class A {", "test_name": "test_broken"}]
    result = checks.check_snippets(snippets, lang)
    assert result.score == pytest.approx(4 / 5)
    assert "test_broken" in result.justification


def test_no_snippets_scores_zero(lang):
    assert checks.check_snippets([], lang).score == 0.0


# --- C7: wiring check (happy path) ---
def test_wiring_each_fact_scores_against_snapshot():
    assert checks.check_wiring(GOOD["wiring_summary"]).score == 1.0
    facts = checks.wiring_facts({**GOOD["wiring_summary"], "extension_map_entry": '("php5", "php"),', "mod_registration": "register it somewhere"})
    assert facts == {
        "workspace_dependency": True,
        "unconditional_dependency": True,
        "extension_map_entry": False,
        "mod_registration": False,
        "match_arms": True,
    }
    assert checks.check_wiring({**GOOD["wiring_summary"], "extension_map_entry": '("php5", "php"),', "mod_registration": "x"}).score == pytest.approx(3 / 5)


def test_wiring_missing_or_wrong_shape_scores_zero():
    assert checks.check_wiring({"workspace_dependency": "add it"}).score == 0.0
    assert checks.check_wiring("not an object").score == 0.0


# --- C4: citation check (edge case) ---
def test_citation_real_kinds_count_and_invented_kind_does_not():
    assert checks.check_inheritance_citation(GOOD["inheritance_walk_citation"]).score == 1.0
    result = checks.check_inheritance_citation("Walk `base_clause` then `inherits_from` to `user_type`.")
    assert result.score == pytest.approx(1 / 3)
    assert "inherits_from" in result.justification


# --- end-to-end ---
def _blank_scored_at(path: Path) -> str:
    doc = json.loads(path.read_text())
    doc["scored_at"] = ""
    return json.dumps(doc, sort_keys=True)


def test_end_to_end_fixtures_are_valid_and_deterministic(tmp_path):
    sessions = ROOT / "fixtures" / "sessions"
    first, second = tmp_path / "a.json", tmp_path / "b.json"
    assert scorer.main([str(sessions), "--out", str(first)]) == 0
    assert scorer.main([str(sessions), "--out", str(second)]) == 0
    assert _blank_scored_at(first) == _blank_scored_at(second)

    doc = json.loads(first.read_text())
    assert list(doc) == ["scored_at", "scorer", "rubric_version", "note", "scores"]
    good = next(r for r in doc["scores"] if r["run_id"] == "known-good")
    bad = next(r for r in doc["scores"] if r["run_id"] == "known-bad")
    assert good["C1"] is None and good["C2"] is None
    assert good["total"] == pytest.approx(sum(good[c] for c in scorer.CRITERIA))
    assert good["total"] == 5.0
    assert bad["total"] == 0.0
    assert set(bad["justifications"]) == {"C1", "C2", "C3", "C4", "C5", "C6", "C7"}


def test_report_variance_lists_every_criterion():
    report = scorer.report_variance([GOOD, BAD])
    assert set(report) == set(scorer.CRITERIA) | {f"C7.{k}" for k in checks.WIRING_KEYS}
    assert report["C4"]["min"] == 0.0 and report["C4"]["max"] == 1.0

from pathlib import Path

import pytest
import yaml

from gen_recipes import CONTROL_INSTRUCTIONS, generate, prompt_body, read_plan

HERE = Path(__file__).resolve().parents[1]

def test_pilot_plan_emits_paired_recipes(tmp_path):
    runs = read_plan(HERE / "plans/pilot.csv")
    body = prompt_body(HERE / "runner-prompt.md")

    written = generate(HERE / "plans/pilot.csv", HERE / "runner-prompt.md", tmp_path)

    assert [p.name for p in written] == ["recipe-01.yaml", "recipe-02.yaml", "recipe-03.yaml", "recipe-04.yaml"]
    recipes = [yaml.safe_load(p.read_text(encoding="utf-8")) for p in written]
    assert [r["settings"]["goose_model"] for r in recipes] == [run.model for run in runs]
    assert {r["prompt"] for r in recipes} == {body}
    assert recipes[0]["settings"] == {"goose_provider": "anthropic", "goose_model": runs[0].model, "temperature": 0.5}
    assert [e["name"] for e in recipes[0]["extensions"]] == ["developer", "context7", "brave_search"]
    assert recipes[1]["title"] == "exp5-h45-treatment"
    assert recipes[1]["instructions"].endswith(recipes[1]["prompt"])
    for control, treatment in ((0, 1), (2, 3)):
        left, right = recipes[control], recipes[treatment]
        assert {k for k in left if left[k] != right[k]} == {"title", "description", "instructions"}
        assert left["instructions"] == CONTROL_INSTRUCTIONS
        assert right["instructions"] == CONTROL_INSTRUCTIONS + "\n\n" + body
    for path in written:
        text = path.read_text(encoding="utf-8")
        assert "/Users/" not in text and "~/" not in text and "thinking_effort" not in text

@pytest.mark.parametrize("plan_text, message", [
    ("run_id,group,model\nr1,placebo,m\n", "group must be"),
    ("run_id,group,model\nr1,control,m\nr1,treatment,m\n", "duplicate run_id"),
])
def test_read_plan_rejects_invalid_rows(tmp_path, plan_text, message):
    plan = tmp_path / "plan.csv"
    plan.write_text(plan_text, encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        read_plan(plan)

def test_prompt_body_rejects_local_path(tmp_path):
    template = tmp_path / "runner-prompt.md"
    template.write_text(f"preamble\n\n---\n\nWork in {Path.home()}/repo and write {{output_path}}.\n", encoding="utf-8")
    with pytest.raises(ValueError, match="absolute local path"):
        prompt_body(template)

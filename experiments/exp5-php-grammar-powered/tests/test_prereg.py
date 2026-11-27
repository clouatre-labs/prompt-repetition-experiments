import re
from pathlib import Path

from gen_recipes import read_plan
from run import seal, tree_sha256

HERE = Path(__file__).resolve().parents[1]
RUN_ID = re.compile(r"^(h45|h55)-[0-9]{2}$")
MODELS = {"h45": "claude-haiku-4-5", "h55": "claude-haiku-5-5"}
HEADINGS = [
    "## Research Question", "## Hypothesis", "## Design", "## Primary Outcome", "## Statistical Analysis",
    "## Pooling and Interaction", "## Floor and Ceiling Rule", "## Exclusions", "## Stopping Rule",
    "## Measurement Limits", "## Cost Reporting", "## Pilot Evidence", "## Deposit",
]

def test_main_csv_shape():
    runs = read_plan(HERE / "plans/main.csv")

    assert len(runs) == 80
    assert all(RUN_ID.match(r.run_id) for r in runs)
    assert all(r.group == ("control" if int(r.run_id[-2:]) % 2 else "treatment") for r in runs)
    assert all(r.model == MODELS[r.run_id[:3]] for r in runs)
    blocks = [r.run_id[:3] for r in runs]
    assert blocks == ["h45"] * 40 + ["h55"] * 40
    cells = {}
    for r in runs:
        cells[r.model, r.group] = cells.get((r.model, r.group), 0) + 1
    assert cells == {(m, g): 20 for m in MODELS.values() for g in ("control", "treatment")}

def test_tree_sha256_stable_and_sensitive(tmp_path: Path):
    (tmp_path / "a.py").write_text("print(1)\n", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.md").write_text("b", encoding="utf-8")
    (tmp_path / "sub" / "c.txt").write_text("excluded by suffix", encoding="utf-8")
    excluded = tmp_path / "tests" / "t.py"
    excluded.parent.mkdir()
    excluded.write_text("x = 1\n", encoding="utf-8")

    before = tree_sha256(tmp_path)

    assert before == tree_sha256(tmp_path)
    assert before != tree_sha256(tmp_path / "sub")
    (tmp_path / "sub" / "b.md").write_text("c", encoding="utf-8")
    assert before != tree_sha256(tmp_path)

def test_seal_hashes():
    runs = read_plan(HERE / "plans/main.csv")

    label_map = seal(runs, 2, "x")

    assert set(label_map["assignments"]) == {r.run_id for r in runs}
    assert all(a["sha256_scorer"] == tree_sha256(HERE / "scorer") for a in label_map["assignments"].values())
    assert all(a["sha256_analysis"] == tree_sha256(HERE / "analysis") for a in label_map["assignments"].values())
    assert all(a["sha256_scorer"] and a["sha256_analysis"] for a in label_map["assignments"].values())

def test_protocol_headings():
    text = (HERE / "protocol.md").read_text(encoding="utf-8")

    assert re.findall(r"^## .*$", text, flags=re.M) == HEADINGS

def test_amendments_header_only():
    lines = [l for l in (HERE / "AMENDMENTS.md").read_text(encoding="utf-8").splitlines() if l.strip()]

    assert len(lines) == 2 and lines[0].startswith("# ") and "No amendments" in lines[1]

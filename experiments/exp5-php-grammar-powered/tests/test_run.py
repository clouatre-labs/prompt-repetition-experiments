import json
import sqlite3
import threading
import time
from pathlib import Path

import pytest
import yaml

from gen_recipes import build_recipe, prompt_body, read_plan, sha256_text, write_recipe
from run import Config, SpawnResult, assignments_sha256, find_session, run_all, utcnow

HERE = Path(__file__).resolve().parents[1]
PLAN = "run_id,group,model\nr1,control,m\nr2,treatment,m\nr3,control,m\nr4,treatment,m\n"

def make_config(tmp_path: Path, with_db: bool = False) -> Config:
    plan = tmp_path / "plan.csv"
    plan.write_text(PLAN, encoding="utf-8")
    recipes = tmp_path / "recipes"
    body = prompt_body(HERE / "runner-prompt.md")
    for run in read_plan(plan):
        write_recipe(build_recipe(run, body), recipes / run.recipe_file)
    db = tmp_path / "sessions.db"
    if with_db:
        conn = sqlite3.connect(db)
        conn.executescript(
            "CREATE TABLE sessions (id TEXT PRIMARY KEY, name TEXT, accumulated_input_tokens INTEGER,"
            " accumulated_output_tokens INTEGER, accumulated_total_tokens INTEGER, accumulated_cache_read_tokens INTEGER,"
            " accumulated_cache_write_tokens INTEGER, accumulated_cost REAL);"
            "CREATE TABLE messages (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, role TEXT, content_json TEXT);"
        )
        for n, name in enumerate(["exp5-r1", "unrelated"]):
            conn.execute("INSERT INTO sessions VALUES (?, ?, 10, 5, 15, 3, 1, 0.0)", (f"sid-{n}", name))
        conn.execute("INSERT INTO messages (session_id, role, content_json) VALUES ('sid-0', 'assistant', ?)", (json.dumps([
            {"type": "thinking", "thinking": "hmm"},
            {"type": "toolRequest", "toolCall": {"value": {"name": "shell", "arguments": {"command": "ls secret"}}}},
            {"type": "toolRequest", "toolCall": {"value": {"name": "read", "arguments": {"path": "src/lib.rs"}}}},
        ]),))
        conn.commit()
        conn.close()
    return Config(plan=plan, recipes_dir=recipes, template=HERE / "runner-prompt.md", out_dir=tmp_path / "out",
                  scratch=tmp_path / "scratch", sessions_db=db, clone=False)

def ok(req, cfg):
    return SpawnResult(0, "", "", utcnow(), utcnow())

def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

def test_seal_precedes_spawn_and_session_is_backfilled_by_name(tmp_path):
    cfg = make_config(tmp_path, with_db=True)
    seen = []

    def spawn(req, cfg):
        label_map = json.loads((cfg.out_dir / "label-map.json").read_text(encoding="utf-8"))
        a = label_map["assignments"][req.run.run_id]
        seen.append((label_map["sha256"] == assignments_sha256(label_map["assignments"]),
                     a["concurrency_limit"], a["goose_session_id"], req.recipe_path.name))
        return ok(req, cfg)

    run_all(cfg, spawner=spawn)

    assert sorted(s[3] for s in seen) == ["recipe-01.yaml", "recipe-02.yaml", "recipe-03.yaml", "recipe-04.yaml"]
    assert all(sealed and limit == 2 and sid is None for sealed, limit, sid, _ in seen)
    label_map = json.loads((cfg.out_dir / "label-map.json").read_text(encoding="utf-8"))
    body_sha = sha256_text(prompt_body(HERE / "runner-prompt.md"))
    assert all(a["sha256_runner_prompt"] == body_sha for a in label_map["assignments"].values())
    assert label_map["assignments"]["r1"]["goose_session_id"] == "sid-0"
    log = {r["run_id"]: r for r in rows(cfg.out_dir / "latency-log.jsonl")}
    assert all(r["start_ts"] >= label_map["sealed_at"] for r in log.values())
    r1 = log["r1"]
    assert (r1["failure_mode"], r1["goose_session_id"]) == (None, "sid-0")
    assert (r1["input_tokens"], r1["output_tokens"], r1["total_tokens"]) == (10, 5, 15)
    assert (r1["cache_read_tokens"], r1["cache_write_tokens"], r1["cost_usd"]) == (3, 1, 0.0)
    assert r1["thinking_tokens"] is None and r1["thinking_capture"] == "not_captured"
    assert (r1["thinking_blocks"], r1["thinking_chars"]) == (1, 3)
    assert r1["env"] == {"GOOSE_MAX_TURNS": "0", "GOOSE_CONTEXT_LIMIT": None, "GOOSE_PROVIDER": "anthropic"}
    assert log["r2"]["failure_mode"] == "session_not_found"
    tools = rows(cfg.out_dir / "tool-log.jsonl")
    assert [(t["tool"], t["target"]) for t in tools] == [("shell", None), ("read", "src/lib.rs")]
    assert "secret" not in (cfg.out_dir / "tool-log.jsonl").read_text(encoding="utf-8")

def test_find_session_requires_exactly_one_named_row(tmp_path):
    db = make_config(tmp_path, with_db=True).sessions_db
    with sqlite3.connect(db) as conn:
        for sid in ("sid-8", "sid-9"):
            conn.execute("INSERT INTO sessions VALUES (?, 'exp5-dup', 0, 0, 0, 0, 0, 0)", (sid,))

    assert find_session(db, "exp5-r1") == ("sid-0", None)
    assert find_session(db, "exp5-dup") == (None, "session_ambiguous")
    assert find_session(db, "exp5-missing") == (None, "session_not_found")

def test_failed_spawn_records_failure_mode_without_backfill(tmp_path):
    cfg = make_config(tmp_path, with_db=True)

    def failing(req, cfg):
        return SpawnResult(1, "", "Error: provider rejected model", utcnow(), utcnow())

    run_all(cfg, spawner=failing)

    log = rows(cfg.out_dir / "latency-log.jsonl")
    assert len(log) == 4
    assert all(r["failure_mode"] == "goose_exit_1" and r["goose_session_id"] is None for r in log)
    assert all(r["input_tokens"] is None and r["thinking_capture"] == "not_captured" for r in log)
    assert "provider rejected model" in log[0]["detail"]
    assert not (cfg.out_dir / "tool-log.jsonl").exists()

def test_concurrency_is_bounded_and_recorded(tmp_path):
    cfg = make_config(tmp_path, with_db=True)
    lock, state = threading.Lock(), {"current": 0, "peak": 0}

    def slow(req, cfg):
        with lock:
            state["current"] += 1
            state["peak"] = max(state["peak"], state["current"])
        time.sleep(0.05)
        with lock:
            state["current"] -= 1
        return ok(req, cfg)

    summary = run_all(cfg, spawner=slow)

    assert state["peak"] == 2 and len(summary["runs"]) == 4
    label_map = json.loads((cfg.out_dir / "label-map.json").read_text(encoding="utf-8"))
    assert all(a["concurrency_limit"] == 2 for a in label_map["assignments"].values())

def test_stale_recipe_aborts_before_seal(tmp_path):
    cfg = make_config(tmp_path)
    path = cfg.recipes_dir / "recipe-01.yaml"
    recipe = yaml.safe_load(path.read_text(encoding="utf-8"))
    recipe["prompt"] = "edited by hand"
    write_recipe(recipe, path)

    with pytest.raises(SystemExit, match="stale recipes"):
        run_all(cfg, spawner=ok)
    assert not (cfg.out_dir / "label-map.json").exists()

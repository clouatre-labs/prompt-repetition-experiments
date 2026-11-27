#!/usr/bin/env python3
"""Exp5 run harness: validate recipes, seal label-map.json, spawn goose runs with
bounded concurrency in fresh clones, then backfill latency-log.jsonl and
tool-log.jsonl from the goose sessions.db (session resolved by name only)."""

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import yaml

from gen_recipes import PROVIDER, Run, prompt_body, read_plan, recipe_mismatches, sha256_text

REPO_URL = "https://github.com/clouatre-labs/aptu-coder"
PIN = "132ea687e09a916091699a562da3c96c86ec1fd8"
GIT = ["git", "-c", "core.hooksPath=/dev/null"]
# Argument keys that identify a tool call's target; no other argument is ever recorded.
TARGET_KEYS = ("path", "file_path", "filePath", "uri", "url", "libraryName", "library", "query")
TOKEN_COLUMNS = ("input_tokens", "output_tokens", "total_tokens", "cache_read_tokens", "cache_write_tokens")
FACT_KEYS = (*TOKEN_COLUMNS, "cost_usd", "thinking_blocks", "thinking_chars")

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

@dataclass(frozen=True)
class SpawnRequest:
    run: Run
    recipe_path: Path
    clone_dir: Path
    max_turns: int

@dataclass(frozen=True)
class SpawnResult:
    returncode: int | None  # None when the spawn timed out
    stdout: str
    stderr: str
    started: datetime
    finished: datetime

@dataclass
class Config:
    plan: Path
    recipes_dir: Path
    template: Path
    out_dir: Path
    scratch: Path
    sessions_db: Path
    concurrency: int = 2
    max_turns: int = 0  # GOOSE_MAX_TURNS; 0 leaves the goose default
    timeout: float = 0.0  # seconds per goose run; 0 means none
    repo_url: str = REPO_URL
    pin: str = PIN
    goose: str = "goose"
    clone: bool = True
    log_lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

def assignments_sha256(assignments: dict) -> str:
    """Hash of the assignments block with session ids nulled; stays valid after backfill."""
    blinded = {k: {**v, "goose_session_id": None} for k, v in assignments.items()}
    return sha256_text(json.dumps(blinded, sort_keys=True, separators=(",", ":")))

TREE_SUFFIXES = (".py", ".md", ".json", ".toml", ".lock", ".csv")
TREE_EXCLUDED_PARTS = ("__pycache__", ".venv", ".pytest_cache", "tests")

def tree_sha256(root: Path) -> str:
    """sha256 over the sorted included files of a tree: relative posix path + newline + bytes each."""
    root = root.resolve()
    files = sorted(
        p for p in root.rglob("*")
        if p.is_file() and p.suffix in TREE_SUFFIXES and not any(part in TREE_EXCLUDED_PARTS for part in Path(p).parts)
    )
    digest = hashlib.sha256()
    for p in files:
        digest.update(f"{p.relative_to(root).as_posix()}\n".encode("utf-8"))
        digest.update(p.read_bytes())
    return digest.hexdigest()

def seal(runs: list[Run], concurrency_limit: int, prompt_sha256: str) -> dict:
    sealed_at = utcnow().isoformat(timespec="seconds")
    here = Path(__file__).resolve().parent
    sha_scorer, sha_analysis = tree_sha256(here / "scorer"), tree_sha256(here / "analysis")
    assignments = {
        run.run_id: {
            "group": run.group, "model": run.model, "goose_session_id": None, "sealed_at": sealed_at,
            "sha256_runner_prompt": prompt_sha256, "sha256_scorer": sha_scorer, "sha256_analysis": sha_analysis,
            "concurrency_limit": concurrency_limit,
        }
        for run in runs
    }
    return {"sealed_at": sealed_at, "assignments": assignments, "sha256": assignments_sha256(assignments)}

def write_json(path: Path, obj: dict) -> None:
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, allow_nan=False)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)

def append_jsonl(path: Path, row: dict, lock: threading.Lock) -> None:
    with lock, path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, allow_nan=False) + "\n")

def fresh_clone(scratch: Path, run: Run, repo_url: str, pin: str) -> Path:
    clone_dir = scratch / run.run_id / "aptu-coder"
    if clone_dir.exists():
        shutil.rmtree(clone_dir)
    clone_dir.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(GIT + ["clone", "--quiet", "--filter=blob:none", repo_url, str(clone_dir)], check=True, capture_output=True)
    subprocess.run(GIT + ["-C", str(clone_dir), "checkout", "--quiet", "--detach", pin], check=True, capture_output=True)
    return clone_dir

def goose_spawn(req: SpawnRequest, cfg: Config) -> SpawnResult:
    cmd = [cfg.goose, "run", "--recipe", str(req.recipe_path), "--name", f"exp5-{req.run.run_id}",
           "--debug", "--output-format", "json"]
    started = utcnow()
    try:
        proc = subprocess.run(cmd, cwd=req.clone_dir, env=dict(os.environ, GOOSE_MAX_TURNS=str(req.max_turns)),
                              capture_output=True, text=True, timeout=cfg.timeout or None)
    except subprocess.TimeoutExpired as exc:
        text = lambda v: v if isinstance(v, str) else ""
        return SpawnResult(None, text(exc.stdout), text(exc.stderr), started, utcnow())
    return SpawnResult(proc.returncode, proc.stdout, proc.stderr[-2000:], started, utcnow())

def find_session(db_path: Path, name: str) -> tuple[str | None, str | None]:
    """(session_id, failure_mode): the session whose name equals `name`; exactly one row required."""
    with closing(sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)) as conn:
        ids = [r[0] for r in conn.execute("SELECT id FROM sessions WHERE name = ?", (name,))]
    if len(ids) == 1:
        return ids[0], None
    return None, "session_not_found" if not ids else "session_ambiguous"

def session_facts(db_path: Path, session_id: str) -> dict:
    """Token, cache, cost and thinking-block figures plus (tool, target) calls for one session."""
    columns = ", ".join(f"accumulated_{c}" for c in TOKEN_COLUMNS)
    with closing(sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)) as conn:
        row = conn.execute(f"SELECT {columns}, accumulated_cost FROM sessions WHERE id = ?", (session_id,)).fetchone()
        contents = [r[0] for r in conn.execute(
            "SELECT content_json FROM messages WHERE session_id = ? AND role = 'assistant' ORDER BY id", (session_id,))]
    items = []
    for content in contents:
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            continue
        items.extend(i for i in parsed if isinstance(i, dict)) if isinstance(parsed, list) else None
    thinking = [i for i in items if i.get("type") == "thinking"]
    facts = dict(zip(TOKEN_COLUMNS, row))
    facts.update(cost_usd=row[-1], thinking_blocks=len(thinking),
                 thinking_chars=sum(len(str(t.get("thinking") or "")) for t in thinking), tools=[])
    for item in items:
        if item.get("type") == "toolRequest":
            call = item.get("toolCall") or {}
            call = call.get("value") if isinstance(call.get("value"), dict) else call
            args = call.get("arguments") or {}
            target = next((str(args[k]) for k in TARGET_KEYS if isinstance(args.get(k), str)), None)
            facts["tools"].append((call.get("name"), target))
    return facts

def thinking_tokens_in_output(text: str) -> int | None:
    def walk(node):
        if isinstance(node, dict):
            return sum(v if k in ("thinking_tokens", "reasoning_tokens") and isinstance(v, int) else walk(v)
                       for k, v in node.items())
        return sum(walk(i) for i in node) if isinstance(node, list) else 0

    try:
        docs = [json.loads(text)]
    except json.JSONDecodeError:
        docs = []
        for line in text.splitlines():
            try:
                docs.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    total = sum(walk(d) for d in docs)
    return total if total else None

def execute_run(cfg: Config, run: Run, spawner, version: str | None) -> dict:
    failure, session_id, facts, detail = None, None, {}, None
    result = SpawnResult(None, "", "", utcnow(), utcnow())
    try:
        clone_dir = fresh_clone(cfg.scratch, run, cfg.repo_url, cfg.pin) if cfg.clone else cfg.scratch / run.run_id
        clone_dir.mkdir(parents=True, exist_ok=True)
        req = SpawnRequest(run, cfg.recipes_dir / run.recipe_file, clone_dir, cfg.max_turns)
        result = spawner(req, cfg)
        (cfg.scratch / run.run_id / "goose-stdout.txt").write_text(result.stdout, encoding="utf-8")
        code = result.returncode
        failure = "timeout" if code is None else None if code == 0 else f"goose_exit_{code}"
        detail = result.stderr.strip()[-300:] or None
    except subprocess.CalledProcessError as exc:
        failure, detail = "clone_failed", str(exc.stderr)[-300:]
    if failure is None:
        session_id, failure = find_session(cfg.sessions_db, f"exp5-{run.run_id}")
        if failure is None:
            facts = session_facts(cfg.sessions_db, session_id)
            for seq, (tool, target) in enumerate(facts.pop("tools")):
                append_jsonl(cfg.out_dir / "tool-log.jsonl", {"run_id": run.run_id, "goose_session_id": session_id,
                                                              "seq": seq, "tool": tool, "target": target}, cfg.log_lock)
    thinking_tokens = thinking_tokens_in_output(result.stdout)
    row = {
        "run_id": run.run_id, "group": run.group, "model": run.model, "goose_session_id": session_id,
        "start_ts": result.started.isoformat(timespec="seconds"),
        "end_ts": result.finished.isoformat(timespec="seconds"),
        "wall_clock_seconds": int((result.finished - result.started).total_seconds()),
        **{k: facts.get(k) for k in FACT_KEYS},
        "thinking_tokens": thinking_tokens,
        "thinking_capture": "observed" if thinking_tokens is not None else "not_captured",
        "goose_version": version,
        "env": {"GOOSE_MAX_TURNS": str(cfg.max_turns), "GOOSE_CONTEXT_LIMIT": os.environ.get("GOOSE_CONTEXT_LIMIT"),
                "GOOSE_PROVIDER": PROVIDER},
        "exit_code": result.returncode, "failure_mode": failure, "detail": detail,
    }
    append_jsonl(cfg.out_dir / "latency-log.jsonl", row, cfg.log_lock)
    return {"run_id": run.run_id, "group": run.group, "model": run.model, "exit_code": result.returncode,
            "failure_mode": failure, "goose_session_id": session_id}

def run_all(cfg: Config, spawner=goose_spawn) -> dict:
    runs = read_plan(cfg.plan)
    body = prompt_body(cfg.template)
    stale = {}
    for run in runs:
        with (cfg.recipes_dir / run.recipe_file).open(encoding="utf-8") as fh:
            diffs = recipe_mismatches(yaml.safe_load(fh), run, body)
        if diffs:
            stale[run.run_id] = diffs
    if stale:
        raise SystemExit(f"stale recipes, regenerate with gen_recipes.py: {stale}")
    cfg.out_dir.mkdir(parents=True, exist_ok=True)
    cfg.scratch.mkdir(parents=True, exist_ok=True)
    label_map = seal(runs, cfg.concurrency, sha256_text(body))
    write_json(cfg.out_dir / "label-map.json", label_map)  # sealed and closed before the first spawn
    try:
        version = subprocess.run([cfg.goose, "--version"], capture_output=True, text=True, timeout=30).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        version = None
    with ThreadPoolExecutor(max_workers=cfg.concurrency) as pool:
        outcomes = [f.result() for f in [pool.submit(execute_run, cfg, run, spawner, version) for run in runs]]
    for o in outcomes:
        if o["goose_session_id"] is not None:
            label_map["assignments"][o["run_id"]]["goose_session_id"] = o["goose_session_id"]
    write_json(cfg.out_dir / "label-map.json", label_map)
    return {"runs": outcomes}

def main(argv=None) -> int:
    here = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    add = p.add_argument
    add("--plan", type=Path, default=here / "plans/pilot.csv")
    add("--recipes-dir", type=Path, default=here / "recipes")
    add("--template", type=Path, default=here / "runner-prompt.md")
    add("--out-dir", type=Path, default=here)
    add("--scratch", type=Path, required=True, help="untracked dir for clones and goose stdout")
    add("--sessions-db", type=Path, default=Path.home() / ".local/share/goose/sessions/sessions.db")
    add("--concurrency", type=int, default=2)
    add("--max-turns", type=int, default=0, help="GOOSE_MAX_TURNS (0 = goose default)")
    add("--timeout", type=float, default=0.0, help="seconds per goose run (0 = none)")
    add("--goose", default="goose")
    print(json.dumps(run_all(Config(**vars(p.parse_args(argv)))), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

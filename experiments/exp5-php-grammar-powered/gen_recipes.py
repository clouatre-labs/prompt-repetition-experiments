#!/usr/bin/env python3
"""Generate goose recipes for Exp5 from a run-plan CSV (run_id, group, model).

The user `prompt` is the body of runner-prompt.md, byte-verbatim and identical
across arms. The system `instructions` carry the manipulation: control is a
one-liner, treatment is that one-liner plus a second verbatim copy of the body.
"""

import argparse
import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path

import yaml

PROVIDER = "anthropic"
CONTROL_INSTRUCTIONS = "Follow the task instructions given in the initial prompt exactly as written."
OUTPUT_PATH = "exp5-output.json"  # relative to the clone root; never a local path
EXTENSIONS = [
    {"type": "builtin", "name": "developer"},
    {"type": "streamable_http", "name": "context7", "uri": "https://mcp.context7.com/mcp",
     "env_keys": ["CONTEXT7_API_KEY"], "headers": {"Authorization": "Bearer $CONTEXT7_API_KEY"}},
]
# brave_search is deliberately absent: it surfaced upstream #1861 in the first pilot. The task
# needs the grammar docs (Context7) and the pinned clone; web search is a leak path, not a tool.
UNRESOLVED = ("{NN}", "{group}", "{WORKTREE}", "{HEAD_SHA}")

@dataclass(frozen=True)
class Run:
    run_id: str
    group: str
    model: str
    index: int

    @property
    def recipe_file(self) -> str:
        return f"recipe-{self.index:02d}.yaml"

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def read_plan(path: Path) -> list[Run]:
    """Validated runs in row order."""
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not {"run_id", "group", "model"} <= set(rows[0].keys() if rows else ()):
        raise ValueError(f"plan {path} needs columns run_id, group, model")
    seen = set()
    for n, row in enumerate(rows, 1):
        if row["group"].strip() not in ("control", "treatment"):
            raise ValueError(f"plan row {n}: group must be control or treatment")
        if not row["run_id"].strip() or not row["model"].strip():
            raise ValueError(f"plan row {n}: run_id and model are required")
        if row["run_id"].strip() in seen:
            raise ValueError(f"plan row {n}: duplicate run_id {row['run_id'].strip()}")
        seen.add(row["run_id"].strip())
    return [Run(r["run_id"].strip(), r["group"].strip(), r["model"].strip(), i) for i, r in enumerate(rows, 1)]

def prompt_body(template_path: Path, output_path: str = OUTPUT_PATH) -> str:
    """Everything after the `---` line of runner-prompt.md, with `{output_path}` filled in."""
    text = template_path.read_text(encoding="utf-8")
    if "\n---\n" not in text:
        raise ValueError(f"{template_path} has no '---' separator")
    body = text.split("\n---\n", 1)[1].strip("\n").replace("{output_path}", output_path) + "\n"
    if any(token in body for token in UNRESOLVED):
        raise ValueError(f"{template_path} leaves unresolved placeholders")
    if str(Path.home()) in body:
        raise ValueError(f"{template_path} contains an absolute local path")
    return body

def build_recipe(run: Run, body: str) -> dict:
    instructions = CONTROL_INSTRUCTIONS + ("\n\n" + body if run.group == "treatment" else "")
    return {
        "version": "1.0.0",
        "title": f"exp5-{run.run_id}",
        "description": f"exp5-php-grammar-powered run {run.run_id} ({run.group})",
        "settings": {"goose_provider": PROVIDER, "goose_model": run.model, "temperature": 0.5},
        "instructions": instructions,
        "prompt": body,
        "extensions": EXTENSIONS,
    }

def recipe_mismatches(recipe: dict, run: Run, body: str) -> list[str]:
    """Fields where `recipe` differs from what the plan and prompt would generate now."""
    expected = build_recipe(run, body)
    return sorted(k for k in expected if recipe.get(k) != expected[k])

class RecipeDumper(yaml.SafeDumper):
    pass


RecipeDumper.add_representer(str, lambda d, s: d.represent_scalar("tag:yaml.org,2002:str", s, style='"'))

def write_recipe(recipe: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        yaml.dump(recipe, fh, Dumper=RecipeDumper, sort_keys=False, width=float("inf"))

def generate(plan_path: Path, template_path: Path, recipes_dir: Path) -> list[Path]:
    runs = read_plan(plan_path)
    body = prompt_body(template_path)
    paths = [recipes_dir / run.recipe_file for run in runs]
    for run, path in zip(runs, paths):
        write_recipe(build_recipe(run, body), path)
    return paths

def main(argv=None) -> int:
    here = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--plan", type=Path, default=here / "plans/pilot.csv")
    p.add_argument("--template", type=Path, default=here / "runner-prompt.md")
    p.add_argument("--out", type=Path, default=here / "recipes")
    a = p.parse_args(argv)
    for path in generate(a.plan, a.template, a.out):
        print(f"wrote {path}")
    print(f"sha256_runner_prompt {sha256_text(prompt_body(a.template))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

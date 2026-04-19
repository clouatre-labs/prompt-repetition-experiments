"""
Validate schema of experiment analysis.json files.

This script checks that all analysis.json files across experiments contain
the required top-level fields and run records with the expected structure.
Certain fields are nullable (allowed to be None) while others must have values.

Usage:
    uv run python validate_schema.py

Exits with 0 if all files pass validation, 1 if any validation fails.
"""

import json
import sys
import pathlib

# Top-level fields that are allowed to be null/None.
# Note: `bytes` is a run-level field only; it is not listed here.
NULLABLE_FIELDS = {"data_note", "effect_size", "token_analysis"}

def load_analysis(exp_path):
    with open(exp_path) as f:
        return json.load(f)

def check_top_level(data, required_fields):
    missing = []
    for f in required_fields:
        if f not in data:
            missing.append(f)
        elif data[f] is None and f not in NULLABLE_FIELDS:
            missing.append(f)
    return missing

def check_runs(runs, required_run_fields):
    errors = []
    for run_id, rec in runs.items():
        for f in required_run_fields:
            if f not in rec:
                errors.append(f"run {run_id} missing {f}")
            elif rec[f] is None and f not in ('bytes', 'note'):
                errors.append(f"run {run_id} has null {f}")
    return errors

def main():
    base = pathlib.Path('.').resolve()
    exp_paths = sorted((base / 'experiments').glob('*/analysis.json'))
    required_top = [
        'experiment','title','issue','date','model','n_per_group','control_condition','treatment_condition',
        'rubric_version','goose_version','orchestrator_session','repo_head','experiment_start','experiment_end',
        'analyzed_at','runs','scores','statistical_test','conclusion','pre_acknowledged_limitations'
    ]
    required_run = ['group','goose_session_id','messages','input_tokens','output_tokens','total_tokens','wall_clock_seconds','bytes']
    all_ok = True
    for p in exp_paths:
        try:
            data = load_analysis(p)
        except Exception as e:
            print(f"Failed to load {p}: {e}")
            all_ok = False
            continue
        missing = check_top_level(data, required_top)
        if missing:
            print(f"{p} missing top-level fields: {missing}")
            all_ok = False
        runs = data.get('runs',{})
        run_errors = check_runs(runs, required_run)
        if run_errors:
            print(f"{p} run errors: {run_errors}")
            all_ok = False
    sys.exit(0 if all_ok else 1)

if __name__ == '__main__':
    main()

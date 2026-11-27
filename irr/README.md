# Inter-Rater Reliability (IRR) Validation Data

This directory contains IRR validation data produced as part of the companion paper submission, plus a second-judge check for the exploratory Experiment 4.

## Stratified Sample (Exp1 to Exp3)

- **5 sessions**, **33 criteria** total
- Exp1: 2 sessions x 6 criteria = 12
- Exp2: 2 sessions x 7 criteria = 14
- Exp3: 1 session x 7 criteria = 7

## Judges

- **Judge 1**: Claude Haiku 4.5 (primary scorer, blind scoring of all 30 sessions)
- **Judge 2**: Claude Sonnet 4.6 (retrospective validation, temperature=0.0)

## Kappa Computation

Cohen's kappa is computed via `sklearn.metrics.cohen_kappa_score`.

## Results

- Per-criterion agreement: 100% (33/33), kappa_criteria = 1.00
- Session-level kappa is undefined due to a ceiling effect (all 5 sessions pass for both judges)

## How to Re-Run

1. Set the `ANTHROPIC_API_KEY` environment variable
2. Run `python rescore.py` from the `irr/` directory
3. Output overwrites `scores.json`

## Experiment 4 Second-Judge Check (exploratory, non-confirmatory)

`rescore.py` accepts three optional arguments. With none, it keeps the legacy behaviour above.

| Argument | Default | Meaning |
|---|---|---|
| `--experiment <dir>` | none | Experiment directory. Enables blind second-judge mode. |
| `--scores <file>` | `scores-main-run.json` | Judge 1 scores file, resolved relative to the experiment directory. |
| `--out <file>` | `irr/exp4-scores.json` | Output file for `--experiment` mode. |

### Sampling

All 10 main-run sessions of `experiments/exp-swift-grammar-mercury` (runs 07 to 16, n=5+5) are scored. Pilot rounds 01 to 06 are not included.

### Judge 2 inputs

One API call per session (`claude-sonnet-4-6`, temperature 0.0). The prompt contains only the rubric criteria and the content of `sessions/<run_id>.json`. The `run_id` and `group` fields are removed from the session content before it is sent. Judge 1 scores, totals, group and condition are never included, and `rescore.py` does not read `label-map.json`. Criteria come from the rubric tables: `rubric.md` for C1, C2, C6 and `rubric-v3.md` for C3, C4, C5, C7. The rubric source files are recorded in the output metadata.

Unlike the legacy mode, Experiment 4 mode has no Judge 1 fallback. A missing `ANTHROPIC_API_KEY`, a missing key in the scores file, an API error or a response that is not a JSON object with a binary value for every criterion exits non-zero and writes no output.

### Statistics

Judge 1 and Judge 2 vectors are compared per criterion across the 10 sessions. If either vector is constant, kappa is undefined: the criterion is listed under `constant_pair_criteria` with the distinct values of both vectors. The remaining criteria get Cohen's kappa under `per_criterion_kappa`, and the pooled kappa is computed over those non-constant criteria only. Session-level pass/fail (pass = at least 50% of criteria) agreement is reported separately.

### How to Re-Run

From the repository root (no `pyproject.toml`; the anthropic 0.x line is pinned because the 1.x and 2.x SDKs no longer accept `temperature`):

```bash
uv run --no-project --with "anthropic<1" --with scikit-learn irr/rescore.py \
  --experiment experiments/exp-swift-grammar-mercury \
  --scores scores-main-run.json --out irr/exp4-scores.json
```

### Results (`exp4-scores.json`)

**Second-judge agreement is poor: 20% session-level agreement, kappa 0.00.** Judge 1's Exp4 scores, C5 in particular, are not reliable measurements. The Exp4 pass rates and the 4.2 vs 4.0 means must not be interpreted as evidence in either direction.

- Judges agreed on 60 of 70 criterion decisions (85.7%). Every disagreement is a Judge 2 fail where Judge 1 passed: C5 in 8 sessions, C3 in 1, C4 in 1.
- `per_criterion_kappa` is empty and pooled kappa is `null`: for every one of the 7 criteria at least one judge's vector is constant across sessions (Judge 1: C1, C2, C3, C5, C6, C7; Judge 2: C1, C2, C4, C6, C7).
- Session-level pass/fail: Judge 1 passes 10/10, Judge 2 passes 2/10; agreement 20%, kappa 0.00.
- Judge 2 scored the session output file rather than a transcript, and the rubric was not inter-rater checked before the main run, so these numbers describe this rubric and this output format only.

What would be needed before the Exp4 scores could be used: a rubric revision agreed by both judges, followed by a re-score of the 10 sessions under the revised rubric. No score or data file has been changed on the basis of this check.

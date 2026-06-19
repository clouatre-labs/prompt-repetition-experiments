# Inter-Rater Reliability (IRR) Validation Data

This directory contains IRR validation data produced as part of the companion paper submission.

## Stratified Sample

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
# Exp5 HEADROOM pilot (pre-registered template)

Status: template. Pilot sessions arrive with #103; nothing below is filled in and no sessions or scores exist yet.

## Pre-registration

Before any pilot session is scored, the following are fixed:

- Scorer: `experiments/exp5-php-grammar-powered/scorer` at the commit that lands with #101, with its `uv.lock` unchanged.
- Rubric: `exp5-rubric-v1-fractional` (C3 to C7 fractional in `[0,1]`, `total = C3 + C4 + C5 + C6 + C7`, max 5.0; C1/C2 copied verbatim or `null`).
- Headroom criterion: a criterion is considered to have headroom when between-run variance across the pilot is above 0 and no run saturates at 1.0.
- Command: `uv run scorer.py <sessions-dir> --out scores-pilot.json` then `uv run scorer.py --report-variance <sessions-dir>`.

## Measurements (to fill)

| Criterion | n | min | max | mean | variance | Saturated at 1.0 | Headroom |
|-----------|---|-----|-----|------|----------|------------------|----------|
| C3 | | | | | | | |
| C4 | | | | | | | |
| C5 | | | | | | | |
| C6 | | | | | | | |
| C7 | | | | | | | |
| C7.workspace_dependency | | | | | | | |
| C7.unconditional_dependency | | | | | | | |
| C7.extension_map_entry | | | | | | | |
| C7.mod_registration | | | | | | | |
| C7.match_arms | | | | | | | |

## Decision (to fill)

- Criteria with headroom:
- Criteria without headroom and the follow-up (rubric wording vs. scorer rule):
- Date and scorer commit:

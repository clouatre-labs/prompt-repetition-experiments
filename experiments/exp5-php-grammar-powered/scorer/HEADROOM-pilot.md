# Exp5 HEADROOM pilot (pre-registered template)

Status: filled from the 2026-11-27 pilot (4 runs, goose 1.61.1, no turn cap). Gate verdict: CEILING (claude-haiku-5-5 control_mean 4.0476 > 3.5; see Decision).

## Pre-registration

Before any pilot session is scored, the following are fixed:

- Scorer: `experiments/exp5-php-grammar-powered/scorer` at the commit that lands with #101, with its `uv.lock` unchanged.
- Rubric: `exp5-rubric-v1-fractional` (C3 to C7 fractional in `[0,1]`, `total = C3 + C4 + C5 + C6 + C7`, max 5.0; C1/C2 copied verbatim or `null`).
- Headroom criterion: a criterion is considered to have headroom when between-run variance across the pilot is above 0 and no run saturates at 1.0.
- Command: `uv run scorer.py <sessions-dir> --out scores-pilot.json` then `uv run scorer.py --report-variance <sessions-dir>`.

## Measurements (to fill)

Source: `uv run scorer.py --report-variance` over h45-control, h45-treatment, h55-control, h55-treatment (`scores-pilot.json`, scored_at 2026-11-27T16:40:00Z).

| Criterion | n | min | max | mean | variance | Saturated at 1.0 | Headroom |
|-----------|---|-----|-----|------|----------|------------------|----------|
| C3 | 20 | 0.0 | 1.0 | 0.15 | 0.1275 | yes (3 of 4 runs) | no (saturates) |
| C4 | 20 | 0.0 | 1.0 | 0.1674 | 0.1142 | yes (1 of 4 runs) | no (saturates) |
| C5 | 20 | 0.0 | 1.0 | 0.1 | 0.0567 | yes (1 of 4 runs) | no (saturates) |
| C6 | 20 | 0.0 | 1.0 | 0.2 | 0.16 | yes (4 of 4 runs) | no |
| C7 | 20 | 0.0 | 1.0 | 0.2 | 0.16 | yes (4 of 4 runs) | no |
| C7.workspace_dependency | 4 | 1.0 | 1.0 | 1.0 | 0.0 | yes (4 of 4 runs) | no |
| C7.unconditional_dependency | 4 | 1.0 | 1.0 | 1.0 | 0.0 | yes (4 of 4 runs) | no |
| C7.extension_map_entry | 4 | 1.0 | 1.0 | 1.0 | 0.0 | yes (4 of 4 runs) | no |
| C7.mod_registration | 4 | 1.0 | 1.0 | 1.0 | 0.0 | yes (4 of 4 runs) | no |
| C7.match_arms | 4 | 1.0 | 1.0 | 1.0 | 0.0 | yes (4 of 4 runs) | no |

Per-run totals (5.0 scale): h45-control 3.1333 (C3 0.0, C4 0.8, C5 0.3333, C6 1.0, C7 1.0); h45-treatment 4.1667 (1.0, 0.8333, 0.3333, 1.0, 1.0); h55-control 4.0476 (1.0, 0.7143, 0.3333, 1.0, 1.0); h55-treatment 5.0 (1.0, 1.0, 1.0, 1.0, 1.0).

## Decision (to fill)

- Criteria with headroom: none under the pre-registered rule (variance > 0 and no run at 1.0). The closest are C4 (run-level 0.7143 to 1.0, saturates only in h55-treatment) and C5 (0.3333 in three runs, 1.0 in h55-treatment); both have variance > 0 but one run saturates.
- Criteria without headroom and the follow-up (rubric wording vs. scorer rule):
  - C6, C7 and all five C7 sub-criteria: 1.0 in every run, variance 0. These are ceiling effects from the rubric wording (the runner prompt enumerates each wiring fact literally, so every model copies it); follow-up is rubric wording, not the scorer rule.
  - C3: 0.0 in h45-control and 1.0 in the other three. The 0 is "0/6 declaration kinds matched on the fixture corpus; fewer than 3 patterns" (the draft compiles but captures nothing); the other three runs score 6/6. Follow-up is rubric wording (the prompt does not require naming the node kinds in the draft) rather than the scorer rule.
  - C5: 0.3333 in three runs is "defuse query compiles; write captures=0, read captures=0", i.e. credit for compilation only; h55-treatment scores 6 write and 7 read captures. Follow-up is scorer rule granularity (compilation is 1 of 3 sub-checks and is free).
  - Caveat: two runs touched issue 1861 (the closed predecessor of #1864) despite the prompt naming only #1864: h45-control via a brave_search response, h55-treatment by an explicit `gh issue view 1861`. h55-treatment is the only run at 5.0 and the only C4/C5 saturation, so its scores may not be blind.
- Gate arithmetic (band [1.5, 3.5] on the 5.0 scale, n = 1 per arm):
  - claude-haiku-4-5: control_mean 3.1333, treatment_mean 4.1667; mean cost per run 0.3293 USD.
  - claude-haiku-5-5: control_mean 4.0476, treatment_mean 5.0; mean cost per run 0.1623 USD.
  - claude-haiku-4-5 control_mean 3.1333 is in [1.5, 3.5]; claude-haiku-5-5 control_mean 4.0476 is above 3.5. No run has a failure_mode; no model exceeds 2.00 USD per run. Verdict: CEILING (claude-haiku-5-5 control_mean > 3.5).
  - Criteria saturated at 1.0 in a control run: C3 (h55-control), C6 (both), C7 (both) and all five C7 sub-criteria (both). Across the whole pilot C6, C7 and every C7 sub-criterion are 1.0 in all 4 runs; h55-treatment also saturates C3, C4 and C5 (total 5.0).
- Date and scorer commit: 2026-11-27, scorer commit 2011ad0.

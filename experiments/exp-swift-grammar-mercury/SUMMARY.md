# Pilot Summary: exp-swift-grammar-mercury

Exploratory pilot (not part of the paper's confirmatory series). Delegate
model: `inception/mercury-2.5-preview` via OpenRouter, run through Goose
1.49.0. Target: `clouatre-labs/aptu-coder#648` ("add Swift grammar support"),
pinned at `c3d3669c50f14ea0214f1edb4d0f9abb1d8324ac` (origin/main HEAD).
n=2 pilot only (run 01 = control, run 02 = treatment); blind-scored by a
fresh Claude Haiku 4.5 agent against `rubric.md`, with no access to
`label-map.json`.

## Per-criterion pass rate (n=1 per group; pilot only, not statistically
meaningful)

| ID | Control (run 01) | Treatment (run 02) |
|----|:---:|:---:|
| C1 | 0/1 | 0/1 |
| C2 | 0/1 | 0/1 |
| C3 | 0/1 | 0/1 |
| C4 | 0/1 | 0/1 |
| C5 | 0/1 | 0/1 |
| C6 | 0/1 | 0/1 |
| C7 | 0/1 | 0/1 |
| **Total** | **0/7** | **0/7** |

## Zero-in-both-groups check

**All 7 of 7 criteria** scored 0 in both the control and treatment run. This
is a stricter failure than Exp3, where 3 of 7 criteria (C1, C5, C6) hit
0/10 in both groups while C2-C4 and C7 showed mixed or full credit. Here
every criterion collapsed to zero, including C7, the criterion designed to
be the "easy" verification-only check.

**This trips a gate the pre-registered pilot design did not anticipate.**
The bookend's stated pilot gate only covers a ceiling effect (both runs
>=6/7 -> harden the rubric). A total floor effect (both runs 0/7) has no
defined stopping rule, but it is at least as strong a signal that something
in the rubric-runner-model combination is broken before any further spend.
Per the plan, the full n=5+5 run does not proceed without your review of
this result.

## Diagnostic: is the 0/7-in-both-runs a rubric-authoring error?

Comparing `rubric.md`'s C3, C4, C7 wording against Exp3's actual originals
(`exp3-kotlin-grammar/rubric.md`) surfaced a real authoring mistake: for
these three criteria I added a clause Exp3's precedent never required --
an explicit demand that the delegate cite/model on an existing reference
file (`java.rs`, `kotlin.rs`, the `"css"` pattern) on top of correctly
describing Swift's own grammar mechanics. Exp3's originals only ever asked
whether the *target* grammar was correctly described.

To quantify how much of the floor effect this explains, both runs were
re-scored (`scores-v2-diagnostic.json`, `rubric-v2-diagnostic.md`) with
C3/C4/C7 restored to Exp3-equivalent wording (citation-of-reference-file
clause removed) and C1/C2/C5/C6 unchanged. This is a post-hoc diagnostic
only -- it does not alter the sealed `rubric.md` or the official
`scores.json`.

| Run | Original (`scores.json`) | Diagnostic (`scores-v2-diagnostic.json`) |
|-----|:---:|:---:|
| scout-run-01 (control) | 0/7 | 1/7 (recovers C7) |
| scout-run-02 (treatment) | 0/7 | 0/7 (unchanged) |

The rubric-authoring mistake accounts for only 1 point out of 14 possible.
Even under Exp3's own, looser bar, C1-C6 remain 0/2 in both runs: neither
run ever names a specific Swift node field (e.g. `name`, `declaration_kind`)
alongside a query constant, describes the `inheritance_specifier` ->
`inherits_from` field walk, or independently verifies anything against an
external manifest or grammar source -- both runs consistently restate the
issue's own prose instead. **The floor effect is therefore mostly a real
finding about the delegate, not a broken rubric or a broken pipeline.**

## Assessment: general co-design risk, or specific to this rubric?

Both runs' outputs are coherent, correctly-scoped research summaries --
they name the right files (`java.rs`, `mod.rs`, `lang.rs`, `Cargo.toml`),
correctly state the `defuse_query` mandatory-field fact, and (run 02 only)
correctly reference `kotlin.rs` as a structural analogue. What they never
do, in either run, is reproduce a literal artifact: an actual tree-sitter
query string, an actual struct field citation with surrounding code, or a
concrete Swift test snippet. The rubric (deliberately, per the
RUBRIC-AUTHORING requirement carried over from Exp3's C1/C5/C6 postmortem)
scores a criterion 0 whenever it is satisfied only by naming/describing
rather than by citing/reproducing.

That points to a **structural mismatch between the JSON output schema and
the rubric's evidentiary bar**, and this generalizes beyond this one
rubric: the schema (`relevant_files`, `conventions`, `patterns`,
`approaches`, `recommendation`) is a research-summary format with no field
that asks for a literal query string, a literal struct excerpt, or a
literal test snippet. Exp3 hit the same wall for 3 criteria because its
Kotlin rubric happened to demand literal citation for exactly those 3;
this pilot's rubric demanded it for all 7, so the same schema/rubric gap
now shows up everywhere instead of in a subset. In other words: the root
cause Exp3 diagnosed (a runner-prompt/schema that doesn't force literal
artifact production) is the same root cause here, just applied more
uniformly -- this looks like a genuine, generalizable rubric-runner
co-design risk, not an accident specific to Exp3's Kotlin wording.

A second, confounded factor: `mercury-2.5-preview` completed both runs in
15-28 seconds with only ~4-5K output tokens and a single-pass style (no
multi-turn refinement visible in either transcript), which is a much
shallower engagement than Exp3's Haiku 4.5 delegates. Whether the zero
score reflects the schema gap, the model's shallower engagement, or both
cannot be separated with n=1 per group -- this is exactly the ambiguity a
2-run pilot is supposed to surface before spending the full n.

## Limitations

- The rubric (`rubric.md`) is newly authored for this pilot and unvalidated
  -- no inter-rater check was run, unlike the paper-wide kappa=1.00 result
  (paper.tex:460, second judge Sonnet 4.6 over 5 stratified sessions). This
  pilot's single-Haiku-judge score should not be read with that reliability
  in mind.
- Not statistically comparable to Exp3's Haiku 4.5 baseline on
  `code-analyze-mcp#649` -- different issue, different codebase, different
  delegate model and provider.
- Single model (`inception/mercury-2.5-preview`), single temperature (0.5),
  single issue. n=2 total, not n=5+5. No significance test was run or is
  appropriate at this n.
- Goose version used here (1.49.0) differs from the 1.31.1 used for Exp3
  (paper.tex:458) -- a known confound source. This version difference is
  also why this pilot needed corrected recipe syntax: the `settings:` block
  keys are `goose_provider`/`goose_model` in 1.49.0, not `provider`/`model`
  as originally drafted -- confirmed by reading the installed Settings
  struct in the local goose source and by a smoke test before any pilot
  spend. The pinned SHA was also corrected mid-session: the originally
  proposed SHA was the tip of an unpushed local branch, not reachable from
  a fresh clone of `origin`; the pilot instead pins `origin/main` HEAD.
- `brave_search` access was not restricted (consistent with Exp3's own
  Kotlin pilot); the treatment run used it 3 times with generic queries
  ("tree-sitter-swift 0.7.3 grammar API", "aptu-coder issue 648 swift
  tree-sitter") while the control run used it 0 times. No evidence either
  query surfaced a leaked answer (issue #648 has no discussion thread and
  no third-party source would reference this private repo's issue number),
  but the residual risk of a third-party tree-sitter-swift query example
  surfacing is an unmeasured confound, same as in Exp3.

## Round 2: runner-prompt fix (chosen direction) and what it revealed

You chose option 2 above (force literal artifacts via the runner-prompt).
`runner-prompt-v2.md` adds a required Step 7 ("Produce Literal Artifacts")
and five new output fields (`language_info_struct_citation`,
`element_query_draft`, `defuse_query_draft`, `inheritance_walk_citation`,
`test_snippets`) demanding literal quoted text instead of descriptions.
Two fresh runs (scout-run-03 control, scout-run-04 treatment; same target,
same pinned SHA) were spawned with the new prompt. Both now produce real
content: a verbatim `LanguageInfo` struct, real tree-sitter query syntax,
concrete Swift test snippets.

**Scored against the original, unchanged `rubric.md`, both runs still came
back 0/7** -- but the per-criterion justifications this time all pointed at
the same specific cause: C3, C4, C5, and C7 were each marked wrong only for
lacking an additional citation of an unrelated internal reference file
(`java.rs`, `kotlin.rs`, the `"css"` pattern) that I had required by name in
those four criteria's wording -- and that Exp3's own original criteria never
required. My round-1 diagnostic (above) had caught this for C3/C4/C7 but
**missed that C5 carried the identical added clause**; round 2 is what
surfaced that omission.

`rubric-v3.md` corrects C3, C4, C5, and C7 for real (C1, C2, C6 unchanged,
since those require citation of *external* sources or the delegate's own
concrete artifacts, not an unrelated internal file, and were never part of
this bug). Re-scoring the same two round-2 outputs against C1/C2/C6 from
`rubric.md` + C3/C4/C5/C7 from `rubric-v3.md` (`scores-round2-v3.json`):

| Run | C1 | C2 | C3 | C4 | C5 | C6 | C7 | Total |
|-----|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| scout-run-03 (control) | 0 | 0 | 1 | 1 | 1 | 0 | 0 | 3/7 |
| scout-run-04 (treatment) | 0 | 0 | 1 | 1 | 1 | 0 | 0 | 3/7 |

**The floor effect is gone**, and the remaining zeros now have clear,
sensible causes instead of looking like a broken pipeline:
- **C1, C2** (0/2 both): genuinely hard by design and unchanged from
  round 1 -- neither run ever fetches the actual tree-sitter-swift
  Cargo.toml or the grammar's `node-types.json`/`grammar.js`, despite Step
  4 asking for it. This matches Exp3's own pattern (C1 was 0/10, C2 was
  1/10 there too) -- a real, expected floor, not a bug.
- **C6** (0/2 both): a genuine gap in `runner-prompt-v2.md`'s Step 7 spec,
  not the model or the rubric -- `test_snippets` only asked for one example
  per `declaration_kind`, never for the inheritance-shape variants (single
  superclass, multiple protocols, mixed) that C6 also requires. Fixable by
  extending Step 7 in a v3 runner-prompt.
- **C7** (0/2 both): the five wiring facts are individually mentioned across
  scattered fields in both runs but never assembled into one place; a
  dedicated Step 8 asking the delegate to enumerate all five together
  would likely fix this, similar to how Step 7 fixed C3/C4/C5.

Both runs tied at 3/7 exactly -- unsurprising and not meaningful at n=1 per
group; this round-2 pilot is a mechanics check, not evidence about the
prompt-repetition effect itself.

## Round 3: runner-prompt fix for C6/C7 and what it revealed

You chose option 1 from round 2's recommendation (tighten the runner-prompt
further rather than proceed straight to n=5+5). `runner-prompt-v3.md`
extends `runner-prompt-v2.md`'s Step 7 with two changes targeting the two
round-2 gaps directly:

- `test_snippets` now requires >=8 entries (5 `declaration_kind` entries,
  unchanged, plus 3 new `inheritance_shape` entries: single superclass,
  multiple protocols, mixed), each tagged with a `dimension` field.
- A new required `wiring_summary` object consolidates all 5 C7 wiring facts
  (`workspace_dependency`, `unconditional_dependency`, `extension_map_entry`,
  `mod_registration`, `match_arms`) in one place.

Two fresh runs (scout-run-05 control, scout-run-06 treatment; same pinned
SHA, same delegate/settings) were spawned with the new prompt and blind-
scored by a fresh Haiku judge against the same standard as round 2
(`rubric.md` C1/C2/C6 + `rubric-v3.md` C3/C4/C5/C7), with no access to
`label-map.json` (`scores-round3.json`):

| Run | C1 | C2 | C3 | C4 | C5 | C6 | C7 | Total |
|-----|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| scout-run-05 (control) | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 5/7 |
| scout-run-06 (treatment) | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 5/7 |

**Both targeted fixes worked.** C6 and C7 flip from 0/2 to 2/2 in this
round, and the judge's justifications confirm the mechanism: both runs now
produce 8 `test_snippets` covering all 5 declaration kinds and all 3
inheritance shapes, and both now state all 5 wiring facts together in
`wiring_summary`. C1 and C2 remain 0/2 in both runs, exactly as expected --
neither run cites the actual tree-sitter-swift Cargo.toml manifest or the
grammar's `node-types.json`/`grammar.js` field definition, the same genuine,
by-design-hard gap noted in round 2 and consistent with Exp3's own pattern
(C1 0/10, C2 1/10 there). C3, C4, C5 remain 1/1 in both runs, unchanged from
round 2.

Both runs tied at 5/7 exactly -- again unsurprising and not meaningful at
n=1 per group; this round-3 pilot is a mechanics check on the runner-prompt
fix, not evidence about the prompt-repetition effect itself. No criterion
hit ceiling (10/10 would require both runs at 7/7; the highest either run
reaches is 5/7), so no ceiling-effect gate is tripped.

## Status and recommendation

The instrument now behaves as intended across all 7 criteria: `rubric-v3.md`
grades without requiring the wrong citation, and `runner-prompt-v3.md`
successfully elicits every literal artifact the rubric asks for except the
two that require independently fetching an external source document (C1,
C2) -- a real, by-design floor rather than a runner-prompt defect. Both
pilot rounds this instrument has been tested against land both groups at an
identical total (3/7 in round 2, 5/7 in round 3), which is expected at n=1
per group and carries no signal about the prompt-repetition effect itself.

**Recommendation: proceed to the full n=5+5** with `runner-prompt-v3.md` +
(`rubric.md` for C1/C2/C6, `rubric-v3.md` for C3/C4/C5/C7), expecting C1/C2
to floor near 0 in both groups by design and C3-C7 to have headroom to show
a between-group difference, if one exists, at n=5.

This decision is left to you. Total spend so far: 6 Goose delegate runs (3
pilot rounds x 2 runs), well within the pre-registered pilot budget. Per the
pre-registered pilot-gate policy, the full n=5+5 run (scout-run-07 through
scout-run-16) does not proceed without your explicit approval of this
round-3 result.

## Full n=5+5 run (scout-run-07 through scout-run-16)

You approved proceeding after round 3. `label-map.json`'s `main_run` block
was sealed before any run 07 spawn: control = {07,09,11,13,15}, treatment =
{08,10,12,14,16}, interleaved. Same pinned SHA, same
`runner-prompt-v3.md`, same rubric combination (`rubric.md` C1/C2/C6 +
`rubric-v3.md` C3/C4/C5/C7). All 10 runs were blind-scored in a single pass
by a fresh Haiku judge with no access to `label-map.json`
(`scores-main-run.json`).

### Delegate reliability note (new finding this round)

Two of the ten run slots (scout-run-13, scout-run-15) failed on their first
attempt with the same pathology: the delegate got stuck issuing an
identical tool call repeatedly (`ls -la` on the worktree root; a fixed
`brave_web_search` query) instead of progressing, until it either exhausted
the model's 260K-token context window (run 13's first attempt) or was
manually interrupted (both first attempts). Neither pilot round (4 runs
total, rounds 1-3) showed this failure mode. Run 13 needed two retries (its
first two attempts both looped -- once via `ls -la`, once via
`brave_web_search` -- before a third attempt succeeded normally); run 15
needed one retry. Both eventual successful attempts look ordinary (32-167s,
comparable token counts to the other 8 runs). This is a genuine reliability
characteristic of `mercury-2.5-preview` at this temperature/task, not an
artifact of the recipe generation (the failing recipes were diffed
byte-for-byte against successful same-group recipes, differing only in the
run-number substitution). Retries were treated as replacing the failed
attempt outright -- the scored `scout-run-13.json`/`scout-run-15.json`
outputs are each that run's first *successful* completion, not an average
or a choice among attempts.

### Per-criterion pass rate (n=5 per group)

| ID | Control (n=5) | Treatment (n=5) | Combined (n=10) |
|----|:---:|:---:|:---:|
| C1 | 0/5 | 0/5 | 0/10 |
| C2 | 0/5 | 0/5 | 0/10 |
| C3 | 5/5 | 5/5 | 10/10 |
| C4 | 1/5 | 0/5 | 1/10 |
| C5 | 5/5 | 5/5 | 10/10 |
| C6 | 5/5 | 5/5 | 10/10 |
| C7 | 5/5 | 5/5 | 10/10 |
| **Mean total** | **4.2/7** | **4.0/7** | **4.1/7** |

Per-run totals in run order (07-16): 4, 4, 4, 4, 4, 4, 5, 4, 4, 4.

### Zero/ceiling check

**C1 and C2 are 0/10 in both groups** -- a floor, exactly as expected by
design (see rubric.md's own note) and consistent with every prior round of
this experiment and with Exp3's own C1 pattern. **C3, C5, C6, and C7 are
10/10 in both groups** -- a ceiling on 4 of 7 criteria. This is the
ceiling-effect signal the pre-registered pilot gate anticipated (though
framed there as "both runs >=6/7"; here it shows up criterion-by-criterion
instead of at the total-score level, since C1/C2's floor caps every run's
total at 5/7 max). **C4 is 1/10**, passing only in scout-run-13 (control) --
functionally a floor with a single outlier, not evidence of a group
difference at this n.

### Assessment

The two groups are indistinguishable on this rubric at n=5 per group: mean
totals differ by 0.2/7 (4.2 vs 4.0), and every criterion except C4 is
identical between groups (either 5/5 or 0/5 in both). C4's 1-vs-0 split
is a single data point in a 5-run group and carries no statistical
weight -- it is not a signal of a prompt-repetition effect, self-repeated
or otherwise. Practically, the rubric-runner-model combination has
converged to a state where 4 of 7 criteria are guaranteed hits
(C3/C5/C6/C7, driven directly by the forced literal-artifact and
wiring-summary structure in `runner-prompt-v3.md`) and 2 of 7 are
guaranteed misses (C1/C2, requiring an external-source fetch the delegate
never performs) regardless of self-repetition. The one criterion with any
observed variance (C4) shows no group pattern beyond a single outlier. At
this n, sample size, and this rubric's current headroom (effectively 1
of 7 criteria carrying any variance at all), this pilot-scale run does not
support a conclusion about whether prompt self-repetition helps, hurts, or
does nothing for this task -- it is consistent with "no detectable effect
on this instrument," but the instrument itself has very little room left
to show an effect even if one existed.

### Limitations

- The rubric (`rubric.md`, `rubric-v3.md`) was newly authored across 3
  revision rounds specifically for this experiment and was not
  independently inter-rater-checked, unlike the paper-wide kappa=1.00
  result (paper.tex:460, second judge Sonnet 4.6 over 5 stratified
  sessions). A single Haiku judge scored all 10 runs in one pass; no second
  judge or adjudication step was run.
- Not statistically comparable to Exp3's Haiku 4.5 baseline on
  `code-analyze-mcp#649` -- different issue, different codebase, different
  delegate model and provider.
- Single model (`inception/mercury-2.5-preview`), single temperature (0.5),
  single issue, single target repository. n=5+5 (10 total across the main
  run, 16 total including the 3 pilot rounds). No significance test was
  run or is appropriate at this n -- results are reported descriptively
  only, per the pre-registered exploratory design.
- Goose version used here (1.49.0) differs from the 1.31.1 used for Exp3
  (paper.tex:458), a known confound source (see round-1 notes above for
  the specific `settings:` schema difference this caused).
- `brave_search` access was not restricted (consistent with Exp3's own
  Kotlin pilot and with rounds 1-3 of this experiment).
- Two of the ten main-run slots required retries due to a delegate-side
  repeat-tool-call failure mode not observed in the 4 pilot runs (see
  reliability note above). Only the final successful attempt per slot was
  scored; the failed attempts (which never produced an output file) are
  not part of the scored dataset, but their existence is itself a data
  point about this delegate's reliability on this task that a future,
  larger run should account for (e.g., budget for retries, or treat a
  stuck-loop failure as a scorable "0/7, non-completion" outcome rather
  than silently retrying it away).

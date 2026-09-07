# Future Experiment Protocol (v2)

Template for any experiment run after Experiment 3 (`exp3-kotlin-grammar`), incorporating
lessons from an internal, unpublished pilot (`experiments/exp-swift-grammar-mercury/`,
not part of `METHODOLOGY.md` or the paper's confirmatory series) and directly addressing
`paper.tex`'s Future Work section (§Future Work: n>=20 replication, multi-judge ICC, other
model tiers). This document does not itself report results -- it is a checklist to run
*before* spawning delegate 1 of a new experiment.

## Why this exists

The pilot surfaced six failure modes not previously documented in `METHODOLOGY.md`'s
Known Limitations: a rubric that was frozen only after being tuned across three
read-score-revise cycles on real data; a single judge whose one asymmetric criterion
call turned out to be a superficial phrase-match rather than a substantive difference;
a runner-prompt so tightly mirrored to the rubric that four criteria passed by template
compliance rather than capability; delegate self-reported process metadata that
contradicted the orchestrator's own measurements by an order of magnitude; a delegate
failure mode (repeat-tool-call stuck loop) silently discarded via retry rather than
scored; and a model/provider/framework swap treated as comparable to the existing
series when it wasn't. None of this pilot's C1-C7 results are usable, but the failure
modes are, and this protocol exists to close them off before they recur.

## 1. Delegate model selection

- **Confirm reasoning status before allocating any budget.** The treatment mechanism
  under test (Leviathan et al. 2025's `<QUERY><QUERY>` effect) is specific to
  non-reasoning models attending to the full duplicated prompt in a single causal
  pass (`paper.tex` §Mechanism Mismatch). A model that performs extended chain-of-thought
  reasoning by default is testing a different regime; if such a model is used, its
  reasoning effort must be verifiably set to off/minimal for the run, and this setting
  must be recorded in the protocol. Verify the model's reasoning classification against
  its provider documentation, not from assumption -- e.g. a fast/cheap-tier model is not
  automatically a non-reasoning model.
- **Smoke-test genuine multi-turn engagement before pilot spend.** Run one throwaway
  delegate call and check the *orchestrator-measured* session turn count (via the Goose
  `sessions.db`, not the delegate's self-reported `message_count`). A model that
  completes in a single message on an agentic research task is not exercising the tool-use
  loop the experiment is meant to evaluate, regardless of the treatment condition.
- **Any swap of delegate model, provider, or Goose version is a new, non-comparable
  experiment line.** Do not frame it as an extension of Experiments 1-3; report it
  separately with its own baseline.

## 2. Pre-registration timeline

- The rubric must be locked before the *first* pilot run, not merely before the
  confirmatory n-per-group run. If a pilot run reveals the rubric doesn't work, the
  correct response (per the existing pilot-gate policy, see `exp3-kotlin-grammar/protocol.md`)
  is to hold the pilot outputs as scored evidence, swap the target task/issue, or
  publish a v2 protocol amendment with a new timestamp and a rationale -- never to
  edit criterion wording using knowledge of that pilot's own scores and reuse the same
  pilot data downstream.
- `label-map.json` is sealed, and its seal timestamp recorded, before any delegate spawn,
  exactly as in Experiment 3.

## 3. Rubric-runner alignment (two-sided check)

- Compute the alignment score $A = k_r/k$ (`paper.tex` §Rubric-Runner Co-design Failure)
  before spawning delegate 1. $A < 1.0$ is a floor risk: some criteria have no
  traceable instruction in the runner prompt.
- **New check**: no runner-prompt output-schema field may copy a rubric criterion's
  exact count, threshold, or key set (e.g. an output field demanding precisely the
  number of test cases a criterion grades on). This produces a ceiling by tautology,
  not by capability -- $A{=}1.0$ achieved this way is worse than $A{<}1.0$, because it
  looks like a working instrument while measuring nothing. Runner-prompt instructions
  should point at the *investigation* a criterion requires, not restate the criterion's
  literal grading structure.

## 4. Judge protocol

- Minimum two independent judges score every run, or, where budget restricts scoring
  to a single primary judge, any criterion showing a between-group asymmetry must pass
  an adversarial spot-check (re-reading the raw citations behind both the pass and the
  fail) before being reported as a finding. Report per-criterion agreement (kappa or
  raw percent agreement) regardless of sample size.

## 5. Measurement standards

- Only orchestrator-measured session metadata (`sessions.db`-derived: `wall_clock_seconds`,
  `accumulated_input_tokens`, `accumulated_output_tokens`) is eligible for efficiency
  analysis. Delegate self-reported `message_count`, `latency_seconds`, or `started_at`/
  `finished_at` fields inside the scored JSON are informational only and must never be
  used in a results table.

## 6. Failure handling

- Any delegate attempt that fails to produce valid, parseable output -- including a
  stuck-loop or repeat-tool-call pattern -- is scored as a distinct non-completion
  outcome. Its rate is reported as a primary metric alongside the rubric results, not
  silently retried away. Preserve the failed attempt's session transcript; a discarded
  attempt with no retained record cannot be distinguished from a clean pilot run when
  the experiment is reviewed later.

## 7. Sample size

- Target $n \geq 20$ per group where infrastructure budget allows, per `paper.tex`'s own
  Future Work item (power to detect medium effect sizes, $r \approx 0.50$). Where budget
  constrains a run to pilot scale ($n{=}5$ per group), results must be reported
  descriptively only and explicitly labeled non-confirmatory -- no inferential test
  should be run or interpreted at that n.

## Changelog / provenance

| Rule | Source | Paper Future Work item addressed |
|------|--------|-----------------------------------|
| §1 (model selection, reasoning gate) | Pilot audit F6; model swap under consideration | "other tiers may exhibit different context-weighting dynamics" |
| §1 (multi-turn smoke test) | Pilot audit F4 (self-reported metadata unreliable, near-single-shot engagement observed) | -- |
| §2 (pre-registration timeline) | Pilot audit F1 | -- |
| §3 (two-sided alignment) | Pilot audit F3; extends existing $A=k_r/k$ metric | -- |
| §4 (judge protocol) | Pilot audit F2 | "multi-judge scoring with a reported intraclass correlation coefficient" |
| §5 (measurement standards) | Pilot audit F4 | -- |
| §6 (failure handling) | Pilot audit F5 | -- |
| §7 (sample size) | -- | "$n \geq 20$... replication... would determine whether prompt repetition produces any signal" |

Full pilot findings are retained internally and are not published in this repository.

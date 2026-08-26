# CTT sequential ablation and qualification protocol

Date: 2026-08-26  
Status: preregistration draft; experiments have not started.

## Why this protocol exists

The expensive 300-second closed loop is the final behavioral test, not the first place where a broken scientific mechanism should be discovered. CTT therefore uses a sequential design: each module must first improve its own estimand; the composition must then preserve those increments; only the frozen survivor enters House123.

## Factorization and ownership

For one completed observation block \(B_b\), M1 first produces the physical arrival field \(h_s\). It is a carrier, not a third likelihood to multiply. Define A1's independent-event conditional score

\[
J_1(s)=\log p_{iid}(\{t_j,m_j\}\mid N_b,s,h_s),
\]

and let M2 replace it with a structured path-association conditional likelihood

\[
J_2(s)=\log p_{assoc}(\{t_j,m_j\}\mid N_b,s,h_s).
\]

M3 supplies the complementary event-count/survival likelihood

\[
J_3(s,q)=\log p(N_b\mid s,q,h_s).
\]

The complete method is therefore

\[
\ell_{CTT}(s,q;B_b)=J_2(s;B_b)+J_3(s,q;B_b),
\]

not \(J_{M1}+J_{M2}+J_{M3}\). Adding all three would count positive events twice.

- M1 owns the physical first-passage/hazard field and supplies A1's coarse independent-event reference score.
- M2 owns the global assignment of observed positive bursts to candidate transport phases/paths and replaces A1's positive-event score.
- M3 owns only the complementary count/survival factor.

The online update is

\[
p_b(s,q)\propto p_{b-1}(s,q)\exp\{\ell_{CTT}(s,q;B_b)\},
\qquad p_b(s)=\int p_b(s,q)\,dq.
\]

The native PMFS likelihood is not also applied to \(B_b\). The unchanged PMFS planner consumes \(p_b\). This blockwise contract is required to avoid using the same measurements twice.

## Stage 0 — contracts before any result

Freeze and hash:

- candidate support and map-to-carrier mapping;
- M1 PDE/solver or neural surrogate architecture;
- burst parser, M2 cost/capacity/background rules;
- M3 nuisance prior and causal window rule;
- premise atoms, realizations, matched distractors and controls;
- scoring, bootstrap and verdict scripts;
- all inputs and output roots.

No truth-bearing House123 file may be opened by generation/scoring code. Evaluator-only truth is attached after integrity checks.

## Stage 1 — M1 qualification

Run only the frozen synthetic transport premise library.

Required positive evidence:

1. predictive first-passage/hazard score beats the fixed analytical PMFS response field;
2. true-vs-best-matched-false pre-Bayes positive margin is above zero;
3. paired bootstrap lower 95% bound for the improvement is above zero;
4. time shuffle, wrong causal direction and delay permutation remove the gain;
5. at least one predeclared atom reverses a misleading distance-only ordering.

Terminal result: `M1_GO`, `M1_NO_GO`, `M1_INVALID_COVERAGE`, or `M1_NUMERICAL_INVALID`. Only `M1_GO` advances.

## Stage 2 — M2 incremental qualification

Hold M1 fixed. Compare the same candidate bank under:

- `B1 = M1 field + iid conditional event score J1`;
- `B2 = M1 field + M2 structured conditional event score J2`;
- `B2-P = time-permuted J2`;
- `B2-I = independent peak matching`.

Required positive evidence:

\[
\Delta_2=\operatorname{margin}(J_2)-\operatorname{margin}(J_1)>0
\]

with paired-bootstrap lower 95% bound above zero, no atom-family negative median, and loss of gain under time/path permutation. Only `M2_INCREMENTAL_GO` advances.

## Stage 3 — M3 conditional qualification

Hold M1 and M2 fixed. Compare:

- `B2 = J2`, the M2 event-time/mark likelihood conditional on event count;
- `B3 = J2 + J3`, the complete event plus count/survival likelihood;
- `B3-S = J2 + shifted-window J3`;
- `B3-C = J2 + candidate-constant count/miss term`.

Required positive evidence:

\[
\Delta_3=\operatorname{margin}(B3)-\operatorname{margin}(B2)>0
\]

and false-minus-true survival penalty above zero, both with paired-bootstrap lower 95% bounds above zero. Shifted windows must remove the gain; candidate-constant penalty must carry zero relative information. Exact M2/M3 support disjointness is a hard gate. Only `M3_CONDITIONAL_GO` advances.

## Stage 4 — composition and cheap real-stack activation

Before any new 300-second qualification:

1. replay already-revealed development traces only to verify parsing, timing, carrier mapping and evidence logs; these results are never called generalization;
2. run a bounded live shadow with the planner/posterior unchanged to prove that M1/M2/M3 activate on the real ROS/GADEN stack;
3. verify OFF parity and deterministic replay;
4. verify that the full score is not candidate-constant and that the true carrier is inside the frozen support after evaluator-only reveal;
5. verify resource use and update latency fit the closed-loop budget.

Any coverage or activation failure is `INVALID`, not a mixed performance result. No likelihood/gate/planner tuning is permitted here.

## Stage 5 — freeze

Create one immutable manifest containing equations, source and binary SHA-256, all parameters, response banks, candidate support, seed-selection rule, 300-second duration, metrics and pass/fail criteria. After this point no formula, gate, nuisance family, threshold, planner or seed substitution is permitted.

## Stage 6 — efficient closed-loop ablation and generalization

To obtain module attribution without blindly paying for every arm on every seed:

### Tier A: cross-House closed-loop ablation

On one previously unseen preregistered seed per House, run four paired arms for the full 300 seconds:

| Arm | Method |
|---|---|
| A0 | native PMFS |
| A1 | M1 only |
| A2 | M1 + M2 |
| A3 | M1 + M2 + M3 |

This is 3 Houses x 4 arms = 12 runs. It establishes whether each certified information increment survives planner feedback in every environment.

Stop rule: if A1/A2/A3 violates its frozen contract, crashes, fails to activate or causes a preregistered catastrophic regression, preserve the result and do not spend the replication seed.

### Tier B: independent full-method replication

Only after Tier A remains viable, use a second unseen seed per House for:

- A0 native PMFS, 300 seconds;
- A3 complete CTT, 300 seconds.

This is 3 Houses x 2 arms = 6 additional runs. Total maximum cost is 18 runs, not 24. The component attribution comes from Tier A; independent replication of the final method comes from both tiers.

TIME-PERMUTE, PATH-SHUFFLE and WINDOW-SHIFT are mechanistic controls evaluated on frozen traces, not alternative planners, so they do not require additional 300-second runs.

## Primary closed-loop metric and reporting

Use the original PMFS metric `ExpectedValue(sourceProbability, 0.05)` at 300 seconds. For each paired run,

\[
R_{hr}=\frac{E^{OFF}_{hr}-E^{ON}_{hr}}{E^{OFF}_{hr}}.
\]

Report every pair, House medians, the pooled ratio of summed errors, paired bootstrap intervals and update-by-update trajectories. Do not substitute internal posterior variance for localization error. Variance is a diagnostic only.

The final pass threshold must be copied from the frozen manifest before Tier A starts. At minimum it must require pooled improvement of at least 10%, cross-House consistency and no preregistered catastrophic regression. Exact consistency and catastrophe bounds must be fixed after inspecting baseline measurement noise but before reading any A1/A2/A3 outcome.

## Decision table

| Earliest failed stage | Scientific conclusion | Next allowed action |
|---|---|---|
| M1 | transport field lacks direct information | redesign M1 under new version |
| M2 | phase association adds no temporal/path information | remove/redesign M2 |
| M3 | misses add no conditional falsification information | remove/redesign M3 |
| activation | real-stack/data contract invalid | repair contract only, then rerun same frozen gate |
| Tier A | module information does not survive feedback | preserve NO-GO; do not run Tier B |
| Tier B | full method does not replicate | report limited/non-generalizing result |
| all pass | main method is supported | package paper evidence and frozen code |

No later-stage success can overwrite an earlier module failure.

# CG-PC-CTT V5 — Active Sequential Intervention Freeze

Date: 2026-08-28

Base: `aa57af74a54dcdf746052e5b2477ac3a7180a3a8` (V4 truth-blind STOP)

Status: **V5 SCIENTIFIC REFERENCE FROZEN FOR TRUTH-BLIND REPLAY + DIRECT CLOSED-LOOP IMPLEMENTATION**

## Why V5 exists

V4 is scientifically coherent but structurally underpowered. Its frozen truth-blind audit found only 6/30 development runs with any ACCEPT. M1 still formed tens of observation-resolved components in all three Houses; the dominant failure was M2 cross-stop invariance. With only three physical stops in most source-update windows, leave-one-stop-out leaves only two training stops.

V5 does **not** weaken the Jeffreys source-independent null, numerical-zero semantics, coherent transport-member identity, or M3 minimum-change projection. It changes the information architecture before the gate:

1. accumulate spatially unique physical stops across source-update contexts;
2. validate invariance by holding out an entire context, not one stop;
3. when evidence is still insufficient, actively choose the next feasible unvisited physical stop that maximally separates the current source components under every scoring transport member;
4. modify the posterior only after the scientific evidence gate passes.

This converts passive observation into active experimental design. A probe changes **where the robot measures**, not the posterior. Therefore low-coverage runs can acquire genuinely new independent evidence instead of remaining forever identical to Classic PMFS.

## Paper-level three-module interpretation

### M1 — Spatiotemporal Transport Representation（时空输运表征）

Keep the repaired V4 component construction:

- calibration members `0..3` only;
- persistent source carriers;
- finite observation floor `C_y = (1/4 + eps_T^2) I`;
- no Moore–Penrose deletion of stable directions;
- exact geometric aliases remain unresolved;
- all calibration-member leave-one-out checks must agree on a resolved boundary.

For V5 the observation axis is the cumulative ledger of spatially unique physical stops.

### M2 — Active Sequential Invariant Source Evidence（主动序贯不变源证据）

#### M2.1 Unique-stop evidence ledger

At source-update time `t`, retain

`D_t = {(x_j, c_j, r_j, p_{s,m,j})}_{j=1..N_t}`

where:

- `x_j` is a stable PMFS physical-cell key;
- `c_j` is the source-update context that first contributed this cell;
- `r_j` is the unit-weight fractional hit outcome after collapsing the eight raw blocks at that stop;
- `p_{s,m,j}` is the truth-free transport prediction for source carrier `s`, keyed transport member `m`, and that physical stop.

A spatial cell may enter the scientific evidence ledger only once. Re-visits may still update native PMFS, but they do not increase V5 scientific sample size.

#### M2.2 Context-blocked cross-predictive validation

Require at least three effective source-update contexts and at least six spatially unique physical stops.

For scoring members `m=4..7`, retain the V4 fractional Bernoulli log score

`ell_j(s,m) = r_j log p_{s,m,j} + (1-r_j) log(1-p_{s,m,j})`.

For held-out context `k`, let `T_-k` contain every ledger stop not first acquired in context `k`, and `H_k` contain the held-out context stops. Preserve one source and one transport-member identity across all training stops:

`L_-k(s,m) = sum_{j in T_-k} ell_j(s,m)`.

For component `B`, training evidence is

`E_-k(B) = log sum_{s in B} q0(s|B) * mean_m exp(L_-k(s,m))`.

All context-LOO folds must share exactly one best component `B*`.

The held-out conditional predictive score keeps both source and member identity:

`A_k(B) = E_{T_-k union H_k}(B) - E_-k(B)`.

The source-independent null remains Jeffreys-Beta prequential prediction with frozen prior `Beta(1/2,1/2)`, conditioned on training outcomes only and then advanced through the held-out context in acquisition order.

For every held-out context:

- selected `B*` may not lose to any rival component;
- selected `B*` must beat the Jeffreys source-independent null;
- at least two held-out contexts must have a strictly positive rival margin;
- scoring-member leave-one-out may not reverse the accepted component.

There is no House-specific, seed-specific, truth-derived, localization-error-derived, temperature, blend weight, or post-hoc scientific threshold.

#### M2.3 Active measurement intervention when evidence is insufficient

If M2.2 does not ACCEPT, the posterior remains native PMFS exactly. V5 may nevertheless replace the **next measurement target** using an outcome-free active-probe rule.

The candidate set is exactly the native planner's already-feasible next-stop set. V5 may not enlarge the native motion horizon.

For each candidate physical cell `x`, each source component `B`, and scoring member `m`, form the component predictive hit probability using the current native PMFS source weights within the component:

`p_{B,m}(x) = sum_{s in B} w_s p_{s,m}(x) / sum_{s in B} w_s`.

Let `W_B = sum_{s in B} w_s`. The member-specific expected information gain is the Bernoulli Jensen-Shannon / mutual-information quantity

`IG_m(x) = H(sum_B W_B p_{B,m}(x)) - sum_B W_B H(p_{B,m}(x))`.

Transport-robust utility is

`U(x) = min_{m in {4,5,6,7}} IG_m(x)`.

Choose the feasible, spatially unvisited candidate with maximal `U(x)`, with stable physical-cell id as the exact-tie breaker.

**Native-dominance rule:** override the native next-stop choice only when

`U(x*) > U(x_native) + numerical_zero`.

Otherwise use the native action exactly.

Thus V5 never changes the posterior merely because it is uncertain. It first performs an actual measurement intervention that is predicted, under every scoring transport member, to be more informative than the native planned measurement.

### M3 — Observation-Resolved Minimum Causal Assimilation（观测分辨最小因果同化）

Keep the V4 KL/I-projection rule, with one correction for the cumulative ledger:

- after ACCEPT, recompute the causal source state from the frozen geometry prior `q0` and the **full ledger once**;
- do not multiply old ledger evidence again when a new source-update context arrives;
- compute `alpha = q_causal(B*)`;
- if native PMFS already has mass `beta >= alpha` on `B*`, return native exactly;
- otherwise perform the same minimum-KL mass-floor projection as V4.

On M2 ABSTAIN + PROBE:

- posterior output = native PMFS exactly;
- only the next measurement target may change;
- the resulting physical measurement is appended to the ledger at its next valid acquisition point.

On M2 ABSTAIN + no strict probe gain:

- posterior = native exactly;
- planner action = native exactly.

## Why this is not a Gate relaxation

V4 failed because its scientific sample unit was too small: three stops, then only two stops after LOSO. V5 retains V4's absolute adequacy and rival checks but increases **independent observation information** before asking for invariance.

The active-probe rule is also outcome-free. It cannot inspect the next gas result when selecting a stop, and it cannot use source truth or localization error. Its objective is a worst-member expected information gain, not a performance-tuned threshold.

## Required falsification tests

The Python scientific reference must PASS all of the following before C++ parity work:

1. V4 component-construction and coherent-member counterexamples remain blocked.
2. The V4 all-candidates-bad `.01 vs .005` all-hit counterexample fails the absolute null.
3. A synthetic three-context consistent source component ACCEPTs.
4. A contradictory held-out context ABSTAINs.
5. Candidate/source permutation preserves the partition and decision.
6. Scoring-member permutation preserves the decision.
7. Spatial stop re-visits do not increase ledger sample size.
8. Recomputing the full-ledger causal posterior is idempotent and cannot double-count old evidence.
9. Active-probe utility is scoring-member permutation invariant.
10. Active-probe candidate-order permutation preserves the selected physical cell.
11. A visited cell cannot be selected as a new evidence probe.
12. Native next stop is overridden only for strict robust-information gain.

## Truth-blind replay gate

Run the 30 archived development OFF trajectories through the cumulative ledger using the already-frozen 150 V4 NPZ contexts plus a truth-blind physical-cell manifest.

Report per run:

- final number of unique physical cells;
- effective source-update contexts;
- first ACCEPT update if any;
- all context-blocked abstention reasons.

This replay is an actionability diagnostic only. It must not read truth or localization error and must not be used to tune formulas.

If at least 20/30 archived OFF runs obtain a passive V5 ACCEPT, the original `>=20/30 improved-pair` endpoint is no longer mathematically impossible before any active intervention.

If fewer than 20/30 passively ACCEPT, **do not modify the evidence gate**. Proceed to the fixed active-probe implementation because its purpose is precisely to create counterfactual measurement locations absent from the archived OFF trajectory; those outcomes cannot be recovered from passive replay.

## Closed-loop development endpoint remains unchanged

Development remains:

`H01,H02,H03 x seeds 0..9 x OFF/ON = 60 arms`

with frozen Classic PMFS OFF and V5 ON, paired environment, and `TIMEOUT_SEC=300`.

GO still requires all of:

- 30/30 valid pairs;
- pooled top-5 expected-location error reduction >=10%;
- >=20/30 pairs improve;
- no House pooled mean degradation >5%;
- zero new false-confident collapses;
- all runtime and parity contracts pass.

No mid-matrix edits. Seeds 0..9 remain development-only; seeds 10..19 remain untouched for fresh confirmation after a frozen GO.

## Scientific positioning

The methodological transfer is deliberately cross-domain:

- causal representation learning via invariance/symmetry: ICLR 2025, *Unifying Causal Representation Learning with the Invariance Principle*;
- active experiment selection under uncertainty: Nature Communications 2025, *Active learning-assisted directed evolution*;
- rigorous replication and anti-pseudoreplication principles: Nature Communications 2025, *How thoughtful experimental design can empower biologists in the omics era*;
- sequential evidence accumulation / optional continuation: Biometrika 2025, *Anytime-valid and asymptotically efficient inference driven by predictive recursion*.

V5 should be described as **interventional source-identification evidence** rather than a Pearl/Rubin causal-effect estimator: the intervention is on the robot's measurement location, which creates informative contexts for discriminating source–transport hypotheses.

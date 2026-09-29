# CG-PC-CTT V3 direct closed-loop freeze — 2026-08-27

## Decision

No additional H02 trace-bank generation, hard-28 recovery, bridge panel, or small-seed method tuning is required before the next closed-loop experiment.

The verified H02 replacement bank is sufficient as the development/diagnostic asset:

- 51 outcome-blind H02 contexts;
- 201 unique physical carriers;
- 8 keyed transport members;
- 82,008 verified CTT traces;
- `H02_RECONSTRUCTED_CHALLENGE_V1_BANK_VERIFY_PASS`;
- legacy hard-28 remains `LEGACY_HARD28_PROVENANCE_LOST` and is not reconstructed.

The next performance experiment is the already frozen confirmatory matrix:

`House01, House02, House03 x seeds 0..9 x OFF/ON = 30 matched pairs / 60 arms`, 300 s each.

A short infrastructure smoke is allowed only to verify build/launch/output/no-truth-leakage. It is not a method-development experiment and may not be used to tune thresholds or weights.

## Frozen ON-arm method

Name for engineering contract:

**V3 Observation-Resolved Reversible Update (V3-ORR)**.

The proximal/host-aware bridge remains a mechanistic analysis/possible later extension. It is NOT a prerequisite for the direct closed-loop matrix.

### Runtime inputs

Use only causally available PMFS state already materialized in the existing EC-ECDL path:

`rawProbabilities[source][keyed_member][completed_event]`

plus completed event hit/miss, stable block ID, geometry-only persistent-carrier rectangles, and the fixed design/geometry prior.

Forbidden runtime inputs:

- source truth;
- same-window native PMFS posterior/rank as V3 evidence;
- future events;
- wind/config/plume seed IDs as oracle labels;
- offline H02 localization outcome;
- legacy `native_score` from historical candidate manifests;
- outcome-fitted thresholds;
- House/seed-specific parameters.

### Member split

Eight keyed members are frozen as:

- members 0..3: observation-resolution calibration only;
- members 4..7: outcome likelihood scoring only.

This prevents the same finite members from simultaneously defining local resolvability and fitting the observed hit/miss outcome.

### Observation resolution

The physical graph is formed by geometry-only persistent carrier rectangle adjacency.

From calibration members, on the actual completed-event support, estimate full transport nuisance covariance

`Sigma_tr = mean_{s,m<n} 0.5 (p_sm-p_sn)(p_sm-p_sn)^T`

and its numerical Moore-Penrose inverse `Sigma_tr^+`.

For each adjacent source pair i,j and calibration-member contrast `d_m=p_im-p_jm`, compute

`eta_ij = [||sum_m d_m||^2_{Sigma+} - sum_m ||d_m||^2_{Sigma+}] / [M(M-1)]`.

Also compute the minimum leave-one-member-out cross strength.

An edge is considered resolved only if both the full and every leave-one-member-out cross strength are positive above numerical round-off tolerance. Ordinary sign-flip p-values are NOT used online.

Unresolved local edges are joined by connected components. These components are called **resolution cells**; they are not claimed to be pairwise-identical statistical equivalence classes.

### Outcome evidence

Using scoring members 4..7, score binary completed-block outcomes with the proper Bernoulli trajectory likelihood. Empirical-probability clipping is fixed by the native 200-record frequency resolution:

`eps = 0.5/201`.

Split events by stable `block_id % 2` into even and odd reproducibility folds. Each fold must contain at least two events and at least one hit and one miss; otherwise the V3 update abstains.

Member likelihoods are marginalized by log-mean-exp. Candidate scores are projected to the current resolution cells before fold ranking.

### Reversible posterior

Within each fold, use tie-safe normal mid-ranks. Combine folds as

`g(s) = [z_even(s)+z_odd(s)] / sqrt(2)`.

Project `g` again to the current resolution cells. Then

`q(s) proportional q0(s) exp(g(s))`,

where `q0` is the fixed geometry/design prior, not the same-window native PMFS posterior.

Candidate mass is distributed uniformly over free cells inside that persistent carrier rectangle for injection into the PMFS planner shell.

No temperature, blend weight, bridge weight, or online significance threshold exists.

## Code contract

Authoritative pure implementations:

- `experiments/cg_pc_ctt/v3_direct_runtime_reference.py`
- `experiments/cg_pc_ctt/selftest_v3_direct_runtime.py`
- `ros2_package/src/gsl_server/algorithms/PMFS/internal/ObservationResolvedV3.hpp`

The C++ header is the runtime core; Python is the parity/reference implementation.

## Minimal Simulations.cpp integration

Do not rewrite the simulator.

Reuse the current `applyEnsembleEcEdcl()` physical-response construction through the point where `rawProbabilities` has been fully populated, before historical Hellinger/eigenchannel normalization.

Add a new explicit mode, recommended literal:

`pfdiMode == "v3_orr"`.

For this mode only:

1. Build `observedHit` and `blockId` from `pcAciActiveEvents`.
2. Build `rectangles` from `p2LastEvaluatedCandidates[s].rect`.
3. Build fixed `priorMass` by summing `pcAciDesignPriorGrid` over free cells in each persistent carrier rectangle. Never use the current native PMFS posterior.
4. Call `v3_orr::compute(rawProbabilities, observedHit, blockId, rectangles, priorMass)`.
5. If `released=false`, leave the current causal/fixed-prior V3 state unchanged and report ABSTAIN; do not inject the native same-window posterior as V3 evidence.
6. If released, distribute `candidateMass[s] / freeCellsPerSource[s]` over the rectangle's free cells and inject that grid.
7. Emit an audit CSV with update id, event counts/hits by fold, resolution-cell count, resolved/unresolved edge count, nuisance rank, release flag/reason, and binary hash.

The historical EC-ECDL generalized eigenchannel ledger is not part of V3-ORR and should not run after the V3 branch point.

## State rule

The direct V3 posterior is recomputed reversibly from the current completed-event set and fixed prior. Do not recursively use the previous V3 posterior as a new prior. This prevents stale/future factor accumulation and ensures that a later coarsening of observation resolution can erase unsupported historical fine-scale evidence.

## OFF arm

OFF is unmodified Classic PMFS under the same house/seed/runtime contract.

## Infrastructure smoke only

Before the 60-arm matrix, run exactly enough to verify:

- `pfdiMode=v3_orr` reaches the new branch;
- no source truth is available to the method process;
- `rawProbabilities` dimensions and persistent carrier identities are stable;
- ABSTAIN leaves a valid normalized posterior;
- RELEASE writes a normalized final posterior;
- no NaN/Inf;
- 300 s stop works;
- the external evaluator sees truth only after the online process exits.

Do not inspect smoke localization error to tune the method.

## Confirmatory matrix remains frozen

Use `closed_loop/cg_pc_ctt/run_multiseed_matrix.sh` and the existing external evaluator/aggregator.

Success remains:

1. 30/30 matched pairs valid;
2. pooled PMFS top-5 expected-value error reduction >=10%;
3. one-sided paired sign test p<=0.05 (20/30 improved pairs is sufficient);
4. no House pooled mean degrades >5%;
5. zero false-confident-collapse flags.

No House/seed-specific tuning after matrix start.

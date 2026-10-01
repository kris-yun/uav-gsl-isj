# CODEX handoff — SITER-PMFS v0 cross-House offline gate

Date: 2026-10-01
Branch: research/siter-pmfs-v0-20261001

Read first:

1. research/siter_pmfs_v0/THEORY_AND_NOVELTY_AUDIT.md
2. research/siter_pmfs_v0/SITER_V0_OFFLINE_CHARTER.md
3. evidence/siter_pmfs_v0_oracle_screen_20261001/ORACLE_ONE_SIDED_RESULT.json
4. frozen TNQC six-case evidence and context-bank contracts.

## Do not continue the previous search loop

This task is not another theory audit and not another 3-D oracle experiment.

Implement one concrete algorithm family:

PMFS generalist anchor + sparse flow-conditioned contradiction factor.

The transport module must be one-sided:

    new_log_score = native_pmfs_log_score - contradiction_energy

with contradiction_energy >= 0.

No signed unconstrained correction may control the primary posterior.

## Inputs

Use the authoritative existing 300-s six-case TNQC/VGR archive only.
Do not run GADEN.

For every source update/candidate recover:
- native PMFS score and active-leaf geometry;
- measured probability/confidence map;
- simulated native hit map/alignment;
- estimated wind grid;
- occupancy/map metadata.

## Feature implementation

Implement the fixed dictionary in the charter.

At minimum include PMFS/generalist:
- within-update native score quantile;
- confidence-weighted absolute residual mean/q50/q90;
- confident observed-hit unsupported mass;
- confident observed-miss predicted mass;
- support-overlap fraction;
- leaf-area fraction.

Flow:
- candidate-centered along-wind and cross-wind coordinates;
- gas-weighted upwind-violation fraction;
- cross-flow residual dispersion;
- along-flow residual asymmetry;
- local wind coherence;
- optional 2-D streamline reachability if it can be implemented source-blind from the existing estimated-wind grid and occupancy.

Do not use House ID, seed ID or truth coordinates as features.

All feature definitions must be committed before outer-fold truth evaluation.

## Model

Primary:
nonnegative simplex-weight sparse contradiction model.

Weights:
- alpha >= 0;
- sum(alpha)=1;
- train only on outer-training Houses;
- sparsity chosen only inside training Houses.

Use candidate pairwise ranking supervision within training Houses.
Equal-weight each source update.

Do not let the held-out House choose features or hyperparameters.

## Outer test

Three folds:
- H01+H02 -> H03;
- H01+H03 -> H02;
- H02+H03 -> H01.

Evaluate terminal <=300 s fixed-trajectory posterior on both held-out seeds.

Use the validated PMFS ExpectedValue(...,0.05) evaluator.

## Required outputs

- FEATURE_CONTRACT.md
- FEATURE_PROVENANCE.json
- OUTER_FOLD_CONFIG.json
- SITER_V0_CANDIDATES.tsv
- SITER_V0_CASES.tsv
- SITER_V0_RESULT.json
- SITER_V0_DECISION.md
- SITER_V0_ABLATIONS.tsv
- INDEPENDENT_SITER_V0_AUDIT.json
- SHA256SUMS.txt

## Strict STOP

After fixed-trajectory result: STOP.

No closed loop unless the charter returns SITER_V0_CROSS_HOUSE_SIGNAL.

No new GADEN, no H03 redesign after outer truth, no generic deep network rescue.

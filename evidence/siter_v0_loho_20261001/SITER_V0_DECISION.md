# SITER-PMFS v0: completed development LOHO gate

## Decision

**SITER_V0_NO_GO_STOP**

The frozen nonnegative contradiction model did not improve source localization. No feature redesign, penalty rescaling, new forward, plume, training extension or closed loop follows this result.

## Frozen execution chain

- Supplied starting branch/commit: `research/siter-pmfs-v0-20261001`, `4a9777c0307acf6599931da624fbb60bb4c9a22e`.
- Feature/fitting contract: `2c85049b`.
- Source-blind implementation: `cb7d514b`.
- All three outer models committed and pushed before outer scoring: `aaabacf5`.
- Frozen model JSON SHA256: `fa0b890c4eab3bdc893c2f12faba682b02de4e651f3358ee0792a2b6303dcc37`.
- Authoritative TNQC six-case archive SHA256: `81c72910b2fc912e5e0a9340d3f6b1ba20024da510ef58eb95da2ff1d8055708`.
- Original H0 INVALID_STOP and unexecuted H0-R supersession remain unchanged.

## Primary terminal results

Ranks refer to the complete active Native quadtree-leaf partition at that update. Endpoint is the same Native top-5% probability-weighted estimator, with cell measure preserved.

| Case | Active leaves | Native rank | SITER rank | Native error, m | SITER error, m | Margin gain, nats |
|---|---:|---:|---:|---:|---:|---:|
| H01 seed0 | 123 | 81 | 81 | 5.527347 | 5.528912 | +0.214051 |
| H01 seed1 | 121 | 90 | 90 | 4.001642 | 3.999294 | +0.385039 |
| H02 seed0 | 123 | 109.5 | 109.5 | 4.107023 | 4.117493 | +0.388083 |
| H02 seed1 | 119 | 107.5 | 107.5 | 3.700743 | 3.702263 | +0.448839 |
| H03 seed0 | 160 | 112 | 112 | 7.782055 | 7.780373 | +0.251189 |
| H03 seed1 | 160 | 109 | 110 | 8.211551 | 8.214775 | +0.188220 |

Rank improvement: **0/6**; unchanged: 5/6; worsened by one: 1/6. Median rank improvement: 0.

Endpoint improvement: **2/6**. Mean error **5.555060292358270 → 5.557184883078148 m**, an increase of approximately **0.03825%**, failing the required 5% reduction. All six remain geometric failures at 0.5 m.

No newly created false-confident collapse. Importantly, **all six were already false-confident collapses in Native and remain so in SITER**, using the recovered original definition `variance < 1 m² and error > 2 m`. Passing the no-new-collapse check does not establish safety or successful recovery.

The requirement for at least one seed with both rank and endpoint improvement in each House fails in all three Houses.

## Ablations and interpretation

Training-only inner validation selected capacity 1 in every fold. Generalist-only and full both selected feature 6, observed-miss predicted mass; flow-only selected feature 13, downwind observed-miss predicted mass. Full and generalist predictions are identical. Thus this experiment does **not** establish incremental value of the flow-conditioned head.

The signed diagnostic improves rank in only one run and endpoint in four runs, but does not establish cross-House localization gain. Full is not demonstrably better or safer than signed: both retain six collapses, and full has no rank improvement. The one-sided falsification thesis is not supported by this result.

All six primary margins increase, but only by 0.188–0.449 nats. Native truth-vs-best-wrong deficits are approximately 127–293 nats. Under the frozen normalized simplex contract, `0 <= C(s) <= 1`, so any pairwise log-odds correction is at most one nat. It cannot reverse these large deficits. This is an explicit capacity/anchor limitation of this tested v0; it is not permission to increase a multiplier after seeing outcomes, and it does not prove that every possible transport model fails.

Nonnegative C only guarantees one-sided score subtraction. It does not prevent penalizing truth or guarantee a better posterior. The actual held-out results, rather than that algebraic sign, determine the verdict.

## Implementation and independent audit

- Hash-verified all selected archived input files. Preparation uses no truth or Oracle features.
- Reconstructed Native posterior for all **30/30 updates**, maximum absolute deviation **1.2434497875801753e-14**, below `1e-10`.
- Historical endpoint binary was absent. Rebuilt archived original tool plus original `Math.cpp` in an isolated shared-directory workspace. Did not alter ROS2 src/build/install or runtime.
- Rebuilt original evaluator reproduces **18/18** saved Native/TNQC-only/TNQC-fused endpoint outputs within `1e-10`. A separate readout extension calls the same original `Variance(grid)`.
- Independent descriptor formulas agree within **8.881784197001252e-16**; independent Native log-scores within **6.252776074688882e-13**; independent posterior within **1.3322676295501878e-15**.
- Independently checked all fold scaling bounds, inner/outer exclusion, simplex constraints, selected capacities, truth ownership, ranks, margins, corrected posteriors and final decision.
- Complete scoring repeated: candidates, cases, ablations, result, posterior NPZ and endpoint parity JSON are **byte-identical**.
- Analytic objective gradient, bounded simplex energy, zero-confidence behavior, coordinate translation invariance and constant-feature handling passed mathematical checks.
- Existing VM NumPy 1.26.4 / SciPy 1.8.0 emits a supported-version warning. No environment changes were made; optimizer success, gradient verification, independent formula audit and exact repeat are recorded. The warning is disclosed, not suppressed as a scientific result.

## Scope and STOP

These are previously studied historical trajectories with leave-one-House-out fitting, **not untouched confirmation**. Each House contributes one physical truth location with two seeds; six runs are not six independent source positions. This is offline fixed-trajectory source-map evaluation, not a new interactive closed-loop campaign.

Only the explicitly authorized historical TNQC H03 records were read. OCB-R2 confirmation and H03 datasets remain sealed. No new GADEN, PMFS forward, neural model, planner modification or closed loop was run. STOP.

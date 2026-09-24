# SLL-v2 PRE-L1 Root-Cause Freeze

Date: 2026-09-24
Branch: `research/source-lineage-lagrangian-v2`
Status: **READY FOR ONE DECISIVE RAW-FILAMENT L1; NO CLOSED LOOP**

## Root cause accumulated from failed M4-family experiments

The evidence no longer supports the hypothesis that M4 is missing only:
- more wind sensitivity;
- a generic memory module;
- a local wall-slide rule;
- a simple vertical exchange term;
- a generic Eulerian residual correction.

The consistent failure is deeper:

> a single 2-D concentration slice is not a closed transport state for the inverse localization problem.

Projection into (C(x,y,z_{sensor})) removes:
- source-to-path lineage;
- filament age;
- sub-cell position;
- 3-D vertical excursion;
- obstacle/wake encounter history.

Consequently the same wind intervention has strongly source-dependent plume effects,
while M4's reusable concentration-space operator makes those paths too homogeneous.

The inverse failure is dominated by absolute source-to-plume path placement:
nearby false sources can place an otherwise plausible plume closer to the observations
than the true source.

## Resolution being tested

Change the state, not another M4 correction layer.

Use a lineage-bearing 3-D Lagrangian state:

[
Z_s(t)={(x_i,y_i,z_i,sigma_i,a_i)}.
]

Source remains external injection. A single transport law is shared across candidates.

The decisive L1 tests:
1. whether 3-D lineage state itself beats a matched 2-D particle state;
2. whether a learned source-agnostic transition adds value beyond deterministic 3-D physics;
3. whether destroying lineage correspondence destroys that learned gain.

## Existing raw data

No new plume simulation is needed.

Raw 8-cell bank already exists:
`/home/zyc/c0_5_real_gaden_bank_20260923/{CELL}/realization/iteration_*`

566 snapshots per cell.

Exact data-contract corrections frozen before L1:
- actual emission = constant 7 Hz core releaseAccumulator rule;
- deprecated `variable_rate` / `filament_stop_steps` arguments are ignored by this wrapper;
- save indices are counters, not exact 0.5-s timestamps;
- exact save timing is reconstructed with GADEN float32 strict-`>` semantics;
- wrapper T/P parameter-reading defect makes House02 development-only.

## Decisions

### 1. `L1_FAIL_STOP_SOURCE_LINEAGE_MAINLINE`
The state hypothesis itself fails. Stop particle/lineage route.

### 2. `L1_STATE_PASS_OPERATOR_NO_GO`
3-D lineage state matters but deterministic 3-D physics explains it.
Do not claim a learned particle operator main innovation.

### 3. `L1_OPERATOR_PASS_FREEZE_BEFORE_L2`
Both state representation and learned source-agnostic operator survive.
Freeze everything, then and only then run L2 >=20-source truth-rank test.

No result from L1 authorizes ROS/PMFS closed loop directly.

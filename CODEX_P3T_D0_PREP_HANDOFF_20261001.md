# CODEX handoff — P3T-D0 controlled Gaussian-support test

Date: 2026-10-01
Branch to work from: `research/p3t-d0-gaussian-control-20261001`

R1P5 is complete and stopped with:
`PMFS3D_R1P5_HOLD_PARTIAL_SELECTIVITY`.

Do not implement counterexample/hypothesis elimination.

## Read first

1. `research/p3t_world_model_v0/R1P5_TO_D0_INTERPRETATION_20261001.md`
2. `research/p3t_world_model_v0/P3T_D0_GAUSSIAN_SUPPORT_KILL_TEST.md`
3. `research/p3t_world_model_v0/MAINLINE_CANDIDATE_20261001.md`
4. `evidence/pmfs3d_r1_oracle_ranking_20261001/R1_FINAL_REPORT_20261001.md`
5. `research/pmfs3d_r1/R1_FORWARD_CONTRACT_FINAL.md`

The D0 charter is frozen before scientific scoring. Do not relax gates after seeing results.

## Phase P0 — provenance and trajectory gate

Do this first and commit the evidence before opening truth rankings for G2/G3.

### Recover exact physical parameters

Locate, hash and document the historical configuration/source code establishing:

- GADEN/Gaden-RT Gaussian filament concentration equation;
- filament mass / release-mass convention;
- diffusion or sigma-growth schedule;
- gas detection threshold actually used to convert the historical sensor concentration into PMFS hit/miss observations;
- concentration units and coordinate units.

The parameter set must be unique and dataset-compatible.

If any value has multiple plausible choices that would require selecting by source-rank performance:
return `P3T_D0_INVALID_STOP`.

### Recover trajectories

Need center trajectories for every frozen R1 candidate and both transport arms:

- Oracle-2D center trajectories;
- Oracle-3D xyz center trajectories.

Preferred order:

1. use already-retained trajectory/debug artifacts if present;
2. otherwise instrument the frozen R1 oracle code to export center states while proving byte-identical candidate scores/maps against R1 when the export is disabled/ignored;
3. do not alter RNG, collision, source draws, CFD queries, timestep or candidate support.

Do not run GADEN.

### P0 outputs

Create:
- `P0_PROVENANCE.md`
- `P0_PHYSICS_PARAMS.json`
- `P0_TRAJECTORY_PARITY.json`
- `P0_INPUT_SHA256.json`
- `P0_DECISION.md`

Commit them before scientific G2/G3 scoring.

If P0 fails, STOP.

## Phase D0 — four-arm controlled test

P2 and P3 are frozen R1 outputs; do not regenerate them except for parity if needed.

Compute only:

- G2: Gaussian support using frozen Oracle-2D center trajectories embedded on the PMFS sensor plane;
- G3: identical Gaussian mass/diffusion/threshold operator using frozen Oracle-3D xyz center trajectories.

All Gaussian physical parameters must be identical between G2 and G3.

Use on-demand historical GADEN/Gaden-RT concentration evaluation at frozen PMFS query locations. Do not allocate a dense 3-D concentration cube as the primary method.

Convert concentration to hit/miss using the frozen historical detection threshold and then time-average to the simulated PMFS hit probability.

Use the unchanged PMFS likelihood and posterior normalization.

## Required independent controls

Before source truth/ranks are evaluated:

- independent Gaussian concentration equation cross-check;
- deterministic repeat;
- G2/G3 physical-parameter identity;
- P2/P3 exact parity;
- candidate and center-trajectory hash freeze;
- measured-map hash freeze;
- no truth-dependent parameter path.

After source scoring, independently recompute all log scores/ranks/margins from saved Gaussian hit maps.

## Required final outputs

At minimum:

- `P3T_D0_RESULT.json`
- `P3T_D0_CASES.tsv`
- `P3T_D0_CANDIDATES.tsv`
- `P3T_D0_DECISION.md`
- `INDEPENDENT_D0_AUDIT.json`
- `RUN_PROVENANCE.md`
- `SHA256SUMS.txt`

Per case report all four arms P2/P3/G2/G3 and deltas G3-P3, G2-P2, G3-G2.

## Frozen possible decisions

- `P3T_D0_3D_GAUSSIAN_SOURCE_EVIDENCE_PASS`
- `P3T_D0_GAUSSIAN_ONLY_HOLD`
- `P3T_D0_HOLD_SUPPORT_NOT_DISCRIMINATIVE`
- `P3T_D0_NO_POSITIVE_TRUTH_SUPPORT_STOP`
- `P3T_D0_INVALID_STOP`

After any decision: **STOP**.

Do not:
- train a world model;
- open H03/confirmation;
- generate a new GADEN plume;
- run a 300 s closed loop;
- tune sigma/mass/threshold;
- add a learned scorer;
- change candidate support.

## Return to us

Report exactly:

1. branch and final commit;
2. P0 provenance decision;
3. final D0 decision;
4. recovered filament mass/diffusion/threshold provenance;
5. for each case: P2/P3/G2/G3 truth log score, truth rank, tie count and source margin;
6. Gate-A pass/fail details;
7. Gate-B G3-vs-G2 pass/fail details;
8. runtime/memory for G2/G3;
9. evidence SHA256;
10. confirmation: new GADEN=0, training=0, closed-loop=0.

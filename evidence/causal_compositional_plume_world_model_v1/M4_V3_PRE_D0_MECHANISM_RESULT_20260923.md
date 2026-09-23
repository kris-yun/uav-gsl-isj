# M4-v3 Pre-D0 Mechanism Contract Result

Date: 2026-09-23  
Branch: `research/m4-v3-interventional-evolution-propagator`  
Workflow run: `35870310955`  
Status: **STRUCTURAL MECHANISM CONTRACT PASS — D0 NOT YET RUN**

This result is synthetic/structural only. It does not use the S2×W2 development holdout and does not establish scientific ADVANCE.

## Tested invariants

- Source superposition max absolute error: `5.960464477539063e-08` — PASS.
- Positive/negative/zero wind impulse centroid column: `21 / 19 / 20` — reversal and no-advection PASS.
- In-domain mass balance with explicit sink numerically disabled:
  - mass in: `1.0`
  - mass out: `0.9999999403953552`
  - absolute error: `5.960464477539063e-08` — PASS.
- Solid-wall nonpenetration:
  - mass across wall: `0.0`
  - retained total mass: `1.0` — PASS.
- Transport forward signature:
  `state, wind_xy, free_mask, dt_s, cell_m`
  with no source ID/location/map conditioning — PASS.
- Exterior-boundary wrap value: `0.0` — PASS.
- GADEN float32 wind-index timing/loop emulation — PASS.

## Interpretation

The v3 transport now encodes the proposed mechanism before fitting:
1. source is an external forcing intervention;
2. wind changes a forward characteristic map;
3. obstacle crossings are prohibited;
4. local learned closure is conservative and source-agnostic;
5. fixed-environment transport is linear in source/concentration state;
6. nonnegative scalar mass is not created by remap/closure.

These properties are not evidence that the model predicts GADEN correctly. They only make the scientific hypothesis falsifiable without relying on post-hoc interpretation.

## D0 blocker

The exact House02 `3,5-1_slow` iterations 0–10 are not present in:
- the public/Library `GasSourceLocalization-humble.zip` inspected in this session;
- the TNQC V5/R2 140 MB delivery archive inspected in this session;
- GitHub global code search;
- the connected Google Drive keyword search.

The existing W2 iteration-1 hash remains the frozen anchor:
`54d7bc338ea681611f66004a3230f29feffc495446814607141b0623ef1dd9a8`.

No synthetic/reconstructed W2 sequence is authorized. The committed
`run_m4_v3_d0_remote.sh` will export the exact canonical sequence from the VM path and refuse the run if the iteration-1 hash does not match.

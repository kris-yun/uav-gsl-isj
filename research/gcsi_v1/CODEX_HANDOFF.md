# GCSI V1 — Codex / VGR VM handoff

Branch: `research/godambe-composite-source-inference-v1`

Current branch implementation files:

- `reference/gcsi_composite.py`
- `reference/gcsi_vgr_fixed_trajectory_replay.py`
- `reference/test_gcsi_composite.py`
- `reference/aggregate_gcsi_vgr_offline_gate.py`
- `reference/run_gcsi_vgr_offline_gate_20260922.sh`

## Scientific constraint

Do **not** rerun planner feedback or change PMFS.

GCSI V1 must first consume the exact frozen native six-case context banks already produced for TNQC V5:

- House01 seed0/1
- House02 seed0/1
- House03 seed0/1
- full 300 simulation seconds
- native PMFS `ExpectedValue(sourceProbability, 0.05)` endpoint
- source truth used only by the endpoint evaluator

## Preflight

```bash
git checkout research/godambe-composite-source-inference-v1
python3 reference/test_gcsi_composite.py
```

Expected:

```text
PASS: GCSI physical-block calibration is invariant to uniform subcell refinement
```

## Run on the existing native context banks

If the original TNQC native run root and linked endpoint evaluator still exist:

```bash
NATIVE_RUN_ROOT=/dev/shm/tnqc_vgr_300s_offline_20260920 \
ENDPOINT_EVAL_BIN=/dev/shm/tnqc_v5_300s_build/install/gsl_server/lib/gsl_server/tnqc_expected_value_native \
bash reference/run_gcsi_vgr_offline_gate_20260922.sh
```

If those paths have been cleaned, regenerate **native PMFS-only context banks with the already-frozen TNQC V5 runner first**. Do not modify source scoring before export.

## Frozen V1 choices

- physical block size: 0.9 m;
- native source-discrimination power: 1.0;
- pairwise block score is candidate-vs-native-best;
- spatial-block statistic is paired mean difference / block standard error;
- negative evidence against the native best is clipped to zero for V1;
- relative candidate log-weight is `-0.5*z^2`;
- simple block-count/cell-count global temperature is a mandatory control.

These choices are frozen for the six-case development gate. Do not sweep them after viewing truth.

## Advancement rule

Cheap Stage-2 GO requires:

- native posterior reconstruction pass in all six cases;
- pooled GCSI 300-s endpoint gain >= 2% vs native;
- >= 4/6 cases non-worse;
- worst pair degradation <= 25%;
- zero false-confident-collapse cases under the frozen audit;
- pooled GCSI endpoint must beat the simple scalar-temperature control.

This cheap gate only decides whether GCSI deserves further implementation.

The project's stronger >=10% target remains the paper-level bar unless a new independent protocol is explicitly frozen.

## Required output

Commit:

- all six `gcsi_v1_replay.json` files or a reproducible archive/reference;
- `gcsi_v1_300s_gate.json`;
- stdout/stderr logs;
- exact branch/commit;
- endpoint evaluator SHA-256;
- any execution failure without changing the frozen V1 equations.

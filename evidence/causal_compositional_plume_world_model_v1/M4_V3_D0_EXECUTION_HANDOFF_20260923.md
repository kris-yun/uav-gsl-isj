# M4-v3 D0 Execution Handoff

Date: 2026-09-23  
Branch: `research/m4-v3-interventional-evolution-propagator`

## Current state

- M4-v2: closed NO-GO as main.
- M4-v3 structural mechanism: PASS.
- W0 wind-direction semantic self-test: PASS.
- Historical PMFS/GMRF wind path: rejected as deployment evidence due confirmed downwind/upwind contract conflict plus parameter-interface mismatch.
- D0 House02: **NOT RUN**.
- Only missing D0 input: exact canonical House02 `3,5-1_slow` wind iterations 0–10 on the VM.

## Exact execution

From the repository root on the VM:

```bash
git switch research/m4-v3-interventional-evolution-propagator
git pull --ff-only
bash research/causal_compositional_plume_world_model_v1/run_m4_v3_d0_remote.sh
```

The runner itself verifies:
- correct branch;
- no tracked/staged source edits;
- exact canonical W1/W2 paths exist;
- W1/W2 iteration-1 frozen hashes match;
- exported dynamic-wind `.npy` hashes match their manifest;
- CPU deterministic D0 execution;
- checkpoints are written and hashed before S2-W2 targets are opened;
- output is not overwritten;
- model/trainer/exporter hashes and Git HEAD are recorded.

## Required return artifact

The decisive small file is:

`evidence/causal_compositional_plume_world_model_v1/m4_v3_d0_house02_20260923/d0_result.json`

Also preserve:
- `train_manifest.json`
- `m4v3_seed1729.pt`
- `m4v3_seed2718.pt`
- `M4_V3_D0_SHA256SUMS_20260923.txt`
- dynamic-wind manifest and both exported wind sequence arrays.

## Stop rule

If `decision == D0_FAIL_STOP_M4_V3`:
- do not generate House01/House03;
- do not tune v3 against S2-W2;
- do not run PMFS/ROS closed loop.

If `decision == D0_PASS_FREEZE_BEFORE_NEW_CONFIRMATION`:
- first freeze all v3 hashes and C1/C2 protocol;
- only then generate fresh House01/House03 confirmatory data.

House02 can never become confirmatory evidence.

# Codex start here — TNQC VGR 300-s offline gate first

The current candidate is **TNQC (Transport-Nuisance Quotient Canonicalization)**.

## Required order

Do **not** start the TNQC closed-loop matrix first.

The project-level offline gate is now the actual VGR/GADEN localization task:
House01/02/03 × seed0/1, full 300-s budget, final PMFS
`ExpectedValue(sourceProbability, 0.05)` error.

The Orebro3DSEN 2/5/10-min experiments are only an external representation
stress test. They are not a localization GO criterion.

Read in this order:

1. `docs/TNQC_VGR_300S_CORRECTION_20260920.md`
2. `docs/TNQC_CODEX_HANDOFF_20260920.md`
3. `docs/TNQC_OFFLINE_GATE_20260920.md` — auxiliary Orebro evidence only

## Stage 0 — build and replay self-test

Build the current `main` code with the existing VGR ROS2 toolchain, then run:

```bash
python3 reference/test_tnqc_vgr_fixed_trajectory_replay.py
```

Expected:

```text
TNQC_VGR_FIXED_TRAJECTORY_REPLAY_TEST_PASS
```

## Stage 1 — native full-budget VGR export + fixed-trajectory TNQC replay

Run:

```bash
bash reference/run_tnqc_vgr_offline_gate_20260920.sh
```

This deliberately runs `TNQC_MODE=off` only.  It uses the native 300-s
trajectory and native PMFS quadtree candidate bank, then applies TNQC
counterfactually offline.

Each House/seed replay must first pass the exact native-posterior reconstruction
audit.  Then the six-case aggregator applies the frozen GO rule:

- pooled final 300-s top-5% error improvement >= 10%;
- at least 4/6 paired cases improve;
- no pair degrades by more than 25%;
- no false-confident collapse;
- no native reconstruction audit failure.

The result is:

```
<run-root>/tnqc_vgr_300s_offline_gate.json
```

## Stage 2 — hard branch

If and only if the JSON contains:

```json
{"go_for_closed_loop": true}
```

commit the raw six replay JSONs plus the aggregate gate JSON and create a short
GO record.  Then proceed to the OFF/SHADOW determinism gate followed by the
full `off/shadow/fused/only` closed-loop matrix.

If it contains `false`, stop.  Do not tune TNQC from House truth and do not run
the closed-loop matrix as if the method had passed.

## No-touch list before Stage 1 finishes

Do not change:

- TNQC 1:1 continuous/local-order fusion;
- evidence bound ([-1,1]);
- local-edge definition;
- support rule;
- confidence weights;
- `exp(e_s)` modifier;
- `sourceDiscriminationPower=1.0`;
- `stepsSourceUpdate=3`;
- 300-s budget;
- PMFS planner, sensor or wind settings;
- House truth, starts or seed assignment.

Current scientific status before Stage 1 result:

**TNQC MECHANISM/CODE PATH READY — VGR 300-S LOCALIZATION SIGN NOT YET CLAIMED.**

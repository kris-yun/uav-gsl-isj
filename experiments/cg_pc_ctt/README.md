# CG-PC-CTT experimental workspace

This directory contains the 2026-08-27 offline qualification package for the candidate main innovation:

**Completeness-Gated Proximal-Causal Transport Tomography（完备性门控近端因果输运层析）**.

This is not merged into the frozen ME-ACI V10 implementation. The experiment must pass the offline falsification contract before any 300 s closed-loop integration.

## Start here

Read:

`CODEX_EXECUTION_PROTOCOL_20260827.md`

The protocol contains the frozen scientific question, data contracts, formulas, anti-leakage rules, threshold calibration, H02 hard challenge, proximal-bridge test, negative controls, GO/NO-GO criteria, and required result bundle.

## Files

- `compute_identifiability_gate.py` — label-free transport-uncertainty-whitened gate statistics `gamma` and `alpha`.
- `calibrate_gate_thresholds.py` — development-only threshold selection and freeze; prevents test-set retuning.
- `fit_proximal_bridge.py` — minimal cross-fitted two-stage ridge-IV proximal bridge baseline plus `Z`-shuffle negative control.
- `CODEX_EXECUTION_PROTOCOL_20260827.md` — authoritative execution contract.

## Python dependencies

```bash
python3 -m pip install numpy pandas scikit-learn
```

Use the existing VM environment if these are already installed; do not upgrade ROS/GADEN dependencies for this offline analysis.

## Checkout

```bash
git fetch origin
git checkout exp/cg-pc-ctt-identifiability-bridge-20260827
git rev-parse HEAD
```

Record the resulting SHA in `DATA_CONTRACT.md`.

## First run order

1. Convert the frozen House03 M1 bank into the long-form `m1_ensemble_long.csv` contract.
2. Run `compute_identifiability_gate.py` on development contexts/members.
3. Build the development hard-negative margin table.
4. Run `calibrate_gate_thresholds.py` and freeze `gate_thresholds_frozen.json`.
5. Run the frozen gate on held-out contexts/members.
6. Run the 28 historical H02 hard cases.
7. Only for gate-PASS cases, build the proximal bridge table and run `fit_proximal_bridge.py` plus negative controls.
8. Produce `RESULT_SUMMARY.md` with the exact verdict headings required by the protocol.
9. Do not start the 300 s closed loop unless both `G_id` and M2 satisfy the promotion criteria.

## Non-negotiable rule

A gate FAIL means exact abstention:

`q_t(s) = q_{t-1}(s)`.

Do not silently substitute a low-weight update. The scientific hypothesis is that non-identifiable evidence should not be allowed to sharpen the source posterior.

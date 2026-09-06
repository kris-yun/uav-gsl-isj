# CSTAR offline implementation status — 2026-09-06

Branch: `g3-cstar-causal-redesign-20260906`

## Current status

The offline execution layer is now implemented. This document does **not** claim a real-House PASS because the historical raw R4/seed12 trace CSV bodies are not committed to GitHub; the repository contains their hashes/provenance, while the files themselves remain VM assets.

## Implemented

- `experiments/ctpi_cstar/common/trace_io.py`
  - causal latest-at-or-before join of gas, pose and local wind;
  - flexible legacy trace header aliases;
  - no future pose/wind binding;
  - deterministic causal sensor-state summary for offline input.
- `experiments/ctpi_cstar/build_spent_manifest.py`
  - discovers the existing H01/H02/H03 seed12 A0/F00/F01 run directories without launching a simulator.
- `experiments/ctpi_cstar/m1_picr/offline.py`
  - trains PICR and a matched unconstrained ablation;
  - leave-one-House-out evaluation;
  - same-source nuisance/route invariance diagnostic;
  - source localization proper loss/error;
  - candidate domains are generated from the executed-route envelope, **not around ground-truth source coordinates**.
- `experiments/ctpi_cstar/m2_cpo/offline.py`
  - rolling fixed-trajectory future first-passage labels;
  - decision-time local wind only;
  - future route is the known action intervention; future measured gas is label only;
  - compares learned CPO against a frozen causal plume prior using NLL and Brier score.
- `experiments/ctpi_cstar/m3_phs/offline_panel.py`
  - consumes a true counterfactual panel with multiple routes per identical decision context;
  - refuses to reinterpret a single historical executed route as counterfactual evidence;
  - reports `M3_REAL_GATE_BLOCKED_ASSET_MISSING` when the required panel is absent.
- `experiments/ctpi_cstar/M3_COUNTERFACTUAL_PANEL_SCHEMA.json`
  - freezes the real M3 evaluator asset contract.
- `experiments/ctpi_cstar/run_offline_gates.py`
  - one orchestrator for M1/M2/M3;
  - formal closed-loop authorization is true only when all three module gates are true.
- `experiments/ctpi_cstar/run_spent_seed12_offline.sh`
  - one-command VM entry point for existing spent seed12 traces.
- `experiments/ctpi_cstar/selftest_offline_contracts.py`
  - verifies latest-at-or-before pose/wind binding;
  - verifies M1 candidate coordinates do not change when only evaluator source truth changes;
  - mutates post-decision future wind and verifies M2 decision features/prior remain unchanged.

The unified `run_reference_selftests.py` now includes these offline causal-contract tests.

## Local execution evidence in the assistant work environment

The new files were syntax-checked and the offline causal-contract selftest executed successfully:

`CSTAR_OFFLINE_CAUSAL_CONTRACT_SELFTEST PASS`

A deliberately simple three-source/three-nuisance synthetic dataset was also run through the M1 and M2 gates. Both returned `NO_GO` rather than being automatically accepted. This synthetic result is only a gate/implementation stress test and is **not** evidence for or against real GSL performance.

## Real-data blocker verified

The archived failure diagnostics list SHA-256 identities for the historical files such as:

- `H01_seed12_F00/sensor_trace.csv`
- `H01_seed12_F00/sim_pose_trace.csv`
- `H01_seed12_F00/wind_trace.csv`
- corresponding H02/H03 A0/F00/F01 files.

A direct GitHub contents lookup for the historical raw trace path returns 404, confirming that the CSV bodies are not available in this branch. They must be read from the VM/run archive to execute the real M1/M2 offline gates.

This is an asset-location limitation, not permission to regenerate outcomes or substitute synthetic PASS evidence.

## Exact VM command

```bash
cd /home/zyc/gsl_ws/src/GasSourceLocalization
git checkout g3-cstar-causal-redesign-20260906
git pull

RUN_ROOT=/path/to/the/spent/seed12/run/root \
OUT_ROOT=/path/to/fresh/cstar_offline_20260906 \
bash experiments/ctpi_cstar/run_spent_seed12_offline.sh
```

If a valid independent M3 panel already exists, add:

```bash
M3_PANEL=/path/to/CSTAR_M3_COUNTERFACTUAL_PANEL_V1.json
```

No GADEN House campaign is launched by these commands.

## Scientific stop line

- A missing raw trace asset is `BLOCKED_ASSET_MISSING`, not PASS or NO-GO.
- A failed M1/M2 metric is NO-GO; do not tune House/seed-specific weights until it passes.
- A single executed trajectory cannot establish M3 action superiority.
- Production ROS integration and formal A0/F00/F10/F11 closed loop remain unauthorized until real M1/M2/M3 evidence exists.

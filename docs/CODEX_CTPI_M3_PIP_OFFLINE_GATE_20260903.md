# Codex directive — CTPI M3 PIP offline action Gate

Authoritative branch: `research/ctpi-m3-pip-offline-gate-20260903`.
Parent M2 fresh-confirm PASS: `d808b4b37ba7eb4c99a4b34d18aa66b0019c6a75`.

## Scientific boundary

Do not redesign M1 or M2. M1 CREL is frozen PASS. M2 TSDC V0 is frozen PASS.
M3 PIP only ranks an already-feasible candidate-action set by posterior-weighted
expected information about source identity:

`I(S;Y|a)=H(sum_s pi_s q_sa)-sum_s pi_s H(q_sa)`

where `pi` is the frozen M1 F00/CREL carrier posterior and `q_sa` is the frozen
TSDC source/action detection committor.

This offline Gate is truth-blind and structural. It does not claim localization
improvement and runs no GADEN, C++, ROS, or closed loop.

## Inputs

Use the already-frozen Stage1 root:

`/home/zyc/CPIR_FACTORIAL_ROUTE_DIAGNOSTIC_20260901_e2bb4a0_R3/01_STAGE1`

Use the same frozen full-grid bank, historical OFF route root, and support file
that generated that Stage1 artifact. Do not regenerate any bank. If any path is
ambiguous, resolve it from the preserved Stage1 manifest / existing historical
assets; do not substitute a new route dataset or nearest-match file.

Required files:

- `experiments/cg_pc_ctt/ctpi_m2_tsdc_frozen_v0.py`
- `experiments/cg_pc_ctt/ctpi_m3_pip_frozen_v0.py`
- `tools/ctpi_m3_pip_offline_action_gate.py`
- `docs/CTPI_M3_PIP_OFFLINE_GATE_PREREG_20260903.json`

## Candidate-action contract

For each H01/H02/H03 seed0..9 and source update 1..4:

- use the frozen M1 F00 posterior for that update;
- candidate actions are all unvisited future stops in the same 15-stop historical route;
- preserve chronological candidate order;
- the first candidate is the historical next stop;
- exact score ties keep that first/native order;
- decision sensor state is the measured state at the END of the last completed visible dwell, before the next action begins.

Do not use update 5 because all 15 historical stops are already visible and no
future candidate remains.

The offline library tests only whether an informative, non-degenerate action
signal exists and whether the now-validated M2 TSDC changes the resulting action
policy. It does NOT claim that jumping directly to a later historical stop has
already been validated as a runtime transition; that is a later smoke/runtime
question.

## Execute

1. Verify M2 frozen SHA-256 is exactly
   `854a2fc8513201cdb2ae497a62c0cd3c5fa09fdae2f1bc309ad594a8b1aaacf7`.
2. Run `ctpi_m3_pip_frozen_v0.py` selftest and require PASS.
3. Run Python syntax/import checks for `ctpi_m3_pip_offline_action_gate.py`.
4. Run the offline action gate exactly once with frozen inputs.
5. Preserve the complete output directory and hashes.

Expected terminal is only one of:

- `CTPI_M3_PIP_OFFLINE_ACTION_GATE=PASS`
- `CTPI_M3_PIP_OFFLINE_ACTION_GATE=NO_GO`

On NO_GO, stop and do not tune M3 from these outputs.

On PASS, this authorizes only M3 runtime/parity development and preparation for
one true closed-loop smoke. It still does not prove a localization increment.
When M3 is later integrated into PMFS, preserve the native feasibility checks,
exploration cadence, and native navigation-cost term; PIP replaces the
information-interest signal rather than adding an outcome-tuned planner weight.

Formal claims require the later factorial closed-loop comparisons:

- M1 increment: `F00 vs A0`
- M3 increment: `F10 vs F00`
- M2 downstream increment under the same M3: `F11 vs F10`

Do not start formal multi-seed closed-loop until the true causal action chain is
verified in a smoke run.

# CPIR House-aware formal runner boundary — 2026-09-01

Status: `SOURCE_AND_WRAPPER_ALIGNED / VM_EXECUTION_PENDING`

This document follows `CPIR_PRECLOSEDLOOP_P0_FIXES_20260901.md`. It adds the missing House-specific observation-world wrapper required before any A0/A1/A2/A3 closed-loop smoke. It does **not** authorize the formal 9-pair experiment yet.

## Why a new wrapper was required

The frozen earlier paired runner `reference/run_meaci_case_20260824.sh` proves that the three Houses do not share one interchangeable observation backend or initial pose:

| House | config | source | frozen start | observation backend |
|---|---|---|---|---|
| H01 | `2,4-1_fast` | `(-0.40,-2.90,-0.30)` | `(-3.17,-1.75)` | `raw_house1_snapshot` |
| H02 | `3,5-1_fast` | `(0.00,-1.00,0.20)` | `(-0.50,-2.50)` | external `gaden_player` |
| H03 | `1-2,5_fast` | `(-0.45,1.90,-0.10)` | `(2.00,0.00)` | external `gaden_player` |

The generic CPIR launch has H01-oriented defaults and does not itself start the H02/H03 GADEN player and wind-value server. Therefore a direct launch could silently run H02/H03 with the wrong observation chain even while the CPIR inference code was correct.

## New runner

`closed_loop/cpir/run_cpir_formal_case_20260901.sh`

The same wrapper owns all four arms:

- `A0 -> pfdi_mode=off`
- `A1 -> cpir_a1`
- `A2 -> cpir_a2`
- `A3 -> cpir_a3`

For H02/H03 it starts the same external `gaden_player`/manual-iteration path and `wind_value_server.py` used by the frozen paired runtime, then waits fail-closed for `/frame_query` before launching VGR/GSL.

For H01 it requires the frozen raw query executable and retains the raw snapshot backend.

## Formal inputs that must be explicit

The wrapper refuses to run without:

- `HOUSE`
- `SEED`
- `ARM`
- `RUN_ROOT`
- `PFDI_INSTALL_ROOT`
- `INTEGRITY_REPORT`
- `STEPS_SOURCE_UPDATE`
- `MAX_WARMUP_ITERATIONS`
- `MIN_WARMUP_ITERATIONS`

The last three must be recovered from the exact authoritative paired PMFS runtime/parameter manifest. They are deliberately not inferred from the five-update development replay.

The wrapper executes `tools/cpir_formal_preflight.py` first, records the frozen bank/cell hashes into `formal_runtime_manifest.json`, and passes those hashes into the launch fail-closed provenance guard.

## Observation and inference contracts kept identical across A0/A1/A2/A3

The wrapper pins:

- House-specific source/config/start/backend;
- `flight_height=0.3`;
- `deltaTime=0.2`;
- `th_gas_present=0.1`;
- 80 native samples/physical stop (`8 x 10`);
- zero settle samples;
- `measurement_deduplicate_sim_timestamps=true`;
- `sensor_model_mode=dynamic`;
- sensor metadata `fopdt_tau1p2_dead0p4_noise0`;
- common PMFS movement/hit-map parameters;
- same experiment seed passed both as benchmark seed and GSL `seed`;
- CPIR posterior-guidance weight remains zero.

No temperature, alpha, Top-K, reliability gate, M2 parameter tuning, M3 pseudocount tuning or transport-member state is introduced.

## Still required before one closed-loop smoke

1. Build current branch HEAD in an isolated VM Release workspace.
2. Run both bank-free static selftests:
   - `experiments/cg_pc_ctt/selftest_cpir_three_module_contract.py`
   - `tools/selftest_cpir_formal_runner.py`
3. Recover and freeze the authoritative source-update/warmup contract.
4. Run H01/H02/H03 preflight on the existing banks; do not regenerate them.
5. C++ vs Python A1/A2/A3 posterior parity on one immutable H01 tape, then one H02 and H03 tape; target max absolute difference `<=1e-12`.
6. Live observation sensor impulse/step parity for M2.
7. Carrier-to-cell official-evaluator row/tie permutation audit.
8. Measure native planner refresh and CPIR posterior wall time.
9. Run the 30-pair fixed-trajectory nested ablation `A0 -> A1 -> A2 -> A3`.
10. Only if A2 has an independent increment over A1 and A3 has an independent increment over A2 across Houses may one paired closed-loop smoke be opened.

## Scientific boundary

The wrapper fixes experimental validity; it is not a fourth method module. The paper method remains exactly M1 + M2 + M3. House-specific GADEN process startup, bank hash validation, and paired runtime manifests are reproducibility infrastructure.

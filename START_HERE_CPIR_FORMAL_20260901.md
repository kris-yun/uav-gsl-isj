# START HERE — CPIR formal pre-closed-loop execution

Date: 2026-09-01

Current purpose: validate the already-generated H01/H02/H03 full-grid banks against the frozen M1/M2/M3 runtime and a controlled common PMFS planner. **Do not regenerate banks and do not start the 9-pair formal experiment yet.**

Read in this order:

1. `docs/CPIR_THREE_MODULE_THEORY_AND_FORMULA_FREEZE_20260831.md`
2. `docs/CPIR_THREE_MODULE_FORMULA_CONTRACT_20260831.json`
3. `docs/CPIR_PRECLOSEDLOOP_P0_FIXES_20260901.md`
4. `docs/CPIR_HOUSE_AWARE_FORMAL_RUNNER_20260901.md`
5. `docs/CPIR_PLANNER_INTERFACE_BOUNDARY_20260901.md`

Execution entry points:

- bank/read-only preflight: `tools/cpir_formal_preflight.py`
- static House-runner audit: `tools/selftest_cpir_formal_runner.py`
- House-aware paired runner: `closed_loop/cpir/run_cpir_formal_case_20260901.sh`
- three-module offline reference: `experiments/cg_pc_ctt/cpir_three_module_shadow.py`
- source/runtime contract selftest: `experiments/cg_pc_ctt/selftest_cpir_three_module_contract.py`

Before even one A0/A1/A2/A3 online smoke, recover the exact authoritative PMFS values for:

- `STEPS_SOURCE_UPDATE`
- `MAX_WARMUP_ITERATIONS`
- `MIN_WARMUP_ITERATIONS`

from the exact frozen paired PMFS runtime/parameter manifest. Do not infer them from the old five-update development replay.

Then:

1. build the current branch HEAD in an isolated VM Release workspace;
2. run both bank-free selftests;
3. run H01/H02/H03 bank preflight with the recovered runtime values;
4. prove Python/C++ A1/A2/A3 posterior parity on immutable tapes;
5. prove live M2 sensor impulse/step parity;
6. run official evaluator tie/row-order audit;
7. run the 30-pair nested fixed-trajectory A0/A1/A2/A3 analysis;
8. only then open one paired online smoke.

The paper method remains exactly M1 + M2 + M3. Bank verification, House process startup, I-projection, and the fixed PMFS controller are interfaces/reproducibility infrastructure, not extra innovations.

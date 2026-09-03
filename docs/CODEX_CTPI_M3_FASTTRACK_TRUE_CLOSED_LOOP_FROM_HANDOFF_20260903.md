# Codex — CTPI M3 Fast-Track True Closed Loop from Frozen Handoff

## Authority

Repository: `kris-yun/uav-gsl-isj`

Branch: `research/ctpi-m3-fasttrack-20260903`

Use the **exact final handoff HEAD supplied in the ChatGPT handoff message**. Do not reconstruct files from an older worktree and do not continue any uncommitted local M3 edits.

Scientific state at handoff:

- M1 CREL/F00: confirmed PASS.
- M2 TSDC V0: fresh-confirm PASS and frozen.
- M3 PIP: formula, action domain, runtime mapping and Gates frozen before true-closed-loop outcomes.
- No new M2/M3 training data are authorized.
- No true-closed-loop outcome has been used to tune this fast-track implementation.

The only remaining job is VM execution: clean materialization/build, bank verification, H01 seed0 smoke, then gated performance runs.

## Non-negotiable rules

Do not change any M1/M2/M3 formula, TSDC beta, action domain, tie-break, cadence, runtime horizon, planner weight, threshold, bank, or Gate.

Do not add a fallback when an M3 action cannot be forecast or when a Gate fails. Fail closed and report the blocker.

Do not use source truth, localization error, future gas, future wind, or future route data inside the planner. Truth is allowed only in the post-run performance evaluator already frozen in the repository.

Do not regenerate the predictive bank.

The frozen runtime cadence for every arm is exactly:

- `stepsSourceUpdate=3`
- `maxWarmupIterations=3`
- `minWarmupIterations=1`

The closed-loop performance horizon is exactly 240 s.

## Phase 0 — clean authoritative checkout

Start from a new isolated worktree/clone. The target checkout must be clean and must not already contain the generated files:

- `closed_loop/ctpi/vgr_gsl_pmfs_ctpi_fasttrack.launch.py`
- `closed_loop/ctpi/run_ctpi_fasttrack_case_safe_20260903.sh`

Run:

```bash
python3 tools/ctpi_m3_fasttrack_handoff_check.py \
  --repo-root "$PWD" \
  --output /tmp/CTPI_M3_FASTTRACK_HANDOFF_CHECK.json
```

Required terminal line:

`CTPI_M3_FASTTRACK_CODEX_HANDOFF=PASS`

If this does not PASS, stop. Do not repair scientific files locally.

## Phase 1 — materialize, patch, parity, Release build

Choose a fresh build root. Example only:

```bash
export REPO_ROOT="$PWD"
export BUILD_ROOT=/dev/shm/ctpi_m3_fasttrack_build_20260903
rm -rf "$BUILD_ROOT"   # only if this path was created for this attempt and contains no prior evidence
bash closed_loop/ctpi/prepare_ctpi_m3_fasttrack_vm_20260903.sh
```

The prepare script must itself refuse a pre-existing build root. Prefer a genuinely new path instead of deleting one.

Required terminal line:

`CTPI_M3_FASTTRACK_VM_BUILD=PASS`

The script performs frozen launch/runner materialization, runtime patch application, source/hash preflight, TSDC selftest, M3 selftest, Python/C++ formula parity, truth-blind static check and Release `colcon` build. Do not bypass a failed check.

Use the emitted `PFDI_INSTALL_ROOT=<BUILD_ROOT>` for all later runs.

## Phase 2 — verify the three existing banks, no regeneration

Choose a fresh bank-audit output root:

```bash
export BANK_AUDIT_ROOT=/dev/shm/ctpi_m3_fasttrack_bank_audit_20260903
REPO_ROOT="$REPO_ROOT" OUT_ROOT="$BANK_AUDIT_ROOT" \
  bash closed_loop/ctpi/verify_ctpi_fasttrack_banks_vm_20260903.sh
```

Required terminal line:

`CTPI_FASTTRACK_ALL_BANKS_INTEGRITY=PASS`

The integrity reports used later are:

- `$BANK_AUDIT_ROOT/H01_CPIR_LOOKUP_INTEGRITY.json`
- `$BANK_AUDIT_ROOT/H02_CPIR_LOOKUP_INTEGRITY.json`
- `$BANK_AUDIT_ROOT/H03_CPIR_LOOKUP_INTEGRITY.json`

## Phase 3 — H01 seed0 true-closed-loop smoke only

Do not start 12-run or 36-run work before this smoke passes.

Use a fresh run root:

```bash
export SMOKE_ROOT=/dev/shm/ctpi_m3_h01_seed0_smoke_<fresh_id>
REPO_ROOT="$REPO_ROOT" \
RUN_ROOT="$SMOKE_ROOT" \
PFDI_INSTALL_ROOT="$BUILD_ROOT" \
INTEGRITY_REPORT="$BANK_AUDIT_ROOT/H01_CPIR_LOOKUP_INTEGRITY.json" \
DOMAIN_ID=230 \
  bash closed_loop/ctpi/run_ctpi_h01_seed0_smoke_20260903.sh
```

Each F00/F10/F11 arm must first pass `CTPI_FASTTRACK_CASE_TERMINAL=PASS`. F10 and F11 must additionally pass `CTPI_M3_ACTION_SANITY=PASS`.

The smoke is authorized only if the final causal checker prints:

`TRUE_CLOSED_LOOP_CAUSAL_CHAIN=PASS`

and the wrapper prints:

`CTPI_H01_SEED0_SMOKE=PASS`

The causal chain must demonstrate posterior -> M3 action -> navigation command -> physical motion -> fresh sensor observation -> updated posterior -> next action. F10 and F11 must each differ from F00 in at least one navigation action.

If smoke fails for a scientific or runtime reason, stop and package the evidence. Do not tune the planner or TSDC.

## Phase 4 — H01 seeds0-2 12-run screening

Only after the smoke passes, run the pre-registered screening set:

- H01
- seeds 0,1,2
- A0/F00/F10/F11
- 12 total runs

Use a new run root, not the smoke root:

```bash
export SCREEN_ROOT=/dev/shm/ctpi_m3_h01_screen_<fresh_id>
REPO_ROOT="$REPO_ROOT" \
RUN_ROOT="$SCREEN_ROOT" \
PFDI_INSTALL_ROOT="$BUILD_ROOT" \
INTEGRITY_REPORT="$BANK_AUDIT_ROOT/H01_CPIR_LOOKUP_INTEGRITY.json" \
DOMAIN_ID=230 \
  bash closed_loop/ctpi/run_ctpi_h01_3seed_screen_20260903.sh
```

Required authorization for formal cross-House work:

`CTPI_FASTTRACK_H01_3SEED_SCREEN=PASS`

The screening set is development/screening evidence only. Seeds 0-2 must never be counted as the formal cross-House confirmation.

## Phase 5 — 36-run cross-House confirmation

Only if the screening Gate PASS file explicitly sets `formal_crosshouse_authorized=true`, run:

- H01/H02/H03
- fresh confirmation seeds 3,4,5
- A0/F00/F10/F11
- 36 total runs

```bash
export CONFIRM_ROOT=/dev/shm/ctpi_m3_crosshouse_confirm_<fresh_id>
REPO_ROOT="$REPO_ROOT" \
RUN_ROOT="$CONFIRM_ROOT" \
PFDI_INSTALL_ROOT="$BUILD_ROOT" \
H01_SCREEN_GATE="$SCREEN_ROOT/H01_3SEED_SCREEN_GATE.json" \
INTEGRITY_H01="$BANK_AUDIT_ROOT/H01_CPIR_LOOKUP_INTEGRITY.json" \
INTEGRITY_H02="$BANK_AUDIT_ROOT/H02_CPIR_LOOKUP_INTEGRITY.json" \
INTEGRITY_H03="$BANK_AUDIT_ROOT/H03_CPIR_LOOKUP_INTEGRITY.json" \
DOMAIN_ID=230 \
  bash closed_loop/ctpi/run_ctpi_crosshouse_36run_confirm_20260903.sh
```

The frozen evaluator performs the exact 2^9 sign-flip randomization test for the three increments:

- M1: F00 vs A0
- M3: F10 vs F00
- M2 downstream robot-task value: F11 vs F10

Terminal scientific verdict is exactly one of:

- `CTPI_CROSSHOUSE_36RUN_CONFIRM=PASS`
- `CTPI_CROSSHOUSE_36RUN_CONFIRM=NO_GO`

Do not alter the Gate after seeing any outcome.

## Evidence to return

For every attempted phase, preserve:

- exact Git HEAD
- handoff checker JSON
- source preflight/build JSON and build log
- bank integrity JSONs
- formal runtime manifests
- run_status JSONs
- navigation, pose, sensor and source-estimate traces
- F10/F11 M3 action audits and action-sanity JSONs
- causal-chain JSONs
- screening performance/Gate JSON if Phase 4 ran
- 36-run confirmatory JSON if Phase 5 ran
- SHA-256 manifest of the evidence package

If the VM is missing an expected dependency/path, report `BLOCKED_BY_VM_ENVIRONMENT` with exact missing paths. Do not modify frozen scientific code to make the environment pass.

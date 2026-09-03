# CTPI M3 fast-track — resume after Codex quota exhaustion

## Read this first

Repository: `kris-yun/uav-gsl-isj`

Branch: `research/ctpi-m3-fasttrack-20260903`

Runtime/build anchor that already passed committed Release build and all three bank integrity checks:

`c4445ee69d478f48ada19dfb9425726ab78c2d33`

Machine-readable continuation state:

`docs/CTPI_M3_FASTTRACK_AGENT_HANDOFF_AFTER_CODEX_QUOTA_20260903.json`

Do not restart scientific design. Do not redo M2 confirmation. Do not modify M1/M2/M3 unless a later scientific Gate explicitly returns NO-GO and a new research cycle is authorized.

## What is already finished

The prior Codex agent completed the following before quota exhaustion:

- V5 environment-autonomy setup.
- Rebuilt missing non-scientific ROS message packages `olfaction_msgs` and `gsl_actions` in an isolated overlay.
- Qualified the historical GADEN install at `/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/gaden_install`.
- Fixed CMake environment discovery for system `spdlog` and `fmt` without changing scientific code.
- Resolved parallel-build OOM by serializing the Release build.
- Resolved excessive debug/sanitizer build-memory overhead with the repository's low-memory Release option while retaining `-O3` runtime optimization and unchanged scientific equations.
- Resolved `/dev/shm` prototype storage exhaustion and reran from a fresh committed checkout.
- Corrected a post-build binary identity false-negative caused by `pipefail + grep -q`; the same binary contains exact `ctpi_f10` and `ctpi_f11` strings.
- Pushed the reproducible environment recovery to GitHub.
- Created a fresh checkout at `c4445ee69d478f48ada19dfb9425726ab78c2d33`.
- Re-ran Phase 0 / environment-only anti-drift Gates: PASS.
- Re-ran runtime patch materialization/application, TSDC/PIP selftests, Python/C++ parity, and truth-blind source preflight: PASS.
- Built the authoritative frozen `gsl_server` Release binary: PASS.
- Reverified H01/H02/H03 frozen full-grid predictive banks: PASS for all three Houses.

No H01 F00/F10/F11 arm outcome has been generated yet.

## Scientific state — frozen

- M1 CREL / F00: **CONFIRMED PASS**.
- M2 TSDC V0: **fresh-confirm PASS and frozen**.
- M3 PIP: **frozen for true closed-loop test**.
- True closed-loop outcome: **not yet observed**.

Frozen runtime:

- `stepsSourceUpdate = 3`
- `maxWarmupIterations = 3`
- `minWarmupIterations = 1`
- performance horizon = `240 s`
- M3 horizontal speed = `0.4 m/s`
- `dt = 0.2 s`
- dwell = `80` samples
- predictive bank horizon = `1500` samples

Arms:

- A0 = native PMFS
- F00 = M1 + native planner
- F10 = M1 + raw finite-8 forecast + same PIP planner
- F11 = M1 + frozen TSDC + same PIP planner

## Current exact blocker

The first H01 seed0 smoke invocation stopped **before any arm run began** because the frozen H01 runner requires:

`/dev/shm/house1_raw_query`

That historical temporary executable/path is currently missing.

H01 must retain the frozen gas backend semantics:

`raw_house1_snapshot`

Do not bypass the guard by switching H01 to another gas backend.

GitHub history contains runner references to `/dev/shm/house1_raw_query`, but no authoritative builder for the executable was found in repository code search. Therefore recover its provenance on the VM rather than inventing a new physical observation backend.

## Next task — environment/interface recovery only

You are authorized to continue autonomously on VM environment/interface issues until a scientific/runtime Gate or a true H01 smoke result is reached.

First inspect, read-only where possible:

- `/home/zyc/CTPI_M3_FASTTRACK_TRUE_CLOSED_LOOP_20260903_R8_C4445EE/`
- older `/home/zyc/CTPI_*`, `/home/zyc/PF_DEI_*`, `/home/zyc/CPIR_*` workdirs
- shell history / command logs
- `/home/zyc/ros2_ws/src`
- `/mnt/hgfs/workspace`
- archived evidence directories
- executable files / scripts mentioning House01, raw snapshot, query, gas concentration, or `house1_raw_query`

Determine exactly what `/dev/shm/house1_raw_query` was and reconstruct the same interface. Permitted recovery actions include:

- rebuilding an existing historical helper from its original source;
- creating a compatibility symlink to the exact recovered executable;
- rebuilding non-scientific dependencies in an isolated overlay;
- creating reproducible environment wrapper scripts.

Before using the recovered executable, record:

- provenance/source path;
- build command if rebuilt;
- SHA-256;
- `file`/ELF identity if applicable;
- `ldd` unresolved dependencies;
- minimal deterministic invocation/probe showing it is executable and matches expected H01 raw-query interface.

Do not touch the bank during this recovery.

## Reuse the already successful committed build if it still exists

Expected VM artifacts from the prior agent:

- repo: `/home/zyc/CTPI_M3_FASTTRACK_TRUE_CLOSED_LOOP_20260903_R8_C4445EE/repo`
- build: `/dev/shm/ctpi_m3_fasttrack_build_v5_c4445ee`
- runtime environment: `/dev/shm/ctpi_m3_fasttrack_build_v5_c4445ee/ctpi_prepare_audit/CTPI_VM_ENV.sh`
- bank audit: `/dev/shm/ctpi_m3_fasttrack_bank_audit_v5_c4445ee`
- H01 integrity report: `/dev/shm/ctpi_m3_fasttrack_bank_audit_v5_c4445ee/H01_CPIR_LOOKUP_INTEGRITY.json`

If those still exist and their manifests/hashes are valid, reuse them. Do **not** rebuild just because a new documentation-only handoff commit exists.

If `/dev/shm` artifacts were lost, rebuild/reverify from runtime anchor `c4445ee69d478f48ada19dfb9425726ab78c2d33` using the committed environment-autonomy workflow; do not modify science.

## Resume H01 seed0 smoke

After `house1_raw_query` is restored and validated, use a **new** smoke root. Do not reuse the failed pre-arm root.

Suggested pattern:

```bash
ROOT=/home/zyc/CTPI_M3_FASTTRACK_TRUE_CLOSED_LOOP_20260903_R8_C4445EE
export REPO_ROOT="$ROOT/repo"
export PFDI_INSTALL_ROOT=/dev/shm/ctpi_m3_fasttrack_build_v5_c4445ee
export INTEGRITY_REPORT=/dev/shm/ctpi_m3_fasttrack_bank_audit_v5_c4445ee/H01_CPIR_LOOKUP_INTEGRITY.json
export RUN_ROOT=/dev/shm/ctpi_m3_h01_seed0_smoke_c4445ee_resume1
export DOMAIN_ID=230
source "$PFDI_INSTALL_ROOT/ctpi_prepare_audit/CTPI_VM_ENV.sh"
bash "$REPO_ROOT/closed_loop/ctpi/run_ctpi_h01_seed0_smoke_20260903.sh"
```

Required smoke Gates:

- every arm: `CTPI_FASTTRACK_CASE_TERMINAL=PASS`
- F10/F11: `CTPI_M3_ACTION_SANITY=PASS`
- full causal chain: `TRUE_CLOSED_LOOP_CAUSAL_CHAIN=PASS`
- overall: `CTPI_H01_SEED0_SMOKE=PASS`

If a scientific/runtime Gate fails, stop and preserve evidence. Environment-only failures may be repaired autonomously while keeping science frozen.

## If H01 smoke passes

Immediately run the preregistered screening:

H01 seeds `0,1,2` × `A0/F00/F10/F11` = 12 runs.

Required terminal:

`CTPI_FASTTRACK_H01_3SEED_SCREEN=PASS`

Only if that passes, run formal confirmation:

H01/H02/H03 × seeds `3,4,5` × `A0/F00/F10/F11` = 36 runs.

Final scientific terminal must be exactly one of:

- `CTPI_CROSSHOUSE_36RUN_CONFIRM=PASS`
- `CTPI_CROSSHOUSE_36RUN_CONFIRM=NO_GO`

Do not reuse screen seeds 0–2 in formal confirmation.

## Forbidden changes

Do not:

- change M1 formula;
- refit or alter TSDC beta/features;
- change M3 information objective;
- change candidate action domain or tie-break;
- change 3/3/1 cadence;
- change 240 s horizon;
- add planner weights/temperature;
- use truth or future observation in planner;
- regenerate predictive bank;
- change Gate after seeing results;
- replace `raw_house1_snapshot` with another H01 observation backend;
- continue past a required scientific/runtime Gate failure.

## GitHub requirement before handing off again

Commit and push every reproducible environment/interface recovery needed for `house1_raw_query`, plus a short machine-readable manifest containing:

- runtime anchor commit;
- recovered query provenance + SHA-256;
- build binary SHA-256;
- bank audit references;
- smoke/screen/formal evidence locations and terminal verdicts reached;
- confirmation that scientific files remained unchanged.

Keep the same branch unless there is a strong repository reason not to:

`research/ctpi-m3-fasttrack-20260903`

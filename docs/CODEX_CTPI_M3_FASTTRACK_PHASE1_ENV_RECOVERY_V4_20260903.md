# Codex — CTPI M3 fast-track Phase 1 VM environment recovery V4

Use repository `kris-yun/uav-gsl-isj`, branch `research/ctpi-m3-fasttrack-20260903`, and the exact V4 HEAD supplied by ChatGPT.

The previous Phase 1 failure was classified `BLOCKED_BY_VM_ENVIRONMENT`. Scientific/runtime preflight had already passed; the Release build failed because `gaden_msgsConfig.cmake` was unavailable from the then-active overlay.

## Frozen environment recovery

The only newly authorized GADEN candidate is:

`/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/gaden_install`

Do not choose any other overlay and do not modify M1/M2/M3 scientific code.

From a fresh clean checkout at the exact V4 HEAD, first rerun the ordinary Phase 0 V3 handoff checker. It must still report:

`CTPI_M3_FASTTRACK_CODEX_HANDOFF=PASS`

Then run the environment-only handoff checker:

```bash
python3 tools/ctpi_m3_fasttrack_env_recovery_check.py \
  --repo-root "$PWD" \
  --output /tmp/CTPI_M3_FASTTRACK_ENV_RECOVERY_HANDOFF.json
```

Required:

`CTPI_M3_FASTTRACK_ENV_RECOVERY_HANDOFF=PASS`

## Phase 1 retry

Use a completely fresh BUILD_ROOT. Do not reuse the failed build tree.

```bash
export REPO_ROOT="$PWD"
export BUILD_ROOT=/dev/shm/ctpi_m3_fasttrack_build_v4_<fresh_id>
export PREP_AUDIT_ROOT="$BUILD_ROOT/ctpi_prepare_audit"
export CTPI_GADEN_OVERLAY_ROOT=/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/gaden_install

bash closed_loop/ctpi/prepare_ctpi_m3_fasttrack_vm_20260903.sh
```

Before `colcon build`, the prepare script must independently emit:

`CTPI_VM_DEPENDENCY_QUALIFICATION=PASS`

The qualification report is:

`$PREP_AUDIT_ROOT/VM_DEPENDENCY_QUALIFICATION.json`

The deterministic runtime environment is:

`$PREP_AUDIT_ROOT/CTPI_VM_ENV.sh`

The build must then emit:

`CTPI_M3_FASTTRACK_VM_BUILD=PASS`

If either qualification or build fails, stop and return the exact failed checks/logs. Do not select another overlay locally.

## After build PASS

Before Phase 2/3 in each new shell, source:

```bash
source "$BUILD_ROOT/ctpi_prepare_audit/CTPI_VM_ENV.sh"
```

The prepare script may create `/dev/shm/house2_gaden_install` only as a symlink to the exact qualified overlay, and only if the path is absent or already resolves to the same overlay. Existing non-symlink content or a different symlink target is a hard failure.

Then continue the already frozen sequence: bank integrity -> H01 seed0 smoke -> H01 12-run screening -> 36-run cross-House confirmation, with all previous fail-closed Gates unchanged.

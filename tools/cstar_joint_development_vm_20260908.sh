#!/usr/bin/env bash
# Isolated development tests and refreshed environmental input probes only.
# No protected bank, old result directory, or legacy build is modified.
set -e -o pipefail
test "$#" -eq 2 || { echo 'usage: script PATCH_TAR BASE_COMMIT'; exit 2; }
CSTAR_JOINT_ROOT=/dev/shm/cstar_joint_development_20260908
test ! -e "$CSTAR_JOINT_ROOT"
mkdir "$CSTAR_JOINT_ROOT"
cp -a /dev/shm/CSTAR_ENV_RUNTIME_20260907/. "$CSTAR_JOINT_ROOT/"
tar -xf "$1" -C "$CSTAR_JOINT_ROOT"
cd "$CSTAR_JOINT_ROOT"
export PYTHONDONTWRITEBYTECODE=1 PYTHONUTF8=1 PYTHONIOENCODING=utf-8
export CSTAR_RUNTIME_ARCHIVE_COMMIT="$2"
export CSTAR_RUNTIME_OUT=evidence/cstar_joint_development_20260908
mkdir -p "$CSTAR_RUNTIME_OUT"
python3 experiments/ctpi_cstar/selftest_sequential_joint.py > "$CSTAR_RUNTIME_OUT/joint_tests.log" 2>&1
export CSTAR_RUNTIME_OUT=evidence/cstar_joint_environment_20260908
bash tools/cstar_verify_environment_runtime_vm.sh /home/zyc/CSTAR_CONTROLLED_ASSETS_20260907/tools/cstar_numeric_wind_raw_query
python3 tools/cstar_verify_joint_launch_vm.py --preflight "$CSTAR_RUNTIME_OUT/PREFLIGHT.json" \
    --out evidence/cstar_joint_development_20260908/LAUNCH_BINDING.json
bash tools/cstar_probe_reusable_environment_vm.sh "$CSTAR_RUNTIME_OUT/PREFLIGHT.json" \
    /home/zyc/CSTAR_CONTROLLED_ASSETS_20260907/tools/cstar_numeric_wind_raw_query \
    evidence/cstar_joint_live_20260908
echo JOINT_DEVELOPMENT_TESTS_AND_STATIONARY_ENVIRONMENT_PROBES_COMPLETE

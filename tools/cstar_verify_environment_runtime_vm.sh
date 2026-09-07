#!/usr/bin/env bash
# Read-only data audit in the checkout containing this script. No ROS launches.
set -e -o pipefail
CSTAR_RUNTIME_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$CSTAR_RUNTIME_ROOT"
test "$#" -eq 1 || { echo 'usage: cstar_verify_environment_runtime_vm.sh QUALIFIED_HELPER'; exit 2; }
export PYTHONDONTWRITEBYTECODE=1 PYTHONUTF8=1 PYTHONIOENCODING=utf-8
CSTAR_RUNTIME_OUT="${CSTAR_RUNTIME_OUT:-evidence/cstar_reusable_environment_20260907}"
test ! -e "$CSTAR_RUNTIME_OUT"
mkdir -p "$CSTAR_RUNTIME_OUT"
python3 -m experiments.ctpi_cstar.selftest_environment_runtime 2>&1 | tee "$CSTAR_RUNTIME_OUT/selftests.log"
python3 tools/cstar_check_environment_runtime.py \
  --split experiments/ctpi_cstar/CSTAR_RAW_REALIZATION_SPLITS_FROZEN_20260906.json \
  --geometry evidence/cstar_environment_20260906/maps_v1/geometry_manifest.json \
  --sensor-manifest evidence/cstar_environment_20260906/probes_v1/H01/sensor_manifest.json \
  --clock experiments/ctpi_cstar/CSTAR_ENVIRONMENT_CLOCK_V1.json \
  --helper "$1" \
  --helper-attestation evidence/cstar_controlled_assets_20260907_r2/WIND_INDEX_CORRECTION_AUDIT.json \
  --controlled-data evidence/cstar_controlled_assets_20260907_r2 \
  --out "$CSTAR_RUNTIME_OUT/PREFLIGHT.json" 2>&1 | tee "$CSTAR_RUNTIME_OUT/preflight.log"
if git -C "$CSTAR_RUNTIME_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git rev-parse HEAD > "$CSTAR_RUNTIME_OUT/code_commit.txt"
else
  # A git-archive extraction on tmpfs is allowed on a full VM system disk.
  # The preflight independently binds the actual code bytes as well.
  test -n "${CSTAR_RUNTIME_ARCHIVE_COMMIT:-}"
  printf '%s\n' "$CSTAR_RUNTIME_ARCHIVE_COMMIT" > "$CSTAR_RUNTIME_OUT/code_commit.txt"
fi

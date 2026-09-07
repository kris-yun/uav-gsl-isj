#!/usr/bin/env bash
# Three bounded input probes, not navigation or scientific closed-loop arms.
set -e -o pipefail
CSTAR_PROBE_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$CSTAR_PROBE_ROOT"
test "$#" -eq 3 || { echo 'usage: script PREFLIGHT QUALIFIED_HELPER OUT'; exit 2; }
source tools/cstar_environment_vm_dependencies.sh
export PYTHONDONTWRITEBYTECODE=1 PYTHONUTF8=1 PYTHONIOENCODING=utf-8
test ! -e "$3"
mkdir -p "$3"
export ROS_LOG_DIR="$CSTAR_PROBE_ROOT/$3/ros_logs"
mkdir -p "$ROS_LOG_DIR"
for CSTAR_PROBE_HOUSE in H01 H02 H03; do
  python3 tools/cstar_run_environment_house.py --house "$CSTAR_PROBE_HOUSE" \
    --geometry-manifest "$CSTAR_PROBE_ROOT/evidence/cstar_environment_20260906/maps_v1/geometry_manifest.json" \
    --environment-preflight "$1" --raw-query-executable "$2" \
    --out "$3/$CSTAR_PROBE_HOUSE" > "$3/${CSTAR_PROBE_HOUSE}_console.log" 2>&1
  printf '%s input probe PASS\n' "$CSTAR_PROBE_HOUSE"
done

#!/usr/bin/env bash
set -Eeuo pipefail
REPO_ROOT="${REPO_ROOT:-/home/zyc/gsl_ws/src/GasSourceLocalization}"
RUN_ROOT="${RUN_ROOT:?set RUN_ROOT to the spent H01/H02/H03 seed12 run root}"
OUT_ROOT="${OUT_ROOT:?set a fresh OUT_ROOT}"
M3_PANEL="${M3_PANEL:-}"
[[ ! -e "${OUT_ROOT}" ]] || { echo "CSTAR_SPENT_REFUSE_EXISTING_OUT_ROOT=${OUT_ROOT}" >&2; exit 70; }
mkdir -p "${OUT_ROOT}"
python3 "${REPO_ROOT}/experiments/ctpi_cstar/build_spent_manifest.py" \
  --run-root "${RUN_ROOT}" --output "${OUT_ROOT}/SPENT_EPISODES.json"
args=(--manifest "${OUT_ROOT}/SPENT_EPISODES.json" --out-dir "${OUT_ROOT}/gates")
if [[ -n "${M3_PANEL}" ]]; then
  args+=(--m3-panel "${M3_PANEL}")
fi
python3 "${REPO_ROOT}/experiments/ctpi_cstar/run_offline_gates.py" "${args[@]}"

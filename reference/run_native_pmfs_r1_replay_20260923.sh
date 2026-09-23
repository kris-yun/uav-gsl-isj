#!/usr/bin/env bash
set -Ee -o pipefail

# Only source-blind inputs are opened before the freeze. The truth evaluator is
# a separate command and refuses to run without the frozen manifest.
RUN_DIR="${1:?R1 run directory required}"
ROOT="${NATIVE_RECOVERY_ROOT:-/home/zyc/native_pmfs_recovery_v1}"
[[ -f "${RUN_DIR}/gmrf_wind_at_update.csv" && -f "${RUN_DIR}/source_update_complete.txt" ]] || exit 64
[[ ! -e "${RUN_DIR}/r1_scores_frozen_manifest.json" ]] || exit 65
source /opt/ros/humble/setup.bash
source /home/zyc/ros2_ws/install/setup.bash
source "${ROOT}/install/setup.bash"
set -u
export OMP_NUM_THREADS=1
BIN="${ROOT}/install/gsl_server/lib/gsl_server/native_pmfs_r1_forward_replay"
[[ -x "${BIN}" ]] || exit 66
for arm in A B C; do
  for suffix in '' _repeat; do
    output="${RUN_DIR}/R1_arm_${arm}${suffix}"
    [[ ! -e "${output}" ]] || { echo "R1 replay output exists: ${output}" >&2; exit 67; }
    "${BIN}" "${RUN_DIR}" "${arm}" "${output}" \
      >"${RUN_DIR}/R1_arm_${arm}${suffix}.log" 2>&1
    cat "${RUN_DIR}/R1_arm_${arm}${suffix}.log"
  done
done
python3 "${ROOT}/freeze_native_pmfs_r1_scores_20260923.py" "${RUN_DIR}" --replay-binary "${BIN}"

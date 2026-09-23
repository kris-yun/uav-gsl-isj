#!/usr/bin/env bash
set -Ee -o pipefail

# Post-unblinding source repair: replay A/B with the frozen R2 event-keyed
# transport kernel. No parameters, snapshot, wind cells or candidate geometry
# are selected using truth. C is the already-frozen official-source replay.
ORIGINAL="${1:?original R1 run root required}"
CORRECTED="${2:?new corrected R1 output root required}"
ROOT="${NATIVE_RECOVERY_ROOT:-/home/zyc/native_pmfs_recovery_v1}"
[[ ! -e "${CORRECTED}" ]] || { echo "corrected output exists" >&2; exit 64; }
source /opt/ros/humble/setup.bash
source /home/zyc/ros2_ws/install/setup.bash
source "${ROOT}/r2_reference_build/install/setup.bash"
source "${ROOT}/install/setup.bash"
set -u
R2_BIN="${ROOT}/r2_reference_build/install/gsl_server/lib/gsl_server/native_pmfs_r1_r2_forward_replay"
OFFICIAL_BIN="${ROOT}/install/gsl_server/lib/gsl_server/native_pmfs_r1_forward_replay"
[[ -x "${R2_BIN}" && -x "${OFFICIAL_BIN}" ]] || exit 65
mkdir -p "${CORRECTED}"
for name in measurement_events.csv measured_map_at_update.csv frozen_candidate_geometry.csv wind_source_update.csv gmrf_wind_at_update.csv; do
  cp "${ORIGINAL}/${name}" "${CORRECTED}/${name}"
done
cp -a "${ORIGINAL}/R1_arm_C" "${CORRECTED}/R1_arm_C"
cp -a "${ORIGINAL}/R1_arm_C_repeat" "${CORRECTED}/R1_arm_C_repeat"
export OMP_NUM_THREADS=1
for arm in A B; do
  for suffix in '' _repeat; do
    output="${CORRECTED}/R1_arm_${arm}${suffix}"
    "${R2_BIN}" "${CORRECTED}" "${arm}" "${output}" \
      >"${CORRECTED}/R1_arm_${arm}${suffix}.log" 2>&1
    cat "${CORRECTED}/R1_arm_${arm}${suffix}.log"
  done
done
python3 "${ROOT}/freeze_native_pmfs_r1_scores_20260923.py" "${CORRECTED}" \
  --replay-binary "${OFFICIAL_BIN}" --r2-replay-binary "${R2_BIN}"
echo 'R1_R2_SOURCE_CORRECTED_SCORES_FROZEN; truth has not been read by this script'

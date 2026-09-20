#!/usr/bin/env bash
set -Eeo pipefail

# Closed-loop TNQC comparison driver.
#
# Default contract:
#   - native PMFS control: tnqc_mode=off
#   - read-only counterfactual: tnqc_mode=shadow
#   - native x TNQC evidence: tnqc_mode=fused
#   - TNQC evidence only: tnqc_mode=only
#
# This script never changes source truth, PMFS cadence, sensor model, planner
# parameters, or timeout between arms.  The shadow arm is a determinism gate:
# it must reproduce the OFF trajectory/result before fused/only are interpreted.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CASE_RUNNER="${CASE_RUNNER:-${ROOT_DIR}/reference/run_meaci_case_20260824.sh}"
PFDI_INSTALL_ROOT="${PFDI_INSTALL_ROOT:-/dev/shm/meaci_online_20260824}"
RUN_ROOT="${RUN_ROOT:-/dev/shm/tnqc_closed_loop_20260920}"
TNQC_MODES="${TNQC_MODES:-off shadow fused only}"
HOUSES="${HOUSES:-House01 House02 House03}"
SEEDS="${SEEDS:-0 1}"
BASE_DOMAIN_ID="${BASE_DOMAIN_ID:-250}"
STEPS_SOURCE_UPDATE="${STEPS_SOURCE_UPDATE:-3}"
TIMEOUT_SEC="${TIMEOUT_SEC:-300.0}"
OUTER_DEADLINE_SEC="${OUTER_DEADLINE_SEC:-900}"

mkdir -p "${RUN_ROOT}"
summary="${RUN_ROOT}/tnqc_matrix.tsv"
printf 'house\tseed\tmode\texit_code\trun_dir\tresult_line\n' > "${summary}"

launch_file="${PFDI_INSTALL_ROOT}/launch/vgr_gsl_pmfs_pfdi.launch.py"
if [[ ! -f "${launch_file}" ]]; then
  echo "missing installed launch file: ${launch_file}" >&2
  exit 3
fi

# Only experimental arms require the new launch argument.  The historical
# baseline remains runnable even with an older installed launch file.
if [[ " ${TNQC_MODES} " != " off " ]]; then
  if ! ros2 launch "${launch_file}" --show-args 2>/dev/null | grep -q 'tnqc_mode'; then
    cat >&2 <<EOF
TNQC launch argument is not exposed by:
  ${launch_file}
Patch/reinstall the launch overlay so it declares and forwards tnqc_mode to the
PMFS node, then rerun this matrix.  The C++ algorithm already accepts
tnqc_mode={off,shadow,fused,only}.
EOF
    exit 4
  fi
fi

idx=0
for house in ${HOUSES}; do
  for seed in ${SEEDS}; do
    for mode in ${TNQC_MODES}; do
      domain=$((BASE_DOMAIN_ID + idx))
      idx=$((idx + 1))
      echo "TNQC_MATRIX_START house=${house} seed=${seed} mode=${mode} domain=${domain}"

      set +e
      HOUSE="${house}" \
      SEED="${seed}" \
      ARM=off \
      PFDI_MODE=off \
      TNQC_MODE="${mode}" \
      RUN_ROOT="${RUN_ROOT}" \
      DOMAIN_ID="${domain}" \
      STEPS_SOURCE_UPDATE="${STEPS_SOURCE_UPDATE}" \
      TIMEOUT_SEC="${TIMEOUT_SEC}" \
      OUTER_DEADLINE_SEC="${OUTER_DEADLINE_SEC}" \
      PFDI_INSTALL_ROOT="${PFDI_INSTALL_ROOT}" \
      bash "${CASE_RUNNER}"
      status=$?
      set -e

      suffix=""
      if [[ "${mode}" != "off" ]]; then
        suffix="_tnqc_${mode}"
      fi
      run_dir="${RUN_ROOT}/${house}_seed${seed}_off_off${suffix}"
      result_line=""
      if [[ -f "${run_dir}/launch.log" ]]; then
        result_line="$(grep -F 'RESULT IS:' "${run_dir}/launch.log" | tail -n 1 | tr '\t' ' ' || true)"
      fi
      printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
        "${house}" "${seed}" "${mode}" "${status}" "${run_dir}" "${result_line}" >> "${summary}"

      echo "TNQC_MATRIX_DONE house=${house} seed=${seed} mode=${mode} status=${status}"
    done
  done
done

echo "TNQC_MATRIX_SUMMARY=${summary}"
cat "${summary}"

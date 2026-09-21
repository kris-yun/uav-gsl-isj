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
# parameters, or timeout between arms.  It is blocked by default until the
# VGR/GADEN fixed-trajectory 300-s offline gate returns GO.  The shadow arm is
# still a determinism gate and must reproduce OFF before fused/only are
# scientifically interpreted.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CASE_RUNNER="${CASE_RUNNER:-${ROOT_DIR}/reference/run_meaci_case_20260824.sh}"
MANIFEST_VERIFY="${MANIFEST_VERIFY:-${ROOT_DIR}/reference/verify_tnqc_v5_manifest.py}"
BUILD_SCRIPT="${BUILD_SCRIPT:-${ROOT_DIR}/reference/build_tnqc_v5_current.sh}"
TNQC_BUILD_ROOT="${TNQC_BUILD_ROOT:-/dev/shm/tnqc_v5_300s_build}"
LAUNCH_FILE="${LAUNCH_FILE:-/dev/shm/meaci_online_20260824/launch/vgr_gsl_pmfs_pfdi.launch.py}"
RUN_ROOT="${RUN_ROOT:-/dev/shm/tnqc_closed_loop_20260920}"
TNQC_MODES="${TNQC_MODES:-off shadow fused only}"
HOUSES="${HOUSES:-House01 House02 House03}"
SEEDS="${SEEDS:-0 1}"
BASE_DOMAIN_ID="${BASE_DOMAIN_ID:-250}"
STEPS_SOURCE_UPDATE="${STEPS_SOURCE_UPDATE:-3}"
TIMEOUT_SEC="${TIMEOUT_SEC:-300.0}"
OUTER_DEADLINE_SEC="${OUTER_DEADLINE_SEC:-900}"
OFFLINE_GO_FILE="${OFFLINE_GO_FILE:-/dev/shm/tnqc_vgr_300s_offline_20260920/tnqc_vgr_300s_offline_gate.json}"
ALLOW_UNCONFIRMED_DIAGNOSTIC="${ALLOW_UNCONFIRMED_DIAGNOSTIC:-0}"

if [[ "${ALLOW_UNCONFIRMED_DIAGNOSTIC}" != "1" ]]; then
  if [[ ! -s "${OFFLINE_GO_FILE}" ]]; then
    echo "TNQC closed loop blocked: missing offline GO file ${OFFLINE_GO_FILE}" >&2
    exit 5
  fi
  python3 - "${OFFLINE_GO_FILE}" <<'PY'
import json, sys
p=json.load(open(sys.argv[1], encoding="utf-8"))
if p.get("contract") != "TNQC_VGR_FIXED_TRAJECTORY_300S_GATE_V6_LINKED_NATIVE_ENDPOINT":
    raise SystemExit(
        "TNQC closed loop blocked: offline gate is not the authoritative "
        "V6 linked-native endpoint contract")
if not p.get("valid", False) or not p.get("go_for_closed_loop", False):
    raise SystemExit("TNQC closed loop blocked: VGR 300-s offline gate is HOLD/INVALID")
PY
fi

mkdir -p "${RUN_ROOT}"
python3 "${MANIFEST_VERIFY}" --root "${ROOT_DIR}" \
  --manifest "evidence/TNQC_V5_IMPLEMENTATION_MANIFEST_20260921.json"
TNQC_BUILD_ROOT="${TNQC_BUILD_ROOT}" bash "${BUILD_SCRIPT}"
PFDI_INSTALL_ROOT="${TNQC_BUILD_ROOT}"
EXPECTED_ALGORITHM_SHA256="$(sha256sum "${PFDI_INSTALL_ROOT}/install/gsl_server/lib/gsl_server/gsl_actionserver_node" | awk '{print $1}')"
LAUNCH_SHA256="$(sha256sum "${LAUNCH_FILE}" | awk '{print $1}')"

summary="${RUN_ROOT}/tnqc_matrix.tsv"
printf 'house\tseed\tmode\texit_code\trun_dir\tresult_line\n' > "${summary}"

launch_file="${LAUNCH_FILE}"
if [[ ! -f "${launch_file}" ]]; then
  echo "missing external launch file: ${launch_file}" >&2
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
      LAUNCH_FILE="${LAUNCH_FILE}" \
      bash "${CASE_RUNNER}"
      status=$?
      set -e

      suffix=""
      if [[ "${mode}" != "off" ]]; then
        suffix="_tnqc_${mode}"
      fi
      run_dir="${RUN_ROOT}/${house}_seed${seed}_off_off${suffix}"
      if [[ -s "${run_dir}/runtime_manifest.json" ]]; then
        python3 - "${run_dir}/runtime_manifest.json" \
          "${EXPECTED_ALGORITHM_SHA256}" "${LAUNCH_SHA256}" <<'PY'
import json, sys
path, want_alg, want_launch = sys.argv[1:]
p = json.load(open(path, encoding="utf-8"))
if p.get("algorithm_sha256") != want_alg:
    raise SystemExit("closed-loop run used unexpected algorithm binary")
if p.get("launch_sha256") != want_launch:
    raise SystemExit("closed-loop run used unexpected launch overlay")
PY
      fi

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

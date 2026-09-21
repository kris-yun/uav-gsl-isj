#!/usr/bin/env bash
set -Eeo pipefail

# Project-level offline gate for TNQC.
#
# Stage 1: run native PMFS only (TNQC_MODE=off) for the full 300-s budget on
# House01/02/03 x seed0/1 and export the context bank.
# Stage 2: replay TNQC on the frozen native candidate bank/trajectory.
# Stage 3: aggregate the six final top-5%-ExpectedValue errors.
#
# No TNQC online feedback occurs in this script.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CASE_RUNNER="${CASE_RUNNER:-${ROOT_DIR}/reference/run_meaci_case_20260824.sh}"
REPLAY="${REPLAY:-${ROOT_DIR}/reference/tnqc_vgr_fixed_trajectory_replay.py}"
AGGREGATE="${AGGREGATE:-${ROOT_DIR}/reference/aggregate_tnqc_vgr_offline_gate.py}"
MANIFEST_VERIFY="${MANIFEST_VERIFY:-${ROOT_DIR}/reference/verify_tnqc_v5_manifest.py}"
ENDPOINT_EVAL_SRC="${ENDPOINT_EVAL_SRC:-${ROOT_DIR}/reference/tnqc_expected_value_eval.cpp}"
PFDI_INSTALL_ROOT="${PFDI_INSTALL_ROOT:-/dev/shm/meaci_online_20260824}"
RUN_ROOT="${RUN_ROOT:-/dev/shm/tnqc_vgr_300s_offline_20260920}"
BASE_DOMAIN_ID="${BASE_DOMAIN_ID:-270}"
STEPS_SOURCE_UPDATE="${STEPS_SOURCE_UPDATE:-3}"
TIMEOUT_SEC="${TIMEOUT_SEC:-300.0}"
OUTER_DEADLINE_SEC="${OUTER_DEADLINE_SEC:-900}"

mkdir -p "${RUN_ROOT}"
python3 "${MANIFEST_VERIFY}" --root "${ROOT_DIR}" \
  --manifest "evidence/TNQC_V5_IMPLEMENTATION_MANIFEST_20260921.json"
ENDPOINT_EVAL_BIN="${RUN_ROOT}/tnqc_expected_value_eval"
echo "TNQC_ENDPOINT_EVAL_BUILD compiler=$(g++ --version | head -n 1) source=${ENDPOINT_EVAL_SRC}"
g++ -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror \
  "${ENDPOINT_EVAL_SRC}" -o "${ENDPOINT_EVAL_BIN}"

truth_for_house() {
  case "$1" in
    House01) echo "-0.40 -2.90" ;;
    House02) echo "0.00 -1.00" ;;
    House03) echo "-0.45 1.90" ;;
    *) echo "unsupported house $1" >&2; return 2 ;;
  esac
}

idx=0
for house in House01 House02 House03; do
  read -r truth_x truth_y <<<"$(truth_for_house "${house}")"
  for seed in 0 1; do
    domain=$((BASE_DOMAIN_ID + idx))
    idx=$((idx + 1))
    run_dir="${RUN_ROOT}/${house}_seed${seed}_off_off"

    # Prevent stale artifacts from contaminating the fixed-trajectory gate.
    rm -rf "${run_dir}"

    echo "TNQC_VGR_OFFLINE_NATIVE_START house=${house} seed=${seed} domain=${domain}"
    HOUSE="${house}" \
    SEED="${seed}" \
    ARM=off \
    PFDI_MODE=off \
    TNQC_MODE=off \
    RUN_CONTRACT=TNQC_VGR_FIXED_TRAJECTORY_EXPORT_V1 \
    RUN_ROOT="${RUN_ROOT}" \
    DOMAIN_ID="${domain}" \
    STEPS_SOURCE_UPDATE="${STEPS_SOURCE_UPDATE}" \
    TIMEOUT_SEC="${TIMEOUT_SEC}" \
    OUTER_DEADLINE_SEC="${OUTER_DEADLINE_SEC}" \
    TARGET_SOURCE_UPDATES=0 \
    TARGET_ACCEPTED_UPDATES=0 \
    PFDI_INSTALL_ROOT="${PFDI_INSTALL_ROOT}" \
    bash "${CASE_RUNNER}"

    if [[ ! -s "${run_dir}/context_bank/source_update_timing.csv" ]]; then
      echo "missing context bank for ${house} seed ${seed}: ${run_dir}" >&2
      exit 20
    fi

    # Full-budget audit.  The scientific endpoint is 300 simulation seconds,
    # not the first accepted source update.  Require the PMFS terminal result
    # to be emitted near the configured 300-s budget before replaying it.
    result_line="$(grep -F 'RESULT IS:' "${run_dir}/launch.log" | tail -n 1 || true)"
    if [[ -z "${result_line}" ]]; then
      echo "missing final PMFS RESULT IS line for ${house} seed ${seed}" >&2
      exit 21
    fi
    search_t="$(printf '%s\n' "${result_line}" | sed -n 's/.*Search_t=\([0-9.]*\).*/\1/p')"
    python3 - "${search_t}" <<'PY'
import sys
t = float(sys.argv[1])
if not (295.0 <= t <= 330.0):
    raise SystemExit(f"full-budget audit failed: Search_t={t}, expected about 300 s")
PY

    echo "TNQC_VGR_OFFLINE_REPLAY_START house=${house} seed=${seed}"
    # Exit code 3 is a scientific integrity INVALID (the replay writes its
    # JSON first). Keep running the remaining frozen cases so the aggregate
    # report contains the complete six-case diagnosis. Any other replay
    # error is an execution failure and still aborts immediately.
    if python3 "${REPLAY}" \
      --run-dir "${run_dir}" \
      --truth-x "${truth_x}" \
      --truth-y "${truth_y}" \
      --budget-s 300 \
      --source-discrimination-power 1.0 \
      --cpp-endpoint-evaluator "${ENDPOINT_EVAL_BIN}"; then
      echo "TNQC_VGR_OFFLINE_REPLAY_DONE house=${house} seed=${seed} integrity=PASS"
    else
      replay_rc=$?
      if [[ "${replay_rc}" -ne 3 ]]; then
        echo "TNQC replay execution failure house=${house} seed=${seed} rc=${replay_rc}" >&2
        exit "${replay_rc}"
      fi
      echo "TNQC_VGR_OFFLINE_REPLAY_DONE house=${house} seed=${seed} integrity=INVALID"
    fi
  done
done

python3 "${AGGREGATE}" --run-root "${RUN_ROOT}"
echo "TNQC_VGR_300S_GATE_RESULT=${RUN_ROOT}/tnqc_vgr_300s_offline_gate.json"

# Exit nonzero when the frozen GO criterion is not met so an automated caller
# cannot accidentally continue into the closed-loop matrix.
python3 - "${RUN_ROOT}/tnqc_vgr_300s_offline_gate.json" <<'PY'
import json, sys
p = json.load(open(sys.argv[1], encoding="utf-8"))
if not p.get("go_for_closed_loop", False):
    print("TNQC_VGR_300S_OFFLINE_HOLD")
    raise SystemExit(10)
print("TNQC_VGR_300S_OFFLINE_GO")
PY

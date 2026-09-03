#!/usr/bin/env bash
set -Eeo pipefail

REPO_ROOT="${REPO_ROOT:-/home/zyc/gsl_ws/src/GasSourceLocalization}"
RUN_ROOT="${RUN_ROOT:?set a fresh RUN_ROOT}"
PFDI_INSTALL_ROOT="${PFDI_INSTALL_ROOT:?set PFDI_INSTALL_ROOT}"
STEPS_SOURCE_UPDATE="${STEPS_SOURCE_UPDATE:-3}"
MAX_WARMUP_ITERATIONS="${MAX_WARMUP_ITERATIONS:-3}"
MIN_WARMUP_ITERATIONS="${MIN_WARMUP_ITERATIONS:-1}"
INTEGRITY_REPORT="${INTEGRITY_REPORT:?set H01 bank integrity report}"
DOMAIN_ID="${DOMAIN_ID:-230}"
TIMEOUT_SEC="240.0"
[[ "${STEPS_SOURCE_UPDATE}" == 3 && "${MAX_WARMUP_ITERATIONS}" == 3 && "${MIN_WARMUP_ITERATIONS}" == 1 ]] || {
  echo "CTPI_FASTTRACK_CADENCE_MUST_BE_3_3_1" >&2; exit 2;
}

[[ ! -e "${RUN_ROOT}" ]] || { echo "CTPI_SMOKE_REFUSE_EXISTING_RUN_ROOT=${RUN_ROOT}" >&2; exit 70; }
mkdir -p "${RUN_ROOT}"
for ARM in F00 F10 F11; do
  HOUSE=H01 SEED=0 ARM="${ARM}" RUN_ROOT="${RUN_ROOT}" REPO_ROOT="${REPO_ROOT}" \
    PFDI_INSTALL_ROOT="${PFDI_INSTALL_ROOT}" STEPS_SOURCE_UPDATE="${STEPS_SOURCE_UPDATE}" \
    MAX_WARMUP_ITERATIONS="${MAX_WARMUP_ITERATIONS}" MIN_WARMUP_ITERATIONS="${MIN_WARMUP_ITERATIONS}" \
    INTEGRITY_REPORT="${INTEGRITY_REPORT}" DOMAIN_ID="${DOMAIN_ID}" TIMEOUT_SEC="${TIMEOUT_SEC}" \
    bash "${REPO_ROOT}/closed_loop/ctpi/run_ctpi_fasttrack_case_safe_20260903.sh"
  if [[ "${ARM}" == F10 || "${ARM}" == F11 ]]; then
    python3 "${REPO_ROOT}/tools/ctpi_m3_action_sanity.py" \
      --audit "${RUN_ROOT}/H01_seed0_${ARM}/ctpi_audit/ctpi_m3_action_audit.csv" \
      --output "${RUN_ROOT}/H01_seed0_${ARM}/ctpi_m3_action_sanity.json"
  fi
done
python3 "${REPO_ROOT}/tools/ctpi_true_closed_loop_check.py" --run-root "${RUN_ROOT}" --house H01 --seed 0 --output "${RUN_ROOT}/TRUE_CLOSED_LOOP_CAUSAL_CHAIN.json"
echo "CTPI_H01_SEED0_SMOKE=PASS"

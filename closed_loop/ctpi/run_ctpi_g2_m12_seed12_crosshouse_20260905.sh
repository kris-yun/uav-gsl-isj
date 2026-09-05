#!/usr/bin/env bash
set -Eeo pipefail

REPO_ROOT="${REPO_ROOT:-/home/zyc/gsl_ws/src/GasSourceLocalization}"
RUN_ROOT="${RUN_ROOT:?set a fresh RUN_ROOT}"
PFDI_INSTALL_ROOT="${PFDI_INSTALL_ROOT:?set PFDI_INSTALL_ROOT}"
VGR_BRIDGE_SOURCE_ROOT="${VGR_BRIDGE_SOURCE_ROOT:?set an audited vgr_bridge source overlay}"
INTEGRITY_H01="${INTEGRITY_H01:?set H01 integrity report}"
INTEGRITY_H02="${INTEGRITY_H02:?set H02 integrity report}"
INTEGRITY_H03="${INTEGRITY_H03:?set H03 integrity report}"
DOMAIN_ID="${DOMAIN_ID:-230}"
SEED="${SEED:-12}"

[[ "${SEED}" == 12 ]] || { echo "CTPI_G2_M12_SEED_MUST_BE_12" >&2; exit 2; }
[[ ! -e "${RUN_ROOT}" ]] || { echo "CTPI_G2_M12_REFUSE_EXISTING_RUN_ROOT=${RUN_ROOT}" >&2; exit 70; }
mkdir -p "${RUN_ROOT}"

for HOUSE in H01 H02 H03; do
  case "${HOUSE}" in
    H01) INTEGRITY_REPORT="${INTEGRITY_H01}" ;;
    H02) INTEGRITY_REPORT="${INTEGRITY_H02}" ;;
    H03) INTEGRITY_REPORT="${INTEGRITY_H03}" ;;
  esac
  for ARM in A0 F00 F01; do
    HOUSE="${HOUSE}" SEED="${SEED}" ARM="${ARM}" RUN_ROOT="${RUN_ROOT}" \
      REPO_ROOT="${REPO_ROOT}" PFDI_INSTALL_ROOT="${PFDI_INSTALL_ROOT}" \
      VGR_BRIDGE_SOURCE_ROOT="${VGR_BRIDGE_SOURCE_ROOT}" \
      STEPS_SOURCE_UPDATE=3 MAX_WARMUP_ITERATIONS=3 MIN_WARMUP_ITERATIONS=1 \
      INTEGRITY_REPORT="${INTEGRITY_REPORT}" DOMAIN_ID="${DOMAIN_ID}" \
      TIMEOUT_SEC=240.0 METHOD=CTPI_G2_M1_M2 METHOD_FAMILY=ctpi_two_module \
      bash "${REPO_ROOT}/closed_loop/ctpi/run_ctpi_fasttrack_case_safe_20260903.sh"
    python3 "${REPO_ROOT}/tools/ctpi_fasttrack_terminal_guard.py" \
      --run-dir "${RUN_ROOT}/${HOUSE}_seed${SEED}_${ARM}" --arm "${ARM}" \
      --output "${RUN_ROOT}/${HOUSE}_seed${SEED}_${ARM}/CTPI_FASTTRACK_CASE_TERMINAL.json"
  done
  python3 "${REPO_ROOT}/tools/ctpi_g2_m12_seed12_causal_check.py" \
    --run-root "${RUN_ROOT}" --house "${HOUSE}" --seed "${SEED}" \
    --output "${RUN_ROOT}/${HOUSE}_seed${SEED}_CTPI_G2_M12_CAUSAL_CHAIN.json"
done

python3 "${REPO_ROOT}/tools/ctpi_g2_m12_seed12_performance.py" \
  --run-root "${RUN_ROOT}" --seed "${SEED}" \
  --output "${RUN_ROOT}/CTPI_G2_M12_SEED12_PERFORMANCE.json"

echo "CTPI_G2_M12_SEED12_CROSSHOUSE=COMPLETE"

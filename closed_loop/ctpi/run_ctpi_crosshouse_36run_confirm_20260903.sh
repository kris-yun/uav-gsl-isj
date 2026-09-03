#!/usr/bin/env bash
set -Eeo pipefail
REPO_ROOT="${REPO_ROOT:-/home/zyc/gsl_ws/src/GasSourceLocalization}"
RUN_ROOT="${RUN_ROOT:?set a fresh confirmation RUN_ROOT}"
PFDI_INSTALL_ROOT="${PFDI_INSTALL_ROOT:?set PFDI_INSTALL_ROOT}"
STEPS_SOURCE_UPDATE="${STEPS_SOURCE_UPDATE:-3}"
MAX_WARMUP_ITERATIONS="${MAX_WARMUP_ITERATIONS:-3}"
MIN_WARMUP_ITERATIONS="${MIN_WARMUP_ITERATIONS:-1}"
H01_SCREEN_GATE="${H01_SCREEN_GATE:?point to the PASS H01 seeds0-2 screening Gate}"
INTEGRITY_H01="${INTEGRITY_H01:?set H01 integrity report}"
INTEGRITY_H02="${INTEGRITY_H02:?set H02 integrity report}"
INTEGRITY_H03="${INTEGRITY_H03:?set H03 integrity report}"
DOMAIN_ID="${DOMAIN_ID:-230}"
[[ "${STEPS_SOURCE_UPDATE}" == 3 && "${MAX_WARMUP_ITERATIONS}" == 3 && "${MIN_WARMUP_ITERATIONS}" == 1 ]] || { echo "CTPI_FASTTRACK_CADENCE_MUST_BE_3_3_1" >&2; exit 2; }
python3 - "${H01_SCREEN_GATE}" <<'PY'
import json,sys
p=json.load(open(sys.argv[1],encoding='utf-8'))
assert p.get('verdict')=='CTPI_FASTTRACK_H01_3SEED_SCREEN=PASS' and p.get('formal_crosshouse_authorized') is True
print('CTPI_CROSSHOUSE_SCREEN_AUTHORIZATION=PASS')
PY
[[ ! -e "${RUN_ROOT}" ]] || { echo "CTPI_CONFIRM_REFUSE_EXISTING_RUN_ROOT=${RUN_ROOT}" >&2; exit 70; }
mkdir -p "${RUN_ROOT}"
for HOUSE in H01 H02 H03; do
  case "$HOUSE" in H01) IR="$INTEGRITY_H01";; H02) IR="$INTEGRITY_H02";; H03) IR="$INTEGRITY_H03";; esac
  for SEED in 3 4 5; do
    for ARM in A0 F00 F10 F11; do
      HOUSE="$HOUSE" SEED="$SEED" ARM="$ARM" RUN_ROOT="$RUN_ROOT" REPO_ROOT="$REPO_ROOT" \
        PFDI_INSTALL_ROOT="$PFDI_INSTALL_ROOT" STEPS_SOURCE_UPDATE="$STEPS_SOURCE_UPDATE" \
        MAX_WARMUP_ITERATIONS="$MAX_WARMUP_ITERATIONS" MIN_WARMUP_ITERATIONS="$MIN_WARMUP_ITERATIONS" \
        INTEGRITY_REPORT="$IR" DOMAIN_ID="$DOMAIN_ID" TIMEOUT_SEC=240.0 \
        bash "$REPO_ROOT/closed_loop/ctpi/run_ctpi_fasttrack_case_safe_20260903.sh"
      if [[ "$ARM" == F10 || "$ARM" == F11 ]]; then
        python3 "$REPO_ROOT/tools/ctpi_m3_action_sanity.py" --audit "$RUN_ROOT/${HOUSE}_seed${SEED}_${ARM}/ctpi_audit/ctpi_m3_action_audit.csv" --output "$RUN_ROOT/${HOUSE}_seed${SEED}_${ARM}/ctpi_m3_action_sanity.json"
      fi
    done
    python3 "$REPO_ROOT/tools/ctpi_true_closed_loop_check.py" --run-root "$RUN_ROOT" --house "$HOUSE" --seed "$SEED" --output "$RUN_ROOT/${HOUSE}_seed${SEED}_TRUE_CLOSED_LOOP_CAUSAL_CHAIN.json"
  done
done
python3 "$REPO_ROOT/tools/ctpi_crosshouse_performance.py" --run-root "$RUN_ROOT" --seeds 3,4,5 --output "$RUN_ROOT/CTPI_CROSSHOUSE_36RUN_CONFIRM.json"
echo "CTPI_CROSSHOUSE_36RUN_BATCH=COMPLETE"

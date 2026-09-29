#!/usr/bin/env bash
set -Eeuo pipefail

HOUSE="${HOUSE:?set HOUSE=House01, House02, or House03}"
case "$HOUSE" in
  House01) DOMAIN_ID=221 ;;
  House02) DOMAIN_ID=222 ;;
  House03) DOMAIN_ID=223 ;;
  *) echo "unsupported HOUSE=$HOUSE" >&2; exit 2 ;;
esac

freeze=/home/zyc/meaci_v12_m_freeze_20260825
binary="$freeze/install/gsl_server/lib/gsl_server/gsl_actionserver_node"
runner="$freeze/run_meaci_case_20260824.sh"
expected_binary=100ca267c1dc6f098f1080f669733bf7cf655d8a05ce8d5afe3ef9b9458a51ce
expected_runner=78404eff2fe205d01d62b0f4273f3b3568c73a7313c12aa47c6827d88b803484
bank_root=/home/zyc/meaci_v12_banks_20260825
bank="$bank_root/$HOUSE/v12_response_bank.bin"
run_root=/home/zyc/meaci_v12_bank_build_logs_20260825_retry3
run_dir="$run_root/${HOUSE}_seed0_on_rc_sd_tfei_v12"

[[ "$(sha256sum "$binary" | awk '{print $1}')" == "$expected_binary" ]]
[[ "$(sha256sum "$runner" | awk '{print $1}')" == "$expected_runner" ]]
[[ ! -e "$bank" ]]
[[ ! -e "$bank.tmp" ]]
[[ ! -e "$run_dir" ]]
mkdir -p "$bank_root/$HOUSE" "$run_root"

export HOUSE SEED=0 ARM=on RUN_ROOT="$run_root"
export PFDI_MODE=rc_sd_tfei_v12
export RUN_ID="V12_RESPONSE_BANK_${HOUSE}_METHODSEED20260818"
export DOMAIN_ID PFDI_INSTALL_ROOT="$freeze"
export RUN_CONTRACT=V12_M_RESPONSE_BANK_BUILD_V1
export TIMEOUT_SEC=600 OUTER_DEADLINE_SEC=800
export TARGET_SOURCE_UPDATES=0 TARGET_ACCEPTED_UPDATES=0
export STEPS_SOURCE_UPDATE=3 TADM_REPLICAS=8
export POSTERIOR_GUIDANCE_WEIGHT=0 REALTIME_FACTOR=1.0
export EVALUATOR_SCRIPT=/nonexistent/v12_defer_truth_evaluation.py
export PFDI_V12_RESPONSE_BANK_PATH="$bank"
export PFDI_V12_BUILD_RESPONSE_BANK=1

"$runner" >"$run_root/${HOUSE}_builder_wrapper.log" 2>&1 &
runner_pid=$!
deadline=$((SECONDS + 650))
while kill -0 "$runner_pid" 2>/dev/null; do
  summary="$run_dir/tadm/v12_update_summary.csv"
  if [[ -s "$bank" && -s "$summary" ]] &&
     awk -F, 'NR > 1 && $NF == "PASS" {ok=1} END {exit(ok ? 0 : 1)}' "$summary"; then
    cat >"$run_dir/run_status.json" <<EOF
{
  "status": "response_bank_built",
  "run_id": "$RUN_ID",
  "house": "$HOUSE",
  "method_seed": 20260818,
  "source_truth_used_by_bank": false
}
EOF
    break
  fi
  if (( SECONDS >= deadline )); then
    echo "V12_RESPONSE_BANK_BUILD_TIMEOUT HOUSE=$HOUSE" >&2
    kill -TERM "$runner_pid" 2>/dev/null || true
    wait "$runner_pid" || true
    exit 70
  fi
  sleep 2
done
wait "$runner_pid"
unset PFDI_V12_BUILD_RESPONSE_BANK
test -s "$bank"
test -s "$run_dir/tadm/v12_update_summary.csv"
sha256sum "$bank"

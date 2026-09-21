#!/usr/bin/env bash
set -Eeo pipefail

# GCSI V1 consumes the already-frozen native PMFS six-case context banks.
# It does not re-run ROS and does not modify any trajectory or source update.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NATIVE_RUN_ROOT="${NATIVE_RUN_ROOT:-/dev/shm/tnqc_vgr_300s_offline_20260920}"
REPLAY="${REPLAY:-${ROOT_DIR}/reference/gcsi_vgr_fixed_trajectory_replay.py}"
AGGREGATE="${AGGREGATE:-${ROOT_DIR}/reference/aggregate_gcsi_vgr_offline_gate.py}"
ENDPOINT_EVAL_BIN="${ENDPOINT_EVAL_BIN:-/dev/shm/tnqc_v5_300s_build/install/gsl_server/lib/gsl_server/tnqc_expected_value_native}"
BLOCK_SIZE_M="${BLOCK_SIZE_M:-0.9}"

[[ -x "${ENDPOINT_EVAL_BIN}" ]] || {
  echo "missing linked native endpoint evaluator: ${ENDPOINT_EVAL_BIN}" >&2
  exit 69
}

truth_for_house() {
  case "$1" in
    House01) echo "-0.40 -2.90" ;;
    House02) echo "0.00 -1.00" ;;
    House03) echo "-0.45 1.90" ;;
    *) echo "unsupported house $1" >&2; return 2 ;;
  esac
}

for house in House01 House02 House03; do
  read -r truth_x truth_y <<<"$(truth_for_house "${house}")"
  for seed in 0 1; do
    run_dir="${NATIVE_RUN_ROOT}/${house}_seed${seed}_off_off"
    [[ -s "${run_dir}/context_bank/source_update_timing.csv" ]] || {
      echo "missing frozen native context bank: ${run_dir}" >&2
      exit 20
    }
    [[ -s "${run_dir}/launch.log" ]] || {
      echo "missing frozen native launch.log: ${run_dir}" >&2
      exit 21
    }

    echo "GCSI_REPLAY_START house=${house} seed=${seed}"
    python3 "${REPLAY}"       --run-dir "${run_dir}"       --truth-x "${truth_x}"       --truth-y "${truth_y}"       --budget-s 300       --source-discrimination-power 1.0       --block-size-m "${BLOCK_SIZE_M}"       --cpp-endpoint-evaluator "${ENDPOINT_EVAL_BIN}"       --json-out "${run_dir}/gcsi_v1_replay.json"
    echo "GCSI_REPLAY_DONE house=${house} seed=${seed}"
  done
done

python3 "${AGGREGATE}" --run-root "${NATIVE_RUN_ROOT}"
echo "GCSI_V1_300S_GATE=${NATIVE_RUN_ROOT}/gcsi_v1_300s_gate.json"

python3 - "${NATIVE_RUN_ROOT}/gcsi_v1_300s_gate.json" <<'PY'
import json, sys
p = json.load(open(sys.argv[1], encoding="utf-8"))
if not p.get("go_for_next_stage", False):
    print("GCSI_V1_300S_HOLD")
    raise SystemExit(10)
print("GCSI_V1_300S_STAGE2_GO")
PY

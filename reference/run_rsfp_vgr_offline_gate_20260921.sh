#!/usr/bin/env bash
set -Eeo pipefail

# Replay-only RSFP 300-s gate on the already-frozen six native R2 runs.
#
# Required environment:
#   RUN_ROOT          directory containing House01_seed0_off_off ... House03_seed1_off_off
#   ENDPOINT_EVAL_BIN linked-native tnqc_expected_value_native binary
#
# This script MUST NOT regenerate or modify the native trajectories.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPLAY="${ROOT_DIR}/reference/rsfp_vgr_fixed_trajectory_replay.py"
AGGREGATE="${ROOT_DIR}/reference/aggregate_rsfp_vgr_offline_gate.py"
TEST="${ROOT_DIR}/reference/test_rsfp_multiscale_score.py"

: "${RUN_ROOT:?set RUN_ROOT to the extracted frozen R2 six-case run root}"
: "${ENDPOINT_EVAL_BIN:?set ENDPOINT_EVAL_BIN to tnqc_expected_value_native}"

[[ -x "${ENDPOINT_EVAL_BIN}" ]] || {
  echo "missing/non-executable linked-native endpoint evaluator: ${ENDPOINT_EVAL_BIN}" >&2
  exit 69
}

python3 -m py_compile "${REPLAY}" "${AGGREGATE}" "${TEST}"
python3 "${TEST}"

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
    run_dir="${RUN_ROOT}/${house}_seed${seed}_off_off"
    [[ -s "${run_dir}/context_bank/source_update_timing.csv" ]] || {
      echo "missing frozen context bank: ${run_dir}" >&2
      exit 20
    }
    [[ -s "${run_dir}/launch.log" ]] || {
      echo "missing frozen launch log: ${run_dir}" >&2
      exit 21
    }

    # Remove only RSFP counterfactual outputs from an earlier attempt.
    rm -rf "${run_dir}/rsfp_endpoint_posteriors"
    rm -f "${run_dir}/rsfp_fixed_trajectory_evaluation.json"

    echo "RSFP_REPLAY_START house=${house} seed=${seed}"
    if python3 "${REPLAY}"       --run-dir "${run_dir}"       --truth-x "${truth_x}"       --truth-y "${truth_y}"       --budget-s 300       --source-discrimination-power 1.0       --factors 1,2,4,8       --cpp-endpoint-evaluator "${ENDPOINT_EVAL_BIN}"; then
      echo "RSFP_REPLAY_DONE house=${house} seed=${seed} integrity=PASS"
    else
      rc=$?
      if [[ "${rc}" -ne 3 ]]; then
        echo "RSFP replay execution failure house=${house} seed=${seed} rc=${rc}" >&2
        exit "${rc}"
      fi
      echo "RSFP_REPLAY_DONE house=${house} seed=${seed} integrity=INVALID"
    fi
  done
done

python3 "${AGGREGATE}" --run-root "${RUN_ROOT}"
echo "RSFP_VGR_300S_GATE_RESULT=${RUN_ROOT}/rsfp_vgr_300s_offline_gate.json"

python3 - "${RUN_ROOT}/rsfp_vgr_300s_offline_gate.json" <<'PY'
import json, sys
p = json.load(open(sys.argv[1], encoding="utf-8"))
print(p["verdict"])
if not p.get("go_for_closed_loop", False):
    raise SystemExit(10)
PY

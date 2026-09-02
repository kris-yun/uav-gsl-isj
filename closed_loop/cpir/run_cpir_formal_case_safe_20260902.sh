#!/usr/bin/env bash
set -Eeo pipefail

# Safety wrapper for the canonical formal CPIR runner.
# It does not change any scientific formula, parameter, bank, ROS topic, or launch contract.
# It only prevents two orchestration false-positive modes:
#   1) reusing a stale RUN_DIR/run_status.json from an earlier execution;
#   2) treating a child exit code 0 as success when no fresh run_status.json exists.

HOUSE="${HOUSE:?set HOUSE=H01,H02,H03 (or House01,House02,House03)}"
SEED="${SEED:?set SEED explicitly}"
ARM="${ARM:?set ARM=A0,F00,F01,F10,F11}"
RUN_ROOT="${RUN_ROOT:?set RUN_ROOT}"
REPO_ROOT="${REPO_ROOT:-/home/zyc/gsl_ws/src/GasSourceLocalization}"
CANONICAL_RUNNER="${CANONICAL_RUNNER:-${REPO_ROOT}/closed_loop/cpir/run_cpir_formal_case_20260901.sh}"

case "${HOUSE}" in
  H01|House01) HSHORT="H01" ;;
  H02|House02) HSHORT="H02" ;;
  H03|House03) HSHORT="H03" ;;
  *) echo "CPIR_SAFE_UNSUPPORTED_HOUSE=${HOUSE}" >&2; exit 2 ;;
esac

case "${ARM}" in
  A0|F00|F01|F10|F11) ;;
  *) echo "CPIR_SAFE_UNSUPPORTED_ARM=${ARM}" >&2; exit 2 ;;
esac

[[ -x "${CANONICAL_RUNNER}" ]] || {
  echo "CPIR_SAFE_CANONICAL_RUNNER_NOT_EXECUTABLE=${CANONICAL_RUNNER}" >&2
  exit 3
}

RUN_DIR="${RUN_ROOT}/${HSHORT}_seed${SEED}_${ARM}"

# Formal runs must start from a fresh result directory. Otherwise an old
# run_status.json can cause the canonical runner to stop the new launch early.
if [[ -e "${RUN_DIR}" ]]; then
  echo "CPIR_SAFE_RUN_DIR_ALREADY_EXISTS=${RUN_DIR}" >&2
  echo "CPIR_SAFE_ACTION=choose_a_fresh_RUN_ROOT_or_archive_the_old_run" >&2
  exit 70
fi

mkdir -p "${RUN_ROOT}"
START_EPOCH_NS="$(date +%s%N)"

set +e
"${CANONICAL_RUNNER}"
child_status=$?
set -e

STATUS_FILE="${RUN_DIR}/run_status.json"
if [[ ! -s "${STATUS_FILE}" ]]; then
  echo "CPIR_SAFE_MISSING_TERMINAL_STATUS=${STATUS_FILE}" >&2
  echo "CPIR_SAFE_CHILD_STATUS=${child_status}" >&2
  exit 71
fi

python3 - "${STATUS_FILE}" "${START_EPOCH_NS}" "${HSHORT}" "${SEED}" "${ARM}" <<'PY'
import json
import os
import sys

path, start_ns, house, seed, arm = sys.argv[1:]
start_ns = int(start_ns)
try:
    st = os.stat(path)
except OSError as exc:
    raise SystemExit(f"CPIR_SAFE_STATUS_STAT_FAILED:{exc}")

mtime_ns = st.st_mtime_ns
if mtime_ns < start_ns:
    raise SystemExit(
        f"CPIR_SAFE_STALE_TERMINAL_STATUS:mtime_ns={mtime_ns}:start_ns={start_ns}"
    )

try:
    payload = json.load(open(path, encoding="utf-8"))
except Exception as exc:
    raise SystemExit(f"CPIR_SAFE_STATUS_JSON_INVALID:{exc}")

if not isinstance(payload, dict):
    raise SystemExit("CPIR_SAFE_STATUS_JSON_NOT_OBJECT")

# Do not invent a schema field that older benchmark runners may not have.
# When identity fields are present, however, they must agree with this run.
checks = {
    "house": house,
    "seed": int(seed),
    "arm": arm,
    "ablation_id": arm,
}
for key, expected in checks.items():
    if key in payload and payload[key] != expected:
        raise SystemExit(
            f"CPIR_SAFE_STATUS_IDENTITY_MISMATCH:{key}:{payload[key]}:{expected}"
        )

print(f"CPIR_SAFE_TERMINAL_STATUS_FRESH={path}")
PY

# A nonzero canonical-runner status is still a failure even if a diagnostic
# run_status.json was produced. This keeps shell-level failure semantics strict.
if (( child_status != 0 )); then
  echo "CPIR_SAFE_CHILD_NONZERO_WITH_STATUS=${child_status}" >&2
  exit "${child_status}"
fi

echo "CPIR_SAFE_CASE_COMPLETE HOUSE=${HSHORT} SEED=${SEED} ARM=${ARM} RUN_DIR=${RUN_DIR}"

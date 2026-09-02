#!/usr/bin/env bash
set -Eeo pipefail

# Safety wrapper for the *future/actual* CTPI V0.4 canonical closed-loop runner.
# It intentionally does not implement or substitute any scientific formula.
# The inherited CPIR runner is forbidden as a canonical CTPI V0.4 runner.

HOUSE="${HOUSE:?set HOUSE=H01,H02,H03 (or House01,House02,House03)}"
SEED="${SEED:?set SEED explicitly}"
ARM="${ARM:?set ARM explicitly for the CTPI V0.4 runtime contract}"
RUN_ROOT="${RUN_ROOT:?set a fresh RUN_ROOT}"
REPO_ROOT="${REPO_ROOT:-/home/zyc/gsl_ws/src/GasSourceLocalization}"
PFDI_INSTALL_ROOT="${PFDI_INSTALL_ROOT:?set PFDI_INSTALL_ROOT to the build of the exact CTPI V0.4 commit}"
CANONICAL_RUNNER="${CTPI_V04_CANONICAL_RUNNER:?set CTPI_V04_CANONICAL_RUNNER to the actual CTPI V0.4 runner}"
DOMAIN_ID="${DOMAIN_ID:-230}"

case "${HOUSE}" in
  H01|House01) HSHORT="H01" ;;
  H02|House02) HSHORT="H02" ;;
  H03|House03) HSHORT="H03" ;;
  *) echo "CTPI_V04_SAFE_UNSUPPORTED_HOUSE=${HOUSE}" >&2; exit 2 ;;
esac

# Old CPIR factorial identifiers are deliberately rejected.  CTPI V0.4 has a
# different module graph and must not inherit F00/F01/F10/F11 -> cpir_* mapping.
case "${ARM}" in
  F00|F01|F10|F11|cpir_*|CPIR_*)
    echo "CTPI_V04_SAFE_FORBIDS_CPIR_ARM=${ARM}" >&2
    exit 64
    ;;
esac

if ! [[ "${DOMAIN_ID}" =~ ^[0-9]+$ ]] || (( DOMAIN_ID < 0 || DOMAIN_ID > 232 )); then
  echo "CTPI_V04_SAFE_INVALID_ROS_DOMAIN_ID=${DOMAIN_ID}; expected 0..232" >&2
  exit 65
fi

[[ -d "${REPO_ROOT}" ]] || { echo "CTPI_V04_SAFE_REPO_ROOT_MISSING=${REPO_ROOT}" >&2; exit 3; }
[[ -f "${REPO_ROOT}/tools/ctpi_v04_runtime_parity_guard.py" ]] || {
  echo "CTPI_V04_SAFE_PARITY_GUARD_MISSING" >&2; exit 3;
}
[[ -f "${CANONICAL_RUNNER}" ]] || { echo "CTPI_V04_SAFE_CANONICAL_RUNNER_MISSING=${CANONICAL_RUNNER}" >&2; exit 3; }

# Do not allow the inherited CPIR runner to masquerade as CTPI V0.4.
runner_real="$(readlink -f "${CANONICAL_RUNNER}")"
case "${runner_real}" in
  *closed_loop/cpir/*|*run_cpir_*)
    echo "CTPI_V04_SAFE_CANONICAL_RUNNER_IS_CPIR=${runner_real}" >&2
    exit 66
    ;;
esac

ALGORITHM_BINARY="${PFDI_INSTALL_ROOT}/install/gsl_server/lib/gsl_server/gsl_actionserver_node"
[[ -f "${ALGORITHM_BINARY}" ]] || { echo "CTPI_V04_SAFE_ALGORITHM_BINARY_MISSING=${ALGORITHM_BINARY}" >&2; exit 3; }

mkdir -p "${RUN_ROOT}"
RUN_DIR="${RUN_ROOT}/${HSHORT}_seed${SEED}_${ARM}"
if [[ -e "${RUN_DIR}" ]]; then
  echo "CTPI_V04_SAFE_RUN_DIR_ALREADY_EXISTS=${RUN_DIR}" >&2
  echo "Use a new RUN_ROOT or archive/remove the old run explicitly." >&2
  exit 70
fi

mkdir -p "${RUN_DIR}"
PARITY_JSON="${RUN_DIR}/ctpi_v04_runtime_parity.json"
python3 "${REPO_ROOT}/tools/ctpi_v04_runtime_parity_guard.py" \
  --repo-root "${REPO_ROOT}" \
  --binary "${ALGORITHM_BINARY}" \
  --json-out "${PARITY_JSON}"

# Guard exits 42 while the real CREL/APRS C++ runtime is absent.  Do not
# override that exit code and do not map CTPI to a CPIR mode to make it pass.

START_NS="$(date +%s%N)"
SOURCE_HEAD="$(git -C "${REPO_ROOT}" rev-parse HEAD 2>/dev/null || echo UNKNOWN)"
BINARY_SHA256="$(sha256sum "${ALGORITHM_BINARY}" | awk '{print $1}')"
cat >"${RUN_DIR}/ctpi_v04_safe_wrapper_manifest.json" <<EOF
{
  "contract": "CTPI_V04_SAFE_WRAPPER_V1",
  "house": "${HSHORT}",
  "seed": ${SEED},
  "arm": "${ARM}",
  "source_git_commit": "${SOURCE_HEAD}",
  "algorithm_sha256": "${BINARY_SHA256}",
  "ros_domain_id": ${DOMAIN_ID},
  "canonical_runner": "${runner_real}",
  "start_ns": ${START_NS}
}
EOF

export ROS_DOMAIN_ID="${DOMAIN_ID}"
export RMW_IMPLEMENTATION="${RMW_IMPLEMENTATION:-rmw_fastrtps_cpp}"

# Preserve caller inputs but force the same fresh run directory/root identity.
set +e
HOUSE="${HOUSE}" SEED="${SEED}" ARM="${ARM}" RUN_ROOT="${RUN_ROOT}" \
  REPO_ROOT="${REPO_ROOT}" PFDI_INSTALL_ROOT="${PFDI_INSTALL_ROOT}" \
  DOMAIN_ID="${DOMAIN_ID}" bash "${CANONICAL_RUNNER}"
child_status=$?
set -e

STATUS_JSON="${RUN_DIR}/run_status.json"
if [[ ! -s "${STATUS_JSON}" ]]; then
  echo "CTPI_V04_SAFE_FRESH_RUN_STATUS_MISSING=${STATUS_JSON}" >&2
  exit 71
fi

python3 - "${STATUS_JSON}" "${START_NS}" "${HSHORT}" "${SEED}" "${ARM}" <<'PY'
import json, os, sys
p, start_ns, house, seed, arm = sys.argv[1:]
start_ns = int(start_ns)
st = os.stat(p)
if st.st_mtime_ns < start_ns:
    raise SystemExit("CTPI_V04_SAFE_STALE_RUN_STATUS")
try:
    d = json.load(open(p, encoding="utf-8"))
except Exception as exc:
    raise SystemExit(f"CTPI_V04_SAFE_RUN_STATUS_JSON_INVALID:{exc}")
for key, expected in (("house", house), ("seed", str(seed)), ("arm", arm)):
    if key in d and str(d[key]) != expected:
        raise SystemExit(f"CTPI_V04_SAFE_RUN_STATUS_IDENTITY_MISMATCH:{key}:{d[key]}:{expected}")
text = json.dumps(d).lower()
if "cpir_a1" in text or "cpir_a2" in text or "cpir_a3" in text or "cpir_m1" in text:
    raise SystemExit("CTPI_V04_SAFE_RUN_STATUS_REPORTS_CPIR_MODE")
PY

if (( child_status != 0 )); then
  echo "CTPI_V04_SAFE_CANONICAL_RUNNER_FAILED=${child_status}" >&2
  exit "${child_status}"
fi

echo "CTPI_V04_SAFE_CASE_COMPLETE HOUSE=${HSHORT} SEED=${SEED} ARM=${ARM} RUN_DIR=${RUN_DIR}"

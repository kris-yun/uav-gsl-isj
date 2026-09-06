#!/usr/bin/env bash
set -Eeo pipefail

REPO_ROOT="${REPO_ROOT:-/home/zyc/gsl_ws/src/GasSourceLocalization}"
RUN_ROOT="${RUN_ROOT:?set a fresh RUN_ROOT}"
EVID_ROOT="${EVID_ROOT:?set EVID_ROOT containing closed-loop authorization}"
AUTH_JSON="${AUTH_JSON:-${EVID_ROOT}/CSTAR_FORMAL_CLOSED_LOOP_AUTHORIZATION_V1.json}"
CASE_RUNNER="${CASE_RUNNER:?set CASE_RUNNER to the audited single-case cstar_v1 runner}"
DOMAIN_BASE="${DOMAIN_BASE:-180}"

[[ -f "${AUTH_JSON}" ]] || { echo "CSTAR_12RUN_AUTH_MISSING=${AUTH_JSON}" >&2; exit 2; }
[[ -f "${CASE_RUNNER}" ]] || { echo "CSTAR_12RUN_CASE_RUNNER_MISSING=${CASE_RUNNER}" >&2; exit 2; }
[[ ! -e "${RUN_ROOT}" ]] || { echo "CSTAR_12RUN_REFUSE_EXISTING_RUN_ROOT=${RUN_ROOT}" >&2; exit 70; }

python3 - "${AUTH_JSON}" <<'PY'
import json,sys
p=json.load(open(sys.argv[1],encoding='utf-8'))
assert p.get('contract')=='CSTAR_FORMAL_CLOSED_LOOP_AUTHORIZATION_V1', p.get('contract')
assert p.get('pass') is True and p.get('formal_closed_loop_authorized') is True
m=p.get('authorized_matrix',{})
assert m.get('houses')==['H01','H02','H03']
assert m.get('seed')==12
assert m.get('arms')==['A0','F00','F10','F11']
assert float(m.get('horizon_s'))==240.0
assert int(m.get('run_count'))==12
print('CSTAR_12RUN_AUTHORIZATION_VERIFIED')
PY

mkdir -p "${RUN_ROOT}"
cp "${AUTH_JSON}" "${RUN_ROOT}/CSTAR_FORMAL_CLOSED_LOOP_AUTHORIZATION_V1.json"

declare -a HOUSES=(H01 H02 H03)
declare -a ARMS=(A0 F00 F10 F11)
case_index=0

for HOUSE in "${HOUSES[@]}"; do
  for ARM in "${ARMS[@]}"; do
    DOMAIN_ID=$((DOMAIN_BASE + case_index))
    if (( DOMAIN_ID > 232 )); then
      echo "CSTAR_12RUN_DOMAIN_ID_OUT_OF_FASTDDS_RANGE=${DOMAIN_ID}" >&2
      exit 2
    fi
    CASE_DIR="${RUN_ROOT}/${HOUSE}_seed12_${ARM}"
    [[ ! -e "${CASE_DIR}" ]] || { echo "CSTAR_12RUN_CASE_EXISTS=${CASE_DIR}" >&2; exit 70; }
    echo "CSTAR_12RUN_START house=${HOUSE} seed=12 arm=${ARM} domain=${DOMAIN_ID}"

    HOUSE="${HOUSE}" \
    SEED=12 \
    ARM="${ARM}" \
    TIMEOUT_SEC=240.0 \
    DOMAIN_ID="${DOMAIN_ID}" \
    CASE_RUN_DIR="${CASE_DIR}" \
    CSTAR_AUTH_JSON="${AUTH_JSON}" \
    REPO_ROOT="${REPO_ROOT}" \
      bash "${CASE_RUNNER}"

    for required in source_estimate_trace.csv sensor_trace.csv sim_pose_trace.csv wind_trace.csv; do
      [[ -f "${CASE_DIR}/${required}" ]] || {
        echo "CSTAR_12RUN_REQUIRED_TRACE_MISSING=${CASE_DIR}/${required}" >&2
        exit 2
      }
    done
    [[ -f "${CASE_DIR}/CSTAR_CASE_AUDIT.json" ]] || {
      echo "CSTAR_12RUN_CASE_AUDIT_MISSING=${CASE_DIR}/CSTAR_CASE_AUDIT.json" >&2
      exit 2
    }
    python3 - "${CASE_DIR}/CSTAR_CASE_AUDIT.json" "${HOUSE}" "${ARM}" <<'PY'
import json,sys
p=json.load(open(sys.argv[1],encoding='utf-8'))
assert p.get('contract')=='CSTAR_CASE_AUDIT_V1'
assert p.get('house')==sys.argv[2] and p.get('arm')==sys.argv[3] and p.get('seed')==12
assert p.get('terminal_ok') is True
assert p.get('future_read_violations',0)==0
assert p.get('truth_or_house_runtime_reads',0)==0
assert p.get('deployment_bank_queries',0)==0
print('CSTAR_CASE_AUDIT_PASS',sys.argv[2],sys.argv[3])
PY
    case_index=$((case_index + 1))
  done
done

[[ "${case_index}" -eq 12 ]] || { echo "CSTAR_12RUN_CASE_COUNT=${case_index}" >&2; exit 2; }

python3 "${REPO_ROOT}/tools/cstar_seed12_crosshouse_performance.py" \
  --run-root "${RUN_ROOT}" --seed 12 \
  --output "${RUN_ROOT}/CSTAR_SEED12_CROSSHOUSE_PERFORMANCE_V1.json" || true

python3 - "${RUN_ROOT}" <<'PY'
from pathlib import Path
import hashlib,json,sys
root=Path(sys.argv[1])
rows=[]
for path in sorted(p for p in root.rglob('*') if p.is_file()):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    rows.append({'path':path.relative_to(root).as_posix(),'size':path.stat().st_size,'sha256':h.hexdigest()})
out={'contract':'CSTAR_12RUN_FILE_MANIFEST_V1','files':rows,'file_count':len(rows)}
(root/'CSTAR_12RUN_FILE_MANIFEST_V1.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print('CSTAR_12RUN_COMPLETE')
PY

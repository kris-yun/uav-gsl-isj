#!/usr/bin/env bash
set -Eeuo pipefail

REPO_ROOT="${REPO_ROOT:-/home/zyc/gsl_ws/src/GasSourceLocalization}"
RUN_ROOT="${RUN_ROOT:?set a fresh RUN_ROOT}"
EVID_ROOT="${EVID_ROOT:?set EVID_ROOT containing closed-loop authorization}"
AUTH_JSON="${AUTH_JSON:-${EVID_ROOT}/CSTAR_FORMAL_CLOSED_LOOP_AUTHORIZATION_V1.json}"
CASE_RUNNER="${CASE_RUNNER:?set CASE_RUNNER to the audited single-case cstar_v1 runner}"
DOMAIN_BASE="${DOMAIN_BASE:-180}"

[[ -f "${AUTH_JSON}" ]] || { echo "CSTAR_12RUN_AUTH_MISSING=${AUTH_JSON}" >&2; exit 2; }
[[ -f "${CASE_RUNNER}" ]] || { echo "CSTAR_12RUN_CASE_RUNNER_MISSING=${CASE_RUNNER}" >&2; exit 2; }
[[ ! -e "${RUN_ROOT}" ]] || { echo "CSTAR_12RUN_REFUSE_EXISTING_RUN_ROOT=${RUN_ROOT}" >&2; exit 70; }

# Re-verify the authorization identity and every input hash immediately before
# launching the first formal case. Do not trust a stale authorization label.
python3 - "${AUTH_JSON}" "${REPO_ROOT}" <<'PY'
import hashlib,json,pathlib,subprocess,sys

def fail(msg):
    raise SystemExit(msg)

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

auth_path=pathlib.Path(sys.argv[1])
repo=pathlib.Path(sys.argv[2])
p=json.loads(auth_path.read_text(encoding='utf-8'))
if p.get('contract')!='CSTAR_FORMAL_CLOSED_LOOP_AUTHORIZATION_V1': fail('CSTAR_12RUN_AUTH_CONTRACT')
if p.get('pass') is not True or p.get('formal_closed_loop_authorized') is not True: fail('CSTAR_12RUN_AUTH_NOT_PASS')
m=p.get('authorized_matrix')
if not isinstance(m,dict): fail('CSTAR_12RUN_AUTH_MATRIX_MISSING')
expected={'houses':['H01','H02','H03'],'seed':12,'arms':['A0','F00','F10','F11'],'horizon_s':240.0,'run_count':12}
for k,v in expected.items():
    if m.get(k)!=v: fail(f'CSTAR_12RUN_AUTH_MATRIX_MISMATCH:{k}:{m.get(k)}:{v}')
inputs=p.get('inputs')
if not isinstance(inputs,dict): fail('CSTAR_12RUN_AUTH_INPUTS_MISSING')
for label in ('m1','m2','m3','models','production','smoke'):
    item=inputs.get(label)
    if not isinstance(item,dict): fail(f'CSTAR_12RUN_AUTH_INPUT_MISSING:{label}')
    path=pathlib.Path(str(item.get('path','')))
    if not path.is_file(): fail(f'CSTAR_12RUN_AUTH_INPUT_FILE_MISSING:{label}:{path}')
    actual=sha(path)
    if actual!=item.get('sha256'): fail(f'CSTAR_12RUN_AUTH_INPUT_HASH_DRIFT:{label}:{actual}:{item.get("sha256")}')
head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
if head!=p.get('authorized_git_sha'): fail(f'CSTAR_12RUN_GIT_DRIFT:{head}:{p.get("authorized_git_sha")}')
print('CSTAR_12RUN_AUTHORIZATION_REVERIFIED')
PY

AUTH_SHA="$(sha256sum "${AUTH_JSON}" | awk '{print $1}')"
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
    CSTAR_AUTH_SHA256="${AUTH_SHA}" \
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

    python3 - "${CASE_DIR}/CSTAR_CASE_AUDIT.json" "${AUTH_JSON}" "${HOUSE}" "${ARM}" <<'PY'
import hashlib,json,pathlib,sys

def fail(msg):
    raise SystemExit(msg)

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

audit_path=pathlib.Path(sys.argv[1]); auth_path=pathlib.Path(sys.argv[2])
house=sys.argv[3]; arm=sys.argv[4]
p=json.loads(audit_path.read_text(encoding='utf-8'))
a=json.loads(auth_path.read_text(encoding='utf-8'))
required=[
 'contract','house','seed','arm','git_sha','authorization_sha256','terminal_ok',
 'sim_start_s','sim_end_s','future_read_violations','truth_or_house_runtime_reads',
 'deployment_bank_queries','decision_count','fallback_count','fallback_reasons',
 'invalid_route_count','native_route_missing_when_feasible','model_manifest_sha256',
 'production_manifest_sha256','legacy_classic_pmfs','cstar_model_calls','picr_calls',
 'phs_calls','baseline_route_provider_calls','learned_cpo_calls','map_chase_calls',
 'posterior_guidance_coefficient_used','baseline_route_provider_scientific_path',
 'start_time_utc','end_time_utc'
]
missing=[k for k in required if k not in p]
if missing: fail('CSTAR_CASE_AUDIT_FIELDS_MISSING:'+','.join(missing))
if p['contract']!='CSTAR_CASE_AUDIT_V1': fail('CSTAR_CASE_AUDIT_CONTRACT')
if p['house']!=house or p['arm']!=arm or p['seed']!=12: fail('CSTAR_CASE_AUDIT_IDENTITY')
if p['git_sha']!=a.get('authorized_git_sha'): fail('CSTAR_CASE_AUDIT_GIT_MISMATCH')
if p['authorization_sha256']!=sha(auth_path): fail('CSTAR_CASE_AUDIT_AUTH_HASH_MISMATCH')
inputs=a.get('inputs',{})
if p['model_manifest_sha256']!=inputs.get('models',{}).get('sha256'): fail('CSTAR_CASE_AUDIT_MODEL_HASH_MISMATCH')
if p['production_manifest_sha256']!=inputs.get('production',{}).get('sha256'): fail('CSTAR_CASE_AUDIT_PRODUCTION_HASH_MISMATCH')
if p['terminal_ok'] is not True: fail('CSTAR_CASE_AUDIT_TERMINAL_FAIL')
if abs(float(p['sim_start_s']))>1e-9: fail('CSTAR_CASE_AUDIT_SIM_START')
if float(p['sim_end_s'])<240.0: fail('CSTAR_CASE_AUDIT_SIM_END')
for field in ('future_read_violations','truth_or_house_runtime_reads','deployment_bank_queries','invalid_route_count','native_route_missing_when_feasible','fallback_count'):
    if type(p[field]) is not int or p[field]!=0: fail(f'CSTAR_CASE_AUDIT_NONZERO:{field}:{p[field]}')
if type(p['decision_count']) is not int or p['decision_count']<=0: fail('CSTAR_CASE_AUDIT_NO_DECISIONS')
for field in ('cstar_model_calls','picr_calls','phs_calls','baseline_route_provider_calls','learned_cpo_calls','map_chase_calls'):
    if type(p[field]) is not int or p[field]<0: fail(f'CSTAR_CASE_AUDIT_BAD_CALL_COUNT:{field}:{p[field]}')
if type(p['posterior_guidance_coefficient_used']) is not bool: fail('CSTAR_CASE_AUDIT_BAD_GUIDANCE_FLAG')
if type(p['legacy_classic_pmfs']) is not bool or type(p['baseline_route_provider_scientific_path']) is not bool: fail('CSTAR_CASE_AUDIT_BAD_BOOL')

if arm=='A0':
    if p['legacy_classic_pmfs'] is not True: fail('CSTAR_A0_NOT_CLASSIC')
    if any(p[k]!=0 for k in ('cstar_model_calls','picr_calls','phs_calls','baseline_route_provider_calls','learned_cpo_calls')): fail('CSTAR_A0_CSTAR_CALLS_PRESENT')
elif arm=='F00':
    if p['legacy_classic_pmfs'] is not False or p['picr_calls']<=0: fail('CSTAR_F00_PICR_IDENTITY')
    if p['phs_calls']!=0 or p['baseline_route_provider_calls']!=0 or p['learned_cpo_calls']!=0: fail('CSTAR_F00_FORBIDDEN_MODULE_CALL')
    if p['map_chase_calls']!=0 or p['posterior_guidance_coefficient_used'] is not False: fail('CSTAR_F00_GUIDANCE_BYPASS')
elif arm=='F10':
    if p['legacy_classic_pmfs'] is not False or p['picr_calls']<=0 or p['phs_calls']<=0 or p['baseline_route_provider_calls']<=0: fail('CSTAR_F10_MODULE_IDENTITY')
    if p['learned_cpo_calls']!=0 or p['baseline_route_provider_scientific_path'] is not True: fail('CSTAR_F10_PROVIDER_IDENTITY')
elif arm=='F11':
    if p['legacy_classic_pmfs'] is not False or p['picr_calls']<=0 or p['phs_calls']<=0 or p['learned_cpo_calls']<=0: fail('CSTAR_F11_MODULE_IDENTITY')
    if p['baseline_route_provider_scientific_path'] is not False: fail('CSTAR_F11_BASELINE_PROVIDER_USED')
else:
    fail('CSTAR_CASE_AUDIT_UNKNOWN_ARM')
print('CSTAR_CASE_AUDIT_PASS',house,arm)
PY
    case_index=$((case_index + 1))
  done
done

[[ "${case_index}" -eq 12 ]] || { echo "CSTAR_12RUN_CASE_COUNT=${case_index}" >&2; exit 2; }

PERF_JSON="${RUN_ROOT}/CSTAR_SEED12_CROSSHOUSE_PERFORMANCE_V1.json"
set +e
python3 "${REPO_ROOT}/tools/cstar_seed12_crosshouse_performance.py" \
  --run-root "${RUN_ROOT}" --seed 12 --output "${PERF_JSON}"
EVAL_RC=$?
set -e

[[ -f "${PERF_JSON}" ]] || {
  echo "CSTAR_12RUN_EVALUATOR_FAILED_WITHOUT_ARTIFACT rc=${EVAL_RC}" >&2
  exit 3
}

EVAL_CLASS="$(python3 - "${PERF_JSON}" "${EVAL_RC}" <<'PY'
import json,sys
p=json.load(open(sys.argv[1],encoding='utf-8')); rc=int(sys.argv[2])
if p.get('contract')!='CSTAR_SEED12_CROSSHOUSE_PERFORMANCE_V1':
    raise SystemExit('CSTAR_12RUN_BAD_PERFORMANCE_CONTRACT')
if rc==0 and p.get('pass') is True:
    print('SCIENTIFIC_PASS')
elif rc==2 and p.get('pass') is False:
    print('SCIENTIFIC_NO_GO')
else:
    raise SystemExit(f'CSTAR_12RUN_EVALUATOR_STATUS_MISMATCH:rc={rc}:pass={p.get("pass")}')
PY
)"

python3 - "${RUN_ROOT}" "${EVAL_CLASS}" <<'PY'
from pathlib import Path
import hashlib,json,sys
root=Path(sys.argv[1]); eval_class=sys.argv[2]
rows=[]
for path in sorted(p for p in root.rglob('*') if p.is_file()):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    rows.append({'path':path.relative_to(root).as_posix(),'size':path.stat().st_size,'sha256':h.hexdigest()})
out={
 'contract':'CSTAR_12RUN_FILE_MANIFEST_V1',
 'matrix_execution_complete':True,
 'scientific_evaluation_status':eval_class,
 'files':rows,'file_count':len(rows)
}
(root/'CSTAR_12RUN_FILE_MANIFEST_V1.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print('CSTAR_12RUN_MATRIX_EXECUTED')
print('CSTAR_12RUN_'+eval_class)
PY

if [[ "${EVAL_CLASS}" == "SCIENTIFIC_NO_GO" ]]; then
  exit 2
fi

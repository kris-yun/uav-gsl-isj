#!/usr/bin/env bash
# Four offline H03 source x transport probe worlds. No PMFS or planner runs.
set -Ee -o pipefail

OUT_ROOT=${1:?output root required}
REPO_ROOT=${2:?frozen extracted repository root required}
SENSOR_ROOT=${3:?qualified sensor root required}
: "${FREEZE_COMMIT:?full frozen commit required}"
: "${FREEZE_RECEIPT:?host verification receipt required}"
: "${SOURCE_ARCHIVE:?host source archive required}"
[[ "$FREEZE_COMMIT" =~ ^[0-9a-f]{40}$ ]] || { echo FULL_FREEZE_COMMIT_REQUIRED >&2; exit 2; }
[[ ! -e "$OUT_ROOT" ]] || { echo REFUSE_EXISTING_OUTPUT >&2; exit 2; }

ROUTE_ROOT=$REPO_ROOT/evidence/m1r_h03_rank2_paired_probe_20260913/route
ROUTE=$ROUTE_ROOT/H03/history_route.csv
RULE=$ROUTE_ROOT/ROUTE_RULE.json
SELF=$REPO_ROOT/tools/run_h03_rank2_paired_probe.sh
EXTRACTOR=$REPO_ROOT/tools/cstar_extract_current_runtime_history.py
SIM_BIN=/home/zyc/PF_DEI_V3_GADEN_BUILD_REF/install/lib/gaden_filament_simulator/filament_simulator
ENV_BASE=/mnt/hgfs/workspace/GADEN_files/scenarios
RAW_BASE=/mnt/hgfs/workspace/GADEN_files/scenarios
HELPER=/home/zyc/CSTAR_CONTROLLED_ASSETS_20260907/tools/cstar_numeric_wind_raw_query
PY=/usr/bin/python3
export FREEZE_COMMIT FREEZE_RECEIPT SOURCE_ARCHIVE REPO_ROOT ROUTE RULE SELF OUT_ROOT

cmp -- "${BASH_SOURCE[0]}" "$SELF"
python3 - <<'PY'
import hashlib,json,os,pathlib
e=os.environ; receipt=pathlib.Path(e['FREEZE_RECEIPT']); archive=pathlib.Path(e['SOURCE_ARCHIVE'])
r=json.loads(receipt.read_text()); digest=hashlib.sha256(archive.read_bytes()).hexdigest()
expected={'schema':'M1R_RANK2_HOST_REMOTE_RECEIPT_V1','resolved_commit':e['FREEZE_COMMIT'],
          'source_archive_sha256':digest}
for key,value in expected.items():
    if r.get(key)!=value: raise SystemExit('FREEZE_RECEIPT_MISMATCH:'+key)
rule=json.loads(pathlib.Path(e['RULE']).read_text())
route=pathlib.Path(e['ROUTE'])
if rule['status']!='PRE_EXPERIMENT_SOURCE_GAS_BLIND_FREEZE': raise SystemExit('ROUTE_NOT_FROZEN')
if hashlib.sha256(route.read_bytes()).hexdigest()!=rule['route']['sha256']: raise SystemExit('ROUTE_HASH_MISMATCH')
if rule['measurement_operator_rank']!=2 or rule['direction_condition_number']>1.1:
    raise SystemExit('RANK2_GEOMETRY_CONTRACT_FAILED')
PY

source /opt/ros/humble/setup.bash
source /home/zyc/PF_DEI_V3_GADEN_BUILD_REF/install/setup.bash
set -u
export LD_LIBRARY_PATH=/home/zyc/PF_DEI_V3_GADEN_BUILD_REF/install/gaden_common/lib:/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/gaden_install/gaden_common/lib:/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/gaden_install/lib:/home/zyc/ros2_ws/install/gaden_common/lib:${LD_LIBRARY_PATH:-}
export GADEN_RNG_SEED=1234
export PYTHONDONTWRITEBYTECODE=1

read -r ROUTE_END SIM_TIME_S EXPECTED_FRAMES < <(python3 - <<'PY'
import csv,math,os
rows=list(csv.DictReader(open(os.environ['ROUTE'])))
end=float(rows[-1]['t_sim_s']); sim=round(end+0.1,9); frames=round(sim/0.1)
print(end,sim,frames)
PY
)
export ROUTE_END SIM_TIME_S EXPECTED_FRAMES

check_idle() {
  python3 - <<'PY'
import os,pathlib
found=[]
for p in pathlib.Path('/proc').iterdir():
    if not p.name.isdigit(): continue
    try:
        if p.stat().st_uid!=os.getuid(): continue
        args=p.joinpath('cmdline').read_bytes().decode(errors='replace').split('\0')
        if any(pathlib.Path(x).name in {'filament_simulator','gsl_actionserver_node','vgr_sim_node'} for x in args[:3] if x):
            found.append((p.name,args[:3]))
    except (FileNotFoundError,PermissionError): pass
if found: raise SystemExit('EXPERIMENT_ALREADY_RUNNING:'+repr(found))
PY
}

mkdir -p "$OUT_ROOT/provenance"
cp -- "$RULE" "$OUT_ROOT/provenance/ROUTE_RULE.json"
cp -- "$FREEZE_RECEIPT" "$OUT_ROOT/provenance/HOST_REMOTE_RECEIPT.json"
sha256sum "$SOURCE_ARCHIVE" >"$OUT_ROOT/provenance/SOURCE_ARCHIVE.sha256"
sha256sum "$SELF" "$EXTRACTOR" "$ROUTE" >"$OUT_ROOT/provenance/PRE_RUN_SHA256"

run_case() {
  local id=$1 wind_config=$2 sx=$3 sy=$4 sz=$5
  check_idle
  local work=/dev/shm/m1r_rank2_${FREEZE_COMMIT:0:12}_${id}
  [[ ! -e "$work" ]] || { echo REFUSE_EXISTING_WORK:$work >&2; return 3; }
  local input=$work/input output=$work/output raw_wind
  mkdir -p "$input" "$output" "$OUT_ROOT/$id"
  raw_wind=$(find "$RAW_BASE/House03/gas_simulations/$wind_config" -maxdepth 4 -type d -name wind | sort | head -1)
  [[ -n "$raw_wind" ]] || { echo WIND_NOT_FOUND:$wind_config >&2; return 4; }
  [[ $(find "$raw_wind" -maxdepth 1 -type f -name 'wind_iteration_*' | wc -l) -eq 11 ]] || {
    echo WIND_FILE_COUNT_MISMATCH:$wind_config >&2; return 4;
  }
  for file in "$raw_wind"/wind_iteration_*; do
    number=${file##*_}
    cp -- "$file" "$input/wind_iteration_${number}.csv_gaden"
  done
  python3 - "$OUT_ROOT/$id/CASE_MANIFEST.json" "$id" "$wind_config" "$sx" "$sy" "$sz" "$raw_wind" <<'PY'
import datetime,hashlib,json,pathlib,sys,os
out,cid,wind,sx,sy,sz,wind_dir=sys.argv[1:]
files=sorted(pathlib.Path(wind_dir).glob('wind_iteration_*'))
m={'contract':'M1R_H03_RANK2_PAIRED_WORLD_V1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
   'freeze_commit':os.environ['FREEZE_COMMIT'],'case_id':cid,'house':'H03','canonical_wind_config':wind,
   'source_xyz_m_evaluator_only':[float(sx),float(sy),float(sz)],'gaden_rng_seed':1234,
   'route_sha256':hashlib.sha256(pathlib.Path(os.environ['ROUTE']).read_bytes()).hexdigest(),
   'wind_directory':wind_dir,'wind_iteration_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
pathlib.Path(out).write_text(json.dumps(m,indent=2)+'\n')
PY
  timeout 300s "$SIM_BIN" --ros-args \
    -p sim_time:="$SIM_TIME_S" -p time_step:=0.1 -p num_filaments_sec:=7 \
    -p variable_rate:=true -p filament_stop_steps:=0 -p ppm_filament_center:=10.0 \
    -p filament_initial_std:=10.0 -p filament_growth_gamma:=15.0 \
    -p filament_noise_std:=0.01 -p gas_type:=10 -p temperature:=298.0 -p pressure:=1.0 \
    -p concentration_unit_choice:=1 -p occupancy3D_data:="$ENV_BASE/House03/OccupancyGrid3D.csv" \
    -p wind_data:="$input/wind_iteration" -p wind_time_step:=1.0 \
    -p allow_looping:=true -p loop_from_step:=1 -p loop_to_step:=10 \
    -p source_position_x:="$sx" -p source_position_y:="$sy" -p source_position_z:="$sz" \
    -p save_results:=1 -p results_time_step:=0.0 -p results_min_time:=0.0 \
    -p writeConcentrations:=false -p results_location:="$output" \
    >"$OUT_ROOT/$id/sim.log" 2>&1
  [[ $(find "$output" -maxdepth 1 -type f -name 'iteration_*' | wc -l) -ge "$EXPECTED_FRAMES" ]] || {
    echo INCOMPLETE_GAS_FRAMES:$id >&2; return 5;
  }
  "$PY" "$EXTRACTOR" \
    --env-root "$ENV_BASE/House03" --gas-results "$output" --route "$ROUTE" --helper "$HELPER" \
    --sensor-module "$SENSOR_ROOT/H03/sensor_model.py" \
    --sensor-manifest "$SENSOR_ROOT/H03/sensor_manifest.json" --raw-dt 0.1 \
    --output "$OUT_ROOT/$id/measured_history.jsonl" \
    --candidate-forward-output "$OUT_ROOT/$id/candidate_forward_input.jsonl"
  sha256sum "$OUT_ROOT/$id/CASE_MANIFEST.json" "$OUT_ROOT/$id/measured_history.jsonl" \
    "$OUT_ROOT/$id/candidate_forward_input.jsonl" "$OUT_ROOT/$id/sim.log" \
    >"$OUT_ROOT/$id/FILE_SHA256"
}

# Same failed H03 source and historical strongest-false region centroid, each
# under the same two existing transport interventions.  No new House or seed.
run_case H03_SA_fast '1-2,5_fast' -0.45 1.90 -0.10
run_case H03_SA_slow '1-2,5_slow' -0.45 1.90 -0.10
run_case H03_HF_fast '1-2,5_fast' 8.15 -1.413 -0.10
run_case H03_HF_slow '1-2,5_slow' 8.15 -1.413 -0.10

python3 - <<'PY'
import datetime,hashlib,json,os,pathlib
root=pathlib.Path(os.environ['OUT_ROOT']); files=[]
for path in sorted(root.rglob('*')):
    if path.is_file(): files.append({'path':str(path.relative_to(root)),'bytes':path.stat().st_size,
        'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
m={'contract':'M1R_H03_RANK2_PAIRED_PROBE_RAW_V1','completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
   'freeze_commit':os.environ['FREEZE_COMMIT'],'route_end_s':float(os.environ['ROUTE_END']),
   'sim_time_s':float(os.environ['SIM_TIME_S']),'cases':['H03_SA_fast','H03_SA_slow','H03_HF_fast','H03_HF_slow'],
   'scope':'offline H03 response premise only; no PMFS, planner, posterior or closed loop','files':files}
(root/'RAW_MANIFEST.json').write_text(json.dumps(m,indent=2)+'\n')
print('M1R_H03_RANK2_PAIRED_PROBE_RAW_COMPLETE='+str(root))
PY

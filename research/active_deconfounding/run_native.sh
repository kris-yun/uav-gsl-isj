#!/usr/bin/env bash
source /opt/ros/humble/setup.bash
source /home/zyc/ros2_ws/install/setup.bash
source /dev/shm/house1_msgs_install/setup.bash
set -Ee -o pipefail
ROOT=/home/zyc/ros2_ws/active_deconfounding_v1_20260921
mkdir -p "$ROOT/source"
tar -xzf /home/zyc/ros2_ws/active_deconfounding_source_20260921.tar.gz -C "$ROOT/source"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
python3 "$ROOT/source/research/active_deconfounding/build_native.py" \
  /home/zyc/ros2_ws/tnqc_h01_pipeline_20260921/verified_native_v2/build "$ROOT/build"
python3 - "$ROOT" <<'PY'
import csv,hashlib,json,pathlib,subprocess,sys
r=pathlib.Path(sys.argv[1]); evidence=r/'source/evidence/active_deconfounding_v1/pre_response'
original=pathlib.Path('/home/zyc/ros2_ws/tnqc_r2_six_offline_20260921_authoritative')
worlds=evidence/'worlds.csv'
freeze=json.loads((evidence/'PRE_RESPONSE_FREEZE.json').read_text())
for case in freeze['cases']:
    design=evidence/(case['case']+'.json')
    assert hashlib.sha256(design.read_bytes()).hexdigest()==case['design_sha256']
    d=json.loads(design.read_text()); out=r/'run'/d['case'];out.mkdir(parents=True,exist_ok=True)
    src=out/'sources.csv'
    with src.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(d['sources'][0]));w.writeheader();w.writerows(d['sources'])
    bank=original/'native'/(d['case']+'_off_off')/'context_bank'
    for p,h in d['inputs_sha256'].items():
        suffix=p.replace('\\','/').split('/context_bank/',1)[1]
        assert hashlib.sha256((bank/suffix).read_bytes()).hexdigest()==h,(d['case'],suffix)
    subprocess.run([str(r/'build/native_bank'),str(bank),str(d['update']),str(src),str(worlds),str(out),str(d['seed'])],check=True)
PY

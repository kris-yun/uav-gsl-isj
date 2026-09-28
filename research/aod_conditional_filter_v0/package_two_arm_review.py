#!/usr/bin/env python3
"""Package the one-case, two-arm VGR pilot with full raw logs and frozen code."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import zipfile


def sha(blob):return hashlib.sha256(blob).hexdigest()


def result_from_archive(path,zstd):
    data=subprocess.run([zstd,'-dc',str(path)],capture_output=True,check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:') as tar:
        names=[m for m in tar.getmembers() if m.name.endswith('.json') and '/' not in m.name]
        if len(names)!=1:raise RuntimeError(f'unexpected top-level result in {path}')
        return json.load(tar.extractfile(names[0]))


def main():
    ap=argparse.ArgumentParser()
    for name in ('native','filter','zstd','code-dir','output','summary'):
        ap.add_argument('--'+name,required=True)
    a=ap.parse_args()
    native=Path(a.native);filt=Path(a.filter);code=Path(a.code_dir)
    n=result_from_archive(native,a.zstd);f=result_from_archive(filt,a.zstd)
    fields=('case_id','source_id','plume_id','initial_pose_id','observation_contract_id',
            'candidate_support_id','truth_xy','budget_s')
    if any(n[k]!=f[k] for k in fields):raise RuntimeError('two-arm case/observation mismatch')
    if n['arm']!='native_pmfs' or f['arm']!='aod_filter':raise RuntimeError('arms differ')
    if n['actual_native_support_count']!=596 or f['actual_native_support_count']!=596:
        raise RuntimeError('support count mismatch')
    if not n['common_legal_support_matches'] or not f['common_legal_support_matches']:
        raise RuntimeError('legal support mismatch')
    for row in (n,f):
        if row['callback_exception_count'] or row['navigation_failure_count'] or row['issued_goal_count']<1:
            raise RuntimeError('invalid interactive navigation run')
    summary={'status':'AOD_TWO_ARM_CASE009_BOTH_GEOMETRIC_FAIL_FILTER_ERROR_LOWER',
             'scope':'one OPEN development case; no neural network and no scientific confirmation',
             'case_id':n['case_id'],'truth_xy':n['truth_xy'],
             'candidate_support_count':596,'budget_s':300,
             'native':{k:n[k] for k in ('estimate_xy','final_source_error_m','geometric_success',
                'status','timeout','measurement_count','path_length_m','issued_goal_count')},
             'aod_filter':{k:f[k] for k in ('estimate_xy','final_source_error_m','geometric_success',
                'status','timeout','measurement_count','path_length_m','issued_goal_count')},
             'error_reduction_m':n['final_source_error_m']-f['final_source_error_m'],
             'interpretation':'Filter error is smaller in this single case, but both exceed 0.5 m. The eight OPEN dev cases had poor truth ranks; no general benefit is claimed.'}
    Path(a.summary).write_text(json.dumps(summary,indent=2)+'\n')
    files={'raw/'+native.name:native.read_bytes(),'raw/'+filt.name:filt.read_bytes(),
           'TWO_ARM_RESULT.json':json.dumps(summary,indent=2).encode()+b'\n'}
    for name in ('gain_innovation_bank.py','bank.py','episode_io.py','calibrate_open.py',
                 'check_open_dev.py','serve_aod_filter_vm.py','bind_aod_case_vm.py',
                 'TRAIN_ONLY_CALIBRATION.json','OPEN_DEV_CHECK.json','SYNTHETIC_SELFTEST.json',
                 'TWO_ARM_FREEZE.json'):
        files['code_and_freeze/'+name]=(code/name).read_bytes()
    manifest=''.join(f'{sha(value)}  {name}\n' for name,value in sorted(files.items())).encode()
    out=Path(a.output)
    if out.exists():raise FileExistsError(out)
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,data in files.items():z.writestr(name,data)
        z.writestr('SHA256SUMS',manifest)
    with zipfile.ZipFile(out) as z:
        for line in z.read('SHA256SUMS').decode().splitlines():
            expected,name=line.split('  ',1)
            if sha(z.read(name))!=expected:raise RuntimeError('ZIP internal hash failure')
    print(json.dumps({'status':'AOD_TWO_ARM_REVIEW_PACKAGED','path':str(out),
                      'bytes':out.stat().st_size,'sha256':sha(out.read_bytes()),
                      'summary':summary},indent=2))

if __name__=='__main__':main()

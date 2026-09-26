#!/usr/bin/env python3
"""Allowlisted evidence packaging. Freeze phase never reads truth."""
import argparse,hashlib,json,os,platform,shutil,subprocess,tarfile,zipfile
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['freeze','final']);a=ap.parse_args()
root=Path('/home/zyc/wind_alignment_d0_20260926');dest=root/('freeze_evidence' if a.phase=='freeze' else 'review_evidence')
dest.mkdir(exist_ok=False)
items=['code','inputs','state_inputs','forward_bank','forward_bank_repeat','P0_preflight','scores','scores_repeat','P0_parity.json','P0_bank_parity.json','P0_repeat_parity.json','deterministic_repeat.json','build_provenance.json','build.log','prepare_inputs.log','P0_preflight.log','forward_bank.log','forward_bank_repeat.log']
if a.phase=='final':items+=['evaluation','truth_historical.json','freeze_commit.txt']
for name in items:
    p=root/name
    if p.is_dir(): shutil.copytree(p,dest/name,ignore=shutil.ignore_patterns('__pycache__'))
    else: shutil.copy2(p,dest/name)
ref=dest/'historical_kernel';ref.mkdir()
base=Path('/home/zyc/native_pmfs_recovery_v1/src/gsl_server/src/gsl_server/algorithms')
for p in [base/'PMFS/internal/Simulations.cpp',base/'PMFS/internal/Simulations.hpp',base/'Common/Utils/Math.cpp',base/'Common/Utils/Math.hpp']:
    shutil.copy2(p,ref/p.name)
prior=Path('/home/zyc/wind_contract_identity_audit_20260926/evidence_collection_attempt1/assets')
for name in ['wind_value_server.py','vgr_sim_node.py','wind_trace.csv','sim_timebase.py']:
    shutil.copy2(prior/name,ref/name)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record={'phase':a.phase,'truth_opened_in_this_package_step':False,'python':platform.python_version(),'numpy':__import__('numpy').__version__,'platform':platform.platform(),'compiler':subprocess.check_output(['c++','--version'],text=True).splitlines()[0],'rng':'historical continuous minstd_rand0 and normal distribution cache; fork siblings','threads':{'OMP_NUM_THREADS':1,'OPENBLAS_NUM_THREADS':1,'OpenCV':1},'scientific_contract':'WIND_ALIGNMENT_D0_20260926','original_zip_sha256':'ccab1bd8409a8810d858ba5f7c5a7e9963b2b54b5641428fe027906120b39981','infrastructure_only_patch':False,'implementation_added':'supplied package had specification only; exact historical replay reused with fork snapshot and frozen scorer/evaluator','source_blind_inputs':'no source truth is read by prepare, replay, scorer, repeat checker or freeze packager'}
(dest/'EXECUTION_PROVENANCE.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
files=[p for p in sorted(dest.rglob('*')) if p.is_file()]
(dest/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(dest))+'\n' for p in files))
if a.phase=='freeze':
    archive=root/'freeze_evidence.tar.gz'
    with tarfile.open(archive,'w:gz') as tf:tf.add(dest,arcname='.')
else:
    archive=root/'WIND_ALIGNMENT_D0_REVIEW_20260926.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(dest.rglob('*')):
            if p.is_file():z.write(p,str(p.relative_to(dest)))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for line in z.read('SHA256SUMS').decode().splitlines():
            expected,name=line.split('  ',1);assert hashlib.sha256(z.read(name)).hexdigest()==expected
print(json.dumps({'path':str(archive),'bytes':archive.stat().st_size,'sha256':sha(archive)},indent=2))

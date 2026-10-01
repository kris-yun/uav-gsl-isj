"""Execute only after a committed final contract and explicit gate amendment."""
import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--repo',type=Path,required=True)
p.add_argument('--audit',type=Path,required=True)
p.add_argument('--inputs',type=Path,required=True)
p.add_argument('--binary',type=Path,required=True)
p.add_argument('--build-audit',type=Path,required=True)
p.add_argument('--amendment',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
amendment=json.loads(a.amendment.read_text())
assert amendment['scientific_execution_authorized'] is True
assert amendment['three_arm_control_authorized'] is True
assert amendment['rank_gate'] in ('strict_improvement','noninferiority')
contract=a.repo/'research/pmfs3d_r1/R1_FORWARD_CONTRACT_FINAL.md'
assert contract.is_file(), 'final contract not frozen'
head=subprocess.check_output(['git','-C',str(a.repo),'rev-parse','HEAD'],text=True).strip()
for file in (contract,a.amendment):
    relative=file.resolve().relative_to(a.repo.resolve()).as_posix()
    subprocess.run(['git','-C',str(a.repo),'ls-files','--error-unmatch',relative],check=True,capture_output=True)
    subprocess.run(['git','-C',str(a.repo),'diff','--exit-code','HEAD','--',relative],check=True,capture_output=True)
build=json.loads(a.build_audit.read_text())
assert sha(a.binary)==build['binary_sha256']
assert sha(a.repo/'research/pmfs3d_r1/oracle_forward.cpp')==build['source_sha256']
assert build['protected_unchanged'] is True
audit=json.loads(a.audit.read_text())
assert len(audit['cases'])==4
assert not a.out.exists(), 'existing run preserved; refusing overwrite/retry'
a.out.mkdir(parents=True)
before={str(f.relative_to(a.inputs)):sha(f) for f in sorted(a.inputs.rglob('*')) if f.is_file()}
oracle_assets=json.loads((a.inputs/'ORACLE_ASSET_HASHES.json').read_text())
for asset in oracle_assets:assert sha(Path(asset['path']))==asset['sha256']
run_audit=dict(preforward_commit=head,amendment_sha256=sha(a.amendment),contract_sha256=sha(contract),
               inputs_sha256=before,build_audit_sha256=sha(a.build_audit),new_gaden_runs=0,closed_loop_runs=0)
(a.out/'PREFORWARD_FREEZE.json').write_text(json.dumps(run_audit,indent=2,sort_keys=True)+'\n')
timings=[]
for repeat in (1,2):
    folder=a.out/f'repeat{repeat}'
    for case in audit['cases']:
        inputs=a.inputs/case['case']
        for arm in ('native','oracle2d','oracle3d'):
            out=folder/case['case']/arm
            started=time.monotonic()
            subprocess.run([str(a.binary),str(inputs),str(inputs/'config.csv'),arm,str(out)],check=True)
            timings.append(dict(repeat=repeat,case=case['case'],arm=arm,seconds=time.monotonic()-started))
    subprocess.run([sys.executable,str(a.repo/'research/pmfs3d_r1/evaluate_oracle_ranking.py'),
                    '--audit',str(a.audit),'--outputs',str(folder),'--amendment',str(a.amendment),
                    '--out',str(a.out/f'evaluation{repeat}')],check=True)
first={str(f.relative_to(a.out/'repeat1')):sha(f) for f in sorted((a.out/'repeat1').rglob('*')) if f.is_file()}
second={str(f.relative_to(a.out/'repeat2')):sha(f) for f in sorted((a.out/'repeat2').rglob('*')) if f.is_file()}
eval1={str(f.relative_to(a.out/'evaluation1')):sha(f) for f in sorted((a.out/'evaluation1').rglob('*')) if f.is_file()}
eval2={str(f.relative_to(a.out/'evaluation2')):sha(f) for f in sorted((a.out/'evaluation2').rglob('*')) if f.is_file()}
assert first==second,'forward repeat differs'
assert eval1==eval2,'evaluation repeat differs'
after={str(f.relative_to(a.inputs)):sha(f) for f in sorted(a.inputs.rglob('*')) if f.is_file()}
assert before==after,'frozen inputs changed'
for asset in oracle_assets:assert sha(Path(asset['path']))==asset['sha256']
(a.out/'DETERMINISTIC_REPEAT.json').write_text(json.dumps(dict(forward_byte_identical=True,evaluation_byte_identical=True,
    frozen_inputs_unchanged=True,oracle_assets_unchanged=True,forward_hashes=first,evaluation_hashes=eval1),indent=2,sort_keys=True)+'\n')
(a.out/'RUNTIME_ONLY.json').write_text(json.dumps(timings,indent=2,sort_keys=True)+'\n')
print('PMFS3D_R1_DONE_STOP')

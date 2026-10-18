"""Freeze the final C4 audit; copy evidence, never alter archived studies."""
from pathlib import Path
import csv, datetime, hashlib, json, shutil, subprocess, base64
R=Path(__file__).resolve().parent
OLD=R.parent/'C4H17'
PY=Path(r'C:\Users\50176\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe')
for d in ['code','inputs','results','scripts','lineage','logs','source']:(R/d).mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(cmd,name,input=None):
    q=subprocess.run(cmd,input=input,capture_output=True)
    (R/'logs'/f'{name}.stdout').write_bytes(q.stdout);(R/'logs'/f'{name}.stderr').write_bytes(q.stderr)
    (R/'logs'/f'{name}.command.json').write_text(json.dumps(dict(command=cmd,exit_code=q.returncode),indent=2))
    assert q.returncode==0,(name,q.stderr[-2000:]);return q.stdout
assert not (R/'FROZEN_PLAN.json').exists(),'Refuse refreeze'
plan=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
 objective='Final bounded closure: same-realization centre/PID event audit, not a new method',
 maximum_forward_calls=6, states=[2026101701,2026101702,2026101703],
 source_jobs=['fine_truth_1272','fine_competitor'], warmup_steps=0,record_steps=3600,dt=.1,
 release_per_step=5,source_truth_use='offline diagnostic only; never online free information',
 no_new_worlds=True,no_ROS=True,no_more_time_or_seed_search=True,
 no_candidate_posterior_from_truth_world=True,
 stop='End C4 innovation pursuit if no identifiable necessary new operation; no automatic next experiment',
 prior_study_final_decision_sha256=sha(OLD/'FINAL_DECISION.json'))
(R/'FROZEN_PLAN.json').write_text(json.dumps(plan,indent=2))
for p in (OLD/'code').iterdir():
    if p.is_file():shutil.copy2(p,R/'code'/p.name)
shutil.copy2(OLD/'diagnostic.cpp',R/'diagnostic.cpp')
shutil.copytree(OLD/'inputs/C4_update_1',R/'inputs/C4_update_1')
jobs=list(csv.DictReader((OLD/'inputs/jobs.csv').open()))
jobs=[r for r in jobs if r['key']=='C4_update_1' and r['job_id'] in plan['source_jobs']]
assert len(jobs)==6
with (R/'inputs/jobs.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(jobs[0]));w.writeheader();w.writerows(jobs)
for n in ['FINAL_DECISION.json','科学裁决_zh.md','PACKAGE_VERIFY.json','PUBLICATION.json']:
    shutil.copy2(OLD/n,R/'lineage'/('prior_'+n))
for n in ['HISTORICAL_NATIVE_PAIR_REFERENCE.csv','HISTORICAL_NATIVE_RECEIVER_REFERENCE.csv','PAIR_COMPARISONS.csv']:
    p=OLD/'analysis'/n
    if p.exists():shutil.copy2(p,R/'lineage'/n)
script='''import pathlib,json,base64,subprocess
g=pathlib.Path('/home/zyc/ros2_ws/src/GADEN')
c=g/'gaden_common/third_party/gaden_core'
files=[g/'gaden_player/src/simulation_player.cpp',g/'simulated_gas_sensor/src/fake_gas_sensor.cpp',g/'simulated_gas_sensor/src/fake_gas_sensor.h']
files += [c/'src'/n for n in ['Simulation.cpp','PlaybackSimulation.cpp','RunningSimulation.cpp','Scene.cpp','Environment.cpp']]
files += [c/'include/gaden'/n for n in ['datatypes/SimulationMetadata.hpp','datatypes/Filament.hpp','internal/compression.hpp','internal/Serialization.hpp','Environment.hpp','Simulation.hpp','core/Vectors.hpp']]
out={str(p.relative_to(g)):base64.b64encode(p.read_bytes()).decode() for p in files if p.exists()}
out['_identity']={str(p):subprocess.run(['git','-C',str(p),'rev-parse','HEAD'],capture_output=True,text=True).stdout.strip() for p in [g,c]}
print(json.dumps(out))
'''
payload=json.loads(run(['ssh','-o','BatchMode=yes','zyc@192.168.111.128','python3','-'], 'snapshot_local_gaden_sources',script.encode()))
identity=payload.pop('_identity')
for name,b64 in payload.items():
    p=R/'source'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(b64))
(R/'lineage/GADEN_SOURCE_IDENTITY.json').write_text(json.dumps(dict(revisions=identity,warning='Current source snapshot; runtime equivalence must be checked against recorded responses, not assumed'),indent=2))
(R/'lineage/INITIAL_SHA256.json').write_text(json.dumps({str(p.relative_to(R)):sha(p) for d in ['code','inputs','source'] for p in (R/d).rglob('*') if p.is_file()},indent=2))
print('Frozen final audit; six source calls only; GADEN source snapshot captured.')

"""Bounded native whole-population Monte Carlo necessity experiment."""
from pathlib import Path
import csv,hashlib,json,subprocess,resource,time,shlex,shutil,datetime,os
R=Path(__file__).resolve().parent;plan=json.loads((R/'FROZEN_PLAN.json').read_text())
origin=datetime.datetime.fromisoformat(plan['created_utc']).timestamp()
if (R/'RUN_STARTED.json').exists():
    commands=json.loads((R/'COMMANDS.json').read_text())
    assert all(x['source_call_starts']==0 for x in commands),'No automatic scientific rerun'
    (R/'lineage/ZERO_FORWARD_BUILD_RECOVERY.json').write_text(json.dumps(dict(preserved_original_origin=True,previous_source_starts=0,reason='Missing copied DDA include directory; copy original dependency, no kernel change'),indent=2))
else:
    (R/'RUN_STARTED.json').write_text(json.dumps(dict(epoch=time.time(),host='VM',new_worlds=0,new_ROS=0)));commands=[]
starts=0;complete=0
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(cmd,tag,n=0):
    global starts,complete
    assert shutil.disk_usage('/').free>=plan['minimum_VM_free_GiB']*1024**3,'VM reserve guard'
    assert starts+n<=plan['maximum_source_call_starts'];starts+=n
    before=resource.getrusage(resource.RUSAGE_CHILDREN);t=time.monotonic()
    with (R/'logs'/f'{tag}.stdout').open('w') as f,(R/'logs'/f'{tag}.stderr').open('w') as e:q=subprocess.run(list(map(str,cmd)),stdout=f,stderr=e,env=env)
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    commands.append(dict(command=list(map(str,cmd)),tag=tag,exit_code=q.returncode,wall_s=time.monotonic()-t,cpu_s=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,source_call_starts=n))
    (R/'COMMANDS.json').write_text(json.dumps(commands,indent=2))
    assert q.returncode==0,tag
    complete+=n
    progress=dict(started_source_calls=starts,completed_source_calls=complete,child_cpu_s=sum(x['cpu_s'] for x in commands),elapsed_wall_s=time.time()-origin)
    (R/'PROGRESS.json').write_text(json.dumps(progress,indent=2))
    assert progress['child_cpu_s']<plan['maximum_child_cpu_s'],'CPU guard'
    assert progress['elapsed_wall_s']<plan['maximum_host_wall_s'],'Wall guard'
    return progress
cflags=shlex.split(subprocess.check_output(['pkg-config','--cflags','opencv4'],text=True))
run(['g++','-std=c++20','-O2','-g0',*cflags,'-I'+str(R/'code'),'-I'+str(R/'code/dda'),R/'code/export_states.cpp',R/'code/native_math.cpp','-o','/tmp/aimmd_export_states'],'build_exporter_'+str(len(commands)+1))
run(['/tmp/aimmd_export_states',R/'inputs/NEW_PREDICTION_STATES.csv',R],'export_native_constructor_states')
jobs=list(csv.DictReader((R/'inputs/NEW_PREDICTION_STATES.csv').open()));states={(x['key'],x['seed']):x for x in csv.DictReader((R/'inputs/CONSTRUCTOR_STATES.csv').open())}
for x in jobs:
    state=states[(x['key'],x['seed'])];x['rng_before']=state['rng_before'];x['gaussian_before']=state['gaussian_before']
with (R/'inputs/jobs.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(jobs[0]));w.writeheader();w.writerows(jobs)
exe=Path('/tmp/c4h17_build/timed')
(R/'lineage/EXECUTABLE_IDENTITY.json').write_text(json.dumps(dict(native_timed_sha256=sha(exe),exporter_sha256=sha(Path('/tmp/aimmd_export_states'))),indent=2))
parity=json.loads((R/'lineage/PRIOR_TARGET_MAPS.json').read_text())
for c in plan['cases']:
    key=c['key'];out=R/'results/parity'/key
    run([exe,R/'inputs'/key,R/'inputs/PARITY_JOBS.csv',out,'2026101701','1800','200'],'parity_'+key,2)
    for a in [x for x in parity if x['key']==key]:
        assert sha(out/a['job_id']/'raw.f32')==a['raw_sha256'] and sha(out/a['job_id']/'blur.f32')==a['blur_sha256']
(R/'lineage/FOUR_SOURCE_PARITY.json').write_text(json.dumps(dict(status='PASS_EXACT_RAW_AND_BLURRED_MAP_PARITY',calls=4,unchanged_movement_kernel=True),indent=2))
for i,x in enumerate(jobs):
    dest=R/'results'/x['phase']/x['key']/x['job_id']/x['replicate']
    p=run([exe,R/'inputs'/x['key'],R/'inputs/jobs.csv',dest,x['seed'],'1800','200'],f'sim_{i:04d}',1)
    receipt=json.loads((dest/'COMPLETE.json').read_text());assert receipt['simulations']==1
    if i%16==0 or i==len(jobs)-1:print(x['phase'],x['key'],x['job_id'],x['replicate'],'complete',complete,'cpu',round(p['child_cpu_s'],2),flush=True)
assert starts==complete==900
(R/'PRIMARY_COMPLETE.json').write_text(json.dumps(dict(status='PASS_FROZEN_900_SOURCE_STARTS_COMPLETE',forward_calls=starts,primary=896,parity=4,child_cpu_s=sum(x['cpu_s'] for x in commands)),indent=2))
print('PRIMARY_COMPLETE',complete,flush=True)

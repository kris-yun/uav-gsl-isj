"""Run once on Linux. This is an offline, frozen source-pair diagnostic."""
from pathlib import Path
import argparse,csv,hashlib,json,os,resource,shutil,subprocess,time,datetime
R=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--build',type=Path,default=Path('/tmp/c4h17_build'));parser.add_argument('--build-attempt',default='1');parser.add_argument('--resume',action='store_true');args=parser.parse_args()
plan=json.loads((R/'FROZEN_PLAN.json').read_text());jobs=list(csv.DictReader((R/'inputs/jobs.csv').open()))
commands=[];calls=0
if (R/'EXECUTION.json').exists():commands=json.loads((R/'EXECUTION.json').read_text())
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
start=time.monotonic()
origin_file=R/'RUN_ORIGIN.json'
if origin_file.exists():
    frozen_start=json.loads(origin_file.read_text())['epoch_seconds']
else:
    # A fresh portable replay gets its own run origin. A resumed historical
    # run conservatively retains the original freeze time; never reset it.
    historical=bool(commands)
    frozen_start=datetime.datetime.fromisoformat(plan['timestamp']).timestamp() if historical else time.time()
    origin_file.write_text(json.dumps(dict(epoch_seconds=frozen_start,historical_origin_from_scientific_freeze=historical)))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def persist(): (R/'EXECUTION.json').write_text(json.dumps(commands,indent=2))
def execute(cmd,tag):
    assert shutil.disk_usage('/').free>plan['minimum_VM_free_GiB']*1024**3,'VM free-space floor'
    before=resource.getrusage(resource.RUSAGE_CHILDREN);t=time.monotonic()
    with (R/'logs'/(tag+'.stdout')).open('w') as out,(R/'logs'/(tag+'.stderr')).open('w') as err:
        q=subprocess.run(cmd,env=env,stdout=out,stderr=err)
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    commands.append(dict(command=list(map(str,cmd)),tag=tag,exit_code=q.returncode,wall_s=time.monotonic()-t,
                         cpu_s=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime))
    persist();print(tag,'exit',q.returncode,'cpu',commands[-1]['cpu_s'],flush=True)
    assert q.returncode==0,tag
    assert sum(a.get('charged_cpu_s',a['cpu_s']) for a in commands)<plan['maximum_child_cpu_s'],'CPU cap'
    assert time.time()-frozen_start<5400,'90 minute host guard from original freeze'

execute(['cmake','-S',str(R/'code'),'-B',str(args.build)],'configure_'+args.build_attempt)
execute(['cmake','--build',str(args.build),'--target','timed','-j2'],'build_'+args.build_attempt)
source_manifest={str(p.relative_to(R)):sha(p) for p in (R/'code').rglob('*') if p.is_file()}
source_manifest['diagnostic.cpp']=sha(R/'diagnostic.cpp')
(R/'lineage/BUILD_SHA256.json').write_text(json.dumps(dict(files=source_manifest,executable_sha256=sha(args.build/'timed')),indent=2))
parity=json.loads((R/'lineage/ADAPTIVE_PARITY.json').read_text()) if args.resume else []
def output_size():
    # No repeated global rglob/stat traversal through VMware HGFS.
    # Map lengths are fixed by grid size and frozen record horizon. Only
    # compressed trace lengths and each process's two small files need stat.
    total=0
    for cond in plan['conditions']:
        for case in plan['cases']:
            key=case['key'];n=case['metadata']['width']*case['metadata']['height'];T=cond['record_steps']
            for seed in plan['prediction_states']:
                d=R/'results'/key/cond['id']/str(seed)
                if not (d/'COMPLETE.json').exists():continue
                total+=(d/'scores.csv').stat().st_size+(d/'COMPLETE.json').stat().st_size
                selected=[a for a in jobs if a['key']==key and int(a['seed'])==seed]
                for job in selected:total+=8*n*(1+T//100+T//200)+(d/job['job_id']/'trace.u32.gz').stat().st_size
    return total
order=['C4_update_1','C4_update_0','C3_update_2']
for condition in plan['conditions']:
    for key in order:
        for seed in plan['prediction_states']:
            out=R/'results'/key/condition['id']/str(seed)
            subset=[a for a in jobs if a['key']==key and int(a['seed'])==seed]
            assert calls+len(subset)<=plan['maximum_forward_calls']
            if args.resume and (out/'COMPLETE.json').exists():
                completed=list(csv.DictReader((out/'scores.csv').open()))
                assert [a['job_id'] for a in completed]==[a['job_id'] for a in subset]
                assert len(completed)==json.loads((out/'COMPLETE.json').read_text())['simulations']
                calls+=len(completed)
                continue
            execute([str(args.build/'timed'),str(R/'inputs'/key),str(R/'inputs/jobs.csv'),str(out),str(seed),str(condition['warmup_steps']),str(condition['record_steps'])],f"{key}_{condition['id']}_{seed}")
            actual=list(csv.DictReader((out/'scores.csv').open()));assert len(actual)==len(subset)
            calls+=len(actual)
            if condition['id']=='adaptive_R20':
                old={a['job_id']:a for a in subset}
                for row in actual:
                    ident=row['job_id'];a=old[ident];exp=R/'inputs/expected'/key/str(seed)
                    assert (out/ident/'raw.f32').read_bytes()==(exp/(ident+'_unblurred.f32')).read_bytes(),(key,seed,ident,'raw parity')
                    assert (out/ident/'blur.f32').read_bytes()==(exp/(ident+'.f32')).read_bytes(),(key,seed,ident,'blur parity')
                    assert abs(float(row['source_logscore'])-float(a['old_logscore']))<1e-14
                    for newcol,oldcol in [('particle_moves','old_moves'),('emitted','old_releases'),('rng_after','old_rng_after'),('gaussian_after','old_gaussian_after')]:assert row[newcol]==a[oldcol],(key,seed,ident,newcol)
                parity.append(dict(key=key,seed=seed,sources=len(actual),raw_blur_rng_moves_scores_identical=True))
                (R/'lineage/ADAPTIVE_PARITY.json').write_text(json.dumps(parity,indent=2))
            if condition['id']=='adaptive_R20' and key==order[-1] and seed==plan['prediction_states'][-1]:
                assert sum(a['sources'] for a in parity)==len(jobs)
                (R/'lineage/QUALIFICATION_PASS.json').write_text(json.dumps(dict(status='PASS_ALL_156_TARGETED_SOURCES_MATCH_PREVIOUS',calls=calls)))
            if condition['id']!='adaptive_R20':assert (R/'lineage/QUALIFICATION_PASS.json').exists()
            (R/'PROGRESS.json').write_text(json.dumps(dict(completed_calls=calls,maximum_calls=plan['maximum_forward_calls'],last_key=key,last_condition=condition['id'],last_state=seed,driver_invocation_wall_s=time.monotonic()-start,host_wall_s_since_run_origin=time.time()-frozen_start),indent=2))
    size=output_size()
    assert size<plan['maximum_output_MiB']*1024**2,'Output cap'
assert calls==plan['maximum_forward_calls']
(R/'CONTRASTS_COMPLETE.json').write_text(json.dumps(dict(status='PASS_COMPLETE_FROZEN_SCHEDULE',forward_calls=calls,host_wall_s_since_freeze=time.time()-frozen_start,measured_logged_child_cpu_s=sum(a['cpu_s'] for a in commands),charged_child_cpu_s=sum(a.get('charged_cpu_s',a['cpu_s']) for a in commands),output_bytes=size,new_ROS_episodes=0,new_gas_worlds=0),indent=2))
print((R/'CONTRASTS_COMPLETE.json').read_text(),flush=True)

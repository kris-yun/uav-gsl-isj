"""Run once on Linux. This is an offline, frozen source-pair diagnostic."""
from pathlib import Path
import argparse,csv,hashlib,json,os,resource,shutil,subprocess,time
R=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--build',type=Path,default=Path('/tmp/c4h17_build'));parser.add_argument('--build-attempt',default='1');args=parser.parse_args()
plan=json.loads((R/'FROZEN_PLAN.json').read_text());jobs=list(csv.DictReader((R/'inputs/jobs.csv').open()))
commands=[];calls=0
if (R/'EXECUTION.json').exists():commands=json.loads((R/'EXECUTION.json').read_text())
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
start=time.monotonic()
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
    assert sum(a['cpu_s'] for a in commands)<plan['maximum_child_cpu_s'],'CPU cap'
    assert time.monotonic()-start<5400,'90 minute host guard'

execute(['cmake','-S',str(R/'code'),'-B',str(args.build)],'configure_'+args.build_attempt)
execute(['cmake','--build',str(args.build),'--target','timed','-j2'],'build_'+args.build_attempt)
source_manifest={str(p.relative_to(R)):sha(p) for p in (R/'code').rglob('*') if p.is_file()}
source_manifest['diagnostic.cpp']=sha(R/'diagnostic.cpp')
(R/'lineage/BUILD_SHA256.json').write_text(json.dumps(dict(files=source_manifest,executable_sha256=sha(args.build/'timed')),indent=2))
parity=[]
order=['C4_update_1','C4_update_0','C3_update_2']
for condition in plan['conditions']:
    for key in order:
        for seed in plan['prediction_states']:
            out=R/'results'/key/condition['id']/str(seed)
            subset=[a for a in jobs if a['key']==key and int(a['seed'])==seed]
            assert calls+len(subset)<=plan['maximum_forward_calls']
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
            (R/'PROGRESS.json').write_text(json.dumps(dict(completed_calls=calls,maximum_calls=plan['maximum_forward_calls'],last_key=key,last_condition=condition['id'],last_state=seed,wall_s=time.monotonic()-start),indent=2))
    size=sum(p.stat().st_size for p in (R/'results').rglob('*') if p.is_file())
    assert size<plan['maximum_output_MiB']*1024**2,'Output cap'
assert calls==plan['maximum_forward_calls']
(R/'CONTRASTS_COMPLETE.json').write_text(json.dumps(dict(status='PASS_COMPLETE_FROZEN_SCHEDULE',forward_calls=calls,host_wall_s=time.monotonic()-start,cpu_s=sum(a['cpu_s'] for a in commands),output_bytes=size,new_ROS_episodes=0,new_gas_worlds=0),indent=2))
print((R/'CONTRASTS_COMPLETE.json').read_text(),flush=True)

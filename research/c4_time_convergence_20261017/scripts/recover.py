"""One documented driver-interrupted call; no completed source is re-run."""
from pathlib import Path
import csv,hashlib,json,os,resource,shutil,subprocess,time
R=Path(__file__).resolve().parents[1]
key='C4_update_1';cond='W360_R20';seed=2026101702
old=R/'lineage/INTERRUPTED_C4u1_W360_state2'
assert old.is_dir() and not (old/'COMPLETE.json').exists()
alljobs=list(csv.DictReader((R/'inputs/jobs.csv').open()))
expected=[a for a in alljobs if a['key']==key and int(a['seed'])==seed]
with (old/'scores.csv').open() as f:reader=csv.DictReader(f);cols=reader.fieldnames;done=list(reader)
assert len(done)==27 and len(expected)==28
ids={a['job_id'] for a in done};pending=[a for a in expected if a['job_id'] not in ids]
assert len(pending)==1 and pending[0]['job_id']=='fine_competitor'
jobfile=R/'lineage/ONE_INTERRUPTED_CALL_JOB.csv'
with jobfile.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(pending[0]));w.writeheader();w.writerows(pending)
recovery=R/'lineage/ONE_CALL_RECOVERY'
cmd=['/tmp/c4h17_build/timed',str(R/'inputs'/key),str(jobfile),str(recovery),str(seed),'1800','200']
before=resource.getrusage(resource.RUSAGE_CHILDREN);start=time.monotonic()
with (R/'logs/recover_one.stdout').open('w') as out,(R/'logs/recover_one.stderr').open('w') as err:q=subprocess.run(cmd,stdout=out,stderr=err)
after=resource.getrusage(resource.RUSAGE_CHILDREN)
commands=json.loads((R/'EXECUTION.json').read_text())
commands.append(dict(command=['python3',str(R/'lineage/run_v1_repeated_hgfs_scan.py')],tag='driver_SIGINT_during_next_call',exit_code=1,cpu_s=0,charged_cpu_s=30,
                     cpu_note='30-second conservative accounting charge for interrupted process; exact process CPU unavailable. 27 completed source CPU readings preserved in CSV.',wall_s=None))
commands.append(dict(command=cmd,tag='same_state_one_source_recovery',exit_code=q.returncode,cpu_s=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,wall_s=time.monotonic()-start))
(R/'EXECUTION.json').write_text(json.dumps(commands,indent=2));assert q.returncode==0
with (recovery/'scores.csv').open() as f:new=list(csv.DictReader(f))
assert len(new)==1 and new[0]['job_id']==pending[0]['job_id']
dest=R/'results'/key/cond/str(seed);dest.mkdir(exist_ok=False)
hashes=[]
for row in done+new:
    src=(old if row['job_id'] in ids else recovery)/row['job_id']
    shutil.copytree(src,dest/row['job_id'])
    for p in src.iterdir():
        if p.is_file():
            a=hashlib.sha256(p.read_bytes()).hexdigest();b=hashlib.sha256((dest/row['job_id']/p.name).read_bytes()).hexdigest();assert a==b
            hashes.append(dict(job_id=row['job_id'],file=p.name,sha256=a))
with (dest/'scores.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(done+new)
(dest/'COMPLETE.json').write_text(json.dumps(dict(simulations=28,seed=seed,warmup_requested_steps=1800,record_steps=200,recovery='27 already-completed sources retained; 1 identical-state incomplete source recovered')))
(R/'lineage/TECHNICAL_RECOVERY.json').write_text(json.dumps(dict(status='PASS_NO_COMPLETED_SOURCE_RERUN',original_frozen_plan_unchanged=True,
      planned_successful_calls=1092,actual_maximum_call_starts=1093,incomplete_driver_interrupted_calls=1,completed_sources_reused=27,
      replacement_source='fine_competitor',replacement_state=seed,conditions_unchanged=True,physical_kernels_unchanged=True,
      evidence_hashes=hashes,reason='Driver interruption raced with start of the next native process. Preserve all original partial files and replace only the final unfinished source. Self-imposed call accounting includes the one failed start; no scientific schedule, source or RNG changes.'),indent=2))
print('PASS_ONE_CALL_RECOVERY_AND_27_COMPLETED_SOURCES_REUSED',flush=True)

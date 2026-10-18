from pathlib import Path
import csv,json,subprocess,time,hashlib,shutil,resource
R=Path(__file__).resolve().parents[1]
plan=json.loads((R/'FROZEN_PLAN.json').read_text())
assert not (R/'results/SIX_COMPLETE.json').exists()
assert shutil.disk_usage('/').free>=5*1024**3
exe=Path('/tmp/c4h17_build/timed')
(R/'lineage/SIX_EXECUTABLE_SHA256.json').write_text(json.dumps(dict(path=str(exe),sha256=hashlib.sha256(exe.read_bytes()).hexdigest())))
logs=[];count=0
for state in plan['states']:
    out=R/'results/six'/str(state)
    cmd=[str(exe),str(R/'inputs/C4_update_1'),str(R/'inputs/jobs.csv'),str(out),str(state),'0','3600']
    t=time.monotonic();before=resource.getrusage(resource.RUSAGE_CHILDREN)
    with (R/'logs'/f'six_{state}.stdout').open('w') as f,(R/'logs'/f'six_{state}.stderr').open('w') as e:
        q=subprocess.run(cmd,stdout=f,stderr=e)
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    logs.append(dict(command=cmd,exit_code=q.returncode,wall_s=time.monotonic()-t,cpu_s=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime))
    (R/'logs/SIX_COMMANDS.json').write_text(json.dumps(logs,indent=2))
    assert q.returncode==0
    rows=list(csv.DictReader((out/'scores.csv').open()));assert len(rows)==2
    count+=len(rows);assert count<=6
    print(state,'complete',len(rows),flush=True)
assert count==6
(R/'results/SIX_COMPLETE.json').write_text(json.dumps(dict(completed_calls=count,additional_calls_authorized=0,commands=logs),indent=2))

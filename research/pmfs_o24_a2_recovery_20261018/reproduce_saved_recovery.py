"""Portable saved-data checks; never starts ROS, worlds or forward simulation."""
from pathlib import Path
import csv,hashlib,json,math,subprocess,sys,time
R=Path(__file__).resolve().parent
manifest=json.loads((R/'MANIFEST_SHA256.json').read_text(encoding='utf-8'))
for x in manifest['files']:assert hashlib.sha256((R/x['path']).read_bytes()).hexdigest()==x['sha256'],x['path']
names=['O24_EPISODES.csv','O24_SOURCE_UPDATE_METRICS.csv','NATIVE_REPLAY_PARITY.csv','O24_NATIVE_CPP_READOUT.csv','FORWARD_AND_RECORDING_COST.csv']
def read(p):return list(csv.DictReader(p.open(encoding='utf-8')))
expected={n:read(R/'analysis'/n)for n in names};original_rng=json.loads((R/'analysis/RNG_STREAM_REPLAY_RESULTS.json').read_text());commands=[];Q=R/'offline_qa';Q.mkdir(exist_ok=True)
for script in ['analyze.py','verify_readout_guest.py','validate_rng_guest.py','minimal_score_sample/replay_score.py','verify_recovery.py']:
 t=time.monotonic();q=subprocess.run([sys.executable,'-B',str(R/script)],cwd=R,capture_output=True);(Q/(Path(script).name+'.stdout')).write_bytes(q.stdout);(Q/(Path(script).name+'.stderr')).write_bytes(q.stderr);commands.append(dict(script=script,exit_code=q.returncode,wall_s=time.monotonic()-t));assert q.returncode==0,(script,q.returncode)
checked=[]
for n,old in expected.items():
 new=read(R/'analysis'/n);assert len(new)==len(old);err=0.
 for a,b in zip(old,new):
  assert set(a)==set(b)
  for k in a:
   if a[k]==b[k]:continue
   try:
    x,y=float(a[k]),float(b[k]);assert math.isclose(x,y,rel_tol=1e-11,abs_tol=1e-11),(n,k,x,y);err=max(err,abs(x-y))
   except ValueError:assert a[k]==b[k],(n,k,a[k],b[k])
 checked.append(dict(file=n,rows=len(old),max_numeric_abs_difference=err))
new_rng=json.loads((R/'analysis/RNG_STREAM_REPLAY_RESULTS.json').read_text());assert original_rng['status']==new_rng['status']
for a,b in zip(original_rng['rows'],new_rng['rows']):assert {k:v for k,v in a.items()if k!='wall_s'}=={k:v for k,v in b.items()if k!='wall_s'}
out=dict(status='PASS_ARCHIVE_EXTRACTION_OFFLINE_RECOVERY_REPRODUCTION',payload_files=len(manifest['files']),commands=commands,numeric_comparisons=checked,RNG_candidate_records=sum(x['candidate_records']for x in new_rng['rows']),new_ROS_goals=0,new_forward_calls=0,new_worlds=0,AIMMD=0)
(R/'OFFLINE_REPRODUCTION_QA.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,ensure_ascii=False))

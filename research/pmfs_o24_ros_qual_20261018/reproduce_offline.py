"""Verify saved evidence only. No ROS, new world, or forward propagation."""
from pathlib import Path
import csv,hashlib,json,math,subprocess,sys,time
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((R/'MANIFEST_SHA256.json').read_text(encoding='utf-8'))
entries=manifest['files']
for row in entries:assert sha(R/row['path'])==row['sha256'],('original payload SHA mismatch',row['path'])
csvnames=['O24_EPISODES.csv','O24_SOURCE_UPDATE_METRICS.csv','NATIVE_REPLAY_PARITY.csv','O24_NATIVE_CPP_READOUT.csv','O24_P24_SEPARATE_RESULTS.csv','FORWARD_AND_RECORDING_COST.csv']
def read(p):return list(csv.DictReader(p.open(encoding='utf-8')))
expected={name:read(R/'analysis'/name)for name in csvnames}
original_rng=json.loads((R/'analysis/RNG_STREAM_REPLAY_RESULTS.json').read_text())
commands=[];Q=R/'offline_qa';Q.mkdir(exist_ok=True)
for script in ['analyze.py','verify_readout_guest.py','validate_rng_guest.py','final_checks.py']:
 t=time.monotonic();q=subprocess.run([sys.executable,str(R/script)],cwd=R,capture_output=True)
 (Q/(script+'.stdout')).write_bytes(q.stdout);(Q/(script+'.stderr')).write_bytes(q.stderr)
 commands.append(dict(script=script,exit_code=q.returncode,wall_s=time.monotonic()-t))
 assert q.returncode==0,('offline calculation failed',script,q.returncode)
comparisons=[]
for name,old in expected.items():
 new=read(R/'analysis'/name);assert len(old)==len(new),name
 maxdiff=0.
 for n,(a,b)in enumerate(zip(old,new)):
  assert set(a)==set(b),(name,n,'columns')
  for k in a:
   if a[k]==b[k]:continue
   try:
    x,y=float(a[k]),float(b[k]);assert math.isclose(x,y,rel_tol=1e-11,abs_tol=1e-11),(name,n,k,x,y)
    maxdiff=max(maxdiff,abs(x-y))
   except ValueError:assert a[k]==b[k],(name,n,k,a[k],b[k])
 comparisons.append(dict(file=name,rows=len(old),max_numeric_abs_difference=maxdiff,status='PASS_NUMERIC_1e_11'))
new_rng=json.loads((R/'analysis/RNG_STREAM_REPLAY_RESULTS.json').read_text())
assert new_rng['status']==original_rng['status']
for a,b in zip(original_rng['rows'],new_rng['rows']):
 assert {k:v for k,v in a.items()if k!='wall_s'}=={k:v for k,v in b.items()if k!='wall_s'}
gate=json.loads((R/'FINAL_QUALIFICATION_GATE.json').read_text())
assert gate['status']=='HOLD_ROS_ISOLATION_A2_R02_BUILD_AND_RNG_PASS_FOUR_RAW_EPISODES_RETAINED'
receipt=dict(status='PASS_OFFLINE_EVIDENCE_REPRODUCTION_RUNTIME_ISOLATION_HOLD_RETAINED',verified_original_payload_files=len(entries),commands=commands,numeric_comparisons=comparisons,RNG_candidate_records=sum(x['candidate_records']for x in new_rng['rows']),new_ROS_goals=0,new_forward_propagation_calls=0,new_worlds=0,AIMMD=0,scientific_verdict=gate['status'],scope='This QA reproduces saved evidence and preserves the historical domain225 qualification HOLD; it does not qualify a clean robot episode.')
(R/'OFFLINE_REPRODUCTION_QA.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False))

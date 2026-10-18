"""Stdlib-only integrity and recorded posterior replay; never starts ROS or a simulator."""
from pathlib import Path
import argparse,csv,hashlib,json,math
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--verify-only',action='store_true');p.add_argument('--out',type=Path);a=p.parse_args()
if (R/'MANIFEST_SHA256.json').exists():
 m=json.loads((R/'MANIFEST_SHA256.json').read_text(encoding='utf-8'))
 for x in m['files']:
  f=R/x['path'];assert f.stat().st_size==x['bytes'];assert hashlib.sha256(f.read_bytes()).hexdigest()==x['sha256'],x['path']
 print(json.dumps(dict(status='PASS_MANIFEST',files=len(m['files']))))
if a.verify_only:raise SystemExit(0)
assert a.out,'Specify a new --out directory';a.out.mkdir(parents=True,exist_ok=False)
results=[]
for role in ['PF24_A2_T02','PF24_B2_Q01']:
 states={}
 with (R/'cases'/role/'runtime/native_posterior_updates.csv').open(encoding='utf-8-sig')as f:
  for x in csv.DictReader(f):states.setdefault(int(x['update']),[]).append(x)
 for update,rs in sorted(states.items()):
  q=[float(r['source_probability'])for r in rs];mass=sum(q);assert abs(mass-1)<1e-9 and all(math.isfinite(v)and v>=0 for v in q)
  ex=sum(v*float(r['x_m'])for v,r in zip(q,rs));ey=sum(v*float(r['y_m'])for v,r in zip(q,rs))
  variance=sum(v*((float(r['x_m'])-ex)**2+(float(r['y_m'])-ey)**2)for v,r in zip(q,rs))
  error=max(abs(float(r['hit_confidence'])-(1-math.exp(-float(r['hit_omega'])**2)))for r in rs)
  assert error<2e-14
  results.append(dict(role=role,update=update,mass=mass,variance_m2=variance,max_Eq6_error=error))
with (a.out/'REPLAY.json').open('w')as f:json.dump(dict(status='PASS_RECORDED_POSTERIOR_AND_EQ6',rows=results,new_ROS=0,new_forward_calls=0),f,indent=2)
print(json.dumps(dict(status='PASS_RECORDED_POSTERIOR_AND_EQ6',updates=len(results),new_ROS=0)))

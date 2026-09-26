#!/usr/bin/env python3
import argparse, concurrent.futures, csv, hashlib, json, os, subprocess, time
from pathlib import Path
import numpy as np
R=Path('/home/zyc/marked_encounter_pmfs_d0_20260927')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
ap=argparse.ArgumentParser();ap.add_argument('--repeat',action='store_true');a=ap.parse_args()
assert json.loads((R/'NATIVE_PARITY.json').read_text())['pass']
envs=json.loads((R/'inputs/environment_manifest.json').read_text())
out=R/('forward_repeat' if a.repeat else 'forward');assert not out.exists();out.mkdir()
log=out/'run.log'; start=time.monotonic()
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
tasks=[(e,s,k,r) for e in range(3) for s in range(6) for k in range(11) for r in range(1,9)]
def run(t):
    e,s,k,r=t;prefix=out/f'env_{e}'/f'source_{s}'/f'state_{k}_replica_{r}'
    cmd=[str(R/'build/marked_forward'),str(R/'inputs'/f'env_{e}'),str(s),str(k),str(r),str(prefix)]
    p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    if p.returncode:raise RuntimeError((t,p.returncode,p.stdout))
    return t,p.stdout
with log.open('w') as f,concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    for n,(t,output) in enumerate(executor.map(run,tasks),1):
        f.write(output);f.flush()
        if n%24==0: print('FORWARD_PROGRESS',n,'/',len(tasks),'elapsed_s',round(time.monotonic()-start,1),flush=True)
rows=[]; per_run=[]
for env in envs:
    e=env['environment_index'];inp=R/'inputs'/f'env_{e}'
    sources=list(csv.DictReader((inp/'sources.csv').open()));probes=list(csv.DictReader((inp/'probes.csv').open()))
    n=env['metadata']['width']*env['metadata']['height'];free=np.fromfile(inp/'occupancy.u8',np.uint8)==1
    for s,sr in enumerate(sources):
        ps=[];us=[]
        for k in range(11):
          for r in range(1,9):
            prefix=out/f'env_{e}'/f'source_{s}'/f'state_{k}_replica_{r}'
            maps={key:np.fromfile(str(prefix)+'.'+key+'.f32','<f4') for key in ('p','u','rawp','rawu')}
            assert all(v.size==n and np.isfinite(v).all() and (v>=0).all() for v in maps.values())
            assert (maps['p'][free]<=1).all() and (maps['rawp'][free]<=1).all()
            assert (maps['rawu'][free]>=maps['rawp'][free]).all()
            assert (maps['u'][free]+1e-5>=maps['p'][free]).all()
            ps.append(maps['p'].astype(float));us.append(maps['u'].astype(float))
            per_run.append({'environment_index':e,'source_index':s,'state':k,'replica_seed':r,'moment_hashes':{key:sha(Path(str(prefix)+'.'+key+'.f32')) for key in maps}})
        p=np.mean(ps,axis=0);u=np.mean(us,axis=0);mu=np.divide(u,p,out=np.zeros_like(u),where=p>0)
        for pr in probes:
            ix=int(pr['cell_index'])
            rows.append(dict(environment_index=e,house=env['house'],wind=env['wind'],source_index=s,source_id=sr['source_id'],probe_rank=int(pr['probe_rank']),presence_prob=p[ix],multiplicity_mean_unconditional=u[ix],multiplicity_mean_conditional=mu[ix],state_count=11,replica_count=8,total_forward_count=88))
with (out/'candidate_mark_bank.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader()
    for row in rows:w.writerow({k:format(v,'.17g') if isinstance(v,float) else v for k,v in row.items()})
dump(out/'FORWARD_MANIFEST.json',{'forward_count':len(per_run),'environment_count':3,'source_units':18,'rows':per_run,'candidate_bank_sha256':sha(out/'candidate_mark_bank.csv'),'worker_count':4,'all_checks_passed':True})
if a.repeat:
    first=R/'forward'
    assert sha(first/'candidate_mark_bank.csv')==sha(out/'candidate_mark_bank.csv')
    assert sha(first/'FORWARD_MANIFEST.json')==sha(out/'FORWARD_MANIFEST.json')
    dump(R/'BANK_REPEAT.json',{'pass':True,'forward_realizations_each_run':1584,'full_float_maps_compared':6336,'candidate_bank_byte_identical':True,'forward_manifest_byte_identical':True,'candidate_bank_sha256':sha(out/'candidate_mark_bank.csv')})
print('MARKED_BANK_COMPLETE',len(per_run),sha(out/'candidate_mark_bank.csv'),flush=True)

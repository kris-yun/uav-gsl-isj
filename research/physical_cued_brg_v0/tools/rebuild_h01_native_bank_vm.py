"""User-authorized H01-only reconstruction; never reads target gas."""
import concurrent.futures,csv,hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
ROOT=Path('/home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927');sys.path.insert(0,str(ROOT))
from pmfs_brg.bank import TemplateBank
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    out=ROOT/'h01_native_rebuild';out.mkdir(exist_ok=False);inputs=out/'inputs';inputs.mkdir()
    cache=ROOT/'full_support';old=cache/'inputs/env_0';legal=ROOT/'legal_support_v2/env_0_occupancy.u8'
    m=json.loads((old/'meta.json').read_text());cells=np.flatnonzero(np.fromfile(legal,np.uint8)==1);assert len(cells)==596
    for n in ['meta.json','meta.csv']:shutil.copyfile(old/n,inputs/n)
    shutil.copyfile(legal,inputs/'occupancy.u8')
    xy=np.stack([m['origin_x']+(cells%m['width']+.5)*m['resolution'],m['origin_y']+(cells//m['width']+.5)*m['resolution']],1)
    ids=[f'pmfs_{int(c)%m["width"]}_{int(c)//m["width"]}' for c in cells]
    with (inputs/'sources.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['source_index','source_id','x','y','z','pair_id']);w.writerows((i,s,*v,.2,'') for i,(s,v) in enumerate(zip(ids,xy)))
    winds=[];q=np.c_[xy,np.full(len(cells),.2)]
    for k in range(11):
        raw=Path('/mnt/hgfs/workspace/GADEN_files/scenarios/House01/wind_simulations/1,3-2,4_fast')/f'1,3-2,4_fast_{k}.csv'
        if not raw.exists():raw=Path('/mnt/hgfs/workspace/GADEN_files/scenarios/House01/House01/wind_simulations/1,3-2,4_fast')/f'1,3-2,4_fast_{k}.csv'
        a=np.loadtxt(raw,delimiter=',',skiprows=1);pos=a[:,3:6];d,ii=cKDTree(pos).query(q,k=2);near=ii[:,0].copy()
        for j in np.flatnonzero(np.abs(d[:,1]-d[:,0])<=1e-12):near[j]=int(np.argmin(np.sum((pos-q[j])**2,axis=1)))
        uv=a[near,:2].astype(np.float32);p=inputs/f'wind_{k}.csv'
        with p.open('w',newline='') as f:
            w=csv.writer(f);w.writerow(['cell_index','u','v']);w.writerows((int(c),repr(float(u)),repr(float(v))) for c,(u,v) in zip(cells,uv))
        winds.append({'state':k,'asset_sha256':sha(raw),'export_sha256':sha(p),'nearest_rows':near.tolist()})
    binary=cache/'full_support_forward';freeze={'authorization_sha256':sha(ROOT/'amendment/09_H01_REBUILD_AUTHORIZATION.md'),'candidate_count':596,'state_count':11,'seed_keys':list(range(1,9)),
        'new_plumes':0,'target_gas_read':False,'original_626_cache_preserved':True,'binary_sha256':sha(binary),'source_sha256':sha(cache/'full_support_forward.cpp'),
        'inputs':{p.name:sha(p) for p in inputs.iterdir()},'wind_provenance':winds,'workers':8}
    (out/'PRE_FORWARD_FREEZE.json').write_text(json.dumps(freeze,sort_keys=True,indent=2)+'\n')
    print('H01_REBUILD_PRE_FORWARD_FROZEN',sha(out/'PRE_FORWARD_FREEZE.json'),flush=True)
    os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    tmp=out/'temporary';tmp.mkdir();means=out/'source_means';means.mkdir();inventory=(out/'forward_hash_inventory.jsonl').open('a',buffering=1);begin=time.monotonic();n=m['width']*m['height']
    def run(si):
        p=np.zeros(n);u=np.zeros(n);rows=[]
        for k in range(11):
            for seed in range(1,9):
                prefix=tmp/f'source_{si}_state_{k}_seed_{seed}'
                proc=subprocess.run([str(binary),str(inputs),str(si),str(k),str(seed),str(prefix)],capture_output=True,text=True)
                if proc.returncode:raise RuntimeError((si,k,seed,proc.stdout,proc.stderr))
                row={'source':si,'source_id':ids[si],'state':k,'seed':seed,'hashes':{}}
                for kind in ['p','u','rawp','rawu']:
                    path=Path(str(prefix)+'.'+kind+'.f32');b=path.read_bytes();a=np.frombuffer(b,'<f4');assert len(a)==n and np.isfinite(a).all() and np.all(a>=0)
                    row['hashes'][kind]=hashlib.sha256(b).hexdigest()
                    if kind=='p':assert np.all(a[cells]<=1);p+=a
                    if kind=='rawu':u+=a
                    assert path.resolve().is_relative_to(tmp.resolve());path.unlink()
                rows.append(row)
        np.savez_compressed(means/f'{si}.npz',p=p/88,rawu=u/88)
        return rows
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for done,rows in enumerate(pool.map(run,range(596)),1):
            for row in rows:inventory.write(json.dumps(row,sort_keys=True)+'\n')
            if done%8==0:print('H01_NATIVE_SOURCES',done,'/596 elapsed_s',round(time.monotonic()-begin,1),flush=True)
    inventory.close();pp=[];uu=[]
    for si in range(596):
        with np.load(means/f'{si}.npz') as a:pp.append(a['p']);uu.append(a['rawu'])
    meta={**m,'environment_id':'env_0_native_geometry_rebuilt','house':'House01','wind':'1,3-2,4_fast','height_m':.2,'footprint_x_m':.2,'footprint_y_m':.2,'unit':'area_averaged_cell_count_proxy','support_rule':'actual Native fine z0.20 / scale3 / fixed-start prune'}
    bank=TemplateBank(meta,ids,xy,cells,np.stack(pp),np.stack(uu));bank.save(out/'env_0_bank.npz')
    complete={'environment':0,'candidates':596,'forward_count':596*88,'bank_sha256':sha(out/'env_0_bank.npz'),'bank_id':bank.fingerprint,'freeze_sha256':sha(out/'PRE_FORWARD_FREEZE.json'),'inventory_sha256':sha(out/'forward_hash_inventory.jsonl'),'seconds':time.monotonic()-begin}
    (out/'BANK_COMPLETE.json').write_text(json.dumps(complete,indent=2)+'\n');print('H01_NATIVE_COMPLETE',json.dumps(complete),flush=True)
if __name__=='__main__':main()

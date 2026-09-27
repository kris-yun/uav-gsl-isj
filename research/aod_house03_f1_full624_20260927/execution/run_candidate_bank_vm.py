#!/usr/bin/env python3
"""Exactly the signed 54,912 candidate rows; restart skips verified completed rows."""
import concurrent.futures, csv, hashlib, json, os, shutil, subprocess, time
from pathlib import Path
import numpy as np

R=Path('/home/zyc/aod_house03_f1_full624_20260927')
P=R/'protocol';I=R/'inputs';O=R/'candidate_forward'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
KINDS=('p','u','rawp','rawu')

def dump(p,x):
    tmp=Path(str(p)+'.partial');tmp.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n');tmp.replace(p)

def main():
    assert json.loads((R/'BUILD_AND_ASSET_AUDIT.json').read_text())['passed']
    assert sha(P/'frozen/HOUSE03_FUTURE_PMFS_SEEDS_FULL624_54912.tsv')=='00bf64ab0d1ce55fda58303b11208019473313b97c4de11f7a2305d16143327d'
    rows=list(csv.DictReader((P/'frozen/HOUSE03_FUTURE_PMFS_SEEDS_FULL624_54912.tsv').open(),delimiter='\t'))
    assert len(rows)==54912
    meta=json.loads((I/'meta.json').read_text());n=meta['width']*meta['height']
    O.mkdir(exist_ok=True);start=time.monotonic();free=shutil.disk_usage(R).free
    needed=sum(1 for r in rows if not prefix(r).with_suffix('.done.json').exists())*n*4*4
    if free < needed+512*1024**2:
        dump(R/'BUDGET_HOLD.json',dict(decision='AOD_F1_HOLD_FULL624_BUDGET',free_bytes=free,remaining_map_bytes=needed,reserve_bytes=512*1024**2))
        raise RuntimeError('Full624 disk budget unavailable; no targets may be generated')
    dump(R/'CANDIDATE_EXECUTION_PREFLIGHT.json',dict(free_bytes=free,remaining_float_map_bytes=needed,approved_forward_count=54912,
        workers=4,threads_per_worker=1,host_cpus=os.cpu_count(),new_target_runs=0,started_unix=time.time()))
    os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    def run(row):
        pre=prefix(row);done=pre.with_suffix('.done.json')
        if done.exists():
            rec=json.loads(done.read_text())
            assert rec['requested_seed']==int(row['requested_seed'])
            for k,h in rec['hashes'].items(): assert sha(str(pre)+f'.{k}.f32')==h
            return rec
        # Partial products of an interrupted row are quarantined, never replaced.
        remnants=list(pre.parent.glob(pre.name+'.*')) if pre.parent.exists() else []
        if remnants:
            quarantine=R/'incomplete_rows'/f'{pre.parent.name}_{pre.name}_{time.time_ns()}'
            quarantine.mkdir(parents=True)
            for p in remnants: p.rename(quarantine/p.name)
        t=time.monotonic()
        command=[str(R/'build/marked_forward_full624'),str(I),row['source_index'],row['wind_state'],row['requested_seed'],str(pre)]
        proc=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        if proc.returncode: raise RuntimeError((row,proc.returncode,proc.stdout))
        maps={k:np.fromfile(str(pre)+f'.{k}.f32','<f4') for k in KINDS}
        assert all(v.shape==(n,) and np.isfinite(v).all() and (v>=0).all() for v in maps.values())
        mask=np.fromfile(I/'occupancy.u8',np.uint8)==1
        assert (maps['p'][mask]<=1).all() and (maps['rawp'][mask]<=1).all()
        assert (maps['rawu'][mask]>=maps['rawp'][mask]).all()
        assert (maps['u'][mask]+1e-5>=maps['p'][mask]).all()
        rec=dict(source_index=int(row['source_index']),source_id=row['source_id'],wind_state=int(row['wind_state']),
                 transport_replica_index=int(row['transport_replica_index']),requested_seed=int(row['requested_seed']),
                 hashes={k:sha(str(pre)+f'.{k}.f32') for k in KINDS},wall_seconds=time.monotonic()-t)
        dump(done,rec)
        return rec
    records=[]
    with (O/'run.log').open('a') as log, concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for count,rec in enumerate(pool.map(run,rows),1):
            records.append(rec)
            if count==1 or count%88==0 or count==54912:
                elapsed=time.monotonic()-start
                state=dict(completed=count,total=54912,elapsed_seconds=elapsed,remaining_seconds_at_observed_rate=elapsed*(54912-count)/count,
                           last_source=rec['source_id'],stage='candidate bank only; targets inaccessible')
                dump(R/'CANDIDATE_PROGRESS.json',state)
                log.write(json.dumps(state)+'\n');log.flush()
                print('CANDIDATE_PROGRESS',count,'/ 54912',round(elapsed,1),flush=True)
    dump(R/'CANDIDATE_BANK_AUDIT.json',dict(passed=True,completed=54912,source_count=624,states=11,replicas_per_state=8,
        float_maps=54912*4,wall_seconds=time.monotonic()-start,seed_manifest_sha256=sha(P/'frozen/HOUSE03_FUTURE_PMFS_SEEDS_FULL624_54912.tsv'),
        fresh_targets_generated=0,records=records))
    print('FULL624_CANDIDATE_BANK_COMPLETE',flush=True)

def prefix(row):
    return O/f"source_{row['source_index']}"/f"state_{row['wind_state']}_replica_{row['transport_replica_index']}"

if __name__=='__main__':main()

"""Reference-only physical readout cache. Uses every recorded state and zero response."""
from common_b import *
import numpy as np,csv,collections,importlib.util,time,shutil
def module(n,p):
    s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def csvrows(p):
    with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def main():
    started=time.perf_counter();reg=load(CORE/'experiment_registry.json');root=Path(reg['host_data_path'])
    raw=module('raw_native_readout',CORE/'source/verify_raw_receiver_queries.py');prim=module('native_cache_primitive',CORE/'source/cache_native.py').cutoff_and_contributions
    occ=raw.occupancy(RAW/'OccupancyGrid3D.csv');cache=RAW/'reference_cache';cache.mkdir(exist_ok=False)
    points=np.array(reg['all_receiver_xyz'][:10],dtype=np.float32);entries=[];costs=[];anchors=[]
    jobs=[j for j in reg['jobs'] if j['role'] in ('reference','extra_reference')]
    for job in jobs:
        bank=root/'realizations'/job['job_id'];assert load(bank/'QUALIFICATION.json')['physical_qualification']=='PASS'
        lineage=csvrows(bank/'QUERY_PHYSICAL_LINEAGE.csv');native={r['query_id']:r for r in csvrows(bank/'QUERY_OUTPUT.csv')}
        multiplicity=collections.Counter(int(r['frame']) for r in lineage)
        for frame,count in sorted(multiplicity.items()):
            t=time.perf_counter();desc=raw.snapshot(bank/'bank'/f'iteration_{frame}');parse=time.perf_counter()-t
            t=time.perf_counter();phi,tot,e,b,p=prim(desc['filaments'],points,desc,occ,raw);wall=time.perf_counter()-t
            idx=next(int(l['block_id']) for l in lineage if int(l['frame'])==frame)
            target=np.array([float(native[f'b{idx}_p{k}']['ppm_float32']) for k in range(10)],dtype=np.float32)
            assert np.all(np.abs(tot.astype(float)-target.astype(float))<=3e-7+5e-6*np.abs(target)),(job['job_id'],frame,tot,target)
            fn=f"{job['job_id']}_frame{frame}.npz";np.savez_compressed(cache/fn,filaments=desc['filaments'],contributions=phi,native_totals=tot,exposure=np.array(count))
            entries.append(dict(job_id=job['job_id'],frame=frame,exposure=count,particles=len(desc['filaments']),file=fn,SHA256=sha(cache/fn)))
            costs.append(dict(stage='reference_particle_cache',job_id=job['job_id'],frame=frame,queries=10,parse_wall_s=parse,wall_s=wall,particle_tests=len(desc['filaments'])*10,LOS_calls=int(e.sum()),fallback_particles=0))
            if frame==min(multiplicity):anchors.append(dict(job_id=job['job_id'],frame=frame,maximum_abs_CPP_difference=float(np.max(np.abs(tot-target))),anchor_queries=10,first_anchor_before_fit=True))
            dump(CORE/'progress.json',dict(phase='REFERENCE_CACHE',job=job['job_id'],frame=frame,wall_s=time.perf_counter()-started,particles=len(desc['filaments'])))
    dump(cache/'CACHE_INDEX.json',dict(entries=entries,reference_jobs=len(jobs),poses=10,all_zero_records_retained=True,stable_particle_ID=False,wall_s=time.perf_counter()-started,anchors=anchors))
    for name,rr in [('REFERENCE_CACHE_COSTS.csv',costs),('NATIVE_CPP_CACHE_ANCHORS.csv',anchors)]:
        with (CORE/name).open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
    print(json.dumps(dict(status='PASS_REFERENCE_CACHE_NATIVE_ANCHORS',frames=len(entries),reference_jobs=len(jobs),wall_s=time.perf_counter()-started)))
if __name__=='__main__':main()

from __future__ import annotations
import sys, json, math
from pathlib import Path
import multiprocessing as mp
import pandas as pd
sys.path.insert(0,'/mnt/data/h01_temporal_gate')
import torch
import v3_physics_order_temporal_nre as v3
import train_eval_ctt_temporal_nre as v1

OUT=Path('/mnt/data/h01_temporal_gate/v3')

def worker(u):
    torch.set_num_threads(1)
    D=v1.Data(); M=v3.get_models(D); fs=v3.fresh_sources(D); cut=D.med[u]
    rows=[]
    for j,true in enumerate(fs,1):
        s=v3.score_all(M,D,true,cut,False)
        sp=v3.score_all(M,D,true,cut,True)
        e=v3.raw_energy(D,true,cut)
        r=v1.rank_desc(s,true); rp=v1.rank_desc(sp,true); re=v1.rank_asc(e,true)
        post=v1.rank_desc(__import__('numpy').log(__import__('numpy').maximum(D.prior,1e-300))+s,true)
        rows.append([u,0,cut,D.nblocks(v3.TEST_TRAJ,cut),true,r,rp,re,post])
    p=OUT/f'median_update{u}_cases.csv'
    pd.DataFrame(rows,columns=['update','timing_index','cut_time_s','blocks','true','network','perm','energy','post']).to_csv(p,index=False)
    return str(p)

def aggregate(df): return v3.aggregate(df)

def main():
    with mp.Pool(5) as pool:
        paths=pool.map(worker,range(1,6))
    df=pd.concat([pd.read_csv(p) for p in paths],ignore_index=True)
    df.to_csv(OUT/'median_cases.csv',index=False)
    overall=aggregate(df); by={str(u):aggregate(g) for u,g in df.groupby('update')}
    wins=int((df.network<df.perm).sum()); losses=int((df.network>df.perm).sum()); ties=len(df)-wins-losses; n=wins+losses
    from math import comb
    p=min(1.0,2*sum(comb(n,i) for i in range(min(wins,losses)+1))/(2**n)) if n else 1.0
    t=overall['network']['top10']>=overall['perm']['top10']+0.05 and wins>losses and p<=0.01
    ph=overall['network']['top5']>=overall['energy']['top5']-0.05 and overall['network']['top10']>=overall['energy']['top10'] and overall['network']['mean_norm_rank']<=overall['energy']['mean_norm_rank']
    on=all(by[str(u)]['network']['median_rank']<=1+0.25*209 for u in range(1,6)) and by['1']['network']['mean_norm_rank']<=by['1']['energy']['mean_norm_rank']+0.05
    po=overall['post']['mean_norm_rank']<=overall['network']['mean_norm_rank']+0.05 and all(by[str(u)]['post']['mean_norm_rank']<=by[str(u)]['network']['mean_norm_rank']+0.10 for u in range(1,6))
    summary={'contract':'CTT_PHYSICS_ORDER_CONSISTENT_CAUSAL_TEMPORAL_NRE_V3_H01_GATE','timing_mode':'median','fresh_test':'trajectory4005_member3_on_fresh_source_subset','fresh_source_count':len(v3.fresh_sources(v1.Data())),'overall':overall,'by_update':by,'time_permute':{'wins':wins,'losses':losses,'ties':ties,'sign_p':p},'gates':{'time':bool(t),'physics_non_degradation':bool(ph),'online':bool(on),'posterior':bool(po)},'verdict':'PASS' if t and ph and on and po else 'NO_GO'}
    (OUT/'median_summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))
if __name__=='__main__': main()

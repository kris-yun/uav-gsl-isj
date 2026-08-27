#!/usr/bin/env python3
"""Cross-representation V3 tangent audit for frozen V12 hit-probability response banks.

Scientific boundary:
- V12 response banks are hit-probability response maps, NOT CTT first-passage banks.
- This script must never relabel V12 maps as historical H02 hard-28 evidence.
- It asks only whether observation-conditioned 2-D source-information loss
  persists in the PMFS/response representation.

All source-resolution mathematics is delegated to `v3_math.py`.
"""
from __future__ import annotations
import argparse,csv,json,struct
from pathlib import Path
import numpy as np

from v3_math import nuisance_metric, delaunay_neighbors, tangent_information_for_source


def load_bank(path:Path):
    raw=path.read_bytes()
    if raw[:8]!=b'V12BNKR1': raise ValueError('bad V12 bank magic')
    version,width,height,cells,S,M,T,method_seed,substream=struct.unpack_from('<9Q',raw,8)
    cell_size,ox,oy,dt,noise=struct.unpack_from('<5d',raw,80)
    mask=np.frombuffer(raw,dtype=np.uint8,count=cells,offset=120).astype(bool)
    if int(mask.sum())<=0: raise ValueError('empty free-cell mask')
    payload_bytes=S*M*cells*4
    offset=len(raw)-payload_bytes
    maps=np.frombuffer(raw,dtype='<f4',count=S*M*cells,offset=offset).reshape(S,M,cells).astype(np.float64)
    return maps[:,:,mask],{'version':version,'width':width,'height':height,'cell_count':cells,
        'free_cells':int(mask.sum()),'carrier_count':S,'member_count':M,'timesteps':T,
        'method_seed':method_seed,'transport_substream':substream,'cell_size':cell_size,
        'origin_x':ox,'origin_y':oy,'delta_time':dt,'noise_std':noise,'payload_offset':offset}


def load_xy(path:Path,S:int):
    with path.open(newline='') as f: rr=list(csv.DictReader(f))
    if len(rr)!=S: raise ValueError(f'manifest rows {len(rr)} != carrier_count {S}')
    if [int(r['carrier_index']) for r in rr] != list(range(S)): raise ValueError('carrier_index order drift')
    xy=np.asarray([[float(r['x']),float(r['y'])] for r in rr])
    if len({(round(float(x),7),round(float(y),7)) for x,y in xy})!=S:
        raise ValueError('V12 audit expects unique physical coordinates; quotient separately if not')
    return xy


def tangent_summary(x,xy,nb):
    metric=nuisance_metric(x)
    rows=[tangent_information_for_source(x,xy,i,nb[i],metric) for i in range(len(xy))]
    lam=np.asarray([r['lambda_min'] for r in rows],float)
    gam=np.asarray([r['gamma_xy'] for r in rows],float)
    return {
        'lambda_min_positive_fraction':float(np.mean(lam>0)),
        'gamma_xy_median':float(np.median(gam)),
        'nuisance_rank':metric.numerical_rank,
        'nuisance_dimension':int(metric.covariance.shape[0]),
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('bank',type=Path); ap.add_argument('manifest',type=Path)
    ap.add_argument('--supports',default='1,2,4,8,16,32,64,128,256')
    ap.add_argument('--repeats',type=int,default=5); ap.add_argument('--seed',type=int,default=20260827)
    ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    phi,meta=load_bank(a.bank); xy=load_xy(a.manifest,phi.shape[0]); nb,_=delaunay_neighbors(xy)
    rng=np.random.default_rng(a.seed); D=phi.shape[2]
    supports=[int(x) for x in a.supports.split(',') if x.strip()]
    if D not in supports: supports.append(D)
    result=[]
    for Q in supports:
        if Q<1 or Q>D: continue
        reps=[]
        for _ in range(1 if Q==D else a.repeats):
            idx=np.arange(D) if Q==D else np.sort(rng.choice(D,Q,replace=False))
            reps.append(tangent_summary(phi[:,:,idx],xy,nb))
        result.append({
            'support':Q,
            'lambda_min_positive_fraction_mean':float(np.mean([r['lambda_min_positive_fraction'] for r in reps])),
            'gamma_xy_median_mean':float(np.mean([r['gamma_xy_median'] for r in reps])),
            'nuisance_rank_mean':float(np.mean([r['nuisance_rank'] for r in reps])),
            'repeats':len(reps),
        })
    out={
        'contract':'CG_PC_CTT_V3_V12_SENSOR_RESPONSE_TANGENT_AUDIT_V2_FULL_COVARIANCE',
        'diagnostic_only':True,
        'nuisance_metric':'full_pair_difference_covariance_moore_penrose_precision',
        'scientific_boundary':'V12 hit-probability response maps are not CTT first-passage hard-28 evidence.',
        'bank_meta':meta,'unique_candidate_coordinates':len(xy),'results':result
    }
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(out,indent=2),encoding='utf-8'); print(json.dumps(out,indent=2))

if __name__=='__main__': main()

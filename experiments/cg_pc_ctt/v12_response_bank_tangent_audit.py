#!/usr/bin/env python3
"""Diagnostic-only local 2-D tangent audit for frozen V12 response banks.

Scientific boundary:
- V12 response banks are hit-probability response maps, NOT CTT first-passage banks.
- This script must never relabel V12 maps as CG-PC-CTT hard-28 evidence.
- It is used only to test whether observation-conditioned 2-D source-rank loss
  persists after the PMFS/response representation.

Binary V12BNKR1 contract used here:
  magic[8]
  uint64: version,width,height,cell_count,carrier_count,member_count,timesteps,
          method_seed,transport_substream
  double: cell_size,origin_x,origin_y,delta_time,noise_std
  uint8 occupancy_free[cell_count]
  variable carrier metadata
  trailing float32 response maps [S,M,cell_count]

A separate carrier manifest CSV provides carrier_index,carrier_id,x,y.
"""
from __future__ import annotations
import argparse,csv,json,math,struct
from itertools import combinations
from pathlib import Path
import numpy as np
from scipy.spatial import Delaunay

RIDGE_REL=1e-3; EPS=1e-9


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


def neighbours(xy):
    tri=Delaunay(xy); nb=[set() for _ in range(len(xy))]
    for simplex in tri.simplices:
        for i,j in combinations(map(int,simplex),2): nb[i].add(j); nb[j].add(i)
    return [np.asarray(sorted(v),int) for v in nb]


def whitener(x):
    S,M,D=x.shape; ss=np.zeros(D); n=0
    for m in range(M):
        for h in range(m+1,M):
            d=x[:,m]-x[:,h]; ss+=np.sum(.5*d*d,axis=0); n+=S
    v=ss/max(n,1); ridge=max(EPS,RIDGE_REL*max(float(v.mean()),EPS))
    return 1/np.sqrt(v+ridge)


def tangent(x,xy,nb):
    S,M,D=x.shape; w=whitener(x); rows=[]
    for i,jj in enumerate(nb):
        DX=xy[jj]-xy[i]
        if np.linalg.matrix_rank(DX)<2:
            rows.append((0.,0.,0.)); continue
        P=np.linalg.pinv(DX); B=[]
        for m in range(M): B.append(P@((x[jj,m]-x[i,m])*w[None,:]))
        F=np.zeros((2,2))
        for m in range(M):
            for n in range(M):
                if m!=n: F+=B[m]@B[n].T
        F/=M*(M-1); F=.5*(F+F.T)
        ev=np.linalg.eigvalsh(F); lmin,lmax=map(float,ev)
        gamma=math.sqrt(max(lmin,0.)/max(lmax,EPS)) if lmax>0 else 0.
        rows.append((lmin,lmax,gamma))
    return np.asarray(rows)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('bank',type=Path); ap.add_argument('manifest',type=Path)
    ap.add_argument('--supports',default='1,2,4,8,16,32,64,128,256')
    ap.add_argument('--repeats',type=int,default=5); ap.add_argument('--seed',type=int,default=20260827)
    ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    phi,meta=load_bank(a.bank); xy=load_xy(a.manifest,phi.shape[0]); nb=neighbours(xy)
    rng=np.random.default_rng(a.seed); D=phi.shape[2]
    supports=[int(x) for x in a.supports.split(',') if x.strip()]
    if D not in supports: supports.append(D)
    result=[]
    for Q in supports:
        if Q<1 or Q>D: continue
        reps=[]
        for _ in range(1 if Q==D else a.repeats):
            idx=np.arange(D) if Q==D else np.sort(rng.choice(D,Q,replace=False))
            z=tangent(phi[:,:,idx],xy,nb)
            reps.append({'lambda_min_positive_fraction':float(np.mean(z[:,0]>0)),
                         'gamma_xy_median':float(np.median(z[:,2]))})
        result.append({'support':Q,
                       'lambda_min_positive_fraction_mean':float(np.mean([r['lambda_min_positive_fraction'] for r in reps])),
                       'gamma_xy_median_mean':float(np.mean([r['gamma_xy_median'] for r in reps])),
                       'repeats':len(reps)})
    out={'contract':'CG_PC_CTT_V3_V12_SENSOR_RESPONSE_TANGENT_AUDIT_V1','diagnostic_only':True,
         'scientific_boundary':'V12 hit-probability response maps are not CTT first-passage hard-28 evidence.',
         'bank_meta':meta,'unique_candidate_coordinates':len(xy),'results':result}
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(out,indent=2),encoding='utf-8'); print(json.dumps(out,indent=2))

if __name__=='__main__': main()

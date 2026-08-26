#!/usr/bin/env python3
"""Truth-free local-pair audit for CG-PC-CTT replicated source ensembles.

This is a diagnostic, not a replacement/tuning rule for frozen Gate V2.
It detects candidate-coordinate aliases and asks whether each candidate is
replicably separable from its nearest physical neighbor using the same
pair-difference nuisance scale and exact M-member sign-flip null as the
fast-track H02 pair diagnostic.

NPZ contract:
  phi[N,S,M,D] or phi[S,M,D]
  candidate_xy[S,2]
Optional:
  context[N]
"""
from __future__ import annotations
import argparse,csv,json
from itertools import product
from pathlib import Path
import numpy as np


def noise_whitener(x):
    S,M,D=x.shape; ss=np.zeros(D,dtype=np.float64); n=0
    for m in range(M):
        for h in range(m+1,M):
            diff=x[:,m,:]-x[:,h,:]
            ss += np.sum(0.5*diff*diff,axis=0); n += S
    v=ss/max(n,1)
    ridge=max(1e-9,1e-3*max(float(np.mean(v)),1e-9))
    return 1.0/np.sqrt(v+ridge)


def pair_stat(x,w,i,j,patterns):
    M=x.shape[1]
    d=(x[i]-x[j])*w[None,:]
    selfsum=float(np.sum(d*d))
    totals=patterns@d
    q=(np.sum(totals*totals,axis=1)-selfsum)/float(M*(M-1))
    obs=float(q[-1])  # product order ends at all +1
    p=float(np.mean(q>=obs-1e-12))
    return float(np.sqrt(max(obs,0.0))),p,obs


def coordinate_groups(xy,tol_decimals=7):
    groups={}
    for i,(x,y) in enumerate(xy):
        key=(round(float(x),tol_decimals),round(float(y),tol_decimals))
        groups.setdefault(key,[]).append(i)
    return {k:v for k,v in groups.items() if len(v)>1}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('npz',type=Path)
    ap.add_argument('--out-csv',type=Path,required=True)
    ap.add_argument('--out-json',type=Path,required=True)
    a=ap.parse_args()
    d=np.load(a.npz,allow_pickle=True)
    phi=np.asarray(d['phi'],dtype=np.float64)
    if phi.ndim==3: phi=phi[None,...]
    if phi.ndim!=4: raise ValueError(f'phi must be [N,S,M,D] or [S,M,D], got {phi.shape}')
    xy=np.asarray(d['candidate_xy'],dtype=np.float64)
    N,S,M,D=phi.shape
    if xy.shape!=(S,2): raise ValueError(f'candidate_xy must be [{S},2], got {xy.shape}')
    if M>16: raise ValueError('exact sign-flip audit limited to M<=16')
    patterns=np.asarray([(1.0,)+tail for tail in product((-1.0,1.0),repeat=M-1)],dtype=np.float64)
    d2=((xy[:,None,:]-xy[None,:,:])**2).sum(axis=2)
    np.fill_diagonal(d2,np.inf)
    nn=np.argmin(d2,axis=1); nnd=np.sqrt(d2[np.arange(S),nn])
    dup=coordinate_groups(xy)
    rows=[]
    for n in range(N):
        w=noise_whitener(phi[n])
        for i,j in enumerate(nn):
            alpha,p,cross=pair_stat(phi[n],w,i,int(j),patterns)
            rows.append({'context_index':n,'candidate_idx':i,'nearest_idx':int(j),
                         'distance':float(nnd[i]),'pair_alpha_cf':alpha,
                         'pair_p_signflip':p,'pair_cross_strength':cross,
                         'coordinate_alias':bool(nnd[i] <= 1e-9)})
    a.out_csv.parent.mkdir(parents=True,exist_ok=True)
    with a.out_csv.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    pvals=np.asarray([r['pair_p_signflip'] for r in rows]); alphas=np.asarray([r['pair_alpha_cf'] for r in rows])
    summary={'contract':'CG_PC_CTT_LOCAL_PAIR_AUDIT_V1','diagnostic_only':True,
             'shape':[N,S,M,D],'unique_coordinate_count':int(S-sum(len(v)-1 for v in dup.values())),
             'duplicate_coordinate_groups':int(len(dup)),
             'candidates_in_duplicate_groups':int(sum(len(v) for v in dup.values())),
             'nearest_distance_median':float(np.median(nnd)),
             'nearest_distance_min':float(np.min(nnd)),
             'pair_alpha_median':float(np.median(alphas)),
             'pair_alpha_q05':float(np.quantile(alphas,0.05)),
             'pair_p_le_0p01_fraction':float(np.mean(pvals<=0.01)),
             'pair_p_gt_0p05_fraction':float(np.mean(pvals>0.05)),
             'binding_note':'Do not use this audit to retune frozen Gate V2 after held-out visibility. It diagnoses global-vs-local identifiability and candidate aliases.'}
    a.out_json.write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))
if __name__=='__main__': main()

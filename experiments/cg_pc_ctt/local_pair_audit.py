#!/usr/bin/env python3
"""Truth-free local-pair audit for CG-PC-CTT replicated source ensembles.

Diagnostic only: this does not replace or retune frozen Gate V2.

Two levels are reported separately:
  1) candidate-ID level, which reveals duplicate-coordinate aliases;
  2) physical-coordinate quotient level, where all candidate IDs with the same
     (x,y) source coordinate are one physical source class.

This distinction is essential: two IDs at identical source coordinates are not
physically localizable from one another and must not be counted as two separate
localization failures.

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


def all_coordinate_groups(xy,tol_decimals=7):
    groups={}
    for i,(x,y) in enumerate(xy):
        key=(round(float(x),tol_decimals),round(float(y),tol_decimals))
        groups.setdefault(key,[]).append(i)
    return groups


def duplicate_groups(xy,tol_decimals=7):
    return {k:v for k,v in all_coordinate_groups(xy,tol_decimals).items() if len(v)>1}


def coordinate_quotient(x,xy,tol_decimals=7):
    """Merge exact coordinate aliases; predictions should be identical by physics/RNG contract."""
    groups=all_coordinate_groups(xy,tol_decimals)
    keys=list(groups.keys())
    qxy=np.asarray(keys,dtype=np.float64)
    # Mean is identity-preserving when alias fields are exactly equal; it also
    # avoids privileging one arbitrary candidate ID if a malformed artifact drifts.
    qx=np.stack([x[np.asarray(groups[k],dtype=int)].mean(axis=0) for k in keys],axis=0)
    return qx,qxy,groups


def nearest_rows(x,xy,patterns,context_index,level):
    S=len(xy)
    d2=((xy[:,None,:]-xy[None,:,:])**2).sum(axis=2)
    np.fill_diagonal(d2,np.inf)
    nn=np.argmin(d2,axis=1); nnd=np.sqrt(d2[np.arange(S),nn])
    w=noise_whitener(x)
    rows=[]
    for i,j in enumerate(nn):
        alpha,p,cross=pair_stat(x,w,i,int(j),patterns)
        rows.append({'context_index':context_index,'level':level,'candidate_idx':i,
                     'nearest_idx':int(j),'distance':float(nnd[i]),
                     'pair_alpha_cf':alpha,'pair_p_signflip':p,
                     'pair_cross_strength':cross,'coordinate_alias':bool(nnd[i] <= 1e-9)})
    return rows,nnd


def metrics(rows):
    pvals=np.asarray([r['pair_p_signflip'] for r in rows],dtype=float)
    alphas=np.asarray([r['pair_alpha_cf'] for r in rows],dtype=float)
    dist=np.asarray([r['distance'] for r in rows],dtype=float)
    return {
        'n_rows':int(len(rows)),
        'nearest_distance_median':float(np.median(dist)),
        'nearest_distance_min':float(np.min(dist)),
        'pair_alpha_median':float(np.median(alphas)),
        'pair_alpha_q05':float(np.quantile(alphas,0.05)),
        'pair_p_le_0p01_fraction':float(np.mean(pvals<=0.01)),
        'pair_p_gt_0p05_fraction':float(np.mean(pvals>0.05)),
    }


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

    dup=duplicate_groups(xy)
    id_rows=[]; physical_rows=[]
    physical_count=None
    max_alias_field_drift=0.0
    for n in range(N):
        r,_=nearest_rows(phi[n],xy,patterns,n,'candidate_id')
        id_rows.extend(r)
        qx,qxy,groups=coordinate_quotient(phi[n],xy)
        physical_count=len(qxy) if physical_count is None else physical_count
        qr,_=nearest_rows(qx,qxy,patterns,n,'physical_coordinate_class')
        physical_rows.extend(qr)
        # Alias fields should be exact under candidate-ID-independent keyed transport.
        for inds in groups.values():
            if len(inds)>1:
                ref=phi[n,inds[0]]
                for j in inds[1:]:
                    max_alias_field_drift=max(max_alias_field_drift,float(np.max(np.abs(ref-phi[n,j]))))

    all_rows=id_rows+physical_rows
    a.out_csv.parent.mkdir(parents=True,exist_ok=True)
    with a.out_csv.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(all_rows[0].keys())); w.writeheader(); w.writerows(all_rows)

    summary={'contract':'CG_PC_CTT_LOCAL_PAIR_AUDIT_V2','diagnostic_only':True,
             'shape':[N,S,M,D],
             'candidate_id_count':int(S),
             'physical_coordinate_class_count':int(physical_count),
             'duplicate_coordinate_groups':int(len(dup)),
             'candidates_in_duplicate_groups':int(sum(len(v) for v in dup.values())),
             'max_alias_field_drift':float(max_alias_field_drift),
             'candidate_id_level':metrics(id_rows),
             'physical_coordinate_quotient_level':metrics(physical_rows),
             'binding_note':(
                 'Do not use this audit to retune frozen Gate V2. Exact coordinate aliases are representation '
                 'duplicates, not distinct physical localization targets. Any future method that merges them must '
                 'be separately versioned and truth-free.'
             )}
    a.out_json.write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))
if __name__=='__main__': main()

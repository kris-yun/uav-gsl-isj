#!/usr/bin/env python3
"""2-D local tangent source-information diagnostic for CG-PC-CTT V3.

The physical source coordinate is x=(x,y), so local continuous source
identifiability should be a 2-D inverse-problem property rather than an
arbitrary global rank-3 condition.

For source i and member m, fit a local response Jacobian from Delaunay
neighbours after V2 pair-difference whitening:
    Delta z ~= J_{i,m} Delta x.
Then form the cross-member replicated tangent information matrix
    F_i = avg_{m!=n} J_{i,m}^T W^2 J_{i,n}.
The reported gamma_xy=sqrt(max(lambda_min,0)/max(lambda_max,eps)).

Diagnostic only; no threshold is used to alter frozen V2.
"""
from __future__ import annotations
import argparse,csv,json,math
from itertools import combinations
from pathlib import Path
import numpy as np
from scipy.spatial import Delaunay

RIDGE_REL=1e-3; EPS=1e-9


def coordinate_quotient(x,xy,decimals=7):
    groups={}
    for i,(a,b) in enumerate(xy): groups.setdefault((round(float(a),decimals),round(float(b),decimals)),[]).append(i)
    keys=list(groups); qxy=np.asarray(keys,float)
    qx=np.stack([x[np.asarray(groups[k],int)].mean(0) for k in keys])
    return qx,qxy


def noise_whitener(x):
    S,M,D=x.shape; ss=np.zeros(D); n=0
    for m in range(M):
        for h in range(m+1,M):
            d=x[:,m]-x[:,h]; ss+=np.sum(.5*d*d,axis=0); n+=S
    v=ss/max(n,1); ridge=max(EPS,RIDGE_REL*max(float(v.mean()),EPS))
    return 1/np.sqrt(v+ridge),ridge


def neighbours(xy):
    tri=Delaunay(xy); nb=[set() for _ in range(len(xy))]
    for simplex in tri.simplices:
        for i,j in combinations(map(int,simplex),2): nb[i].add(j); nb[j].add(i)
    return [np.asarray(sorted(x),int) for x in nb]


def context_rows(x,xy):
    x,xy=coordinate_quotient(x,xy); M=x.shape[1]; w,ridge=noise_whitener(x); nb=neighbours(xy); rows=[]
    for i,jj in enumerate(nb):
        DX=xy[jj]-xy[i]
        if np.linalg.matrix_rank(DX)<2:
            rows.append({'physical_source_idx':i,'lambda_max':0.0,'lambda_min':0.0,'gamma_xy':0.0,'neighbor_count':len(jj),'geometry_rank':int(np.linalg.matrix_rank(DX)),'ridge':ridge}); continue
        pinv=np.linalg.pinv(DX); B=[]
        for m in range(M):
            DZ=(x[jj,m]-x[i,m])*w[None,:]
            # B_m is 2 x D, equivalent to J_m^T in whitened feature space.
            B.append(pinv@DZ)
        F=np.zeros((2,2))
        for m in range(M):
            for n in range(M):
                if m!=n: F += B[m]@B[n].T
        F/=float(M*(M-1)); F=.5*(F+F.T)
        ev=np.linalg.eigvalsh(F)[::-1]; lmax,lmin=map(float,ev)
        gamma=math.sqrt(max(lmin,0.0)/max(lmax,EPS)) if lmax>0 else 0.0
        rows.append({'physical_source_idx':i,'lambda_max':lmax,'lambda_min':lmin,'gamma_xy':gamma,'neighbor_count':len(jj),'geometry_rank':2,'ridge':ridge})
    return rows


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('npz',type=Path); ap.add_argument('--feature-index',type=Path,default=None)
    ap.add_argument('--out-csv',type=Path,required=True); ap.add_argument('--out-json',type=Path,required=True); a=ap.parse_args()
    d=np.load(a.npz,allow_pickle=True); phi=np.asarray(d['phi'],float); xy=np.asarray(d['candidate_xy'],float)
    if phi.ndim==3: phi=phi[None]
    N,S,M,D=phi.shape
    if a.feature_index is None: idx=np.arange(D)
    else:
        idx=np.asarray(np.load(a.feature_index) if a.feature_index.suffix in ('.npy','.npz') else np.loadtxt(a.feature_index,dtype=int,ndmin=1)).reshape(-1)
        if a.feature_index.suffix=='.npz':
            zz=np.load(a.feature_index); idx=np.asarray(zz['feature_index'] if 'feature_index' in zz.files else zz[zz.files[0]])
        idx=np.asarray(idx,dtype=int)
    allr=[]; summaries=[]
    for n in range(N):
        rr=context_rows(phi[n][:,:,idx],xy)
        for r in rr:r['context_index']=n
        allr+=rr; lam=np.asarray([r['lambda_min'] for r in rr]); gam=np.asarray([r['gamma_xy'] for r in rr])
        summaries.append({'context_index':n,'feature_count':int(len(idx)),'physical_sources':len(rr),
                          'lambda_min_positive_fraction':float(np.mean(lam>0)),
                          'gamma_xy_median':float(np.median(gam)),
                          'gamma_xy_q05_q95':[float(x) for x in np.quantile(gam,[.05,.95])]})
    a.out_csv.parent.mkdir(parents=True,exist_ok=True)
    with a.out_csv.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(allr[0].keys())); w.writeheader(); w.writerows(allr)
    out={'contract':'CG_PC_CTT_LOCAL_TANGENT_INFORMATION_V1','diagnostic_only':True,
         'source_dimension':2,'contexts':summaries,
         'binding_note':'This diagnostic aligns local source identifiability with the 2-D physical source manifold; it does not retune frozen V2.'}
    a.out_json.write_text(json.dumps(out,indent=2),encoding='utf-8'); print(json.dumps(out,indent=2))

if __name__=='__main__': main()

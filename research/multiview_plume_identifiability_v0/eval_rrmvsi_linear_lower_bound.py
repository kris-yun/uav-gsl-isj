#!/usr/bin/env python3
"""Reproducible RR-MVSI linear D1 lower-bound diagnostics.

Input:
  D1R pooled tensor [168,16,10,30]
  frozen 168-source panel TSV

This script contains no new-simulation logic.
It evaluates paired-view generalized-eigen shared-content representations and
ordinary source-heldout baselines on full 168-candidate support.

The nonlinear RR-MVSI candidate must beat this lower bound; this script is not
itself the paper method.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.linalg import eigh
from scipy.spatial.distance import cdist

EPS=1e-12
DIMS=(5,10,20,40)
LS=(0.3,0.6,1.2,2.4)
RIDGES=(1e-4,1e-3,1e-2,1e-1)
TEMPS=(0.25,0.5,1.0,2.0,4.0)

def rbf_krr(xtr,ytr,xq,l,ridge):
    K=np.exp(-cdist(xtr,xtr,'sqeuclidean')/(2*l*l))
    A=np.linalg.solve(K+ridge*np.eye(len(xtr)),ytr)
    Kq=np.exp(-cdist(xq,xtr,'sqeuclidean')/(2*l*l))
    return Kq@A

def paired_basis(x):
    # x [Ns,8,D], pair first4/last4.
    ns,r,d=x.shape
    xc=x-x.reshape(-1,d).mean(0,keepdims=True)
    a=xc[:,:4].reshape(-1,d)
    b=xc[:,4:8].reshape(-1,d)
    Cxy=(a.T@b+b.T@a)/(2*len(a))
    allv=xc.reshape(-1,d)
    Cxx=(allv.T@allv)/len(allv)
    ridge=1e-4*np.trace(Cxx)/d+1e-8
    vals,vecs=eigh(Cxy,Cxx+ridge*np.eye(d))
    order=np.argsort(vals)[::-1]
    return vecs[:,order], x.reshape(-1,d).mean(0)

def softmax_logscore(z,proto,temp,true_idx):
    dist=((z[:,None,:]-proto[None,:,:])**2).sum(2)
    logits=-dist/max(temp,EPS)
    m=logits.max(1,keepdims=True)
    lp=logits-m-np.log(np.exp(logits-m).sum(1,keepdims=True))
    return lp[np.arange(len(z)),true_idx]/np.log(2), np.argsort(-lp,axis=1)

def source_cv_score(xtrain,xytrain,d,l,ridge,temp):
    # deterministic 4 source folds; basis/KRR learned without validation sources.
    ns=len(xtrain); fold=np.arange(ns)%4; vals=[]
    for f in range(4):
        tr=np.where(fold!=f)[0]; va=np.where(fold==f)[0]
        V,mu=paired_basis(xtrain[tr])
        V=V[:,:d]
        trmean=((xtrain[tr]-mu)@V).mean(1)
        proto=rbf_krr(xytrain[tr],trmean,xytrain,l,ridge)
        z=((xtrain[va]-mu)@V).reshape(-1,d)
        true=np.repeat(va,8)
        sc,_=softmax_logscore(z,proto,temp,true)
        vals.append(sc.mean())
    return float(np.mean(vals))

def fit_eval(X,panel,train_sources,target_sources,train_reps,test_reps):
    xy=panel[['x_m','y_m']].to_numpy(float)
    xt=X[train_sources][:,train_reps]
    # choose everything on train-source CV only
    best=None
    for d in DIMS:
      for l in LS:
       for rg in RIDGES:
        for t in TEMPS:
         s=source_cv_score(xt,xy[train_sources],d,l,rg,t)
         key=(s,-d,-l,-rg,-t)
         if best is None or key>best[0]: best=(key,d,l,rg,t,s)
    _,d,l,rg,t,cv=best
    V,mu=paired_basis(xt); V=V[:,:d]
    src_code=((xt-mu)@V).mean(1)
    # predict prototypes for ALL 168 candidates from outer-train source contexts only
    proto=rbf_krr(xy[train_sources],src_code,xy,l,rg)
    z=((X[target_sources][:,test_reps]-mu)@V).reshape(-1,d)
    true=np.repeat(target_sources,len(test_reps))
    sc,ranked=softmax_logscore(z,proto,t,true)
    ranks=np.array([np.where(ranked[i]==true[i])[0][0]+1 for i in range(len(true))])
    return dict(d=int(d),lengthscale=float(l),ridge=float(rg),temp=float(t),
                inner_cv_log2=float(cv),test_log2=float(sc.mean()),
                top1=float(np.mean(ranks==1)),top3=float(np.mean(ranks<=3)),
                top10=float(np.mean(ranks<=10)),median_rank=float(np.median(ranks)))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--tensor',type=Path,required=True)
    ap.add_argument('--panel',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    C=np.load(a.tensor,allow_pickle=False)
    if C.shape!=(168,16,10,30): raise ValueError(C.shape)
    X=np.log1p(C).reshape(168,16,300)
    p=pd.read_csv(a.panel,sep='\t')
    parity=((p.pmfs_i.to_numpy(int)+p.pmfs_j.to_numpy(int))&1)
    runs=[]
    for direction,(trr,ter) in enumerate(((np.arange(8),np.arange(8,16)),(np.arange(8,16),np.arange(8)))):
      for hp in (0,1):
        train=np.where(parity!=hp)[0]; target=np.where(parity==hp)[0]
        r=fit_eval(X,p,train,target,trr,ter)
        r.update(direction=direction,heldout_parity=hp,n_train_sources=len(train),n_target_sources=len(target))
        runs.append(r)
    out={'decision':'RR_MVSI_LINEAR_LOWER_BOUND_ONLY','runs':runs}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
if __name__=='__main__':
    main()

#!/usr/bin/env python3
"""D2 finite-memory source likelihood on the frozen Gate-1A review bank.

The memory horizon is determined without target A/B:
use the first non-positive mean temporal correlation of independent
prediction-realization differences, and retain all preceding lags.

This remains an offline Gaussian finite-memory proxy, not a full learned
Mori-Zwanzig operator.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd


def pooled_probe(cube, points):
    vals=[]
    for p in points:
        vals.append(cube[:, int(p["native_x0"]):int(p["native_x1_exclusive"]),
                         int(p["native_y0"]):int(p["native_y1_exclusive"])].mean(axis=(1,2)))
    return np.stack(vals,axis=1).astype(np.float64)


def l1_time(z):
    s=z.sum(axis=-1,keepdims=True)
    return np.divide(z,s,out=np.zeros_like(z,dtype=np.float64),where=s>0)


def temporal_cov(z,mask):
    d=z[:,0]-z[:,1]
    m=np.transpose(d[mask],(0,2,1)).reshape(-1,d.shape[1])
    m-=m.mean(axis=0,keepdims=True)
    return np.cov(m,rowvar=False,bias=False)


def lag_corr(k):
    sd=np.sqrt(np.diag(k))
    c=k/np.outer(sd,sd)
    return [float(np.mean([c[i,i+h] for i in range(k.shape[0]-h)]))
            for h in range(1,k.shape[0])]


def first_zero_horizon(k):
    vals=lag_corr(k)
    first_nonpos=next((i+1 for i,v in enumerate(vals) if v<=0),len(vals))
    return max(0,first_nonpos-1),vals


def rank_for_memory(mean_z,y,k,m,truth_idx):
    params=[]
    for t in range(k.shape[0]):
        if t==0 or m==0:
            params.append((np.zeros(0),float(k[t,t]),[]))
        else:
            start=max(0,t-m)
            idx=list(range(start,t))
            kpp=k[np.ix_(idx,idx)]
            kp=k[t,idx]
            coef=kp@np.linalg.inv(kpp)
            var=float(k[t,t]-coef@k[idx,t])
            params.append((coef,var,idx))
    scores=np.zeros(mean_z.shape[0])
    for s in range(mean_z.shape[0]):
        r=mean_z[s]-y
        q=0.0
        for t,(coef,var,idx) in enumerate(params):
            pred=np.tensordot(coef,r[idx,:],axes=(0,0)) if idx else 0.0
            innov=r[t]-pred
            q+=float(np.sum(innov**2)/(var+1e-15))
        scores[s]=q
    order=np.argsort(scores,kind="stable")
    return int(np.where(order==truth_idx)[0][0]+1)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--review-root",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    root=a.review_root
    c=json.loads((root/"frozen_inputs/gate1a_contract.json").read_text())
    bank=pd.read_csv(root/"frozen_inputs/source_bank.tsv",sep="\t")
    ids=bank.source_id.tolist()
    truth_idx=ids.index(c["truth_source_id"])

    x=np.empty((len(ids),2,10,30),dtype=np.float64)
    for si,seed in enumerate(c["prediction_seeds"]):
        for i,src in enumerate(ids):
            x[i,si]=np.load(root/f"predictions/seed_{seed}"/f"{src}.npy").reshape(10,30)
    ya=pooled_probe(np.load(root/"targets/S2_W2_A/concentration.npy"),c["probe_points"])
    yb=pooled_probe(np.load(root/"targets/S2_W2_B/concentration.npy"),c["probe_points"])

    z=l1_time(x)
    za=l1_time(ya)
    zb=l1_time(yb)
    mean_z=z.mean(axis=1)

    masks={
        "all":np.ones(len(ids),dtype=bool),
        "even_index":np.arange(len(ids))%2==0,
        "odd_index":np.arange(len(ids))%2==1,
        "truth_excluded":np.arange(len(ids))!=truth_idx,
    }
    robustness={}
    for name,mask in masks.items():
        k=temporal_cov(z,mask)
        horizon,corr=first_zero_horizon(k)
        robustness[name]={
            "first_nonpositive_lag":horizon+1,
            "memory_horizon":horizon,
            "A_rank":rank_for_memory(mean_z,za,k,horizon,truth_idx),
            "B_rank":rank_for_memory(mean_z,zb,k,horizon,truth_idx),
            "lag_correlations":corr,
        }

    k=temporal_cov(z,masks["all"])
    curve={}
    for m in range(0,10):
        curve[str(m)]={
            "A_rank":rank_for_memory(mean_z,za,k,m,truth_idx),
            "B_rank":rank_for_memory(mean_z,zb,k,m,truth_idx),
        }

    out={
        "decision":"D2_ADVANCE_FINITE_MEMORY_SOURCE_LIKELIHOOD",
        "source_count":len(ids),
        "truth_source_id":c["truth_source_id"],
        "target_blind_horizon_rule":"retain lags before first non-positive mean temporal correlation in C-D prediction differences",
        "robustness":robustness,
        "memory_rank_curve":curve,
        "scope":"Offline finite-memory proxy only; cross-source/cross-house falsification required before mainline freeze."
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out,indent=2))


if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Generic frozen D3 scorer for a new true source using the Gate-1A 630-source bank."""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np
import pandas as pd


def pooled_probe(cube, points):
    vals=[]
    for p in points:
        vals.append(cube[:,int(p["native_x0"]):int(p["native_x1_exclusive"]),
                         int(p["native_y0"]):int(p["native_y1_exclusive"])].mean(axis=(1,2)))
    return np.stack(vals,axis=1).astype(np.float64)


def l1_time(z):
    s=z.sum(axis=-1,keepdims=True)
    return np.divide(z,s,out=np.zeros_like(z,dtype=np.float64),where=s>0)


def rank(scores,truth_idx):
    order=np.argsort(scores,kind="stable")
    return int(np.where(order==truth_idx)[0][0]+1),order


def temporal_cov(z):
    d=z[:,0]-z[:,1]
    m=np.transpose(d,(0,2,1)).reshape(-1,d.shape[1])
    m-=m.mean(axis=0,keepdims=True)
    return np.cov(m,rowvar=False,bias=False)


def lag_corr(k):
    sd=np.sqrt(np.diag(k))
    c=k/np.outer(sd,sd)
    return [float(np.mean([c[i,i+h] for i in range(k.shape[0]-h)]))
            for h in range(1,k.shape[0])]


def horizon_from_predictions(k):
    vals=lag_corr(k)
    first_nonpos=next((i+1 for i,v in enumerate(vals) if v<=0),len(vals))
    return max(0,first_nonpos-1),vals


def finite_memory_scores(mean_z,y,k,m):
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
    return scores


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--contract",type=Path,required=True)
    ap.add_argument("--source-bank",type=Path,required=True)
    ap.add_argument("--prediction-root",type=Path,required=True)
    ap.add_argument("--target-a",type=Path,required=True)
    ap.add_argument("--target-b",type=Path,required=True)
    ap.add_argument("--truth-source-id",required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()

    c=json.loads(a.contract.read_text())
    bank=pd.read_csv(a.source_bank,sep="\t")
    ids=bank.source_id.tolist()
    if a.truth_source_id not in ids:
        raise ValueError("truth source is not in frozen 630-source bank")
    ti=ids.index(a.truth_source_id)

    x=np.empty((len(ids),2,10,30),dtype=np.float64)
    for si,seed in enumerate(c["prediction_seeds"]):
        d=a.prediction_root/f"seed_{seed}"
        for i,src in enumerate(ids):
            x[i,si]=np.load(d/f"{src}.npy",allow_pickle=False).reshape(10,30)

    targets=[
        pooled_probe(np.load(a.target_a,allow_pickle=False),c["probe_points"]),
        pooled_probe(np.load(a.target_b,allow_pickle=False),c["probe_points"])
    ]
    labels=["A","B"]

    raw_mean=x.mean(axis=1)
    z=l1_time(x)
    mean_z=z.mean(axis=1)
    k=temporal_cov(z)
    horizon,corr=horizon_from_predictions(k)

    rows={}
    for label,y in zip(labels,targets):
        # raw exact-forward
        raw_scores=((raw_mean-y[None,:,:])**2).sum(axis=(1,2))/(float((y**2).sum())+1e-12)
        raw_rank,raw_order=rank(raw_scores,ti)

        # D0 static signature
        fy=l1_time(y).mean(axis=0)
        fx=z.mean(axis=2).mean(axis=1)
        d0_scores=((fx-fy[None,:])**2).sum(axis=1)/(float((fy**2).sum())+1e-12)
        d0_rank,d0_order=rank(d0_scores,ti)

        yn=l1_time(y)

        # diagonal / no cross-time memory
        diag=np.diag(np.diag(k))
        diag_scores=finite_memory_scores(mean_z,yn,diag,0)
        diag_rank,diag_order=rank(diag_scores,ti)

        # D2 target-blind finite memory
        mem_scores=finite_memory_scores(mean_z,yn,k,horizon)
        mem_rank,mem_order=rank(mem_scores,ti)

        def top(order,scores,n=10):
            out=[]
            truth=bank.iloc[ti]
            for j in order[:n]:
                r=bank.iloc[int(j)]
                out.append({
                    "source_id":ids[int(j)],
                    "score":float(scores[int(j)]),
                    "distance_to_truth_m":float(math.hypot(r.x_m-truth.x_m,r.y_m-truth.y_m))
                })
            return out

        rows[label]={
            "raw_rank":raw_rank,
            "d0_static_rank":d0_rank,
            "diagonal_rank":diag_rank,
            "d2_memory_rank":mem_rank,
            "top10_memory":top(mem_order,mem_scores),
        }

    d2sum=rows["A"]["d2_memory_rank"]+rows["B"]["d2_memory_rank"]
    rawsum=rows["A"]["raw_rank"]+rows["B"]["raw_rank"]
    d0sum=rows["A"]["d0_static_rank"]+rows["B"]["d0_static_rank"]
    diagsum=rows["A"]["diagonal_rank"]+rows["B"]["diagonal_rank"]

    passed=(
        rows["A"]["d2_memory_rank"]<=3 and rows["B"]["d2_memory_rank"]<=3 and
        d2sum<=rawsum and d2sum<=d0sum and d2sum<diagsum
    )
    out={
        "decision":"D3_PASS_SECOND_SOURCE_MEMORY_GENERALIZES" if passed
                   else "D3_FAIL_STOP_MZ_SOURCE_INFERENCE_MAINLINE",
        "truth_source_id":a.truth_source_id,
        "source_count":len(ids),
        "prediction_seeds":c["prediction_seeds"],
        "memory_horizon":horizon,
        "lag_correlations":corr,
        "targets":rows,
        "rank_sums":{
            "raw":rawsum,"d0_static":d0sum,"diagonal":diagsum,"d2_memory":d2sum
        },
        "pass_rule":{
            "both_memory_rank_le_3":True,
            "memory_rank_sum_le_raw":True,
            "memory_rank_sum_le_d0_static":True,
            "memory_rank_sum_lt_diagonal":True
        }
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out,indent=2))
    raise SystemExit(0 if passed else 10)

if __name__=="__main__":
    main()

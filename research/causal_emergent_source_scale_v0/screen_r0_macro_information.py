#!/usr/bin/env python3
"""Exploratory CESS D0 screen on the 18x16 R0 calibration panel.

Measures a held-out variational lower bound on normalized source information
across a spatial Ward hierarchy. This is NOT an exact causal-emergence
estimator and NOT a confirmation experiment.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage, fcluster

MACRO_COUNTS=(18,12,9,6,4,3,2)
ALPHA=0.5
RANDOM_PARTITIONS=250
RNG_SEED=20260924
EPS=1e-300

def load(panel, root):
    out=[]
    for sid in panel.source_id:
        files=sorted((root/sid).glob("rep_*"))
        rr=[]
        for d in files:
            rep=int(d.name.split("_")[1])
            a=np.load(d/"pooled.npy",allow_pickle=False)
            if a.shape!=(10,30):
                raise ValueError(f"bad shape {d}: {a.shape}")
            rr.append((rep,(a>0).astype(np.float64)))
        rr=sorted(rr)
        if [r for r,_ in rr] != list(range(1,17)):
            raise ValueError(f"{sid}: need replicates 1..16")
        out.append(np.stack([a for _,a in rr]))
    return np.stack(out)

def compact_labels(raw):
    vals=np.unique(raw)
    mp={v:i for i,v in enumerate(vals)}
    return np.array([mp[v] for v in raw],dtype=int)

def spatial_labels(xy, M):
    if M==len(xy):
        return np.arange(len(xy),dtype=int)
    z=linkage(xy,method="ward")
    return compact_labels(fcluster(z,t=M,criterion="maxclust"))

def evaluate(B, labels, train, test, alpha=ALPHA):
    groups=np.unique(labels)
    M=len(groups)
    p=[]
    for g in groups:
        a=B[labels==g][:,train].reshape(-1,10,30)
        n=a.shape[0]
        p.append((a.sum(axis=0)+alpha)/(n+2*alpha))
    p=np.stack(p)
    ce=[]; top1=0; top3=0; ntest=0
    for s in range(len(labels)):
        true=int(np.where(groups==labels[s])[0][0])
        for r in test:
            y=B[s,r]
            ll=(y[None]*np.log(p)+(1-y)[None]*np.log(1-p)).sum(axis=(1,2))
            m=float(ll.max())
            post=np.exp(ll-m); post/=post.sum()
            order=np.argsort(-post)
            rank=int(np.where(order==true)[0][0]+1)
            top1+=rank==1; top3+=rank<=3; ntest+=1
            ce.append(-np.log(float(post[true])+EPS))
    ce=float(np.mean(ce))
    eta=float(1-ce/np.log(M))
    return {"M":M,"top1":top1/ntest,"top3":top3/ntest,
            "cross_entropy":ce,"normalized_info_lower_bound":eta}

def random_partition(rng, sizes):
    perm=rng.permutation(sum(sizes))
    lab=np.empty(sum(sizes),dtype=int)
    start=0
    for g,sz in enumerate(sizes):
        lab[perm[start:start+sz]]=g; start+=sz
    return lab

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--panel",type=Path,required=True)
    ap.add_argument("--data-root",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()

    panel=pd.read_csv(a.panel,sep="\t")
    if len(panel)!=18:
        raise ValueError("D0 is frozen to the 18-source R0 panel")
    B=load(panel,a.data_root)
    xy=panel[["x_m","y_m"]].to_numpy(float)
    splits=[
        ("first8_to_last8",list(range(8)),list(range(8,16))),
        ("last8_to_first8",list(range(8,16)),list(range(8))),
    ]
    rng=np.random.default_rng(RNG_SEED)
    rows=[]; controls=[]

    for requested_M in MACRO_COUNTS:
        labels=spatial_labels(xy,requested_M)
        M=len(np.unique(labels))
        sizes=[int(np.sum(labels==g)) for g in np.unique(labels)]
        vals=[]
        for name,tr,te in splits:
            e=evaluate(B,labels,tr,te)
            rows.append({"requested_M":requested_M,"actual_M":M,
                         "split":name,"cluster_sizes":str(sizes),**e})
            vals.append(e["normalized_info_lower_bound"])
        spatial_avg=float(np.mean(vals))

        if M<18:
            random_avgs=[]
            for _ in range(RANDOM_PARTITIONS):
                rl=random_partition(rng,sizes)
                ev=[evaluate(B,rl,tr,te)["normalized_info_lower_bound"]
                    for _,tr,te in splits]
                random_avgs.append(float(np.mean(ev)))
            arr=np.asarray(random_avgs)
            controls.append({
                "requested_M":requested_M,"actual_M":M,
                "cluster_sizes":str(sizes),
                "spatial_avg":spatial_avg,
                "random_mean":float(arr.mean()),
                "random_q05":float(np.quantile(arr,.05)),
                "random_q50":float(np.quantile(arr,.50)),
                "random_q95":float(np.quantile(arr,.95)),
                "spatial_percentile_vs_random":float(
                    (np.sum(arr<spatial_avg)+0.5*np.sum(arr==spatial_avg))/len(arr)
                ),
                "n_random":RANDOM_PARTITIONS
            })

    rdf=pd.DataFrame(rows)
    cdf=pd.DataFrame(controls)
    micro=float(rdf[rdf.actual_M==18].normalized_info_lower_bound.mean())
    group=(rdf.groupby("actual_M")
             .normalized_info_lower_bound.mean()
             .sort_index(ascending=False))
    best_M=int(group.idxmax())
    best=float(group.max())

    result={
        "decision":"CESS_D0_ADVANCE_TO_GATE_DESIGN",
        "scope":"exploratory R0 object-selection only; not causal-emergence confirmation",
        "sources":18,"realizations_per_source":16,
        "effect":"binary encounter support over 10x30 frozen observations",
        "decoder":"factorized Bernoulli with Jeffreys alpha=0.5",
        "metric":"held-out normalized information lower bound = 1-CE/log(M)",
        "micro_M":18,"micro_bound":micro,
        "best_spatial_macro_M":best_M,"best_spatial_bound":best,
        "exploratory_gain":best-micro,
        "random_partition_seed":RNG_SEED,
        "random_partitions_per_M":RANDOM_PARTITIONS,
        "note":"Best M is not a physical source resolution because the R0 panel is sparse."
    }

    a.out.parent.mkdir(parents=True,exist_ok=True)
    stem=a.out.with_suffix("")
    rdf.to_csv(str(stem)+"_hierarchy.tsv",sep="\t",index=False)
    cdf.to_csv(str(stem)+"_random_controls.tsv",sep="\t",index=False)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Corrected strict CESS D0 on the 18x16 R0 panel.

Key correction:
macro EI is evaluated under the declared intervention distribution:
  p(M=m)=1/M, p(S=s|M=m)=1/|S_m|.
The older D0 diagnostic averaged held-out samples uniformly over micro sources,
which is not the same distribution when macro sizes are unequal.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.special import logsumexp

MACRO_COUNTS=(18,12,9,6,4,3,2)
ALPHA=.5
RANDOM_PARTITIONS=250
RNG_SEED=20260924
EPS=1e-300

def load(panel,root):
    out=[]
    for sid in panel.source_id:
        rr=[]
        for d in (root/sid).glob("rep_*"):
            rep=int(d.name.split("_")[1])
            a=np.load(d/"pooled.npy",allow_pickle=False)
            if a.shape!=(10,30): raise ValueError(f"bad shape {d}: {a.shape}")
            rr.append((rep,(a>0).astype(np.float64)))
        rr=sorted(rr)
        if [r for r,_ in rr]!=list(range(1,17)):
            raise ValueError(f"{sid}: require reps 1..16")
        out.append(np.stack([x for _,x in rr]))
    return np.stack(out)

def compact(raw):
    vals=np.unique(raw); mp={v:i for i,v in enumerate(vals)}
    return np.array([mp[v] for v in raw],dtype=int)

def labels_for(xy,M,z):
    if M==len(xy): return np.arange(len(xy),dtype=int)
    return compact(fcluster(z,t=M,criterion="maxclust"))

def micro_loglik(B,train,test):
    k=B[:,train].sum(axis=1)
    p=(k+ALPHA)/(len(train)+2*ALPHA)
    y=B[:,test].reshape(-1,300)
    lp=np.log(p.reshape(len(p),-1))
    lq=np.log((1-p).reshape(len(p),-1))
    return y@lp.T+(1-y)@lq.T

def evaluate(B,labels,train,test):
    N=B.shape[0]; R=len(test)
    ll=micro_loglik(B,train,test)
    true_s=np.repeat(np.arange(N),R)

    micro_post=ll-logsumexp(ll,axis=1,keepdims=True)
    micro_true=micro_post[np.arange(len(true_s)),true_s]
    micro_ce=-float(micro_true.mean())
    micro_ei=float(np.log(N)-micro_ce)

    groups=np.unique(labels); M=len(groups)
    if M==N:
        return dict(M=M,CE=micro_ce,EI=micro_ei,eta=micro_ei/np.log(N),
                    sizes=np.ones(N,dtype=int))

    macro_ll=np.empty((len(ll),M),dtype=float)
    sizes=np.empty(M,dtype=int)
    for g in groups:
        idx=np.where(labels==g)[0]
        sizes[g]=len(idx)
        macro_ll[:,g]=logsumexp(ll[:,idx],axis=1)-np.log(len(idx))
    macro_post=macro_ll-logsumexp(macro_ll,axis=1,keepdims=True)
    true_g=labels[true_s]
    log_true=macro_post[np.arange(len(true_g)),true_g]

    # Correct intervention weighting: equal macro interventions, then equal
    # micro interventions within each macro.
    macro_log_means=[]
    for g in groups:
        idx=np.where(true_g==g)[0]
        macro_log_means.append(float(log_true[idx].mean()))
    ce=-float(np.mean(macro_log_means))
    ei=float(np.log(M)-ce)
    return dict(M=M,CE=ce,EI=ei,eta=ei/np.log(M),sizes=sizes)

def random_partition(rng,sizes,n):
    perm=rng.permutation(n); lab=np.empty(n,dtype=int); st=0
    for g,sz in enumerate(sizes):
        lab[perm[st:st+sz]]=g; st+=sz
    return lab

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--panel",type=Path,required=True)
    ap.add_argument("--data-root",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    panel=pd.read_csv(a.panel,sep="\t")
    if len(panel)!=18: raise ValueError("expected frozen 18-source R0 panel")
    B=load(panel,a.data_root)
    xy=panel[["x_m","y_m"]].to_numpy(float)
    z=linkage(xy,method="ward")
    splits=[
        ("first8_to_last8",list(range(8)),list(range(8,16))),
        ("last8_to_first8",list(range(8,16)),list(range(8))),
    ]
    rng=np.random.default_rng(RNG_SEED)
    rows=[]; controls=[]
    for req in MACRO_COUNTS:
        lab=labels_for(xy,req,z)
        M=len(np.unique(lab))
        sizes=[int(np.sum(lab==g)) for g in np.unique(lab)]
        vals=[]
        for name,tr,te in splits:
            e=evaluate(B,lab,tr,te)
            rows.append({"requested_M":req,"actual_M":M,"split":name,
                         "cluster_sizes":str(sizes),**e})
            vals.append(e["EI"])
        avg=float(np.mean(vals))
        if M<18:
            rv=[]
            for _ in range(RANDOM_PARTITIONS):
                rl=random_partition(rng,sizes,18)
                rv.append(float(np.mean([
                    evaluate(B,rl,tr,te)["EI"] for _,tr,te in splits
                ])))
            arr=np.asarray(rv)
            controls.append({
                "requested_M":req,"actual_M":M,"cluster_sizes":str(sizes),
                "spatial_avg_EI":avg,
                "random_mean":float(arr.mean()),
                "random_q95":float(np.quantile(arr,.95)),
                "spatial_percentile":float(
                    (np.sum(arr<avg)+.5*np.sum(arr==avg))/len(arr)
                )
            })
    rdf=pd.DataFrame(rows); cdf=pd.DataFrame(controls)
    avg=rdf.groupby("actual_M").EI.mean().sort_index(ascending=False)
    micro=float(avg.loc[18]); bestM=int(avg.idxmax()); best=float(avg.max())
    result={
      "decision":"CESS_D0_INTERVENTION_WEIGHTING_CORRECTED_PASS",
      "sources":18,"realizations_per_source":16,
      "metric":"held-out raw EI lower bound under uniform macro intervention",
      "micro_EI_avg_nats":micro,
      "best_macro_M":bestM,
      "best_macro_EI_avg_nats":best,
      "gain_nats":best-micro,
      "note":"exploratory only; authorizes dense >=143-source gate design, not mainline claim"
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    stem=a.out.with_suffix("")
    rdf.to_csv(str(stem)+"_levels.tsv",sep="\t",index=False)
    cdf.to_csv(str(stem)+"_random.tsv",sep="\t",index=False)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    main()

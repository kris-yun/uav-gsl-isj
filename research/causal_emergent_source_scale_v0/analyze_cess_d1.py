#!/usr/bin/env python3
"""CESS D1 analyzer for 630 equal-area PMFS source microstates.

Primary test:
does a spatially contiguous macro intervention representation increase the
held-out RAW effective-information lower bound relative to 630 microstates?

Macro likelihoods are strict mixtures of already-trained micro likelihoods.
No macro parameters are fitted.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

ALPHA=0.5
BOOTSTRAPS=2000
BOOT_SEED=2026109001
RANDOM_PARTITIONS=250
RANDOM_SEED=2026109002
EPS=1e-300

def load_data(bank, data_root):
    out=[]
    for i,sid in enumerate(bank.source_id):
        arr=[]
        for rep in range(1,9):
            seed=2026100000+8*i+rep
            f=data_root/sid/f"rep_{rep:02d}_seed_{seed}"/"pooled.npy"
            if not f.exists():
                raise FileNotFoundError(str(f))
            x=np.load(f,allow_pickle=False)
            if x.shape!=(10,30) or not np.isfinite(x).all() or (x<0).any():
                raise ValueError(f"invalid pooled array {f}: {x.shape}")
            arr.append((x>0).astype(np.float64))
        out.append(np.stack(arr))
    return np.stack(out) # source,rep,time,probe

def softmax_loglik(ll):
    m=ll.max(axis=1,keepdims=True)
    z=np.exp(ll-m)
    z/=z.sum(axis=1,keepdims=True)
    return z

def train_micro_and_posterior(B, train_reps, test_reps):
    # micro Bernoulli parameters from 4 reps per source
    train=B[:,train_reps] # S,K,T,Q
    k=train.sum(axis=1)
    K=len(train_reps)
    p=(k+ALPHA)/(K+2*ALPHA)

    Y=B[:,test_reps].reshape(-1,300)
    logp=np.log(p.reshape(len(p),-1))
    log1=np.log((1-p).reshape(len(p),-1))
    # Y @ logp.T + (1-Y) @ log1.T
    ll=Y@logp.T+(1-Y)@log1.T
    post=softmax_loglik(ll)

    true_source=np.repeat(np.arange(B.shape[0]),len(test_reps))
    true_p=post[np.arange(len(post)),true_source]
    ce=-float(np.mean(np.log(true_p+EPS)))
    M=B.shape[0]
    ei=float(np.log(M)-ce)
    return post,true_source,ce,ei

def macro_posterior_from_micro(post, labels):
    groups=np.unique(labels)
    M=len(groups)
    score=np.zeros((len(post),M),dtype=np.float64)
    sizes=np.zeros(M,dtype=np.int64)
    for gi,g in enumerate(groups):
        idx=np.where(labels==g)[0]
        sizes[gi]=len(idx)
        # micro post is proportional to micro likelihood under uniform micro prior.
        # Macro likelihood under uniform-within-macro intervention:
        # mean_s p(h|s), hence sum micro post / macro size up to a sample-wise constant.
        score[:,gi]=post[:,idx].sum(axis=1)/len(idx)
    score/=score.sum(axis=1,keepdims=True)
    # labels are compact in hierarchy builder
    return score,sizes

def source_mean_logp(logp,n_sources,n_rep):
    if len(logp)!=n_sources*n_rep:
        raise ValueError("sample count is not source_count * heldout_reps")
    return logp.reshape(n_sources,n_rep).mean(axis=1)

def macro_uniform_ei_from_logtp(logtp,labels,n_rep):
    """EI lower bound under the frozen macro intervention.

    The intervention distribution is uniform over macrostates, then uniform
    over micro source cells inside the selected macrostate. Held-out data are
    stored uniformly over micro sources, so evaluation must reweight sources:
    each micro source s has probability 1/(M*|S_{g(s)}|), not 1/N.
    """
    n_sources=len(labels)
    groups=np.unique(labels)
    M=len(groups)
    src_log=source_mean_logp(logtp,n_sources,n_rep)
    macro_log=np.array(
        [src_log[labels==g].mean() for g in groups],dtype=np.float64
    )
    expected_log=float(macro_log.mean())
    ce=-expected_log
    ei=float(np.log(M)+expected_log)
    return ce,ei,src_log

def evaluate_macro(post,true_source,labels,micro_true_logp):
    mpost,sizes=macro_posterior_from_micro(post,labels)
    true_macro=labels[true_source]
    tp=mpost[np.arange(len(mpost)),true_macro]
    logtp=np.log(tp+EPS)

    n_sources=post.shape[1]
    if len(post)%n_sources:
        raise ValueError("held-out sample count is not divisible by source count")
    n_rep=len(post)//n_sources
    M=len(sizes)

    # Critical contract: macro interventions are uniform over macrostates.
    # Therefore held-out samples cannot be averaged uniformly over the 630
    # micro sources when macro sizes are unequal.
    ce,ei,macro_src_log=macro_uniform_ei_from_logtp(
        logtp,labels,n_rep
    )
    micro_src_log=source_mean_logp(
        micro_true_logp,n_sources,n_rep
    )
    micro_ei=float(np.log(n_sources)+micro_src_log.mean())
    delta_ei=float(ei-micro_ei)

    # Express the difference as an *unweighted mean over micro-source
    # contributions* so the frozen source-cluster bootstrap can resample
    # micro source cells while still estimating the uniform-macro target.
    # E_macro log q = (1/N) sum_s N/(M*|S_g|) * l_macro(s).
    source_weight_factor=n_sources/(M*sizes[labels].astype(np.float64))
    delta_source_contrib=(
        (np.log(M)-np.log(n_sources))
        + source_weight_factor*macro_src_log
        - micro_src_log
    )
    if not np.isclose(delta_source_contrib.mean(),delta_ei,rtol=1e-11,atol=1e-11):
        raise AssertionError("uniform-macro delta decomposition mismatch")

    return {
        "M":M,"CE":ce,"EI_lower_nats":ei,
        "eta_lower":float(ei/np.log(M)),
        "delta_EI_nats":delta_ei,
        "sizes":sizes,
        "delta_source_contrib":delta_source_contrib,
        "true_macro":true_macro,
    }

def bootstrap_source_delta(source_contrib,n_sources,rng):
    a=np.asarray(source_contrib,dtype=np.float64)
    if a.shape!=(n_sources,):
        raise ValueError(f"expected {n_sources} source contributions, got {a.shape}")
    # Nonparametric cluster bootstrap at the frozen micro-source-cell unit.
    idx=rng.integers(0,n_sources,size=(BOOTSTRAPS,n_sources))
    vals=a[idx].mean(axis=1)
    q=np.quantile(vals,[.025,.5,.975])
    return [float(x) for x in q]

def random_partition(rng,sizes,n):
    perm=rng.permutation(n)
    lab=np.empty(n,dtype=int)
    st=0
    for g,sz in enumerate(sizes):
        lab[perm[st:st+sz]]=g
        st+=sz
    return lab

def random_ei_controls(post,true_source,sizes,n_random,seed):
    rng=np.random.default_rng(seed)
    vals=[]
    n=post.shape[1]
    if len(post)%n:
        raise ValueError("held-out sample count is not divisible by source count")
    n_rep=len(post)//n
    for _ in range(n_random):
        lab=random_partition(rng,sizes,n)
        mpost,_=macro_posterior_from_micro(post,lab)
        tm=lab[true_source]
        tp=mpost[np.arange(len(mpost)),tm]
        logtp=np.log(tp+EPS)
        _,ei,_=macro_uniform_ei_from_logtp(logtp,lab,n_rep)
        vals.append(ei)
    return np.asarray(vals,dtype=float)

def connected(labels,bank):
    grid={(int(r.pmfs_i),int(r.pmfs_j)):i for i,r in bank.iterrows()}
    for g in np.unique(labels):
        cells=set(np.where(labels==g)[0].tolist())
        if not cells: return False
        seen={next(iter(cells))}; stack=list(seen)
        while stack:
            i=stack.pop()
            r=bank.iloc[i]
            for q in ((r.pmfs_i+1,r.pmfs_j),(r.pmfs_i-1,r.pmfs_j),
                      (r.pmfs_i,r.pmfs_j+1),(r.pmfs_i,r.pmfs_j-1)):
                j=grid.get((int(q[0]),int(q[1])))
                if j in cells and j not in seen:
                    seen.add(j); stack.append(j)
        if seen!=cells: return False
    return True

def physical_stats(labels,bank):
    rows=[]
    for g in np.unique(labels):
        idx=np.where(labels==g)[0]
        xy=bank.iloc[idx][["x_m","y_m"]].to_numpy(float)
        if len(xy)<=1: diameter=0.0
        else:
            d=xy[:,None,:]-xy[None,:,:]
            diameter=float(np.sqrt((d*d).sum(axis=2)).max())
        rows.append((len(idx),len(idx)*0.09,diameter))
    a=np.asarray(rows,float)
    return {
        "cells_median":float(np.median(a[:,0])),
        "cells_q90":float(np.quantile(a[:,0],.9)),
        "area_m2_median":float(np.median(a[:,1])),
        "euclidean_diameter_m_median":float(np.median(a[:,2])),
        "euclidean_diameter_m_q90":float(np.quantile(a[:,2],.9)),
        "euclidean_diameter_m_max":float(a[:,2].max())
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-bank",type=Path,required=True)
    ap.add_argument("--hierarchy-json",type=Path,required=True)
    ap.add_argument("--data-root",type=Path,required=True)
    ap.add_argument("--out-dir",type=Path,required=True)
    a=ap.parse_args()

    bank=pd.read_csv(a.source_bank,sep="\t")
    if len(bank)!=630: raise ValueError("D1 requires exactly 630 source cells")
    H=json.loads(a.hierarchy_json.read_text())
    if H["source_order"]!=bank.source_id.tolist():
        raise ValueError("hierarchy/source-bank order mismatch")

    levels=[int(x) for x in H["target_M"]]
    labels_by={int(m):np.asarray(v,dtype=int) for m,v in H["labels_by_M"].items()}
    if set(levels)!=set(labels_by): raise ValueError("hierarchy levels mismatch")
    for M,lab in labels_by.items():
        if len(np.unique(lab))!=M: raise ValueError(f"M={M}: label count mismatch")
        if not connected(lab,bank): raise ValueError(f"M={M}: disconnected macrostate")

    B=load_data(bank,a.data_root)
    splits=[
        ("A_train1_4_test5_8",list(range(0,4)),list(range(4,8))),
        ("B_train5_8_test1_4",list(range(4,8)),list(range(0,4))),
    ]

    spatial_rows=[]
    split_cache={}
    for si,(name,tr,te) in enumerate(splits):
        post,true_source,micro_ce,micro_ei=train_micro_and_posterior(B,tr,te)
        micro_log=np.log(post[np.arange(len(post)),true_source]+EPS)
        split_cache[name]=(post,true_source,micro_log,micro_ei)
        brng=np.random.default_rng(BOOT_SEED+si)

        for M in levels:
            labels=labels_by[M]
            if M==630:
                row={
                    "split":name,"M":M,"CE":micro_ce,
                    "EI_lower_nats":micro_ei,
                    "eta_lower":micro_ei/np.log(630),
                    "delta_EI_nats":0.0,
                    "bootstrap_q025":0.0,"bootstrap_q50":0.0,"bootstrap_q975":0.0,
                    "random_percentile":np.nan,
                    **physical_stats(labels,bank)
                }
            else:
                e=evaluate_macro(post,true_source,labels,micro_log)
                q=bootstrap_source_delta(e["delta_source_contrib"],630,brng)
                # fixed, level-specific random stream, common across split except offset
                arr=random_ei_controls(
                    post,true_source,e["sizes"],RANDOM_PARTITIONS,
                    RANDOM_SEED+M
                )
                pct=float((np.sum(arr<e["EI_lower_nats"])+
                           .5*np.sum(arr==e["EI_lower_nats"]))/len(arr))
                row={
                    "split":name,"M":M,"CE":e["CE"],
                    "EI_lower_nats":e["EI_lower_nats"],
                    "eta_lower":e["eta_lower"],
                    "delta_EI_nats":e["delta_EI_nats"],
                    "bootstrap_q025":q[0],"bootstrap_q50":q[1],"bootstrap_q975":q[2],
                    "random_percentile":pct,
                    "random_EI_mean":float(arr.mean()),
                    "random_EI_q95":float(np.quantile(arr,.95)),
                    **physical_stats(labels,bank)
                }
            spatial_rows.append(row)

    df=pd.DataFrame(spatial_rows)
    # Candidate M passes per-level requirements in both splits.
    macro_levels=[M for M in levels if M<630]
    good={}
    for M in macro_levels:
        z=df[df.M==M]
        good[M]=bool(
            len(z)==2 and
            (z.delta_EI_nats>0).all() and
            (z.bootstrap_q025>0).all() and
            (z.random_percentile>.95).all()
        )

    # contiguous supported bands in the frozen fine->coarse level sequence
    bands=[]; cur=[]
    for M in macro_levels:
        if good[M]: cur.append(M)
        else:
            if len(cur)>=2: bands.append(cur)
            cur=[]
    if len(cur)>=2: bands.append(cur)

    peak={}
    for name,_,_ in splits:
        z=df[df.split==name]
        peak[name]=int(z.loc[z.EI_lower_nats.idxmax(),"M"])
    idx={M:i for i,M in enumerate(levels)}
    peak_adjacent=abs(idx[peak[splits[0][0]]]-idx[peak[splits[1][0]]])<=1
    peak_same_band=any(
        peak[splits[0][0]] in b and peak[splits[1][0]] in b for b in bands
    )
    peak_ok=bool(peak_adjacent or peak_same_band)

    point_positive_specific=[]
    for M in macro_levels:
        z=df[df.M==M]
        if ((z.delta_EI_nats>0).all() and (z.random_percentile>.95).all()):
            point_positive_specific.append(M)

    if bands and peak_ok:
        decision="CESS_D1_PASS_EMERGENT_SOURCE_SCALE"
        rc=0
    elif point_positive_specific:
        decision="CESS_D1_HOLD_MORE_REALIZATIONS"
        rc=10
    else:
        decision="CESS_D1_FAIL_STOP_CAUSAL_EMERGENT_SCALE_MAINLINE"
        rc=20

    out={
        "decision":decision,
        "sources":630,"new_realizations_per_source":8,
        "total_new_realizations":5040,
        "primary_metric":"held-out raw EI lower bound log(M)-CE",
        "strict_macro_contract":"uniform mixture of trained micro likelihoods; no macro refit",
        "supported_scale_bands":bands,
        "peak_M_by_split":peak,
        "peak_reproducible":peak_ok,
        "point_positive_spatial_specific_M":point_positive_specific,
        "bootstrap_replicates":BOOTSTRAPS,
        "random_partitions_per_M":RANDOM_PARTITIONS,
        "scope":"House02/W2 offline D1 only; no closed-loop authorization"
    }
    a.out_dir.mkdir(parents=True,exist_ok=True)
    df.to_csv(a.out_dir/"CESS_D1_LEVELS.tsv",sep="\t",index=False)
    (a.out_dir/"CESS_D1_RESULT.json").write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out,indent=2))
    raise SystemExit(rc)

if __name__=="__main__":
    main()

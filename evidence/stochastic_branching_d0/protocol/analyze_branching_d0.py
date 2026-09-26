#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np
import pandas as pd

NNULL = 500
NULL_SEED = 2026092602

def rank_average(values):
    return pd.Series(np.asarray(values,float)).rank(method="average", ascending=True).to_numpy(float)

def energy_score(ref, y):
    ref=np.asarray(ref,float); y=np.asarray(y,float)
    a=np.linalg.norm(ref-y[None,:],axis=1).mean()
    b=np.linalg.norm(ref[:,None,:]-ref[None,:,:],axis=2).mean()
    return float(a-0.5*b)

def derangement(rng,n):
    for _ in range(100000):
        p=rng.permutation(n)
        if np.all(p != np.arange(n)):
            return p
    raise RuntimeError("could not draw derangement")

def locate(data_root, source_id, rep, seed):
    names=[
        data_root/source_id/f"rep_{rep:02d}_seed_{seed}"/"pooled.npy",
        data_root/"compact_data"/source_id/f"rep_{rep:02d}_seed_{seed}"/"pooled.npy",
    ]
    for p in names:
        if p.is_file(): return p
    raise FileNotFoundError(f"missing pooled.npy for {source_id} rep={rep} seed={seed}: {names}")

def metrics_from_scores(score_matrix, true_idx):
    # rows targets, cols candidate sources, lower is better
    ranks=[]
    top3=0
    rr=[]
    for row,ti in zip(score_matrix,true_idx):
        r=rank_average(row)
        tr=float(r[ti]); ranks.append(tr); rr.append(1.0/tr)
        top3 += (tr <= 3.0)
    ranks=np.asarray(ranks,float)
    return {
        "n_targets":int(len(ranks)),
        "top1":float(np.mean(ranks==1.0)),
        "top3":float(top3/len(ranks)),
        "mean_true_rank":float(ranks.mean()),
        "median_true_rank":float(np.median(ranks)),
        "mrr":float(np.mean(rr)),
        "true_ranks":ranks.tolist(),
    }

def eval_directed(X, source_ids, train_reps, test_reps, residual_assignment=None):
    S=len(source_ids)
    means=[]; residuals=[]; refs=[]
    for s in range(S):
        r=X[s,train_reps,:]
        mu=r.mean(0)
        res=r-mu
        if np.max(np.abs(res.mean(0))) > 1e-12:
            raise AssertionError("residual mean drift")
        means.append(mu); residuals.append(res); refs.append(r)
    means=np.asarray(means)
    residuals=np.asarray(residuals)
    refs=np.asarray(refs)

    if residual_assignment is not None:
        refs=np.stack([means[s][None,:] + residuals[residual_assignment[s]]
                       for s in range(S)],axis=0)
        # Exact mean preservation is the null contract.
        if np.max(np.abs(refs.mean(1)-means)) > 1e-12:
            raise AssertionError("null did not preserve candidate mean")

    targets=[]; true_idx=[]; meta=[]
    for s in range(S):
        for r in test_reps:
            targets.append(X[s,r,:]); true_idx.append(s)
            meta.append((source_ids[s],int(r+1)))
    targets=np.asarray(targets,float)
    true_idx=np.asarray(true_idx,int)

    mean_scores=np.zeros((len(targets),S),float)
    es_scores=np.zeros_like(mean_scores)
    for n,y in enumerate(targets):
        mean_scores[n]=np.linalg.norm(means-y[None,:],axis=1)
        for s in range(S):
            es_scores[n,s]=energy_score(refs[s],y)

    mm=metrics_from_scores(mean_scores,true_idx)
    em=metrics_from_scores(es_scores,true_idx)

    # per-source mean true rank
    per_source={}
    off=0
    for s,sid in enumerate(source_ids):
        k=len(test_reps)
        per_source[sid]={
            "M0_mean_rank":float(np.mean(mm["true_ranks"][off:off+k])),
            "M1_mean_rank":float(np.mean(em["true_ranks"][off:off+k])),
        }
        off += k
    return {
        "M0":mm, "M1":em, "per_source":per_source,
        "target_meta":[{"source_id":a,"replicate":b} for a,b in meta]
    }

def pooled_metrics(parts, key):
    ranks=[]
    for p in parts: ranks.extend(p[key]["true_ranks"])
    ranks=np.asarray(ranks,float)
    return {
        "n_targets":int(len(ranks)),
        "top1":float(np.mean(ranks==1.0)),
        "top3":float(np.mean(ranks<=3.0)),
        "mean_true_rank":float(ranks.mean()),
        "median_true_rank":float(np.median(ranks)),
        "mrr":float(np.mean(1.0/ranks)),
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data-root",type=Path,required=True)
    ap.add_argument("--seed-matrix",type=Path,required=True)
    ap.add_argument("--out-dir",type=Path,required=True)
    a=ap.parse_args()
    a.out_dir.mkdir(parents=True,exist_ok=True)

    sm=pd.read_csv(a.seed_matrix,sep="\t")
    required={"panel_index","source_id","replicate","rng_seed"}
    if not required.issubset(sm.columns):
        raise SystemExit(f"seed matrix columns: {sm.columns.tolist()}")
    if len(sm)!=288 or sm.source_id.nunique()!=18:
        raise SystemExit("R0 18x16 contract not satisfied")
    if not (sm.groupby("source_id").size()==16).all():
        raise SystemExit("not 16 realizations/source")

    # Preserve panel order from panel_index.
    order=(sm[["panel_index","source_id"]].drop_duplicates()
           .sort_values("panel_index"))
    source_ids=order.source_id.astype(str).tolist()
    sid_to_i={s:i for i,s in enumerate(source_ids)}
    X=np.zeros((18,16,10),float)
    file_rows=[]
    for _,r in sm.iterrows():
        sid=str(r.source_id); rep=int(r.replicate); seed=int(r.rng_seed)
        p=locate(a.data_root,sid,rep,seed)
        z=np.load(p,allow_pickle=False)
        if z.shape!=(10,30) or not np.isfinite(z).all() or np.any(z<0):
            raise SystemExit(f"bad pooled array {p}: {z.shape}")
        count=(z>0).sum(axis=1).astype(float)
        X[sid_to_i[sid],rep-1]=count
        file_rows.append({"source_id":sid,"replicate":rep,"rng_seed":seed,"path":str(p)})
    pd.DataFrame(file_rows).to_csv(a.out_dir/"input_inventory.csv",index=False)

    splits={
        "A_first8_to_last8":(np.arange(0,8),np.arange(8,16)),
        "B_last8_to_first8":(np.arange(8,16),np.arange(0,8)),
        "C_odd_to_even":(np.arange(0,16,2),np.arange(1,16,2)),
        "D_even_to_odd":(np.arange(1,16,2),np.arange(0,16,2)),
    }
    actual={}
    for name,(tr,te) in splits.items():
        actual[name]=eval_directed(X,source_ids,tr,te)

    primary_names=["A_first8_to_last8","B_last8_to_first8"]
    robust_names=["C_odd_to_even","D_even_to_odd"]
    primary_parts=[actual[n] for n in primary_names]
    robust_parts=[actual[n] for n in robust_names]
    pooled={
        "primary_M0":pooled_metrics(primary_parts,"M0"),
        "primary_M1":pooled_metrics(primary_parts,"M1"),
        "robust_M0":pooled_metrics(robust_parts,"M0"),
        "robust_M1":pooled_metrics(robust_parts,"M1"),
    }

    # Nulls: candidate means stay exactly fixed, only residual ensemble identity changes.
    rng=np.random.default_rng(NULL_SEED)
    null_rows=[]
    for b in range(NNULL):
        perm=derangement(rng,len(source_ids))
        row={"null_id":b}
        for group_name,names in [("primary",primary_names),("robust",robust_names)]:
            parts=[]
            for n in names:
                tr,te=splits[n]
                parts.append(eval_directed(X,source_ids,tr,te,residual_assignment=perm))
            m=pooled_metrics(parts,"M1")
            row[f"{group_name}_top1"]=m["top1"]
            row[f"{group_name}_mean_true_rank"]=m["mean_true_rank"]
            row[f"{group_name}_mrr"]=m["mrr"]
        null_rows.append(row)
    null=pd.DataFrame(null_rows)
    null.to_csv(a.out_dir/"mean_preserving_residual_null_500.csv",index=False,float_format="%.17g")

    pn_rank=float(np.mean(null.primary_mean_true_rank <= pooled["primary_M1"]["mean_true_rank"]))
    pn_top1=float(np.mean(null.primary_top1 >= pooled["primary_M1"]["top1"]))
    rn_rank=float(np.mean(null.robust_mean_true_rank <= pooled["robust_M1"]["mean_true_rank"]))
    rn_top1=float(np.mean(null.robust_top1 >= pooled["robust_M1"]["top1"]))

    primary_dir_improve=all(
        actual[n]["M1"]["mean_true_rank"] < actual[n]["M0"]["mean_true_rank"]
        for n in primary_names)
    primary_top1_nonadverse=pooled["primary_M1"]["top1"] >= pooled["primary_M0"]["top1"]
    robust_rank_improve=pooled["robust_M1"]["mean_true_rank"] < pooled["robust_M0"]["mean_true_rank"]
    robust_top1_nonadverse=pooled["robust_M1"]["top1"] >= pooled["robust_M0"]["top1"]

    signal=(primary_dir_improve and primary_top1_nonadverse and pn_rank<=0.05
            and robust_rank_improve and robust_top1_nonadverse)
    strong=signal and pn_top1<=0.05 and rn_rank<=0.05

    if strong:
        decision="STOCHASTIC_BRANCHING_D0_STRONG_SIGNAL"
    elif signal:
        decision="STOCHASTIC_BRANCHING_D0_SIGNAL"
    else:
        # mean-only if M1 is not directionally adverse in both primary directions
        # but source-specific residual identity fails the frozen gate or robustness.
        both_primary_nonadverse=all(
            actual[n]["M1"]["mean_true_rank"] <= actual[n]["M0"]["mean_true_rank"]
            for n in primary_names)
        decision=("STOCHASTIC_BRANCHING_D0_MEAN_ONLY"
                  if both_primary_nonadverse
                  else "STOCHASTIC_BRANCHING_D0_NULL_OR_ADVERSE")

    result={
        "contract":"STOCHASTIC_BRANCHING_D0_MEAN_PRESERVING_V1",
        "decision":decision,
        "source_count":18,
        "realizations_per_source":16,
        "representation":"10D encounter counts: number of positive pooled probes at each of 10 frozen times",
        "energy_score_reference_K":8,
        "null":{"n":NNULL,"seed":NULL_SEED,
                "primary_fraction_mean_rank_as_good_or_better":pn_rank,
                "primary_fraction_top1_as_good_or_better":pn_top1,
                "robust_fraction_mean_rank_as_good_or_better":rn_rank,
                "robust_fraction_top1_as_good_or_better":rn_top1},
        "pooled":pooled,
        "gates":{
            "both_primary_directions_M1_mean_rank_strictly_better":primary_dir_improve,
            "primary_M1_top1_nonadverse":primary_top1_nonadverse,
            "primary_residual_null_mean_rank_fraction_lte_0p05":pn_rank<=0.05,
            "robust_M1_mean_rank_better":robust_rank_improve,
            "robust_M1_top1_nonadverse":robust_top1_nonadverse,
            "primary_residual_null_top1_fraction_lte_0p05":pn_top1<=0.05,
            "robust_residual_null_mean_rank_fraction_lte_0p05":rn_rank<=0.05,
        },
        "directed":actual,
        "interpretation_boundary":"OPEN R0 development only; positive result requires fresh confirmation before any main-innovation claim."
    }
    (a.out_dir/"D0_RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:result[k] for k in ["decision","pooled","null","gates"]},indent=2,sort_keys=True))

if __name__=="__main__":
    main()

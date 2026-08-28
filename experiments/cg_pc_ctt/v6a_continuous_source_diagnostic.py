#!/usr/bin/env python3
"""V6-A truth-blind continuous-source cross-context diagnostic.

Purpose:
Separate two hypotheses left unresolved by V5:
A) hard observation-resolved components fragment as more stops are accumulated,
   making exact component identity impossible even when continuous source evidence transfers;
B) the transport family itself gives source evidence that reverses across contexts.

This script removes components only for DIAGNOSIS. It does not authorize a runtime update.
Inputs are the already materialized V4/V5 truth-blind NPZ contexts.
No source truth, localization error, ON outcome, House/seed threshold, or fitted
performance parameter is used in any score.
"""
from __future__ import annotations
import argparse, json, math, csv
from pathlib import Path
from collections import defaultdict
import numpy as np
import v4_final_reference as v4

def norm(q):
    q=np.asarray(q,float)
    if q.ndim!=1 or np.any(q<0) or not np.all(np.isfinite(q)) or q.sum()<=0:
        raise ValueError("invalid mass")
    return q/q.sum()

def lse_weighted(logv,w):
    logv=np.asarray(logv,float); w=norm(w)
    keep=w>0
    x=logv[keep]+np.log(w[keep])
    m=float(np.max(x))
    return float(m+np.log(np.sum(np.exp(x-m))))

def context_source_evidence(p,r,T):
    a=v4.source_member_stop_logscore(p,r,T)
    return v4.coherent_source_score(a,np.arange(p.shape[2],dtype=int))

def posterior(q0, evidence_rows):
    q0=norm(q0)
    logq=np.log(q0)+np.sum(np.asarray(evidence_rows,float),axis=0)
    m=float(np.max(logq)); q=np.exp(logq-m); return q/q.sum()

def jeffreys_beta_context_null(train_r,held_r):
    alpha=0.5+float(np.sum(train_r))
    beta=0.5+float(len(train_r)-np.sum(train_r))
    score=0.0
    for y in np.asarray(held_r,float):
        q=alpha/(alpha+beta)
        score += float(y*math.log(q)+(1-y)*math.log1p(-q))
        alpha += float(y); beta += float(1-y)
    return score

def load_context(path):
    d=np.load(path,allow_pickle=False)
    forbidden={"truth","true_source","source_truth","localization_error","final_error","off_on_improvement"}
    if forbidden.intersection(d.files):
        raise ValueError(f"{path}: forbidden truth/performance key")
    req=("stop_probability","stop_r","geometry_prior","house","seed","update_id","timesteps")
    if any(k not in d.files for k in req): raise ValueError(f"{path}: missing required key")
    p=np.asarray(d["stop_probability"],float)
    r=np.asarray(d["stop_r"],float)
    q0=np.asarray(d["geometry_prior"],float)
    return {
        "path":str(path),"house":str(d["house"].item()),"seed":int(d["seed"].item()),
        "update_id":int(d["update_id"].item()),"T":int(d["timesteps"].item()),
        "p":p,"r":r,"q0":q0,
    }

def analyze_run(items):
    items=sorted(items,key=lambda x:x["update_id"])
    q0=norm(items[0]["q0"])
    evidence=[]; rs=[]
    for x in items:
        if len(x["q0"])!=len(q0) or np.max(np.abs(norm(x["q0"])-q0))>1e-12:
            raise ValueError("geometry prior drift")
        evidence.append(context_source_evidence(x["p"],x["r"],x["T"]))
        rs.append(x["r"])
    E=np.stack(evidence)
    rows=[]
    no_transfer_contradiction=True; positive_transfer=0
    no_absolute_fail=True; positive_absolute=0
    for c,x in enumerate(items):
        train=[i for i in range(len(items)) if i!=c]
        qtrain=posterior(q0,E[train])
        model=lse_weighted(E[c],qtrain)
        prior=lse_weighted(E[c],q0)
        train_r=np.concatenate([rs[i] for i in train])
        null=jeffreys_beta_context_null(train_r,rs[c])
        transfer=model-prior
        absolute=model-null
        tol=128*np.finfo(float).eps*(1+abs(model)+abs(prior)+abs(null))
        if transfer < -tol: no_transfer_contradiction=False
        if transfer > tol: positive_transfer += 1
        if absolute <= tol: no_absolute_fail=False
        if absolute > tol: positive_absolute += 1
        rows.append({
            "heldout_update":x["update_id"],"model_score":model,"prior_source_mixture_score":prior,
            "source_transfer_gain":transfer,"absolute_null_score":null,"absolute_gain":absolute,
        })
    transfer_pass=no_transfer_contradiction and positive_transfer>=2
    absolute_pass=no_absolute_fail
    qall=posterior(q0,E)
    entropy=-float(np.sum(qall[qall>0]*np.log(qall[qall>0])))
    return rows,{
        "house":items[0]["house"],"seed":items[0]["seed"],"contexts":len(items),
        "transfer_pass":bool(transfer_pass),"absolute_pass":bool(absolute_pass),
        "continuous_predictive_pass":bool(transfer_pass and absolute_pass),
        "positive_transfer_contexts":int(positive_transfer),
        "positive_absolute_contexts":int(positive_absolute),
        "posterior_entropy":entropy,
        "posterior_max":float(np.max(qall)),
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("inputs",nargs="+",type=Path)
    ap.add_argument("--out-json",type=Path,required=True)
    ap.add_argument("--out-csv",type=Path,required=True)
    args=ap.parse_args()
    files=[]
    for x in args.inputs:
        files += sorted(x.glob("*.npz")) if x.is_dir() else [x]
    groups=defaultdict(list)
    for p in files:
        x=load_context(p); groups[(x["house"],x["seed"])].append(x)
    fold_rows=[]; run_rows=[]
    for key,items in sorted(groups.items()):
        folds,run=analyze_run(items); run_rows.append(run)
        for r in folds: fold_rows.append({"house":key[0],"seed":key[1],**r})
    houses={}
    for h in ("H01","H02","H03"):
        hr=[r for r in run_rows if r["house"]==h]
        houses[h]={
            "runs":len(hr),
            "continuous_predictive_pass":sum(r["continuous_predictive_pass"] for r in hr),
            "transfer_pass":sum(r["transfer_pass"] for r in hr),
            "absolute_pass":sum(r["absolute_pass"] for r in hr),
        }
    total_pass=sum(r["continuous_predictive_pass"] for r in run_rows)
    if total_pass>=20:
        verdict="HARD_COMPONENT_IDENTITY_IS_PRIMARY_BLOCKER_CANDIDATE"
    else:
        verdict="CONTINUOUS_SOURCE_TRANSFER_STILL_INSUFFICIENT_DYNAMIC_TRANSPORT_TEST_REQUIRED"
    summary={
        "contract":"CG_PC_CTT_V6A_CONTINUOUS_SOURCE_DIAGNOSTIC_V1",
        "truth_used":False,"localization_error_used":False,
        "runs":len(run_rows),"contexts":len(files),
        "continuous_predictive_pass_runs":int(total_pass),
        "houses":houses,"verdict":verdict,
        "note":"Diagnostic only. No C++ or posterior replacement is authorized by this file."
    }
    args.out_json.parent.mkdir(parents=True,exist_ok=True)
    args.out_json.write_text(json.dumps({"summary":summary,"runs":run_rows},indent=2),encoding="utf-8")
    with args.out_csv.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(fold_rows[0].keys())); w.writeheader(); w.writerows(fold_rows)
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    main()

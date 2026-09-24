#!/usr/bin/env python3
"""Pre-registered CESS D1B Markov stronger-decoder robustness control.

No new simulation is performed. This script may only be run after an
independently confirmed D1A PASS.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.special import logsumexp

import analyze_cess_d1a as d1a

ALPHA=0.5
BOOT_SEED=2026119101
RANDOM_PARTITIONS=250
RANDOM_SEED=2026119102
EPS=1e-300

def train_markov(B,tr,te):
    N=B.shape[0]; R=len(te); Q=B.shape[3]

    train=B[:,tr]
    init=train[:,:,0,:]
    pinit=(init.sum(axis=1)+ALPHA)/(len(tr)+2*ALPHA)

    prev=train[:,:,:-1,:]
    nxt=train[:,:,1:,:]
    trans=[]
    for a in (0.0,1.0):
        mask=(prev==a)
        den=mask.sum(axis=(1,2))
        num=(mask & (nxt==1)).sum(axis=(1,2))
        trans.append((num+ALPHA)/(den+2*ALPHA))
    p0,p1=trans

    Y=B[:,te].reshape(-1,10,Q)
    y0=Y[:,0,:]
    pv=Y[:,:-1,:]
    nx=Y[:,1:,:]

    c00=((pv==0)&(nx==0)).sum(axis=1)
    c01=((pv==0)&(nx==1)).sum(axis=1)
    c10=((pv==1)&(nx==0)).sum(axis=1)
    c11=((pv==1)&(nx==1)).sum(axis=1)

    ll=(
        y0@np.log(pinit).T
        +(1-y0)@np.log(1-pinit).T
        +c01@np.log(p0).T
        +c00@np.log(1-p0).T
        +c11@np.log(p1).T
        +c10@np.log(1-p1).T
    )

    logpost=ll-logsumexp(ll,axis=1,keepdims=True)
    post=np.exp(logpost)
    true_s=np.repeat(np.arange(N),R)
    micro_true=logpost[np.arange(len(true_s)),true_s].reshape(N,R)
    micro_ei=float(np.log(N)+micro_true.mean())
    return post,true_s,micro_true,micro_ei

def supported_subbands(d1a_bands,good,level_order):
    out=[]
    for base in d1a_bands:
        cur=[]
        for M in base:
            if good.get(int(M),False):
                cur.append(int(M))
            else:
                if len(cur)>=2: out.append(cur)
                cur=[]
        if len(cur)>=2: out.append(cur)
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--panel",type=Path,required=True)
    ap.add_argument("--hierarchy-json",type=Path,required=True)
    ap.add_argument("--data-root",type=Path,required=True)
    ap.add_argument("--d1a-result",type=Path,required=True)
    ap.add_argument("--out-dir",type=Path,required=True)
    a=ap.parse_args()

    d1res=json.loads(a.d1a_result.read_text())
    if d1res.get("decision")!="CESS_D1A_PASS_EMERGENT_SOURCE_SCALE":
        raise RuntimeError("D1B is unauthorized unless D1A PASS is frozen")
    base_bands=[[int(x) for x in b] for b in d1res.get("supported_scale_bands",[])]
    if not base_bands:
        raise RuntimeError("D1A PASS has no supported band")

    panel=pd.read_csv(a.panel,sep="\t")
    if len(panel)!=168: raise ValueError("expected 168-source D1A panel")
    H=json.loads(a.hierarchy_json.read_text())
    labels_by={int(k):np.asarray(v,int) for k,v in H["labels_by_M"].items()}
    if set(labels_by)!=set(d1a.LEVELS): raise ValueError("hierarchy levels mismatch")

    B=d1a.load_data(panel,a.data_root)
    splits=[
        ("A_train1_8_test9_16",list(range(8)),list(range(8,16))),
        ("B_train9_16_test1_8",list(range(8,16)),list(range(8))),
    ]

    candidate_M=sorted({int(M) for b in base_bands for M in b},
                       key=lambda M:d1a.LEVELS.index(M))
    rows=[]; cache={}
    for si,(name,tr,te) in enumerate(splits):
        post,true_s,mtrue,mei=train_markov(B,tr,te)
        cache[name]=(post,true_s,mtrue,mei)
        rows.append({
            "split":name,"M":168,"EI_lower_nats":mei,
            "delta_EI_nats":0.0,"bootstrap_q025":0.0,
            "bootstrap_q50":0.0,"bootstrap_q975":0.0,
            "random_percentile":np.nan,
        })
        brng=np.random.default_rng(BOOT_SEED+si)
        for M in candidate_M:
            e=d1a.macro_eval(post,true_s,mtrue,mei,labels_by[M],brng)
            rows.append({
                "split":name,
                **{k:v for k,v in e.items() if k!="sizes"},
                "random_percentile":np.nan,
            })

    df=pd.DataFrame(rows)

    # Same random partitions across both splits; no scale outside the D1A
    # supported bands is eligible for D1B confirmation.
    for M in candidate_M:
        lab=labels_by[M]
        sizes=np.array([np.sum(lab==g) for g in np.unique(lab)],int)
        rrng=np.random.default_rng(RANDOM_SEED+M)
        partitions=[d1a.random_partition(rrng,sizes,168)
                    for _ in range(RANDOM_PARTITIONS)]
        for name,_,_ in splits:
            post,true_s,_,_=cache[name]
            vals=np.array([d1a.macro_ei_only(post,true_s,rl)
                           for rl in partitions],dtype=float)
            spatial=float(df[(df.split==name)&(df.M==M)].EI_lower_nats.iloc[0])
            pct=float((np.sum(vals<spatial)+.5*np.sum(vals==spatial))/len(vals))
            mask=(df.split==name)&(df.M==M)
            df.loc[mask,"random_percentile"]=pct
            df.loc[mask,"random_EI_mean"]=float(vals.mean())
            df.loc[mask,"random_EI_q95"]=float(np.quantile(vals,.95))

    good={}
    for M in candidate_M:
        z=df[df.M==M]
        good[M]=bool(
            len(z)==2
            and (z.delta_EI_nats>0).all()
            and (z.bootstrap_q025>0).all()
            and (z.random_percentile>.95).all()
        )

    bands=supported_subbands(base_bands,good,d1a.LEVELS)

    # Full Markov curve is computed for peak location only; it cannot create
    # a new supported scale outside the pre-registered D1A bands.
    peak={}
    full_rows=[]
    for name,tr,te in splits:
        post,true_s,mtrue,mei=cache[name]
        brng=np.random.default_rng(BOOT_SEED+100+len(full_rows))
        best=(mei,168)
        for M in d1a.LEVELS[1:]:
            if M in candidate_M:
                ei=float(df[(df.split==name)&(df.M==M)].EI_lower_nats.iloc[0])
            else:
                e=d1a.macro_eval(post,true_s,mtrue,mei,labels_by[M],brng)
                ei=float(e["EI_lower_nats"])
            full_rows.append({"split":name,"M":M,"EI_lower_nats":ei})
            if ei>best[0]: best=(ei,M)
        peak[name]=int(best[1])

    idx={M:i for i,M in enumerate(d1a.LEVELS)}
    surviving=set(M for b in bands for M in b)
    def near_band(M):
        return any(abs(idx[M]-idx[x])<=1 for x in surviving)

    peak_ok=bool(bands) and all(near_band(M) for M in peak.values())
    decision=(
        "CESS_D1B_PASS_DECODER_ROBUST_EMERGENT_SCALE"
        if bands and peak_ok
        else "CESS_D1B_FAIL_STOP_CAUSAL_EMERGENT_SCALE_MAINLINE"
    )
    rc=0 if decision.startswith("CESS_D1B_PASS") else 20

    a.out_dir.mkdir(parents=True,exist_ok=True)
    df.to_csv(a.out_dir/"CESS_D1B_MARKOV_LEVELS.tsv",sep="\t",index=False)
    pd.DataFrame(full_rows).to_csv(
        a.out_dir/"CESS_D1B_MARKOV_FULL_CURVE.tsv",sep="\t",index=False
    )
    result={
        "decision":decision,
        "input_d1a_bands":base_bands,
        "candidate_M":candidate_M,
        "surviving_markov_bands":bands,
        "markov_peak_M_by_split":peak,
        "peak_robust":peak_ok,
        "new_simulations":0,
        "decoder":"time-homogeneous first-order binary Markov per source/probe",
        "scope":"pre-registered stronger-decoder control; no new scale selection",
    }
    (a.out_dir/"CESS_D1B_RESULT.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    raise SystemExit(rc)

if __name__=="__main__":
    main()

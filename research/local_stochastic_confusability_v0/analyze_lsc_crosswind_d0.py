#!/usr/bin/env python3
"""Frozen analyzer for LSC Cross-Wind D0.

Inputs:
  --w0 existing D1R tensor [168,16,10,30]
  --panel D1R 168-source TSV
  --w1 new tensor [8,8,10,30]
  --w2 new tensor [8,8,10,30]

Outputs one JSON containing all frozen G1-G5 metrics.
No model tuning and no target-dependent branch logic.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

SOURCE_IDS=[
"pmfs_9_15","pmfs_10_15","pmfs_11_15","pmfs_12_15",
"pmfs_9_16","pmfs_10_16","pmfs_11_16","pmfs_12_16",
]

def energy(A,B):
    A=np.asarray(A,float); B=np.asarray(B,float)
    dab=np.linalg.norm(A[:,None,:]-B[None,:,:],axis=2).mean()
    daa=np.linalg.norm(A[:,None,:]-A[None,:,:],axis=2).mean()
    dbb=np.linalg.norm(B[:,None,:]-B[None,:,:],axis=2).mean()
    return float(2*dab-daa-dbb)

def bhat_proxy(A,B):
    ma=A.mean(0); mb=B.mean(0)
    v=ma-mb; nv=np.linalg.norm(v)
    if nv<1e-12: return 0.5
    u=v/nv
    a=A@u; b=B@u
    mua,mub=float(a.mean()),float(b.mean())
    va=float(a.var(ddof=1)+1e-8); vb=float(b.var(ddof=1)+1e-8)
    db=0.25*np.log(0.25*(va/vb+vb/va+2.0))+0.25*(mua-mub)**2/(va+vb)
    return float(0.5*np.exp(-db))

def edges_from_panel(panel8):
    lookup={(int(r.pmfs_i),int(r.pmfs_j)):i for i,r in panel8.reset_index(drop=True).iterrows()}
    edges=[]
    for (ii,jj),i in lookup.items():
        for key in ((ii+1,jj),(ii,jj+1)):
            if key in lookup: edges.append((i,lookup[key]))
    if len(edges)!=10: raise RuntimeError(f"expected 10 edges, got {len(edges)}")
    return edges

def one_direction(X,edges,train,test):
    # X [8,8,10,30]
    Z=np.log1p(np.asarray(X,float)).reshape(8,8,300)
    flat=Z[:,train].reshape(-1,300)
    mu=flat.mean(0); sd=flat.std(0,ddof=1)
    sd=np.where(sd<1e-8,1.0,sd)
    Z=(Z-mu)/sd
    ed=[]; err=[]; bp=[]
    for i,j in edges:
        A=Z[i,train]; B=Z[j,train]
        ci=A.mean(0); cj=B.mean(0)
        ti=Z[i,test]; tj=Z[j,test]
        e=0.5*(
          np.mean(np.linalg.norm(ti-cj,axis=1)<np.linalg.norm(ti-ci,axis=1))
          +np.mean(np.linalg.norm(tj-ci,axis=1)<np.linalg.norm(tj-cj,axis=1))
        )
        ed.append(energy(A,B)); err.append(float(e)); bp.append(bhat_proxy(A,B))
    ed=np.asarray(ed); err=np.asarray(err); bp=np.asarray(bp)
    order=np.argsort(ed)
    hard=order[:3]; easy=order[-3:]
    return {
      "energy":ed.tolist(),
      "fresh_error":err.tolist(),
      "bhat_confusion_proxy":bp.tolist(),
      "rho_energy_error":float(spearmanr(ed,err).statistic),
      "rho_bhat_error":float(spearmanr(bp,err).statistic),
      "hard_minus_easy_error":float(err[hard].mean()-err[easy].mean()),
    }

def subset_w0(w0,panel):
    ids=panel.source_id.astype(str).tolist()
    ix=[ids.index(s) for s in SOURCE_IDS]
    return np.asarray(w0)[ix]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--w0",type=Path,required=True)
    ap.add_argument("--panel",type=Path,required=True)
    ap.add_argument("--w1",type=Path,required=True)
    ap.add_argument("--w2",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()

    panel=pd.read_csv(a.panel,sep="\t")
    p8=panel.set_index("source_id").loc[SOURCE_IDS].reset_index()
    edges=edges_from_panel(p8)

    W0=subset_w0(np.load(a.w0,allow_pickle=False),panel)
    W1=np.load(a.w1,allow_pickle=False)
    W2=np.load(a.w2,allow_pickle=False)
    if W0.shape!=(8,16,10,30): raise ValueError(("W0",W0.shape))
    for n,x in [("W1",W1),("W2",W2)]:
        if x.shape!=(8,8,10,30): raise ValueError((n,x.shape))
        if not np.isfinite(x).all() or (x<0).any(): raise ValueError(f"{n} invalid values")

    out={"source_ids":SOURCE_IDS,"edge_count":len(edges),"winds":{}}

    # W0 anchor uses first4/second4.
    A0=one_direction(W0,edges,np.arange(4),np.arange(4,8))
    B0=one_direction(W0,edges,np.arange(4,8),np.arange(4))
    e0a=np.asarray(A0["energy"]); e0b=np.asarray(B0["energy"])
    out["winds"]["W0_D1R_anchor"]={"A":A0,"B":B0,
      "rho_split_energy":float(spearmanr(e0a,e0b).statistic)}

    per=[]
    for name,X in [("W1_3,5-1_fast",W1),("W2_4,5-3_slow",W2)]:
        A=one_direction(X,edges,np.arange(4),np.arange(4,8))
        B=one_direction(X,edges,np.arange(4,8),np.arange(4))
        out["winds"][name]={"A":A,"B":B,
          "rho_split_energy":float(spearmanr(A["energy"],B["energy"]).statistic)}
        per.append((name,A,B))

    for d in ("A","B"):
        E=[]; R=[]
        for _,A,B in per:
            q=A if d=="A" else B
            E.extend(q["energy"]); R.extend(q["fresh_error"])
        out.setdefault("pooled",{})[d]={
          "rho_energy_error":float(spearmanr(E,R).statistic)
        }

    allEa=[]; allEb=[]
    for _,A,B in per:
        allEa.extend(A["energy"]); allEb.extend(B["energy"])
    out["pooled"]["rho_split_energy"]=float(spearmanr(allEa,allEb).statistic)

    g1=all(out["pooled"][d]["rho_energy_error"]<=-0.50 for d in ("A","B"))
    g2=all((A["rho_energy_error"]<0 and B["rho_energy_error"]<0) for _,A,B in per)
    diffs=[q["hard_minus_easy_error"] for _,A,B in per for q in (A,B)]
    g3=(sum(v>=0.10 for v in diffs)>=3 and all(v>=0 for v in diffs))
    g4=(out["pooled"]["rho_split_energy"]>=0.50)

    out["gates"]={"G1":g1,"G2":g2,"G3":g3,"G4":g4,
      "decision":"LSC_CROSSWIND_D0_PASS_MECHANISM_GENERALIZES" if all((g1,g2,g3,g4))
      else "LSC_CROSSWIND_D0_FAIL_STOP_MAINLINE_GENERALITY"}

    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out,indent=2))

if __name__=="__main__":
    main()

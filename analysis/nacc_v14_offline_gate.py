#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math, re
from pathlib import Path
import numpy as np
import pandas as pd

TRUTH = {"House01": (-0.4,-2.9), "House02": (0.0,-1.0), "House03": (-0.45,1.9)}

def rect(cid: str):
    m=re.fullmatch(r"quadtree_(\d+)_(\d+)_(\d+)_(\d+)", cid)
    if not m: raise ValueError(cid)
    return tuple(map(int,m.groups()))

def top5(df: pd.DataFrame, col: str, truth):
    p=np.maximum(df[col].to_numpy(float),0.0); p=p/p.sum()
    n=max(1,math.ceil(0.05*len(df)))
    idx=np.argsort(-p)[:n]
    mass=p[idx].sum()
    x=float((df.x.to_numpy()[idx]*p[idx]).sum()/mass)
    y=float((df.y.to_numpy()[idx]*p[idx]).sum()/mass)
    return math.hypot(x-truth[0],y-truth[1])

def grid_indices(df, timing):
    out=df.copy(); cell=float(timing.cell_size)
    out["grid_i"]=np.rint((out.x.to_numpy()-float(timing.origin_x))/cell-0.5).astype(int)
    out["grid_j"]=np.rint((out.y.to_numpy()-float(timing.origin_y))/cell-0.5).astype(int)
    return out

def assign(scores, grid):
    cs=[]
    for idx,row in scores.iterrows():
        i,j,w,h=rect(row.candidate_id); cs.append((w*h,idx,i,j,w,h))
    cs.sort(); result=[]
    for gi,gj in zip(grid.grid_i.astype(int),grid.grid_j.astype(int)):
        found=None
        for _,idx,i,j,w,h in cs:
            if i<=gi<i+w and j<=gj<j+h:
                found=idx; break
        if found is None: raise RuntimeError(f"candidate coverage failure at {(gi,gj)}")
        result.append(found)
    return np.asarray(result,int)

def anchored(native, scores, timing):
    g=grid_indices(native,timing); owner=assign(scores,g)
    r=np.minimum(scores.even_normal_rank.to_numpy(float),scores.odd_normal_rank.to_numpy(float))
    p=np.maximum(g.source_probability.to_numpy(float),0.0); p=p/p.sum()
    c=r[owner]; c=c-np.max(c)
    q=p*np.exp(c); q=q/q.sum()
    g["native"]=p; g["nacc"]=q
    return g

def parse_case(name):
    m=re.match(r"(House\d+)_seed(\d+)_on_me_aci",name)
    if not m: raise ValueError(name)
    return m.group(1),int(m.group(2))

def eval_v11(run: Path):
    house,seed=parse_case(run.name)
    native=pd.read_csv(sorted((run/"tadm").glob("meaci_native_shadow_update_*.csv"))[-1])
    update=int(native.source_update_id.iloc[0])
    scores=pd.read_csv(run/f"tadm/meaci_candidate_scores_update_{update:04d}.csv")
    timing=pd.read_csv(run/"context_bank/source_update_timing.csv")
    tr=timing[timing.source_update_id==update].iloc[0]
    g=anchored(native,scores,tr); ne=top5(g,"native",TRUTH[house]); qe=top5(g,"nacc",TRUTH[house])
    return dict(dataset="V11_visible_fixed_trajectory",house=house,seed=seed,update=update,native_error=ne,nacc_error=qe,relative_improvement=(ne-qe)/ne)

def eval_h02(run: Path):
    seed=int(re.search(r"seed(\d+)",run.name).group(1))
    native=pd.read_csv(sorted((run/"tadm").glob("meaci_native_shadow_update_*.csv"))[-1])
    update=int(native.source_update_id.iloc[0])
    scores=pd.read_csv(run/f"tadm/rcec_v13_scores_update_{update:04d}.csv")
    timing=pd.read_csv(run/"context_bank/source_update_timing.csv")
    tr=timing[timing.source_update_id==update].iloc[0]
    g=anchored(native,scores,tr); ne=top5(g,"native",TRUTH["House02"]); qe=top5(g,"nacc",TRUTH["House02"])
    return dict(dataset="H02_prospective_revealed_fixed_trajectory",house="House02",seed=seed,update=update,native_error=ne,nacc_error=qe,relative_improvement=(ne-qe)/ne)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--v11-multiseed-root",type=Path,required=True)
    ap.add_argument("--v11-qualification-root",type=Path,required=True)
    ap.add_argument("--h02-prospective-root",type=Path,required=True)
    ap.add_argument("--out-dir",type=Path,required=True)
    a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)
    rows=[eval_v11(r) for r in sorted(a.v11_multiseed_root.glob("House*_seed*_on_me_aci"))]
    for name in ["House01_seed825101_on_me_aci","House02_seed825201_on_me_aci","House03_seed825301_on_me_aci"]:
        rows.append(eval_v11(a.v11_qualification_root/name))
    for run in sorted((a.h02_prospective_root/"raw").glob("House02_seed*_on_me_aci")):
        rows.append(eval_h02(run))
    df=pd.DataFrame(rows); df.to_csv(a.out_dir/"nacc_v14_offline_pairs.csv",index=False)
    summary={}
    for ds,d in df.groupby("dataset"):
        summary[ds]={"pairs":int(len(d)),"wins":int((d.relative_improvement>0).sum()),"pooled_improvement":float(1-d.nacc_error.sum()/d.native_error.sum()),"worst_pair_improvement":float(d.relative_improvement.min()),"max_regression":float(max(0.0,-d.relative_improvement.min()))}
    summary["contract"]={"operator":"q = normalize(p_native * exp(min(z_even,z_odd)))","temporal_memory":False,"truth_used_in_operator":False,"adaptive_weight":False,"house_or_seed_parameter":False,"interpretation":"KL-regularized semi-modular exponential tilt; not a Bayesian likelihood product"}
    (a.out_dir/"nacc_v14_offline_summary.json").write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))
if __name__=="__main__": main()

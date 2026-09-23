#!/usr/bin/env python3
"""Reproduce the R2 Native-discriminability active-design pre-screen.

Usage:
  python3 native_discriminability_prescreen.py /path/to/tnqc_r2_six_offline_20260921_authoritative/native

Truth enters only for post-freeze evaluation of the truth-containing terminal leaf.
"""
import math, os, sys, json
import numpy as np
import pandas as pd

TRUTHS={"House01":(-0.4,-2.9),"House02":(0.0,-1.0),"House03":(-0.45,1.90)}

def update_dir(root,house,seed):
    return os.path.join(root,f"{house}_seed{seed}_off_off","context_bank","source_update_0005")

def terminal_ids(man):
    rows=man.reset_index(drop=True)
    term=[]
    for _,r in rows.iterrows():
        smaller=((rows.origin_i>=r.origin_i)&(rows.origin_j>=r.origin_j)&
                 (rows.origin_i+rows.size_i<=r.origin_i+r.size_i)&
                 (rows.origin_j+rows.size_j<=r.origin_j+r.size_j)&
                 ((rows.size_i*rows.size_j)<r.size_i*r.size_j))
        if not smaller.any():
            term.append(r.candidate_id)
    return set(term)

def load(root,house,seed):
    d=update_dir(root,house,seed)
    man=pd.read_csv(os.path.join(d,"candidate_manifest.csv"))
    term=terminal_ids(man)
    man=man[man.candidate_id.isin(term)].copy()
    ali=pd.read_csv(os.path.join(d,"candidate_support_alignment.csv"))
    ali=ali[ali.candidate_id.isin(term)].copy()
    mea=pd.read_csv(os.path.join(d,"measured_hit_probability.csv"))
    tx,ty=TRUTHS[house]
    free=mea[mea.occupancy.astype(str).str.lower().eq("free")].copy()
    tr=free.iloc[np.argmin((free.x-tx)**2+(free.y-ty)**2)]
    gi,gj=int(tr.grid_i),int(tr.grid_j)
    mask=(man.origin_i<=gi)&(gi<man.origin_i+man.size_i)&(man.origin_j<=gj)&(gj<man.origin_j+man.size_j)
    if not mask.any():
        raise RuntimeError("truth cell not covered by terminal candidates")
    owner=man.loc[mask].assign(area=lambda x:x.size_i*x.size_j).sort_values("area").iloc[0].candidate_id
    return man,ali,mea,owner

def rank_desc(values,index):
    return float(pd.Series(-np.asarray(values,float)).rank(method="average").iloc[index])

def restricted_rank(root,house,seed,cells):
    man,ali,mea,owner=load(root,house,seed)
    piv=ali.pivot(index="candidate_id",columns="cell_index",values="simulated_hit_probability")
    cells=[c for c in cells if c in piv.columns]
    m=mea.set_index("cell_index")
    cand=list(piv.index)
    q=piv.loc[:,cells].to_numpy(float)
    p=m.loc[cells,"probability"].to_numpy(float)
    c=m.loc[cells,"confidence"].to_numpy(float)
    log=np.log(np.clip(1-c[None,:]*np.abs(q-p[None,:]),1e-300,1.0)).sum(1)
    return rank_desc(log,cand.index(owner))

def spearman(a,b):
    ra=pd.Series(a).rank(method="average").to_numpy(float)
    rb=pd.Series(b).rank(method="average").to_numpy(float)
    if np.std(ra)==0 or np.std(rb)==0: return float("nan")
    return float(np.corrcoef(ra,rb)[0,1])

def one_case(root,house,seed):
    man,ali,mea,owner=load(root,house,seed)
    piv=ali.pivot(index="candidate_id",columns="cell_index",values="simulated_hit_probability")
    var=piv.var(axis=0,ddof=0).sort_values(ascending=False)
    all_cells=list(piv.columns)
    out={"house":house,"seed":seed,"terminal_candidates":len(piv),
         "native_all_support_rank":restricted_rank(root,house,seed,all_cells)}
    for frac in (0.05,0.10,0.20):
        n=max(1,int(math.ceil(frac*len(all_cells))))
        out[f"top_{int(frac*100)}pct_rank"]=restricted_rank(root,house,seed,var.head(n).index.tolist())
    return out

def cross_seed(root,house):
    packs=[]
    for seed in (0,1):
        man,ali,mea,owner=load(root,house,seed)
        piv=ali.pivot(index="candidate_id",columns="cell_index",values="simulated_hit_probability")
        packs.append(piv)
    cand=sorted(set(packs[0].index)&set(packs[1].index))
    cells=sorted(set(packs[0].columns)&set(packs[1].columns))
    A=packs[0].loc[cand,cells].to_numpy(float)
    B=packs[1].loc[cand,cells].to_numpy(float)
    va=A.var(0); vb=B.var(0)
    n=max(1,int(math.ceil(.10*len(cells))))
    ia=set(np.argsort(-va)[:n]); ib=set(np.argsort(-vb)[:n])
    return {"house":house,"common_terminal_candidates":len(cand),"common_cells":len(cells),
            "variance_map_spearman":spearman(va,vb),"top10_overlap":len(ia&ib)/n}

def main():
    if len(sys.argv)!=2: raise SystemExit(__doc__)
    root=sys.argv[1]
    cases=[one_case(root,h,s) for h in TRUTHS for s in (0,1)]
    cross=[cross_seed(root,h) for h in TRUTHS]
    print(pd.DataFrame(cases).to_string(index=False))
    print(pd.DataFrame(cross).to_string(index=False))
    print(json.dumps({"cases":cases,"cross_seed":cross},indent=2))

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Truth-blind activation coverage audit for the revised CG-PC-CTT V4 contract.

Each input NPZ is one already-acquired OFF/source-update context and must contain:
  stop_probability [S,M,J]
  stop_r           [J]
  rectangles       [S,4]
  geometry_prior   [S]
Optional scalar/string metadata:
  house, seed, update_id, context_id, timesteps (default 200)

The script never reads source truth, localization error, final estimate, route id,
plume seed, or ON outcome. It only measures whether the frozen V4 M1/M2 contract
would ACCEPT/ABSTAIN on existing observations.
"""
from __future__ import annotations
import argparse, csv, json
from pathlib import Path
import numpy as np
import v4_final_reference as v4

def _scalar(d, key, default):
    if key not in d.files:
        return default
    x=d[key]
    if np.ndim(x)==0:
        return x.item()
    if np.size(x)==1:
        return np.ravel(x)[0].item()
    return default

def audit_one(path: Path):
    d=np.load(path,allow_pickle=True)
    required=("stop_probability","stop_r","rectangles","geometry_prior")
    missing=[k for k in required if k not in d.files]
    if missing: raise ValueError(f"{path}: missing {missing}")
    forbidden={"truth","true_source","source_truth","localization_error","final_error","off_on_improvement"}
    leaked=forbidden.intersection(d.files)
    if leaked: raise ValueError(f"{path}: forbidden truth/performance keys {sorted(leaked)}")
    p=np.asarray(d["stop_probability"],float)
    r=np.asarray(d["stop_r"],float)
    rect=np.asarray(d["rectangles"],int)
    q0=np.asarray(d["geometry_prior"],float)
    T=int(_scalar(d,"timesteps",200))
    build=v4.build_components(p,rect,T)
    dec=v4.strict_loso_m2(p,r,build.labels,q0,T)
    member_loo=False
    if dec.accepted:
        member_loo=v4.member_loo_robust(p,r,build.labels,q0,T,dec.selected_mask)
        if not member_loo:
            dec.accepted=False; dec.reason="SCORING_MEMBER_LOO_FAIL"
    return {
        "path":str(path),
        "context_id":str(_scalar(d,"context_id",path.stem)),
        "house":str(_scalar(d,"house","UNKNOWN")),
        "seed":str(_scalar(d,"seed","UNKNOWN")),
        "update_id":str(_scalar(d,"update_id","UNKNOWN")),
        "timesteps":T,
        "sources":int(p.shape[0]),
        "members":int(p.shape[1]),
        "physical_stops":int(p.shape[2]),
        "components":int(len(np.unique(build.labels))),
        "resolved_edges":int(len(build.resolved_edges)),
        "unresolved_edges":int(len(build.unresolved_edges)),
        "min_c_eff_eigenvalue":float(np.min(build.c_eff_eigenvalues)),
        "accepted":bool(dec.accepted),
        "reason":dec.reason,
        "selected_component":"" if dec.selected_component is None else int(dec.selected_component),
        "informative_heldout":int(dec.informative_heldout),
        "min_absolute_gain":"" if dec.heldout_absolute_gain is None else float(np.min(dec.heldout_absolute_gain)),
        "min_rival_margin":"" if dec.heldout_rival_margin is None else float(np.min(dec.heldout_rival_margin)),
        "member_loo_pass":bool(member_loo) if dec.accepted else "",
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("inputs",nargs="+",type=Path)
    ap.add_argument("--out-csv",type=Path,required=True)
    ap.add_argument("--out-json",type=Path,required=True)
    a=ap.parse_args()
    files=[]
    for x in a.inputs:
        if x.is_dir(): files.extend(sorted(x.glob("*.npz")))
        else: files.append(x)
    if not files: raise ValueError("no NPZ contexts")
    rows=[audit_one(p) for p in files]
    houses={}
    for r in rows:
        h=r["house"]
        z=houses.setdefault(h,{"contexts":0,"accept":0,"reasons":{}})
        z["contexts"]+=1; z["accept"]+=int(r["accepted"])
        z["reasons"][r["reason"]]=z["reasons"].get(r["reason"],0)+1
    known=[h for h in ("H01","H02","H03") if h in houses]
    total_accept=sum(int(r["accepted"]) for r in rows)
    active_houses=sum(houses[h]["accept"]>0 for h in known)
    if len(known)==3 and total_accept==0:
        feasibility="STOP_ZERO_ACTIONABILITY"
    elif len(known)==3 and active_houses<2:
        feasibility="STOP_SINGLE_HOUSE_ACTIONABILITY"
    else:
        feasibility="COVERAGE_REPORTED_NO_PERFORMANCE_CLAIM"
    summary={
        "contract":"CG_PC_CTT_V4_TRUTHBLIND_COVERAGE_V1",
        "truth_used":False,
        "localization_error_used":False,
        "contexts":len(rows),
        "total_accept":total_accept,
        "houses":houses,
        "feasibility":feasibility,
        "note":"Coverage is a pre-C++ actionability audit only. It is not localization-performance evidence and must not tune the frozen M1/M2 rules."
    }
    a.out_csv.parent.mkdir(parents=True,exist_ok=True)
    with a.out_csv.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    a.out_json.write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__": main()

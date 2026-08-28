#!/usr/bin/env python3
"""Representation-stability diagnostics for the already-frozen H03 Gate V2.

This script NEVER changes the gate decision rule. It asks whether the observed
H03 10/10 PASS and gamma≈0.865 are artifacts of using all 626 free-space cells
as separate features.

For each context it re-evaluates the frozen V2 statistic on deterministic
feature subsets: all cells, every 2nd, every 4th, every 8th. If query_xy[D,2]
is supplied, it also uses four deterministic spatial checkerboard subsets.
No subset result is eligible for threshold fitting or method promotion.
"""
from __future__ import annotations
import argparse, csv, json
from pathlib import Path
import numpy as np
from completeness_gate import GateConfig, compute_gate

CFG = GateConfig(gamma_min=0.05, p_max=0.01, rank_k=3,
                 member_semantics="exchangeable_realizations")


def checkerboard_indices(xy, mod, residue):
    xy = np.asarray(xy, dtype=float)
    # Deterministic rank-based bins avoid dependence on map resolution units.
    ox = np.argsort(np.argsort(xy[:, 0]))
    oy = np.argsort(np.argsort(xy[:, 1]))
    return np.flatnonzero((ox + oy) % mod == residue)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("npz", type=Path)
    ap.add_argument("--out-csv", type=Path, required=True)
    ap.add_argument("--out-json", type=Path, required=True)
    a=ap.parse_args(); d=np.load(a.npz,allow_pickle=True); phi=np.asarray(d["phi"],float)
    if phi.ndim!=4: raise ValueError(f"phi must be [N,S,M,D], got {phi.shape}")
    N,S,M,D=phi.shape
    contexts=np.asarray(d["context"]).astype(str) if "context" in d else np.asarray([str(i) for i in range(N)])
    subsets={"all":np.arange(D)}
    for stride in (2,4,8): subsets[f"stride_{stride}"]=np.arange(0,D,stride)
    xy=None
    for key in ("query_xy","free_xy","feature_xy"):
        if key in d:
            xy=np.asarray(d[key],float); break
    if xy is not None:
        if xy.shape!=(D,2): raise ValueError(f"query_xy expected {(D,2)}, got {xy.shape}")
        for r in range(4):
            idx=checkerboard_indices(xy,4,r)
            if len(idx)>=3: subsets[f"checker4_{r}"]=idx

    rows=[]
    for name,idx in subsets.items():
        for n in range(N):
            g=compute_gate(phi[n,:,:,idx],CFG)
            rows.append({"subset":name,"feature_count":len(idx),"context":contexts[n],**g.to_dict()})
    a.out_csv.parent.mkdir(parents=True,exist_ok=True)
    with a.out_csv.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

    by={}
    for name in subsets:
        rr=[r for r in rows if r["subset"]==name]
        gam=np.array([r["gamma_cf"] for r in rr],float); acc=np.array([r["accepted"] for r in rr],bool)
        by[name]={"feature_count":rr[0]["feature_count"],"coverage":float(acc.mean()),"gamma_median":float(np.median(gam)),"gamma_min":float(gam.min()),"gamma_max":float(gam.max())}
    all_med=by["all"]["gamma_median"]
    rel=[]
    for name,v in by.items():
        if name=="all": continue
        rel.append(abs(v["gamma_median"]-all_med)/max(abs(all_med),1e-12))
    summary={"contract":"CG_PC_CTT_H03_REPRESENTATION_STRESS_V1","shape":[N,S,M,D],"subsets":by,"max_relative_median_gamma_shift":float(max(rel) if rel else 0.0),"binding_note":"diagnostic only; no threshold or feature-set changes are permitted from this result"}
    a.out_json.write_text(json.dumps(summary,indent=2),encoding="utf-8"); print(json.dumps(summary,indent=2))
if __name__=="__main__": main()

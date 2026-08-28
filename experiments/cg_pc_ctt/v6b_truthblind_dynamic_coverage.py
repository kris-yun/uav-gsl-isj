#!/usr/bin/env python3
"""Truth-blind 30-run V6-B ordered-dynamics coverage versus matched static ablation."""
from __future__ import annotations
import argparse,csv,json
from collections import defaultdict
from pathlib import Path
import numpy as np
import v6b_dynamic_transport_reference as v6

FORBIDDEN={"truth","true_source","source_truth","localization_error","final_error","off_on_improvement"}
REQ=("sim_occupancy","observed_tape","geometry_prior","house","seed","update_id","context_id","timesteps","lag_steps")


def load(path):
    d=np.load(path,allow_pickle=False)
    if FORBIDDEN.intersection(d.files): raise ValueError(f"{path}: forbidden truth/performance key")
    if any(k not in d.files for k in REQ): raise ValueError(f"{path}: missing required dynamic key")
    x=np.asarray(d["sim_occupancy"],dtype=np.int8)
    y=np.asarray(d["observed_tape"],dtype=np.int8)
    if x.ndim!=4 or y.ndim!=2 or x.shape[2]!=y.shape[0]: raise ValueError(f"{path}: shape mismatch")
    if not np.all((x==0)|(x==1)) or not np.all((y==0)|(y==1)): raise ValueError(f"{path}: nonbinary tape")
    return {"path":str(path),"sim_occupancy":x,"observed_tape":y,
            "q0":np.asarray(d["geometry_prior"],float),"house":str(d["house"].item()),
            "seed":int(d["seed"].item()),"update_id":int(d["update_id"].item()),
            "id":str(d["context_id"].item()),"timesteps":int(d["timesteps"].item()),
            "lag_steps":int(d["lag_steps"].item())}


def static_transfer(items,q0):
    E=np.stack([v6.frequency_source_evidence(c["sim_occupancy"],c["observed_tape"],c["timesteps"]) for c in items])
    pos=0; no_contra=True; rows=[]
    for h,c in enumerate(items):
        train=[i for i in range(len(items)) if i!=h]
        q=v6.source_posterior(q0,E[train])
        model=v6._weighted_lse(E[h],q); prior=v6._weighted_lse(E[h],q0)
        g=float(model-prior); tol=128*np.finfo(float).eps*(1+abs(model)+abs(prior))
        if g < -tol: no_contra=False
        if g > tol: pos+=1
        rows.append(g)
    return bool(no_contra and pos>=2),rows


def analyze(items):
    items=sorted(items,key=lambda z:z["update_id"])
    q0=v6._norm(items[0]["q0"],"geometry prior")
    lag={c["lag_steps"] for c in items}
    if len(lag)!=1: raise ValueError("lag_steps changed within run")
    for c in items:
        if len(c["q0"])!=len(q0) or np.max(np.abs(v6._norm(c["q0"])-q0))>1e-12:
            raise ValueError("geometry prior drift")
    contexts=[{"id":c["id"],"sim_occupancy":c["sim_occupancy"],
               "observed_tape":c["observed_tape"],"timesteps":c["timesteps"]} for c in items]
    dyn=v6.loco_dynamic_diagnostic(contexts,q0,next(iter(lag)))
    st,sg=static_transfer(items,q0)
    return dyn,st,sg


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("inputs",nargs="+",type=Path)
    ap.add_argument("--out-json",type=Path,required=True); ap.add_argument("--out-csv",type=Path,required=True)
    a=ap.parse_args(); files=[]
    for p in a.inputs: files += sorted(p.glob("*.npz")) if p.is_dir() else [p]
    if not files: raise ValueError("no dynamic NPZs")
    g=defaultdict(list)
    for p in files:
        c=load(p); g[(c["house"],c["seed"])].append(c)
    run=[]; folds=[]
    for key,items in sorted(g.items()):
        dyn,stat,sg=analyze(items)
        run.append({"house":key[0],"seed":key[1],"dynamic_transfer_pass":dyn.transfer_pass,
                    "dynamic_absolute_pass":dyn.absolute_pass,"dynamic_predictive_pass":dyn.dynamic_predictive_pass,
                    "static_transfer_pass":stat,"positive_dynamic_transfer_contexts":dyn.positive_transfer_contexts})
        for f,s in zip(dyn.folds,sg):
            folds.append({"house":key[0],"seed":key[1],"heldout_context":f.heldout_context,
                          "dynamic_transfer_gain":f.source_transfer_gain,"dynamic_absolute_gain":f.absolute_gain,
                          "static_transfer_gain":float(s)})
    houses={}
    for h in ("H01","H02","H03"):
        rr=[r for r in run if r["house"]==h]
        houses[h]={"runs":len(rr),
                   "dynamic_predictive_pass":sum(int(r["dynamic_predictive_pass"]) for r in rr),
                   "dynamic_transfer_pass":sum(int(r["dynamic_transfer_pass"]) for r in rr),
                   "static_transfer_pass":sum(int(r["static_transfer_pass"]) for r in rr)}
    total=sum(int(r["dynamic_predictive_pass"]) for r in run)
    if total>=20 and all(houses[h]["dynamic_predictive_pass"]>0 for h in houses):
        verdict="V6B_ORDERED_DYNAMICS_ACTIONABLE_FOR_RUNTIME_REFERENCE"
    elif total>=10:
        verdict="V6B_PARTIAL_DYNAMIC_RECOVERY_NO_CPP_YET"
    else:
        verdict="V6B_CTT_DYNAMIC_FAMILY_INSUFFICIENT_ESCALATE_TO_PHYSICS_FACTORIZED_SBI"
    summary={"contract":"CG_PC_CTT_V6B_TRUTHBLIND_DYNAMIC_COVERAGE_V1","truth_used":False,
             "localization_error_used":False,"runs":len(run),"contexts":len(files),
             "dynamic_predictive_pass_runs":total,"houses":houses,"verdict":verdict,
             "note":"Diagnostic/actionability only. Dynamic and static scores use different proper observation models; compare pass structure, not raw score magnitudes."}
    a.out_json.parent.mkdir(parents=True,exist_ok=True)
    a.out_json.write_text(json.dumps({"summary":summary,"runs":run},indent=2),encoding="utf-8")
    with a.out_csv.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(folds[0].keys())); w.writeheader(); w.writerows(folds)
    print(json.dumps(summary,indent=2))

if __name__=="__main__": main()

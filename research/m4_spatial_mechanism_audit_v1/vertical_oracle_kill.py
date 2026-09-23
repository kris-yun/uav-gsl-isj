#!/usr/bin/env python3
"""Kill-only vertical-transport attribution for frozen M4-v3.

M4-v3 consumes only wind x/y although exported GADEN wind contains x/y/z.
Use source-blind masks defined by |Wz| and |W2z-W1z|. Inside each mask an
oracle replaces frozen M4's wind-delta with truth; elsewhere M4 is untouched.
No training, no parameter selection from truth.
"""
from __future__ import annotations
import argparse, importlib.util, json
from pathlib import Path
import numpy as np
import torch
from torch.nn import functional as F

PAIRS=(("S2","W2"),("S2","W1"))
SEEDS=(1729,2718)
PLUMES=("A","B")
TOP_FRACS=(0.10,0.25,0.50)
MAX_LOCAL_AREA=0.35
COS_GATE=0.5

def load_py(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def cosine(a,b):
    a=a.reshape(-1).double(); b=b.reshape(-1).double()
    na=torch.linalg.vector_norm(a); nb=torch.linalg.vector_norm(b)
    return float(torch.dot(a,b)/(na*nb)) if float(na)>0 and float(nb)>0 else float("nan")

def metrics(dp,dy,free):
    f=(free[0,0]>0.5)[None].expand(dp.shape[1],-1,-1)
    return cosine(dp[0,:,0][f],dy[0,:,0][f])

def raw_wind3(dynamic,wid):
    a=np.load(dynamic/f"wind_{wid}_sequence_z0p20.npy",allow_pickle=False).astype(np.float32)
    t=torch.from_numpy(a).permute(0,3,1,2)
    return F.avg_pool2d(t,2,ceil_mode=True)

def record_vertical_masks(d0,mm,dynamic,free):
    w1=raw_wind3(dynamic,"W1"); w2=raw_wind3(dynamic,"W2")
    max_steps=int(round(max(d0.TARGET_TIMES_S)/d0.PHYSICS_DT_S))
    ids=mm.gaden_wind_index_schedule(max_steps,d0.PHYSICS_DT_S,d0.WIND_DT_S,11,d0.LOOP_FROM,d0.LOOP_TO)
    free2=free[0,0]>0.5
    absz=[]; dz=[]
    for step in d0.record_steps():
        i=ids[step-1]
        z1=w1[i,2].abs(); z2=w2[i,2].abs()
        absz.append(torch.maximum(z1,z2))
        dz.append((w2[i,2]-w1[i,2]).abs())
    absz=torch.stack(absz); dz=torch.stack(dz)
    out={}
    for label,x in (("vertical_abs",absz),("vertical_intervention",dz)):
        for frac in TOP_FRACS:
            ms=[]
            for t in range(x.shape[0]):
                vals=x[t][free2]
                q=torch.quantile(vals,1-frac)
                ms.append(x[t]>=q)
            out[f"{label}_top_{int(frac*100)}pct"]=torch.stack(ms)
    return out

def oracle_row(name,mask,dp,dy,free,base):
    ft=(free[0,0]>0.5)[None].expand(dp.shape[1],-1,-1)
    m=mask & ft
    o=dp.clone(); o[0,:,0][m]=dy[0,:,0][m]
    err=(dy-dp)[0,:,0].double()
    area=float(m.sum()/ft.sum())
    eall=(err[ft]**2).sum()
    cap=float((err[m]**2).sum()/eall) if float(eall)>0 else float("nan")
    oc=metrics(o,dy,free)
    return {"mask":name,"area_fraction":area,"delta_error_energy_captured":cap,
            "error_density_enrichment":cap/max(area,1e-12),
            "oracle_cosine":oc,"oracle_cosine_gain":oc-base,
            "localized_gate_eligible":bool(area<=MAX_LOCAL_AREA),
            "oracle_crosses_cos_gate":bool(oc>COS_GATE)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",type=Path,required=True)
    ap.add_argument("--dynamic-wind",type=Path,required=True)
    ap.add_argument("--d0-out",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    torch.use_deterministic_algorithms(True); torch.set_num_threads(4)
    root=args.repo_root
    cr=root/"research/causal_compositional_plume_world_model_v1"
    bank=root/"evidence/causal_compositional_plume_world_model_v1/c0_5_real_gaden_bank"
    d0=load_py(cr/"m4_v3_d0_house02.py","d0")
    mm=load_py(cr/"m4_v3_interventional_evolution.py","mm")
    sources,free=d0.load_static_context(bank)
    winds,_=d0.load_dynamic_winds(args.dynamic_wind)
    manifest=json.loads((args.d0_out/"train_manifest.json").read_text())
    masks=record_vertical_masks(d0,mm,args.dynamic_wind,free)
    out={"mode":"M4_V3_VERTICAL_TRANSPORT_ORACLE_KILL_ONLY","training":False,
         "truth_used_for_attribution_only":True,"cosine_gate":COS_GATE,
         "max_local_area_fraction":MAX_LOCAL_AREA,"top_fractions":list(TOP_FRACS),"fits":{}}
    rows_by={}
    for seed in SEEDS:
        key=f"m4v3_seed{seed}"; cp=args.d0_out/f"{key}.pt"
        if d0.sha256(cp)!=manifest["fits"][key]["checkpoint_sha256"]:
            raise RuntimeError("checkpoint hash mismatch "+key)
        model=mm.InterventionalEvolutionPropagator(cell_m=manifest["effective_cell_m"],
                                                   internal_dt_s=manifest["physics_dt_s"])
        model.load_state_dict(torch.load(cp,map_location="cpu",weights_only=True)); model.eval()
        sb=torch.cat([sources[s] for s,_ in PAIRS],0)
        sch=d0.build_batch_schedule(mm,winds,PAIRS,torch.device("cpu"))
        with torch.no_grad():
            pred=d0.evolve_to_records(model,sb,sch,free,use_checkpoint=False)
            p=torch.log1p(pred.clamp_min(0))
        dp=p[0:1]-p[1:2]
        so={}
        for ps in PLUMES:
            dy=d0.target(bank,"S2","W2",ps)[None]-d0.target(bank,"S2","W1",ps)[None]
            base=metrics(dp,dy,free)
            rows=[oracle_row(n,m,dp,dy,free,base) for n,m in masks.items()]
            so[ps]={"base_cosine":base,"oracle_masks":rows}; rows_by[(seed,ps)]=rows
        out["fits"][key]=so
    names=list(masks.keys()); survivors=[]
    for n in names:
        rr=[next(x for x in rows if x["mask"]==n) for rows in rows_by.values()]
        if all(x["localized_gate_eligible"] and x["oracle_crosses_cos_gate"] for x in rr):
            survivors.append({"mask":n,"max_area_fraction":max(x["area_fraction"] for x in rr),
                              "min_oracle_cosine":min(x["oracle_cosine"] for x in rr),
                              "min_error_energy_captured":min(x["delta_error_energy_captured"] for x in rr),
                              "mean_oracle_gain":float(np.mean([x["oracle_cosine_gain"] for x in rr]))})
    out["summary"]={"surviving_masks":survivors,
                    "decision":"VERTICAL_TRANSPORT_MECHANISM_SURVIVES_KILL_ONLY" if survivors else "VERTICAL_LOCAL_MECHANISM_NO_GO",
                    "interpretation":"oracle attribution only; survival cannot ADVANCE a model"}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,indent=2,allow_nan=True)+"\n")
    print(json.dumps(out,indent=2,allow_nan=True))
if __name__=="__main__": main()

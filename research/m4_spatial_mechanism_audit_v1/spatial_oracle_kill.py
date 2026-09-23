#!/usr/bin/env python3
"""Kill-only spatial mechanism attribution for frozen M4-v3.

Uses opened House02 truth ONLY as an attribution oracle. No fitting/training.

Question:
Can the frozen M4-v3 wind-delta geometry failure be repaired by correcting only
source-blind regions defined by (a) wall proximity, (b) high local strain, or
(c) their union? If even a perfect oracle correction inside such regions cannot
recover the frozen cosine > 0.5 gate, that localized physical mechanism is not
large enough to justify a new auxiliary/mainline.

This script never writes/changes model parameters.
"""
from __future__ import annotations

import argparse, importlib.util, json, math
from pathlib import Path

import numpy as np
import torch
from scipy.ndimage import distance_transform_edt

PAIRS=(("S2","W2"),("S2","W1"))
SEEDS=(1729,2718)
PLUMES=("A","B")
WALL_BANDS=(1,2,4,8)
STRAIN_TOP_FRACS=(0.10,0.25,0.50)
MAX_LOCAL_AREA=0.35
COS_GATE=0.5

def load_py(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def flat_masked(x,mask):
    # x [1,T,1,H,W], mask [T,H,W] bool
    z=x[0,:,0].double()
    return z[mask].reshape(-1)

def cosine(a,b):
    aa=a.reshape(-1).double(); bb=b.reshape(-1).double()
    na=torch.linalg.vector_norm(aa); nb=torch.linalg.vector_norm(bb)
    if float(na)<=0 or float(nb)<=0:
        return float("nan")
    return float(torch.dot(aa,bb)/(na*nb))

def strain_field(wind,cell_m):
    """Rate-of-strain Frobenius-like magnitude for [2,H,W]."""
    u=wind[0].double()
    v=wind[1].double()
    # tensor dims: first component moves rows; second moves cols in this codebase.
    du_dr,du_dc=torch.gradient(u,spacing=(cell_m,cell_m))
    dv_dr,dv_dc=torch.gradient(v,spacing=(cell_m,cell_m))
    s11=du_dr
    s22=dv_dc
    s12=0.5*(du_dc+dv_dr)
    return torch.sqrt(s11*s11+s22*s22+2.0*s12*s12)

def record_wind_strain(d0,mm,winds,cell_m):
    max_steps=int(round(max(d0.TARGET_TIMES_S)/d0.PHYSICS_DT_S))
    ids=mm.gaden_wind_index_schedule(
        max_steps,d0.PHYSICS_DT_S,d0.WIND_DT_S,11,d0.LOOP_FROM,d0.LOOP_TO)
    out=[]
    for step in d0.record_steps():
        idx=ids[step-1]
        s1=strain_field(winds["W1"][idx],cell_m)
        s2=strain_field(winds["W2"][idx],cell_m)
        out.append(torch.maximum(s1,s2))
    return torch.stack(out,dim=0) # [T,H,W]

def wall_distance_cells(free):
    f=(free[0,0].cpu().numpy()>0.5)
    # Pad map boundary as blocked so outer boundary is also a physical boundary.
    p=np.pad(f.astype(np.uint8),1,mode="constant",constant_values=0)
    d=distance_transform_edt(p)[1:-1,1:-1]
    d[~f]=0.0
    return torch.from_numpy(d.astype(np.float64))

def delta_metrics(delta_pred,delta_true,free):
    mask=(free[0,0]>0.5)[None].expand(delta_pred.shape[1],-1,-1)
    p=flat_masked(delta_pred,mask)
    y=flat_masked(delta_true,mask)
    return {
        "cosine":cosine(p,y),
        "pred_norm":float(torch.linalg.vector_norm(p)),
        "true_norm":float(torch.linalg.vector_norm(y)),
    }

def oracle_row(name,mask,delta_pred,delta_true,free,base_cos):
    free_t=(free[0,0]>0.5)[None].expand(delta_pred.shape[1],-1,-1)
    m=mask & free_t
    oracle=delta_pred.clone()
    oracle[0,:,0][m]=delta_true[0,:,0][m]

    err=(delta_true-delta_pred)[0,:,0].double()
    true=delta_true[0,:,0].double()
    free_err=(err[free_t]**2).sum()
    free_true=(true[free_t]**2).sum()
    err_cap=float((err[m]**2).sum()/free_err) if float(free_err)>0 else float("nan")
    true_share=float((true[m]**2).sum()/free_true) if float(free_true)>0 else float("nan")
    area=float(m.sum()/free_t.sum())
    oc=delta_metrics(oracle,delta_true,free)["cosine"]
    enrich=err_cap/max(area,1e-12)
    signal_enrich=true_share/max(area,1e-12)
    return {
        "mask":name,
        "area_fraction":area,
        "delta_error_energy_captured":err_cap,
        "true_delta_energy_share":true_share,
        "error_density_enrichment":enrich,
        "signal_density_enrichment":signal_enrich,
        "oracle_cosine":oc,
        "oracle_cosine_gain":oc-base_cos,
        "localized_gate_eligible":bool(area<=MAX_LOCAL_AREA),
        "oracle_crosses_cos_gate":bool(oc>COS_GATE),
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",type=Path,required=True)
    ap.add_argument("--dynamic-wind",type=Path,required=True)
    ap.add_argument("--d0-out",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()

    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(4)
    root=args.repo_root
    cr=root/"research/causal_compositional_plume_world_model_v1"
    bank=root/"evidence/causal_compositional_plume_world_model_v1/c0_5_real_gaden_bank"
    d0=load_py(cr/"m4_v3_d0_house02.py","d0")
    mm=load_py(cr/"m4_v3_interventional_evolution.py","mm")

    sources,free=d0.load_static_context(bank)
    winds,_=d0.load_dynamic_winds(args.dynamic_wind)
    manifest=json.loads((args.d0_out/"train_manifest.json").read_text())
    cell_m=float(manifest["effective_cell_m"])

    wall=wall_distance_cells(free)
    strain=record_wind_strain(d0,mm,winds,cell_m)
    free2=(free[0,0]>0.5)
    # Fixed source-blind strain masks: percentile among free cells independently per record.
    strain_masks={}
    for frac in STRAIN_TOP_FRACS:
        masks=[]
        for t in range(strain.shape[0]):
            vals=strain[t][free2]
            q=torch.quantile(vals,1.0-frac)
            masks.append(strain[t]>=q)
        strain_masks[frac]=torch.stack(masks,dim=0)

    wall_masks={}
    for band in WALL_BANDS:
        wall_masks[band]=(wall<=float(band))[None].expand(strain.shape[0],-1,-1)

    result={
        "mode":"M4_V3_SPATIAL_MECHANISM_ORACLE_KILL_ONLY",
        "training":False,
        "truth_used_for_attribution_only":True,
        "cosine_gate":COS_GATE,
        "max_local_area_fraction":MAX_LOCAL_AREA,
        "wall_bands_cells":list(WALL_BANDS),
        "strain_top_fractions":list(STRAIN_TOP_FRACS),
        "cell_m":cell_m,
        "fits":{},
    }

    all_rows={}
    for seed in SEEDS:
        key=f"m4v3_seed{seed}"
        cp=args.d0_out/f"{key}.pt"
        if d0.sha256(cp)!=manifest["fits"][key]["checkpoint_sha256"]:
            raise RuntimeError("checkpoint hash mismatch "+key)
        model=mm.InterventionalEvolutionPropagator(
            cell_m=cell_m,internal_dt_s=manifest["physics_dt_s"])
        model.load_state_dict(torch.load(cp,map_location="cpu",weights_only=True))
        model.eval()

        sb=torch.cat([sources[s] for s,_ in PAIRS],dim=0)
        schedule=d0.build_batch_schedule(mm,winds,PAIRS,torch.device("cpu"))
        with torch.no_grad():
            pred=d0.evolve_to_records(model,sb,schedule,free,use_checkpoint=False)
            plog=torch.log1p(pred.clamp_min(0))
        dp=(plog[0:1]-plog[1:2])

        seedout={}
        for ps in PLUMES:
            y22=d0.target(bank,"S2","W2",ps)[None]
            y21=d0.target(bank,"S2","W1",ps)[None]
            dy=y22-y21
            base=delta_metrics(dp,dy,free)
            rows=[]

            for band in WALL_BANDS:
                rows.append(oracle_row(
                    f"wall_le_{band}_cells",wall_masks[band],dp,dy,free,base["cosine"]))

            for frac in STRAIN_TOP_FRACS:
                rows.append(oracle_row(
                    f"strain_top_{int(frac*100)}pct",strain_masks[frac],dp,dy,free,base["cosine"]))

            # Predeclared combinations only: same wall bands crossed with top-25% strain.
            s25=strain_masks[0.25]
            for band in (2,4,8):
                rows.append(oracle_row(
                    f"wall_le_{band}_OR_strain_top25",
                    wall_masks[band] | s25,dp,dy,free,base["cosine"]))
                rows.append(oracle_row(
                    f"wall_le_{band}_AND_strain_top25",
                    wall_masks[band] & s25,dp,dy,free,base["cosine"]))

            seedout[ps]={"base":base,"oracle_masks":rows}
            all_rows[(seed,ps)]=rows
        result["fits"][key]=seedout

    # A mechanism family survives only if the SAME source-blind mask name is
    # local (<=35% area) and crosses the frozen 0.5 cosine gate in all 4 cases.
    common_names=[r["mask"] for r in next(iter(all_rows.values()))]
    survivors=[]
    for name in common_names:
        rr=[]
        for k,rows in all_rows.items():
            r=next(x for x in rows if x["mask"]==name)
            rr.append(r)
        if all(r["localized_gate_eligible"] and r["oracle_crosses_cos_gate"] for r in rr):
            survivors.append({
                "mask":name,
                "max_area_fraction":max(r["area_fraction"] for r in rr),
                "min_oracle_cosine":min(r["oracle_cosine"] for r in rr),
                "min_error_energy_captured":min(r["delta_error_energy_captured"] for r in rr),
                "mean_oracle_gain":float(np.mean([r["oracle_cosine_gain"] for r in rr])),
            })

    wall_surv=[s for s in survivors if s["mask"].startswith("wall_le_") and "_strain_" not in s["mask"]]
    strain_surv=[s for s in survivors if s["mask"].startswith("strain_top_")]
    combo_surv=[s for s in survivors if "_strain_" in s["mask"]]
    if wall_surv:
        decision="BOUNDARY_LOCALIZED_MECHANISM_SURVIVES_KILL_ONLY"
    elif strain_surv or combo_surv:
        decision="DEFORMATION_LOCALIZED_MECHANISM_SURVIVES_KILL_ONLY"
    else:
        decision="LOCAL_BOUNDARY_DEFORMATION_MECHANISM_NO_GO"

    result["summary"]={
        "surviving_masks":survivors,
        "wall_family_survives":bool(wall_surv),
        "strain_or_combo_family_survives":bool(strain_surv or combo_surv),
        "decision":decision,
        "interpretation":"oracle attribution only; survival cannot ADVANCE a model, failure kills localized mechanism",
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=True)+"\n")
    print(json.dumps(result,indent=2,allow_nan=True))

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Descriptive overlap audit for already-open House02 mechanism masks.

NOT a gate and not a model. Thresholds are inherited from the prior oracle
audits (wall<=1 pooled cell, strain top25%, |Wz| top25%, |dWz| top25%).
Quantifies whether candidate missing mechanisms occupy the same space-time
support and how much frozen M4-v3 wind-delta error lies in unique/intersection
regions.
"""
from __future__ import annotations
import argparse, importlib.util, json
from pathlib import Path
import numpy as np
import torch
from scipy.ndimage import distance_transform_edt
from torch.nn import functional as F

SEEDS=(1729,2718); PLUMES=("A","B"); PAIRS=(("S2","W2"),("S2","W1"))

def load_py(p,n):
    s=importlib.util.spec_from_file_location(n,p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def strain(w,cell):
    u=w[0].double(); v=w[1].double()
    ur,uc=torch.gradient(u,spacing=(cell,cell)); vr,vc=torch.gradient(v,spacing=(cell,cell))
    return torch.sqrt(ur*ur+vc*vc+0.5*(uc+vr)**2)

def topmask(x,free,q=.75):
    ms=[]
    for t in range(x.shape[0]):
        th=torch.quantile(x[t][free],q); ms.append(x[t]>=th)
    return torch.stack(ms)

def overlap(a,b,free_t):
    a=a&free_t; b=b&free_t
    inter=(a&b).sum(); union=(a|b).sum()
    return {"jaccard":float(inter/union) if int(union)>0 else float("nan"),
            "intersection_area":float(inter/free_t.sum()),
            "a_given_b":float(inter/b.sum()) if int(b.sum())>0 else float("nan"),
            "b_given_a":float(inter/a.sum()) if int(a.sum())>0 else float("nan")}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",type=Path,required=True)
    ap.add_argument("--dynamic-wind",type=Path,required=True)
    ap.add_argument("--d0-out",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    root=a.repo_root
    cr=root/"research/causal_compositional_plume_world_model_v1"
    bank=root/"evidence/causal_compositional_plume_world_model_v1/c0_5_real_gaden_bank"
    d0=load_py(cr/"m4_v3_d0_house02.py","d0"); mm=load_py(cr/"m4_v3_interventional_evolution.py","mm")
    src,free=d0.load_static_context(bank); winds,_=d0.load_dynamic_winds(a.dynamic_wind)
    man=json.loads((a.d0_out/"train_manifest.json").read_text()); cell=float(man["effective_cell_m"])
    free2=free[0,0]>0.5; T=len(d0.record_steps()); free_t=free2[None].expand(T,-1,-1)
    # wall <= one pooled 0.2 m cell
    f=free2.numpy(); dist=distance_transform_edt(np.pad(f.astype(np.uint8),1))[1:-1,1:-1]
    wall=(torch.from_numpy(dist)<=1.0)[None].expand(T,-1,-1)
    # recorded strains
    ids=mm.gaden_wind_index_schedule(d0.record_steps()[-1],d0.PHYSICS_DT_S,d0.WIND_DT_S,11,d0.LOOP_FROM,d0.LOOP_TO)
    ss=[]
    raw={}
    for wid in ("W1","W2"):
        x=np.load(a.dynamic_wind/f"wind_{wid}_sequence_z0p20.npy",allow_pickle=False).astype(np.float32)
        raw[wid]=F.avg_pool2d(torch.from_numpy(x).permute(0,3,1,2),2,ceil_mode=True)
    wz=[]; dwz=[]
    for step in d0.record_steps():
        i=ids[step-1]
        ss.append(torch.maximum(strain(winds["W1"][i],cell),strain(winds["W2"][i],cell)))
        wz.append(torch.maximum(raw["W1"][i,2].abs(),raw["W2"][i,2].abs()))
        dwz.append((raw["W2"][i,2]-raw["W1"][i,2]).abs())
    masks={"wall1":wall,"strain25":topmask(torch.stack(ss),free2),
           "wz25":topmask(torch.stack(wz),free2),
           "dwz25":topmask(torch.stack(dwz),free2)}
    ovs={}
    names=list(masks)
    for i in range(len(names)):
        for j in range(i+1,len(names)):
            ovs[f"{names[i]}__{names[j]}"]=overlap(masks[names[i]],masks[names[j]],free_t)

    # frozen M4 error attribution into disjoint wall/wz supports
    result={"mode":"DESCRIPTIVE_AFTER_ORACLE","mask_areas":{k:float((v&free_t).sum()/free_t.sum()) for k,v in masks.items()},
            "overlaps":ovs,"error_partitions":{}}
    sch=d0.build_batch_schedule(mm,winds,PAIRS,torch.device("cpu")); sb=torch.cat([src[s] for s,_ in PAIRS],0)
    for seed in SEEDS:
        key=f"m4v3_seed{seed}"; cp=a.d0_out/f"{key}.pt"
        model=mm.InterventionalEvolutionPropagator(cell_m=cell,internal_dt_s=man["physics_dt_s"])
        model.load_state_dict(torch.load(cp,map_location="cpu",weights_only=True)); model.eval()
        with torch.no_grad():
            p=torch.log1p(d0.evolve_to_records(model,sb,sch,free,use_checkpoint=False).clamp_min(0))
        dp=p[0:1]-p[1:2]
        for ps in PLUMES:
            dy=d0.target(bank,"S2","W2",ps)[None]-d0.target(bank,"S2","W1",ps)[None]
            e=(dy-dp)[0,:,0].double(); tot=(e[free_t]**2).sum()
            w=masks["wall1"]&free_t; z=masks["dwz25"]&free_t
            parts={"wall_only":w&(~z),"dwz_only":z&(~w),"intersection":w&z,"neither":free_t&(~w)&(~z)}
            result["error_partitions"][f"{seed}_{ps}"]={
                k:{"area_fraction":float(m.sum()/free_t.sum()),
                   "error_energy_fraction":float((e[m]**2).sum()/tot)}
                for k,m in parts.items()
            }
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+"\n"); print(json.dumps(result,indent=2))
if __name__=="__main__": main()

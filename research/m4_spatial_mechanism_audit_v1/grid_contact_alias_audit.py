#!/usr/bin/env python3
"""Source-blind audit: does M4's 2x pooling suppress obstacle-contact events?"""
from __future__ import annotations
import argparse, importlib.util, json
from pathlib import Path
import numpy as np
import torch
from torch.nn import functional as F

def load(p,n):
    s=importlib.util.spec_from_file_location(n,p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def collision_stats(mm,free,wind_xy,cell_m,dt=.1):
    b=1; _,h,w=free.shape
    row,col=mm._base_grid(h,w,wind_xy.device,wind_xy.dtype)
    dr=dt*wind_xy[0].reshape(1,-1)/cell_m
    dc=dt*wind_xy[1].reshape(1,-1)/cell_m
    clear=mm._path_is_clear(free[None],row.reshape(-1),col.reshape(-1),dr,dc,substeps=4)[0]
    ff=free[0].reshape(-1)>0.5
    active=ff & (~clear)
    return {
      "free_cells":int(ff.sum()),
      "collision_cells":int(active.sum()),
      "collision_fraction":float(active.sum()/ff.sum()),
      "mean_displacement_cells":float(torch.sqrt(dr[0,ff]**2+dc[0,ff]**2).mean()),
      "p95_displacement_cells":float(torch.quantile(torch.sqrt(dr[0,ff]**2+dc[0,ff]**2),.95)),
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo-root",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); a=ap.parse_args()
    root=a.repo_root
    mm=load(root/"research/causal_compositional_plume_world_model_v1/m4_v3_interventional_evolution.py","mm")
    bank=root/"evidence/causal_compositional_plume_world_model_v1/c0_5_real_gaden_bank"
    dyn=root/"evidence/causal_compositional_plume_world_model_v1/m4_v3_dynamic_wind_house02"
    mask=np.load(bank/"geometry/obstacle_mask_z0p20.npy",allow_pickle=False)
    free01=torch.from_numpy((mask==0).astype(np.float32))[None]
    free02=(1.0-F.max_pool2d(1.0-free01[None],2,ceil_mode=True))[0]
    out={"mode":"GRID_CONTACT_ALIAS_AUDIT","dt_s":.1,"records":{}}
    for wid in ("W1","W2"):
        raw=np.load(dyn/f"wind_{wid}_sequence_z0p20.npy",allow_pickle=False).astype(np.float32)
        w01=torch.from_numpy(raw).permute(0,3,1,2)[:,:2]
        w02=F.avg_pool2d(w01,2,ceil_mode=True)
        rec=[]
        for i in range(11):
            rec.append({"wind_index":i,
                        "grid_0p1m":collision_stats(mm,free01,w01[i],.1),
                        "grid_0p2m":collision_stats(mm,free02,w02[i],.2)})
        out["records"][wid]=rec
    vals={}
    for scale,key in ((.1,"grid_0p1m"),(.2,"grid_0p2m")):
        x=[r[key]["collision_fraction"] for wid in ("W1","W2") for r in out["records"][wid]]
        vals[str(scale)]={"mean_collision_fraction":float(np.mean(x)),"max_collision_fraction":float(np.max(x))}
    out["summary"]=vals
    a.output.write_text(json.dumps(out,indent=2)+"\n"); print(json.dumps(out,indent=2))
if __name__=="__main__": main()

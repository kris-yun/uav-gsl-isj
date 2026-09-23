#!/usr/bin/env python3
"""Build a pretraining-semantics-aligned House02 token smoke for M6 G0.5-B.

This uses historical estimated wind ONLY for the checkpoint/runtime interface
smoke. It must not be used for gas-performance claims. Geometry semantics match
GeoPT pretraining: y-up coordinates and free-point -> nearest-boundary direction.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--hit",type=Path,required=True)
    ap.add_argument("--wind",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--meta",type=Path,required=True)
    ap.add_argument("--target-x-extent",type=float,default=5.0)
    ap.add_argument("--tau-ref-s",type=float,default=1.0)
    args=ap.parse_args()

    hit=pd.read_csv(args.hit)
    wind=pd.read_csv(args.wind)
    free=hit[hit["occupancy"]=="Free"].copy()
    obs=hit[hit["occupancy"]=="Obstacle"].copy()
    xy=free[["x","y"]].to_numpy(float)
    oxy=obs[["x","y"]].to_numpy(float)
    if len(free)!=631:
        raise RuntimeError(f"House02 free-token contract drift: {len(free)}")
    tree=cKDTree(oxy)
    dist,idx=tree.query(xy,k=1)
    nearest=oxy[idx]

    # GeoPT pretraining sign: free point -> nearest boundary.
    wall_xy=nearest-xy
    wall_xy/=np.maximum(dist[:,None],1e-12)

    x_extent=float(hit["x"].max()-hit["x"].min())
    scale=args.target_x_extent/x_extent

    # Deterministic y-up mapping:
    # GeoPT X <- world x; GeoPT Y <- physical height (0 here);
    # GeoPT Z <- world y.
    xg=(xy[:,0]-float(hit["x"].mean()))*scale
    zg=(xy[:,1]-float(hit["y"].mean()))*scale
    pos=np.column_stack([xg,np.zeros(len(xg)),zg])

    # Geometry7 duplicates xyz as in released downstream/pretraining contract.
    wall_dir=np.column_stack([wall_xy[:,0],np.zeros(len(wall_xy)),wall_xy[:,1]])
    geom=np.column_stack([pos,dist*scale,wall_dir])

    fw=free[["cell_index","x","y"]].merge(
        wind,on=["cell_index","x","y"],how="left",validate="one_to_one")
    if fw[["wind_x","wind_y"]].isna().any().any():
        raise RuntimeError("wind coverage drift")
    wxy=fw[["wind_x","wind_y"]].to_numpy(float)
    speed=np.linalg.norm(wxy,axis=1)
    wdir=np.zeros((len(speed),3),dtype=float)
    nz=speed>1e-12
    wdir[nz,0]=wxy[nz,0]/speed[nz]
    wdir[nz,2]=wxy[nz,1]/speed[nz]
    step=scale*speed*float(args.tau_ref_s)
    dynamics=np.column_stack([wdir,step])
    fx=np.column_stack([geom,dynamics])

    if pos.shape!=(631,3) or fx.shape!=(631,11):
        raise RuntimeError(f"shape drift pos={pos.shape} fx={fx.shape}")
    if not np.isfinite(pos).all() or not np.isfinite(fx).all():
        raise RuntimeError("nonfinite feature")
    args.out.parent.mkdir(parents=True,exist_ok=True)
    np.savez(args.out,x=pos.astype(np.float32),fx=fx.astype(np.float32),
             cell_index=free["cell_index"].to_numpy())
    meta={
      "scientific_use":"interface/runtime only; historical estimated wind",
      "token_count":len(free),
      "geometry_scale":scale,
      "tau_ref_s":args.tau_ref_s,
      "wall_direction":"free_point_to_nearest_obstacle_center",
      "axis_mapping":"GeoPT X=world x, Y=vertical(0), Z=world y",
      "wind_prompt":"[unit_wind_X,0,unit_wind_Z,scale*speed*tau_ref]",
      "speed_quantiles":np.quantile(speed,[0,.25,.5,.75,.9,.95,1]).tolist(),
      "step_quantiles":np.quantile(step,[0,.25,.5,.75,.9,.95,1]).tolist(),
    }
    args.meta.write_text(json.dumps(meta,indent=2)+"\n")
    print(json.dumps(meta,indent=2))

if __name__=="__main__":
    main()

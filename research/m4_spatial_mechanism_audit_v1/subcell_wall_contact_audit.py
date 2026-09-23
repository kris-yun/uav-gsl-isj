#!/usr/bin/env python3
"""House02 source-blind sub-cell wall-contact audit.

No plume/source truth, no training.

M4-v3 stores Eulerian mass at cell centres. A real GADEN filament has continuous
sub-cell position. This audit asks whether, under the same House02 occupancy and
dynamic wind, continuous sub-cell position + the preregistered L1 GADEN noise
scale creates wall contacts that a cell-centre state cannot represent.

L1 provenance: config filament_noise_std=0.01 under the compatibility scaling in
current GADEN core => approximately 0.01 m single-step displacement std at
dt=0.1 s. We also report deterministic wind-only and 0.02 m sensitivity without
using plume/source truth.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np

DT=0.1
CELL=0.1
NOISE_DISP_M=(0.0,0.01,0.02)
SAMPLES_PER_FREE_CELL=256
SEED=84017

def path_hits_obstacle(r0,c0,dr,dc,free,substeps=8):
    h,w=free.shape
    hit=np.zeros(r0.shape,dtype=bool)
    for k in range(1,substeps+1):
        q=k/substeps
        rr=r0+q*dr
        cc=c0+q*dc
        ri=np.floor(rr).astype(np.int64)
        ci=np.floor(cc).astype(np.int64)
        inside=(ri>=0)&(ri<h)&(ci>=0)&(ci<w)
        blocked=~inside
        good=inside
        if np.any(good):
            blocked[good] |= ~free[ri[good],ci[good]]
        hit |= blocked
    return hit

def adjacent_to_obstacle(free):
    h,w=free.shape
    out=np.zeros_like(free,dtype=bool)
    for di,dj in ((1,0),(-1,0),(0,1),(0,-1)):
        shifted=np.zeros_like(free,dtype=bool)
        si=slice(max(0,di),min(h,h+di)); sj=slice(max(0,dj),min(w,w+dj))
        ti=slice(max(0,-di),min(h,h-di)); tj=slice(max(0,-dj),min(w,w-dj))
        shifted[ti,tj]=~free[si,sj]
        out |= shifted
    # outer map boundary also constraint-active
    out[0,:]=True; out[-1,:]=True; out[:,0]=True; out[:,-1]=True
    return out & free

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()

    root=a.repo_root
    bank=root/"evidence/causal_compositional_plume_world_model_v1/c0_5_real_gaden_bank"
    dyn=root/"evidence/causal_compositional_plume_world_model_v1/m4_v3_dynamic_wind_house02"
    obstacle=np.load(bank/"geometry/obstacle_mask_z0p20.npy",allow_pickle=False)
    free=(obstacle==0)
    near=adjacent_to_obstacle(free)
    free_idx=np.argwhere(free)
    near_idx=np.argwhere(near)
    rng=np.random.default_rng(SEED)

    result={
      "mode":"HOUSE02_SUBCELL_WALL_CONTACT_SOURCE_BLIND",
      "dt_s":DT,"cell_m":CELL,
      "samples_per_free_cell":SAMPLES_PER_FREE_CELL,
      "rng_seed":SEED,
      "free_cells":int(free.sum()),
      "near_wall_free_cells":int(near.sum()),
      "near_wall_free_fraction":float(near.sum()/free.sum()),
      "noise_displacement_std_m":list(NOISE_DISP_M),
      "records":{},
    }

    for wid in ("W1","W2"):
        arr=np.load(dyn/f"wind_{wid}_sequence_z0p20.npy",allow_pickle=False).astype(np.float64)
        rec=[]
        for wind_i in range(arr.shape[0]):
            uv=arr[wind_i,:,:,:2]
            wi=uv[free_idx[:,0],free_idx[:,1]]
            # continuous coordinates in units of grid cells
            n=len(free_idx)*SAMPLES_PER_FREE_CELL
            base=np.repeat(free_idx,SAMPLES_PER_FREE_CELL,axis=0)
            frac=rng.random((n,2))
            r0=base[:,0]+frac[:,0]
            c0=base[:,1]+frac[:,1]
            wind_rep=np.repeat(wi,SAMPLES_PER_FREE_CELL,axis=0)
            row_is_near=np.repeat(near[free_idx[:,0],free_idx[:,1]],SAMPLES_PER_FREE_CELL)
            item={"wind_index":wind_i,"noise":{}}
            for sigma_m in NOISE_DISP_M:
                # grid index convention: channel x->row, channel y->col follows
                # the frozen M4-v3 implementation, so comparison is like-for-like.
                noise=rng.normal(0.0,sigma_m,size=(n,2)) if sigma_m>0 else np.zeros((n,2))
                disp_m=wind_rep*DT+noise
                dr=disp_m[:,0]/CELL
                dc=disp_m[:,1]/CELL
                hit=path_hits_obstacle(r0,c0,dr,dc,free,8)
                item["noise"][str(sigma_m)]={
                  "all_contact_fraction":float(hit.mean()),
                  "near_wall_contact_fraction":float(hit[row_is_near].mean()),
                  "far_contact_fraction":float(hit[~row_is_near].mean()),
                  "contact_events":int(hit.sum()),
                  "near_wall_contact_events":int(hit[row_is_near].sum()),
                }
            rec.append(item)
        result["records"][wid]=rec

    summary={}
    for sigma in NOISE_DISP_M:
        rows=[x["noise"][str(sigma)] for wid in ("W1","W2") for x in result["records"][wid]]
        summary[str(sigma)]={
          "mean_all_contact_fraction":float(np.mean([x["all_contact_fraction"] for x in rows])),
          "mean_near_wall_contact_fraction":float(np.mean([x["near_wall_contact_fraction"] for x in rows])),
          "max_near_wall_contact_fraction":float(np.max([x["near_wall_contact_fraction"] for x in rows])),
          "mean_far_contact_fraction":float(np.mean([x["far_contact_fraction"] for x in rows])),
        }
    result["summary"]=summary
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Recover persistent filament lineage IDs from exported GADEN snapshots.

For the frozen House02 bank, emission_rate * sim_dt == 1 filament/step.
All filaments share the same initial sigma and deterministic sigma growth, so
sigma encodes filament age. A persistent birth-step key is then

    birth_step = snapshot_sim_step - age_level

No source coordinates or concentration targets are used.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np

def load_npz(path:Path):
    z=np.load(path,allow_pickle=False)
    return z["filaments"].astype(np.float32),z["offsets"].astype(np.int64),z["times_s"].astype(np.float64)

def sigma_levels(sigmas:np.ndarray,decimals:int):
    q=np.round(sigmas.astype(np.float64),decimals)
    levels=np.unique(q)
    levels.sort()
    return q,levels

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("filament_npz",type=Path)
    ap.add_argument("output_npz",type=Path)
    ap.add_argument("--sim-dt",type=float,default=0.1)
    ap.add_argument("--emission-rate",type=float,default=10.0)
    ap.add_argument("--sigma-decimals",type=int,default=6)
    args=ap.parse_args()
    eps=args.emission_rate*args.sim_dt
    if abs(eps-1.0)>1e-6:
        raise ValueError(
            "v1 exact birth-step reconstruction requires emission_rate*sim_dt == 1; "
            f"got {eps}. Use explicit particle matching for multi-emission steps.")

    fil,off,times=load_npz(args.filament_npz)
    q,levels=sigma_levels(fil[:,3],args.sigma_decimals)
    level_index={float(v):i for i,v in enumerate(levels)}
    age=np.fromiter((level_index[float(v)] for v in q),dtype=np.int64,count=len(q))
    lineage=np.empty(len(fil),dtype=np.int64)
    ambiguity=[]
    shared_counts=[]
    for k,t in enumerate(times):
        s,e=int(off[k]),int(off[k+1])
        step=int(round(float(t)/args.sim_dt))
        lineage[s:e]=step-age[s:e]
        u,c=np.unique(lineage[s:e],return_counts=True)
        ambiguity.append(int(np.sum(c>1)))
        if k:
            ps,pe=int(off[k-1]),int(off[k])
            shared_counts.append(int(np.intersect1d(lineage[ps:pe],lineage[s:e]).size))

    ambiguous_snapshots=sum(x>0 for x in ambiguity)
    if ambiguous_snapshots:
        raise RuntimeError(
            f"lineage ambiguity in {ambiguous_snapshots}/{len(times)} snapshots; "
            "sigma-only reconstruction contract is invalid for this bank")

    args.output_npz.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(args.output_npz,lineage_id=lineage,age_level=age,
                        sigma_levels=levels)
    manifest={
      "format":"gaden_filament_lineage_v1",
      "source":str(args.filament_npz),
      "sim_dt_s":args.sim_dt,"emission_rate_hz":args.emission_rate,
      "sigma_round_decimals":args.sigma_decimals,
      "sigma_age_levels":int(len(levels)),
      "snapshots":int(len(times)),
      "ambiguous_snapshots":int(ambiguous_snapshots),
      "adjacent_shared_lineage_min":int(min(shared_counts)) if shared_counts else 0,
      "adjacent_shared_lineage_median":float(np.median(shared_counts)) if shared_counts else 0.0,
      "decision":"LINEAGE_RECONSTRUCTION_PASS"
    }
    args.output_npz.with_suffix(".json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps(manifest,indent=2))

if __name__=="__main__":
    main()

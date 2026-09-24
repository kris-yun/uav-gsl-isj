#!/usr/bin/env python3
"""Reproduce the frozen R0 18-source calibration panel from Gate-1A C/D assets.

Selection is target-blind with respect to all new R0 realizations.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

PREVIOUS = np.array([
    [-2.242730141, -2.200880051],  # S1
    [-4.342730045,  2.899120331],  # S2
    [-4.342730045, -3.700880051],  # S3
], dtype=float)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-bank",type=Path,required=True)
    ap.add_argument("--prediction-root",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()

    bank=pd.read_csv(args.source_bank,sep="\t")
    seeds=[2026092401,2026092402]
    x=np.empty((len(bank),2,300),dtype=float)
    for si,s in enumerate(seeds):
        d=args.prediction_root/f"seed_{s}"
        for i,sid in enumerate(bank.source_id):
            x[i,si]=np.load(d/f"{sid}.npy",allow_pickle=False).reshape(-1)

    mu=x.mean(axis=1)
    rel=np.linalg.norm(x[:,0]-x[:,1],axis=1)/(np.linalg.norm(mu,axis=1)+1e-12)
    mass=mu.sum(axis=1)
    logmass=np.log1p(mass)

    xy=bank[["x_m","y_m"]].to_numpy(float)
    min_prev=np.min(
        np.stack([np.hypot(xy[:,0]-p[0],xy[:,1]-p[1]) for p in PREVIOUS],axis=1),
        axis=1,
    )
    eligible=min_prev>=2.0

    re=np.quantile(rel[eligible],[0,1/3,2/3,1])
    me=np.quantile(logmass[eligible],[0,1/3,2/3,1])
    rb=np.digitize(rel,re[1:-1],right=True)
    mb=np.digitize(logmass,me[1:-1],right=True)

    rows=[]
    labels=["low","mid","high"]
    ordinal=1
    for rbin in range(3):
        for mbin in range(3):
            idx=np.where(eligible & (rb==rbin) & (mb==mbin))[0]
            if len(idx)<2:
                raise RuntimeError(f"stratum {rbin},{mbin} has <2 sources")

            rmed=np.median(rel[idx])
            mmed=np.median(logmass[idx])
            rmad=np.median(np.abs(rel[idx]-rmed))
            mmad=np.median(np.abs(logmass[idx]-mmed))
            if rmad==0: rmad=1.0
            if mmad==0: mmad=1.0
            metric=((rel[idx]-rmed)/rmad)**2+((logmass[idx]-mmed)/mmad)**2

            order=sorted(range(len(idx)),key=lambda k:(metric[k],str(bank.source_id.iloc[idx[k]])))
            central=idx[order[0]]

            dist=np.hypot(xy[idx,0]-xy[central,0],xy[idx,1]-xy[central,1])
            md=dist.max()
            far_candidates=idx[np.isclose(dist,md)]
            spatial_far=sorted(far_candidates,key=lambda j:str(bank.source_id.iloc[j]))[0]

            for role,j in [("central",central),("spatial_far",spatial_far)]:
                b=bank.iloc[j]
                rows.append({
                    "panel_index":ordinal,
                    "source_id":b.source_id,
                    "x_m":float(b.x_m),
                    "y_m":float(b.y_m),
                    "z_m":float(b.z_m),
                    "legacy_cd_variability_stratum":labels[rbin],
                    "legacy_cd_mass_stratum":labels[mbin],
                    "selection_role":role,
                    "legacy_cd_rel_l2":float(rel[j]),
                    "legacy_cd_mean_mass":float(mass[j]),
                    "min_distance_to_S1_S2_S3_m":float(min_prev[j]),
                })
                ordinal+=1

    out=pd.DataFrame(rows)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    out.to_csv(args.out,sep="\t",index=False,float_format="%.12f")
    print(out.to_string(index=False))

if __name__=="__main__":
    main()

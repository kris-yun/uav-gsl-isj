#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--cube",type=Path,required=True)
    ap.add_argument("--contract",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    cube=np.load(a.cube,allow_pickle=False)
    assert cube.shape==(10,83,119)
    assert np.isfinite(cube).all() and (cube>=0).all()
    c=json.loads(a.contract.read_text())
    vals=[]
    for p in c["probe_points"]:
        x0,x1=int(p["native_x0"]),int(p["native_x1_exclusive"])
        y0,y1=int(p["native_y0"]),int(p["native_y1_exclusive"])
        vals.append(cube[:,x0:x1,y0:y1].mean(axis=(1,2)))
    pooled=np.stack(vals,axis=1).astype(np.float64)
    assert pooled.shape==(10,30)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    np.save(a.out,pooled,allow_pickle=False)
    print(a.out,pooled.shape,float(pooled.sum()))

if __name__=="__main__":
    main()

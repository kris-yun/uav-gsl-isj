#!/usr/bin/env python3
"""Export an immutable compact full-3D House02 transport bundle.

Read-only source-blind data step. It reads:
- House02 OccupancyGrid3D.csv
- canonical W1=3,5-1_fast wind_iteration_0..10
- canonical W2=3,5-1_slow wind_iteration_0..10

It writes float32 full-volume winds plus occupancy and provenance hashes.
No plume concentration, source-rank result, model checkpoint, or PMFS state is read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import numpy as np

EXPECTED_OCC_SHA = "9402690152be4568ced8f2256e9098d82691aaaa1f22a1887eeac55d0e5d098d"
EXPECTED_W1_ITER1_SHA = "2fa27ec72a7f05fbaca58b99e4f9390a5c477ee379d7e247e6fde57bbde49846"
EXPECTED_W2_ITER1_SHA = "54d7bc338ea681611f66004a3230f29feffc495446814607141b0623ef1dd9a8"
SOURCES = {
    "S1": (-2.242730141, -2.200880051, 0.20),
    "S2": (-4.342730045,  2.899120331, 0.20),
}


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()


def read_occupancy(path: Path):
    lines=path.read_text(encoding="utf-8",errors="replace").splitlines()
    headers={}
    start=None
    for i,line in enumerate(lines):
        if line.startswith("#"):
            toks=line[1:].split()
            if toks:
                headers[toks[0]]=[float(x) for x in toks[1:]]
        else:
            start=i
            break
    if start is None:
        raise ValueError("occupancy contains no data")
    nx,ny,nz=map(int,headers["num_cells"])
    vals=np.fromiter(
        (int(x) for line in lines[start:] if line.strip()!=";" for x in line.split()),
        dtype=np.int8,
    )
    if vals.size != nx*ny*nz:
        raise ValueError(f"occupancy values {vals.size} != {nx*ny*nz}")
    # [z,x,y], same convention as frozen C0.5 context.
    return headers,vals.reshape(nz,nx,ny)


def read_wind(path: Path,nx:int,ny:int,nz:int) -> np.ndarray:
    n=nx*ny*nz
    raw=path.read_bytes()
    legacy=3*n*8
    modern=8+legacy
    if len(raw)==legacy:
        comp=np.frombuffer(raw,dtype="<f8").reshape(3,nz,ny,nx)
        arr=comp.transpose(1,3,2,0)
    elif len(raw)==modern:
        major,minor=struct.unpack_from("<ii",raw,0)
        if major < 2:
            raise ValueError(f"unexpected modern wind header {(major,minor)}")
        arr=np.frombuffer(raw,dtype="<f8",offset=8).reshape(nz,ny,nx,3).transpose(0,2,1,3)
    else:
        raise ValueError(f"{path}: unexpected byte count {len(raw)}")
    if not np.isfinite(arr).all():
        raise ValueError(f"{path}: nonfinite wind")
    return arr


def load_sequence(directory:Path,nx:int,ny:int,nz:int):
    seq=[]; records=[]
    for i in range(11):
        p=directory/f"wind_iteration_{i}"
        if not p.is_file():
            raise FileNotFoundError(p)
        a=read_wind(p,nx,ny,nz)
        seq.append(a.astype(np.float32))
        records.append({"iteration":i,"sha256":sha256(p),"bytes":p.stat().st_size})
    return np.stack(seq,axis=0),records


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--scenario-root",type=Path,
                    default=Path("/mnt/hgfs/workspace/GADEN_files/scenarios/House02"))
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--force",action="store_true")
    args=ap.parse_args()

    root=args.scenario_root
    occ_path=root/"OccupancyGrid3D.csv"
    w1_dir=root/"gas_simulations/3,5-1_fast/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20/wind"
    w2_dir=root/"gas_simulations/3,5-1_slow/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20/wind"

    if args.out.exists() and any(args.out.iterdir()) and not args.force:
        raise RuntimeError(f"refuse nonempty output directory: {args.out}")
    args.out.mkdir(parents=True,exist_ok=True)

    occ_sha=sha256(occ_path)
    if occ_sha != EXPECTED_OCC_SHA:
        raise RuntimeError(f"occupancy anchor mismatch {occ_sha}")

    headers,occ=read_occupancy(occ_path)
    nx,ny,nz=map(int,headers["num_cells"])
    env_min=headers["env_min(m)"]
    cell=float(headers["cell_size(m)"][0])

    w1,r1=load_sequence(w1_dir,nx,ny,nz)
    w2,r2=load_sequence(w2_dir,nx,ny,nz)

    if r1[1]["sha256"] != EXPECTED_W1_ITER1_SHA:
        raise RuntimeError("W1 iteration-1 anchor mismatch")
    if r2[1]["sha256"] != EXPECTED_W2_ITER1_SHA:
        raise RuntimeError("W2 iteration-1 anchor mismatch")

    # Inventory established that the initial fields are identical.
    if r1[0]["sha256"] != r2[0]["sha256"]:
        raise RuntimeError("expected W1/W2 iteration-0 equality")

    source_indices={}
    for sid,(sx,sy,sz) in SOURCES.items():
        ix=int(np.floor((sx-env_min[0])/cell))
        iy=int(np.floor((sy-env_min[1])/cell))
        iz=int(round((sz-env_min[2])/cell))
        if not (0<=ix<nx and 0<=iy<ny and 0<=iz<nz):
            raise RuntimeError(f"{sid} index out of bounds {(ix,iy,iz)}")
        if int(occ[iz,ix,iy]) != 0:
            raise RuntimeError(f"{sid} not free at {(ix,iy,iz)}")
        source_indices[sid]={"xyz_m":[sx,sy,sz],"grid_xyz":[ix,iy,iz]}

    occ_out=args.out/"occupancy_full3d.npy"
    w1_out=args.out/"wind_W1_full3d_float32.npz"
    w2_out=args.out/"wind_W2_full3d_float32.npz"
    np.save(occ_out,occ,allow_pickle=False)
    np.savez_compressed(w1_out,wind=w1)
    np.savez_compressed(w2_out,wind=w2)

    manifest={
        "purpose":"Compact-3D hidden-transport development input; no plume outcomes",
        "house":"House02",
        "canonical_paths":{
            "occupancy":str(occ_path),"W1":str(w1_dir),"W2":str(w2_dir),
        },
        "dimensions_xyz":[nx,ny,nz],
        "array_convention":{
            "occupancy":"[z,x,y]",
            "wind":"[iteration,z,x,y,component_xyz]",
        },
        "env_min_m":env_min,
        "cell_m":cell,
        "source_indices":source_indices,
        "input_anchors":{
            "occupancy_sha256":occ_sha,
            "W1_iteration1_sha256":r1[1]["sha256"],
            "W2_iteration1_sha256":r2[1]["sha256"],
            "W1_W2_iteration0_equal":True,
        },
        "W1_records":r1,
        "W2_records":r2,
        "output":{
            "occupancy":{"file":occ_out.name,"sha256":sha256(occ_out),"shape":list(occ.shape),"dtype":str(occ.dtype)},
            "W1":{"file":w1_out.name,"sha256":sha256(w1_out),"shape":list(w1.shape),"dtype":str(w1.dtype)},
            "W2":{"file":w2_out.name,"sha256":sha256(w2_out),"shape":list(w2.shape),"dtype":str(w2.dtype)},
        },
    }
    mpath=args.out/"compact3d_manifest.json"
    mpath.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    with (args.out/"SHA256SUMS").open("w",encoding="utf-8") as f:
        for p in (occ_out,w1_out,w2_out,mpath):
            f.write(f"{sha256(p)}  {p.name}\n")

    print(json.dumps({
        "status":"COMPACT3D_EXPORT_OK",
        "dimensions_xyz":[nx,ny,nz],
        "W1_shape":list(w1.shape),
        "W2_shape":list(w2.shape),
        "output_dir":str(args.out),
        "output_bytes":sum(p.stat().st_size for p in (occ_out,w1_out,w2_out,mpath)),
    },indent=2))


if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Export the complete House02 sensor-height GADEN wind sequence for M4-v3.

Read-only. No plume field, source truth, PMFS state, or model outcome is read.
The output is a compact [iteration,x,y,component] float32 tensor plus provenance.
"""
from __future__ import annotations
import argparse, hashlib, json, re, struct
from pathlib import Path
import numpy as np

WIND_RE = re.compile(r"^wind_iteration_(\d+)$")

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def read_occ_header(path: Path):
    header={}
    for line in path.read_text(encoding="utf-8",errors="replace").splitlines()[:30]:
        if line.startswith("#num_cells"):
            header["dims"]=[int(x) for x in line.split()[1:]]
        elif line.startswith("#env_min"):
            header["env_min"]=[float(x) for x in line.split()[1:]]
        elif line.startswith("#cell_size"):
            vals=[float(x) for x in line.split()[1:]]
            header["cell"]=vals[0]
    if not {"dims","env_min","cell"} <= set(header):
        raise ValueError("occupancy header incomplete")
    return header

def read_wind(path: Path, n: int) -> np.ndarray:
    raw=path.read_bytes()
    legacy=n*3*8
    modern=8+legacy
    if len(raw)==legacy:
        c=np.frombuffer(raw,dtype="<f8").reshape(3,n)
        return np.column_stack((c[0],c[1],c[2]))
    if len(raw)==modern:
        major,minor=struct.unpack_from("<ii",raw,0)
        if major < 2: raise ValueError(f"unexpected modern header {(major,minor)}")
        return np.frombuffer(raw,dtype="<f8",offset=8).reshape(n,3)
    raise ValueError(f"{path}: bad byte count {len(raw)}")

def export_one(wind_dir: Path, dims, z_index: int):
    nx,ny,nz=dims
    n=nx*ny*nz
    rec=[]
    for p in wind_dir.iterdir():
        m=WIND_RE.match(p.name)
        if m and p.is_file(): rec.append((int(m.group(1)),p))
    rec.sort()
    if [i for i,_ in rec] != list(range(len(rec))):
        raise ValueError("wind iterations are not contiguous")
    seq=[]
    hashes=[]
    for idx,p in rec:
        v=read_wind(p,n)
        # Legacy GADEN linear index: x + y*nx + z*nx*ny.
        xyz=v.reshape(nz,ny,nx,3).transpose(0,2,1,3)
        sl=xyz[z_index].astype(np.float32)
        if not np.isfinite(sl).all(): raise ValueError(f"nonfinite {p}")
        seq.append(sl)
        hashes.append({"iteration":idx,"sha256":sha256(p),"bytes":p.stat().st_size})
    return np.stack(seq),hashes

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("occupancy",type=Path)
    ap.add_argument("wind_w1",type=Path)
    ap.add_argument("wind_w2",type=Path)
    ap.add_argument("out",type=Path)
    ap.add_argument("--sensor-z",type=float,default=0.20)
    ap.add_argument("--wind-iteration-dt",type=float,default=1.0)
    ap.add_argument("--loop-from",type=int,default=1)
    ap.add_argument("--loop-to",type=int,default=10)
    args=ap.parse_args()
    h=read_occ_header(args.occupancy)
    nx,ny,nz=h["dims"]
    zi=int(round((args.sensor_z-h["env_min"][2])/h["cell"]))
    if not 0<=zi<nz: raise ValueError("sensor z outside grid")
    s1,h1=export_one(args.wind_w1,h["dims"],zi)
    s2,h2=export_one(args.wind_w2,h["dims"],zi)
    if s1.shape!=s2.shape: raise ValueError("W1/W2 shape mismatch")
    if not (0<=args.loop_from<=args.loop_to<s1.shape[0]):
        raise ValueError("invalid loop bounds")
    args.out.mkdir(parents=True,exist_ok=True)
    p1=args.out/"wind_W1_sequence_z0p20.npy"
    p2=args.out/"wind_W2_sequence_z0p20.npy"
    np.save(p1,s1,allow_pickle=False); np.save(p2,s2,allow_pickle=False)
    manifest={
      "purpose":"M4-v3 development input; geometry/wind only",
      "occupancy_path":str(args.occupancy),
      "occupancy_sha256":sha256(args.occupancy),
      "dims_xyz":[nx,ny,nz],"cell_m":h["cell"],
      "sensor_z_m":args.sensor_z,"sensor_z_index":zi,
      "sequence_shape":list(s1.shape),
      "wind_iteration_dt_s":args.wind_iteration_dt,
      "loop":{"enabled":True,"from":args.loop_from,"to":args.loop_to},
      "W1":{"path":str(args.wind_w1),"records":h1,"export_sha256":sha256(p1)},
      "W2":{"path":str(args.wind_w2),"records":h2,"export_sha256":sha256(p2)},
      "iteration1_matches_existing_contract":{
        "W1_expected":"2fa27ec72a7f05fbaca58b99e4f9390a5c477ee379d7e247e6fde57bbde49846",
        "W2_expected":"54d7bc338ea681611f66004a3230f29feffc495446814607141b0623ef1dd9a8",
        "W1_actual":h1[1]["sha256"],"W2_actual":h2[1]["sha256"],
        "pass":h1[1]["sha256"]=="2fa27ec72a7f05fbaca58b99e4f9390a5c477ee379d7e247e6fde57bbde49846" and h2[1]["sha256"]=="54d7bc338ea681611f66004a3230f29feffc495446814607141b0623ef1dd9a8"
      }
    }
    (args.out/"wind_sequence_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    if not manifest["iteration1_matches_existing_contract"]["pass"]:
        raise RuntimeError("iteration-1 hash does not match frozen House02 context")
    print(json.dumps({"shape":list(s1.shape),"W1_sha256":sha256(p1),"W2_sha256":sha256(p2),"manifest":"wind_sequence_manifest.json"},indent=2))

if __name__=="__main__": main()

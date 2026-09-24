#!/usr/bin/env python3
"""Export complete 3-D GADEN wind sequences for source-lineage L1.

Output shape: [iteration, z, x, y, 3] float32.
Read-only; no gas/source outcomes are opened.
"""
from __future__ import annotations
import argparse, hashlib, json, re, struct
from pathlib import Path
import numpy as np

WIND_RE=re.compile(r"^wind_iteration_(\d+)$")

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def read_occ_header(path:Path):
    h={}
    for line in path.read_text(encoding="utf-8",errors="replace").splitlines()[:30]:
        if line.startswith("#num_cells"): h["dims"]=[int(x) for x in line.split()[1:]]
        elif line.startswith("#env_min"): h["env_min"]=[float(x) for x in line.split()[1:]]
        elif line.startswith("#cell_size"): h["cell"]=float(line.split()[1])
    if not {"dims","env_min","cell"}<=set(h): raise ValueError("occupancy header incomplete")
    return h

def read_wind(path:Path,n:int)->np.ndarray:
    raw=path.read_bytes()
    legacy=n*3*8
    modern=8+legacy
    if len(raw)==legacy:
        c=np.frombuffer(raw,dtype="<f8").reshape(3,n)
        return np.column_stack((c[0],c[1],c[2]))
    if len(raw)==modern:
        major,minor=struct.unpack_from("<ii",raw,0)
        if major<2: raise ValueError(f"unexpected wind header {(major,minor)}")
        return np.frombuffer(raw,dtype="<f8",offset=8).reshape(n,3)
    raise ValueError(f"{path}: bad byte count {len(raw)}")

def export_one(wind_dir:Path,dims):
    nx,ny,nz=dims; n=nx*ny*nz
    rec=[]
    for p in wind_dir.iterdir():
        m=WIND_RE.match(p.name)
        if m and p.is_file(): rec.append((int(m.group(1)),p))
    rec.sort()
    if [i for i,_ in rec] != list(range(len(rec))): raise ValueError("wind iterations not contiguous")
    seq=[]; hashes=[]
    for idx,p in rec:
        v=read_wind(p,n)
        xyz=v.reshape(nz,ny,nx,3).transpose(0,2,1,3).astype(np.float32)
        if not np.isfinite(xyz).all(): raise ValueError(f"nonfinite {p}")
        seq.append(xyz)
        hashes.append({"iteration":idx,"sha256":sha256(p),"bytes":p.stat().st_size})
    return np.stack(seq),hashes

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("occupancy",type=Path)
    ap.add_argument("wind_w1",type=Path)
    ap.add_argument("wind_w2",type=Path)
    ap.add_argument("out",type=Path)
    ap.add_argument("--wind-iteration-dt",type=float,default=1.0)
    ap.add_argument("--loop-from",type=int,default=1)
    ap.add_argument("--loop-to",type=int,default=10)
    args=ap.parse_args()
    h=read_occ_header(args.occupancy)
    w1,h1=export_one(args.wind_w1,h["dims"])
    w2,h2=export_one(args.wind_w2,h["dims"])
    if w1.shape!=w2.shape: raise ValueError("W1/W2 shape mismatch")
    args.out.mkdir(parents=True,exist_ok=True)
    p1=args.out/"wind_W1_sequence_3d.npy"; p2=args.out/"wind_W2_sequence_3d.npy"
    np.save(p1,w1,allow_pickle=False); np.save(p2,w2,allow_pickle=False)
    m={
      "format":"gaden_wind_3d_v1",
      "dims_xyz":h["dims"],"env_min_xyz":h["env_min"],"cell_m":h["cell"],
      "shape":list(w1.shape),"wind_iteration_dt_s":args.wind_iteration_dt,
      "loop":{"enabled":True,"from":args.loop_from,"to":args.loop_to},
      "occupancy_path":str(args.occupancy),"occupancy_sha256":sha256(args.occupancy),
      "W1":{"path":str(args.wind_w1),"records":h1,"sha256":sha256(p1)},
      "W2":{"path":str(args.wind_w2),"records":h2,"sha256":sha256(p2)}
    }
    (args.out/"wind_3d_manifest.json").write_text(json.dumps(m,indent=2)+"\n")
    print(json.dumps({"shape":list(w1.shape),"manifest":"wind_3d_manifest.json"},indent=2))
if __name__=="__main__": main()

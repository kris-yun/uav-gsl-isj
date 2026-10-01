#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, struct
from pathlib import Path
import numpy as np

WIND_RE = re.compile(r"^wind_iteration_(\d+)$")

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1<<20), b""):
            h.update(b)
    return h.hexdigest()

def read_occ_header(path: Path):
    out={}
    for line in path.read_text(encoding="utf-8",errors="replace").splitlines()[:30]:
        if line.startswith("#env_min"):
            out["env_min"]=[float(x) for x in line.split()[1:]]
        elif line.startswith("#num_cells"):
            out["dims"]=[int(x) for x in line.split()[1:]]
        elif line.startswith("#cell_size"):
            out["cell"]=float(line.split()[1])
    if not {"env_min","dims","cell"} <= set(out):
        raise ValueError("occupancy header incomplete")
    return out

def read_wind(path: Path, n: int):
    raw=path.read_bytes()
    legacy=n*3*8
    modern=8+legacy
    if len(raw)==legacy:
        c=np.frombuffer(raw,dtype="<f8").reshape(3,n).copy()
        arr=np.column_stack((c[0],c[1],c[2]))
        return arr, {"format":"legacy_component_major","header":b""}
    if len(raw)==modern:
        major,minor=struct.unpack_from("<ii",raw,0)
        if major < 2:
            raise ValueError(f"unexpected modern header {(major,minor)}")
        arr=np.frombuffer(raw,dtype="<f8",offset=8).reshape(n,3).copy()
        return arr, {"format":"modern_cell_major","header":raw[:8],"version":[major,minor]}
    raise ValueError(f"{path}: bad byte count {len(raw)} expected {legacy} or {modern}")

def write_wind(path: Path, arr: np.ndarray, meta: dict):
    arr=np.asarray(arr,dtype="<f8")
    if meta["format"]=="legacy_component_major":
        raw=np.vstack((arr[:,0],arr[:,1],arr[:,2])).astype("<f8",copy=False).tobytes(order="C")
    elif meta["format"]=="modern_cell_major":
        raw=meta["header"]+arr.astype("<f8",copy=False).tobytes(order="C")
    else:
        raise ValueError(meta["format"])
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(raw)

def project(arr: np.ndarray, dims, zi: int) -> np.ndarray:
    nx,ny,nz=dims
    if arr.shape != (nx*ny*nz,3):
        raise ValueError((arr.shape,dims))
    vol=arr.reshape(nz,ny,nx,3).copy()
    sl=vol[zi].copy()
    vol[...,0]=sl[None,...,0]
    vol[...,1]=sl[None,...,1]
    vol[...,2]=0.0
    return vol.reshape(-1,3)

def self_test():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        n=2*3*2
        a=np.arange(n*3,dtype=np.float64).reshape(n,3)/10
        p=td/"legacy"
        write_wind(p,a,{"format":"legacy_component_major","header":b""})
        b,m=read_wind(p,n)
        assert np.array_equal(a,b) and m["format"].startswith("legacy")
        p2=td/"modern"
        hdr=struct.pack("<ii",2,0)
        write_wind(p2,a,{"format":"modern_cell_major","header":hdr})
        b2,m2=read_wind(p2,n)
        assert np.array_equal(a,b2) and m2["version"]==[2,0]
        c=project(a,[2,3,2],1).reshape(2,3,2,3)
        assert np.all(c[...,2]==0)
        assert np.array_equal(c[0,...,:2],c[1,...,:2])
    print("PMFS3D_WIND_PROJECTION_SELF_TEST_PASS")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("occupancy",type=Path,nargs="?")
    ap.add_argument("wind_dir",type=Path,nargs="?")
    ap.add_argument("out_dir",type=Path,nargs="?")
    ap.add_argument("--sensor-z",type=float,default=0.20)
    ap.add_argument("--self-test",action="store_true")
    args=ap.parse_args()
    if args.self_test:
        self_test()
        return
    if not (args.occupancy and args.wind_dir and args.out_dir):
        ap.error("occupancy wind_dir out_dir required")
    h=read_occ_header(args.occupancy)
    nx,ny,nz=h["dims"]
    n=nx*ny*nz
    zi=int(round((args.sensor_z-h["env_min"][2])/h["cell"]))
    if not 0<=zi<nz:
        raise ValueError("sensor z outside grid")
    rec=[]
    for p in args.wind_dir.iterdir():
        m=WIND_RE.match(p.name)
        if m and p.is_file():
            rec.append((int(m.group(1)),p))
    rec.sort()
    if [i for i,_ in rec] != list(range(len(rec))):
        raise ValueError("wind iterations not contiguous")
    args.out_dir.mkdir(parents=True,exist_ok=False)
    rows=[]
    for idx,p in rec:
        a,meta=read_wind(p,n)
        b=project(a,h["dims"],zi)
        out=args.out_dir/p.name
        write_wind(out,b,meta)
        rows.append({
          "iteration":idx,
          "input":str(p),
          "input_sha256":sha256(p),
          "output":str(out),
          "output_sha256":sha256(out),
          "format":meta["format"],
          "max_abs_w":float(np.max(np.abs(b[:,2]))),
          "uv_source_slice_preserved":bool(np.array_equal(
              a.reshape(nz,ny,nx,3)[zi,...,:2],
              b.reshape(nz,ny,nx,3)[zi,...,:2]))
        })
    manifest={
      "method":"PMFS3D_O0_PROJECTED_2D_WIND",
      "definition":"replicate sensor-height u,v through all z; set w=0",
      "occupancy":str(args.occupancy),
      "occupancy_sha256":sha256(args.occupancy),
      "dims_xyz":h["dims"],
      "cell_m":h["cell"],
      "sensor_z_m":args.sensor_z,
      "sensor_z_index":zi,
      "source_wind_dir":str(args.wind_dir),
      "records":rows
    }
    (args.out_dir/"projection_manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    if not all(x["max_abs_w"]==0.0 and x["uv_source_slice_preserved"] for x in rows):
        raise RuntimeError("projection audit failed")
    print(json.dumps({"decision":"PMFS3D_PROJECTED2D_WIND_PASS","out":str(args.out_dir),"iterations":len(rows)},indent=2))

if __name__=="__main__":
    main()

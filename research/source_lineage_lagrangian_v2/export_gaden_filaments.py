#!/usr/bin/env python3
"""Export GADEN filament snapshots without ROS/GADEN runtime dependencies.

Supports legacy zlib result files (v1, v2.x) and modern GADEN_RESULT files
when compression is raw or zlib. LIBBSC files are rejected explicitly.

Output NPZ stores concatenated [x,y,z,sigma] float32 filaments plus snapshot
offsets/iterations. No concentration reconstruction is performed.
"""
from __future__ import annotations

import argparse, hashlib, json, math, re, struct, zlib
from pathlib import Path
import numpy as np

IDENT=b"GADEN_RESULT"
MODERN_HEADER_BYTES=len(IDENT)+1+1+8  # C-string incl. NUL + mode + size_t


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):
            h.update(chunk)
    return h.hexdigest()


def decompress_result(path: Path) -> tuple[bytes,str]:
    data=path.read_bytes()
    if data.startswith(IDENT):
        # sizeof("GADEN_RESULT") in C++ includes terminating NUL.
        if len(data) < MODERN_HEADER_BYTES or data[len(IDENT)] != 0:
            raise ValueError(f"{path}: malformed modern header")
        mode=data[len(IDENT)+1]
        usize=struct.unpack_from("<Q",data,len(IDENT)+2)[0]
        payload=data[MODERN_HEADER_BYTES:]
        if mode==0:
            raw=payload
            comp="none"
        elif mode==1:
            raw=zlib.decompress(payload)
            comp="zlib"
        elif mode==2:
            raise RuntimeError(
                f"{path}: LIBBSC-compressed snapshot. Use gaden_core PlaybackSimulation "
                "or re-export/decompress with GADEN's libbsc utility.")
        else:
            raise ValueError(f"{path}: unknown compression mode {mode}")
        if usize and len(raw)!=usize:
            raise ValueError(f"{path}: uncompressed size mismatch {len(raw)} != {usize}")
        return raw,comp
    return zlib.decompress(data),"legacy-zlib"


def _valid_rows(a: np.ndarray) -> bool:
    return bool(
        a.ndim==2 and a.shape[1]==4 and np.isfinite(a).all()
        and (a[:,3] > 0).all()
        and (np.abs(a[:,:3]) < 1e5).all()
    )


def parse_modern_filaments(raw: bytes) -> np.ndarray:
    marker=b"filaments"
    pos=raw.rfind(marker)
    if pos<8:
        raise ValueError("modern snapshot has no filaments marker")
    if struct.unpack_from("<Q",raw,pos-8)[0] != len(marker):
        raise ValueError("modern filament marker length mismatch")
    vec_size_pos=pos+len(marker)
    n=struct.unpack_from("<Q",raw,vec_size_pos)[0]
    data_pos=vec_size_pos+8
    if data_pos+n*16 != len(raw):
        raise ValueError("modern filament vector does not terminate at buffer end")
    a=np.frombuffer(raw,dtype="<f4",count=n*4,offset=data_pos).reshape(n,4).copy()
    if not _valid_rows(a):
        raise ValueError("modern filament values failed sanity checks")
    return a


def parse_legacy_filaments(raw: bytes) -> tuple[np.ndarray,int,int]:
    if len(raw)<8:
        raise ValueError("legacy snapshot too short")
    major=struct.unpack_from("<i",raw,0)[0]
    minor=0 if major==1 else struct.unpack_from("<i",raw,4)[0]

    if major==1 or (major==2 and minor<=5):
        rec_size,fmt=36,"<idddd"
    elif major==2:
        rec_size,fmt=20,"<iffff"
    else:
        # v3+ without modern outer header still uses vector serialization.
        return parse_modern_filaments(raw),major,minor

    # Legacy metadata is small. The filament suffix stores sequential indices.
    limit=min(len(raw),8192)
    for start in range(4,limit,4):
        rem=len(raw)-start
        if rem<=0 or rem%rec_size:
            continue
        n=rem//rec_size
        rows=np.empty((n,4),dtype=np.float32)
        ok=True
        for j in range(n):
            vals=struct.unpack_from(fmt,raw,start+j*rec_size)
            if vals[0] != j:
                ok=False
                break
            rows[j]=vals[1:5]
        if ok and _valid_rows(rows):
            return rows,major,minor
    raise ValueError(f"could not locate legacy filament suffix for v{major}.{minor}")


def parse_snapshot(path: Path) -> tuple[np.ndarray,dict]:
    raw,compression=decompress_result(path)
    major=struct.unpack_from("<i",raw,0)[0]
    minor=0
    if major>=2 and len(raw)>=8:
        minor=struct.unpack_from("<i",raw,4)[0]
    if major>=3:
        arr=parse_modern_filaments(raw)
    else:
        arr,major,minor=parse_legacy_filaments(raw)
    return arr,{"major":int(major),"minor":int(minor),"compression":compression}


def select_iterations(results: Path,start:int|None,stop:int|None,stride:int):
    found=[]
    rx=re.compile(r"^iteration_(\d+)$")
    for p in results.iterdir():
        m=rx.match(p.name)
        if m and p.is_file():
            i=int(m.group(1))
            if start is not None and i<start: continue
            if stop is not None and i>stop: continue
            if (start is not None and (i-start)%stride) or (start is None and i%stride):
                continue
            found.append((i,p))
    found.sort()
    if not found:
        raise FileNotFoundError(f"no iteration_* snapshots in {results}")
    return found


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("results_dir",type=Path)
    ap.add_argument("output_npz",type=Path)
    ap.add_argument("--start",type=int)
    ap.add_argument("--stop",type=int)
    ap.add_argument("--stride",type=int,default=1)
    ap.add_argument("--snapshot-dt",type=float,default=0.5)
    ap.add_argument("--hash-inputs",action="store_true")
    args=ap.parse_args()
    if args.stride<1: raise ValueError("--stride must be >=1")

    items=select_iterations(args.results_dir,args.start,args.stop,args.stride)
    arrays=[]; offsets=[0]; versions=set(); comps=set(); hashes={}
    for it,p in items:
        a,meta=parse_snapshot(p)
        arrays.append(a); offsets.append(offsets[-1]+len(a))
        versions.add((meta["major"],meta["minor"])); comps.add(meta["compression"])
        if args.hash_inputs: hashes[p.name]=sha256(p)

    fil=np.concatenate(arrays,axis=0) if arrays else np.empty((0,4),np.float32)
    iterations=np.asarray([i for i,_ in items],dtype=np.int32)
    offsets=np.asarray(offsets,dtype=np.int64)
    times=iterations.astype(np.float64)*float(args.snapshot_dt)

    args.output_npz.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(args.output_npz,filaments=fil,offsets=offsets,
                        iterations=iterations,times_s=times)
    manifest={
        "format":"gaden_filament_npz_v1",
        "source_directory":str(args.results_dir.resolve()),
        "snapshots":len(items),"filaments_total":int(len(fil)),
        "versions":[list(x) for x in sorted(versions)],
        "compressions":sorted(comps),
        "snapshot_dt_s":float(args.snapshot_dt),
        "columns":["x_m","y_m","z_m","sigma_gaden"],
        "input_sha256":hashes,
        "output_sha256":sha256(args.output_npz),
    }
    args.output_npz.with_suffix(".json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps(manifest,indent=2))


if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Independently verify portable archive of all 180 E2 raw cubes and pooled vectors."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import tarfile
from pathlib import Path

import numpy as np


def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda:f.read(1024*1024),b""):
            h.update(part)
    return h.hexdigest()


def rows(path:Path)->list[dict]:
    with path.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f,delimiter="\t"))


def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--archive",type=Path,required=True)
    p.add_argument("--evidence",type=Path,required=True)
    p.add_argument("--probe-contract",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    reference=rows(a.evidence/"JTD_E2_NEW_REFERENCE_MANIFEST.tsv")
    target=rows(a.evidence/"JTD_E2_FRESH_TARGET_MANIFEST.tsv")
    all_rows=reference+target
    assert len(reference)==108 and len(target)==72
    probes_all=rows(a.probe_contract)
    probes={h:sorted([q for q in probes_all if q["house"]==h],key=lambda x:int(x["probe_rank"]))
            for h in ("House01","House02")}
    ref_tensor=np.load(a.evidence/"JTD_E2_NEW_REFERENCE_10x30.npy",allow_pickle=False)
    target_tensor=np.load(a.evidence/"JTD_E2_FRESH_TARGET_10x30.npy",allow_pickle=False)
    checked=set(); metadata_count=0
    with tarfile.open(a.archive,"r:gz") as archive:
        members={q.name:q for q in archive.getmembers() if q.isfile()}
        for row in all_rows:
            phase=row["phase"]
            prefix=row["run_dir"].removeprefix("/home/zyc/")
            cube_name=prefix+"/concentration.npy"
            pooled_name=prefix+"/pooled.npy"
            metadata_name=prefix+"/run_metadata.json"
            for name in (cube_name,pooled_name,metadata_name):
                assert name in members and name not in checked
                checked.add(name)
            cube_bytes=archive.extractfile(members[cube_name]).read()
            pooled_bytes=archive.extractfile(members[pooled_name]).read()
            assert hashlib.sha256(cube_bytes).hexdigest()==row["cube_sha256"]
            assert hashlib.sha256(pooled_bytes).hexdigest()==row["pooled_sha256"]
            meta=json.load(archive.extractfile(members[metadata_name]))
            assert meta["cube_sha256"]==row["cube_sha256"] and meta["requested_seed"]==int(row["requested_seed"])
            metadata_count+=1
            cube=np.load(io.BytesIO(cube_bytes),allow_pickle=False)
            pooled=np.load(io.BytesIO(pooled_bytes),allow_pickle=False)
            house=row["house"]
            assert cube.shape==((10,87,114) if house=="House01" else (10,83,119))
            repooled=np.stack([cube[:,int(q["native_x0"]):int(q["native_x1_exclusive"]),
                                     int(q["native_y0"]):int(q["native_y1_exclusive"])].mean(axis=(1,2))
                               for q in probes[house]],axis=1).astype(np.float32)
            assert np.array_equal(repooled,pooled)
            ei,si,ri=(int(row[k]) for k in ("environment_index","source_index","new_index"))
            expected=ref_tensor[ei,si,ri] if phase=="REFERENCE" else target_tensor[ei,si,ri]
            assert np.array_equal(pooled,expected)
    output={"raw_archive_validation":"PASS","reference_cube_count":108,"target_cube_count":72,
            "metadata_count":metadata_count,"exact_repool_and_tensor_match_count":180,
            "archive_sha256":sha(a.archive),"archive_bytes":a.archive.stat().st_size,
            "sealed_data_included":False}
    a.out.write_bytes((json.dumps(output,indent=2,sort_keys=True)+"\n").encode("utf-8"))
    print("JTD_E2_RAW_ARCHIVE_VERIFICATION_PASS",output["archive_sha256"])


if __name__=="__main__":
    main()

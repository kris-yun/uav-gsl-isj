#!/usr/bin/env python3
"""Re-extract all 36 fresh target observations from archived concentration cubes."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import tarfile
from pathlib import Path

import numpy as np

TARGET_ROOT = Path("/home/zyc/JTD_E1_FRESH_TARGETS_20260925")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--raw-tar", type=Path, required=True)
    parser.add_argument("--probe-contract", type=Path, required=True)
    args = parser.parse_args()
    out = args.out
    lock = json.loads((out / "JTD_E1_PRE_RUN_LOCK.json").read_text(encoding="utf-8"))
    if sha(args.probe_contract.read_bytes()) != lock["probe_contract_sha256"]:
        raise ValueError("E1 observation contract hash drift")
    with args.probe_contract.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    probes = {house: sorted((r for r in rows if r["house"] == house),
                            key=lambda r: int(r["probe_rank"])) for house in ("House01", "House02")}
    if any(len(group) != 30 for group in probes.values()):
        raise ValueError("30-probe contract drift")
    with (out / "JTD_E1_TARGET_MANIFEST.tsv").open(newline="", encoding="utf-8") as stream:
        manifest = list(csv.DictReader(stream, delimiter="\t"))
    if len(manifest) != 36:
        raise ValueError("fresh target manifest count drift")
    observations = np.load(out / "JTD_E1_FRESH_TARGETS_10x30.npy", allow_pickle=False)
    if observations.shape != (3,6,2,10,30):
        raise ValueError("target observation tensor drift")
    checked = []
    with tarfile.open(args.raw_tar, "r:gz") as archive:
        member_names = {m.name for m in archive.getmembers() if m.isfile()}
        if len([n for n in member_names if n.endswith("/concentration.npy")]) != 36:
            raise ValueError("raw review tar cube count drift")
        for row in manifest:
            run_dir = Path(row["run_dir"])
            if not run_dir.is_relative_to(TARGET_ROOT):
                raise ValueError("raw target path escaped E1 fresh-target root")
            prefix = Path(TARGET_ROOT.name) / run_dir.relative_to(TARGET_ROOT)
            blobs = {}
            for name in ("concentration.npy", "pooled.npy", "run_metadata.json"):
                member_name = (prefix / name).as_posix()
                if member_name not in member_names:
                    raise ValueError(f"missing raw target archive member: {member_name}")
                with archive.extractfile(member_name) as stream:
                    blobs[name] = stream.read()
            if sha(blobs["concentration.npy"]) != row["cube_sha256"]:
                raise ValueError("raw cube hash mismatch")
            if sha(blobs["pooled.npy"]) != row["pooled_sha256"]:
                raise ValueError("raw pooled hash mismatch")
            meta = json.loads(blobs["run_metadata.json"])
            if meta["requested_seed"] != int(row["requested_seed"]) or meta["cube_sha256"] != row["cube_sha256"]:
                raise ValueError("raw target simulator metadata mismatch")
            cube = np.load(io.BytesIO(blobs["concentration.npy"]), allow_pickle=False)
            shape = (10,87,114) if row["house"] == "House01" else (10,83,119)
            if cube.shape != shape or not np.isfinite(cube).all() or (cube < 0).any():
                raise ValueError("raw cube QC failure")
            vals = []
            for p in probes[row["house"]]:
                x0, x1 = int(p["native_x0"]), int(p["native_x1_exclusive"])
                y0, y1 = int(p["native_y0"]), int(p["native_y1_exclusive"])
                vals.append(cube[:,x0:x1,y0:y1].mean(axis=(1,2)))
            repooled = np.stack(vals,axis=1).astype(np.float32)
            pooled = np.load(io.BytesIO(blobs["pooled.npy"]), allow_pickle=False)
            e,s,t = (int(row[k]) for k in ("environment_index","source_index","target_replicate"))
            if not np.array_equal(repooled,pooled) or not np.array_equal(repooled,observations[e,s,t]):
                raise ValueError("exact raw target 10x30 re-extraction mismatch")
            checked.append((e,s,t,int(row["requested_seed"]),row["cube_sha256"]))
    if len(set(checked)) != 36:
        raise ValueError("raw target uniqueness failure")
    report = {"raw_review_archive_sha256":sha(args.raw_tar.read_bytes()),
              "all_36_cubes_sha256_match":True,
              "all_36_exact_10x30_reextractions_match":True,
              "all_36_simulator_seeds_match":True,
              "fresh_target_count":36,
              "sealed_data_read":False}
    (out/"JTD_E1_RAW_REVIEW_VERIFICATION.json").write_bytes(
        (json.dumps(report,indent=2,sort_keys=True)+"\n").encode("utf-8"))
    print("JTD_E1_RAW_36_EXACT_REEXTRACTION_PASS")


if __name__ == "__main__":
    main()

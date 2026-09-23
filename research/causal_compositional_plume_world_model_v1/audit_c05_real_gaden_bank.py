#!/usr/bin/env python3
"""Audit the frozen eight-cell C0.5 raw GADEN bank.

This audit is source-blind with respect to plume outcomes.  It checks only
the predeclared factorial, provenance consistency, frame counts, and whether
the two declared RNG seeds produce byte-distinct raw iteration files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


CELLS = [
    "S1_W1_A", "S1_W1_B", "S1_W2_A", "S1_W2_B",
    "S2_W1_A", "S2_W1_B", "S2_W2_A", "S2_W2_B",
]
PAIRS = [("S1_W1_A", "S1_W1_B"), ("S1_W2_A", "S1_W2_B"),
         ("S2_W1_A", "S2_W1_B"), ("S2_W2_A", "S2_W2_B")]


def read_tsv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        key, value = line.split("\t", 1)
        out[key] = value
    return out


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def iteration_files(cell_dir: Path) -> list[Path]:
    return sorted((cell_dir / "realization").glob("iteration_*"),
                  key=lambda p: int(p.name.split("_")[-1]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    root = args.root
    expected_frames = 566

    result: dict[str, object] = {
        "root": str(root),
        "cells": CELLS,
        "expected_frames": expected_frames,
        "checks": {},
        "cell_manifests": {},
        "replication_pairs": {},
    }
    errors: list[str] = []

    if not (root / "bank_contract.tsv").is_file():
        errors.append("missing bank_contract.tsv")
    else:
        result["bank_contract"] = read_tsv(root / "bank_contract.tsv")

    manifests: dict[str, dict[str, str]] = {}
    for cell in CELLS:
        mpath = root / cell / "manifest.tsv"
        if not mpath.is_file():
            errors.append(f"{cell}: missing manifest.tsv")
            continue
        manifest = read_tsv(mpath)
        manifests[cell] = manifest
        result["cell_manifests"][cell] = manifest
        files = iteration_files(root / cell)
        if len(files) != expected_frames:
            errors.append(f"{cell}: {len(files)} iteration files, expected {expected_frames}")
        if manifest.get("iteration_files") != str(expected_frames):
            errors.append(f"{cell}: manifest frame count mismatch")
        if not (root / cell / "OccupancyGrid3D.csv").is_symlink():
            errors.append(f"{cell}: missing occupancy provenance symlink")

    if len(manifests) == len(CELLS):
        occupancy = {m.get("occupancy_sha256") for m in manifests.values()}
        binaries = {m.get("binary_sha256") for m in manifests.values()}
        if len(occupancy) != 1:
            errors.append("occupancy hash differs across cells")
        if len(binaries) != 1:
            errors.append("binary hash differs across cells")
        seeds = {m.get("gaden_rng_seed") for m in manifests.values()}
        if seeds != {"2026092301", "2026092302"}:
            errors.append(f"unexpected seed set: {sorted(seeds)}")

    for a, b in PAIRS:
        fa = iteration_files(root / a)
        fb = iteration_files(root / b)
        same = 0
        different = 0
        first_difference = None
        for pa, pb in zip(fa, fb):
            if sha256(pa) == sha256(pb):
                same += 1
            else:
                different += 1
                if first_difference is None:
                    first_difference = pa.name
        pair_result = {
            "seed_a": manifests.get(a, {}).get("gaden_rng_seed"),
            "seed_b": manifests.get(b, {}).get("gaden_rng_seed"),
            "common_frame_count": min(len(fa), len(fb)),
            "byte_identical_frame_count": same,
            "byte_distinct_frame_count": different,
            "first_distinct_frame": first_difference,
            "manifest_sha256_a": sha256(root / a / "manifest.tsv") if (root / a / "manifest.tsv").is_file() else None,
            "manifest_sha256_b": sha256(root / b / "manifest.tsv") if (root / b / "manifest.tsv").is_file() else None,
        }
        result["replication_pairs"][f"{a}__{b}"] = pair_result
        if pair_result["common_frame_count"] != expected_frames:
            errors.append(f"{a}/{b}: common frame count mismatch")
        if different == 0:
            errors.append(f"{a}/{b}: pseudoreplication; every raw frame identical")
        if manifests.get(a, {}).get("gaden_rng_seed") == manifests.get(b, {}).get("gaden_rng_seed"):
            errors.append(f"{a}/{b}: declared seeds are equal")

    result["checks"] = {
        "factorial_complete": not any("missing manifest" in e for e in errors),
        "frame_counts_exact": not any("iteration files" in e or "frame count" in e for e in errors),
        "shared_geometry_and_binary": not any("hash differs" in e for e in errors),
        "independent_seed_pairs": not any("pseudoreplication" in e for e in errors),
        "pass": not errors,
    }
    result["errors"] = errors
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["checks"], sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Summarize frozen official GADEN concentration slices and replication pairs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


CELLS = [
    "S1_W1_A", "S1_W1_B", "S1_W2_A", "S1_W2_B",
    "S2_W1_A", "S2_W1_B", "S2_W2_A", "S2_W2_B",
]
PAIRS = [("S1_W1_A", "S1_W1_B"), ("S1_W2_A", "S1_W2_B"),
         ("S2_W1_A", "S2_W1_B"), ("S2_W2_A", "S2_W2_B")]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def summary(arr: np.ndarray) -> dict[str, float | int]:
    x = np.asarray(arr, dtype=np.float64)
    return {
        "min": float(x.min()),
        "median": float(np.median(x)),
        "max": float(x.max()),
        "mean": float(x.mean()),
        "p95": float(np.quantile(x, 0.95)),
        "nonzero_fraction": float(np.mean(x > 0.0)),
        "finite": int(np.isfinite(x).all()),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    result: dict[str, object] = {"root": str(args.root), "cells": {}, "replication_pairs": {}, "checks": {}}
    errors: list[str] = []
    arrays: dict[str, np.ndarray] = {}
    for cell in CELLS:
        path = args.root / cell / "spatial" / "concentration.npy"
        if not path.is_file():
            errors.append(f"{cell}: missing concentration.npy")
            continue
        arr = np.load(path, allow_pickle=False)
        arrays[cell] = arr
        result["cells"][cell] = {
            "shape": list(arr.shape),
            "dtype": str(arr.dtype),
            "sha256": sha256(path),
            "stats": summary(arr),
        }
        if arr.shape != (10, 83, 119):
            errors.append(f"{cell}: unexpected shape {arr.shape}")
        if not np.isfinite(arr).all():
            errors.append(f"{cell}: non-finite values")

    for a, b in PAIRS:
        if a not in arrays or b not in arrays:
            continue
        d = np.abs(arrays[a].astype(np.float64) - arrays[b].astype(np.float64))
        pair = {
            "shape": list(d.shape),
            "byte_identical": bool(np.array_equal(arrays[a], arrays[b])),
            "different_element_count": int(np.count_nonzero(d > 0.0)),
            "total_element_count": int(d.size),
            "mean_abs_difference": float(d.mean()),
            "max_abs_difference": float(d.max()),
            "relative_l1_difference": float(d.sum() / (np.abs(arrays[a]).sum() + 1e-12)),
        }
        result["replication_pairs"][f"{a}__{b}"] = pair
        if pair["byte_identical"] or pair["different_element_count"] == 0:
            errors.append(f"{a}/{b}: spatial pseudoreplication")
        if pair["mean_abs_difference"] <= 1e-12:
            errors.append(f"{a}/{b}: concentration difference at floating-point noise")

    result["checks"] = {
        "all_spatial_slices_present": len(arrays) == len(CELLS),
        "shapes_and_finiteness": not any("unexpected shape" in e or "non-finite" in e for e in errors),
        "independent_concentration_pairs": not any("pseudoreplication" in e or "floating-point noise" in e for e in errors),
        "pass": not errors,
    }
    result["errors"] = errors
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["checks"], sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

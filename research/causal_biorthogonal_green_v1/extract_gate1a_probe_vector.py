#!/usr/bin/env python3
"""Extract the frozen 30x10 Gate-1A probe vector from a GADEN spatial cube."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--concentration", type=Path, required=True)
    ap.add_argument("--contract", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    a = np.load(args.concentration, allow_pickle=False)
    if a.shape != (10, 83, 119):
        raise ValueError(f"shape drift: {a.shape}")
    if not np.isfinite(a).all() or (a < 0).any():
        raise ValueError("invalid concentration values")

    c = json.loads(args.contract.read_text(encoding="utf-8"))
    points = c["probe_points"]
    gx = np.asarray([int(p["grid_x"]) for p in points], dtype=np.int64)
    gy = np.asarray([int(p["grid_y"]) for p in points], dtype=np.int64)
    v = a[:, gx, gy].astype(np.float32).reshape(-1)
    if v.size != 300:
        raise ValueError(f"expected 300 values, got {v.size}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.out.with_suffix(args.out.suffix + ".tmp")
    with tmp.open("wb") as f:
        np.save(f, v, allow_pickle=False)
    tmp.replace(args.out)
    print(json.dumps({
        "out": str(args.out),
        "count": int(v.size),
        "nonzero": int(np.count_nonzero(v > 0)),
        "max": float(v.max(initial=0)),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

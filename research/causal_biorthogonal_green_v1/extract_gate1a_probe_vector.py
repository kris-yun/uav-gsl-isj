#!/usr/bin/env python3
"""Extract the frozen 30x10 Gate-1A pooled-probe vector from a GADEN cube."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def pooled_probe_vector(a: np.ndarray, points: list[dict]) -> np.ndarray:
    vals = []
    for p in points:
        x0, x1 = int(p["native_x0"]), int(p["native_x1_exclusive"])
        y0, y1 = int(p["native_y0"]), int(p["native_y1_exclusive"])
        block = a[:, x0:x1, y0:y1]
        if block.shape[1:] != (x1 - x0, y1 - y0):
            raise ValueError(f"probe block shape drift: {p}")
        vals.append(block.mean(axis=(1, 2)))
    # time-major then probe-major, matching pooled target sampling.
    return np.stack(vals, axis=1).astype(np.float32).reshape(-1)


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
    op = c.get("probe_operator", {})
    if op.get("type") != "avg_pool_2x2_then_sample":
        raise ValueError(f"unexpected probe operator: {op}")
    v = pooled_probe_vector(a, c["probe_points"])
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
        "probe_operator": op["type"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

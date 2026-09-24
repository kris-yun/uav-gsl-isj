#!/usr/bin/env python3
"""Compact a dense GADEN spatial history to the frozen 30 pooled M0 probes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--concentration", type=Path, required=True)
    ap.add_argument("--gate1-contract", type=Path, required=True)
    ap.add_argument("--iteration-list", type=Path, required=True)
    ap.add_argument("--results-dt", type=float, default=0.5)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    a = np.load(args.concentration, allow_pickle=False)
    if a.ndim != 3 or a.shape[1:] != (83, 119):
        raise ValueError(f"expected [T,83,119], got {a.shape}")
    if not np.isfinite(a).all() or (a < 0).any():
        raise ValueError("invalid concentration values")

    iterations = np.asarray(
        [int(x.strip()) for x in args.iteration_list.read_text().splitlines() if x.strip()],
        dtype=np.int64,
    )
    if iterations.ndim != 1 or len(iterations) != a.shape[0]:
        raise ValueError(f"iteration count {len(iterations)} != spatial T {a.shape[0]}")
    if len(np.unique(iterations)) != len(iterations) or np.any(np.diff(iterations) <= 0):
        raise ValueError("iteration list must be unique and strictly increasing")
    if len(iterations) < 500:
        raise ValueError(f"dense history unexpectedly short: {len(iterations)}")

    contract = json.loads(args.gate1_contract.read_text(encoding="utf-8"))
    if contract.get("probe_operator", {}).get("type") != "avg_pool_2x2_then_sample":
        raise ValueError("unexpected probe operator")
    points = contract["probe_points"]
    if len(points) != 30:
        raise ValueError(f"expected 30 probes, got {len(points)}")

    cols = []
    for p in points:
        x0, x1 = int(p["native_x0"]), int(p["native_x1_exclusive"])
        y0, y1 = int(p["native_y0"]), int(p["native_y1_exclusive"])
        block = a[:, x0:x1, y0:y1]
        expected = (a.shape[0], x1 - x0, y1 - y0)
        if block.shape != expected:
            raise ValueError(f"probe block shape drift: {p}")
        cols.append(block.mean(axis=(1, 2)))
    probe = np.stack(cols, axis=1).astype(np.float32)
    time_s = iterations.astype(np.float64) * float(args.results_dt)

    if probe.shape != (len(iterations), 30):
        raise ValueError(f"compact shape drift: {probe.shape}")
    if np.any(np.diff(time_s) <= 0):
        raise ValueError("non-increasing times")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.out.with_suffix(args.out.suffix + ".tmp")
    with tmp.open("wb") as f:
        np.savez_compressed(
            f,
            iteration_index=iterations,
            time_s=time_s,
            probe_ppm=probe,
        )
    tmp.replace(args.out)

    print(json.dumps({
        "out": str(args.out),
        "shape": list(probe.shape),
        "t_min_s": float(time_s[0]),
        "t_max_s": float(time_s[-1]),
        "nonzero": int(np.count_nonzero(probe > 0)),
        "max_ppm": float(probe.max(initial=0.0)),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

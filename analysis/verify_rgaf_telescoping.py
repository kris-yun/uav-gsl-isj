#!/usr/bin/env python3
"""Verify the R-GAF telescoping generalized-evidence identity.

Usage:
    python3 analysis/verify_rgaf_telescoping.py scores_tminus1.csv scores_t.csv

Both files must be V11 `meaci_candidate_scores_update_XXXX.csv` exports and
contain `candidate_id`, `temporal_rank_channel`, and `posterior_mass`.
"""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


def load(path: Path):
    rows = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows[row["candidate_id"]] = {
                "g": float(row["temporal_rank_channel"]),
                "q": float(row["posterior_mass"]),
            }
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("previous", type=Path)
    ap.add_argument("current", type=Path)
    args = ap.parse_args()

    prev = load(args.previous)
    cur = load(args.current)
    ids = sorted(set(prev) & set(cur))
    if not ids or len(ids) != len(prev) or len(ids) != len(cur):
        raise SystemExit("candidate sets do not match")

    unnormalized = []
    innovations = []
    for cid in ids:
        delta = cur[cid]["g"] - prev[cid]["g"]
        innovations.append(delta)
        unnormalized.append(prev[cid]["q"] * math.exp(delta))
    total = sum(unnormalized)
    if not (total > 0.0 and math.isfinite(total)):
        raise SystemExit("invalid recursive normalization")

    rebuilt = [v / total for v in unnormalized]
    target = [cur[cid]["q"] for cid in ids]
    max_abs = max(abs(a - b) for a, b in zip(rebuilt, target))
    l1 = sum(abs(a - b) for a, b in zip(rebuilt, target))

    print("RGAF_TELESCOPING_AUDIT=PASS" if max_abs < 1e-12 else "RGAF_TELESCOPING_AUDIT=FAIL")
    print(f"candidate_count={len(ids)}")
    print(f"innovation_min={min(innovations):.17g}")
    print(f"innovation_max={max(innovations):.17g}")
    print(f"max_abs_posterior_error={max_abs:.17g}")
    print(f"l1_posterior_error={l1:.17g}")


if __name__ == "__main__":
    main()

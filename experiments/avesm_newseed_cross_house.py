#!/usr/bin/env python3
"""Bounded AVESM cross-house gate on one fresh H01/H03 seed.

The model is intentionally pooled and source-relative: fit a Bernoulli gas-hit
kernel versus distance on the old VGR factorial episodes, then evaluate two
source candidates per fresh house case.  This is a transfer diagnostic, not a
PMFS confirmation.
"""
from __future__ import annotations

import csv
import json
import math
import random
from pathlib import Path

BINS = (0.0, 0.8, 1.2, 2.0, 3.0, 5.0, 99.0)
ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT.parent / "CSTAR_CCDE_VGR_FACTORIAL_20260914" / "_staging" / "vgr_factorial_source_evidence_input" / "episodes"
TARGET = ROOT / "experiments" / "avesm_newseed_inputs"


def bid(d):
    for i in range(len(BINS) - 1):
        if BINS[i] <= d < BINS[i + 1]:
            return i
    return len(BINS) - 2


def dist(x, y, c):
    return math.hypot(float(x) - c[0], float(y) - c[1])


def load_vgr():
    rows = []
    coords = {}
    for p in sorted(TRAIN.glob("*.csv")):
        with p.open(encoding="utf-8-sig", newline="") as f:
            rr = list(csv.DictReader(f))
        if not rr:
            continue
        r0 = rr[0]
        coords[r0["source_id"]] = (float(r0["source_x"]), float(r0["source_y"]))
        rows.extend(rr)
    return rows, coords


def fit(rows, coords):
    counts = [[1.0, 1.0] for _ in range(len(BINS) - 1)]
    for r in rows:
        y = int(float(r["gas_hit"]) > 0)
        # Pool source-relative distances; this is the only cross-house
        # invariance assumed by the diagnostic.
        c = coords[r["source_id"]]
        counts[bid(dist(r["position_x"], r["position_y"], c))][y] += 1.0
    return [[v / sum(row) for v in row] for row in counts]


def score(rows, model, candidates):
    le = {k: 0.0 for k in candidates}
    for r in rows:
        y = int(float(r["gas_ppm"]) > 0.0)
        p = {k: model[bid(dist(r["pose_xy"][0], r["pose_xy"][1], c))][y] for k, c in candidates.items()}
        for k in candidates:
            others = [p[u] for u in candidates if u != k]
            q = sum(others) / len(others)
            le[k] += math.log(q / p[k])
    return le


def shuffled(rows, seed):
    out = [dict(r) for r in rows]
    ys = [r["gas_ppm"] for r in out]
    random.Random(seed).shuffle(ys)
    for r, y in zip(out, ys):
        r["gas_ppm"] = y
    return out


def main():
    train_rows, train_coords = load_vgr()
    model = fit(train_rows, train_coords)
    all_rows = []
    results = []
    for house in ("H01", "H03"):
        cases = sorted(TARGET.glob(f"{house}_*/CASE_MANIFEST.json"))
        candidates = {}
        loaded = {}
        for manifest in cases:
            meta = json.loads(manifest.read_text(encoding="utf-8"))
            key = manifest.parent.name
            candidates[key] = tuple(meta["source_xyz_m"][:2])
            rows = [json.loads(x) for x in (manifest.parent / "measured_history.jsonl").read_text(encoding="utf-8").splitlines() if x]
            loaded[key] = rows
        if len(candidates) != 2:
            raise RuntimeError(f"expected_two_candidates:{house}:{sorted(candidates)}")
        for i, (true, rows) in enumerate(sorted(loaded.items())):
            le = score(rows, model, candidates)
            wrong = next(k for k in candidates if k != true)
            margin = le[wrong] - le[true]
            ctl = score(shuffled(rows, 12000 + i), model, candidates)
            c_margin = ctl[wrong] - ctl[true]
            rank = 1 + sum(le[k] > le[true] for k in candidates if k != true)
            results.append({"house": house, "true_case": true, "inverse_e_margin": margin,
                            "destructive_margin": c_margin, "true_rank": rank,
                            "n_frames": len(rows),
                            "nonzero_gas_frames": sum(float(r["gas_ppm"]) > 0.0 for r in rows),
                            "max_log_e_true": max(le.values())})
            all_rows.extend(rows)
    margins = [r["inverse_e_margin"] for r in results]
    controls = [r["destructive_margin"] for r in results]
    ranks = [r["true_rank"] for r in results]
    # The old AVESM gate is retained for comparability, but this result is
    # explicitly a fresh-seed transfer diagnostic, not a confirmation gate.
    out = {
        "status": "PASS_CROSS_HOUSE_TRANSFER_DIAGNOSTIC" if sum(margins) / len(margins) > 0 and sum(abs(x) for x in controls) / len(controls) < sum(abs(x) for x in margins) / len(margins) and sum(ranks) / len(ranks) <= 1.5 else "CROSS_HOUSE_TRANSFER_NO_GO",
        "train_asset": str(TRAIN),
        "target_asset": str(TARGET),
        "n_target_episodes": len(results),
        "mean_inverse_e_margin": sum(margins) / len(margins),
        "mean_destructive_margin": sum(controls) / len(controls),
        "mean_true_rank": sum(ranks) / len(ranks),
        "per_episode": results,
        "boundary": "fresh-seed cross-house transfer diagnostic; no closed-loop or independent PMFS confirmation claim",
    }
    out_path = ROOT / "experiments" / "avesm_newseed_cross_house_result.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

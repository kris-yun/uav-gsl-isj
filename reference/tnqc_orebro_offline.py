#!/usr/bin/env python3
"""Frozen public-data falsification probe for TNQC.

Uses only Orebro3DSEN measured data.  No source truth enters feature
construction.  Source labels are used only after representation construction
for same-source/different-condition evaluation.

Primary checks:
  1) raw amplitude is a poor repeated-source identity representation;
  2) affine quotient shape retains source identity;
  3) local neighbour ordering retains non-trivial source identity and is
     exactly invariant to strictly monotone pointwise calibration transforms;
  4) equal continuous/order fusion is an untuned robustness probe.

This script is deliberately independent of ROS and the PMFS implementation.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import statistics
import urllib.request
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Sequence, Tuple

BASE = "https://raw.githubusercontent.com/jburgues/Orebro3DSEN/master/logs"
EXPERIMENTS = [f"Exp{i:02d}" for i in range(1, 11)]

# Dataset-table structure: these five experiments share the same physical
# source coordinate while release/airflow conditions change.
SOURCE_GROUP = {
    "Exp01": "A", "Exp02": "A", "Exp03": "B", "Exp04": "C", "Exp05": "D",
    "Exp06": "A", "Exp07": "E", "Exp08": "A", "Exp09": "A", "Exp10": "F",
}

# Fixed, source-blind condition-specific monotone distortions used only as a
# stress test.  They emulate different compressive sensor transfer curves.
NONLINEAR_ALPHA = {
    "Exp01": 0.25, "Exp02": 0.40, "Exp03": 0.70, "Exp04": 1.10, "Exp05": 0.18,
    "Exp06": 1.60, "Exp07": 0.55, "Exp08": 2.20, "Exp09": 3.00, "Exp10": 0.90,
}


@dataclass
class WindowRep:
    exp: str
    raw: List[float]
    z: List[float]
    rank: List[float]
    edge: List[int]
    distorted_z: List[float]
    distorted_edge: List[int]


def mean(x: Sequence[float]) -> float:
    return sum(x) / len(x)


def stdev(x: Sequence[float]) -> float:
    if len(x) < 2:
        return 1.0
    s = statistics.stdev(x)
    return s if s > 1e-12 else 1.0


def fetch_csv(exp: str) -> Tuple[List[str], List[List[float]]]:
    url = f"{BASE}/{exp}.csv"
    with urllib.request.urlopen(url, timeout=60) as response:
        text = response.read().decode("utf-8", errors="replace")
    reader = csv.reader(io.StringIO(text))
    header = next(reader)
    rows: List[List[float]] = []
    for row in reader:
        if not row:
            continue
        vals = [float(v) for v in row]
        if len(vals) >= 38 and math.isfinite(vals[0]):
            rows.append(vals)
    return header, rows


def sensor_indices_and_coords(header: Sequence[str]) -> Tuple[List[int], List[Tuple[int, int, int]]]:
    idx: List[int] = []
    coords: List[Tuple[int, int, int]] = []
    for i, name in enumerate(header):
        name = name.strip()
        if not name.startswith("C_"):
            continue
        code = name.split()[0][2:]
        if len(code) != 3 or not code.isdigit():
            raise ValueError(f"unexpected sensor header {name!r}")
        idx.append(i)
        coords.append(tuple(int(c) for c in code))
    if len(idx) != 27:
        raise ValueError(f"expected 27 gas sensors, got {len(idx)}")
    return idx, coords


def local_edges(coords: Sequence[Tuple[int, int, int]]) -> List[Tuple[int, int]]:
    out: List[Tuple[int, int]] = []
    for i in range(len(coords)):
        for j in range(i + 1, len(coords)):
            d = sum(abs(coords[i][k] - coords[j][k]) for k in range(3))
            if d == 1:
                out.append((i, j))
    return out


def z_rep(v: Sequence[float]) -> List[float]:
    m = mean(v)
    s = stdev(v)
    return [(x - m) / s for x in v]


def rank_rep(v: Sequence[float]) -> List[float]:
    order = sorted(range(len(v)), key=lambda i: (v[i], i))
    out = [0.0] * len(v)
    mid = (len(v) - 1) / 2.0
    scale = max(mid, 1.0)
    for rank, index in enumerate(order):
        out[index] = (rank - mid) / scale
    return out


def edge_rep(v: Sequence[float], edges: Sequence[Tuple[int, int]]) -> List[int]:
    out: List[int] = []
    for a, b in edges:
        out.append(1 if v[a] > v[b] else -1 if v[a] < v[b] else 0)
    return out


def nonlinear(v: Sequence[float], alpha: float) -> List[float]:
    return [math.asinh(alpha * x) / alpha for x in v]


def euclidean(a: Sequence[float], b: Sequence[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)) / len(a))


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    ab = sum(x * y for x, y in zip(a, b))
    aa = sum(x * x for x in a)
    bb = sum(y * y for y in b)
    return ab / math.sqrt(max(aa * bb, 1e-30))


def order_agreement(a: Sequence[int], b: Sequence[int]) -> float:
    vals = [x * y for x, y in zip(a, b) if x and y]
    return mean(vals) if vals else 0.0


def vector_centroid(items: Sequence[Sequence[float]]) -> List[float]:
    return [mean([row[j] for row in items]) for j in range(len(items[0]))]


def edge_centroid(items: Sequence[Sequence[int]]) -> List[int]:
    out: List[int] = []
    for j in range(len(items[0])):
        s = sum(row[j] for row in items)
        out.append(1 if s > 0 else -1 if s < 0 else 0)
    return out


def auc_positive_greater(pos: Sequence[float], neg: Sequence[float]) -> float:
    wins = 0.0
    total = 0
    for p in pos:
        for n in neg:
            total += 1
            wins += 1.0 if p > n else 0.5 if p == n else 0.0
    return wins / total


def auc_distance(pos: Sequence[float], neg: Sequence[float]) -> float:
    # Smaller distance means same source.
    return auc_positive_greater([-x for x in pos], [-x for x in neg])


def build_windows(window_minutes: int) -> Tuple[List[WindowRep], int]:
    reps: List[WindowRep] = []
    edges: List[Tuple[int, int]] | None = None
    for exp in EXPERIMENTS:
        header, rows = fetch_csv(exp)
        sensor_idx, coords = sensor_indices_and_coords(header)
        if edges is None:
            edges = local_edges(coords)
        width = window_minutes * 60.0
        start, stop = 40.0 * 60.0, 90.0 * 60.0
        s = start
        while s + width <= stop + 1e-9:
            chosen = [r for r in rows if s <= r[0] < s + width]
            if len(chosen) > int(width * 1.5):
                raw = [mean([r[j] for r in chosen]) for j in sensor_idx]
                dist = nonlinear(raw, NONLINEAR_ALPHA[exp])
                reps.append(WindowRep(
                    exp=exp,
                    raw=raw,
                    z=z_rep(raw),
                    rank=rank_rep(raw),
                    edge=edge_rep(raw, edges),
                    distorted_z=z_rep(dist),
                    distorted_edge=edge_rep(dist, edges),
                ))
            s += width
    assert edges is not None
    return reps, len(edges)


def evaluate_distance(reps: Sequence[WindowRep], attr: str) -> Dict[str, float]:
    by = {e: [getattr(r, attr) for r in reps if r.exp == e] for e in EXPERIMENTS}
    cent = {e: vector_centroid(by[e]) for e in EXPERIMENTS}
    same, diff = [], []
    for i, a in enumerate(EXPERIMENTS):
        for b in EXPERIMENTS[i + 1:]:
            d = euclidean(cent[a], cent[b])
            (same if SOURCE_GROUP[a] == SOURCE_GROUP[b] else diff).append(d)

    anchor = [e for e in EXPERIMENTS if SOURCE_GROUP[e] == "A"]
    others = [e for e in EXPERIMENTS if SOURCE_GROUP[e] != "A"]
    hit = total = 0
    per_condition: Dict[str, float] = {}
    for held in anchor:
        positive = vector_centroid([v for e in anchor if e != held for v in by[e]])
        h = t = 0
        for v in by[held]:
            ds = euclidean(v, positive)
            dn = min(euclidean(v, cent[e]) for e in others)
            h += int(ds < dn)
            t += 1
        per_condition[held] = h / t
        hit += h
        total += t
    return {
        "same_vs_different_auc": auc_distance(same, diff),
        "leave_condition_out_accuracy": hit / total,
        "same_median_distance": statistics.median(same),
        "different_median_distance": statistics.median(diff),
        "per_condition": per_condition,
    }


def evaluate_edge(reps: Sequence[WindowRep], attr: str) -> Dict[str, float]:
    by = {e: [getattr(r, attr) for r in reps if r.exp == e] for e in EXPERIMENTS}
    cent = {e: edge_centroid(by[e]) for e in EXPERIMENTS}
    same, diff = [], []
    for i, a in enumerate(EXPERIMENTS):
        for b in EXPERIMENTS[i + 1:]:
            s = order_agreement(cent[a], cent[b])
            (same if SOURCE_GROUP[a] == SOURCE_GROUP[b] else diff).append(s)

    anchor = [e for e in EXPERIMENTS if SOURCE_GROUP[e] == "A"]
    others = [e for e in EXPERIMENTS if SOURCE_GROUP[e] != "A"]
    hit = total = 0
    per_condition: Dict[str, float] = {}
    for held in anchor:
        positive = edge_centroid([v for e in anchor if e != held for v in by[e]])
        h = t = 0
        for v in by[held]:
            sp = order_agreement(v, positive)
            sn = max(order_agreement(v, cent[e]) for e in others)
            h += int(sp > sn)
            t += 1
        per_condition[held] = h / t
        hit += h
        total += t
    return {
        "same_vs_different_auc": auc_positive_greater(same, diff),
        "leave_condition_out_accuracy": hit / total,
        "same_median_agreement": statistics.median(same),
        "different_median_agreement": statistics.median(diff),
        "per_condition": per_condition,
    }


def evaluate_fusion(reps: Sequence[WindowRep], z_attr: str, edge_attr: str) -> Dict[str, float]:
    by = {e: [r for r in reps if r.exp == e] for e in EXPERIMENTS}

    def centroid(rows: Sequence[WindowRep]):
        return (
            vector_centroid([getattr(r, z_attr) for r in rows]),
            edge_centroid([getattr(r, edge_attr) for r in rows]),
        )

    def score_one(z: Sequence[float], edge: Sequence[int], c) -> float:
        return 0.5 * (cosine(z, c[0]) + order_agreement(edge, c[1]))

    cent = {e: centroid(by[e]) for e in EXPERIMENTS}
    same, diff = [], []
    for i, a in enumerate(EXPERIMENTS):
        for b in EXPERIMENTS[i + 1:]:
            s = 0.5 * (cosine(cent[a][0], cent[b][0]) +
                       order_agreement(cent[a][1], cent[b][1]))
            (same if SOURCE_GROUP[a] == SOURCE_GROUP[b] else diff).append(s)

    anchor = [e for e in EXPERIMENTS if SOURCE_GROUP[e] == "A"]
    others = [e for e in EXPERIMENTS if SOURCE_GROUP[e] != "A"]
    hit = total = 0
    per_condition: Dict[str, float] = {}
    for held in anchor:
        positive = centroid([r for e in anchor if e != held for r in by[e]])
        h = t = 0
        for r in by[held]:
            z = getattr(r, z_attr)
            edge = getattr(r, edge_attr)
            sp = score_one(z, edge, positive)
            sn = max(score_one(z, edge, cent[e]) for e in others)
            h += int(sp > sn)
            t += 1
        per_condition[held] = h / t
        hit += h
        total += t
    return {
        "same_vs_different_auc": auc_positive_greater(same, diff),
        "leave_condition_out_accuracy": hit / total,
        "same_median_effect": statistics.median(same),
        "different_median_effect": statistics.median(diff),
        "per_condition": per_condition,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--window-minutes", type=int, default=5)
    ap.add_argument("--json-out")
    args = ap.parse_args()

    reps, edge_count = build_windows(args.window_minutes)
    payload = {
        "contract": "TNQC_OREBRO_PUBLIC_FALSIFICATION_V1",
        "window_minutes": args.window_minutes,
        "window_count": len(reps),
        "local_edge_count": edge_count,
        "source_group_A": [e for e in EXPERIMENTS if SOURCE_GROUP[e] == "A"],
        "raw": evaluate_distance(reps, "raw"),
        "affine_quotient_z": evaluate_distance(reps, "z"),
        "rank_invariant": evaluate_distance(reps, "rank"),
        "local_order": evaluate_edge(reps, "edge"),
        "continuous_plus_local_order": evaluate_fusion(reps, "z", "edge"),
        "nonlinear_stress": {
            "affine_quotient_z": evaluate_distance(reps, "distorted_z"),
            "local_order": evaluate_edge(reps, "distorted_edge"),
            "continuous_plus_local_order": evaluate_fusion(
                reps, "distorted_z", "distorted_edge"),
        },
        "checks": {
            "local_order_exactly_preserved_under_monotone_stress":
                all(r.edge == r.distorted_edge for r in reps),
        },
    }
    text = json.dumps(payload, indent=2)
    print(text)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            f.write(text + "\n")


if __name__ == "__main__":
    main()

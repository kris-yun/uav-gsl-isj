#!/usr/bin/env python3
"""VGR/House mechanism screen for Transport-Nuisance Quotient Canonicalization.

This is a project-data mechanism test, not the authoritative 300 s endpoint.

Data are the archived VGR/GADEN House01/02/03 fixed-route histories on
project/research-master-20260914:
  H01/H02/H03 x source A/B x fast/slow transport, 1200 samples to 240 s.

The same geometry-only route is used within each House.  To align the offline
probe with the online PMFS representation, samples are aggregated onto the
actual reduced PMFS grid: raw map resolution 0.1 m, scale=3, cell size=0.3 m,
using the map origins recorded by the historical native PMFS logs.

The screen asks:
  * does an affine quotient retain source identity across fast/slow transport?
  * does it survive source-blind release/gain perturbations?
  * does the broader monotone local-spatial-order channel help or hurt?
  * can a parameter-free symmetry-hierarchy guard prevent the broader channel
    from overriding the exact affine quotient when the two disagree?

The authoritative feasibility gate remains:
  House01/02/03 x seed0/1, full 300 simulation seconds,
  PMFS ExpectedValue(sourceProbability, 0.05) localization error.
Run reference/run_tnqc_vgr_offline_gate_20260920.sh on the VGR VM for that gate.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import subprocess
from pathlib import Path
from typing import Callable, Dict, List, Mapping, Sequence, Tuple

HOUSES = ("H01", "H02", "H03")
SOURCES = ("SA", "SB")
WINDS = ("fast", "slow")
DEFAULT_REF = "project/research-master-20260914"
ROOT = "evidence/cstar_current_runtime_assets240_20260907/realizations"

# Native PMFS logs on the same VGR Houses:
# H01 raw 87x114 res=0.1 origin=(-7.55,-7.88), reduced cellSize=0.3
# H02 raw 83x119 res=0.1 origin=(-5.39,-7.45), reduced cellSize=0.3
# H03 raw 138x83 res=0.1 origin=(-0.85,-1.86), reduced cellSize=0.3
PMFS_CELL_SIZE_M = 0.3
PMFS_ORIGIN = {
    "H01": (-7.55, -7.88),
    "H02": (-5.39, -7.45),
    "H03": (-0.85, -1.86),
}

SOURCE_XY = {
    "H01": {"SA": (-0.6, 1.95), "SB": (-0.4, -2.9)},
    "H02": {"SA": (0.0, -1.0), "SB": (1.0, -2.3)},
    "H03": {"SA": (-0.45, 1.9), "SB": (8.2, 5.0)},
}


def git_text(repo: Path, ref: str, path: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), "show", f"{ref}:{path}"], text=True
    )


def load_histories(repo: Path, ref: str) -> Dict[str, List[dict]]:
    out: Dict[str, List[dict]] = {}
    for house in HOUSES:
        for source in SOURCES:
            for wind in WINDS:
                key = f"{house}_{source}_{wind}"
                path = f"{ROOT}/{key}/measured_history.jsonl"
                rows = [
                    json.loads(x)
                    for x in git_text(repo, ref, path).splitlines()
                    if x.strip()
                ]
                if len(rows) != 1200:
                    raise RuntimeError(f"{key}: expected 1200 rows, got {len(rows)}")
                if abs(float(rows[-1]["t_sim_s"]) - 240.0) > 1e-9:
                    raise RuntimeError(f"{key}: history does not end at 240 s")
                out[key] = rows
    return out


def mean(x: Sequence[float]) -> float:
    return sum(x) / len(x)


def source_distance(house: str) -> float:
    a, b = SOURCE_XY[house]["SA"], SOURCE_XY[house]["SB"]
    return math.hypot(a[0] - b[0], a[1] - b[1])


def field(
    house: str,
    rows: Sequence[dict],
    end_s: float,
    transform: Callable[[float], float] | None = None,
) -> Dict[Tuple[int, int], float]:
    ox, oy = PMFS_ORIGIN[house]
    accum: Dict[Tuple[int, int], List[float]] = {}
    for r in rows:
        if float(r["t_sim_s"]) > end_s + 1e-9:
            continue
        x, y = map(float, r["pose_xy"])
        i = math.floor((x - ox) / PMFS_CELL_SIZE_M + 1e-12)
        j = math.floor((y - oy) / PMFS_CELL_SIZE_M + 1e-12)
        v = float(r["gas_ppm"])
        if transform is not None:
            v = transform(v)
        accum.setdefault((i, j), []).append(v)
    if not accum:
        raise ValueError(f"{house}: empty field at {end_s} s")
    return {k: mean(v) for k, v in accum.items()}


def common_values(
    a: Mapping[Tuple[int, int], float],
    b: Mapping[Tuple[int, int], float],
) -> Tuple[List[Tuple[int, int]], List[float], List[float]]:
    keys = sorted(set(a).intersection(b))
    if not keys:
        raise ValueError("no common PMFS cells")
    return keys, [a[k] for k in keys], [b[k] for k in keys]


def rmse(a: Sequence[float], b: Sequence[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)) / len(a))


def centered_cosine(a: Sequence[float], b: Sequence[float]) -> float | None:
    if len(a) < 2:
        return None
    ma, mb = mean(a), mean(b)
    cross = aa = bb = 0.0
    for x0, y0 in zip(a, b):
        x, y = x0 - ma, y0 - mb
        cross += x * y
        aa += x * x
        bb += y * y
    if aa <= 1e-30 or bb <= 1e-30:
        return None
    return cross / math.sqrt(aa * bb)


def spatial_edges(keys: Sequence[Tuple[int, int]]) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    support = set(keys)
    out = []
    for i, j in support:
        for nb in ((i + 1, j), (i, j + 1)):
            if nb in support:
                out.append(((i, j), nb))
    return out


def local_spatial_order(
    a: Mapping[Tuple[int, int], float],
    b: Mapping[Tuple[int, int], float],
) -> Tuple[float | None, int, int]:
    keys = sorted(set(a).intersection(b))
    edges = spatial_edges(keys)
    signed = 0.0
    valid = 0
    for u, v in edges:
        da, db = a[u] - a[v], b[u] - b[v]
        sa = (da > 0.0) - (da < 0.0)
        sb = (db > 0.0) - (db < 0.0)
        if sa == 0 or sb == 0:
            continue
        signed += sa * sb
        valid += 1
    return (signed / valid if valid else None), valid, len(edges)


def pair_score(
    query: Mapping[Tuple[int, int], float],
    template: Mapping[Tuple[int, int], float],
) -> dict:
    keys, q, t = common_values(query, template)
    qa = centered_cosine(q, t)
    qo, valid_edges, total_edges = local_spatial_order(query, template)
    a = 0.0 if qa is None else qa
    o = 0.0 if qo is None else qo

    # Old experimental fusion, retained only as a destructive/control arm.
    equal_fusion = 0.5 * (a + o)

    # Symmetry-hierarchy guard:
    # the broader monotone/order quotient may corroborate the exact physical
    # affine quotient, but may not reverse it.  No fitted coefficient or
    # threshold is introduced.  When signs disagree, fall back to q_aff.
    order_consistent = valid_edges >= 2 and a * o >= 0.0
    guarded = 0.5 * (a + o) if order_consistent else a

    return {
        "raw": -rmse(q, t),
        "affine": a,
        "order": o,
        "equal_fusion": equal_fusion,
        "guarded": guarded,
        "order_consistent": order_consistent,
        "common_bins": len(keys),
        "valid_local_edges": valid_edges,
        "total_local_edges": total_edges,
    }


def classify(
    hist: Mapping[str, Sequence[dict]],
    end_s: float,
    transform_family: Callable[[str], Callable[[float], float]] | None = None,
) -> dict:
    fields = {}
    for house in HOUSES:
        for source in SOURCES:
            for wind in WINDS:
                key = f"{house}_{source}_{wind}"
                transform = transform_family(key) if transform_family else None
                fields[key] = field(house, hist[key], end_s, transform)

    methods = ("raw", "affine", "order", "equal_fusion", "guarded")
    hits = {k: 0 for k in methods}
    errors = {k: 0.0 for k in methods}
    cases = []

    for house in HOUSES:
        for wind in WINDS:
            other_wind = "slow" if wind == "fast" else "fast"
            for truth in SOURCES:
                query = fields[f"{house}_{truth}_{wind}"]
                sa = pair_score(query, fields[f"{house}_SA_{other_wind}"])
                sb = pair_score(query, fields[f"{house}_SB_{other_wind}"])
                preds = {}
                for method in methods:
                    pred = "SA" if sa[method] >= sb[method] else "SB"
                    preds[method] = pred
                    hits[method] += int(pred == truth)
                    if pred != truth:
                        errors[method] += source_distance(house)
                cases.append(
                    {
                        "house": house,
                        "wind": wind,
                        "truth": truth,
                        "predictions": preds,
                        "scores": {
                            m: [sa[m], sb[m]]
                            for m in methods
                        },
                        "sa_meta": {
                            k: sa[k]
                            for k in (
                                "order_consistent", "common_bins",
                                "valid_local_edges", "total_local_edges"
                            )
                        },
                        "sb_meta": {
                            k: sb[k]
                            for k in (
                                "order_consistent", "common_bins",
                                "valid_local_edges", "total_local_edges"
                            )
                        },
                    }
                )

    n = len(cases)
    return {
        "end_s": end_s,
        "case_count": n,
        "accuracy": {k: hits[k] / n for k in methods},
        "mean_two_source_error_m": {k: errors[k] / n for k in methods},
        "cases": cases,
    }


def fnv1a32(text: str) -> int:
    h = 2166136261
    for b in text.encode("utf-8"):
        h ^= b
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def seed_rng(seed: int, key: str, salt: int = 0):
    state = (seed ^ fnv1a32(key) ^ salt) & 0xFFFFFFFF

    def rand() -> float:
        nonlocal state
        state = (1664525 * state + 1013904223) & 0xFFFFFFFF
        return state / 2**32

    return rand


def scale_stress(seed: int):
    def family(key: str):
        r = seed_rng(seed, key)
        a = math.exp(math.log(0.1) + r() * (math.log(10.0) - math.log(0.1)))
        return lambda v: a * v

    return family


def monotone_stress(seed: int):
    def family(key: str):
        r = seed_rng(seed, key, 0x9E3779B9)
        alpha = math.exp(
            math.log(1e-2) + r() * (math.log(1e4) - math.log(1e-2))
        )
        return lambda v: math.log1p(alpha * max(v, 0.0)) / alpha

    return family


def summarize_runs(runs: Sequence[dict], method: str) -> dict:
    vals = sorted(float(r["accuracy"][method]) for r in runs)
    return {
        "mean": statistics.fmean(vals),
        "min": vals[0],
        "median": statistics.median(vals),
        "max": vals[-1],
        "perfect_count": sum(v == 1.0 for v in vals),
        "run_count": len(vals),
    }


def compact(result: dict) -> dict:
    return {
        "end_s": result["end_s"],
        "case_count": result["case_count"],
        "accuracy": result["accuracy"],
        "mean_two_source_error_m": result["mean_two_source_error_m"],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=Path("."))
    ap.add_argument("--ref", default=DEFAULT_REF)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    hist = load_histories(args.repo, args.ref)
    checkpoints = {
        str(end): classify(hist, float(end))
        for end in (60, 120, 180, 240)
    }
    scale_runs = [classify(hist, 240.0, scale_stress(i)) for i in range(1, 101)]
    monotone_runs = [
        classify(hist, 240.0, monotone_stress(i)) for i in range(1, 201)
    ]

    methods = ("raw", "affine", "order", "equal_fusion", "guarded")
    payload = {
        "contract": "TNQC_VGR_240S_SPATIAL_MECHANISM_V2",
        "data_ref": args.ref,
        "data_root": ROOT,
        "pmfs_grid": {
            "cell_size_m": PMFS_CELL_SIZE_M,
            "origins": PMFS_ORIGIN,
            "provenance": "native PMFS MAP-DEBUG logs, raw resolution 0.1 m, scale=3",
        },
        "authoritative_endpoint_note":
            "Mechanism screen only. GO is decided only by the full 300-s "
            "House01/02/03 x seed0/1 PMFS top-5%-ExpectedValue gate.",
        "checkpoint_summary": {
            k: compact(v) for k, v in checkpoints.items()
        },
        "base_240s_cases": checkpoints["240"]["cases"],
        "scale_nuisance_100_source_blind_seeds": {
            m: summarize_runs(scale_runs, m) for m in methods
        },
        "monotone_compression_200_source_blind_seeds": {
            m: summarize_runs(monotone_runs, m) for m in methods
        },
        "frozen_interpretation": {
            "affine_quotient_positive": (
                checkpoints["240"]["accuracy"]["affine"] == 1.0
                and summarize_runs(scale_runs, "affine")["min"] == 1.0
            ),
            "unconditional_equal_fusion_rejected": (
                checkpoints["240"]["accuracy"]["equal_fusion"]
                < checkpoints["240"]["accuracy"]["affine"]
            ),
            "symmetry_hierarchy_guard_survives": (
                checkpoints["240"]["accuracy"]["guarded"]
                == checkpoints["240"]["accuracy"]["affine"]
                and summarize_runs(scale_runs, "guarded")["min"] == 1.0
                and summarize_runs(monotone_runs, "guarded")["min"] == 1.0
            ),
        },
    }

    text = json.dumps(payload, indent=2, sort_keys=True)
    print(text)
    if args.json_out:
        args.json_out.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

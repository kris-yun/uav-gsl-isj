#!/usr/bin/env python3
"""Frozen VGR/House offline feasibility screen for TNQC.

This is the authoritative offline screen for the current project data.  It does
NOT replace the final 300 s closed-loop endpoint.  It reads the user's archived
VGR House01/02/03 controlled histories from the historical research branch and
asks a narrower question:

    does the quotient representation preserve source identity across a
    transport intervention (fast vs slow) on the same frozen geometry-only
    route, and does it remain stable under source-blind nuisance transforms?

Data source (git object, no web download required):
    project/research-master-20260914
    evidence/cstar_current_runtime_assets240_20260907/

Each House contains SA/SB x fast/slow.  All four histories in a House use the
same pose sequence, so opposite-wind histories can be compared on a common
spatial route without source truth entering representation construction.

The 240 s histories are a mechanism proxy only.  The paper endpoint remains the
original PMFS top-5% expected-location error after the frozen 300 s closed-loop
budget on House01/02/03 x seed0/1.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import subprocess
from pathlib import Path
from typing import Dict, List, Sequence

HOUSES = ("H01", "H02", "H03")
SOURCES = ("SA", "SB")
WINDS = ("fast", "slow")
DEFAULT_REF = "project/research-master-20260914"
ROOT = "evidence/cstar_current_runtime_assets240_20260907"

SOURCE_XY = {
    "H01": {"SA": (-0.6, 1.95), "SB": (-0.4, -2.9)},
    "H02": {"SA": (0.0, -1.0), "SB": (1.0, -2.3)},
    "H03": {"SA": (-0.45, 1.9), "SB": (8.2, 5.0)},
}


def git_text(repo: Path, ref: str, path: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), "show", f"{ref}:{path}"],
        text=True,
    )


def load_histories(repo: Path, ref: str) -> Dict[str, List[dict]]:
    out: Dict[str, List[dict]] = {}
    for house in HOUSES:
        for source in SOURCES:
            for wind in WINDS:
                key = f"{house}_{source}_{wind}"
                path = f"{ROOT}/realizations/{key}/measured_history.jsonl"
                rows = [json.loads(x) for x in git_text(repo, ref, path).splitlines() if x.strip()]
                if len(rows) != 1200:
                    raise RuntimeError(f"{key}: expected 1200 rows, got {len(rows)}")
                if abs(float(rows[-1]["t_sim_s"]) - 240.0) > 1e-9:
                    raise RuntimeError(f"{key}: history does not end at 240 s")
                out[key] = rows
    return out


def mean(x: Sequence[float]) -> float:
    return sum(x) / len(x)


def centered_cosine(a: Sequence[float], b: Sequence[float]) -> float | None:
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


def local_order(a: Sequence[float], b: Sequence[float]) -> float | None:
    signed = 0.0
    n = 0
    for i in range(len(a) - 1):
        da, db = a[i + 1] - a[i], b[i + 1] - b[i]
        sa = 1 if da > 0 else -1 if da < 0 else 0
        sb = 1 if db > 0 else -1 if db < 0 else 0
        if sa == 0 or sb == 0:
            continue
        signed += sa * sb
        n += 1
    return signed / n if n else None


def rmse(a: Sequence[float], b: Sequence[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)) / len(a))


def vector(rows: Sequence[dict], end_s: float = 240.0) -> List[float]:
    return [float(r["gas_ppm"]) for r in rows if float(r["t_sim_s"]) <= end_s + 1e-9]


def source_distance(house: str) -> float:
    a, b = SOURCE_XY[house]["SA"], SOURCE_XY[house]["SB"]
    return math.hypot(a[0] - b[0], a[1] - b[1])


def classify(hist: Dict[str, List[dict]], end_s: float, transformed=None) -> dict:
    data = {}
    for key, rows in hist.items():
        v = vector(rows, end_s)
        data[key] = transformed(key, v) if transformed else v

    totals = {"raw": 0, "affine": 0, "order": 0, "fused": 0}
    errors = {k: 0.0 for k in totals}
    cases = 0
    valid_affine = 0
    valid_affine_correct = 0
    per_case = []

    for house in HOUSES:
        for wind in WINDS:
            other_wind = "slow" if wind == "fast" else "fast"
            for truth in SOURCES:
                q = data[f"{house}_{truth}_{wind}"]
                a = data[f"{house}_SA_{other_wind}"]
                b = data[f"{house}_SB_{other_wind}"]

                raw_sa, raw_sb = -rmse(q, a), -rmse(q, b)
                aff_sa, aff_sb = centered_cosine(q, a), centered_cosine(q, b)
                ord_sa, ord_sb = local_order(q, a), local_order(q, b)

                # Invalid quotient comparisons are abstentions; for the
                # ungated diagnostic below they are numerically represented as 0.
                aa = 0.0 if aff_sa is None else aff_sa
                ab = 0.0 if aff_sb is None else aff_sb
                oa = 0.0 if ord_sa is None else ord_sa
                ob = 0.0 if ord_sb is None else ord_sb
                fus_sa, fus_sb = 0.5 * (aa + oa), 0.5 * (ab + ob)

                scores = {
                    "raw": (raw_sa, raw_sb),
                    "affine": (aa, ab),
                    "order": (oa, ob),
                    "fused": (fus_sa, fus_sb),
                }
                d = source_distance(house)
                preds = {}
                for name, (sa, sb) in scores.items():
                    pred = "SA" if sa >= sb else "SB"
                    preds[name] = pred
                    totals[name] += int(pred == truth)
                    if pred != truth:
                        errors[name] += d

                affine_valid = (
                    aff_sa is not None and aff_sb is not None and
                    abs(aff_sa - aff_sb) > 1e-15
                )
                if affine_valid:
                    valid_affine += 1
                    valid_affine_correct += int(preds["affine"] == truth)

                per_case.append({
                    "house": house,
                    "wind": wind,
                    "truth": truth,
                    "scores": scores,
                    "predictions": preds,
                    "affine_identifiable": affine_valid,
                })
                cases += 1

    return {
        "end_s": end_s,
        "case_count": cases,
        "accuracy": {k: totals[k] / cases for k in totals},
        "mean_two_source_error_m": {k: errors[k] / cases for k in totals},
        "affine_identifiability_gate": {
            "accepted": valid_affine,
            "coverage": valid_affine / cases,
            "accepted_accuracy": (
                valid_affine_correct / valid_affine if valid_affine else None
            ),
        },
        "cases": per_case,
    }


def fnv1a32(text: str) -> int:
    h = 2166136261
    for b in text.encode("utf-8"):
        h ^= b
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def seed_rng(seed: int, key: str, salt: int = 0):
    # Deterministic source-blind LCG. Only episode id + stress seed enter.
    state = (seed ^ fnv1a32(key) ^ salt) & 0xFFFFFFFF

    def rand() -> float:
        nonlocal state
        state = (1664525 * state + 1013904223) & 0xFFFFFFFF
        return state / 2**32

    return rand


def scale_stress(seed: int):
    def f(key: str, x: List[float]) -> List[float]:
        r = seed_rng(seed, key)
        a = math.exp(math.log(0.1) + r() * (math.log(10.0) - math.log(0.1)))
        return [a * v for v in x]
    return f


def monotone_stress(seed: int):
    def f(key: str, x: List[float]) -> List[float]:
        r = seed_rng(seed, key, 0x9E3779B9)
        factor = math.exp(
            math.log(1e-2) + r() * (math.log(1e4) - math.log(1e-2))
        )
        scale = max(max(x), 1e-9)
        alpha = factor / scale
        return [math.log1p(alpha * max(v, 0.0)) / alpha for v in x]
    return f


def summarize_runs(runs: Sequence[dict], field: str, metric: str) -> dict:
    vals = sorted(float(r[field][metric]) for r in runs)
    n = len(vals)
    return {
        "mean": mean(vals),
        "min": vals[0],
        "p10": vals[max(0, int(0.10 * n) - 1)],
        "median": statistics.median(vals),
        "p90": vals[min(n - 1, int(0.90 * n) - 1)],
        "max": vals[-1],
        "perfect_count": sum(v == 1.0 for v in vals),
        "run_count": n,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=Path("."))
    ap.add_argument("--ref", default=DEFAULT_REF)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    hist = load_histories(args.repo, args.ref)

    base240 = classify(hist, 240.0)
    prefix180 = classify(hist, 180.0)

    scale_runs = [classify(hist, 240.0, scale_stress(i)) for i in range(1, 101)]
    monotone_runs = [classify(hist, 240.0, monotone_stress(i)) for i in range(1, 201)]

    payload = {
        "contract": "TNQC_VGR_OFFLINE_FEASIBILITY_V1",
        "data_ref": args.ref,
        "data_root": ROOT,
        "authoritative_endpoint_note":
            "This is a 240 s fixed-route mechanism screen only. Final evidence is "
            "the 300 s closed-loop PMFS top-5%-expected-location error.",
        "base_240s": base240,
        "prefix_identifiability_diagnostic_180s": {
            k: prefix180[k] for k in (
                "end_s", "case_count", "accuracy",
                "mean_two_source_error_m", "affine_identifiability_gate"
            )
        },
        "scale_nuisance_100_source_blind_seeds": {
            "accuracy": {
                name: summarize_runs(scale_runs, "accuracy", name)
                for name in ("raw", "affine", "order", "fused")
            },
            "mean_two_source_error_m": {
                name: {
                    "mean": mean([r["mean_two_source_error_m"][name] for r in scale_runs]),
                    "min": min(r["mean_two_source_error_m"][name] for r in scale_runs),
                    "max": max(r["mean_two_source_error_m"][name] for r in scale_runs),
                }
                for name in ("raw", "affine", "order", "fused")
            },
        },
        "monotone_compression_200_source_blind_seeds": {
            "accuracy": {
                name: summarize_runs(monotone_runs, "accuracy", name)
                for name in ("raw", "affine", "order", "fused")
            }
        },
    }

    text = json.dumps(payload, indent=2, sort_keys=True)
    print(text)
    if args.json_out:
        args.json_out.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

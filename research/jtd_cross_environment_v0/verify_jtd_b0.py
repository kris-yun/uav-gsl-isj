#!/usr/bin/env python3
"""Independent CSV-level B0 gate replay and raw-reextraction tensor comparison."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import trim_mean


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--g0-cache", type=Path, required=True)
    parser.add_argument("--raw-reaudit-cache", type=Path, required=True)
    parser.add_argument("--raw-reaudit-json", type=Path, required=True)
    args = parser.parse_args()
    out = args.out
    raw_audit = json.loads(args.raw_reaudit_json.read_text(encoding="utf-8"))
    assert raw_audit["input_contract_pass"] and raw_audit["all_288_raw_cube_reextractions_exact"]
    assert raw_audit["canonical_cache_sha256"] == sha(args.raw_reaudit_cache)
    with np.load(args.g0_cache, allow_pickle=False) as original, np.load(args.raw_reaudit_cache, allow_pickle=False) as replay:
        for key in ("X", "source_ids", "source_xy", "realization_ids", "time_index", "probe_index", "time_iteration"):
            if not np.array_equal(original[key], replay[key]):
                raise ValueError(f"raw cube replay differs from G0 input: {key}")
    with (out / "JTD_B0_TARGETS.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 288 or len({(r["source_id"], r["replicate"]) for r in rows}) != 288:
        raise ValueError("target-level CSV not exactly 288 unique realizations")
    source_order = {int(r["source_index"]): r["source_id"] for r in rows}
    if sorted(source_order) != list(range(1, 19)):
        raise ValueError("source index drift")
    source_ids = [source_order[i] for i in range(1, 19)]
    if len(source_ids) != 18:
        raise ValueError("source count drift")
    by_source = {source: sorted((r for r in rows if r["source_id"] == source),
                                key=lambda r: int(r["replicate"])) for source in source_ids}
    for source, source_rows in by_source.items():
        if [int(r["replicate"]) for r in source_rows] != list(range(1, 17)):
            raise ValueError(f"replicate drift: {source}")
        for row in source_rows:
            rep = int(row["replicate"])
            if int(row["quartet"]) != (rep-1)//4+1 or int(row["fold"]) != (rep-1)%4+1:
                raise ValueError("quartet/fold drift")
    full = np.array([[float(r["full_truth_nll"]) for r in by_source[s]] for s in source_ids])
    null = np.array([[float(r["shuffled_median_truth_nll"]) for r in by_source[s]] for s in source_ids])
    delta = np.array([[float(r["delta_nll"]) for r in by_source[s]] for s in source_ids])
    if not np.allclose(null-full, delta, rtol=0, atol=1e-12):
        raise ValueError("target-level delta mismatch")
    flat = delta.reshape(-1)
    # Independent loop rather than scorer's vectorized indexing.
    rng = np.random.default_rng(2026092502)
    boot = []
    for _ in range(5000):
        selected_sources = rng.integers(0, 18, 18)
        selected_reps = rng.integers(0, 16, (18, 16))
        sampled = [delta[int(selected_sources[i]), int(selected_reps[i, j])]
                   for i in range(18) for j in range(16)]
        boot.append(float(np.mean(sampled)))
    ci = np.quantile(boot, (0.025, 0.975))
    quartet = [float(np.mean([float(r["delta_nll"]) for r in rows if int(r["quartet"]) == q])) for q in range(1, 5)]
    positive = sorted((float(d) for d in flat if d > 0), reverse=True)
    removed = positive[:math.ceil(0.05*288)]
    # Multiset removal by value handles equal deltas without changing the mean.
    kept = list(float(x) for x in flat)
    for value in removed:
        kept.remove(value)
    relative = float((null.mean() - full.mean()) / null.mean())
    gates = {
        "B0_G1": bool(flat.mean() > 0 and ci[0] > 0),
        "B0_G2": bool(all(x > 0 for x in quartet)),
        "B0_G3": bool(sum(np.mean(delta[i]) > 0 for i in range(18)) >= 14),
        "B0_G4": bool(trim_mean(flat, 0.2) > 0),
        "B0_G5": bool(np.mean(kept) > 0),
        "B0_G6": bool(relative >= 0.10),
    }
    result = json.loads((out / "JTD_B0_RESULT.json").read_text(encoding="utf-8"))
    comparisons = {"mean_delta_nll": float(flat.mean()), "median_delta_nll": float(np.median(flat)),
                   "trimmed_10_mean_delta_nll": float(trim_mean(flat, 0.1)),
                   "trimmed_20_mean_delta_nll": float(trim_mean(flat, 0.2)),
                   "relative_mean_nll_improvement": relative,
                   "g5_retained_mean_delta_nll": float(np.mean(kept)),
                   "full_mean_nll": float(full.mean()),
                   "shuffled_target_median_mean_nll": float(null.mean())}
    for field, value in comparisons.items():
        if not np.isclose(value, result[field], rtol=0, atol=1e-10):
            raise ValueError(f"CSV-level metric mismatch: {field}")
    if not np.allclose(ci, result["bootstrap_95_ci"], atol=1e-10, rtol=0):
        raise ValueError("bootstrap mismatch")
    if not np.allclose(quartet, result["quartet_mean_deltas"], atol=1e-10, rtol=0):
        raise ValueError("quartet mismatch")
    if gates != result["gates"]:
        raise ValueError("gate mismatch")
    decision = "JTD_B0_PASS_R4_ESTIMATOR_BRIDGE" if all(gates.values()) else "JTD_B0_FAIL_R4_ESTIMATOR_NOT_RELIABLE"
    if decision != result["decision"]:
        raise ValueError("decision mismatch")
    verification = {"independent_csv_recompute_pass": True,
                    "all_288_raw_cubes_reextracted": True,
                    "canonical_array_equal_to_g0": True,
                    "raw_reaudit_cache_sha256": sha(args.raw_reaudit_cache),
                    "g0_cache_sha256": sha(args.g0_cache),
                    "raw_reaudit_json_sha256": sha(args.raw_reaudit_json),
                    "metrics": comparisons, "bootstrap_95_ci": ci.tolist(),
                    "quartet_mean_deltas": quartet, "gates": gates,
                    "decision": decision}
    (out / "JTD_B0_INDEPENDENT_VERIFICATION.json").write_text(
        json.dumps(verification, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(decision, "INDEPENDENT_RECOMPUTE_PASS")


if __name__ == "__main__":
    main()

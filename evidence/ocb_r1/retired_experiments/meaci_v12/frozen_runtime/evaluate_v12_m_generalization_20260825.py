#!/usr/bin/env python3
"""One-shot external truth evaluator for the frozen V12-M six-arm qualification."""
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path("/home/zyc/meaci_v12_generalization_20260825_r1")
TRUTHS = {
    "House01": (-0.40, -2.90, 418310734),
    "House02": (0.00, -1.00, 661532441),
    "House03": (-0.45, 1.90, 538848658),
}
BINARY_SHA = "100ca267c1dc6f098f1080f669733bf7cf655d8a05ce8d5afe3ef9b9458a51ce"


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def posterior_metrics(path, truth_x, truth_y):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        raw = list(csv.DictReader(stream))
    points = [(int(r["cell_index"]), float(r["x"]), float(r["y"]),
               max(0.0, float(r["source_probability"]))) for r in raw]
    total = sum(p for _, _, _, p in points)
    assert points and math.isfinite(total) and total > 0.0
    points = [(i, x, y, p / total) for i, x, y, p in points]

    # Exact PMFS Utils::ExpectedValue(grid, 0.05) contract: descending free-cell
    # probability; C++ loop i < N*0.05 retains ceil(0.05*N) cells.
    count = max(1, math.ceil(0.05 * len(points)))
    top = sorted(points, key=lambda z: -z[3])[:count]
    top_mass = sum(p for _, _, _, p in top)
    top_x = sum(x * p for _, x, _, p in top) / top_mass
    top_y = sum(y * p for _, _, y, p in top) / top_mass
    error = math.hypot(top_x - truth_x, top_y - truth_y)

    mean_x = sum(x * p for _, x, _, p in points)
    mean_y = sum(y * p for _, _, y, p in points)
    variance = sum(p * ((x - mean_x) ** 2 + (y - mean_y) ** 2)
                   for _, x, y, p in points)
    within_1m = sum(p for _, x, y, p in points
                    if math.hypot(x - truth_x, y - truth_y) <= 1.0)
    ranked = sorted(points, key=lambda z: (-z[3], z[0]))
    nearest = min(points, key=lambda z: math.hypot(z[1] - truth_x, z[2] - truth_y))
    nearest_rank = next(k + 1 for k, row in enumerate(ranked) if row[0] == nearest[0])
    map_row = ranked[0]
    return {
        "posterior_sha256": sha256(path),
        "free_cell_count": len(points),
        "top5_cell_count": count,
        "top5_mass": top_mass,
        "estimate_x": top_x,
        "estimate_y": top_y,
        "pmfs_expected_value_005_error_m": error,
        "posterior_mean_x": mean_x,
        "posterior_mean_y": mean_y,
        "posterior_variance_m2": variance,
        "posterior_std_m": math.sqrt(max(0.0, variance)),
        "mass_within_1m": within_1m,
        "nearest_truth_cell_index": nearest[0],
        "nearest_truth_cell_distance_m": math.hypot(nearest[1] - truth_x, nearest[2] - truth_y),
        "nearest_truth_cell_rank": nearest_rank,
        "nearest_truth_cell_rank_fraction": nearest_rank / len(points),
        "map_x": map_row[1],
        "map_y": map_row[2],
        "map_error_m": math.hypot(map_row[1] - truth_x, map_row[2] - truth_y),
    }


def main():
    cases = []
    for house, (tx, ty, seed) in TRUTHS.items():
        for arm, mode in (("off", "off"), ("on", "rc_sd_tfei_v12")):
            run = ROOT / f"{house}_seed{seed}_{arm}_{mode}"
            status = json.loads((run / "run_status.json").read_text())
            manifest = json.loads((run / "runtime_manifest.json").read_text())
            assert status["status"] == "time_budget_timeout" and status["seed"] == seed
            assert manifest["algorithm_sha256"] == BINARY_SHA
            assert manifest["contract"] == "V12_M_HELDOUT_FRESH_SEED_FULL300_V1"
            updates = sorted((run / "context_bank").glob("source_update_*/source_posterior.csv"))
            assert len(updates) == 5
            metrics = posterior_metrics(updates[-1], tx, ty)
            metrics.update({"house": house, "seed": seed, "arm": arm,
                            "final_update": updates[-1].parent.name,
                            "truth_x": tx, "truth_y": ty})
            cases.append(metrics)

    pairs = []
    for house in TRUTHS:
        off = next(x for x in cases if x["house"] == house and x["arm"] == "off")
        on = next(x for x in cases if x["house"] == house and x["arm"] == "on")
        off_error = off["pmfs_expected_value_005_error_m"]
        on_error = on["pmfs_expected_value_005_error_m"]
        improvement = (off_error - on_error) / max(off_error, 1e-15)
        catastrophe = on_error >= 1.20 * off_error and on_error - off_error >= 0.5
        false_confident = on["posterior_variance_m2"] < 1.0 and on_error > 2.0
        pairs.append({
            "house": house,
            "seed": off["seed"],
            "off_error_m": off_error,
            "on_error_m": on_error,
            "improvement_fraction": improvement,
            "improved": on_error < off_error,
            "catastrophic_regression": catastrophe,
            "false_confident_collapse": false_confident,
            "off_variance_m2": off["posterior_variance_m2"],
            "on_variance_m2": on["posterior_variance_m2"],
            "off_mass_within_1m": off["mass_within_1m"],
            "on_mass_within_1m": on["mass_within_1m"],
            "off_truth_rank": off["nearest_truth_cell_rank"],
            "on_truth_rank": on["nearest_truth_cell_rank"],
        })

    pooled_off = sum(p["off_error_m"] for p in pairs)
    pooled_on = sum(p["on_error_m"] for p in pairs)
    pooled_improvement = (pooled_off - pooled_on) / pooled_off
    improved_count = sum(p["improved"] for p in pairs)
    no_catastrophe = not any(p["catastrophic_regression"] for p in pairs)
    no_collapse = not any(p["false_confident_collapse"] for p in pairs)
    go = pooled_improvement >= 0.10 and improved_count >= 2 and no_catastrophe and no_collapse
    payload = {
        "contract": "V12_M_HELDOUT_GENERALIZATION_EXTERNAL_TRUTH_EVALUATION_V1",
        "primary_metric": "PMFS Utils::ExpectedValue(sourceProbability, 0.05) Euclidean error",
        "unblinded_after_six_arm_integrity": True,
        "cases": cases,
        "pairs": pairs,
        "aggregate": {
            "pooled_off_error_sum_m": pooled_off,
            "pooled_on_error_sum_m": pooled_on,
            "pooled_improvement_fraction": pooled_improvement,
            "houses_improved": improved_count,
            "houses_total": len(pairs),
            "no_catastrophic_regression": no_catastrophe,
            "no_false_confident_collapse": no_collapse,
        },
        "frozen_rule": {
            "pooled_improvement_at_least_10_percent": pooled_improvement >= 0.10,
            "at_least_2_of_3_houses_improve": improved_count >= 2,
            "no_catastrophic_regression": no_catastrophe,
            "no_false_confident_collapse": no_collapse,
        },
        "verdict": "V12_M_HELDOUT_GENERALIZATION_GO" if go else "V12_M_HELDOUT_GENERALIZATION_NO_GO",
    }
    out = ROOT / "V12_M_HELDOUT_GENERALIZATION_RESULT.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    with (ROOT / "V12_M_HELDOUT_GENERALIZATION_PAIRS.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(pairs[0]))
        writer.writeheader(); writer.writerows(pairs)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

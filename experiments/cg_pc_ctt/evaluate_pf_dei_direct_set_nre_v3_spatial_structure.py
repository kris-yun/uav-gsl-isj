#!/usr/bin/env python3
"""Spatial-structure audit for frozen PF-DEI Direct Set-NRE V2 outputs.

This script does NOT train, tune, or alter the frozen V2 posterior. It asks a
narrow diagnostic question: did V2 move posterior mass into a physically local
source region even when the exact carrier ID failed Top-K?

Truth is used only after scoring to evaluate spatial localization metrics.
The truth-blind regional summary is defined purely from carrier geometry and
the frozen direct posterior.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np

from pf_dei_direct_set_nre_v2 import direct_posterior


FIXED_RADII_M = (0.5, 1.0, 2.0)
EPS = 1e-12


def stable_argmax(values: np.ndarray, carrier_ids: np.ndarray) -> int:
    values = np.asarray(values, dtype=np.float64)
    carrier_ids = np.asarray(carrier_ids).astype(str)
    if values.ndim != 1 or values.shape[0] != carrier_ids.shape[0]:
        raise ValueError("stable_argmax shape mismatch")
    order = np.lexsort((carrier_ids, -values))
    return int(order[0])


def normalize_mass(p: np.ndarray) -> np.ndarray:
    p = np.asarray(p, dtype=np.float64)
    if p.ndim != 1 or not np.all(np.isfinite(p)) or np.any(p < 0):
        raise ValueError("invalid mass vector")
    total = float(p.sum())
    if total <= 0:
        raise ValueError("mass vector sums to zero")
    return p / total


def carrier_arrays(carriers: list[dict]):
    ids = np.asarray([str(c["carrier_id"]) for c in carriers])
    xy = np.asarray([[float(c["centroid_x"]), float(c["centroid_y"])] for c in carriers], dtype=np.float64)
    widths = np.asarray([float(c["width_m"]) for c in carriers], dtype=np.float64)
    heights = np.asarray([float(c["height_m"]) for c in carriers], dtype=np.float64)
    q0 = normalize_mass(np.asarray([float(c["prior_mass"]) for c in carriers], dtype=np.float64))
    if np.any(widths <= 0) or np.any(heights <= 0):
        raise ValueError("carrier width/height must be positive")
    radius = 0.5 * np.sqrt(widths * widths + heights * heights)
    return ids, xy, radius, q0


def resolution_overlap_graph(xy: np.ndarray, radius: np.ndarray) -> np.ndarray:
    """Geometry-only adjacency using overlap of circumscribed carrier disks.

    A_ij = 1 iff ||x_i-x_j|| <= a_i + a_j, with self-inclusion guaranteed.
    There is no learned/tuned bandwidth.
    """
    xy = np.asarray(xy, dtype=np.float64)
    radius = np.asarray(radius, dtype=np.float64)
    delta = xy[:, None, :] - xy[None, :, :]
    dist = np.linalg.norm(delta, axis=-1)
    graph = dist <= (radius[:, None] + radius[None, :] + 1e-12)
    np.fill_diagonal(graph, True)
    return graph


def regional_summary(
    posterior: np.ndarray,
    prior: np.ndarray,
    xy: np.ndarray,
    graph: np.ndarray,
    carrier_ids: np.ndarray,
) -> dict:
    """Truth-blind regional summary of an already-frozen posterior."""
    p = normalize_mass(posterior)
    q = normalize_mass(prior)
    A = np.asarray(graph, dtype=bool)
    if A.shape != (len(p), len(p)):
        raise ValueError("graph shape mismatch")

    region_mass = A.astype(np.float64) @ p
    region_prior = A.astype(np.float64) @ q
    log_region_bf = np.log(region_mass + EPS) - np.log(region_prior + EPS)

    mass_idx = stable_argmax(region_mass, carrier_ids)
    bf_idx = stable_argmax(log_region_bf, carrier_ids)

    def local_centroid(idx: int) -> np.ndarray:
        mask = A[idx]
        mass = float(p[mask].sum())
        if mass <= 0:
            return xy[idx].copy()
        return np.sum(p[mask, None] * xy[mask], axis=0) / mass

    return {
        "region_mass": region_mass,
        "region_prior": region_prior,
        "log_region_bf": log_region_bf,
        "mass_mode_index": mass_idx,
        "bf_mode_index": bf_idx,
        "mass_mode_xy": local_centroid(mass_idx),
        "bf_mode_xy": local_centroid(bf_idx),
    }


def expected_radial_error(posterior: np.ndarray, xy: np.ndarray, truth_xy: np.ndarray) -> float:
    p = normalize_mass(posterior)
    return float(np.sum(p * np.linalg.norm(xy - truth_xy[None, :], axis=1)))


def posterior_mean(posterior: np.ndarray, xy: np.ndarray) -> np.ndarray:
    p = normalize_mass(posterior)
    return np.sum(p[:, None] * xy, axis=0)


def exact_rank_desc(values: np.ndarray, carrier_ids: np.ndarray, target_idx: int) -> int:
    order = np.lexsort((carrier_ids.astype(str), -np.asarray(values, dtype=np.float64)))
    return int(np.flatnonzero(order == target_idx)[0]) + 1


def topk_min_distance(posterior: np.ndarray, xy: np.ndarray, carrier_ids: np.ndarray, truth_xy: np.ndarray, k: int) -> float:
    order = np.lexsort((carrier_ids.astype(str), -np.asarray(posterior, dtype=np.float64)))
    top = order[: min(int(k), len(order))]
    return float(np.min(np.linalg.norm(xy[top] - truth_xy[None, :], axis=1)))


def mass_within_radius(posterior: np.ndarray, xy: np.ndarray, truth_xy: np.ndarray, radius_m: float) -> float:
    p = normalize_mass(posterior)
    mask = np.linalg.norm(xy - truth_xy[None, :], axis=1) <= float(radius_m) + 1e-12
    return float(p[mask].sum())


def summarize(rows: list[dict]) -> dict:
    def mean(key):
        return float(np.mean([float(r[key]) for r in rows]))

    def median(key):
        return float(np.median([float(r[key]) for r in rows]))

    out = {
        "cases": len(rows),
        "direct_expected_radial_error_m": mean("direct_expected_radial_error_m"),
        "pmfs_expected_radial_error_m": mean("pmfs_expected_radial_error_m"),
        "direct_posterior_mean_error_m": mean("direct_posterior_mean_error_m"),
        "pmfs_posterior_mean_error_m": mean("pmfs_posterior_mean_error_m"),
        "direct_map_error_m": mean("direct_map_error_m"),
        "pmfs_map_error_m": mean("pmfs_map_error_m"),
        "direct_region_mass_mode_error_m": mean("direct_region_mass_mode_error_m"),
        "direct_region_bf_mode_error_m": mean("direct_region_bf_mode_error_m"),
        "median_true_local_log_bf": median("direct_true_local_log_bf"),
        "true_local_log_bf_positive_cases": int(sum(float(r["direct_true_local_log_bf"]) > 0.0 for r in rows)),
        "direct_top10_min_distance_mean_m": mean("direct_top10_min_distance_m"),
        "pmfs_top10_min_distance_mean_m": mean("pmfs_top10_min_distance_m"),
    }
    for radius_m in FIXED_RADII_M:
        tag = str(radius_m).replace(".", "p")
        out[f"direct_mass_within_{tag}m_mean"] = mean(f"direct_mass_within_{tag}m")
        out[f"pmfs_mass_within_{tag}m_mean"] = mean(f"pmfs_mass_within_{tag}m")
    base = out["pmfs_expected_radial_error_m"]
    out["direct_expected_radial_error_relative_improvement"] = (
        (base - out["direct_expected_radial_error_m"]) / base if base > 0 else math.nan
    )
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset-root", type=Path, required=True)
    ap.add_argument("--pmfs-posteriors", type=Path, required=True)
    ap.add_argument("--historical-evaluation", type=Path, required=True)
    ap.add_argument("--historical-logits", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    carriers = json.loads((args.dataset_root / "H01_carriers.json").read_text(encoding="utf-8"))
    carrier_ids, xy, support_radius, q0 = carrier_arrays(carriers)
    graph = resolution_overlap_graph(xy, support_radius)

    frozen = np.load(args.pmfs_posteriors, allow_pickle=False)
    pmfs_ids = np.asarray(frozen["carrier_id"]).astype(str)
    pmfs = np.asarray(frozen["posterior"], dtype=np.float64)
    if not np.array_equal(pmfs_ids, carrier_ids) or pmfs.shape != (10, 5, len(carrier_ids)):
        raise ValueError("PMFS posterior identity mismatch")

    evaluation = json.loads(args.historical_evaluation.read_text(encoding="utf-8"))
    if evaluation.get("contract") != "PF_DEI_DIRECT_SET_NRE_V2_H01_HISTORICAL_HOLDOUT_EVAL":
        raise ValueError("wrong frozen V2 evaluation contract")
    cases = evaluation["cases"]
    if len(cases) != 50:
        raise ValueError("expected 50 frozen H01 cases")

    logits = np.asarray(np.load(args.historical_logits, allow_pickle=False), dtype=np.float64)
    if logits.shape != (50, len(carrier_ids)):
        raise ValueError("historical logits shape mismatch")

    truth_id = str(cases[0]["true_carrier_evaluation_only"])
    hits = np.flatnonzero(carrier_ids == truth_id)
    if len(hits) != 1:
        raise ValueError("truth carrier missing")
    truth_idx = int(hits[0])
    truth_xy = xy[truth_idx]

    rows = []
    for case_index, case in enumerate(cases):
        if str(case["true_carrier_evaluation_only"]) != truth_id:
            raise ValueError("truth carrier changed across cases")
        seed = int(case["seed"])
        update = int(case["source_update_id"])
        if not (0 <= seed <= 9 and 1 <= update <= 5):
            raise ValueError("unexpected seed/update")

        direct = direct_posterior(q0, logits[case_index])
        base = normalize_mass(pmfs[seed, update - 1])

        reconstructed_rank = exact_rank_desc(direct, carrier_ids, truth_idx)
        if reconstructed_rank != int(case["direct_true_rank"]):
            raise ValueError(
                f"case {case_index}: reconstructed direct rank {reconstructed_rank} "
                f"!= frozen {case['direct_true_rank']}"
            )

        region = regional_summary(direct, q0, xy, graph, carrier_ids)
        direct_map = stable_argmax(direct, carrier_ids)
        pmfs_map = stable_argmax(base, carrier_ids)

        row = {
            "case_index": case_index,
            "seed": seed,
            "source_update_id": update,
            "true_carrier": truth_id,
            "direct_exact_true_rank": reconstructed_rank,
            "pmfs_exact_true_rank": exact_rank_desc(base, carrier_ids, truth_idx),
            "direct_posterior_mean_error_m": float(np.linalg.norm(posterior_mean(direct, xy) - truth_xy)),
            "pmfs_posterior_mean_error_m": float(np.linalg.norm(posterior_mean(base, xy) - truth_xy)),
            "direct_expected_radial_error_m": expected_radial_error(direct, xy, truth_xy),
            "pmfs_expected_radial_error_m": expected_radial_error(base, xy, truth_xy),
            "direct_map_error_m": float(np.linalg.norm(xy[direct_map] - truth_xy)),
            "pmfs_map_error_m": float(np.linalg.norm(xy[pmfs_map] - truth_xy)),
            "direct_region_mass_mode_error_m": float(np.linalg.norm(region["mass_mode_xy"] - truth_xy)),
            "direct_region_bf_mode_error_m": float(np.linalg.norm(region["bf_mode_xy"] - truth_xy)),
            "direct_region_mass_mode_index": int(region["mass_mode_index"]),
            "direct_region_bf_mode_index": int(region["bf_mode_index"]),
            "direct_true_local_mass": float(region["region_mass"][truth_idx]),
            "prior_true_local_mass": float(region["region_prior"][truth_idx]),
            "direct_true_local_log_bf": float(region["log_region_bf"][truth_idx]),
            "direct_top1_min_distance_m": topk_min_distance(direct, xy, carrier_ids, truth_xy, 1),
            "direct_top5_min_distance_m": topk_min_distance(direct, xy, carrier_ids, truth_xy, 5),
            "direct_top10_min_distance_m": topk_min_distance(direct, xy, carrier_ids, truth_xy, 10),
            "pmfs_top1_min_distance_m": topk_min_distance(base, xy, carrier_ids, truth_xy, 1),
            "pmfs_top5_min_distance_m": topk_min_distance(base, xy, carrier_ids, truth_xy, 5),
            "pmfs_top10_min_distance_m": topk_min_distance(base, xy, carrier_ids, truth_xy, 10),
            "truth_used_during_scoring": False,
            "regional_rule_truth_blind": True,
        }
        for radius_m in FIXED_RADII_M:
            tag = str(radius_m).replace(".", "p")
            row[f"direct_mass_within_{tag}m"] = mass_within_radius(direct, xy, truth_xy, radius_m)
            row[f"pmfs_mass_within_{tag}m"] = mass_within_radius(base, xy, truth_xy, radius_m)
        rows.append(row)

    aggregate = summarize(rows)
    by_update = {
        str(update): summarize([r for r in rows if r["source_update_id"] == update])
        for update in range(1, 6)
    }

    result = {
        "contract": "PF_DEI_DIRECT_SET_NRE_V3_SPATIAL_STRUCTURE_AUDIT",
        "parent_contract": evaluation["contract"],
        "scientific_status": "DIAGNOSTIC_ONLY_DO_NOT_AUTHORIZE_RETRAINING_OR_CLOSED_LOOP",
        "frozen_fixed_radii_m": list(FIXED_RADII_M),
        "adaptive_region_definition": "circumscribed-carrier-disk overlap: d_ij <= a_i + a_j",
        "adaptive_radius_definition": "a_i = 0.5*sqrt(width_m^2 + height_m^2)",
        "regional_mass_is_decision_summary_not_new_posterior": True,
        "truth_used_only_for_post_scoring_evaluation": True,
        "aggregate": aggregate,
        "by_source_update": by_update,
        "cases": rows,
    }

    with (args.out / "spatial_structure_cases.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (args.out / "spatial_structure_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("PF_DEI_DIRECT_SET_NRE_V3_SPATIAL_STRUCTURE_AUDIT_COMPLETE " + json.dumps(aggregate, sort_keys=True))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Held-out-House reserved multi-source sweep for frozen PF-SNRE.

Canonical reserved panel files per House:
  reserved_predictive_measured.npy [S,8,J,T]
  reserved_observations_measured.npy [S,4,J,T]
  reserved_source_xy.npy [S,4,J,2]
  reserved_blocks.npz CanonicalBlocks for J trajectories
The predictive array uses train8 nuisance members. The observation array uses
exactly four frozen reserved nuisance members. Both measured arrays must have
been produced by advancing the persistent sensor state on the complete timeline.
"""
from __future__ import annotations
import argparse
import csv
import json
import time
from pathlib import Path

import numpy as np
import torch

from pf_snre_final_core import (
    ConditionedMomentSetDirectNRE, HouseDataset, block_context,
    candidate_features, direct_posterior, log_measurement, sha256,
)
from pf_snre_spatial_eval import (
    load_carrier_cells, expand_region_mass_to_cells, posterior_mean_xy,
    spatial_energy_score, hpd_cell_mask, mass_within_radius, density_rank,
    deterministic_kcenter, precompute_distance_matrix,
)


def score_candidates(model, data, observation, trajectory, visible,
                     physics_source_map=None, batch_size=32):
    idx = data.blocks.sample_indices[trajectory, :visible]
    obs = log_measurement(observation[idx])
    logits = np.empty(data.source_count, dtype=np.float64)
    with torch.no_grad():
        for start in range(0, data.source_count, batch_size):
            candidates = np.arange(start, min(start + batch_size, data.source_count), dtype=np.int64)
            n = len(candidates)
            physics = candidates if physics_source_map is None else np.asarray(physics_source_map)[candidates]
            pred = data.measured[physics, :, trajectory][:, :, idx]
            pred = np.transpose(pred, (0, 2, 1, 3))
            obs_batch = np.repeat(obs[None, :, :], n, axis=0)
            ctx = np.stack([block_context(data, trajectory, visible, int(c)) for c in candidates])
            cand = np.stack([
                candidate_features(data.carriers[int(c)], data.xy_center, data.xy_scale)
                for c in candidates
            ])
            bm = np.ones((n, visible), dtype=np.bool_)
            mm = np.ones((n, 8), dtype=np.bool_)
            tensor_args = [torch.from_numpy(a) for a in (
                obs_batch.astype(np.float32), log_measurement(pred), ctx, cand, bm, mm)]
            logits[start:start + n] = model(*tensor_args).numpy()
    return logits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--house", choices=("H01", "H02", "H03"), required=True)
    ap.add_argument("--carriers", type=Path, required=True)
    ap.add_argument("--reserved-predictive", type=Path, required=True)
    ap.add_argument("--reserved-observations", type=Path, required=True)
    ap.add_argument("--reserved-source-xy", type=Path, required=True)
    ap.add_argument("--reserved-blocks", type=Path, required=True)
    ap.add_argument("--checkpoint", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()

    data = HouseDataset.load(args.house, args.reserved_predictive, args.carriers, args.reserved_blocks)
    obs = np.load(args.reserved_observations, mmap_mode="r")
    truth_xy = np.load(args.reserved_source_xy, mmap_mode="r")
    if obs.shape[:3] != (data.source_count, 4, data.trajectory_count):
        raise ValueError("reserved observation panel must be [S,4,J,T]")
    if truth_xy.shape != (data.source_count, 4, data.trajectory_count, 2):
        raise ValueError("reserved source XY must be [S,4,J,2]")
    if obs.shape[-1] != data.measured.shape[-1]:
        raise ValueError("reserved observation/predictive timeline length mismatch")

    ck = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    if (ck.get("heldout_house") != args.house or
            ck.get("architecture") != "conditioned_moment_set_direct_nre_v2_exact_topology"):
        raise ValueError("checkpoint is not the frozen LOHO PF-SNRE model for this House")
    model = ConditionedMomentSetDirectNRE(
        int(ck["candidate_dim"]), int(ck["block_context_dim"]), int(ck["hidden"]))
    model.load_state_dict(ck["model_state"])
    model.eval()

    ids, centroids, q0, cells, ptr = load_carrier_cells(args.carriers)
    if not np.array_equal(ids, np.asarray([str(c["carrier_id"]) for c in data.carriers])):
        raise ValueError("carrier identity mismatch")
    if np.max(np.abs(q0 - data.prior)) > 1e-12:
        raise ValueError("q0 mismatch")
    selected = deterministic_kcenter(centroids, ids, 32)
    traj_order = np.argsort(data.blocks.trajectory_sha.astype(str), kind="stable")
    if len(traj_order) < 2:
        raise ValueError("need >=2 reserved trajectories")
    trajectories = np.asarray([traj_order[0], traj_order[-1]], dtype=np.int64)

    # Deterministic no-physics leakage diagnostic: preserve candidate geometry
    # and observations while assigning every candidate another source's physics.
    id_order = np.argsort(ids, kind="stable")
    physics_perm = np.empty(len(ids), dtype=np.int64)
    physics_perm[id_order] = np.roll(id_order, 1)
    if np.any(physics_perm == np.arange(len(ids))):
        raise RuntimeError("no-physics permutation contains a fixed point")

    dmat = precompute_distance_matrix(cells)
    q0_cells = expand_region_mass_to_cells(q0, ptr)
    q0_point = posterior_mean_xy(q0_cells, cells)
    rows = []
    for source in selected:
        for member in range(4):
            for trajectory in trajectories:
                for update in range(1, 6):
                    visible = data.blocks.visible(int(trajectory), update)
                    y = np.asarray(obs[source, member, trajectory], dtype=np.float32)
                    logits = score_candidates(model, data, y, int(trajectory), visible)
                    posterior = direct_posterior(q0, logits)
                    cellp = expand_region_mass_to_cells(posterior, ptr)
                    no_logits = score_candidates(
                        model, data, y, int(trajectory), visible, physics_source_map=physics_perm)
                    no_p = direct_posterior(q0, no_logits)
                    no_cell = expand_region_mass_to_cells(no_p, ptr)
                    true = np.asarray(truth_xy[source, member, trajectory], dtype=np.float64)
                    point = posterior_mean_xy(cellp, cells)
                    no_point = posterior_mean_xy(no_cell, cells)
                    hpd90 = hpd_cell_mask(cellp, 0.9)

                    source_cells = cells[ptr[source]:ptr[source + 1]]
                    hit = np.flatnonzero(np.linalg.norm(source_cells - true[None, :], axis=1) <= 1e-8)
                    if len(hit) != 1:
                        raise ValueError(
                            f"exact source XY is not one free-cell center: {args.house} {ids[source]}")
                    true_cell = ptr[source] + int(hit[0])
                    rows.append({
                        "house": args.house, "source_id": str(ids[source]),
                        "reserved_member": member,
                        "trajectory_sha": str(data.blocks.trajectory_sha[trajectory]),
                        "update": update, "visible_blocks": visible,
                        "pf_error_m": float(np.linalg.norm(point - true)),
                        "q0_error_m": float(np.linalg.norm(q0_point - true)),
                        "no_physics_error_m": float(np.linalg.norm(no_point - true)),
                        "pf_energy_score": float(spatial_energy_score(cellp, cells, true, dmat)),
                        "q0_energy_score": float(spatial_energy_score(q0_cells, cells, true, dmat)),
                        "mass_1m": mass_within_radius(cellp, cells, true, 1.0),
                        "mass_2m": mass_within_radius(cellp, cells, true, 2.0),
                        "density_rank": density_rank(logits, int(source), ids),
                        "posterior_carrier_rank": density_rank(np.log(posterior), int(source), ids),
                        "hpd90_contains_truth": bool(hpd90[true_cell]),
                        "hpd90_cell_fraction": float(hpd90.mean()),
                        "max_carrier_mass": float(posterior.max()),
                        "max_cell_mass": float(cellp.max()),
                    })

    def agg(key):
        return float(np.mean([r[key] for r in rows]))

    summary = {
        "contract": "PF_SNRE_RESERVED_SOURCE_SWEEP_V1", "house": args.house,
        "cases": len(rows), "source_count": len(selected), "reserved_members": 4,
        "reserved_trajectories": 2, "updates": 5,
        "selected_source_ids": [str(ids[i]) for i in selected],
        "trajectory_sha": [str(data.blocks.trajectory_sha[i]) for i in trajectories],
        "mean_pf_error_m": agg("pf_error_m"), "mean_q0_error_m": agg("q0_error_m"),
        "mean_no_physics_error_m": agg("no_physics_error_m"),
        "relative_error_improvement_vs_q0":
            (agg("q0_error_m") - agg("pf_error_m")) / agg("q0_error_m"),
        "relative_error_improvement_no_physics_vs_q0":
            (agg("q0_error_m") - agg("no_physics_error_m")) / agg("q0_error_m"),
        "mean_pf_energy_score": agg("pf_energy_score"),
        "mean_q0_energy_score": agg("q0_energy_score"),
        "median_normalized_density_rank": float(np.median([
            (r["density_rank"] - 1) / (len(ids) - 1) for r in rows])),
        "hpd90_coverage": float(np.mean([r["hpd90_contains_truth"] for r in rows])),
        "checkpoint_sha256": sha256(args.checkpoint),
        "wall_time_s": time.monotonic() - started,
    }
    with (args.out / "source_sweep_cases.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    (args.out / "source_sweep_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PF_SNRE_RESERVED_SOURCE_SWEEP_COMPLETE " + json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()

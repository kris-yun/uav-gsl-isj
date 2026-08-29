#!/usr/bin/env python3
"""One-shot historical H01 seeds0..9 x five-update Set-NRE evaluation."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import time

import numpy as np
import torch

from pf_dei_set_nre import (
    ConditionedDeepSetNRE,
    block_context,
    build_block_layout,
    candidate_features,
    log_measurement,
    residual_corrected_posterior,
    sha256,
)


TRUE_CARRIER_EVAL_ONLY = "quadtree_22_16_2_2"


def stable_rank_desc(values: np.ndarray, ids: np.ndarray, target: int) -> int:
    order = np.lexsort((ids.astype(str), -np.asarray(values, dtype=np.float64)))
    return int(np.flatnonzero(order == target)[0]) + 1


def norm_rank(rank: int, n: int = 210) -> float:
    return float(rank - 1) / float(n - 1)


def load_observed_blocks(path: Path):
    out = {seed: [] for seed in range(10)}
    with path.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["house"] != "House01" or int(row["seed"]) not in out:
                continue
            out[int(row["seed"])].append({
                "block_id": int(row["block_id"]),
                "indices": np.asarray([int(v) for v in row["sample_row_indices"].split(";")], dtype=np.int64),
                "measured": np.asarray([float(v) for v in row["measured_ppm"].split(";")], dtype=np.float32),
            })
    for seed, rows in out.items():
        rows.sort(key=lambda r: r["block_id"])
        if [r["block_id"] for r in rows] != list(range(1, len(rows) + 1)):
            raise ValueError(f"seed{seed}: observed blocks are incomplete")
    return out


def summarize(rows):
    base = np.asarray([r["pmfs_true_rank"] for r in rows])
    corr = np.asarray([r["corrected_true_rank"] for r in rows])
    bn = np.asarray([r["pmfs_normalized_rank"] for r in rows])
    cn = np.asarray([r["corrected_normalized_rank"] for r in rows])
    be = np.asarray([r["pmfs_carrier_centroid_expected_error_m"] for r in rows])
    ce = np.asarray([r["corrected_carrier_centroid_expected_error_m"] for r in rows])
    return {
        "cases": len(rows),
        "pmfs_top1": int(np.sum(base <= 1)),
        "pmfs_top5": int(np.sum(base <= 5)),
        "pmfs_top10": int(np.sum(base <= 10)),
        "corrected_top1": int(np.sum(corr <= 1)),
        "corrected_top5": int(np.sum(corr <= 5)),
        "corrected_top10": int(np.sum(corr <= 10)),
        "pmfs_median_normalized_rank": float(np.median(bn)),
        "corrected_median_normalized_rank": float(np.median(cn)),
        "pmfs_mean_normalized_rank": float(np.mean(bn)),
        "corrected_mean_normalized_rank": float(np.mean(cn)),
        "rank_improved": int(np.sum(corr < base)),
        "rank_tied": int(np.sum(corr == base)),
        "rank_worsened": int(np.sum(corr > base)),
        "pmfs_mean_carrier_centroid_expected_error_m": float(np.mean(be)),
        "corrected_mean_carrier_centroid_expected_error_m": float(np.mean(ce)),
        "relative_expected_error_improvement": float((np.mean(be) - np.mean(ce)) / np.mean(be)),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset-root", type=Path, required=True)
    ap.add_argument("--pmfs-posteriors", type=Path, required=True)
    ap.add_argument("--observed-block-manifest", type=Path, required=True)
    ap.add_argument("--checkpoint", type=Path, required=True)
    ap.add_argument("--training-summary", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()

    training = json.loads(args.training_summary.read_text(encoding="utf-8"))
    if training["seed"] != 3101 or training["checkpoint_selection"] != "minimum simulated validation BCE only":
        raise ValueError("checkpoint is not the frozen seed3101 validation-BCE selection")
    if training["checkpoint_sha256"] != sha256(args.checkpoint):
        raise ValueError("checkpoint hash mismatch")
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    model = ConditionedDeepSetNRE(
        candidate_dim=int(checkpoint["candidate_dim"]),
        block_context_dim=int(checkpoint["block_context_dim"]),
        hidden=int(checkpoint["hidden"]),
    )
    model.load_state_dict(checkpoint["model_state"]); model.eval()

    measured = np.load(args.dataset_root / "H01_measured_train.npy", mmap_mode="r")
    schedule = np.load(args.dataset_root / "H01_schedule_train.npz", allow_pickle=False)
    carriers = json.loads((args.dataset_root / "H01_carriers.json").read_text(encoding="utf-8"))
    frozen = np.load(args.pmfs_posteriors, allow_pickle=False)
    q_matrix = np.asarray(frozen["posterior"], dtype=np.float64)
    ids = np.asarray(frozen["carrier_id"]).astype(str)
    carrier_ids = np.asarray([c["carrier_id"] for c in carriers]).astype(str)
    if not np.array_equal(ids, carrier_ids) or q_matrix.shape != (10, 5, 210):
        raise ValueError("evaluation carrier/posterior identity mismatch")
    true_hit = np.flatnonzero(ids == TRUE_CARRIER_EVAL_ONLY)
    if len(true_hit) != 1:
        raise ValueError("evaluation-only truth carrier is missing")
    true_idx = int(true_hit[0])
    xy = np.asarray([[c["centroid_x"], c["centroid_y"]] for c in carriers], dtype=np.float64)
    true_xy = xy[true_idx]
    xy_center = 0.5 * (xy.min(axis=0) + xy.max(axis=0))
    xy_scale = np.maximum(xy.max(axis=0) - xy.min(axis=0), 1e-6)
    observed = load_observed_blocks(args.observed_block_manifest)
    layouts = [
        build_block_layout(schedule["x"][seed], schedule["y"][seed],
                           schedule["stop_start"][seed], int(schedule["lengths"][seed]))
        for seed in range(10)
    ]

    rows = []
    all_logits = []
    with torch.no_grad():
        for seed in range(10):
            layout = layouts[seed]
            manifest_indices = np.stack([r["indices"] for r in observed[seed]])
            if len(manifest_indices) < 128:
                raise ValueError(f"seed{seed}: fewer than five authoritative source-update prefixes")
            for update in range(1, 6):
                visible = layout.visible_blocks(update)
                obs_np = log_measurement(np.stack([r["measured"] for r in observed[seed][:visible]]))
                q = q_matrix[seed, update - 1]
                logits = np.empty(210, dtype=np.float64)
                for start in range(0, 210, 30):
                    candidates = np.arange(start, min(start + 30, 210))
                    count = len(candidates)
                    indices = manifest_indices[:visible]
                    pred = measured[candidates, :, seed][:, :, indices]
                    pred = np.transpose(pred, (0, 2, 1, 3))
                    obs_batch = np.repeat(obs_np[None, :, :], count, axis=0)
                    ctx = np.stack([
                        block_context(layout, visible, carriers[int(c)], xy_center, xy_scale)
                        for c in candidates
                    ])
                    cand = np.stack([
                        candidate_features(carriers[int(c)], xy_center, xy_scale, q, xy, int(c))
                        for c in candidates
                    ])
                    bmask = np.ones((count, visible), dtype=np.bool_)
                    mmask = np.ones((count, 8), dtype=np.bool_)
                    tensor_args = [torch.from_numpy(a) for a in (
                        obs_batch.astype(np.float32), log_measurement(pred), ctx.astype(np.float32),
                        cand.astype(np.float32), bmask, mmask)]
                    logits[start:start + count] = model(*tensor_args).numpy()
                # Evaluation truth enters only after all 210 scores are complete.
                corrected = residual_corrected_posterior(q, logits)
                pmfs_rank = stable_rank_desc(q, ids, true_idx)
                corrected_rank = stable_rank_desc(corrected, ids, true_idx)
                pmfs_xy = np.sum(q[:, None] * xy, axis=0)
                corrected_xy = np.sum(corrected[:, None] * xy, axis=0)
                rows.append({
                    "seed": seed,
                    "source_update_id": update,
                    "visible_blocks": visible,
                    "pmfs_true_rank": pmfs_rank,
                    "pmfs_normalized_rank": norm_rank(pmfs_rank),
                    "pmfs_truth_mass": float(q[true_idx]),
                    "corrected_true_rank": corrected_rank,
                    "corrected_normalized_rank": norm_rank(corrected_rank),
                    "corrected_truth_mass": float(corrected[true_idx]),
                    "rank_delta_corrected_minus_pmfs": corrected_rank - pmfs_rank,
                    "pmfs_carrier_centroid_expected_error_m": float(np.linalg.norm(pmfs_xy - true_xy)),
                    "corrected_carrier_centroid_expected_error_m": float(np.linalg.norm(corrected_xy - true_xy)),
                    "selected_pmfs_carrier": str(ids[np.lexsort((ids, -q))[0]]),
                    "selected_corrected_carrier": str(ids[np.lexsort((ids, -corrected))[0]]),
                    "log_ratio_true": float(logits[true_idx]),
                    "log_ratio_min": float(np.min(logits)),
                    "log_ratio_max": float(np.max(logits)),
                    "posterior_kl_corrected_to_pmfs": float(np.sum(corrected * (np.log(corrected) - np.log(q)))),
                    "true_carrier_evaluation_only": TRUE_CARRIER_EVAL_ONLY,
                    "truth_available_during_scoring": False,
                })
                all_logits.append(logits)

    overall = summarize(rows)
    by_update = {str(u): summarize([r for r in rows if r["source_update_id"] == u]) for u in range(1, 6)}
    trajectories = []
    for seed in range(10):
        srows = [r for r in rows if r["seed"] == seed]
        trajectories.append({
            "seed": seed,
            "pmfs_rank_u1_to_u5": [r["pmfs_true_rank"] for r in srows],
            "corrected_rank_u1_to_u5": [r["corrected_true_rank"] for r in srows],
            "pmfs_error_u1_to_u5": [r["pmfs_carrier_centroid_expected_error_m"] for r in srows],
            "corrected_error_u1_to_u5": [r["corrected_carrier_centroid_expected_error_m"] for r in srows],
        })
    result = {
        "contract": "PF_DEI_SET_NRE_H01_HISTORICAL_10SEED_5UPDATE_EVALUATION_V1",
        "scientific_status": "H01_DEVELOPMENT_EXISTING_BANK_DIAGNOSTIC_ONLY",
        "checkpoint_selected_by": "simulated validation BCE only",
        "checkpoint_step": int(checkpoint["step"]),
        "checkpoint_validation_bce": float(checkpoint["validation_bce"]),
        "checkpoint_sha256": sha256(args.checkpoint),
        "overall": overall,
        "by_source_update": by_update,
        "per_seed_trajectories": trajectories,
        "cases": rows,
        "logits_sha256": None,
        "gaden_runs": 0,
        "neural_architecture": "candidate_conditioned_deep_set_plus_plus",
        "forbidden_architectures_used": [],
        "a0_temperature_blend_used": False,
        "wall_time_s": time.monotonic() - started,
    }
    logits_path = args.out / "historical_log_ratios.npy"
    np.save(logits_path, np.asarray(all_logits, dtype=np.float32))
    result["logits_sha256"] = sha256(logits_path)
    with (args.out / "historical_cases.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    (args.out / "historical_evaluation.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PF_DEI_SET_NRE_HISTORICAL_EVALUATION_COMPLETE " + json.dumps({
        "overall": overall, "by_source_update": by_update,
        "checkpoint_step": result["checkpoint_step"],
        "checkpoint_validation_bce": result["checkpoint_validation_bce"],
        "wall_time_s": result["wall_time_s"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()

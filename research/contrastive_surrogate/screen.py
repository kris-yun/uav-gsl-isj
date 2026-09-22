#!/usr/bin/env python3
"""Truth-blind contrastive source-manifold screen on the frozen response bank.

Scientific question
-------------------
Does source identity survive transport variation in a representation that
explicitly contracts same-source / different-transport responses, rather than
treating each simulator response as a literal likelihood?

This script is a *necessary mechanism screen only*.  It never reads source
truth.  Candidate source IDs supplied by the simulator are training group
identities, not evaluation truth.

Frozen bank contract inherited from active_deconfounding V1:
  responses.f32 shape = [world, source, cell]
  worlds 0:27          = design transport worlds
  worlds 27:35         = held-out grid-off transport worlds
  actions              = design["actions"][*]["cell_index"]

V1 deliberately avoids a neural network.  It tests the minimum linear
contrastive object first:
  1. map each Bernoulli action probability p to Hellinger coordinates
       [sqrt(p), sqrt(1-p)];
  2. compute one prototype per candidate source over the 27 design worlds;
  3. estimate pooled *within-source* transport covariance;
  4. whiten that nuisance covariance;
  5. retrieve source identity in the eight untouched held-out worlds.

If this linear proxy cannot beat raw response geometry, a deeper InfoNCE
encoder is not authorized by this screen.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


TRAIN_WORLDS = 27
HELDOUT_WORLDS = 8
EIGEN_FLOOR_REL = 1e-6
EIGEN_FLOOR_ABS = 1e-10
TIE_TOL = 1e-10


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dump(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def load_bank(design_path: Path, bank: Path):
    design = json.loads(design_path.read_text(encoding="utf-8"))
    meta = json.loads((bank / "COMPLETE.json").read_text(encoding="utf-8"))
    if meta.get("worlds") != TRAIN_WORLDS + HELDOUT_WORLDS:
        raise RuntimeError(f"Expected 35 worlds, got {meta.get('worlds')}")
    if meta.get("sources") != len(design["sources"]):
        raise RuntimeError("Source count mismatch between design and bank")

    full = np.memmap(
        bank / "responses.f32",
        dtype="<f4",
        mode="r",
        shape=(meta["worlds"], len(design["sources"]), meta["cells"]),
    )
    if not np.isfinite(full).all() or full.min() < 0.0 or full.max() > 1.0:
        raise RuntimeError("Response bank must contain finite probabilities in [0,1]")

    leaves = np.array(
        [i for i, s in enumerate(design["sources"])
         if float(s.get("measure", 0.0)) > 0.0],
        dtype=int,
    )
    if len(leaves) < 2:
        raise RuntimeError("Need at least two positive-measure source leaves")

    action_cells = np.array(
        [int(a["cell_index"]) for a in design["actions"]], dtype=int)
    if len(action_cells) < 2:
        raise RuntimeError("Need at least two actions for manifold screen")

    # [world, source, action]
    response = np.asarray(full[:, leaves, :][:, :, action_cells], dtype=float)

    measure = np.array(
        [float(design["sources"][i]["measure"]) for i in leaves], dtype=float)
    measure /= measure.sum()

    xy = np.array(
        [[float(design["sources"][i]["x"]), float(design["sources"][i]["y"])]
         for i in leaves],
        dtype=float,
    )
    source_ids = [str(design["sources"][i]["id"]) for i in leaves]
    return design, meta, leaves, action_cells, response, measure, xy, source_ids


def hellinger_features(p: np.ndarray) -> np.ndarray:
    """Bernoulli Hellinger embedding, preserving action identity."""
    p = np.clip(np.asarray(p, dtype=float), 0.0, 1.0)
    return np.concatenate([np.sqrt(p), np.sqrt(1.0 - p)], axis=-1)


def fit_raw(train: np.ndarray, source_weight: np.ndarray) -> dict:
    # train: [world, source, feature]
    prototype = train.mean(axis=0)
    return {
        "kind": "raw",
        "center": np.zeros(train.shape[-1]),
        "whitener": np.eye(train.shape[-1]),
        "prototype": prototype,
    }


def fit_within_source_whitening(
    train: np.ndarray,
    source_weight: np.ndarray,
) -> dict:
    """Whiten transport variability estimated within each source group.

    No truth labels are used.  The only grouping is the simulator candidate ID.
    Source-leaf physical measure weights prevent adaptive-quadtree density from
    dominating the covariance estimate.
    """
    n_world, n_source, dim = train.shape
    if n_world != TRAIN_WORLDS:
        raise RuntimeError("Unexpected training-world count")

    prototype_raw = train.mean(axis=0)  # [source, dim]
    residual = train - prototype_raw[None, :, :]

    # Each source contributes according to represented physical source measure,
    # and its worlds are equally weighted.
    cov = np.zeros((dim, dim), dtype=float)
    for s in range(n_source):
        rs = residual[:, s, :]
        cov += source_weight[s] * (rs.T @ rs) / max(1, n_world - 1)
    cov = 0.5 * (cov + cov.T)

    eigval, eigvec = np.linalg.eigh(cov)
    mean_eig = max(float(np.mean(np.maximum(eigval, 0.0))), EIGEN_FLOOR_ABS)
    floor = max(EIGEN_FLOOR_ABS, EIGEN_FLOOR_REL * mean_eig)
    eigval_f = np.maximum(eigval, floor)
    whitener = eigvec @ np.diag(1.0 / np.sqrt(eigval_f)) @ eigvec.T

    # Weighted global center is source-blind; it merely removes a common mode.
    center = np.sum(prototype_raw * source_weight[:, None], axis=0)
    z_train = (train - center[None, None, :]) @ whitener
    prototype = z_train.mean(axis=0)

    return {
        "kind": "within_source_whitening",
        "center": center,
        "whitener": whitener,
        "prototype": prototype,
        "cov_eigenvalues": eigval.tolist(),
        "eigen_floor": floor,
        "condition_after_floor": float(eigval_f.max() / eigval_f.min()),
    }


def apply(model: dict, x: np.ndarray) -> np.ndarray:
    return (x - model["center"]) @ model["whitener"]


def evaluate(
    model: dict,
    heldout: np.ndarray,
    source_weight: np.ndarray,
    source_xy: np.ndarray,
) -> dict:
    # heldout [world, source, feature]
    z = apply(model, heldout)
    proto = np.asarray(model["prototype"], dtype=float)
    n_world, n_source, _ = z.shape

    rows = []
    for w in range(n_world):
        for s in range(n_source):
            d2 = np.sum((proto - z[w, s]) ** 2, axis=1)
            dt = float(d2[s])
            better = int(np.sum(d2 < dt - TIE_TOL))
            ties = int(np.sum(np.abs(d2 - dt) <= TIE_TOL))
            rank_min = 1 + better
            unique_top1 = bool(rank_min == 1 and ties == 1)
            top5 = bool(rank_min <= 5)
            pred = int(np.argmin(d2))
            rows.append({
                "world": w,
                "source_index": s,
                "rank_min": rank_min,
                "tie_count_at_true_distance": ties,
                "unique_top1": unique_top1,
                "top5": top5,
                "predicted_source_index": pred,
                "xy_error": float(np.linalg.norm(source_xy[pred] - source_xy[s])),
                "weight": float(source_weight[s] / n_world),
            })

    def weighted(field: str) -> float:
        return float(sum(r["weight"] * float(r[field]) for r in rows))

    weighted_mean_rank = float(
        sum(r["weight"] * r["rank_min"] for r in rows))
    unweighted_top1 = float(np.mean([r["unique_top1"] for r in rows]))
    unweighted_top5 = float(np.mean([r["top5"] for r in rows]))
    unweighted_error = float(np.mean([r["xy_error"] for r in rows]))

    by_world = []
    for w in range(n_world):
        rr = [r for r in rows if r["world"] == w]
        # Re-normalize source measure within one world.
        sw = sum(source_weight)
        by_world.append({
            "world": w,
            "unique_top1_weighted": float(sum(
                source_weight[r["source_index"]] * r["unique_top1"] for r in rr) / sw),
            "top5_weighted": float(sum(
                source_weight[r["source_index"]] * r["top5"] for r in rr) / sw),
            "mean_rank_weighted": float(sum(
                source_weight[r["source_index"]] * r["rank_min"] for r in rr) / sw),
            "mean_xy_error_weighted": float(sum(
                source_weight[r["source_index"]] * r["xy_error"] for r in rr) / sw),
        })

    return {
        "sample_count": len(rows),
        "source_count": n_source,
        "heldout_world_count": n_world,
        "unique_top1_weighted": weighted("unique_top1"),
        "top5_weighted": weighted("top5"),
        "mean_rank_weighted": weighted_mean_rank,
        "mean_xy_error_m_weighted": weighted("xy_error"),
        "unique_top1_unweighted": unweighted_top1,
        "top5_unweighted": unweighted_top5,
        "mean_xy_error_m_unweighted": unweighted_error,
        "minimum_world_top5_weighted": min(x["top5_weighted"] for x in by_world),
        "by_world": by_world,
    }


def shuffled_positive_control(
    train: np.ndarray,
    heldout: np.ndarray,
    source_weight: np.ndarray,
    source_xy: np.ndarray,
    runs: int,
    seed: int,
) -> dict:
    """Destroy same-source-across-world correspondence, preserve each world."""
    rng = np.random.default_rng(seed)
    top1, top5, err = [], [], []
    for _ in range(runs):
        shuffled = np.empty_like(train)
        for w in range(train.shape[0]):
            perm = rng.permutation(train.shape[1])
            shuffled[w] = train[w, perm]
        model = fit_within_source_whitening(shuffled, source_weight)
        metric = evaluate(model, heldout, source_weight, source_xy)
        top1.append(metric["unique_top1_weighted"])
        top5.append(metric["top5_weighted"])
        err.append(metric["mean_xy_error_m_weighted"])

    def summary(x):
        a = np.sort(np.asarray(x, dtype=float))
        return {
            "min": float(a[0]),
            "mean": float(a.mean()),
            "median": float(np.median(a)),
            "max": float(a[-1]),
        }

    return {
        "runs": runs,
        "seed": seed,
        "unique_top1_weighted": summary(top1),
        "top5_weighted": summary(top5),
        "mean_xy_error_m_weighted": summary(err),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", type=Path, required=True)
    ap.add_argument("--bank", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--shuffle-runs", type=int, default=100)
    ap.add_argument("--seed", type=int, default=20260922)
    args = ap.parse_args()

    design, meta, leaves, action_cells, response, measure, xy, source_ids = (
        load_bank(args.design, args.bank)
    )
    feature = hellinger_features(response)
    train = feature[:TRAIN_WORLDS]
    heldout = feature[TRAIN_WORLDS:]

    raw_model = fit_raw(train, measure)
    contrastive_model = fit_within_source_whitening(train, measure)

    raw = evaluate(raw_model, heldout, measure, xy)
    contrastive = evaluate(contrastive_model, heldout, measure, xy)
    shuffle = shuffled_positive_control(
        train, heldout, measure, xy, args.shuffle_runs, args.seed)

    top1_gain = (
        contrastive["unique_top1_weighted"] - raw["unique_top1_weighted"])
    error_reduction = (
        (raw["mean_xy_error_m_weighted"] -
         contrastive["mean_xy_error_m_weighted"]) /
        max(raw["mean_xy_error_m_weighted"], 1e-12)
    )
    shuffle_gap = (
        contrastive["unique_top1_weighted"] -
        shuffle["unique_top1_weighted"]["mean"]
    )

    criteria = {
        # V1 requires independent benefit over raw full-response geometry.
        "top1_gain_at_least_0p05": bool(top1_gain >= 0.05),
        "weighted_xy_error_reduction_at_least_0p10": bool(
            error_reduction >= 0.10),
        # Every held-out transport world must preserve a useful candidate set.
        "minimum_world_top5_at_least_0p90": bool(
            contrastive["minimum_world_top5_weighted"] >= 0.90),
        # Positive grouping must be load-bearing, not incidental preprocessing.
        "source_group_shuffle_top1_gap_at_least_0p20": bool(
            shuffle_gap >= 0.20),
    }
    go = all(criteria.values())

    payload = {
        "contract": "CSL_V1_TRANSPORT_CONTRASTIVE_MANIFOLD_SCREEN",
        "case": design.get("case"),
        "truth_read": False,
        "status": "GO_FOR_NEXT_OFFLINE_STAGE" if go else "NO_GO_STAGE1",
        "design_sha256": sha256(args.design),
        "response_sha256": sha256(args.bank / "responses.f32"),
        "bank_worlds": int(meta["worlds"]),
        "training_worlds": TRAIN_WORLDS,
        "heldout_worlds": HELDOUT_WORLDS,
        "positive_measure_source_count": int(len(leaves)),
        "action_count": int(len(action_cells)),
        "feature_dimension": int(train.shape[-1]),
        "source_measure_sum": float(measure.sum()),
        "representation": {
            "input": "all frozen feasible-action Bernoulli hit probabilities",
            "base_geometry": "per-action Bernoulli Hellinger coordinates",
            "contrastive_proxy":
                "pooled within-source transport-covariance whitening",
            "positive_definition":
                "same candidate source across different design transport worlds",
            "negative_definition":
                "different candidate sources",
            "uses_source_truth": False,
            "uses_heldout_worlds_in_fit": False,
            "uses_neural_network": False,
        },
        "raw_geometry": raw,
        "contrastive_proxy": contrastive,
        "source_label_shuffle_control": shuffle,
        "diagnostics": {
            "top1_gain": top1_gain,
            "weighted_xy_error_reduction_fraction": error_reduction,
            "shuffle_top1_gap": shuffle_gap,
            "within_cov_eigen_floor": contrastive_model["eigen_floor"],
            "within_cov_condition_after_floor":
                contrastive_model["condition_after_floor"],
        },
        "criteria": criteria,
        "go_for_next_offline_stage": go,
        "claim_boundary": [
            "This is a simulator-manifold identity test, not measured-data localization.",
            "It does not authorize ROS or closed-loop testing.",
            "It uses all frozen feasible actions and therefore does not establish an online action budget.",
            "A positive result only justifies testing a learned/linear compatibility embedding on actual frozen observations.",
        ],
        "source_ids_sha256": hashlib.sha256(
            "\n".join(source_ids).encode("utf-8")).hexdigest(),
    }
    dump(args.out, payload)
    print(json.dumps({
        "case": payload["case"],
        "status": payload["status"],
        "raw_top1": raw["unique_top1_weighted"],
        "contrastive_top1": contrastive["unique_top1_weighted"],
        "raw_error_m": raw["mean_xy_error_m_weighted"],
        "contrastive_error_m": contrastive["mean_xy_error_m_weighted"],
        "shuffle_top1_mean": shuffle["unique_top1_weighted"]["mean"],
        "criteria": criteria,
    }, sort_keys=True))


if __name__ == "__main__":
    main()

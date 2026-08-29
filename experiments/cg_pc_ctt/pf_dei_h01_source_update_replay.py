#!/usr/bin/env python3
"""Exact-source-update House01 replay on the frozen existing physical bank.

This is the cheap pre-closed-loop diagnostic that supersedes arbitrary
25/50/75% prefix interpretation.  It evaluates the PF-DEI backend only at the
actual historical PMFS source-update times recorded in source_update_timing.csv.
No GADEN generation and no neural training are performed.

It also fixes the M1 ablation semantics.  FULL compares inverse-canonicalized
physical observation C_obs against physical candidate predictions C_sim.
`pfdei_ablate_sensor` instead compares measured M_obs against T(C_sim), where T
is the same frozen source-independent persistent sensor.  M_obs is never compared
directly with C_sim.

Truth carrier / coordinates, when supplied, are evaluation-only.  They never
enter scoring, prior construction, sensor inversion, or posterior formation.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
from pathlib import Path
import tarfile
import time
from collections import defaultdict

import numpy as np

from pf_dei_modular_core import (
    Mode,
    SensorInverseConfig,
    StreamingSensorInverse,
    infer,
)
from pf_dei_h01_multiseed_replay import (
    ROOT,
    load_observation,
    load_bank,
    rank_lower,
    normalized_rank,
    six_decimal_inverse_negative_bound,
)

MODES = (
    Mode.FULL,
    Mode.ABLATE_SENSOR,
    Mode.ABLATE_NUISANCE,
    Mode.ABLATE_COHERENCE,
    Mode.ABLATE_TEMPORAL,
)


def rank_higher(values: np.ndarray, idx: int) -> int:
    """Tie-safe rank for quantities where larger is better."""
    x = np.asarray(values, dtype=np.float64)
    tol = 1e-12 * (1.0 + abs(float(x[idx])))
    return 1 + int(np.sum(x > x[idx] + tol))


def entropy(probability: np.ndarray) -> float:
    q = np.asarray(probability, dtype=np.float64)
    q = q[q > 0]
    return float(-np.sum(q * np.log(q)))


def forward_sensor_aligned(physical_ppm, cfg: SensorInverseConfig) -> np.ndarray:
    """Apply frozen delayed first-order sensor and return M[delay:delay+T].

    Accepts [...,T] and uses zero sensor pre-history, which is the frozen
    benchmark launch contract.  Output has the same last-axis length T.
    """
    c = np.asarray(physical_ppm, dtype=np.float64)
    if c.ndim < 1 or c.shape[-1] < 1 or np.any(c < 0) or not np.all(np.isfinite(c)):
        raise ValueError("physical_ppm must be finite nonnegative [...,T]")
    if cfg.delay_samples < 1 or cfg.dt <= 0 or cfg.tau <= 0:
        raise ValueError("invalid sensor config")
    alpha = math.exp(-cfg.dt / cfg.tau)
    delay = int(cfg.delay_samples)
    out = np.zeros(c.shape[:-1] + (c.shape[-1] + delay,), dtype=np.float64)
    for k in range(1, out.shape[-1]):
        if k >= delay:
            inp = c[..., k - delay]
        else:
            inp = 0.0
        out[..., k] = alpha * out[..., k - 1] + (1.0 - alpha) * inp
    return out[..., delay:]


def _timing_member(tf: tarfile.TarFile, seed: int) -> str:
    prefix = f"{ROOT}/seed{seed}/off/runtime/"
    hits = [n for n in tf.getnames()
            if n.startswith(prefix) and n.endswith("/context_bank/source_update_timing.csv")]
    if len(hits) != 1:
        raise RuntimeError(f"seed{seed}: expected one source_update_timing.csv, got {len(hits)}")
    return hits[0]


def load_source_updates(tf: tarfile.TarFile, seed: int):
    member = _timing_member(tf, seed)
    f = tf.extractfile(member)
    if f is None:
        raise RuntimeError(f"cannot open {member}")
    rows = list(csv.DictReader(io.StringIO(f.read().decode("utf-8"))))
    if not rows or not {"source_update_id", "sim_time"}.issubset(rows[0]):
        raise ValueError(f"seed{seed}: source-update timing schema mismatch")
    out = [(int(r["source_update_id"]), float(r["sim_time"])) for r in rows]
    if any(out[i][1] <= out[i - 1][1] for i in range(1, len(out))):
        raise ValueError(f"seed{seed}: non-increasing source-update time")
    return out, member


def load_carrier_xy(path: Path | None, house: str = "H01"):
    if path is None:
        return None
    accum = defaultdict(list)
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("house") != house:
                continue
            accum[row["carrier_id"]].append((float(row["pmfs_x"]), float(row["pmfs_y"])))
    if not accum:
        raise ValueError(f"no {house} carrier rows in {path}")
    return {k: np.mean(np.asarray(v, dtype=np.float64), axis=0) for k, v in accum.items()}


def expected_xy(ids: np.ndarray, mass: np.ndarray, carrier_xy) -> tuple[float, float] | None:
    if carrier_xy is None:
        return None
    xy = []
    for sid in ids:
        if str(sid) not in carrier_xy:
            raise ValueError(f"carrier coordinate missing: {sid}")
        xy.append(carrier_xy[str(sid)])
    arr = np.asarray(xy, dtype=np.float64)
    q = np.asarray(mass, dtype=np.float64)
    p = np.sum(arr * q[:, None], axis=0)
    return float(p[0]), float(p[1])


def evaluate_one(obs, pred, q0, ids, true_idx, reference_ppm, mode):
    r = infer(obs, pred, q0, reference_ppm, mode=mode)
    raw_rank = rank_lower(r.scores, true_idx)
    posterior_rank = rank_higher(r.posterior, true_idx)
    prior_rank = rank_higher(q0 / np.sum(q0), true_idx)
    rivals = np.delete(r.scores, true_idx)
    margin = float(np.min(rivals) - r.scores[true_idx])
    return r, {
        "raw_score_true_rank": int(raw_rank),
        "raw_score_normalized_rank": normalized_rank(raw_rank, len(ids)),
        "raw_top1": bool(raw_rank <= 1),
        "raw_top5": bool(raw_rank <= 5),
        "raw_top10": bool(raw_rank <= 10),
        "raw_true_vs_best_rival_margin": margin,
        "prior_true_rank": int(prior_rank),
        "posterior_true_rank": int(posterior_rank),
        "posterior_normalized_rank": normalized_rank(posterior_rank, len(ids)),
        "posterior_truth_mass": float(r.posterior[true_idx]),
        "posterior_entropy": entropy(r.posterior),
        "posterior_max_mass": float(np.max(r.posterior)),
        "selected_source_id": str(ids[r.selected_source]),
        "a0_rank_shift_posterior_minus_raw": int(posterior_rank - raw_rank),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", type=Path, required=True,
                    help="CG_PC_CTT_V3_ORR_FULL60_PACKAGE_20260827.tar.gz")
    ap.add_argument("--bank-dir", type=Path, required=True,
                    help="directory containing H01_seed{0..9}_candidate_physical.npz")
    ap.add_argument("--truth-carrier-id", default="quadtree_22_16_2_2")
    ap.add_argument("--reference-ppm", type=float, default=0.1)
    ap.add_argument("--seeds", default="0,1,2,3,4,5,6,7,8,9")
    ap.add_argument("--support-manifest", type=Path, default=None)
    ap.add_argument("--truth-x", type=float, default=None)
    ap.add_argument("--truth-y", type=float, default=None)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    if (args.truth_x is None) != (args.truth_y is None):
        raise ValueError("truth-x and truth-y must be supplied together")
    seeds = [int(x) for x in args.seeds.split(",") if x.strip()]
    if not seeds:
        raise ValueError("empty seed list")

    replay_tol = six_decimal_inverse_negative_bound()
    sensor_cfg = SensorInverseConfig(serialization_bound_ppm=replay_tol + 1e-12)
    inverse = StreamingSensorInverse(sensor_cfg)
    carrier_xy = load_carrier_xy(args.support_manifest)

    cases = []
    t0 = time.perf_counter()
    with tarfile.open(args.archive, "r:gz") as tf:
        for seed in seeds:
            t, measured, _true_eval_unused, sensor_member = load_observation(tf, seed)
            updates, timing_member = load_source_updates(tf, seed)
            pred_all, ids, q0, bt = load_bank(args.bank_dir / f"H01_seed{seed}_candidate_physical.npz")
            q0 = q0 / np.sum(q0)
            hit = np.flatnonzero(ids == args.truth_carrier_id)
            if len(hit) != 1:
                raise ValueError(f"seed{seed}: truth carrier occurs {len(hit)} times")
            true_idx = int(hit[0])

            expected_full_t = t[:-sensor_cfg.delay_samples]
            if pred_all.shape[2] != len(expected_full_t):
                raise ValueError(f"seed{seed}: bank/sensor aligned length mismatch")
            if bt is not None and (len(bt) != len(expected_full_t) or
                                   np.max(np.abs(bt - expected_full_t)) > 1e-9):
                raise ValueError(f"seed{seed}: bank time alignment mismatch")

            for update_id, update_time in updates:
                # Causal prefix: only sensor samples whose timestamp is <= the
                # actual PMFS source-update sim_time are visible.
                n_measured = int(np.searchsorted(t, update_time + 1e-12, side="right"))
                if n_measured <= sensor_cfg.delay_samples + 2:
                    raise ValueError(f"seed{seed} update{update_id}: insufficient prefix")
                measured_prefix = measured[:n_measured]
                physical_obs = inverse.deconvolve(measured_prefix)
                n_phys = len(physical_obs)
                pred_c = pred_all[:, :, :n_phys]

                for mode in MODES:
                    if mode == Mode.ABLATE_SENSOR:
                        # Clean M1 removal: same measured domain on both sides.
                        obs = measured_prefix[sensor_cfg.delay_samples:]
                        pred = forward_sensor_aligned(pred_c, sensor_cfg)
                        score_mode = Mode.FULL  # M2/M3/M4 unchanged; only domain differs.
                    else:
                        obs = physical_obs
                        pred = pred_c
                        score_mode = mode

                    r, metrics = evaluate_one(
                        obs, pred, q0, ids, true_idx, args.reference_ppm, score_mode)
                    post_xy = expected_xy(ids, r.posterior, carrier_xy)
                    prior_xy = expected_xy(ids, q0, carrier_xy)
                    metrics.update({
                        "seed": int(seed),
                        "source_update_id": int(update_id),
                        "source_update_sim_time_s": float(update_time),
                        "last_visible_sensor_time_s": float(t[n_measured - 1]),
                        "measured_samples": int(n_measured),
                        "aligned_samples": int(len(obs)),
                        "mode": mode.value,
                        "true_carrier_id_eval_only": args.truth_carrier_id,
                        "sensor_trace_member": sensor_member,
                        "source_update_timing_member": timing_member,
                    })
                    if post_xy is not None:
                        metrics["posterior_expected_x"] = post_xy[0]
                        metrics["posterior_expected_y"] = post_xy[1]
                        metrics["prior_expected_x"] = prior_xy[0]
                        metrics["prior_expected_y"] = prior_xy[1]
                        if args.truth_x is not None:
                            metrics["posterior_expected_error_m_eval_only"] = float(
                                math.hypot(post_xy[0] - args.truth_x, post_xy[1] - args.truth_y))
                            metrics["prior_expected_error_m_eval_only"] = float(
                                math.hypot(prior_xy[0] - args.truth_x, prior_xy[1] - args.truth_y))
                    cases.append(metrics)

    aggregate = {}
    for mode in MODES:
        rows = [r for r in cases if r["mode"] == mode.value]
        raw = np.asarray([r["raw_score_true_rank"] for r in rows], dtype=np.int64)
        post = np.asarray([r["posterior_true_rank"] for r in rows], dtype=np.int64)
        aggregate[mode.value] = {
            "cases": int(len(rows)),
            "raw_top1": int(np.sum(raw <= 1)),
            "raw_top5": int(np.sum(raw <= 5)),
            "raw_top10": int(np.sum(raw <= 10)),
            "raw_median_rank": float(np.median(raw)),
            "posterior_top5": int(np.sum(post <= 5)),
            "posterior_median_rank": float(np.median(post)),
            "a0_worsened_rank_cases": int(sum(r["a0_rank_shift_posterior_minus_raw"] > 0 for r in rows)),
            "a0_improved_rank_cases": int(sum(r["a0_rank_shift_posterior_minus_raw"] < 0 for r in rows)),
            "a0_tied_rank_cases": int(sum(r["a0_rank_shift_posterior_minus_raw"] == 0 for r in rows)),
        }
        err_key = "posterior_expected_error_m_eval_only"
        if rows and err_key in rows[0]:
            aggregate[mode.value]["mean_posterior_expected_error_m_eval_only"] = float(
                np.mean([r[err_key] for r in rows]))

    by_update = {}
    for update_id in sorted({r["source_update_id"] for r in cases}):
        by_update[str(update_id)] = {}
        for mode in MODES:
            rows = [r for r in cases if r["source_update_id"] == update_id and r["mode"] == mode.value]
            ranks = np.asarray([r["raw_score_true_rank"] for r in rows], dtype=np.int64)
            pranks = np.asarray([r["posterior_true_rank"] for r in rows], dtype=np.int64)
            by_update[str(update_id)][mode.value] = {
                "seeds": int(len(rows)),
                "raw_top5": int(np.sum(ranks <= 5)),
                "raw_median_rank": float(np.median(ranks)),
                "posterior_top5": int(np.sum(pranks <= 5)),
                "posterior_median_rank": float(np.median(pranks)),
            }

    out = {
        "contract": "PF_DEI_H01_ACTUAL_SOURCE_UPDATE_REPLAY_V2",
        "new_gaden_runs": 0,
        "neural_training": False,
        "inference_uses_true_gas": False,
        "inference_uses_localization_error": False,
        "sensor_ablation_semantics": "M_obs_vs_forward_sensor(C_sim)",
        "reference_ppm": float(args.reference_ppm),
        "serialized_csv_inverse_negative_bound_ppm": float(replay_tol),
        "aggregate": aggregate,
        "by_source_update": by_update,
        "cases": cases,
        "total_wall_s": float(time.perf_counter() - t0),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({"aggregate": aggregate, "by_source_update": by_update}, indent=2))
    print(f"TOTAL_WALL_S={out['total_wall_s']:.3f}")


if __name__ == "__main__":
    main()

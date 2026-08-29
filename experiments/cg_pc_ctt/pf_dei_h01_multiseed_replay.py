#!/usr/bin/env python3
"""Efficient House01 seed0..9 PF-DEI replay on frozen historical OFF trajectories.

This script is deliberately *not* a simulator.  It reuses archived raw measured
sensor traces and consumes one already-materialized candidate physical-ppm bank
per seed.  It therefore provides a cheap fixed-trajectory screen of the frozen
FULL backend and all one-module removals before any new closed-loop run.

Scientific separation:
  - measured_gas_ppm is the only observation used by inference;
  - true_gas_ppm is optional evaluation-only sensor-inverse parity;
  - source truth is used only after scoring to report candidate rank;
  - no localization error is used to fit a parameter;
  - no GADEN generation or neural training is performed here.

Expected bank layout, one NPZ per seed:
  H01_seed0_candidate_physical.npz ... H01_seed9_candidate_physical.npz
with arrays:
  candidate_physical_ppm [S,M,Tphys]  # already aligned to recovered C_0:T-3
  source_id              [S]          # stable carrier IDs
  geometry_prior         [S]
optional:
  sample_time_s          [Tphys]

The bank must use the frozen predictive/train nuisance members.  Reserved
members are qualification observations only and must never enter this ensemble.
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
from typing import Iterable

import numpy as np

from pf_dei_modular_core import Mode, SensorInverseConfig, StreamingSensorInverse, infer

ROOT = "CG_PC_CTT_V3_ORR_FULL60_PACKAGE_20260827/results/House01"
MODES = (
    Mode.FULL,
    Mode.ABLATE_SENSOR,
    Mode.ABLATE_NUISANCE,
    Mode.ABLATE_COHERENCE,
    Mode.ABLATE_TEMPORAL,
)


def six_decimal_inverse_negative_bound(dt: float = 0.2, tau: float = 1.2) -> float:
    """Worst-case inverse negativity from rounding each measured value to 1e-6 ppm."""
    a = math.exp(-dt / tau)
    return 0.5e-6 * (1.0 + a) / (1.0 - a)


def _sensor_member(tf: tarfile.TarFile, seed: int) -> str:
    prefix = f"{ROOT}/seed{seed}/off/runtime/"
    hits = [n for n in tf.getnames() if n.startswith(prefix) and n.endswith("/sensor_trace.csv")]
    if len(hits) != 1:
        raise RuntimeError(f"seed{seed}: expected one OFF sensor_trace.csv, got {len(hits)}")
    return hits[0]


def load_observation(tf: tarfile.TarFile, seed: int):
    member = _sensor_member(tf, seed)
    raw = tf.extractfile(member)
    if raw is None:
        raise RuntimeError(f"cannot open {member}")
    rows = list(csv.DictReader(io.StringIO(raw.read().decode("utf-8"))))
    required = {"t_sim_s", "measured_gas_ppm", "true_gas_ppm"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"seed{seed}: sensor trace schema mismatch")
    t = np.asarray([float(r["t_sim_s"]) for r in rows], dtype=np.float64)
    measured = np.asarray([float(r["measured_gas_ppm"]) for r in rows], dtype=np.float64)
    truth_eval = np.asarray([float(r["true_gas_ppm"]) for r in rows], dtype=np.float64)
    if np.any(np.diff(t) <= 0):
        raise ValueError(f"seed{seed}: non-increasing sensor timestamps")
    return t, measured, truth_eval, member


def load_bank(path: Path):
    with np.load(path, allow_pickle=False) as d:
        for k in ("candidate_physical_ppm", "source_id", "geometry_prior"):
            if k not in d:
                raise ValueError(f"{path}: missing {k}")
        x = np.asarray(d["candidate_physical_ppm"], dtype=np.float64)
        ids = np.asarray(d["source_id"]).astype(str)
        q0 = np.asarray(d["geometry_prior"], dtype=np.float64)
        bt = np.asarray(d["sample_time_s"], dtype=np.float64) if "sample_time_s" in d else None
    if x.ndim != 3 or x.shape[0] != len(ids) or len(q0) != len(ids):
        raise ValueError(f"{path}: invalid candidate bank shape")
    return x, ids, q0, bt


def rank_lower(scores: np.ndarray, idx: int) -> int:
    # tie-safe pessimistic rank: 1 + number strictly better than the true source
    x = np.asarray(scores, dtype=np.float64)
    return 1 + int(np.sum(x < x[idx] - 1e-12 * (1.0 + abs(float(x[idx])))))


def normalized_rank(rank: int, n: int) -> float:
    return 0.0 if n <= 1 else float(rank - 1) / float(n - 1)


def evaluate_prefixes(observed, predicted, q0, true_idx, reference_ppm, mode, fractions):
    rows = []
    T = len(observed)
    for f in fractions:
        n = max(3, min(T, int(round(T * f))))
        r = infer(observed[:n], predicted[:, :, :n], q0, reference_ppm, mode=mode)
        rank = rank_lower(r.scores, true_idx)
        rows.append({
            "fraction": float(f),
            "samples": int(n),
            "rank": int(rank),
            "normalized_rank": normalized_rank(rank, len(q0)),
            "top1": bool(rank <= 1),
            "top5": bool(rank <= 5),
            "top10": bool(rank <= 10),
            "selected_source": str(int(r.selected_source)),
        })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", type=Path, required=True,
                    help="CG_PC_CTT_V3_ORR_FULL60_PACKAGE_20260827.tar.gz")
    ap.add_argument("--bank-dir", type=Path, required=True)
    ap.add_argument("--truth-carrier-id", default="quadtree_22_16_2_2")
    ap.add_argument("--reference-ppm", type=float, default=0.1)
    ap.add_argument("--seeds", default="0,1,2,3,4,5,6,7,8,9")
    ap.add_argument("--prefix-fractions", default="0.25,0.50,0.75,1.0")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    seeds = [int(x) for x in args.seeds.split(",") if x.strip()]
    fractions = [float(x) for x in args.prefix_fractions.split(",") if x.strip()]
    if not seeds or not fractions or any(not (0 < x <= 1) for x in fractions):
        raise ValueError("invalid seed/prefix contract")

    replay_tol = six_decimal_inverse_negative_bound()
    inverse = StreamingSensorInverse(SensorInverseConfig(serialization_bound_ppm=replay_tol + 1e-12))
    per_seed = []
    t0 = time.perf_counter()

    with tarfile.open(args.archive, "r:gz") as tf:
        for seed in seeds:
            st = time.perf_counter()
            t, measured, true_eval, member = load_observation(tf, seed)
            physical = inverse.deconvolve(measured)
            # Evaluation only: M[i] inverse aligns to C[i-2], so physical == true[:-2].
            if len(true_eval) != len(measured) or len(physical) != len(true_eval) - 2:
                raise RuntimeError(f"seed{seed}: inverse alignment mismatch")
            inverse_err = physical - true_eval[:-2]

            bank_path = args.bank_dir / f"H01_seed{seed}_candidate_physical.npz"
            pred, ids, q0, bt = load_bank(bank_path)
            if pred.shape[2] != len(physical):
                raise ValueError(
                    f"seed{seed}: bank T={pred.shape[2]} but recovered observation T={len(physical)}; "
                    "materializer must output the same physical-time alignment, do not crop by outcome")
            if bt is not None:
                expected_t = t[:-2]
                if len(bt) != len(expected_t) or np.max(np.abs(bt - expected_t)) > 1e-9:
                    raise ValueError(f"seed{seed}: physical-bank time alignment mismatch")
            hit = np.flatnonzero(ids == args.truth_carrier_id)
            if len(hit) != 1:
                raise ValueError(f"seed{seed}: truth carrier {args.truth_carrier_id} occurs {len(hit)} times")
            true_idx = int(hit[0])

            modes = {}
            for mode in MODES:
                # Sensor ablation is the sole special case: compare measured prefix against
                # physical predictions without M->C canonicalization.  Align by dropping the
                # final two measured samples so all arms use exactly the same T and context.
                obs = measured[:-2] if mode == Mode.ABLATE_SENSOR else physical
                r = infer(obs, pred, q0, args.reference_ppm, mode=Mode.FULL if mode == Mode.ABLATE_SENSOR else mode)
                rank = rank_lower(r.scores, true_idx)
                modes[mode.value] = {
                    "rank": int(rank),
                    "normalized_rank": normalized_rank(rank, len(ids)),
                    "top1": bool(rank <= 1),
                    "top5": bool(rank <= 5),
                    "top10": bool(rank <= 10),
                    "selected_source_id": str(ids[r.selected_source]),
                    "prefix": evaluate_prefixes(obs, pred, q0, true_idx, args.reference_ppm,
                                                Mode.FULL if mode == Mode.ABLATE_SENSOR else mode,
                                                fractions),
                }

            per_seed.append({
                "seed": seed,
                "sensor_trace_member": member,
                "samples_measured": int(len(measured)),
                "samples_physical": int(len(physical)),
                "sensor_inverse_max_abs_error_ppm_eval_only": float(np.max(np.abs(inverse_err))),
                "sensor_inverse_rmse_ppm_eval_only": float(np.sqrt(np.mean(inverse_err ** 2))),
                "bank_sources": int(pred.shape[0]),
                "bank_members": int(pred.shape[1]),
                "truth_carrier_id_eval_only": args.truth_carrier_id,
                "modes": modes,
                "wall_s": float(time.perf_counter() - st),
            })

    summary = {}
    for mode in MODES:
        rs = [r["modes"][mode.value]["rank"] for r in per_seed]
        summary[mode.value] = {
            "seeds": len(rs),
            "top1": int(sum(x <= 1 for x in rs)),
            "top5": int(sum(x <= 5 for x in rs)),
            "top10": int(sum(x <= 10 for x in rs)),
            "median_rank": float(np.median(rs)),
            "median_normalized_rank": float(np.median([(x - 1) / max(per_seed[i]["bank_sources"] - 1, 1)
                                                         for i, x in enumerate(rs)])),
        }

    out = {
        "contract": "PF_DEI_H01_MULTI_SEED_FIXED_TRAJECTORY_REPLAY_V1",
        "inference_uses_true_gas": False,
        "inference_uses_localization_error": False,
        "new_gaden_runs": 0,
        "neural_training": False,
        "reference_ppm": args.reference_ppm,
        "serialized_csv_inverse_negative_bound_ppm": replay_tol,
        "summary": summary,
        "per_seed": per_seed,
        "total_wall_s": float(time.perf_counter() - t0),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"TOTAL_WALL_S={out['total_wall_s']:.3f}")


if __name__ == "__main__":
    main()

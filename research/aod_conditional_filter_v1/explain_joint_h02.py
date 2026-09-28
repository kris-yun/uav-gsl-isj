#!/usr/bin/env python3
"""Post-screen diagnostic of H02 odds; never used for parameter selection."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from scipy.linalg import cholesky, solve_triangular
from scipy.special import log_ndtr, logsumexp

OLD = Path(__file__).resolve().parents[1] / "aod_conditional_filter_v0"
sys.path.insert(0, str(OLD))
from bank import TemplateBank  # noqa: E402
from episode_io import predicted_event_means  # noqa: E402


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def split_terms(t, y, m, cfg):
    g0, vg = cfg["gain_mean"], cfg["gain_variance"]
    K = cfg["discrepancy_variance"] * np.exp(-np.abs(t[:, None] - t[None, :]) /
                                                cfg["correlation_time_s"])
    K.flat[::len(y) + 1] += cfg["measurement_variance"]
    L = cholesky(K, lower=True, check_finite=False)
    wy = solve_triangular(L, y, lower=True, check_finite=False)
    wm = solve_triangular(L, m, lower=True, check_finite=False)
    A = np.sum(wm * wm, axis=0)
    B = wm.T @ wy
    yy = wy @ wy
    vp = 1 / (1 / vg + A)
    gp = vp * (g0 / vg + B)
    active = A > 0
    free = np.zeros(m.shape[1])
    free[active] = B[active] / A[active]
    shape = np.full(m.shape[1], -.5 * yy)
    shape[active] = -.5 * (yy - B[active] ** 2 / A[active])
    penalty = np.zeros(m.shape[1])
    penalty[active] = -.5 * (free[active] - g0) ** 2 / (vg + 1 / A[active])
    determinant = -.5 * np.log1p(vg * A)
    truncation = log_ndtr(gp / np.sqrt(vp)) - log_ndtr(g0 / np.sqrt(vg))
    total = shape + penalty + determinant + truncation
    return {"shape": shape, "gain_prior": penalty, "determinant": determinant,
            "positive_gain_truncation": truncation, "total": total,
            "unconstrained_gls_gain": free, "posterior": np.exp(total - logsumexp(total))}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--raw", type=Path, required=True)
    p.add_argument("--bank", type=Path, required=True)
    p.add_argument("--calibration", type=Path, required=True)
    p.add_argument("--dev-screen", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    screen = json.loads(args.dev_screen.read_text(encoding="utf-8"))
    if screen["status"] != "AOD_V1_DEV_SCREEN_FAIL_STOP_BEFORE_PLANNER":
        raise RuntimeError("H02 explanation must follow the fixed dev screen")
    freeze = json.loads(Path(__file__).with_name("PREFIT_CONTRACT_20260928.json").read_text(encoding="utf-8"))
    if sha(args.bank) != freeze["bank_sha256"]["2"]:
        raise RuntimeError("H02 bank mismatch")
    bank = TemplateBank.load(args.bank)
    required = ("sim_pose_trace.csv", "sensor_trace.csv", "measurement_blocks.csv", "measurement_samples.csv")
    data = {}
    for name in required:
        with (args.raw / name).open(newline="", encoding="utf-8") as f:
            data[name] = list(csv.DictReader(f))
    events = predicted_event_means(bank, data)
    t = np.array([e[0] for e in events]);y = np.array([e[1] for e in events]);m = np.stack([e[2] for e in events])
    true_id, wrong_id = "pmfs_2_37", "pmfs_6_36"
    truth, wrong = bank.ids.index(true_id), bank.ids.index(wrong_id)
    old = json.loads((OLD / "TRAIN_ONLY_CALIBRATION.json").read_text(encoding="utf-8"))
    new = json.loads(args.calibration.read_text(encoding="utf-8"))
    result = {"status": "AOD_V1_H02_POSTSCREEN_EXPLANATION_ONLY", "events": len(y),
              "truth_source_id": true_id, "historical_wrong_source_id": wrong_id,
              "raw_file_sha256": {name: sha(args.raw / name) for name in required},
              "bank_sha256": sha(args.bank), "calibration_sha256": sha(args.calibration),
              "dev_screen_sha256": sha(args.dev_screen), "models": {}}
    for label, cfg in (("old", old), ("new", new)):
        v = split_terms(t, y, m, cfg)
        components = {k: float(v[k][wrong] - v[k][truth]) for k in
                      ("shape", "gain_prior", "determinant", "positive_gain_truncation", "total")}
        assert abs(components["total"] - sum(components[k] for k in
                   ("shape", "gain_prior", "determinant", "positive_gain_truncation"))) < 1e-8
        truth_rank = 1 + int(np.sum(v["total"] > v["total"][truth]))
        result["models"][label] = {
            "wrong_over_truth_log_odds": components,
            "wrong_over_truth_odds": float(np.exp(components["total"])),
            "true_source_posterior": float(v["posterior"][truth]),
            "historical_wrong_source_posterior": float(v["posterior"][wrong]),
            "true_source_rank": truth_rank,
            "unconstrained_gls_gains": {true_id: float(v["unconstrained_gls_gain"][truth]),
                                        wrong_id: float(v["unconstrained_gls_gain"][wrong])}}
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result["models"], indent=2), flush=True)


if __name__ == "__main__":
    main()

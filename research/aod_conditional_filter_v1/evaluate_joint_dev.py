#!/usr/bin/env python3
"""One-shot frozen eight-case dev comparison before any planner work."""

from __future__ import annotations

import argparse
import glob
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
from episode_io import predicted_event_means, read_archive  # noqa: E402
from gain_innovation_bank import GainInnovationBank  # noqa: E402


def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def final_evidence(t, y, m, cfg):
    vd, tc, R = (cfg["discrepancy_variance"], cfg["correlation_time_s"],
                 cfg["measurement_variance"])
    g0, vg = cfg["gain_mean"], cfg["gain_variance"]
    K = vd * np.exp(-np.abs(t[:, None] - t[None, :]) / tc)
    K.flat[::len(y) + 1] += R
    L = cholesky(K, lower=True, check_finite=False)
    wy = solve_triangular(L, y, lower=True, check_finite=False)
    wm = solve_triangular(L, m, lower=True, check_finite=False)
    A = np.sum(wm * wm, axis=0)
    B = wm.T @ wy
    yy = wy @ wy
    vp = 1. / (1. / vg + A)
    gp = vp * (g0 / vg + B)
    common = -.5 * (len(y) * np.log(2 * np.pi) + 2 * np.log(np.diag(L)).sum())
    logev = common - .5 * (yy + g0 * g0 / vg) + .5 * (gp * gp / vp + np.log(vp / vg))
    logev += log_ndtr(gp / np.sqrt(vp)) - log_ndtr(g0 / np.sqrt(vg))
    return logev


def innovation_stats(t, y, m, cfg):
    model = GainInnovationBank(np.ones(1),
                               gain_mean=cfg["gain_mean"], gain_variance=cfg["gain_variance"],
                               discrepancy_variance=cfg["discrepancy_variance"],
                               correlation_time_s=cfg["correlation_time_s"],
                               measurement_variance=cfg["measurement_variance"],
                               positive_gain=True)
    last = 0.;z=[]
    for k in range(len(t)):
        update = model.update(k, t[k] - last, y[k], np.asarray([m[k]]))
        z.append((y[k] - update.gaussian_envelope_prediction[0]) /
                 np.sqrt(update.gaussian_envelope_innovation_variance[0]))
        last = t[k]
    z = np.asarray(z)
    return {"standardized_innovation_rms": float(np.sqrt(np.mean(z * z))),
            "standardized_innovation_lag1": float(np.corrcoef(z[:-1], z[1:])[0, 1]),
            "standardized_innovation_max_abs": float(np.max(np.abs(z)))}


def main():
    p = argparse.ArgumentParser()
    for name in ("cases", "archives", "bank-dir", "calibration", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--zstd", required=True)
    args = p.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    freeze_file = Path(__file__).with_name("PREFIT_CONTRACT_20260928.json")
    freeze = json.loads(freeze_file.read_text(encoding="utf-8"))
    new = json.loads(args.calibration.read_text(encoding="utf-8"))
    assert new["freeze_sha256"] == sha(freeze_file)
    old = json.loads((OLD / "TRAIN_ONLY_CALIBRATION.json").read_text(encoding="utf-8"))
    banks = {}; rows = []
    for case_file in sorted(args.cases.glob("*.json")):
        case = json.loads(case_file.read_text(encoding="utf-8"))
        if case["split"] != "dev":
            continue
        env = int(case["environment_index"])
        if env not in banks:
            bank_file = args.bank_dir / f"env_{env}_bank.npz"
            assert sha(bank_file) == freeze["bank_sha256"][str(env)]
            banks[env] = TemplateBank.load(bank_file)
        bank = banks[env]
        truth = bank.ids.index(case["source_id"])
        matches = glob.glob(str(args.archives / f'native_{case["ordinal"]:03d}_{case["case_id"]}.tar.zst'))
        if len(matches) != 1:
            raise RuntimeError(f"Missing frozen dev archive {case['case_id']}")
        archive = Path(matches[0])
        events = predicted_event_means(bank, read_archive(archive, args.zstd))
        t = np.asarray([e[0] for e in events]); y = np.asarray([e[1] for e in events])
        m = np.stack([e[2] for e in events])
        row = {"case_id": case["case_id"], "truth_source_id": case["source_id"],
               "archive_sha256": sha(archive), "events": len(y), "zero_events": int((y == 0).sum()),
               "uniform_support_nll": float(np.log(len(bank.ids)))}
        for label, cfg in (("old", old), ("new", new)):
            logev = final_evidence(t, y, m, cfg)
            logq = logev - logsumexp(logev)
            q = np.exp(logq)
            rank = 1 + int(np.sum(logq > logq[truth]))
            keep = max(1, int(np.ceil(.05 * len(q))))
            top = np.argsort(-q, kind="stable")[:keep]
            estimate = np.average(bank.xy[top], axis=0, weights=q[top])
            row[label] = {"truth_rank": rank, "true_source_posterior_nll": float(-logq[truth]),
                          "truth_predictive_log_density_per_event": float(logev[truth] / len(y)),
                          "source_error_m": float(np.linalg.norm(estimate - np.asarray(case["truth_xy"]))),
                          "estimate_xy": estimate.tolist(),
                          **innovation_stats(t, y, m[:, truth], cfg)}
        rows.append(row)
        print(f"dev {len(rows)}/8 old/new ranks {row['old']['truth_rank']}/{row['new']['truth_rank']}", flush=True)
    if len(rows) != 8:
        raise RuntimeError("Frozen 8-dev contract not met")
    mean = lambda key, field: float(np.mean([r[key][field] for r in rows]))
    old_nll = mean("old", "true_source_posterior_nll")
    new_nll = mean("new", "true_source_posterior_nll")
    uniform_nll = float(np.mean([r["uniform_support_nll"] for r in rows]))
    old_rank = mean("old", "truth_rank")
    new_rank = mean("new", "truth_rank")
    passes = new_nll < old_nll and new_nll < uniform_nll and new_rank < old_rank
    output = {"status": "AOD_V1_DEV_SCREEN_PASS_PLANNER_ALLOWED" if passes else "AOD_V1_DEV_SCREEN_FAIL_STOP_BEFORE_PLANNER",
              "freeze_sha256": sha(freeze_file), "calibration_sha256": sha(args.calibration),
              "mean_old_nll": old_nll, "mean_new_nll": new_nll, "mean_uniform_nll": uniform_nll,
              "mean_old_truth_rank": old_rank, "mean_new_truth_rank": new_rank,
              "mean_old_truth_predictive_log_density_per_event": mean("old", "truth_predictive_log_density_per_event"),
              "mean_new_truth_predictive_log_density_per_event": mean("new", "truth_predictive_log_density_per_event"),
              "boundary_flags": new["boundary_flags"], "cases": rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in output.items() if k != "cases"}, indent=2), flush=True)


if __name__ == "__main__":
    main()

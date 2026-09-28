#!/usr/bin/env python3
"""Fit the frozen two-state AOD likelihood using 40 original train episodes."""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from scipy.linalg import cholesky, solve_triangular
from scipy.optimize import minimize
from scipy.special import log_ndtr

OLD = Path(__file__).resolve().parents[1] / "aod_conditional_filter_v0"
sys.path.insert(0, str(OLD))
from bank import TemplateBank  # noqa: E402
from episode_io import predicted_event_means, read_archive  # noqa: E402


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def episode_log_evidence(y: np.ndarray, m: np.ndarray, abs_dt: np.ndarray,
                         g0: float, vg: float, vd: float, tc: float, R: float) -> float:
    K = vd * np.exp(-abs_dt / tc)
    K.flat[:: len(y) + 1] += R
    L = cholesky(K, lower=True, check_finite=False)
    wy = solve_triangular(L, y, lower=True, check_finite=False)
    wm = solve_triangular(L, m, lower=True, check_finite=False)
    A = float(wm @ wm)
    B = float(wm @ wy)
    yy = float(wy @ wy)
    vp = 1.0 / (1.0 / vg + A)
    gp = vp * (g0 / vg + B)
    common = -0.5 * (len(y) * np.log(2 * np.pi) + 2.0 * np.log(np.diag(L)).sum())
    return float(common - 0.5 * (yy + g0 * g0 / vg)
                 + 0.5 * (gp * gp / vp + np.log(vp / vg))
                 + log_ndtr(gp / np.sqrt(vp)) - log_ndtr(g0 / np.sqrt(vg)))


def load_train(cases: Path, archives: Path, bank_dir: Path, zstd: str, freeze: dict):
    banks = {}
    episodes = []
    for case_file in sorted(cases.glob("*.json")):
        case = json.loads(case_file.read_text(encoding="utf-8"))
        if case["split"] != "train":
            continue
        env = int(case["environment_index"])
        if env not in banks:
            bank_file = bank_dir / f"env_{env}_bank.npz"
            assert file_sha(bank_file) == freeze["bank_sha256"][str(env)]
            banks[env] = TemplateBank.load(bank_file)
        bank = banks[env]
        source_id = case["source_id"]
        if source_id not in bank.ids:
            raise RuntimeError(f"Train source outside legal support: {source_id}")
        i = bank.ids.index(source_id)
        import copy
        single = copy.copy(bank)
        single.ids = (source_id,)
        single.p = bank.p[i:i + 1]
        single.u = bank.u[i:i + 1]
        matches = glob.glob(str(archives / f'native_{case["ordinal"]:03d}_{case["case_id"]}.tar.zst'))
        if len(matches) != 1:
            raise RuntimeError(f"Missing/duplicate original archive for {case['case_id']}")
        archive = Path(matches[0])
        rows = predicted_event_means(single, read_archive(archive, zstd))
        t = np.asarray([r[0] for r in rows], float)
        y = np.asarray([r[1] for r in rows], float)
        m = np.asarray([r[2][0] for r in rows], float)
        if len(t) < 2 or not np.isfinite(t).all() or not np.all(np.diff(t) > 0):
            raise RuntimeError(f"Invalid physical event times: {case['case_id']}")
        episodes.append({"case_id": case["case_id"], "environment_index": env,
                         "source_id": source_id, "t": t, "y": y, "m": m,
                         "abs_dt": np.abs(t[:, None] - t[None, :]),
                         "archive_sha256": file_sha(archive)})
        print(f"train {len(episodes):02d}/40 env={env} events={len(t)}", flush=True)
    if len(episodes) != 40 or sorted(set(e["environment_index"] for e in episodes)) != [0, 1, 2]:
        raise RuntimeError("Frozen 40-train/three-environment contract not met")
    return episodes


def score(parameter_vector: np.ndarray, episodes) -> float:
    g0, gsd, dsd, tc, rsd = np.exp(parameter_vector)
    scores = {0: [], 1: [], 2: []}
    try:
        for e in episodes:
            logev = episode_log_evidence(e["y"], e["m"], e["abs_dt"],
                                         g0, gsd * gsd, dsd * dsd, tc, rsd * rsd)
            scores[e["environment_index"]].append(logev / len(e["y"]))
    except (ValueError, FloatingPointError, np.linalg.LinAlgError):
        return float("inf")
    return -float(np.mean([np.mean(scores[env]) for env in (0, 1, 2)]))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cases", type=Path, required=True)
    p.add_argument("--archives", type=Path, required=True)
    p.add_argument("--bank-dir", type=Path, required=True)
    p.add_argument("--zstd", required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    freeze_file = Path(__file__).with_name("PREFIT_CONTRACT_20260928.json")
    freeze = json.loads(freeze_file.read_text(encoding="utf-8"))
    episodes = load_train(args.cases, args.archives, args.bank_dir, args.zstd, freeze)
    names = tuple(freeze["parameters_and_bounds"])
    bounds = np.log(np.asarray([freeze["parameters_and_bounds"][n] for n in names], float))
    starts = np.asarray(freeze["optimizer"]["fixed_starts"], float)
    if starts.shape != (4, 5):
        raise RuntimeError("Fixed optimizer starts changed")
    old = json.loads((OLD / "TRAIN_ONLY_CALIBRATION.json").read_text(encoding="utf-8"))
    old_vector = np.log(np.asarray([old["gain_mean"], np.sqrt(old["gain_variance"]),
                                    np.sqrt(old["discrepancy_variance"]),
                                    old["correlation_time_s"], np.sqrt(old["measurement_variance"])], float))
    old_objective = score(old_vector, episodes)
    runs = []
    for index, start in enumerate(starts):
        result = minimize(score, np.log(start), args=(episodes,), method="L-BFGS-B",
                          bounds=[tuple(v) for v in bounds],
                          options={"maxiter": freeze["optimizer"]["maxiter_per_start"],
                                   "ftol": freeze["optimizer"]["ftol"]})
        runs.append({"start_index": index, "start": start.tolist(),
                     "parameters": np.exp(result.x).tolist(), "objective": float(result.fun),
                     "success": bool(result.success), "message": str(result.message),
                     "iterations": int(result.nit), "evaluations": int(result.nfev)})
        print(json.dumps(runs[-1]), flush=True)
    usable = [run for run in runs if np.isfinite(run["objective"])]
    if not usable:
        raise RuntimeError("All four frozen starts failed")
    best = min(usable, key=lambda run: (run["objective"], run["start_index"]))
    g0, gsd, dsd, tc, rsd = best["parameters"]
    output = {
        "status": "AOD_V1_TRAIN_ONLY_JOINT_CALIBRATION",
        "freeze_sha256": file_sha(freeze_file),
        "code_sha256": file_sha(Path(__file__)),
        "train_case_count": len(episodes),
        "train_environment_counts": {str(env): sum(e["environment_index"] == env for e in episodes) for env in (0, 1, 2)},
        "train_archives": [{"case_id": e["case_id"], "source_id": e["source_id"],
                            "environment_index": e["environment_index"], "events": len(e["y"]),
                            "zero_events": int((e["y"] == 0).sum()),
                            "archive_sha256": e["archive_sha256"]} for e in episodes],
        "old_train_objective": old_objective,
        "optimizer_runs": runs,
        "selected_start_index": best["start_index"],
        "new_train_objective": best["objective"],
        "gain_mean": g0,
        "gain_variance": gsd * gsd,
        "discrepancy_variance": dsd * dsd,
        "correlation_time_s": tc,
        "measurement_variance": rsd * rsd,
        "positive_gain": True,
        "boundary_flags": {name: (abs(best["parameters"][i] - freeze["parameters_and_bounds"][name][0]) < 1e-6
                                   or abs(best["parameters"][i] - freeze["parameters_and_bounds"][name][1]) < 1e-6)
                           for i, name in enumerate(names)}
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in output.items() if k not in ("train_archives", "optimizer_runs")}, indent=2), flush=True)


if __name__ == "__main__":
    main()

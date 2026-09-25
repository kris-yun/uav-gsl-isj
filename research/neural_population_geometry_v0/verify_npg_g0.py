#!/usr/bin/env python3
"""Independent NPG-G0 audit from frozen bank, pair records and saved predictions."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np
from scipy.stats import spearmanr
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import log_loss
from sklearn.preprocessing import StandardScaler


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def records(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def get_xy(tensor: np.ndarray, indices: tuple[int, int], reps: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    a, b = indices
    return np.vstack((tensor[a][reps], tensor[b][reps])), np.r_[np.zeros(len(reps)), np.ones(len(reps))]


def score(train: tuple[np.ndarray, np.ndarray], valid: tuple[np.ndarray, np.ndarray], c: float) -> tuple[float, float, float]:
    fit = LogisticRegression(C=c, solver="lbfgs", max_iter=500, tol=1e-8)
    fit.fit(*train)
    truth = valid[1]
    probability = fit.predict_proba(valid[0])[:, 1]
    return (float(log_loss(truth, probability, labels=[0, 1])),
            float(np.mean((probability - truth) ** 2)),
            float(np.mean((probability >= 0.5) == truth)))


def representations(bank: np.ndarray, design: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    z = np.empty((168, 16, 10), dtype=float)
    for block in range(5):
        view = bank[:, :, block * 2:block * 2 + 2].reshape(168, 16, 60)
        training = view[:, design].reshape(-1, 60)
        scaling = StandardScaler().fit(training)
        projection = PCA(n_components=2, svd_solver="full").fit(scaling.transform(training))
        z[:, :, block * 2:block * 2 + 2] = projection.transform(scaling.transform(view.reshape(-1, 60))).reshape(168, 16, 2)
    z_scaling = StandardScaler().fit(z[:, design].reshape(-1, 10))
    z = z_scaling.transform(z.reshape(-1, 10)).reshape(168, 16, 10)
    bounded = z / np.sqrt(1 + z ** 2)
    pieces = []
    for first in range(5):
        for second in range(first + 1, 5):
            a = bounded[:, :, 2 * first:2 * first + 2]
            b = bounded[:, :, 2 * second:2 * second + 2]
            pieces.append((a[:, :, :, None] * b[:, :, None, :]).reshape(168, 16, 4))
    return z, np.concatenate((z, *pieces), axis=2)


def ridge_prediction(features: np.ndarray, targets: np.ndarray, bands: np.ndarray, held: int, grid: list[float]) -> tuple[np.ndarray, float]:
    available = [band for band in range(4) if band != held]
    inner_error = []
    for alpha in grid:
        errors = []
        for validation in available:
            tr = np.isin(bands, [band for band in available if band != validation])
            te = bands == validation
            scaling = StandardScaler().fit(features[tr])
            model = Ridge(alpha=alpha).fit(scaling.transform(features[tr]), targets[tr])
            errors.extend((targets[te] - model.predict(scaling.transform(features[te]))) ** 2)
        inner_error.append(np.mean(errors))
    alpha = grid[int(np.argmin(inner_error))]
    tr = bands != held
    te = bands == held
    scaling = StandardScaler().fit(features[tr])
    model = Ridge(alpha=alpha).fit(scaling.transform(features[tr]), targets[tr])
    return model.predict(scaling.transform(features[te])), alpha


def compare(actual: float, expected: float, label: str, tolerance: float = 1e-9) -> None:
    if not np.isclose(actual, expected, rtol=tolerance, atol=tolerance):
        raise RuntimeError(f"{label}: saved={expected} independent={actual}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--bank", type=Path, required=True)
    args = parser.parse_args()
    repo, bank_path = args.repo.resolve(), args.bank.resolve()
    folder = repo / "evidence/neural_population_geometry_v0/g0"
    lock = json.loads((folder / "NPG_G0_PRE_RUN_LOCK.json").read_text(encoding="utf-8"))
    result = json.loads((folder / "NPG_G0_RESULT.json").read_text(encoding="utf-8"))
    if digest(bank_path) != lock["input_sha256"] or digest(repo / "research/neural_population_geometry_v0/npg_g0.py") != lock["code_sha256"]:
        raise RuntimeError("bank or locked scorer code changed")
    pairs = records(folder / "NPG_G0_PAIR_DEFINITION.csv")
    utility = records(folder / "NPG_G0_PAIR_UTILITY.csv")
    features = records(folder / "NPG_G0_GEOMETRY_FEATURES.csv")
    predictions = records(folder / "NPG_G0_HELDOUT_PREDICTIONS.csv")
    if len(pairs) != 84 or any(len(table) != 168 for table in (utility, features, predictions)):
        raise RuntimeError("record counts invalid")
    if digest(folder / "NPG_G0_PAIR_DEFINITION.csv") != lock["pair_definition_sha256"]:
        raise RuntimeError("pair definition SHA drift")
    for p in pairs:
        i, j = int(p["left_i"]), int(p["y_row"])
        if (int(p["left_index"]), int(p["right_index"]), int(p["band"])) != ((i - 1) * 7 + j - 12, i * 7 + j - 12, (i - 1) // 6):
            raise RuntimeError("pair geometry drift")
    bank = np.load(bank_path, allow_pickle=False)
    if bank.shape != (168, 16, 10, 30):
        raise RuntimeError("bank shape drift")
    lookup_u = {(row["split"], int(row["pair_index"])): row for row in utility}
    lookup_f = {(row["split"], int(row["pair_index"])): row for row in features}
    lookup_p = {(row["split"], int(row["pair_index"])): row for row in predictions}
    band_vector = np.array([int(p["band"]) for p in pairs])
    c_grid = lock["config"]["reader_C_grid"]
    ridge_grid = lock["config"]["ridge_alpha_grid"]
    maximum_loss_diff = 0.0
    maximum_prediction_diff = 0.0
    for split in ("A", "B"):
        design = np.arange(0 if split == "A" else 1, 16, 2)
        audit = np.arange(1 if split == "A" else 0, 16, 2)
        base, interaction = representations(bank, design)
        models = (base, interaction)
        inner = np.empty((2, 84, len(c_grid)))
        for mi, tensor in enumerate(models):
            for pi, pair in enumerate(pairs):
                indices = int(pair["left_index"]), int(pair["right_index"])
                for ci, c in enumerate(c_grid):
                    losses = []
                    for training, validation in ((design[:4], design[4:]), (design[4:], design[:4])):
                        losses.append(score(get_xy(tensor, indices, training), get_xy(tensor, indices, validation), c)[0])
                    inner[mi, pi, ci] = np.mean(losses)
        selected = {}
        for held in range(4):
            train_mask = band_vector != held
            selected[held] = [int(np.argmin(inner[mi, train_mask].mean(axis=0))) for mi in range(2)]
        targets = np.empty(84)
        for pi, pair in enumerate(pairs):
            band = int(pair["band"])
            indices = int(pair["left_index"]), int(pair["right_index"])
            row = lookup_u[(split, pi)]
            c_base, c_int = [c_grid[index] for index in selected[band]]
            compare(c_base, float(row["base_C"]), "base C")
            compare(c_int, float(row["interaction_C"]), "interaction C")
            values = [score(get_xy(tensor, indices, design), get_xy(tensor, indices, audit), c)
                      for tensor, c in ((base, c_base), (interaction, c_int))]
            actual_delta = values[0][0] - values[1][0]
            cv_delta = inner[0, pi, selected[band][0]] - inner[1, pi, selected[band][1]]
            for independent, saved, label in ((values[0][0], row["audit_base_logloss"], "base loss"),
                                              (values[1][0], row["audit_interaction_logloss"], "interaction loss"),
                                              (actual_delta, row["audit_delta_log"], "utility"),
                                              (cv_delta, row["design_inner_cv_delta_log"], "inner CV")):
                compare(independent, float(saved), label)
                maximum_loss_diff = max(maximum_loss_diff, abs(independent - float(saved)))
            targets[pi] = actual_delta
            compare(actual_delta, float(lookup_p[(split, pi)]["actual_delta_log"]), "prediction target")
        geometry = np.array([[float(lookup_f[(split, pi)][f"geometry_{k}"]) for k in range(21)] for pi in range(84)])
        scalars = {name: np.array([[float(lookup_f[(split, pi)][f"ordinary_{name}"])] for pi in range(84)])
                   for name in lock["config"]["ordinary_predictors"] if name != "INNER_CV"}
        for held in range(4):
            test_indices = np.where(band_vector == held)[0]
            for name, matrix in (("GEOMETRY", geometry), *scalars.items()):
                estimated, alpha = ridge_prediction(matrix, targets, band_vector, held, ridge_grid)
                for offset, pi in enumerate(test_indices):
                    saved = lookup_p[(split, int(pi))]
                    compare(float(estimated[offset]), float(saved[name]), name)
                    compare(alpha, float(saved["geometry_alpha" if name == "GEOMETRY" else f"alpha_{name}"]), "ridge alpha")
                    maximum_prediction_diff = max(maximum_prediction_diff, abs(float(estimated[offset]) - float(saved[name])))
        print("NPG_G0_INDEPENDENT_SPLIT", split, flush=True)
    y = np.array([[float(lookup_p[(split, pi)]["actual_delta_log"]) for split in ("A", "B")] for pi in range(84)])
    g = np.array([[float(lookup_p[(split, pi)]["GEOMETRY"]) for split in ("A", "B")] for pi in range(84)])
    cv = np.array([[float(lookup_p[(split, pi)]["INNER_CV"]) for split in ("A", "B")] for pi in range(84)])
    dy = y.mean(axis=1)
    dg = g.mean(axis=1)
    dc = cv.mean(axis=1)
    advantage = ((cv - y) ** 2 - (g - y) ** 2).mean(axis=1)
    rng = np.random.default_rng(lock["config"]["bootstrap_seed"])
    bootstrap_rho = np.empty(lock["config"]["bootstrap_draws"])
    bootstrap_adv = np.empty_like(bootstrap_rho)
    for index in range(len(bootstrap_rho)):
        draw = rng.integers(0, 84, 84)
        bootstrap_rho[index] = spearmanr(dy[draw], dg[draw]).statistic
        bootstrap_adv[index] = advantage[draw].mean()
    with np.load(folder / "NPG_G0_PAIR_BOOTSTRAP_10000.npz", allow_pickle=False) as saved:
        bootstrap_rho_error = float(np.max(np.abs(bootstrap_rho - saved["spearman"])))
        bootstrap_adv_error = float(np.max(np.abs(bootstrap_adv - saved["mse_advantage"])))
        if bootstrap_rho_error > 1e-12 or bootstrap_adv_error > 1e-12:
            raise RuntimeError("bootstrap draws differ")
    rho = float(spearmanr(dy, dg).statistic)
    rho_ci = np.quantile(bootstrap_rho, [0.025, 0.975])
    adv_ci = np.quantile(bootstrap_adv, [0.025, 0.975])
    compare(rho, result["geometry_spearman"], "Spearman")
    compare(float(advantage.mean()), result["mse_advantage_inner_cv_minus_geometry"], "MSE advantage")
    for index in range(2):
        compare(float(rho_ci[index]), result["geometry_spearman_ci95"][index], "Spearman CI")
        compare(float(adv_ci[index]), result["mse_advantage_ci95"][index], "MSE CI")
    positive = dy > 0
    negative = dy < 0
    ba_geo = 0.5 * ((dg[positive] > 0).mean() + (dg[negative] <= 0).mean())
    ba_cv = 0.5 * ((dc[positive] > 0).mean() + (dc[negative] <= 0).mean())
    compare(float(ba_geo), result["geometry_balanced_accuracy"], "geometry BA")
    compare(float(ba_cv), result["inner_cv_balanced_accuracy"], "CV BA")
    gates = {
        "G0_1": int(positive.sum()) >= 9 and int(negative.sum()) >= 9,
        "G0_2": rho > 0 and rho_ci[0] > 0 and all(spearmanr(y[:, i], g[:, i]).statistic > 0 for i in range(2)),
        "G0_3": advantage.mean() > 0 and adv_ci[0] > 0,
        "G0_4": ba_geo >= 0.60 and ba_geo >= ba_cv,
        "G0_5": sum(advantage[band_vector == band].mean() > 0 for band in range(4)) >= 3,
    }
    if gates != result["gates"] or result["decision"] != "NPG_G0_STOP_GEOMETRY_NOT_BETTER_THAN_ORDINARY_SELECTION":
        raise RuntimeError("gate/decision mismatch")
    output = {"independent_recomputation": "PASS", "decision": result["decision"], "gates": {k: bool(v) for k, v in gates.items()},
              "source_pairs_checked": 84, "audit_pair_models_refit": 336,
              "geometry_and_scalar_predictions_refit": 840,
              "bootstrap_draws_recomputed": len(bootstrap_rho),
              "max_audit_logloss_difference": maximum_loss_diff,
              "max_ridge_prediction_difference": maximum_prediction_diff,
              "max_bootstrap_spearman_difference": bootstrap_rho_error,
              "max_bootstrap_mse_advantage_difference": bootstrap_adv_error,
              "input_sha256": lock["input_sha256"], "sealed_data_read": False}
    path = folder / "NPG_G0_INDEPENDENT_RECOMPUTATION.json"
    path.write_bytes((json.dumps(output, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    print("NPG_G0_INDEPENDENT_RECOMPUTATION_PASS", result["decision"])


if __name__ == "__main__":
    main()

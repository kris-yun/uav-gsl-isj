#!/usr/bin/env python3
"""Frozen zero-plume NPG-G0 reference-only falsification gate."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
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

HERE = Path(__file__).resolve().parent
OUT_REL = Path("evidence/neural_population_geometry_v0/g0")
PANEL_REL = Path("evidence/causal_emergent_source_scale_v0/d1r/CESS_D1R_PANEL_168.tsv")
EXPECTED_INPUT_SHA = "b21a089cb015ace71a448db58bd7a2f1fee25e9a8431cbb56728f48ca39573d9"
EXPECTED_PANEL_SHA = "5df11712dd0e7dbef6e454c8d146427407644b9f27245c447479185ab2129d8e"
DECISIONS = {
    "PASS": "NPG_G0_PASS_TASK_GEOMETRY_PREDICTS_INTERACTION_UTILITY",
    "HOLD": "NPG_G0_HOLD_INSUFFICIENT_UTILITY_HETEROGENEITY",
    "STOP": "NPG_G0_STOP_GEOMETRY_NOT_BETTER_THAN_ORDINARY_SELECTION",
}
CONFIG = {
    "data_shape": [168, 16, 10, 30],
    "source_grid": "24 x-columns i=1..24 by 7 y-rows j=12..18, panel index=(i-1)*7+(j-12)",
    "pairs": "within each y-row adjacent x columns (1,2),(3,4),...,(23,24)",
    "macro_bands": [[1, 6], [7, 12], [13, 18], [19, 24]],
    "splits": {"A": {"design": "even zero-based indices", "audit": "odd zero-based indices"},
               "B": {"design": "odd zero-based indices", "audit": "even zero-based indices"}},
    "block_transform": "five contiguous two-time blocks; raw ppm; StandardScaler per 60-D block, PCA full SVD 2-D; fit all 168x8 DESIGN observations; global DESIGN z-coordinate StandardScaler after concatenation",
    "interaction": "u=z/sqrt(1+z^2); concatenate 2x2 u_b outer u_c for all b<c in lexicographic order to 40-D; no additional scaling",
    "reader": "LogisticRegression L2 lbfgs, fit_intercept True, class_weight None, max_iter 500, tol 1e-8; base and interaction independent global C",
    "reader_C_grid": [0.01, 0.1, 1.0, 10.0, 100.0],
    "reader_C_selection": "minimum mean pairwise 4/4-swap DESIGN log loss across 63 pairs in 3 non-held-out macro-bands; ties smallest C",
    "inner_cv": "within-pair first4/last4 and reverse, same globally selected C for each reader; Delta=base minus interaction DESIGN validation log loss",
    "geometry": "seven DESIGN-only descriptors for base and interaction plus interaction-minus-base: center norm, sqrt(trace pooled within covariance), participation ratio, task-noise alignment, absolute leading within-axis dot, d/(2K)*traceW/(sep2+traceW), sep2/(traceW+1e-12)-PR/(2K); pooled within covariance uses ddof=1 per class; signed log1p of all 21 values",
    "geometry_predictor": "Ridge with intercept; feature StandardScaler on 3 training bands; alpha selected by 3-fold leave-one-training-band-out mean MSE; ties smallest alpha",
    "ordinary_predictors": ["INNER_CV", "CROSSBLOCK_COV_NORM", "INTERACTION_ENERGY", "RAW_MASS_DIFFERENCE", "BASE_SNR"],
    "ordinary_fit": "for four scalar descriptors use same 3-band ridge protocol; INNER_CV is its direct DESIGN utility estimate",
    "ridge_alpha_grid": [0.01, 0.1, 1.0, 10.0, 100.0, 1000.0],
    "bootstrap_seed": 202609250,
    "bootstrap_draws": 10000,
    "bootstrap_unit": "84 disjoint source pairs; both A/B directions remain clustered within sampled pair",
    "bootstrap_ci": "percentile 2.5%,97.5%; lower bound must be strictly >0",
    "aggregation": "primary Spearman and balanced accuracy use A/B mean for each of 84 pairs; MSE advantage averages both directions per pair; macro-band MSE advantage averages 42 split-pair observations",
    "gate_G0_1": "at least 9/84 positive and at least 9/84 negative A/B-mean utilities (ceil 10%)",
    "gate_G0_2": "pooled Spearman >0, pair bootstrap CI lower >0, and each split Spearman >0",
    "gate_G0_3": "mean paired squared-error advantage INNER_CV minus GEOMETRY >0 and pair bootstrap CI lower >0",
    "gate_G0_4": "GEOMETRY pair-mean benefit-sign balanced accuracy >=0.60 and >=INNER_CV",
    "gate_G0_5": "MSE advantage positive in at least 3 of 4 macro-bands",
    "gate_precedence": "G0-1 false => HOLD; otherwise any G0-2..G0-5 false => STOP; all true => PASS",
}


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"empty table: {path}")
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def panel_and_pairs(repo: Path) -> tuple[list[dict], list[dict]]:
    panel_path = repo / PANEL_REL
    if sha(panel_path) != EXPECTED_PANEL_SHA:
        raise RuntimeError("frozen panel SHA mismatch")
    with panel_path.open(encoding="utf-8", newline="") as stream:
        panel = list(csv.DictReader(stream, delimiter="\t"))
    if len(panel) != 168:
        raise RuntimeError("not 168 panel sources")
    for row in panel:
        i, j, index = int(row["pmfs_i"]), int(row["pmfs_j"]), int(row["panel_index"])
        if not (1 <= i <= 24 and 12 <= j <= 18 and index == (i - 1) * 7 + j - 12):
            raise RuntimeError("24x7 panel ordering mismatch")
    pairs = []
    for j in range(12, 19):
        for i in range(1, 24, 2):
            left, right = (i - 1) * 7 + j - 12, i * 7 + j - 12
            a, b = panel[left], panel[right]
            distance = ((float(a["x_m"]) - float(b["x_m"])) ** 2 +
                        (float(a["y_m"]) - float(b["y_m"])) ** 2) ** 0.5
            if abs(distance - 0.3) > 1e-5:
                raise RuntimeError("pair is not a 0.3m neighbor")
            pairs.append({"pair_index": len(pairs), "band": (i - 1) // 6,
                          "y_row": j, "left_i": i, "right_i": i + 1,
                          "left_index": left, "right_index": right,
                          "left_source_id": a["source_id"], "right_source_id": b["source_id"],
                          "distance_m": distance})
    if len(pairs) != 84 or sorted([int(p[k]) for p in pairs for k in ("left_index", "right_index")]) != list(range(168)):
        raise RuntimeError("pairs not disjoint/exhaustive")
    if [sum(p["band"] == b for p in pairs) for b in range(4)] != [21] * 4:
        raise RuntimeError("macro-band counts mismatch")
    return panel, pairs


def prepare(repo: Path, bank: Path) -> None:
    branch = subprocess.check_output(["git", "-C", str(repo), "branch", "--show-current"], text=True).strip()
    if branch != "research/neural-population-geometry-g0-20260925":
        raise RuntimeError("wrong branch")
    if sha(bank) != EXPECTED_INPUT_SHA:
        raise RuntimeError("frozen input SHA mismatch")
    tensor = np.load(bank, mmap_mode="r", allow_pickle=False)
    if tensor.shape != (168, 16, 10, 30) or tensor.dtype != np.float64:
        raise RuntimeError("frozen input shape/dtype mismatch")
    if not np.isfinite(tensor).all() or (tensor < 0).any():
        raise RuntimeError("frozen input nonfinite/negative")
    _, pairs = panel_and_pairs(repo)
    out = repo / OUT_REL
    out.mkdir(parents=True, exist_ok=True)
    lock = out / "NPG_G0_PRE_RUN_LOCK.json"
    if lock.exists():
        raise RuntimeError("refuse to overwrite NPG pre-run lock")
    write_csv(out / "NPG_G0_PAIR_DEFINITION.csv", pairs)
    write_json(lock, {"branch": branch, "input_sha256": EXPECTED_INPUT_SHA,
                      "panel_sha256": EXPECTED_PANEL_SHA, "pair_definition_sha256": sha(out / "NPG_G0_PAIR_DEFINITION.csv"),
                      "code_sha256": sha(Path(__file__)), "charter_sha256": sha(HERE / "NPG_G0_REFERENCE_ONLY_CHARTER_20260925.md"),
                      "python": sys.version,
                      "numpy": np.__version__, "config": CONFIG,
                      "audit_utility_scored_at_lock": False})
    print("NPG_G0_A0_LOCK_WRITTEN", sha(lock), len(pairs))


def transformed(x: np.ndarray, design: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    z = np.empty((168, 16, 10), dtype=np.float64)
    for block in range(5):
        raw = x[:, :, 2 * block:2 * block + 2, :].reshape(168, 16, 60)
        training = raw[:, design].reshape(-1, 60)
        scaler = StandardScaler().fit(training)
        pca = PCA(n_components=2, svd_solver="full").fit(scaler.transform(training))
        z[:, :, 2 * block:2 * block + 2] = pca.transform(scaler.transform(raw.reshape(-1, 60))).reshape(168, 16, 2)
    zscaler = StandardScaler().fit(z[:, design].reshape(-1, 10))
    z = zscaler.transform(z.reshape(-1, 10)).reshape(168, 16, 10)
    u = z / np.sqrt(1.0 + z * z)
    interaction = np.concatenate([np.einsum("sri,srj->srij", u[:, :, 2*b:2*b+2],
                                                     u[:, :, 2*c:2*c+2]).reshape(168, 16, 4)
                                  for b in range(5) for c in range(b + 1, 5)], axis=2)
    return z, np.concatenate([z, interaction], axis=2)


def pair_data(values: np.ndarray, pair: dict, reps: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    left, right = int(pair["left_index"]), int(pair["right_index"])
    return np.concatenate([values[left, reps], values[right, reps]], axis=0), np.array([0] * len(reps) + [1] * len(reps))


def reader_loss(train_x: np.ndarray, train_y: np.ndarray, test_x: np.ndarray, test_y: np.ndarray, c: float) -> tuple[float, float, float]:
    model = LogisticRegression(C=c, solver="lbfgs", max_iter=500, tol=1e-8, fit_intercept=True)
    model.fit(train_x, train_y)
    probability = model.predict_proba(test_x)[:, 1]
    loss = float(log_loss(test_y, probability, labels=[0, 1]))
    brier = float(np.mean((probability - test_y) ** 2))
    accuracy = float(np.mean((probability >= 0.5) == test_y))
    return loss, brier, accuracy


def swap_cv(values: np.ndarray, pair: dict, design: np.ndarray, c: float) -> float:
    losses = []
    for train_reps, validation_reps in ((design[:4], design[4:]), (design[4:], design[:4])):
        train_x, train_y = pair_data(values, pair, train_reps)
        test_x, test_y = pair_data(values, pair, validation_reps)
        losses.append(reader_loss(train_x, train_y, test_x, test_y, c)[0])
    return float(np.mean(losses))


def descriptors(values: np.ndarray, pair: dict, design: np.ndarray) -> list[float]:
    left = values[int(pair["left_index"]), design]
    right = values[int(pair["right_index"]), design]
    d = right.mean(axis=0) - left.mean(axis=0)
    sep2 = float(d @ d)
    cov_left = np.cov(left, rowvar=False)
    cov_right = np.cov(right, rowvar=False)
    within = 0.5 * (cov_left + cov_right)
    trace = max(0.0, float(np.trace(within)))
    pr = trace ** 2 / max(float(np.sum(within * within)), 1e-12)
    alignment = float(d @ within @ d) / max(sep2 * trace, 1e-12)
    axis_l = np.linalg.eigh(cov_left)[1][:, -1]
    axis_r = np.linalg.eigh(cov_right)[1][:, -1]
    axes = abs(float(axis_l @ axis_r))
    dimension, k = values.shape[2], len(design)
    finite_penalty = dimension / (2 * k) * trace / max(sep2 + trace, 1e-12)
    analytic_ab = sep2 / (trace + 1e-12) - pr / (2 * k)
    return [np.sqrt(sep2), np.sqrt(trace), pr, alignment, axes, finite_penalty, analytic_ab]


def signed_log(values: np.ndarray) -> np.ndarray:
    return np.sign(values) * np.log1p(np.abs(values))


def scalar_features(x: np.ndarray, z: np.ndarray, interaction: np.ndarray, pair: dict, design: np.ndarray) -> dict[str, float]:
    left, right = int(pair["left_index"]), int(pair["right_index"])
    zz = np.concatenate([z[left, design], z[right, design]])
    c0 = np.cov(z[left, design], rowvar=False)
    c1 = np.cov(z[right, design], rowvar=False)
    cov = 0.5 * (c0 + c1)
    mask = np.ones((10, 10), dtype=bool)
    for b in range(5):
        mask[2*b:2*b+2, 2*b:2*b+2] = False
    cross = float(np.linalg.norm(cov[mask]))
    energy = float(np.mean(np.sum(interaction[[left, right]][:, design, 10:] ** 2, axis=2)))
    mass_left = x[left, design].sum(axis=(1, 2)).mean()
    mass_right = x[right, design].sum(axis=(1, 2)).mean()
    mass_diff = float(abs(mass_right - mass_left))
    base = descriptors(z, pair, design)
    return {"CROSSBLOCK_COV_NORM": cross, "INTERACTION_ENERGY": energy,
            "RAW_MASS_DIFFERENCE": mass_diff, "BASE_SNR": base[0] / max(base[1], 1e-12)}


def choose_ridge(features: np.ndarray, target: np.ndarray, bands: np.ndarray, train_bands: list[int], grid: list[float]) -> float:
    scores = []
    for alpha in grid:
        fold_mse = []
        for held in train_bands:
            tr = np.isin(bands, [b for b in train_bands if b != held])
            va = bands == held
            scaler = StandardScaler().fit(features[tr])
            model = Ridge(alpha=alpha).fit(scaler.transform(features[tr]), target[tr])
            fold_mse.extend((target[va] - model.predict(scaler.transform(features[va]))) ** 2)
        scores.append(float(np.mean(fold_mse)))
    return grid[int(np.argmin(scores))]


def predict_ridge(features: np.ndarray, target: np.ndarray, bands: np.ndarray, held: int, grid: list[float]) -> tuple[np.ndarray, float]:
    training_bands = [b for b in range(4) if b != held]
    train = bands != held
    test = bands == held
    alpha = choose_ridge(features, target, bands, training_bands, grid)
    scaler = StandardScaler().fit(features[train])
    model = Ridge(alpha=alpha).fit(scaler.transform(features[train]), target[train])
    return model.predict(scaler.transform(features[test])), alpha


def balanced_accuracy(truth: np.ndarray, predicted: np.ndarray) -> float:
    labels = truth > 0
    if not labels.any() or labels.all():
        return float("nan")
    guess = predicted > 0
    return float(0.5 * (np.mean(guess[labels]) + np.mean(~guess[~labels])))


def run(repo: Path, bank: Path) -> None:
    out = repo / OUT_REL
    lock_path = out / "NPG_G0_PRE_RUN_LOCK.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if (lock["code_sha256"] != sha(Path(__file__)) or lock["input_sha256"] != sha(bank)
            or lock["panel_sha256"] != sha(repo / PANEL_REL) or lock["config"] != CONFIG):
        raise RuntimeError("pre-run lock mismatch")
    if subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain"], text=True).strip():
        raise RuntimeError("runner refuses dirty checkout")
    x = np.load(bank, allow_pickle=False)
    _, pairs = panel_and_pairs(repo)
    if lock["pair_definition_sha256"] != sha(out / "NPG_G0_PAIR_DEFINITION.csv"):
        raise RuntimeError("pair lock mismatch")
    if (out / "NPG_G0_RESULT.json").exists():
        raise RuntimeError("refuse result overwrite")
    bands = np.array([int(p["band"]) for p in pairs])
    all_utility: list[dict] = []
    all_features: list[dict] = []
    all_predictions: list[dict] = []
    c_grid = CONFIG["reader_C_grid"]
    for split in ("A", "B"):
        design = np.arange(0 if split == "A" else 1, 16, 2)
        audit = np.arange(1 if split == "A" else 0, 16, 2)
        z, interaction = transformed(x, design)
        models = {"BASE": z, "INTERACTION": interaction}
        inner = np.empty((2, len(pairs), len(c_grid)))
        for mi, (name, values) in enumerate(models.items()):
            for pi, pair in enumerate(pairs):
                for ci, c in enumerate(c_grid):
                    inner[mi, pi, ci] = swap_cv(values, pair, design, c)
        geometry = np.empty((len(pairs), 21), dtype=np.float64)
        ordinary: dict[str, np.ndarray] = {name: np.empty(len(pairs)) for name in CONFIG["ordinary_predictors"] if name != "INNER_CV"}
        for pi, pair in enumerate(pairs):
            base = descriptors(z, pair, design)
            intr = descriptors(interaction, pair, design)
            geometry[pi] = signed_log(np.array(base + intr + list(np.array(intr) - base)))
            for name, value in scalar_features(x, z, interaction, pair, design).items():
                ordinary[name][pi] = np.sign(value) * np.log1p(abs(value))
            all_features.append({"split": split, "pair_index": pi, "band": pair["band"],
                                 **{f"geometry_{k}": float(v) for k, v in enumerate(geometry[pi])},
                                 **{f"ordinary_{k}": float(v[pi]) for k, v in ordinary.items()}})
        # Every held-out band's C values use only other bands' DESIGN CV losses.
        selected: dict[int, tuple[int, int]] = {}
        for band in range(4):
            train_pairs = bands != band
            selected[band] = tuple(int(np.argmin(inner[mi, train_pairs].mean(axis=0))) for mi in range(2))
        utilities = np.empty(len(pairs))
        cv_predictions = np.empty(len(pairs))
        for pi, pair in enumerate(pairs):
            band = int(pair["band"])
            cb, ci = selected[band]
            cb_val, ci_val = c_grid[cb], c_grid[ci]
            values = []
            for name, matrix, c in (("BASE", z, cb_val), ("INTERACTION", interaction, ci_val)):
                train_x, train_y = pair_data(matrix, pair, design)
                test_x, test_y = pair_data(matrix, pair, audit)
                values.append(reader_loss(train_x, train_y, test_x, test_y, c))
            utilities[pi] = values[0][0] - values[1][0]
            cv_predictions[pi] = inner[0, pi, cb] - inner[1, pi, ci]
            all_utility.append({"split": split, "pair_index": pi, "band": band,
                                "base_C": cb_val, "interaction_C": ci_val,
                                "audit_base_logloss": values[0][0], "audit_interaction_logloss": values[1][0],
                                "audit_delta_log": utilities[pi],
                                "audit_delta_brier": values[0][1] - values[1][1],
                                "audit_delta_accuracy": values[1][2] - values[0][2],
                                "design_inner_cv_delta_log": cv_predictions[pi]})
        for held in range(4):
            geom_pred, geom_alpha = predict_ridge(geometry, utilities, bands, held, CONFIG["ridge_alpha_grid"])
            ordinary_pred = {}
            ordinary_alpha = {}
            for name, values in ordinary.items():
                prediction, alpha = predict_ridge(values[:, None], utilities, bands, held, CONFIG["ridge_alpha_grid"])
                ordinary_pred[name] = prediction
                ordinary_alpha[name] = alpha
            for position, pi in enumerate(np.where(bands == held)[0]):
                all_predictions.append({"split": split, "pair_index": int(pi), "band": held,
                                        "actual_delta_log": float(utilities[pi]),
                                        "GEOMETRY": float(geom_pred[position]),
                                        "INNER_CV": float(cv_predictions[pi]),
                                        **{name: float(prediction[position]) for name, prediction in ordinary_pred.items()},
                                        "geometry_alpha": geom_alpha,
                                        **{f"alpha_{name}": alpha for name, alpha in ordinary_alpha.items()}})
        print("NPG_G0_SPLIT_SCORED", split, flush=True)
    all_utility.sort(key=lambda row: (row["pair_index"], row["split"]))
    all_features.sort(key=lambda row: (row["pair_index"], row["split"]))
    all_predictions.sort(key=lambda row: (row["pair_index"], row["split"]))
    write_csv(out / "NPG_G0_PAIR_UTILITY.csv", all_utility)
    write_csv(out / "NPG_G0_GEOMETRY_FEATURES.csv", all_features)
    write_csv(out / "NPG_G0_HELDOUT_PREDICTIONS.csv", all_predictions)
    actual = np.array([[float(r["actual_delta_log"]) for r in all_predictions if r["pair_index"] == pi] for pi in range(84)])
    geo = np.array([[float(r["GEOMETRY"]) for r in all_predictions if r["pair_index"] == pi] for pi in range(84)])
    cv = np.array([[float(r["INNER_CV"]) for r in all_predictions if r["pair_index"] == pi] for pi in range(84)])
    advantage = (cv - actual) ** 2 - (geo - actual) ** 2
    a_bar, g_bar, c_bar = actual.mean(axis=1), geo.mean(axis=1), cv.mean(axis=1)
    rho = float(spearmanr(a_bar, g_bar).statistic)
    rho_split = {split: float(spearmanr(actual[:, si], geo[:, si]).statistic) for si, split in enumerate(("A", "B"))}
    rng = np.random.default_rng(CONFIG["bootstrap_seed"])
    boot_rho = np.empty(CONFIG["bootstrap_draws"])
    boot_advantage = np.empty(CONFIG["bootstrap_draws"])
    for bi in range(len(boot_rho)):
        sampled = rng.integers(0, 84, size=84)
        boot_rho[bi] = float(spearmanr(a_bar[sampled], g_bar[sampled]).statistic)
        boot_advantage[bi] = float(advantage[sampled].mean())
    if not np.isfinite(boot_rho).all() or not np.isfinite(boot_advantage).all():
        raise RuntimeError("nonfinite bootstrap metric")
    rho_ci = np.quantile(boot_rho, [0.025, 0.975]).tolist()
    advantage_ci = np.quantile(boot_advantage, [0.025, 0.975]).tolist()
    bands_out = []
    for band in range(4):
        mask = bands == band
        bands_out.append({"band": band, "pair_count": int(mask.sum()),
                          "mean_mse_advantage_inner_cv_minus_geometry": float(advantage[mask].mean()),
                          "geometry_spearman": float(spearmanr(actual[mask].mean(axis=1), geo[mask].mean(axis=1)).statistic)})
    write_csv(out / "NPG_G0_MACRO_BAND_SUMMARY.csv", bands_out)
    np.savez_compressed(out / "NPG_G0_PAIR_BOOTSTRAP_10000.npz", spearman=boot_rho,
                        mse_advantage=boot_advantage, seed=np.array(CONFIG["bootstrap_seed"]))
    positives = int((a_bar > 0).sum())
    negatives = int((a_bar < 0).sum())
    ba_geo, ba_cv = balanced_accuracy(a_bar, g_bar), balanced_accuracy(a_bar, c_bar)
    gates = {
        "G0_1": positives >= 9 and negatives >= 9,
        "G0_2": rho > 0 and rho_ci[0] > 0 and all(value > 0 for value in rho_split.values()),
        "G0_3": float(advantage.mean()) > 0 and advantage_ci[0] > 0,
        "G0_4": ba_geo >= 0.60 and ba_geo >= ba_cv,
        "G0_5": sum(row["mean_mse_advantage_inner_cv_minus_geometry"] > 0 for row in bands_out) >= 3,
    }
    decision = DECISIONS["HOLD" if not gates["G0_1"] else ("PASS" if all(gates.values()) else "STOP")]
    result = {"decision": decision, "gates": gates, "pair_count": 84, "source_count": 168,
              "new_plume_runs": 0, "positive_utility_pairs": positives, "negative_utility_pairs": negatives,
              "geometry_spearman": rho, "geometry_spearman_split": rho_split, "geometry_spearman_ci95": rho_ci,
              "mse_advantage_inner_cv_minus_geometry": float(advantage.mean()),
              "mse_advantage_ci95": advantage_ci, "geometry_balanced_accuracy": ba_geo,
              "inner_cv_balanced_accuracy": ba_cv, "macro_band_advantages": bands_out,
              "pre_run_lock_sha256": sha(lock_path), "input_sha256": sha(bank),
              "charter_boundary": "OPEN historical House02 reference bank only; no E2 targets, H01 DEV, House03, G2, or closed loop"}
    write_json(out / "NPG_G0_RESULT.json", result)
    print("NPG_G0_DECISION", decision, flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["prepare", "run"])
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--bank", type=Path, required=True)
    args = parser.parse_args()
    repo, bank = args.repo.resolve(), args.bank.resolve()
    if args.phase == "prepare":
        prepare(repo, bank)
    else:
        run(repo, bank)


if __name__ == "__main__":
    main()

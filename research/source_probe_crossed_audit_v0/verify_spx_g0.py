#!/usr/bin/env python3
"""Independent full SPX-G0 pair-refit and frozen-rule recomputation."""
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
from scipy.linalg import solve_triangular
from scipy.special import expit
from scipy.stats import spearmanr
from sklearn.covariance import OAS
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def table(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def close(actual: float, saved: float, label: str, *, rtol: float = 5e-8, atol: float = 1e-7) -> float:
    if not np.isclose(actual, saved, rtol=rtol, atol=atol):
        raise RuntimeError(f"{label} independent={actual}, saved={saved}")
    return abs(actual - saved)


def gaussian(data: np.ndarray, mean: np.ndarray, cov: np.ndarray) -> np.ndarray:
    chol = np.linalg.cholesky(cov)
    whitened = solve_triangular(chol, (data - mean).T, lower=True)
    return -0.5 * (data.shape[1] * np.log(2 * np.pi) +
                   2 * np.log(np.diag(chol)).sum() +
                   np.sum(whitened * whitened, axis=0))


def fitted(data: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    model = OAS(assume_centered=False, store_precision=False).fit(data)
    cov = model.covariance_.copy()
    d = cov.shape[0]
    cov[np.diag_indices(d)] += 1e-10 * max(1.0, float(np.trace(cov)) / d)
    return model.location_.copy(), cov


def one_fold(raw: np.ndarray, held: tuple[int, ...]) -> dict[str, np.ndarray]:
    reference = [i for i in range(16) if i not in held]
    transformed = np.empty((2, 16, 10), dtype=float)
    for b in range(5):
        cube = raw[:, :, 2 * b:2 * b + 2].reshape(2, 16, 60)
        reference_raw = cube[:, reference].reshape(24, 60)
        scaler = StandardScaler().fit(reference_raw)
        pca = PCA(n_components=2, svd_solver="full").fit(scaler.transform(reference_raw))
        transformed[:, :, 2 * b:2 * b + 2] = pca.transform(scaler.transform(cube.reshape(32, 60))).reshape(2, 16, 2)
    train = transformed[:, reference]
    test = transformed[:, list(held)].reshape(8, 10)
    scores = {name: np.empty((8, 2)) for name in ("FULL", "BLOCK_PRODUCT", "MATCHED_BLOCK_DIAG")}
    for s in range(2):
        mu, cov = fitted(train[s])
        scores["FULL"][:, s] = gaussian(test, mu, cov)
        matched = np.zeros((10, 10))
        for block in range(5):
            indices = np.arange(2 * block, 2 * block + 2)
            matched[np.ix_(indices, indices)] = cov[np.ix_(indices, indices)]
        scores["MATCHED_BLOCK_DIAG"][:, s] = gaussian(test, mu, matched)
        bp = np.zeros(8)
        for block in range(5):
            sl = slice(2 * block, 2 * block + 2)
            bmu, bcov = fitted(train[s, :, sl])
            bp += gaussian(test[:, sl], bmu, bcov)
        scores["BLOCK_PRODUCT"][:, s] = bp
    return scores


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    folder = repo / "evidence/source_probe_crossed_audit_v0"
    lock = json.loads((folder / "SPX_G0_PRE_SCORE_LOCK.json").read_text(encoding="utf-8"))
    result = json.loads((folder / "SPX_G0_RESULT.json").read_text(encoding="utf-8"))
    if lock["code_sha256"] != digest(repo / "research/source_probe_crossed_audit_v0/score_spx_g0.py"):
        raise RuntimeError("scorer changed after frozen lock")
    if lock["pairs_sha256"] != digest(folder / "SPX_G0_FROZEN_PAIRS.csv"):
        raise RuntimeError("pair lock drift")
    pairs = table(folder / "SPX_G0_FROZEN_PAIRS.csv")
    if len(pairs) != 87:
        raise RuntimeError("pair count")
    tensors = {}
    for panel in ("CENTRAL", "OFFSTRIP"):
        for protocol in ("P_G1A", "P_E2"):
            key = f"{panel}_{protocol}"
            path = folder / f"SPX_G0_{key}_10x30.npy"
            if digest(path) != lock["crossed_tensor_sha256"][key]:
                raise RuntimeError("crossed tensor drift")
            tensors[(panel, protocol)] = np.load(path, allow_pickle=False)
    target_rows = table(folder / "SPX_G0_TARGET_METRICS.csv")
    if len(target_rows) != 87 * 2 * 2 * 16 * 3:
        raise RuntimeError("target metric count")
    target_lookup = {(r["panel"], int(r["pair_index"]), r["protocol"], int(r["source_direction"]),
                      int(r["replicate_index"]), r["model"]): r for r in target_rows}
    if len(target_lookup) != len(target_rows):
        raise RuntimeError("duplicate target metric key")
    folds = [tuple(v) for v in lock["config"]["folds"]]
    max_margin = 0.0
    max_nll = 0.0
    count = 0
    for pair in pairs:
        panel = pair["panel"]
        pi = int(pair["pair_index"])
        indices = [int(pair["source0_index"]), int(pair["source1_index"])]
        for protocol in ("P_G1A", "P_E2"):
            source_data = tensors[(panel, protocol)][indices]
            for fold, held in enumerate(folds):
                likelihood = one_fold(source_data, held)
                labels = np.repeat(np.arange(2), 4)
                for model, scores in likelihood.items():
                    for position in range(8):
                        s = int(labels[position])
                        r = held[position % 4]
                        row = target_lookup[(panel, pi, protocol, s, r, model)]
                        if int(row["fold"]) != fold:
                            raise RuntimeError("fold assignment mismatch")
                        margin = float(scores[position, s] - scores[position, 1-s])
                        nll = float(np.logaddexp(0, -margin))
                        brier = float(2 * (1 - expit(margin)) ** 2)
                        accuracy = float(1 if margin > 0 else (0 if margin < 0 else 0.5))
                        max_margin = max(max_margin, close(margin, float(row["truth_margin"]), "margin"))
                        max_nll = max(max_nll, close(nll, float(row["two_class_nll"]), "NLL"))
                        close(brier, float(row["brier"]), "Brier")
                        close(accuracy, float(row["accuracy"]), "accuracy", rtol=0, atol=0)
                        count += 1
        if pi % 21 == 0:
            print("SPX_G0_INDEPENDENT_PAIR", panel, pi, flush=True)
    if count != len(target_rows):
        raise RuntimeError("incomplete independent target refit")
    indexed = {(r["panel"], int(r["pair_index"]), r["protocol"]): r for r in
               table(folder / "SPX_G0_CENTRAL_PAIR_PROBE.csv") + table(folder / "SPX_G0_OFFSTRIP_PAIR_PROBE.csv")}
    paired = {(r["panel"], int(r["pair_index"])): r for r in table(folder / "SPX_G0_PAIRED_PROBE_EFFECT.csv")}
    max_pair = 0.0
    for pair in pairs:
        panel, pi = pair["panel"], int(pair["pair_index"])
        for protocol in ("P_G1A", "P_E2"):
            row = indexed[(panel, pi, protocol)]
            means = {}
            for model, key in (("FULL", "full_nll"), ("BLOCK_PRODUCT", "bp_nll"), ("MATCHED_BLOCK_DIAG", "mbd_nll")):
                values = [float(target_lookup[(panel, pi, protocol, s, r, model)]["two_class_nll"])
                          for s in range(2) for r in range(16)]
                means[model] = float(np.mean(values))
                max_pair = max(max_pair, close(means[model], float(row[key]), "pair NLL"))
            close(means["BLOCK_PRODUCT"] - means["FULL"], float(row["delta_bp"]), "pair delta BP")
            close(means["MATCHED_BLOCK_DIAG"] - means["FULL"], float(row["delta_mbd"]), "pair delta MBD")
        probe_row = paired[(panel, pi)]
        g = indexed[(panel, pi, "P_G1A")]
        e = indexed[(panel, pi, "P_E2")]
        for comparator in ("bp", "mbd"):
            close(float(e[f"delta_{comparator}"]) - float(g[f"delta_{comparator}"]),
                  float(probe_row[f"probe_effect_{comparator}"]), "paired probe effect")
    central = [paired[("CENTRAL", i)] for i in range(84)]
    offstrip = [paired[("OFFSTRIP", i)] for i in range(3)]
    rng = np.random.default_rng(lock["config"]["bootstrap_seed"])
    indices = rng.integers(0, 84, size=(lock["config"]["bootstrap_draws"], 84))
    rules = {}
    with np.load(folder / "SPX_G0_PAIR_BOOTSTRAP_10000.npz", allow_pickle=False) as bootstrap:
        for name in ("BP", "MBD"):
            key = name.lower()
            cg = np.array([float(row[f"delta_{key}_p_g1a"]) for row in central])
            ce = np.array([float(row[f"delta_{key}_p_e2"]) for row in central])
            og = np.array([float(row[f"delta_{key}_p_g1a"]) for row in offstrip])
            oe = np.array([float(row[f"delta_{key}_p_e2"]) for row in offstrip])
            paired_delta = ce - cg
            mean_boot = paired_delta[indices].mean(axis=1)
            median_boot = np.median(paired_delta[indices], axis=1)
            if not np.array_equal(mean_boot, bootstrap[f"{key}_probe_mean"]) or not np.array_equal(median_boot, bootstrap[f"{key}_probe_median"]):
                raise RuntimeError("bootstrap mismatch")
            summary = result["comparators"][name]
            joint_positive = int(((cg > 0) & (ce > 0)).sum())
            joint_negative = int(((og <= 0) & (oe <= 0)).sum())
            reversals = int(((cg > 0) != (ce > 0)).sum())
            off_direction = int((np.sign(oe - og) == np.sign(np.median(paired_delta))).sum()) if np.median(paired_delta) != 0 else 0
            contrast = abs(float(np.median((cg + ce) / 2) - np.median((og + oe) / 2)))
            magnitude = abs(float(np.median(paired_delta)))
            for actual, field in ((joint_positive, "central_both_positive_count"),
                                  (joint_negative, "offstrip_both_nonpositive_count"),
                                  (reversals, "central_sign_reversal_count"),
                                  (off_direction, "offstrip_probe_effect_same_direction_count"),
                                  (contrast, "source_regime_contrast_abs"),
                                  (magnitude, "probe_effect_magnitude_abs"),
                                  (float(spearmanr(cg, ce).statistic), "central_cross_probe_spearman")):
                close(float(actual), float(summary[field]), field)
            for actual, field in ((np.quantile(mean_boot, [.025, .975]), "central_probe_effect_mean_ci95"),
                                  (np.quantile(median_boot, [.025, .975]), "central_probe_effect_median_ci95")):
                if not np.allclose(actual, summary[field], rtol=0, atol=1e-12):
                    raise RuntimeError(f"{field} mismatch")
            rules[name] = {"source_regime": joint_positive >= 51 and joint_negative >= 2 and magnitude < contrast,
                           "probe_protocol": reversals >= 34 and off_direction >= 2 and magnitude > contrast}
    if rules != result["diagnosis_rules"]:
        raise RuntimeError("diagnosis gate mismatch")
    expected = ("SPX_G0_SOURCE_REGIME_DOMINANT" if all(rules[c]["source_regime"] for c in rules) else
                "SPX_G0_PROBE_PROTOCOL_DOMINANT" if all(rules[c]["probe_protocol"] for c in rules) else
                "SPX_G0_SOURCE_PROBE_INTERACTION")
    if expected != result["decision"]:
        raise RuntimeError("decision mismatch")
    output = {"independent_recomputation": "PASS", "decision": expected,
              "target_models_refit": count, "pairs_verified": 87,
              "max_margin_difference": max_margin, "max_truth_nll_difference": max_nll,
              "max_pair_nll_difference": max_pair, "bootstrap_draws_recomputed": len(indices),
              "diagnosis_rules": rules, "sealed_data_read": False}
    (folder / "SPX_G0_INDEPENDENT_RECOMPUTATION.json").write_bytes((json.dumps(output, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    print("SPX_G0_INDEPENDENT_RECOMPUTATION_PASS", expected)


if __name__ == "__main__":
    main()

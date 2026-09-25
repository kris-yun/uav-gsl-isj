#!/usr/bin/env python3
"""Frozen two-source SPX-G0 FULL/BP/MBD crossed diagnostic."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
from pathlib import Path

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np
from scipy.special import expit, logsumexp
from scipy.stats import spearmanr, trim_mean
from sklearn.covariance import OAS
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

EVIDENCE_REL = Path("evidence/source_probe_crossed_audit_v0")
CENTRAL_PANEL_REL = Path("evidence/causal_emergent_source_scale_v0/d1r/CESS_D1R_PANEL_168.tsv")
OFFSTRIP_PANEL_REL = Path("evidence/environment_level_benchmark_v0/e1/E1_HOUSE_SOURCE_PANELS.tsv")
NPG_PAIRS_REL = Path("evidence/neural_population_geometry_v0/g0/NPG_G0_PAIR_DEFINITION.csv")
FOLDS = ((0, 4, 8, 12), (1, 5, 9, 13), (2, 6, 10, 14), (3, 7, 11, 15))
MODEL_NAMES = ("FULL", "BLOCK_PRODUCT", "MATCHED_BLOCK_DIAG")
PROTOCOLS = ("P_G1A", "P_E2")
COMPARATORS = ("BP", "MBD")
CONFIG = {
    "physical_environment": "House02 / 3,5-1_slow only",
    "pairs": "84 frozen NPG horizontal CENTRAL pairs and 3 frozen E1 OFFSTRIP pairs, each at 0.3 m",
    "folds": [list(fold) for fold in FOLDS],
    "reference_test": "12 reference and 4 held-out realizations per source per fold",
    "observation": "raw ppm, 10x30, five contiguous two-time blocks",
    "preprocessing": "for each pair/protocol/fold, StandardScaler and PCA(n_components=2, svd_solver=full) independently on 24 pair reference samples per 60-D two-time block; retain rank-deficient blocks with deterministic sklearn full SVD; no additional z scaling, pair removal or data substitution",
    "density": "source-specific sklearn OAS(assume_centered=False, store_precision=False); jitter 1e-10*max(1,trace(covariance)/dimension) on diagonal",
    "FULL": "two 10-D OAS Gaussians",
    "BP": "five independent 2-D source-specific OAS Gaussians, one per block, product likelihood",
    "MBD": "block-diagonal of the FULL post-jitter covariance; identical FULL means and fitted block marginals",
    "prior": "uniform over the two pair members",
    "margin": "log p(y|true source) minus log p(y|the other pair member)",
    "NLL": "logaddexp(0,-margin) under uniform two-source prior",
    "Brier": "two-class sum of squared probability errors =2*(1-sigmoid(margin))^2",
    "pair_aggregation": "mean across 4 held-out realizations within each source direction, then equal mean of two directions, equivalently 32 outcomes per pair/protocol",
    "probe_effect": "pair delta(P_E2) minus pair delta(P_G1A) using the same 32 raw realizations",
    "positive_sign": "strictly greater than zero; exact zero is non-positive",
    "source_regime_rule": "for each BP and MBD: >=ceil(0.60*84)=51 CENTRAL pairs positive under both probes; >=2/3 OFFSTRIP pairs non-positive under both; abs(CENTRAL median paired probe effect) < abs(CENTRAL median pair delta averaged across probes - OFFSTRIP median pair delta averaged across probes)",
    "probe_protocol_rule": "for each BP and MBD: >=ceil(0.40*84)=34 CENTRAL pair signs reverse under probe switch; >=2/3 OFFSTRIP paired probe effects share the sign of CENTRAL median paired effect; abs(CENTRAL median paired effect) > abs(CENTRAL median mean-of-probes delta - OFFSTRIP median mean-of-probes delta)",
    "diagnosis_priority": "SOURCE_REGIME_DOMINANT, then PROBE_PROTOCOL_DOMINANT, otherwise SOURCE_PROBE_INTERACTION",
    "bootstrap_seed": 202609251,
    "bootstrap_draws": 10000,
    "bootstrap_unit": "84 CENTRAL disjoint pair units, resample pairs with replacement; 95% percentile intervals for paired probe-effect mean and median",
    "heavy_tail_trim": "10% and 20% scipy.stats.trim_mean over per-target delta",
    "no_science_tuning_after_lock": True,
}


def sha(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            value.update(block)
    return value.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_bytes((json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8"))


def rows(path: Path, delimiter: str = ",") -> list[dict]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter=delimiter))


def write_csv(path: Path, data: list[dict]) -> None:
    if not data:
        raise RuntimeError(f"empty output: {path}")
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(data[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(data)


def pair_table(repo: Path) -> list[dict]:
    panel = rows(repo / CENTRAL_PANEL_REL, "\t")
    npg = rows(repo / NPG_PAIRS_REL)
    if len(panel) != 168 or len(npg) != 84:
        raise RuntimeError("frozen CENTRAL panel/pair count mismatch")
    pairs = []
    for row in npg:
        left, right = int(row["left_index"]), int(row["right_index"])
        if row["left_source_id"] != panel[left]["source_id"] or row["right_source_id"] != panel[right]["source_id"]:
            raise RuntimeError("CENTRAL NPG pair-source mismatch")
        if abs(float(row["distance_m"]) - .3) > 1e-6:
            raise RuntimeError("nonadjacent CENTRAL pair")
        pairs.append({"panel": "CENTRAL", "pair_index": int(row["pair_index"]), "source0_index": left,
                      "source1_index": right, "source0_id": row["left_source_id"],
                      "source1_id": row["right_source_id"], "distance_m": float(row["distance_m"])})
    offstrip = [row for row in rows(repo / OFFSTRIP_PANEL_REL, "\t") if row["house"] == "House02"]
    if len(offstrip) != 6:
        raise RuntimeError("OFFSTRIP source count mismatch")
    for pair_index in range(3):
        a, b = offstrip[2 * pair_index:2 * pair_index + 2]
        if (a["pair_id"], b["pair_id"], a["role"], b["role"]) != (str(pair_index + 1), str(pair_index + 1), "anchor", "partner"):
            raise RuntimeError("OFFSTRIP pair contract mismatch")
        distance = ((float(a["x_m"]) - float(b["x_m"])) ** 2 +
                    (float(a["y_m"]) - float(b["y_m"])) ** 2) ** 0.5
        if abs(distance - .3) > 1e-6:
            raise RuntimeError("nonadjacent OFFSTRIP pair")
        pairs.append({"panel": "OFFSTRIP", "pair_index": pair_index, "source0_index": 2 * pair_index,
                      "source1_index": 2 * pair_index + 1, "source0_id": a["source_id"],
                      "source1_id": b["source_id"], "distance_m": distance})
    return pairs


def tensor_paths(out: Path) -> dict[tuple[str, str], Path]:
    return {(panel, protocol): out / f"SPX_G0_{panel}_{protocol}_10x30.npy"
            for panel in ("CENTRAL", "OFFSTRIP") for protocol in PROTOCOLS}


def preflight(repo: Path) -> tuple[dict, dict[tuple[str, str], Path], list[dict]]:
    out = repo / EVIDENCE_REL
    a0 = json.loads((out / "SPX_G0_A0_COMPATIBILITY.json").read_text(encoding="utf-8"))
    if a0["decision"] != "SPX_G0_A0_COMPATIBLE":
        raise RuntimeError("A0 not compatible")
    paths = tensor_paths(out)
    for (panel, protocol), path in paths.items():
        record = a0["crossed_tensors"][f"{panel}_{protocol}"]
        if sha(path) != record["sha256"]:
            raise RuntimeError(f"crossed tensor SHA mismatch: {path}")
    pairs = pair_table(repo)
    if len(pairs) != 87:
        raise RuntimeError("pair count mismatch")
    return a0, paths, pairs


def prepare(repo: Path) -> None:
    branch = subprocess.check_output(["git", "-C", str(repo), "branch", "--show-current"], text=True).strip()
    if branch != "research/source-probe-crossed-audit-20260925":
        raise RuntimeError("wrong branch")
    a0, paths, pairs = preflight(repo)
    out = repo / EVIDENCE_REL
    lock = out / "SPX_G0_PRE_SCORE_LOCK.json"
    if lock.exists():
        raise RuntimeError("refuse to overwrite pre-score lock")
    pair_path = out / "SPX_G0_FROZEN_PAIRS.csv"
    write_csv(pair_path, pairs)
    write_json(lock, {"branch": branch, "a0_sha256": sha(out / "SPX_G0_A0_COMPATIBILITY.json"),
                      "asset_audit_sha256": a0["asset_audit_sha256"],
                      "code_sha256": sha(Path(__file__)),
                      "charter_sha256": sha(repo / "research/source_probe_crossed_audit_v0/SPX_G0_CHARTER_20260925.md"),
                      "pairs_sha256": sha(pair_path),
                      "crossed_tensor_sha256": {f"{panel}_{protocol}": sha(path) for (panel, protocol), path in paths.items()},
                      "config": CONFIG,
                      "score_calculated_before_lock": False})
    print("SPX_G0_PRE_SCORE_LOCK_WRITTEN", sha(lock), len(pairs))


def log_gaussian(x: np.ndarray, mean: np.ndarray, covariance: np.ndarray) -> np.ndarray:
    residual = x - mean
    sign, logdet = np.linalg.slogdet(covariance)
    if sign != 1:
        raise RuntimeError("nonpositive covariance")
    quadratic = np.einsum("ni,ni->n", residual, np.linalg.solve(covariance, residual.T).T)
    return -.5 * (x.shape[1] * np.log(2 * np.pi) + logdet + quadratic)


def oas(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    model = OAS(assume_centered=False, store_precision=False).fit(values)
    cov = model.covariance_.copy()
    d = cov.shape[0]
    cov.flat[::d + 1] += 1e-10 * max(1.0, float(np.trace(cov)) / d)
    return model.location_.copy(), cov


def transformed(pair_values: np.ndarray, references: list[int]) -> np.ndarray:
    z = np.empty((2, 16, 10), dtype=np.float64)
    for block in range(5):
        raw = pair_values[:, :, 2 * block:2 * block + 2, :].reshape(2, 16, 60)
        training = raw[:, references].reshape(24, 60)
        scaling = StandardScaler().fit(training)
        pca = PCA(n_components=2, svd_solver="full").fit(scaling.transform(training))
        z[:, :, 2 * block:2 * block + 2] = pca.transform(scaling.transform(raw.reshape(32, 60))).reshape(2, 16, 2)
    return z


def pair_fold_scores(pair_values: np.ndarray, eval_indices: tuple[int, ...]) -> dict[str, np.ndarray]:
    references = [i for i in range(16) if i not in eval_indices]
    z = transformed(pair_values, references)
    test = z[:, list(eval_indices)].reshape(8, 10)
    train = z[:, references]
    full = [oas(train[source]) for source in range(2)]
    predictions = {name: np.empty((8, 2), dtype=np.float64) for name in MODEL_NAMES}
    for source in range(2):
        mean, cov = full[source]
        predictions["FULL"][:, source] = log_gaussian(test, mean, cov)
        matched = np.zeros_like(cov)
        for block in range(5):
            sl = slice(2 * block, 2 * block + 2)
            matched[sl, sl] = cov[sl, sl]
        predictions["MATCHED_BLOCK_DIAG"][:, source] = log_gaussian(test, mean, matched)
        likelihood = np.zeros(8)
        for block in range(5):
            sl = slice(2 * block, 2 * block + 2)
            block_mean, block_cov = oas(train[source, :, sl])
            likelihood += log_gaussian(test[:, sl], block_mean, block_cov)
        predictions["BLOCK_PRODUCT"][:, source] = likelihood
    return predictions


def score(repo: Path) -> None:
    out = repo / EVIDENCE_REL
    lock_path = out / "SPX_G0_PRE_SCORE_LOCK.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    a0, paths, pairs = preflight(repo)
    if (lock["a0_sha256"] != sha(out / "SPX_G0_A0_COMPATIBILITY.json") or
            lock["asset_audit_sha256"] != a0["asset_audit_sha256"] or
            lock["code_sha256"] != sha(Path(__file__)) or
            lock["pairs_sha256"] != sha(out / "SPX_G0_FROZEN_PAIRS.csv") or
            lock["config"] != CONFIG):
        raise RuntimeError("frozen pre-score lock mismatch")
    for key, expected in lock["crossed_tensor_sha256"].items():
        panel, protocol = key.split("_P_", 1)
        if sha(paths[(panel, "P_" + protocol)]) != expected:
            raise RuntimeError("frozen tensor hash mismatch")
    if subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain"], text=True).strip():
        raise RuntimeError("scoring requires committed clean checkout")
    if (out / "SPX_G0_RESULT.json").exists():
        raise RuntimeError("refuse result overwrite")
    tensors = {key: np.load(path, allow_pickle=False) for key, path in paths.items()}
    target_rows = []
    pair_rows = []
    direction_rows = []
    for pair in pairs:
        panel = pair["panel"]
        source_indices = [int(pair["source0_index"]), int(pair["source1_index"])]
        for protocol in PROTOCOLS:
            pair_values = tensors[(panel, protocol)][source_indices]
            model_records = {name: [] for name in MODEL_NAMES}
            for fold, test_indices in enumerate(FOLDS):
                likelihoods = pair_fold_scores(pair_values, test_indices)
                truth = np.repeat(np.arange(2), 4)
                for name, ll in likelihoods.items():
                    margin = ll[np.arange(8), truth] - ll[np.arange(8), 1 - truth]
                    nll = np.logaddexp(0, -margin)
                    probability = expit(margin)
                    brier = 2 * (1 - probability) ** 2
                    accuracy = (margin > 0).astype(float) + .5 * (margin == 0)
                    for position in range(8):
                        source_direction = int(truth[position])
                        replicate = test_indices[position % 4]
                        row = {"panel": panel, "pair_index": pair["pair_index"], "protocol": protocol,
                               "fold": fold, "source_direction": source_direction,
                               "source_id": pair[f"source{source_direction}_id"],
                               "replicate_index": replicate, "model": name,
                               "truth_margin": float(margin[position]),
                               "two_class_nll": float(nll[position]),
                               "brier": float(brier[position]), "accuracy": float(accuracy[position])}
                        target_rows.append(row)
                        model_records[name].append(row)
            mean_nll = {name: float(np.mean([row["two_class_nll"] for row in model_records[name]])) for name in MODEL_NAMES}
            summary = {"panel": panel, "pair_index": pair["pair_index"], "protocol": protocol,
                       "source0_id": pair["source0_id"], "source1_id": pair["source1_id"],
                       "distance_m": pair["distance_m"], "target_count": 32,
                       "full_nll": mean_nll["FULL"], "bp_nll": mean_nll["BLOCK_PRODUCT"],
                       "mbd_nll": mean_nll["MATCHED_BLOCK_DIAG"],
                       "delta_bp": mean_nll["BLOCK_PRODUCT"] - mean_nll["FULL"],
                       "delta_mbd": mean_nll["MATCHED_BLOCK_DIAG"] - mean_nll["FULL"]}
            for name in MODEL_NAMES:
                summary[f"{name.lower()}_accuracy"] = float(np.mean([row["accuracy"] for row in model_records[name]]))
                summary[f"{name.lower()}_brier"] = float(np.mean([row["brier"] for row in model_records[name]]))
            pair_rows.append(summary)
            for source_direction in range(2):
                subsets = {name: [row for row in model_records[name] if row["source_direction"] == source_direction]
                           for name in MODEL_NAMES}
                direction_rows.append({"panel": panel, "pair_index": pair["pair_index"], "protocol": protocol,
                                       "source_direction": source_direction,
                                       "source_id": pair[f"source{source_direction}_id"],
                                       "delta_bp": float(np.mean([r["two_class_nll"] for r in subsets["BLOCK_PRODUCT"]]) -
                                                         np.mean([r["two_class_nll"] for r in subsets["FULL"]])),
                                       "delta_mbd": float(np.mean([r["two_class_nll"] for r in subsets["MATCHED_BLOCK_DIAG"]]) -
                                                          np.mean([r["two_class_nll"] for r in subsets["FULL"]]))})
        if pair["pair_index"] % 14 == 0:
            print("SPX_G0_PAIR_SCORED", panel, pair["pair_index"], flush=True)
    write_csv(out / "SPX_G0_TARGET_METRICS.csv", target_rows)
    write_csv(out / "SPX_G0_SOURCE_DIRECTION.csv", direction_rows)
    write_csv(out / "SPX_G0_CENTRAL_PAIR_PROBE.csv", [row for row in pair_rows if row["panel"] == "CENTRAL"])
    write_csv(out / "SPX_G0_OFFSTRIP_PAIR_PROBE.csv", [row for row in pair_rows if row["panel"] == "OFFSTRIP"])
    index = {(row["panel"], row["pair_index"], row["protocol"]): row for row in pair_rows}
    paired = []
    for pair in pairs:
        panel, pi = pair["panel"], pair["pair_index"]
        g = index[(panel, pi, "P_G1A")]
        e = index[(panel, pi, "P_E2")]
        paired.append({"panel": panel, "pair_index": pi,
                       "delta_bp_p_g1a": g["delta_bp"], "delta_bp_p_e2": e["delta_bp"],
                       "probe_effect_bp": e["delta_bp"] - g["delta_bp"],
                       "delta_mbd_p_g1a": g["delta_mbd"], "delta_mbd_p_e2": e["delta_mbd"],
                       "probe_effect_mbd": e["delta_mbd"] - g["delta_mbd"],
                       "bp_sign_agreement": (g["delta_bp"] > 0) == (e["delta_bp"] > 0),
                       "mbd_sign_agreement": (g["delta_mbd"] > 0) == (e["delta_mbd"] > 0)})
    write_csv(out / "SPX_G0_PAIRED_PROBE_EFFECT.csv", paired)
    central = [row for row in paired if row["panel"] == "CENTRAL"]
    offstrip = [row for row in paired if row["panel"] == "OFFSTRIP"]
    rng = np.random.default_rng(CONFIG["bootstrap_seed"])
    sampled = rng.integers(0, 84, size=(CONFIG["bootstrap_draws"], 84))
    bootstrap = {}
    summaries = {}
    rules = {}
    for comparator in COMPARATORS:
        lower = comparator.lower()
        c0 = np.array([row[f"delta_{lower}_p_g1a"] for row in central])
        c1 = np.array([row[f"delta_{lower}_p_e2"] for row in central])
        o0 = np.array([row[f"delta_{lower}_p_g1a"] for row in offstrip])
        o1 = np.array([row[f"delta_{lower}_p_e2"] for row in offstrip])
        effect = c1 - c0
        boot_mean = effect[sampled].mean(axis=1)
        boot_median = np.median(effect[sampled], axis=1)
        bootstrap[f"{lower}_probe_mean"] = boot_mean
        bootstrap[f"{lower}_probe_median"] = boot_median
        source_contrast = abs(float(np.median((c0 + c1) / 2) - np.median((o0 + o1) / 2)))
        probe_magnitude = abs(float(np.median(effect)))
        central_both_positive = int(((c0 > 0) & (c1 > 0)).sum())
        offstrip_both_nonpositive = int(((o0 <= 0) & (o1 <= 0)).sum())
        central_sign_reversal = int(((c0 > 0) != (c1 > 0)).sum())
        same_direction_offstrip = int((np.sign(o1 - o0) == np.sign(np.median(effect))).sum()) if np.median(effect) != 0 else 0
        rules[comparator] = {"source_regime": (central_both_positive >= 51 and offstrip_both_nonpositive >= 2 and probe_magnitude < source_contrast),
                             "probe_protocol": (central_sign_reversal >= 34 and same_direction_offstrip >= 2 and probe_magnitude > source_contrast)}
        summaries[comparator] = {
            "central_both_positive_count": central_both_positive,
            "offstrip_both_nonpositive_count": offstrip_both_nonpositive,
            "central_sign_reversal_count": central_sign_reversal,
            "offstrip_probe_effect_same_direction_count": same_direction_offstrip,
            "central_probe_effect_median": float(np.median(effect)),
            "central_probe_effect_mean": float(np.mean(effect)),
            "central_probe_effect_mean_ci95": np.quantile(boot_mean, [.025, .975]).tolist(),
            "central_probe_effect_median_ci95": np.quantile(boot_median, [.025, .975]).tolist(),
            "source_regime_contrast_abs": source_contrast,
            "probe_effect_magnitude_abs": probe_magnitude,
            "central_cross_probe_spearman": float(spearmanr(c0, c1).statistic),
            "central_pair_mean_delta_p_g1a": float(c0.mean()),
            "central_pair_mean_delta_p_e2": float(c1.mean()),
            "offstrip_pair_mean_delta_p_g1a": float(o0.mean()),
            "offstrip_pair_mean_delta_p_e2": float(o1.mean()),
            "offstrip_pair_deltas": [{"pair_index": i, "p_g1a": float(o0[i]), "p_e2": float(o1[i])} for i in range(3)],
        }
    np.savez_compressed(out / "SPX_G0_PAIR_BOOTSTRAP_10000.npz", **bootstrap, seed=np.array(CONFIG["bootstrap_seed"]))
    tail = []
    target_index = {(row["panel"], row["pair_index"], row["protocol"], row["source_direction"], row["replicate_index"], row["model"]): row
                    for row in target_rows}
    for panel in ("CENTRAL", "OFFSTRIP"):
        for protocol in PROTOCOLS:
            for comparator, name in (("BP", "BLOCK_PRODUCT"), ("MBD", "MATCHED_BLOCK_DIAG")):
                deltas = []
                for row in target_rows:
                    if row["panel"] == panel and row["protocol"] == protocol and row["model"] == name:
                        key = (panel, row["pair_index"], protocol, row["source_direction"], row["replicate_index"], "FULL")
                        deltas.append(row["two_class_nll"] - target_index[key]["two_class_nll"])
                values = np.asarray(deltas)
                tail.append({"panel": panel, "protocol": protocol, "comparator": comparator,
                             "count": len(values), "mean": float(values.mean()),
                             "median": float(np.median(values)),
                             "trimmed_10_mean": float(trim_mean(values, .1)),
                             "trimmed_20_mean": float(trim_mean(values, .2)),
                             "minimum": float(values.min()), "maximum": float(values.max())})
    write_csv(out / "SPX_G0_TAIL_SUMMARY.csv", tail)
    if all(rules[c]["source_regime"] for c in COMPARATORS):
        decision = "SPX_G0_SOURCE_REGIME_DOMINANT"
    elif all(rules[c]["probe_protocol"] for c in COMPARATORS):
        decision = "SPX_G0_PROBE_PROTOCOL_DOMINANT"
    else:
        decision = "SPX_G0_SOURCE_PROBE_INTERACTION"
    result = {"decision": decision, "diagnosis_rules": rules, "comparators": summaries,
              "central_pairs": 84, "offstrip_pairs": 3, "new_plume_runs": 0,
              "a0_reproduction": a0["historical_reproduction"],
              "pre_score_lock_sha256": sha(lock_path),
              "scope": "House02 3,5-1_slow 0.3m two-source conditional pairs; H02 W2 distant aliasing excluded",
              "sealed_data_read": False,
              "main_innovation_status": "diagnostic only; JTD and NPG STOP remain unchanged"}
    write_json(out / "SPX_G0_RESULT.json", result)
    print("SPX_G0_DECISION", decision, flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["prepare", "score"])
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.phase == "prepare":
        prepare(repo)
    else:
        score(repo)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Independent numerical recomputation of the frozen SOLICM-G0 result."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import f1_score

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "evidence/solicm_v0/g0"
VARIANTS = ("SOURCE_ONLY", "PL_ONLY", "LCA_NO_ALIGN", "LCA_FULL")
DIRECTIONS = ("W0_to_W2", "W2_to_W0")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    lock = json.loads((OUT / "SOLICM_G0_PRE_SCORE_LOCK.json").read_text())
    assert sha(Path(__file__).resolve()) == lock["independent_verifier_sha256"]
    logits = np.load(OUT / "SOLICM_G0_TARGET_LOGITS.npy").astype(np.float64)
    assert logits.shape == (2, 4, 3, 4, 24, 6)
    exported_prob = np.load(OUT / "SOLICM_G0_TARGET_PROBABILITIES.npy")
    assert exported_prob.shape == logits.shape
    e = np.exp(logits - logits.max(axis=-1, keepdims=True))
    assert np.allclose(exported_prob, e / e.sum(axis=-1, keepdims=True), atol=1e-12)
    labels = np.repeat(np.arange(6), 4)
    target_rows = list(csv.DictReader((OUT / "SOLICM_G0_TARGET_METRICS.csv").open(newline="")))
    assert len(target_rows) == 2 * 4 * 3 * 4 * 24
    run_rows = list(csv.DictReader((OUT / "SOLICM_G0_RUN_METRICS.csv").open(newline="")))
    assert len(run_rows) == 96
    row_i = 0
    run_i = 0
    for d in range(2):
        for fold in range(4):
            for seed in range(3):
                for v, variant in enumerate(VARIANTS):
                    x = logits[d, fold, seed, v]
                    e = np.exp(x - x.max(axis=1, keepdims=True))
                    p = e / e.sum(axis=1, keepdims=True)
                    rr = run_rows[run_i]
                    run_i += 1
                    assert rr["direction"] == DIRECTIONS[d] and rr["variant"] == variant
                    assert int(rr["fold"]) == fold and int(rr["seed"]) == seed
                    assert abs(float(rr["macro_f1"]) - f1_score(labels, x.argmax(axis=1), labels=list(range(6)), average="macro", zero_division=0)) < 5e-6
                    for i, truth in enumerate(labels):
                        row = target_rows[row_i]
                        row_i += 1
                        partner = truth + 1 if truth % 2 == 0 else truth - 1
                        rank = 1 + int((x[i] > x[i, truth]).sum())
                        pair_p = p[i, truth] / (p[i, truth] + p[i, partner])
                        expected = {
                            "nll": -np.log(p[i, truth]),
                            "brier": ((p[i] - np.eye(6)[truth]) ** 2).sum(),
                            "accuracy": int(x[i].argmax() == truth),
                            "truth_rank": rank,
                            "top3": int(rank <= 3),
                            "entropy": -(p[i] * np.log(p[i])).sum(),
                            "truth_vs_partner_log_odds": x[i, truth] - x[i, partner],
                            "pair_restricted_brier": 2 * (1 - pair_p) ** 2,
                            "pair_restricted_accuracy": int(pair_p > .5),
                        }
                        assert row["direction"] == DIRECTIONS[d] and row["variant"] == variant
                        assert int(row["fold"]) == fold and int(row["seed"]) == seed
                        assert int(row["source_index"]) == truth and int(row["replicate_index"]) == fold*4+i%4
                        for metric, value in expected.items():
                            assert abs(float(row[metric]) - value) < 5e-6, (metric, d, fold, seed, v, i)
    unit_nll = np.empty((2, 6, 4), dtype=np.float64)
    unit_brier = np.empty_like(unit_nll)
    unit_accuracy = np.empty_like(unit_nll)
    for d in range(2):
        for v in range(4):
            # Each fold evaluates four realizations of each of six sources.
            fold_by_source = [[], [], [], [], [], []]
            for fold in range(4):
                for seed in range(3):
                    x = logits[d, fold, seed, v]
                    e = np.exp(x - x.max(axis=1, keepdims=True))
                    p = e / e.sum(axis=1, keepdims=True)
                    nll = -np.log(p[np.arange(24), labels])
                    brier = ((p - np.eye(6)[labels]) ** 2).sum(axis=1)
                    accuracy = (x.argmax(axis=1) == labels).astype(np.float64)
                    for s in range(6):
                        fold_by_source[s].append((nll[4*s:4*s+4],
                                                  brier[4*s:4*s+4],
                                                  accuracy[4*s:4*s+4]))
            for s in range(6):
                unit_nll[d, s, v] = np.mean([a.mean() for a, _, _ in fold_by_source[s]])
                unit_brier[d, s, v] = np.mean([b.mean() for _, b, _ in fold_by_source[s]])
                unit_accuracy[d, s, v] = np.mean([c.mean() for _, _, c in fold_by_source[s]])
    da = unit_nll[:, :, 2] - unit_nll[:, :, 3]
    dp = unit_nll[:, :, 1] - unit_nll[:, :, 3]
    saved = json.loads((OUT / "SOLICM_G0_RESULT.json").read_text())
    rows = list(csv.DictReader((OUT / "SOLICM_G0_DIRECTION_SOURCE_SUMMARY.csv").open(newline="")))
    assert len(rows) == 12
    for d in range(2):
        for s in range(6):
            row = rows[d*6+s]
            assert row["direction"] == DIRECTIONS[d] and int(row["source_index"]) == s
            assert abs(float(row["delta_align"]) - da[d, s]) < 5e-6
            assert abs(float(row["delta_PL"]) - dp[d, s]) < 5e-6
            for v, name in enumerate(VARIANTS):
                for metric, mat in (("nll", unit_nll), ("brier", unit_brier), ("accuracy", unit_accuracy)):
                    assert abs(float(row[f"{name}_{metric}"]) - mat[d, s, v]) < 5e-6
    boot = np.load(OUT / "SOLICM_G0_CLUSTER_BOOTSTRAP_10000.npz")
    draws = boot["cluster_draws"]
    assert draws.shape == (10000, 12) and draws.min() >= 0 and draws.max() < 12
    ci_a = np.quantile(da.reshape(-1)[draws].mean(axis=1), [.025, .975])
    ci_p = np.quantile(dp.reshape(-1)[draws].mean(axis=1), [.025, .975])
    assert np.allclose(ci_a, saved["pooled_delta_align_CI95"], atol=5e-6)
    assert np.allclose(ci_p, saved["pooled_delta_PL_CI95"], atol=5e-6)
    assert abs(da.mean() - saved["pooled_delta_align"]) < 5e-6
    assert abs(dp.mean() - saved["pooled_delta_PL"]) < 5e-6
    directions = {}
    for d, name in enumerate(DIRECTIONS):
        z = saved["directions"][name]
        assert abs(da[d].mean() - z["mean_delta_align"]) < 5e-6
        assert abs(dp[d].mean() - z["mean_delta_PL"]) < 5e-6
        assert int((da[d] > 0).sum()) == z["positive_source_units"]
        for v, variant in enumerate(VARIANTS):
            assert abs(unit_brier[d, :, v].mean() - z["mean_brier"][variant]) < 5e-6
            assert abs(unit_accuracy[d, :, v].mean() - z["accuracy"][variant]) < 5e-6
        directions[name] = {"delta_align": float(da[d].mean()),
                            "delta_PL": float(dp[d].mean()),
                            "positive_units": int((da[d] > 0).sum())}
    seed_rows = list(csv.DictReader((OUT / "SOLICM_G0_SEED_SUMMARY.csv").open(newline="")))
    assert len(seed_rows) == 6
    seed_delta = np.empty((2, 3))
    seed_ratio = np.empty((2, 3))
    for d in range(2):
        for seed in range(3):
            row = next(r for r in seed_rows if r["direction"] == DIRECTIONS[d] and int(r["seed"]) == seed)
            seed_nll = []
            for v in range(4):
                x = logits[d, :, seed, v].reshape(4 * 24, 6)
                e = np.exp(x - x.max(axis=1, keepdims=True))
                p = e / e.sum(axis=1, keepdims=True)
                truth = np.tile(labels, 4)
                value = float(-np.log(p[np.arange(96), truth]).mean())
                assert abs(value - float(row[f"{VARIANTS[v]}_nll"])) < 5e-6
                seed_nll.append(value)
            seed_delta[d, seed] = seed_nll[2] - seed_nll[3]
            seed_ratio[d, seed] = seed_nll[3] / seed_nll[2]
            assert abs(seed_delta[d, seed] - float(row["delta_align"])) < 5e-6
            assert np.isclose(seed_delta[d, seed], saved["directions"][DIRECTIONS[d]]["seed_delta_align"][seed])
    gates = {
        "G0_1": bool(np.all(da.mean(axis=1) > 0)),
        "G0_2": bool(ci_a[0] > 0),
        "G0_3": bool((da > 0).sum() >= 8 and np.all((da > 0).sum(axis=1) >= 4)),
        "G0_4": bool(np.all(dp.mean(axis=1) > 0) and ci_p[0] > 0),
        "G0_5": bool(np.all(unit_brier[:, :, 3].mean(axis=1) < unit_brier[:, :, 2].mean(axis=1))
                     and np.all(unit_brier[:, :, 3].mean(axis=1) < unit_brier[:, :, 1].mean(axis=1))
                     and np.all(unit_accuracy[:, :, 3].mean(axis=1) >=
                                np.maximum(unit_accuracy[:, :, 2].mean(axis=1),
                                           unit_accuracy[:, :, 1].mean(axis=1)) - .02)),
        "G0_6": bool(np.all(np.median(seed_delta, axis=1) > 0) and np.all(seed_ratio <= 1.10)),
    }
    decision = ("SOLICM_G0_PASS_LATENT_CAUSAL_ALIGNMENT_TRANSFER_SIGNAL" if all(gates.values()) else
                "SOLICM_G0_HOLD_UNSTABLE_NEURAL_TRANSFER_SIGNAL" if all(gates[f"G0_{i}"] for i in range(1,6)) else
                "SOLICM_G0_STOP_LATENT_CAUSAL_ALIGNMENT_NOT_SOURCE_USEFUL")
    assert gates == saved["gates"] and decision == saved["decision"]
    audit = {
        "verification": "PASS",
        "decision": decision,
        "gates": gates,
        "directions": directions,
        "pooled_delta_align_CI95": ci_a.tolist(),
        "pooled_delta_PL_CI95": ci_p.tolist(),
        "source_units": 12,
        "logits_sha256": sha(OUT / "SOLICM_G0_TARGET_LOGITS.npy"),
        "result_sha256": sha(OUT / "SOLICM_G0_RESULT.json"),
        "training_label_path_review": "Training script source_scaled_arrays constructs labels only for source domain; target loader dummy labels are ignored by upstream training_epoch; checkpoint criterion is source risk; heldout truth occurs only in scorer."
    }
    (OUT / "SOLICM_G0_INDEPENDENT_RECOMPUTATION.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
    print("INDEPENDENT_VERIFICATION", decision)


if __name__ == "__main__":
    main()

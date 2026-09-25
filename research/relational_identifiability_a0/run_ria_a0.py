#!/usr/bin/env python3
"""Frozen, staged RIA-A0 audit of the SPX crossed observations."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import rankdata, spearmanr, trim_mean

ROOT = Path(__file__).resolve().parents[2]
UP = ROOT / "evidence/source_probe_crossed_audit_v0"
OUT = ROOT / "evidence/relational_identifiability_a0"
CODE = Path(__file__).resolve()
FOLDS = ((0, 4, 8, 12), (1, 5, 9, 13), (2, 6, 10, 14), (3, 7, 11, 15))
PROTOCOLS = ("P_G1A", "P_E2")
MODELS = ("FULL", "BLOCK_PRODUCT", "MATCHED_BLOCK_DIAG")
SPX_MODELS = {"FULL": "FULL", "BLOCK_PRODUCT": "BP", "MATCHED_BLOCK_DIAG": "MBD"}
SEED = 202609260


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def jwrite(path, obj):
    path.write_bytes((json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n").encode())


def readcsv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def writecsv(path, rows):
    if not rows:
        raise ValueError("empty CSV")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def paths(panel):
    return {p: UP / f"SPX_G0_{panel}_{p}_10x30.npy" for p in PROTOCOLS}


def pairs(panel):
    return [r for r in readcsv(UP / "SPX_G0_FROZEN_PAIRS.csv") if r["panel"] == panel]


def verify_upstream():
    lock = json.loads((UP / "SPX_G0_PRE_SCORE_LOCK.json").read_text())
    assert tuple(tuple(x) for x in lock["config"]["folds"]) == FOLDS
    assert sha(UP / "SPX_G0_FROZEN_PAIRS.csv") == lock["pairs_sha256"]
    for panel in ("CENTRAL", "OFFSTRIP"):
        for p, file in paths(panel).items():
            assert sha(file) == lock["crossed_tensor_sha256"][f"{panel}_{p}"]
    assert len(pairs("CENTRAL")) == 84 and len(pairs("OFFSTRIP")) == 3
    return lock


def ref_metrics(a, b):
    ma, mb = a.mean(axis=0), b.mean(axis=0)
    s = float(np.sum((ma - mb) ** 2))
    w = float((np.sum((a - ma) ** 2, axis=1).mean() + np.sum((b - mb) ** 2, axis=1).mean()) / 2)
    def d(x, y):
        return np.sqrt(np.maximum(0, np.sum((x[:, None, :] - y[None, :, :]) ** 2, axis=2)))
    aa, bb, ab = d(a, a), d(b, b), d(a, b)
    n, m = len(a), len(b)
    wa = (aa.sum() - np.trace(aa)) / (n * (n - 1))
    wb = (bb.sum() - np.trace(bb)) / (m * (m - 1))
    we = float((wa + wb) / 2)
    ed = float(2 * ab.mean() - wa - wb)
    return {"S": s, "W": w, "D_CNR": s / (w + 1e-12 * max(1, w)),
            "ED": ed, "W_E": we, "D_ED": ed / (we + 1e-12 * max(1, we))}


def make_reference(panel):
    tensors = {p: np.load(file) for p, file in paths(panel).items()}
    expected = (168 if panel == "CENTRAL" else 6, 16, 10, 30)
    for t in tensors.values():
        assert t.shape == expected and np.isfinite(t).all()
    rows = []
    for pair in pairs(panel):
        idx = int(pair["pair_index"])
        ai, bi = int(pair["source0_index"]), int(pair["source1_index"])
        for protocol in PROTOCOLS:
            a, b = tensors[protocol][[ai, bi]].reshape(2, 16, 300)
            foldvals = []
            for fold, test in enumerate(FOLDS):
                train = [i for i in range(16) if i not in test]
                foldvals.append(ref_metrics(a[train], b[train]))
            row = {"panel": panel, "pair_index": idx, "protocol": protocol,
                   "source0_id": pair["source0_id"], "source1_id": pair["source1_id"]}
            for key in ("S", "W", "D_CNR", "ED", "W_E", "D_ED"):
                vals = np.array([v[key] for v in foldvals])
                row[key] = float(vals.mean())
                row[f"{key}_fold_min"] = float(vals.min())
                row[f"{key}_fold_max"] = float(vals.max())
                row[f"{key}_fold_std"] = float(vals.std(ddof=0))
            rows.append(row)
    return rows


def lock_stage():
    OUT.mkdir(parents=True, exist_ok=True)
    spx = verify_upstream()
    inputs = {f.name: sha(f) for f in [UP / "SPX_G0_PRE_SCORE_LOCK.json", UP / "SPX_G0_FROZEN_PAIRS.csv",
             *paths("CENTRAL").values(), *paths("OFFSTRIP").values(),
             UP / "SPX_G0_CENTRAL_PAIR_PROBE.csv", UP / "SPX_G0_OFFSTRIP_PAIR_PROBE.csv",
             UP / "SPX_G0_TARGET_METRICS.csv"]}
    lock = {"branch": "research/relational-identifiability-a0-20260926", "upstream_spx_commit":
            "666e7996b5b060516e32b2d93df0679171981745", "code_sha256": sha(CODE),
            "charter_sha256": sha(ROOT / "research/relational_identifiability_a0/RIA_A0_CHARTER_20260926.md"),
            "input_sha256": inputs, "folds_heldout": FOLDS, "bootstrap_seed": SEED,
            "bootstrap_resamples": 10000, "bootstrap_unit": "84 CENTRAL pairs",
            "normalizer_epsilon": "1e-12*max(1,W) independently for W and W_E",
            "risk_materiality": "For either BP or MBD, Spearman(delta utility, delta FULL tail excess) <= -0.30 and 10000-pair-bootstrap 95% upper bound < 0.",
            "flip_rule": "strict utility sign flip; bounded agrees when both Delta_A and Delta_B have the sign of delta utility; risk agrees when -delta FULL tail excess has that sign",
            "spx_lock_sha256": sha(UP / "SPX_G0_PRE_SCORE_LOCK.json"),
            "spx_pairs_sha256": spx["pairs_sha256"]}
    file = OUT / "RIA_A0_PRE_RUN_LOCK.json"
    if file.exists():
        assert json.loads(file.read_text()) == lock, "pre-run lock drift"
    else:
        jwrite(file, lock)
    print("PRE_RUN_LOCK", sha(file))


def reference_stage():
    lock = json.loads((OUT / "RIA_A0_PRE_RUN_LOCK.json").read_text())
    assert sha(CODE) == lock["code_sha256"]
    verify_upstream()
    output = OUT / "RIA_A0_REFERENCE_IDENTIFIABILITY.csv"
    if output.exists():
        raise RuntimeError("Reference output exists; do not overwrite")
    rows = make_reference("CENTRAL")
    writecsv(output, rows)
    jwrite(OUT / "RIA_A0_REFERENCE_FREEZE.json", {"rows": len(rows), "reference_csv_sha256": sha(output),
           "heldout_metrics_imported": False})
    print("REFERENCE_FREEZE", len(rows), sha(output))


def corr(x, y):
    r = float(spearmanr(x, y).statistic)
    return r if np.isfinite(r) else 0.0


def bootstrap(x, y, draws):
    # Pair resampling is shared across every association. Rank each resample, preserving ties.
    xr = rankdata(x[draws], axis=1)
    yr = rankdata(y[draws], axis=1)
    xr -= xr.mean(axis=1, keepdims=True)
    yr -= yr.mean(axis=1, keepdims=True)
    den = np.sqrt((xr*xr).sum(axis=1) * (yr*yr).sum(axis=1))
    vals = np.divide((xr*yr).sum(axis=1), den, out=np.zeros(len(draws)), where=den > 0)
    return float(np.quantile(vals, .025)), float(np.quantile(vals, .975)), vals


def operational(panel):
    pr = [r for r in readcsv(UP / f"SPX_G0_{panel}_PAIR_PROBE.csv")]
    grouped = {(int(r["pair_index"]), r["protocol"]): r for r in pr}
    out = []
    for pair in pairs(panel):
        idx = int(pair["pair_index"])
        byp = {}
        for p in PROTOCOLS:
            r = grouped[idx, p]
            acc = np.array([float(r[k]) for k in ("full_accuracy", "block_product_accuracy", "matched_block_diag_accuracy")])
            brier = np.array([float(r[k]) for k in ("full_brier", "block_product_brier", "matched_block_diag_brier")])
            byp[p] = {"A": float(np.median(acc)), "B": -float(np.median(brier)),
                      "utility_BP": float(r["delta_bp"]), "utility_MBD": float(r["delta_mbd"])}
        out.append({"panel": panel, "pair_index": idx,
                    **{f"{k}_{p}": v for p, d in byp.items() for k, v in d.items()},
                    **{f"Delta_{k}": byp["P_E2"][k] - byp["P_G1A"][k]
                       for k in ("A", "B", "utility_BP", "utility_MBD")}})
    return out


def risk(panel):
    target = [r for r in readcsv(UP / "SPX_G0_TARGET_METRICS.csv") if r["panel"] == panel]
    group = {}
    for r in target:
        key = (int(r["pair_index"]), r["protocol"], r["model"])
        group.setdefault(key, []).append(r)
    out = []
    for pair in pairs(panel):
        idx = int(pair["pair_index"])
        for p in PROTOCOLS:
            for model in MODELS:
                rr = group[idx, p, model]
                assert len(rr) == 32
                nll = np.array([float(r["two_class_nll"]) for r in rr])
                acc = np.array([float(r["accuracy"]) for r in rr])
                wrong = acc < .5
                mean, trimmed = float(nll.mean()), float(trim_mean(nll, .2))
                out.append({"panel": panel, "pair_index": idx, "protocol": p, "model": model,
                            "target_count": len(rr), "mean_nll": mean, "trimmed20_nll": trimmed,
                            "tail_excess": mean - trimmed, "misclassification_rate": float(wrong.mean()),
                            "mean_nll_given_error": float(nll[wrong].mean()) if wrong.any() else "",
                            "q95_nll": float(np.quantile(nll, .95)), "max_nll": float(nll.max())})
    return out


def central_stage():
    lock = json.loads((OUT / "RIA_A0_PRE_RUN_LOCK.json").read_text())
    assert sha(CODE) == lock["code_sha256"]
    frozen = json.loads((OUT / "RIA_A0_REFERENCE_FREEZE.json").read_text())
    ref_file = OUT / "RIA_A0_REFERENCE_IDENTIFIABILITY.csv"
    assert sha(ref_file) == frozen["reference_csv_sha256"]
    verify_upstream()
    ref = readcsv(ref_file)
    assert len(ref) == 168
    op = operational("CENTRAL")
    rk = risk("CENTRAL")
    writecsv(OUT / "RIA_A0_BOUNDED_OPERATIONAL.csv", op)
    writecsv(OUT / "RIA_A0_ESTIMATOR_RISK.csv", rk)
    rr = {(int(r["pair_index"]), r["protocol"]): r for r in ref}
    tails = {(int(r["pair_index"]), r["protocol"]): float(r["tail_excess"]) for r in rk if r["model"] == "FULL"}
    n = len(op)
    x = {d: np.array([float(rr[i, "P_E2"][d]) - float(rr[i, "P_G1A"][d]) for i in range(n)]) for d in ("D_CNR", "D_ED")}
    y = {d: np.array([float(r[f"Delta_{d}"]) for r in op]) for d in ("A", "B", "utility_BP", "utility_MBD")}
    tail = np.array([tails[i, "P_E2"] - tails[i, "P_G1A"] for i in range(n)])
    rng = np.random.default_rng(SEED)
    draws = rng.integers(0, n, (10000, n), dtype=np.int32)
    comparison = {("D_CNR", "A"), ("D_CNR", "B"), ("D_ED", "A"), ("D_ED", "B")}
    for model in ("BP", "MBD"):
        comparison.update({("D_CNR", f"utility_{model}"), ("D_ED", f"utility_{model}"),
                           ("TAIL", f"utility_{model}")})
    assoc = {}
    samples = {}
    for a, b in sorted(comparison):
        xx = tail if a == "TAIL" else x[a]
        yy = y[b]
        lo, hi, bs = bootstrap(xx, yy, draws)
        key = f"{a}__{b}"
        assoc[key] = {"spearman": corr(xx, yy), "bootstrap95": [lo, hi]}
        samples[key] = bs
    loo_rows = []
    for i in range(n):
        keep = np.arange(n) != i
        row = {"pair_index": i}
        for d in ("D_CNR", "D_ED"):
            for bounded in ("A", "B"):
                row[f"{d}__{bounded}_spearman"] = corr(x[d][keep], y[bounded][keep])
        loo_rows.append(row)
    writecsv(OUT / "RIA_A0_LOO_INFLUENCE.csv", loo_rows)
    q3 = {}
    for d in ("D_CNR", "D_ED"):
        positive = {b: assoc[f"{d}__{b}"]["spearman"] > 0 for b in ("A", "B")}
        lower = {b: assoc[f"{d}__{b}"]["bootstrap95"][0] > 0 for b in ("A", "B")}
        loo = {b: sum(row[f"{d}__{b}_spearman"] > 0 for row in loo_rows) / n for b in ("A", "B")}
        q3[d] = {"positive_with_both": all(positive.values()), "positive_lower_bound": lower,
                 "loo_positive_fraction": loo,
                 "passes": all(positive.values()) and any(lower[b] and loo[b] >= .95 for b in ("A", "B"))}
    risk_material = {m: assoc[f"TAIL__utility_{m}"]["spearman"] <= -.30 and
                     assoc[f"TAIL__utility_{m}"]["bootstrap95"][1] < 0 for m in ("BP", "MBD")}
    flips = {}
    source_util = {(int(r["pair_index"]), r["protocol"]): r for r in readcsv(UP / "SPX_G0_CENTRAL_PAIR_PROBE.csv")}
    for m, col in (("BP", "delta_bp"), ("MBD", "delta_mbd")):
        flip_indices = [i for i in range(n) if float(source_util[i, "P_G1A"][col]) * float(source_util[i, "P_E2"][col]) < 0]
        aligned = [i for i in flip_indices if np.sign(y["A"][i]) == np.sign(y[f"utility_{m}"][i])
                   and np.sign(y["B"][i]) == np.sign(y[f"utility_{m}"][i])]
        disagree = [i for i in flip_indices if i not in aligned and
                    np.sign(-tail[i]) == np.sign(y[f"utility_{m}"][i])]
        flips[m] = {"count": len(flip_indices), "bounded_both_agree_count": len(aligned),
                    "bounded_both_agree_fraction": len(aligned)/len(flip_indices) if flip_indices else None,
                    "bounded_disagree_tail_agrees_count": len(disagree),
                    "bounded_disagree_tail_agrees_fraction": len(disagree)/len(flip_indices) if flip_indices else None}
    decision = ("RIA_A0_PHYSICAL_IDENTIFIABILITY_TARGET_SUPPORTED" if all(v["passes"] for v in q3.values()) else
                "RIA_A0_MODEL_RISK_DOMINANT_NO_PHYSICAL_TARGET_YET" if any(risk_material.values()) else
                "RIA_A0_MIXED_OR_UNRESOLVED")
    jwrite(OUT / "RIA_A0_ASSOCIATIONS.json", {"central_pairs": n, "associations": assoc, "q3": q3,
           "risk_materiality": risk_material, "utility_sign_flips": flips,
           "delta_summaries": {k: {"median": float(np.median(v)), "mean": float(np.mean(v))}
                                for k, v in {**x, **y, "FULL_tail_excess": tail}.items()}})
    np.savez_compressed(OUT / "RIA_A0_BOOTSTRAP_10000.npz", pair_draws=draws, **samples)
    result = {"decision": decision, "central_pairs": n, "new_plume": 0, "bootstrap_resamples": 10000,
              "reference_freeze_sha256": sha(OUT / "RIA_A0_REFERENCE_FREEZE.json"),
              "associations_sha256": sha(OUT / "RIA_A0_ASSOCIATIONS.json"),
              "offstrip_read_before_decision": False}
    jwrite(OUT / "RIA_A0_RESULT.json", result)
    print(decision)


def offstrip_stage():
    result_file = OUT / "RIA_A0_RESULT.json"
    assert result_file.exists()
    result_sha = sha(result_file)
    ref = make_reference("OFFSTRIP")
    op = operational("OFFSTRIP")
    rk = risk("OFFSTRIP")
    lookup = {(int(r["pair_index"]), r["protocol"]): r for r in ref}
    risks = {(int(r["pair_index"]), r["protocol"]): r for r in rk if r["model"] == "FULL"}
    rows = []
    for r in op:
        i = int(r["pair_index"])
        rows.append({**r,
                     "Delta_CNR": lookup[i, "P_E2"]["D_CNR"] - lookup[i, "P_G1A"]["D_CNR"],
                     "Delta_ED": lookup[i, "P_E2"]["D_ED"] - lookup[i, "P_G1A"]["D_ED"],
                     "Delta_FULL_tail_excess": risks[i, "P_E2"]["tail_excess"] - risks[i, "P_G1A"]["tail_excess"]})
    writecsv(OUT / "RIA_A0_OFFSTRIP_STRESS.csv", rows)
    assert sha(result_file) == result_sha, "CENTRAL decision changed"
    print("OFFSTRIP_DESCRIPTIVE_ONLY", len(rows))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=("lock", "reference", "central", "offstrip"))
    args = ap.parse_args()
    {"lock": lock_stage, "reference": reference_stage, "central": central_stage,
     "offstrip": offstrip_stage}[args.stage]()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Independent JTD-E1 null-score, target, cluster-gate and seed replay."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import trim_mean


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def close(a: float, b: float, name: str) -> None:
    if not np.isclose(a, b, atol=1e-9, rtol=0):
        raise ValueError(f"E1 independent mismatch {name}: {a} vs {b}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out
    lock = json.loads((out / "JTD_E1_PRE_RUN_LOCK.json").read_text(encoding="utf-8"))
    result = json.loads((out / "JTD_E1_RESULT.json").read_text(encoding="utf-8"))
    with (out / "JTD_E1_TARGETS.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    with (out / "JTD_E1_TARGET_MANIFEST.tsv").open(newline="", encoding="utf-8") as stream:
        manifest = list(csv.DictReader(stream, delimiter="\t"))
    if len(rows) != 36 or len(manifest) != 36 or len(lock["fresh_target_plan"]) != 36:
        raise ValueError("E1 target count drift")
    key = lambda r: (int(r["environment_index"]), int(r["source_index"]), int(r["target_replicate"]))
    row_map, manifest_map, plan_map = ({key(r): r for r in collection} for collection in
                                        (rows, manifest, lock["fresh_target_plan"]))
    if len(row_map) != 36 or set(row_map) != set(manifest_map) or set(row_map) != set(plan_map):
        raise ValueError("E1 target identity/uniqueness drift")
    reference_seeds = {int(r["requested_seed"]) for group in lock["reference_groups"] for r in group["reference_runs"]}
    target_seeds = set()
    for (ei, si, target), row in row_map.items():
        expected = 2026120000+1000*ei+10*si+target
        if int(row["requested_seed"]) != expected or int(manifest_map[(ei,si,target)]["requested_seed"]) != expected:
            raise ValueError("fresh target seed formula drift")
        if plan_map[(ei,si,target)]["requested_seed"] != expected:
            raise ValueError("pre-run target plan seed drift")
        if row["cube_sha256"] != manifest_map[(ei,si,target)]["cube_sha256"]:
            raise ValueError("fresh target cube hash label drift")
        target_seeds.add(expected)
    if len(target_seeds) != 36 or target_seeds & reference_seeds:
        raise ValueError("fresh/reference seed collision")
    reference = np.load(out / "JTD_E1_REFERENCE_10x30.npy", allow_pickle=False)
    targets = np.load(out / "JTD_E1_FRESH_TARGETS_10x30.npy", allow_pickle=False)
    if reference.shape != (3,6,4,10,30) or targets.shape != (3,6,2,10,30):
        raise ValueError("reference/target observation tensor drift")
    if sha(out / "JTD_E1_REFERENCE_10x30.npy") != lock["reference_snapshot_sha256"]:
        raise ValueError("reference snapshot hash drift")
    perm = np.load(out / "JTD_E1_NULL_DERANGEMENTS.npy", allow_pickle=False)
    if perm.shape != (3,200,6,4,4) or sha(out / "JTD_E1_NULL_DERANGEMENTS.npy") != lock["null_derangements_sha256"]:
        raise ValueError("frozen null matrix drift")
    for ei in range(3):
        for mi in range(200):
            for si in range(6):
                for b in range(1,5):
                    base = f"JTD-E1|environment={ei}|null={mi}|source={si}|block={b}"
                    seed = int.from_bytes(hashlib.sha256(base.encode("ascii")).digest()[:8], "little")
                    rng = np.random.default_rng(seed)
                    for _ in range(1000):
                        candidate = rng.permutation(4)
                        if np.all(candidate != np.arange(4)):
                            break
                    else:
                        raise ValueError("null derangement generation failed")
                    if not np.array_equal(candidate, perm[ei,mi,si,b-1]):
                        raise ValueError("null SHA key/permutation drift")
    with np.load(out / "JTD_E1_RAW_SCORES.npz", allow_pickle=False) as scores:
        full_nll, null_nll = scores["full_nll"], scores["null_nll"]
        full_loglik, null_loglik = scores["full_loglik"], scores["null_loglik"]
        full_rank, null_rank = scores["full_rank"], scores["null_rank"]
    if (full_nll.shape, null_nll.shape, full_loglik.shape, null_loglik.shape) != (
            (3,6,2), (3,200,6,2), (3,12,6), (3,200,12,6)):
        raise ValueError("raw score shape drift")
    def from_loglik(loglik: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        truth = np.repeat(np.arange(6),2)
        peak = loglik.max(axis=1, keepdims=True)
        logpost = loglik-peak-np.log(np.exp(loglik-peak).sum(axis=1, keepdims=True))
        nll = -logpost[np.arange(12),truth].reshape(6,2)
        rank = (1+np.sum(loglik > loglik[np.arange(12),truth,None],axis=1)).reshape(6,2)
        return nll, rank
    for ei in range(3):
        f_nll, f_rank = from_loglik(full_loglik[ei])
        if not np.allclose(f_nll, full_nll[ei], atol=1e-9, rtol=0) or not np.array_equal(f_rank, full_rank[ei]):
            raise ValueError("FULL raw loglikelihood inconsistency")
        for mi in range(200):
            n_nll, n_rank = from_loglik(null_loglik[ei,mi])
            if not np.allclose(n_nll, null_nll[ei,mi], atol=1e-9, rtol=0) or not np.array_equal(n_rank, null_rank[ei,mi]):
                raise ValueError("SHUFFLED raw loglikelihood inconsistency")
    null_median = np.median(null_nll, axis=1)
    delta = null_median-full_nll
    for (ei, si, target), row in row_map.items():
        close(float(row["full_truth_nll"]), full_nll[ei,si,target], "target FULL NLL")
        close(float(row["shuffled_median_truth_nll"]), null_median[ei,si,target], "target null median NLL")
        close(float(row["delta_nll"]), delta[ei,si,target], "target delta")
        if int(row["full_truth_rank"]) != full_rank[ei,si,target]:
            raise ValueError("target truth rank drift")
    rng = np.random.default_rng(2026092502)
    draws = []
    for _ in range(5000):
        selected = rng.integers(0,6,(3,6))
        draws.append(float(np.mean([delta[e,int(selected[e,i]),t]
                                    for e in range(3) for i in range(6) for t in range(2)])))
    ci = np.quantile(draws,(0.025,0.975))
    stored_boot = np.load(out / "JTD_E1_BOOTSTRAP_5000.npy", allow_pickle=False)
    if not np.allclose(draws,stored_boot,atol=1e-12,rtol=0):
        raise ValueError("cluster bootstrap draws drift")
    positives = sorted((float(x) for x in delta.ravel() if x>0),reverse=True)
    retained = list(float(x) for x in delta.ravel())
    for value in positives[:2]: retained.remove(value)
    env_means = [float(np.mean(delta[e])) for e in range(3)]
    local_positive = [int(sum(np.mean(delta[e,s])>0 for s in range(6))) for e in range(3)]
    full_means = [float(np.mean(full_nll[e])) for e in range(3)]
    null_means = [float(np.mean(null_median[e])) for e in range(3)]
    relative = float((null_median.mean()-full_nll.mean())/null_median.mean())
    gates = {"E1_G1": bool(all(v>0 for v in env_means)),
             "E1_G2": bool(ci[0]>0),
             "E1_G3": bool(sum(local_positive)>=13 and all(v>=4 for v in local_positive)),
             "E1_G4": bool(trim_mean(delta.ravel(),0.2)>0),
             "E1_G5": bool(np.mean(retained)>0),
             "E1_G6": bool(relative>=0.10),
             "E1_G7": bool(all(full_means[e]<=1.10*null_means[e] for e in range(3)))}
    failures = [e for e in range(3) if not (env_means[e]>0 and local_positive[e]>=4)]
    if all(gates.values()):
        decision = "JTD_E1_GO_CROSS_ENVIRONMENT_TEMPORAL_DEPENDENCE"
    elif all(gates[g] for g in ("E1_G2","E1_G4","E1_G5","E1_G7")) and len(failures)==1:
        decision = "JTD_E1_HOLD_ENVIRONMENT_HETEROGENEOUS_SIGNAL"
    else:
        decision = "JTD_E1_STOP_TEMPORAL_DEPENDENCE_NOT_GENERAL"
    if gates != result["gates"] or decision != result["decision"]:
        raise ValueError("independent E1 decision/gate mismatch")
    for name,value in (("pooled_mean_delta_nll",float(delta.mean())),
                       ("pooled_trimmed_20_mean_delta_nll",float(trim_mean(delta.ravel(),0.2))),
                       ("pooled_relative_mean_nll_improvement",relative),
                       ("g5_retained_mean_delta_nll",float(np.mean(retained)))):
        close(value,result[name],name)
    if not np.allclose(ci,result["cluster_bootstrap_95_ci"],atol=1e-9,rtol=0):
        raise ValueError("bootstrap CI mismatch")
    report = {"independent_recomputation_pass":True,"decision":decision,"gates":gates,
              "cluster_bootstrap_95_ci":ci.tolist(),"environment_mean_deltas":env_means,
              "positive_sources_by_environment":local_positive,
              "pooled_relative_mean_nll_improvement":relative,
              "g5_retained_mean_delta_nll":float(np.mean(retained)),
              "target_count":36,"raw_null_score_count":3*200*12,
              "target_csv_sha256":sha(out/"JTD_E1_TARGETS.csv"),
              "raw_scores_sha256":sha(out/"JTD_E1_RAW_SCORES.npz")}
    (out/"JTD_E1_INDEPENDENT_VERIFICATION.json").write_bytes(
        (json.dumps(report,indent=2,sort_keys=True)+"\n").encode("utf-8"))
    print(decision,"INDEPENDENT_VERIFICATION_PASS")


if __name__ == "__main__":
    main()

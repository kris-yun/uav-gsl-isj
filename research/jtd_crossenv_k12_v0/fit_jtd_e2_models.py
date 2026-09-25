#!/usr/bin/env python3
"""Fit and freeze all K=12 JTD-E2 models and destructive-null models before fresh targets."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import sklearn
from sklearn.covariance import OAS
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence/jtd_e2_20260925"
N_ENV, N_SOURCE, N_REF, N_NULL, DIM = 3, 6, 12, 200, 10
JITTER = 1e-10


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def save_json(path: Path, value: object) -> None:
    path.write_bytes((json.dumps(value, indent=2, sort_keys=True)+"\n").encode("utf-8"))


def fit_oas(data: np.ndarray, diagonal: bool = False) -> tuple[np.ndarray, np.ndarray, float]:
    fit = OAS(assume_centered=False, store_precision=False).fit(data)
    c = fit.covariance_.copy()
    if diagonal:
        c = np.diag(np.diag(c))
    d = c.shape[0]
    c.flat[::d+1] += JITTER*max(1.0, float(np.trace(c))/d)
    np.linalg.cholesky(c)
    return fit.location_.copy(), c, float(fit.shrinkage_)


def main() -> None:
    lock_path = EVIDENCE / "JTD_E2_INITIAL_LOCK.json"
    acquisition_path = EVIDENCE / "JTD_E2_REFERENCE_ACQUISITION.json"
    pretarget = EVIDENCE / "JTD_E2_PRE_TARGET_LOCK.json"
    if pretarget.exists() or (EVIDENCE / "JTD_E2_FRESH_TARGET_10x30.npy").exists():
        raise RuntimeError("refuse refit after E2 pre-target lock or target")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    acquisition = json.loads(acquisition_path.read_text(encoding="utf-8"))
    reference_path = EVIDENCE / "JTD_E2_REFERENCE_12x10x30.npy"
    if acquisition["reference_count"] != 216 or acquisition["reference_tensor_sha256"] != sha(reference_path):
        raise RuntimeError("E2 K12 reference acquisition incomplete")
    if acquisition["initial_lock_sha256"] != sha(lock_path):
        raise RuntimeError("E2 initial lock drift")
    x = np.load(reference_path, allow_pickle=False)
    if x.shape != (3,6,12,10,30) or x.dtype != np.float32 or not np.isfinite(x).all() or (x < 0).any():
        raise RuntimeError("E2 K12 reference shape/dtype/content drift")
    scaler_mean = np.empty((3,5,60)); scaler_scale = np.empty((3,5,60))
    pca_mean = np.empty((3,5,60)); pca_components = np.empty((3,5,2,60))
    pca_explained = np.empty((3,5,2))
    projected = np.empty((3,6,12,10))
    full_mu = np.empty((3,6,10)); full_cov = np.empty((3,6,10,10)); full_shrink = np.empty((3,6))
    bp_mu = np.empty((3,6,5,2)); bp_cov = np.empty((3,6,5,2,2)); bp_shrink = np.empty((3,6,5))
    mbd_cov = np.zeros((3,6,10,10))
    diag_mu = np.empty((3,6,10)); diag_cov = np.empty((3,6,10,10))
    for ei in range(3):
        for block in range(5):
            raw = x[ei, :, :, 2*block:2*block+2, :].reshape(72,60)
            if np.count_nonzero(np.var(raw, axis=0) > 0) < 2:
                raise RuntimeError("K12 reference PCA block lacks two dimensions")
            scaler = StandardScaler().fit(raw)
            standardized = scaler.transform(raw)
            pca = PCA(n_components=2, svd_solver="full").fit(standardized)
            projected[ei, :, :, 2*block:2*block+2] = pca.transform(standardized).reshape(6,12,2)
            scaler_mean[ei, block] = scaler.mean_
            scaler_scale[ei, block] = scaler.scale_
            pca_mean[ei, block] = pca.mean_
            pca_components[ei, block] = pca.components_
            pca_explained[ei, block] = pca.explained_variance_ratio_
        for si in range(6):
            ref = projected[ei, si]
            full_mu[ei, si], full_cov[ei, si], full_shrink[ei, si] = fit_oas(ref)
            diag_mu[ei, si], diag_cov[ei, si], _ = fit_oas(ref, diagonal=True)
            for block in range(5):
                sl = slice(2*block,2*block+2)
                bp_mu[ei, si, block], bp_cov[ei, si, block], bp_shrink[ei, si, block] = fit_oas(ref[:,sl])
                mbd_cov[ei, si, sl, sl] = full_cov[ei, si, sl, sl]
                if not np.array_equal(mbd_cov[ei, si, sl, sl], full_cov[ei, si, sl, sl]):
                    raise RuntimeError("MBD changed FULL stabilized block marginal")
            np.linalg.cholesky(mbd_cov[ei,si])
    np.savez_compressed(EVIDENCE / "JTD_E2_MODEL_LOCK.npz",
                        scaler_mean=scaler_mean, scaler_scale=scaler_scale,
                        pca_mean=pca_mean, pca_components=pca_components, pca_explained=pca_explained,
                        reference_projected=projected, full_mu=full_mu, full_cov=full_cov,
                        full_shrinkage=full_shrink, bp_mu=bp_mu, bp_cov=bp_cov, bp_shrinkage=bp_shrink,
                        mbd_cov=mbd_cov, diag_mu=diag_mu, diag_cov=diag_cov)
    source_ids = [[lock["source_groups"][6*ei+si]["source_id"] for si in range(6)] for ei in range(3)]
    seeds = np.empty((3,200,6,4), dtype=np.uint64)
    permutations = np.empty((3,200,6,4,12), dtype=np.uint8)
    null_mu = np.empty((3,200,6,10)); null_cov = np.empty((3,200,6,10,10))
    used = set()
    for ei in range(3):
        for null_id in range(N_NULL):
            for si in range(6):
                shuffled = projected[ei, si].copy()
                for block in range(1,5):
                    key = f"JTD_E2|NULL|environment_id={ei}|source_id={source_ids[ei][si]}|null_id={null_id}|block_id={block}|purpose=within_source_derangement"
                    seed = int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:8], "big")
                    if seed in used:
                        raise RuntimeError("E2 null SHA seed alias")
                    used.add(seed)
                    rng = np.random.default_rng(seed)
                    for _ in range(1000):
                        perm = rng.permutation(12)
                        if np.all(perm != np.arange(12)):
                            break
                    else:
                        raise RuntimeError("E2 null derangement generation failed")
                    seeds[ei, null_id, si, block-1] = seed
                    permutations[ei, null_id, si, block-1] = perm
                    sl = slice(2*block,2*block+2)
                    shuffled[:,sl] = projected[ei,si,perm,sl]
                    if not np.array_equal(np.sort(shuffled[:,sl],axis=0), np.sort(projected[ei,si,:,sl],axis=0)):
                        raise RuntimeError("E2 SHUFFLED block marginals changed")
                if not np.allclose(shuffled.mean(axis=0), projected[ei,si].mean(axis=0), atol=1e-12, rtol=0):
                    raise RuntimeError("E2 SHUFFLED source mean changed")
                null_mu[ei,null_id,si], null_cov[ei,null_id,si], _ = fit_oas(shuffled)
        print("JTD_E2_NULL_MODELS_FIT_ENV", ei, flush=True)
    np.savez_compressed(EVIDENCE / "JTD_E2_NULL_MODEL_LOCK.npz", seeds=seeds, permutations=permutations,
                        null_mu=null_mu, null_cov=null_cov)
    null_spec = {"source_ids_by_environment": source_ids,
                 "key_template": "JTD_E2|NULL|environment_id={ei}|source_id={source_id}|null_id={0..199}|block_id={1..4}|purpose=within_source_derangement",
                 "seed_mapping": "first eight SHA256 digest bytes big-endian uint64 -> numpy default_rng -> G0 rejection-sampled 12-derangement",
                 "unique_seed_count": len(used), "seeds_shape": list(seeds.shape),
                 "permutations_shape": list(permutations.shape),
                 "null_model_lock_sha256": sha(EVIDENCE / "JTD_E2_NULL_MODEL_LOCK.npz")}
    save_json(EVIDENCE / "JTD_E2_NULL_KEY_MANIFEST.json", null_spec)
    with (EVIDENCE / "JTD_E2_SEED_PLAN_180.tsv").open(newline="", encoding="utf-8") as f:
        plan = list(csv.DictReader(f, delimiter="\t"))
    assert len(plan) == 180 and len([r for r in plan if r["phase"]=="TARGET"]) == 72
    # Freeze the exact source geometry and tie rule before any fresh target is generated.
    nearest = []
    for ei in range(3):
        xy = np.asarray([lock["source_groups"][6*ei+si]["source_xyz"][:2] for si in range(6)])
        d = np.linalg.norm(xy[:,None,:]-xy[None,:,:], axis=2)
        np.fill_diagonal(d,np.inf)
        nearest.append(np.argmin(d,axis=1).tolist())
    score_code = ROOT / "research/jtd_crossenv_k12_v0/score_jtd_e2.py"
    if not score_code.exists():
        raise RuntimeError("scoring code must exist before pre-target lock")
    pre = {"branch": lock["branch"], "phase": "BEFORE_ANY_E2_FRESH_TARGET",
           "initial_lock_sha256": sha(lock_path),
           "reference_acquisition_sha256": sha(acquisition_path),
           "reference_tensor_sha256": sha(reference_path), "reference_count": 216,
           "model_lock_sha256": sha(EVIDENCE / "JTD_E2_MODEL_LOCK.npz"),
           "null_model_lock_sha256": sha(EVIDENCE / "JTD_E2_NULL_MODEL_LOCK.npz"),
           "null_key_manifest_sha256": sha(EVIDENCE / "JTD_E2_NULL_KEY_MANIFEST.json"),
           "target_seed_plan_sha256": lock["seed_plan_sha256"],
           "target_count": 72, "nearest_neighbor_index_by_environment": nearest,
           "code_sha256": {name: sha(ROOT / "research/jtd_crossenv_k12_v0" / name) for name in
                           ("run_jtd_e2_vm.py", "run_jtd_e2_vm.sh", "fit_jtd_e2_models.py", "score_jtd_e2.py")},
           "model_contract": {"references_per_source": 12, "blocks": [[0,1],[2,3],[4,5],[6,7],[8,9]],
                              "standard_scaler": "per environment/block, reference only",
                              "pca": "2 per block, full solver, reference only",
                              "FULL": "source-specific 10D sklearn OAS, original G0 jitter",
                              "BP": "five separate source-specific 2D sklearn OAS with G0 jitter",
                              "MBD": "FULL stabilized covariance block diagonal; exact FULL mean; no OAS refit or second jitter",
                              "DIAG": "source-specific 10D OAS then diagonalize before G0 jitter",
                              "SHUFFLED": "200 within-source nonanchor-block derangements; diagnostic only",
                              "prior": "uniform over six frozen sources"},
           "gate_rules": {"G1": "all three environment means >0 for both BP and MBD",
                          "G2": "both pooled environment-source bootstrap 95% lower bounds >0, 10000 draws",
                          "G3": "both >=13/18 positive source units and >=4/6 each environment",
                          "G4": "both pooled 20% trim and remove largest positive 5% target mean >0",
                          "G5": "FULL improves >=2/3 Brier, 1m mass, expected distance vs BP; none worsens >5% in any environment",
                          "G6": "no environment FULL mean truth NLL >1.10*BP or >1.10*MBD"},
           "bootstrap": {"draws": 10000, "seed": 2026092503,
                         "unit": "six source units resampled with replacement within each of three environments; four fresh targets kept together"},
           "software": {"numpy": np.__version__, "sklearn": sklearn.__version__},
           "no_target_seen": True, "no_sealed_input": True}
    save_json(pretarget, pre)
    print("JTD_E2_PRE_TARGET_LOCK_READY", sha(pretarget), "reference_count", 216, flush=True)


if __name__ == "__main__":
    main()

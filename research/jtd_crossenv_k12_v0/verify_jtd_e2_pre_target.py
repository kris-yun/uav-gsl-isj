#!/usr/bin/env python3
"""Independently reconstruct all E2 K12 fitted Gaussian and null parameters."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from sklearn.covariance import OAS
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "evidence/jtd_e2_20260925"


def fit(data: np.ndarray, diagonal: bool = False) -> tuple[np.ndarray, np.ndarray]:
    o = OAS(assume_centered=False, store_precision=False).fit(data)
    c = o.covariance_.copy()
    if diagonal:
        c = np.diag(np.diag(c))
    d = c.shape[0]
    c.flat[::d+1] += 1e-10*max(1.0,float(np.trace(c))/d)
    return o.location_,c


def check(actual: np.ndarray, expected: np.ndarray, name: str) -> float:
    diff = float(np.max(np.abs(actual-expected)))
    if diff > 1e-9:
        raise AssertionError(f"{name}: {diff}")
    return diff


def main() -> None:
    x=np.load(OUT/"JTD_E2_REFERENCE_12x10x30.npy",allow_pickle=False)
    with np.load(OUT/"JTD_E2_MODEL_LOCK.npz",allow_pickle=False) as z:
        model={k:z[k] for k in z.files}
    with np.load(OUT/"JTD_E2_NULL_MODEL_LOCK.npz",allow_pickle=False) as z:
        null={k:z[k] for k in z.files}
    initial=json.loads((OUT/"JTD_E2_INITIAL_LOCK.json").read_text(encoding="utf-8"))
    assert x.shape==(3,6,12,10,30)
    max_diff=0.0; block_checks=0; source_model_checks=0; null_model_checks=0; seed_set=set()
    projected=np.empty((3,6,12,10))
    for ei in range(3):
        for b in range(5):
            raw=x[ei,:,:,2*b:2*b+2,:].reshape(72,60)
            scaler=StandardScaler().fit(raw)
            pca=PCA(n_components=2,svd_solver="full").fit(scaler.transform(raw))
            for observed,expected,name in ((model["scaler_mean"][ei,b],scaler.mean_,"scaler mean"),
                                           (model["scaler_scale"][ei,b],scaler.scale_,"scaler scale"),
                                           (model["pca_mean"][ei,b],pca.mean_,"pca mean"),
                                           (model["pca_components"][ei,b],pca.components_,"pca components")):
                max_diff=max(max_diff,check(observed,expected,name))
            projected[ei,:,:,2*b:2*b+2]=pca.transform(scaler.transform(raw)).reshape(6,12,2)
            block_checks+=1
        for si in range(6):
            ref=projected[ei,si]
            max_diff=max(max_diff,check(model["reference_projected"][ei,si],ref,"projected ref"))
            mu,cov=fit(ref)
            for observed,expected,name in ((model["full_mu"][ei,si],mu,"full mean"),
                                           (model["full_cov"][ei,si],cov,"full covariance")):
                max_diff=max(max_diff,check(observed,expected,name))
            diag_mu,diag_cov=fit(ref,True)
            max_diff=max(max_diff,check(model["diag_mu"][ei,si],diag_mu,"diag mean"),
                         check(model["diag_cov"][ei,si],diag_cov,"diag covariance"))
            matched=np.zeros((10,10))
            for b in range(5):
                sl=slice(2*b,2*b+2)
                bp_mu,bp_cov=fit(ref[:,sl])
                max_diff=max(max_diff,check(model["bp_mu"][ei,si,b],bp_mu,"BP mean"),
                             check(model["bp_cov"][ei,si,b],bp_cov,"BP covariance"))
                matched[sl,sl]=cov[sl,sl]
            max_diff=max(max_diff,check(model["mbd_cov"][ei,si],matched,"MBD covariance"))
            source_model_checks+=1
        for ni in range(200):
            for si in range(6):
                shuffled=projected[ei,si].copy()
                sid=initial["source_groups"][6*ei+si]["source_id"]
                for b in range(1,5):
                    key=f"JTD_E2|NULL|environment_id={ei}|source_id={sid}|null_id={ni}|block_id={b}|purpose=within_source_derangement"
                    seed=int.from_bytes(hashlib.sha256(key.encode()).digest()[:8],"big")
                    assert seed==int(null["seeds"][ei,ni,si,b-1]) and seed not in seed_set
                    seed_set.add(seed)
                    rng=np.random.default_rng(seed)
                    for _ in range(1000):
                        permutation=rng.permutation(12)
                        if np.all(permutation!=np.arange(12)):
                            break
                    assert np.array_equal(permutation,null["permutations"][ei,ni,si,b-1])
                    sl=slice(2*b,2*b+2)
                    shuffled[:,sl]=projected[ei,si,permutation,sl]
                    assert np.array_equal(np.sort(shuffled[:,sl],axis=0),np.sort(projected[ei,si,:,sl],axis=0))
                mu,cov=fit(shuffled)
                max_diff=max(max_diff,check(null["null_mu"][ei,ni,si],mu,"null mean"),
                             check(null["null_cov"][ei,ni,si],cov,"null covariance"))
                null_model_checks+=1
    result={"independent_pre_target_model_refit":"PASS","pca_block_checks":block_checks,
            "source_model_checks":source_model_checks,"null_model_checks":null_model_checks,
            "unique_null_seed_count":len(seed_set),"max_abs_parameter_difference":max_diff,
            "target_data_read":False,"sealed_data_read":False}
    (OUT/"JTD_E2_PRE_TARGET_INDEPENDENT_VERIFICATION.json").write_bytes(
        (json.dumps(result,indent=2,sort_keys=True)+"\n").encode("utf-8"))
    print("JTD_E2_PRE_TARGET_INDEPENDENT_VERIFICATION_PASS",len(seed_set),flush=True)


if __name__=="__main__":
    main()

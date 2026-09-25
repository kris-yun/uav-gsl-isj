#!/usr/bin/env python3
"""Score genuinely fresh JTD-E2 targets using only pre-target frozen K12 models."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.special import logsumexp
from scipy.stats import trim_mean

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence/jtd_e2_20260925"
MODELS = ("FULL", "BLOCK_PRODUCT", "MATCHED_BLOCK_DIAG", "DIAG_COV")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, obj: object) -> None:
    path.write_bytes((json.dumps(obj, indent=2, sort_keys=True, allow_nan=False)+"\n").encode("utf-8"))


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def gaussian(targets: np.ndarray, mean: np.ndarray, cov: np.ndarray) -> np.ndarray:
    scores = np.empty((len(targets), len(mean)))
    d = targets.shape[1]
    for si in range(len(mean)):
        lower = np.linalg.cholesky(cov[si])
        projected = np.linalg.solve(lower, (targets-mean[si]).T)
        scores[:, si] = -0.5*(d*np.log(2*np.pi)+np.sum(projected*projected,axis=0)) - np.log(np.diag(lower)).sum()
    return scores


def normalized(loglik: np.ndarray, truth: np.ndarray) -> tuple[np.ndarray,np.ndarray,np.ndarray]:
    logpost = loglik-logsumexp(loglik,axis=1,keepdims=True)
    nll = -logpost[np.arange(len(truth)),truth]
    rank = 1+np.sum(loglik > loglik[np.arange(len(truth)),truth,None],axis=1)
    if not np.isfinite(nll).all():
        raise RuntimeError("E2 nonfinite target truth NLL")
    return logpost,nll,rank


def tail(delta: np.ndarray) -> dict:
    flat = delta.ravel()
    positive = np.flatnonzero(flat>0)
    sorted_ix = positive[np.argsort(flat[positive])[::-1]]
    result = {"mean":float(flat.mean()),"trimmed_10_mean":float(trim_mean(flat,.1)),
              "trimmed_20_mean":float(trim_mean(flat,.2)),
              "largest_positive":float(flat.max()),"largest_negative":float(flat.min())}
    for pct in (1,5):
        remove = sorted_ix[:math.ceil(len(flat)*pct/100)]
        result[f"remove_largest_positive_{pct}pct_count"] = len(remove)
        result[f"remove_largest_positive_{pct}pct_mean"] = float(np.delete(flat,remove).mean())
    return result


def main() -> None:
    if (EVIDENCE / "JTD_E2_RESULT.json").exists():
        raise RuntimeError("refuse replacing E2 scientific result")
    initial_path = EVIDENCE / "JTD_E2_INITIAL_LOCK.json"
    pre_path = EVIDENCE / "JTD_E2_PRE_TARGET_LOCK.json"
    target_acq_path = EVIDENCE / "JTD_E2_TARGET_ACQUISITION.json"
    initial = json.loads(initial_path.read_text(encoding="utf-8"))
    pre = json.loads(pre_path.read_text(encoding="utf-8"))
    acquisition = json.loads(target_acq_path.read_text(encoding="utf-8"))
    if pre["initial_lock_sha256"] != sha(initial_path) or acquisition["pre_target_lock_sha256"] != sha(pre_path):
        raise RuntimeError("E2 lock chain drift")
    if acquisition["new_fresh_target_runs"] != 72 or pre["reference_count"] != 216:
        raise RuntimeError("E2 reference/target count drift")
    for name, key in (("JTD_E2_REFERENCE_12x10x30.npy","reference_tensor_sha256"),
                      ("JTD_E2_MODEL_LOCK.npz","model_lock_sha256"),
                      ("JTD_E2_NULL_MODEL_LOCK.npz","null_model_lock_sha256")):
        if sha(EVIDENCE/name) != pre[key]:
            raise RuntimeError(f"E2 pre-target artifact drift: {name}")
    for name, expected in pre["code_sha256"].items():
        if sha(ROOT/"research/jtd_crossenv_k12_v0"/name) != expected:
            raise RuntimeError(f"E2 frozen code drift: {name}")
    target_path = EVIDENCE / "JTD_E2_FRESH_TARGET_10x30.npy"
    if sha(target_path) != acquisition["target_tensor_sha256"]:
        raise RuntimeError("E2 target vector hash drift")
    targets = np.load(target_path, allow_pickle=False)
    if targets.shape != (3,6,4,10,30) or targets.dtype != np.float32 or not np.isfinite(targets).all():
        raise RuntimeError("E2 target shape/dtype invalid")
    with np.load(EVIDENCE/"JTD_E2_MODEL_LOCK.npz",allow_pickle=False) as z:
        model = {k:z[k] for k in z.files}
    with np.load(EVIDENCE/"JTD_E2_NULL_MODEL_LOCK.npz",allow_pickle=False) as z:
        null = {k:z[k] for k in z.files}
    with (EVIDENCE/"JTD_E2_FRESH_TARGET_MANIFEST.tsv").open(newline="",encoding="utf-8") as f:
        manifest = list(csv.DictReader(f,delimiter="\t"))
    if len(manifest)!=72 or sha(EVIDENCE/"JTD_E2_FRESH_TARGET_MANIFEST.tsv")!=acquisition["manifest_sha256"]:
        raise RuntimeError("E2 target manifest drift")
    groups = initial["source_groups"]
    logpost = np.empty((3,4,6,4,6))
    nll = np.empty((3,4,6,4))
    rank = np.empty((3,4,6,4),dtype=np.int16)
    null_nll = np.empty((3,200,6,4))
    null_rank = np.empty((3,200,6,4),dtype=np.int16)
    truth = np.repeat(np.arange(6),4)
    for ei in range(3):
        z_target = np.empty((6,4,10))
        for b in range(5):
            raw = targets[ei,:,:,2*b:2*b+2,:].reshape(24,60)
            standard = (raw-model["scaler_mean"][ei,b])/model["scaler_scale"][ei,b]
            z_target[:,:,2*b:2*b+2] = ((standard-model["pca_mean"][ei,b]) @
                                       model["pca_components"][ei,b].T).reshape(6,4,2)
        flat = z_target.reshape(24,10)
        full_ll = gaussian(flat,model["full_mu"][ei],model["full_cov"][ei])
        bp_ll = np.zeros((24,6))
        for b in range(5):
            sl = slice(2*b,2*b+2)
            bp_ll += gaussian(flat[:,sl],model["bp_mu"][ei,:,b],model["bp_cov"][ei,:,b])
        mbd_ll = gaussian(flat,model["full_mu"][ei],model["mbd_cov"][ei])
        diag_ll = gaussian(flat,model["diag_mu"][ei],model["diag_cov"][ei])
        for mi,ll in enumerate((full_ll,bp_ll,mbd_ll,diag_ll)):
            lp,nl,ra = normalized(ll,truth)
            logpost[ei,mi] = lp.reshape(6,4,6)
            nll[ei,mi] = nl.reshape(6,4)
            rank[ei,mi] = ra.reshape(6,4)
        for null_id in range(200):
            ll = gaussian(flat,null["null_mu"][ei,null_id],null["null_cov"][ei,null_id])
            _,nl,ra = normalized(ll,truth)
            null_nll[ei,null_id] = nl.reshape(6,4)
            null_rank[ei,null_id] = ra.reshape(6,4)
        print("JTD_E2_FRESH_ENVIRONMENT_SCORED",ei,flush=True)
    np.savez_compressed(EVIDENCE/"JTD_E2_COMPLETE_POSTERIORS.npz",logpost=logpost,
                        posterior=np.exp(logpost),model_names=np.asarray(MODELS))
    np.savez_compressed(EVIDENCE/"JTD_E2_SCORE_ARRAYS.npz",nll=nll,rank=rank,
                        null_nll=null_nll,null_rank=null_rank)
    metrics = {}
    target_rows=[]; unit_rows=[]; env_rows=[]; nn_rows=[]
    by_key={(int(r["environment_index"]),int(r["source_index"]),int(r["new_index"])):r for r in manifest}
    if len(by_key)!=72:
        raise RuntimeError("duplicate E2 target key")
    for ei in range(3):
        ids=[groups[6*ei+si]["source_id"] for si in range(6)]
        xy=np.asarray([groups[6*ei+si]["source_xyz"][:2] for si in range(6)])
        distance=np.linalg.norm(xy[:,None,:]-xy[None,:,:],axis=2)
        nearest=np.asarray(pre["nearest_neighbor_index_by_environment"][ei],dtype=int)
        no_self=distance.copy(); np.fill_diagonal(no_self,np.inf)
        if not np.array_equal(nearest,np.argmin(no_self,axis=1)):
            raise RuntimeError("E2 frozen nearest neighbor drift")
        metrics[ei]={}
        for mi,name in enumerate(MODELS):
            p=np.exp(logpost[ei,mi])
            p_true=p[np.arange(6)[:,None],np.arange(4)[None,:],np.arange(6)[:,None]]
            brier=np.sum(p*p,axis=2)-2*p_true+1
            mass05=np.einsum("src,sc->sr",p,distance<=.5+1e-12)
            mass10=np.einsum("src,sc->sr",p,distance<=1+1e-12)
            expected=np.einsum("src,sc->sr",p,distance)
            map_ix=np.argmax(logpost[ei,mi],axis=2)
            map_error=distance[np.arange(6)[:,None],map_ix]
            nn_margin=logpost[ei,mi,np.arange(6)[:,None],np.arange(4)[None,:],np.arange(6)[:,None]] - \
                      logpost[ei,mi,np.arange(6)[:,None],np.arange(4)[None,:],nearest[:,None]]
            metrics[ei][name]={"mean_nll":float(nll[ei,mi].mean()),
                               "mean_brier":float(brier.mean()),"mean_mass_1m":float(mass10.mean()),
                               "mean_expected_distance_m":float(expected.mean()),
                               "top1":float((rank[ei,mi]==1).mean()),"top3":float((rank[ei,mi]<=3).mean()),
                               "mean_rank":float(rank[ei,mi].mean()),
                               "mean_mass_0p5m":float(mass05.mean()),
                               "mean_map_error_m":float(map_error.mean()),
                               "nearest_confusion_rate":float((map_ix==nearest[:,None]).mean()),
                               "mean_true_vs_nearest_logodds":float(nn_margin.mean())}
            for si in range(6):
                for ti in range(4):
                    row=by_key[(ei,si,ti)]
                    if row["source_id"]!=ids[si]:
                        raise RuntimeError("E2 target source identity drift")
                    target_rows.append({"environment_index":ei,"house":groups[6*ei+si]["house"],
                                        "wind":groups[6*ei+si]["wind"],"source_index":si,"source_id":ids[si],
                                        "target_index":ti,"seed":row["requested_seed"],"cube_sha256":row["cube_sha256"],
                                        "model":name,"truth_nll":float(nll[ei,mi,si,ti]),
                                        "truth_rank":int(rank[ei,mi,si,ti]),"top1":int(rank[ei,mi,si,ti]==1),
                                        "top3":int(rank[ei,mi,si,ti]<=3),"brier":float(brier[si,ti]),
                                        "mass_0p5m":float(mass05[si,ti]),"mass_1m":float(mass10[si,ti]),
                                        "expected_distance_m":float(expected[si,ti]),
                                        "map_distance_error_m":float(map_error[si,ti]),
                                        "map_source_id":ids[int(map_ix[si,ti])],
                                        "nearest_confusion":int(map_ix[si,ti]==nearest[si]),
                                        "true_vs_nearest_logodds":float(nn_margin[si,ti])})
        for si in range(6):
            unit_rows.append({"environment_index":ei,"house":groups[6*ei+si]["house"],
                              "wind":groups[6*ei+si]["wind"],"source_index":si,"source_id":ids[si],
                              "mean_delta_bp":float((nll[ei,1,si]-nll[ei,0,si]).mean()),
                              "mean_delta_mbd":float((nll[ei,2,si]-nll[ei,0,si]).mean()),
                              "positive_bp":int((nll[ei,1,si]-nll[ei,0,si]).mean()>0),
                              "positive_mbd":int((nll[ei,2,si]-nll[ei,0,si]).mean()>0)})
            for ti in range(4):
                nn_rows.append({"environment_index":ei,"source_id":ids[si],"target_index":ti,
                                "nearest_id":ids[int(nearest[si])],
                                "full_logodds":float(logpost[ei,0,si,ti,si]-logpost[ei,0,si,ti,nearest[si]]),
                                "bp_logodds":float(logpost[ei,1,si,ti,si]-logpost[ei,1,si,ti,nearest[si]]),
                                "mbd_logodds":float(logpost[ei,2,si,ti,si]-logpost[ei,2,si,ti,nearest[si]])})
        env_rows.append({"environment_index":ei,"house":groups[6*ei]["house"],"wind":groups[6*ei]["wind"],
                         "mean_delta_bp":float((nll[ei,1]-nll[ei,0]).mean()),
                         "mean_delta_mbd":float((nll[ei,2]-nll[ei,0]).mean()),
                         "positive_sources_bp":int(np.sum((nll[ei,1]-nll[ei,0]).mean(axis=1)>0)),
                         "positive_sources_mbd":int(np.sum((nll[ei,2]-nll[ei,0]).mean(axis=1)>0)),
                         "full_mean_nll":metrics[ei]["FULL"]["mean_nll"],
                         "bp_mean_nll":metrics[ei]["BLOCK_PRODUCT"]["mean_nll"],
                         "mbd_mean_nll":metrics[ei]["MATCHED_BLOCK_DIAG"]["mean_nll"]})
    write_csv(EVIDENCE/"JTD_E2_TARGET_METRICS.csv",target_rows)
    write_csv(EVIDENCE/"JTD_E2_ENVIRONMENT_SOURCE_SUMMARY.csv",unit_rows)
    write_csv(EVIDENCE/"JTD_E2_ENVIRONMENT_SUMMARY.csv",env_rows)
    write_csv(EVIDENCE/"JTD_E2_NEAREST_NEIGHBOR_DIAGNOSTICS.csv",nn_rows)
    bp=nll[:,1]-nll[:,0]
    mbd=nll[:,2]-nll[:,0]
    unit_bp=bp.mean(axis=2); unit_mbd=mbd.mean(axis=2)
    rng=np.random.default_rng(pre["bootstrap"]["seed"])
    draws=rng.integers(0,6,size=(10000,3,6))
    env=np.arange(3)[None,:,None]
    boot_bp=unit_bp[env,draws].mean(axis=(1,2))
    boot_mbd=unit_mbd[env,draws].mean(axis=(1,2))
    ci_bp=np.quantile(boot_bp,(.025,.975)); ci_mbd=np.quantile(boot_mbd,(.025,.975))
    np.savez_compressed(EVIDENCE/"JTD_E2_BOOTSTRAP_10000.npz",bp=boot_bp,mbd=boot_mbd)
    tail_bp,tail_mbd=tail(bp),tail(mbd)
    write_json(EVIDENCE/"JTD_E2_TAIL_SENSITIVITY.json",{"bp":tail_bp,"mbd":tail_mbd})
    null_means=null_nll.mean(axis=(2,3))
    write_csv(EVIDENCE/"JTD_E2_SHUFFLED_NULL_SUMMARY.csv",
              [{"environment_index":ei,"null_id":ni,"mean_truth_nll":float(null_means[ei,ni]),
                "mean_truth_rank":float(null_rank[ei,ni].mean())} for ei in range(3) for ni in range(200)])
    g1=bool(all(r["mean_delta_bp"]>0 and r["mean_delta_mbd"]>0 for r in env_rows))
    g2=bool(ci_bp[0]>0 and ci_mbd[0]>0)
    per_env_bp=[int((unit_bp[ei]>0).sum()) for ei in range(3)]
    per_env_mbd=[int((unit_mbd[ei]>0).sum()) for ei in range(3)]
    g3=bool(sum(per_env_bp)>=13 and sum(per_env_mbd)>=13 and min(per_env_bp)>=4 and min(per_env_mbd)>=4)
    g4=bool(tail_bp["trimmed_20_mean"]>0 and tail_bp["remove_largest_positive_5pct_mean"]>0 and
            tail_mbd["trimmed_20_mean"]>0 and tail_mbd["remove_largest_positive_5pct_mean"]>0)
    utility=[]
    for ei in range(3):
        f,b=metrics[ei]["FULL"],metrics[ei]["BLOCK_PRODUCT"]
        better=(b["mean_brier"]-f["mean_brier"],f["mean_mass_1m"]-b["mean_mass_1m"],
                b["mean_expected_distance_m"]-f["mean_expected_distance_m"])
        baseline=(b["mean_brier"],b["mean_mass_1m"],b["mean_expected_distance_m"])
        utility.append({"environment_index":ei,"improvements":list(better),
                        "worsening_over_5pct":[bool((-x)/abs(y)>.05 if y else x<0) for x,y in zip(better,baseline)]})
    pooled={name:{key:float(np.mean([metrics[ei][name][key] for ei in range(3)])) for key in metrics[0][name]}
            for name in MODELS}
    full,bp_model=pooled["FULL"],pooled["BLOCK_PRODUCT"]
    pooled_improved=[full["mean_brier"]<bp_model["mean_brier"],
                     full["mean_mass_1m"]>bp_model["mean_mass_1m"],
                     full["mean_expected_distance_m"]<bp_model["mean_expected_distance_m"]]
    g5=bool(sum(pooled_improved)>=2 and not any(any(u["worsening_over_5pct"]) for u in utility))
    g6=bool(all(r["full_mean_nll"]<=1.10*r["bp_mean_nll"] and r["full_mean_nll"]<=1.10*r["mbd_mean_nll"]
                for r in env_rows))
    gates={f"E2_G{i}":v for i,v in enumerate((g1,g2,g3,g4,g5,g6),1)}
    if all(gates.values()):
        decision="JTD_E2_GO_EQUAL_DEPTH_CROSS_ENVIRONMENT_CONFIRMED"
    elif all((g1,g2,g4,g5,g6)) and not g3:
        decision="JTD_E2_HOLD_RESIDUAL_ENVIRONMENT_HETEROGENEITY"
    else:
        decision="JTD_E2_STOP_CROSSBLOCK_VALUE_NOT_ENVIRONMENT_GENERAL"
    result={"decision":decision,"gates":gates,"environment_count":3,"source_units":18,
            "fresh_target_count":72,"new_reference_runs":108,"new_target_runs":72,
            "reference_count_per_source":12,"fresh_targets_per_source":4,
            "pre_target_lock_sha256":sha(pre_path),"target_acquisition_sha256":sha(target_acq_path),
            "environment_summaries":env_rows,"pooled_model_metrics":pooled,
            "delta_bp":{"mean":float(bp.mean()),"ci_95_environment_source_panel":ci_bp.tolist(),
                        "positive_units":int((unit_bp>0).sum()),"positive_units_per_environment":per_env_bp,**tail_bp},
            "delta_mbd":{"mean":float(mbd.mean()),"ci_95_environment_source_panel":ci_mbd.tolist(),
                         "positive_units":int((unit_mbd>0).sum()),"positive_units_per_environment":per_env_mbd,**tail_mbd},
            "spatial_utility":{"pooled_improved_brier_mass1m_expected_distance":pooled_improved,
                               "environment_relative_harm":utility},
            "shuffled_continuity":{"full_mean_nll":float(nll[:,0].mean()),
                                   "median_pooled_aggregate_null_mean_nll":float(np.median(null_means.mean(axis=0))),
                                   "mean_targetwise_median_null_minus_full":float((np.median(null_nll,axis=1)-nll[:,0]).mean())},
            "interpretation_boundary":"Three already OPEN environments, two Houses; House01 DEV and all House03 remain sealed. Bootstrap intervals describe this 18-unit panel, not an environment population."}
    write_json(EVIDENCE/"JTD_E2_RESULT.json",result)
    print(decision,flush=True)
    print("E2_GATES",json.dumps(gates,sort_keys=True),flush=True)


if __name__=="__main__":
    main()

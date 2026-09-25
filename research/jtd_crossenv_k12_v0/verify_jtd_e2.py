#!/usr/bin/env python3
"""Independent raw-target, locked-model, posterior and E2-G1..G6 verification."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.linalg import solve_triangular
from scipy.special import logsumexp
from scipy.stats import trim_mean

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"evidence/jtd_e2_20260925"
E1=ROOT/"evidence/environment_level_benchmark_v0/e1"
NAMES=("FULL","BLOCK_PRODUCT","MATCHED_BLOCK_DIAG","DIAG_COV")


def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda:f.read(1024*1024),b""):
            h.update(part)
    return h.hexdigest()


def rows(path:Path)->list[dict]:
    with path.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f,delimiter="\t"))


def close(x:float,y:float,label:str,tol:float=1e-7)->None:
    if abs(float(x)-float(y))>tol*max(1,abs(float(y))):
        raise AssertionError(f"{label}: {x} != {y}")


def likelihood(z:np.ndarray,mu:np.ndarray,cov:np.ndarray)->np.ndarray:
    ll=np.empty((len(z),len(mu)))
    for si in range(len(mu)):
        chol=np.linalg.cholesky(cov[si])
        v=solve_triangular(chol,(z-mu[si]).T,lower=True,check_finite=False)
        ll[:,si]=-.5*(z.shape[1]*np.log(2*np.pi)+(v*v).sum(axis=0)) - np.log(np.diag(chol)).sum()
    return ll


def main()->None:
    initial=json.loads((OUT/"JTD_E2_INITIAL_LOCK.json").read_text(encoding="utf-8"))
    pre=json.loads((OUT/"JTD_E2_PRE_TARGET_LOCK.json").read_text(encoding="utf-8"))
    result=json.loads((OUT/"JTD_E2_RESULT.json").read_text(encoding="utf-8"))
    acquisition=json.loads((OUT/"JTD_E2_TARGET_ACQUISITION.json").read_text(encoding="utf-8"))
    assert pre["initial_lock_sha256"]==sha(OUT/"JTD_E2_INITIAL_LOCK.json")
    assert acquisition["pre_target_lock_sha256"]==sha(OUT/"JTD_E2_PRE_TARGET_LOCK.json")
    x=np.load(OUT/"JTD_E2_FRESH_TARGET_10x30.npy",allow_pickle=False)
    with np.load(OUT/"JTD_E2_MODEL_LOCK.npz",allow_pickle=False) as z:
        model={k:z[k] for k in z.files}
    with np.load(OUT/"JTD_E2_NULL_MODEL_LOCK.npz",allow_pickle=False) as z:
        null={k:z[k] for k in z.files}
    with np.load(OUT/"JTD_E2_COMPLETE_POSTERIORS.npz",allow_pickle=False) as z:
        lp=z["logpost"]; posterior=z["posterior"]
        assert tuple(z["model_names"].tolist())==NAMES
    with np.load(OUT/"JTD_E2_SCORE_ARRAYS.npz",allow_pickle=False) as z:
        nll=z["nll"]; rank=z["rank"]; null_nll=z["null_nll"]; null_rank=z["null_rank"]
    assert x.shape==(3,6,4,10,30) and lp.shape==posterior.shape==(3,4,6,4,6)
    assert nll.shape==rank.shape==(3,4,6,4) and null_nll.shape==(3,200,6,4)
    assert np.isfinite(lp).all() and np.isfinite(nll).all() and np.isfinite(null_nll).all()
    assert np.allclose(np.exp(lp),posterior,atol=1e-15,rtol=1e-12)
    assert np.allclose(posterior.sum(axis=4),1,atol=1e-12)
    # Re-extract all 72 truly fresh targets directly from retained raw cubes.
    probe_rows=rows(E1/"E1_HOUSE_PROBE_CONTRACTS.tsv")
    probe={h:sorted([p for p in probe_rows if p["house"]==h],key=lambda q:int(q["probe_rank"]))
           for h in ("House01","House02")}
    manifest=rows(OUT/"JTD_E2_FRESH_TARGET_MANIFEST.tsv")
    seed_plan=rows(OUT/"JTD_E2_SEED_PLAN_180.tsv")
    plan={(r["phase"],int(r["environment_index"]),int(r["source_index"]),int(r["new_index"])):r for r in seed_plan}
    assert len(manifest)==72 and len(plan)==180
    unique_seeds=set()
    for row in manifest:
        ei,si,ti=(int(row[k]) for k in ("environment_index","source_index","new_index"))
        requested=int(row["requested_seed"])
        assert row["phase"]=="TARGET" and requested not in unique_seeds
        unique_seeds.add(requested)
        assert int(plan[("TARGET",ei,si,ti)]["requested_seed"])==requested
        cube_path=Path(row["run_dir"])/"concentration.npy"
        pooled_path=Path(row["run_dir"])/"pooled.npy"
        assert sha(cube_path)==row["cube_sha256"] and sha(pooled_path)==row["pooled_sha256"]
        cube=np.load(cube_path,allow_pickle=False)
        house=initial["source_groups"][6*ei+si]["house"]
        assert cube.shape==((10,87,114) if house=="House01" else (10,83,119))
        measured=np.stack([cube[:,int(p["native_x0"]):int(p["native_x1_exclusive"]),
                                  int(p["native_y0"]):int(p["native_y1_exclusive"])].mean(axis=(1,2))
                           for p in probe[house]],axis=1).astype(np.float32)
        assert np.array_equal(measured,np.load(pooled_path,allow_pickle=False))
        assert np.array_equal(measured,x[ei,si,ti])
    max_lp_diff=0.0; max_nll_diff=0.0; null_checks=0
    truth=np.repeat(np.arange(6),4)
    for ei in range(3):
        projected=np.empty((24,10))
        for b in range(5):
            raw=x[ei,:,:,2*b:2*b+2,:].reshape(24,60)
            scaled=(raw-model["scaler_mean"][ei,b])/model["scaler_scale"][ei,b]
            projected[:,2*b:2*b+2]=(scaled-model["pca_mean"][ei,b])@model["pca_components"][ei,b].T
        full=likelihood(projected,model["full_mu"][ei],model["full_cov"][ei])
        bp=np.zeros_like(full)
        for b in range(5):
            sl=slice(2*b,2*b+2)
            bp+=likelihood(projected[:,sl],model["bp_mu"][ei,:,b],model["bp_cov"][ei,:,b])
        mbd=likelihood(projected,model["full_mu"][ei],model["mbd_cov"][ei])
        diag=likelihood(projected,model["diag_mu"][ei],model["diag_cov"][ei])
        for mi,ll in enumerate((full,bp,mbd,diag)):
            post=ll-logsumexp(ll,axis=1,keepdims=True)
            saved=lp[ei,mi].reshape(24,6)
            max_lp_diff=max(max_lp_diff,float(np.max(np.abs(post-saved))))
            nn=-post[np.arange(24),truth]
            max_nll_diff=max(max_nll_diff,float(np.max(np.abs(nn-nll[ei,mi].reshape(24)))))
            assert np.array_equal(1+(ll>ll[np.arange(24),truth,None]).sum(axis=1),rank[ei,mi].reshape(24))
        for ni in range(200):
            ll=likelihood(projected,null["null_mu"][ei,ni],null["null_cov"][ei,ni])
            post=ll-logsumexp(ll,axis=1,keepdims=True)
            max_nll_diff=max(max_nll_diff,float(np.max(np.abs(-post[np.arange(24),truth]-null_nll[ei,ni].reshape(24)))))
            assert np.array_equal(1+(ll>ll[np.arange(24),truth,None]).sum(axis=1),null_rank[ei,ni].reshape(24))
            null_checks+=1
    if max_lp_diff>1e-5 or max_nll_diff>1e-5:
        raise AssertionError(f"E2 model posterior mismatch {max_lp_diff} {max_nll_diff}")
    bp_delta=nll[:,1]-nll[:,0]; mbd_delta=nll[:,2]-nll[:,0]
    bp_unit=bp_delta.mean(axis=2); mbd_unit=mbd_delta.mean(axis=2)
    rng=np.random.default_rng(pre["bootstrap"]["seed"])
    draw=rng.integers(0,6,size=(10000,3,6))
    boot_bp=bp_unit[np.arange(3)[None,:,None],draw].mean(axis=(1,2))
    boot_mbd=mbd_unit[np.arange(3)[None,:,None],draw].mean(axis=(1,2))
    with np.load(OUT/"JTD_E2_BOOTSTRAP_10000.npz",allow_pickle=False) as z:
        assert np.array_equal(boot_bp,z["bp"]) and np.array_equal(boot_mbd,z["mbd"])
    ci_bp=np.quantile(boot_bp,(.025,.975)); ci_mbd=np.quantile(boot_mbd,(.025,.975))
    np.testing.assert_allclose(ci_bp,result["delta_bp"]["ci_95_environment_source_panel"],atol=1e-12)
    np.testing.assert_allclose(ci_mbd,result["delta_mbd"]["ci_95_environment_source_panel"],atol=1e-12)
    for name,delta,unit in (("delta_bp",bp_delta,bp_unit),("delta_mbd",mbd_delta,mbd_unit)):
        observed=result[name]; flat=delta.ravel()
        close(flat.mean(),observed["mean"],name+" mean")
        close(trim_mean(flat,.2),observed["trimmed_20_mean"],name+" trim")
        positive=np.flatnonzero(flat>0); sorted_ix=positive[np.argsort(flat[positive])[::-1]]
        for pct in (1,5):
            remaining=np.delete(flat,sorted_ix[:math.ceil(len(flat)*pct/100)])
            close(remaining.mean(),observed[f"remove_largest_positive_{pct}pct_mean"],name+" tail")
        assert int((unit>0).sum())==observed["positive_units"]
        assert [(unit[ei]>0).sum() for ei in range(3)]==observed["positive_units_per_environment"]
    spatial={}
    env_means=[]
    for ei in range(3):
        xy=np.asarray([initial["source_groups"][6*ei+si]["source_xyz"][:2] for si in range(6)])
        distance=np.linalg.norm(xy[:,None,:]-xy[None,:,:],axis=2)
        nearest=np.asarray(pre["nearest_neighbor_index_by_environment"][ei])
        spatial[ei]={}
        for mi,name in enumerate(NAMES):
            p=posterior[ei,mi]
            true=p[np.arange(6)[:,None],np.arange(4)[None,:],np.arange(6)[:,None]]
            spatial[ei][name]={"mean_nll":float(nll[ei,mi].mean()),
                               "mean_brier":float((np.sum(p*p,axis=2)-2*true+1).mean()),
                               "mean_mass_1m":float(np.einsum("src,sc->sr",p,distance<=1+1e-12).mean()),
                               "mean_expected_distance_m":float(np.einsum("src,sc->sr",p,distance).mean())}
        env_means.append((float(bp_delta[ei].mean()),float(mbd_delta[ei].mean())))
        for name, field in (("FULL","full_mean_nll"),("BLOCK_PRODUCT","bp_mean_nll"),
                            ("MATCHED_BLOCK_DIAG","mbd_mean_nll")):
            close(spatial[ei][name]["mean_nll"],result["environment_summaries"][ei][field],
                  "environment mean NLL")
        close(bp_delta[ei].mean(),result["environment_summaries"][ei]["mean_delta_bp"],"environment BP delta")
        close(mbd_delta[ei].mean(),result["environment_summaries"][ei]["mean_delta_mbd"],"environment MBD delta")
    pooled={name:{key:float(np.mean([spatial[ei][name][key] for ei in range(3)])) for key in spatial[0][name]}
            for name in NAMES}
    for name in NAMES:
        for key,value in pooled[name].items():
            close(value,result["pooled_model_metrics"][name][key],"pooled spatial")
    g1=all(a>0 and b>0 for a,b in env_means)
    g2=ci_bp[0]>0 and ci_mbd[0]>0
    g3=all((unit>0).sum()>=13 and all((unit[ei]>0).sum()>=4 for ei in range(3)) for unit in (bp_unit,mbd_unit))
    def robust(delta:np.ndarray)->bool:
        flat=delta.ravel(); positive=np.flatnonzero(flat>0)
        order=positive[np.argsort(flat[positive])[::-1]]
        return trim_mean(flat,.2)>0 and np.delete(flat,order[:math.ceil(.05*len(flat))]).mean()>0
    g4=robust(bp_delta) and robust(mbd_delta)
    f,b=pooled["FULL"],pooled["BLOCK_PRODUCT"]
    better=(b["mean_brier"]-f["mean_brier"],f["mean_mass_1m"]-b["mean_mass_1m"],
            b["mean_expected_distance_m"]-f["mean_expected_distance_m"])
    g5=sum(v>0 for v in better)>=2
    for ei in range(3):
        f,b=spatial[ei]["FULL"],spatial[ei]["BLOCK_PRODUCT"]
        changes=(b["mean_brier"]-f["mean_brier"],f["mean_mass_1m"]-b["mean_mass_1m"],
                 b["mean_expected_distance_m"]-f["mean_expected_distance_m"])
        base=(b["mean_brier"],b["mean_mass_1m"],b["mean_expected_distance_m"])
        g5=g5 and all((-c)/abs(q)<=.05 if q else c>=0 for c,q in zip(changes,base))
    g6=all(spatial[ei]["FULL"]["mean_nll"]<=1.1*spatial[ei][comp]["mean_nll"]
           for ei in range(3) for comp in ("BLOCK_PRODUCT","MATCHED_BLOCK_DIAG"))
    gates={f"E2_G{i}":bool(v) for i,v in enumerate((g1,g2,g3,g4,g5,g6),1)}
    assert gates==result["gates"]
    decision=("JTD_E2_GO_EQUAL_DEPTH_CROSS_ENVIRONMENT_CONFIRMED" if all(gates.values()) else
              "JTD_E2_HOLD_RESIDUAL_ENVIRONMENT_HETEROGENEITY" if all((g1,g2,g4,g5,g6)) and not g3 else
              "JTD_E2_STOP_CROSSBLOCK_VALUE_NOT_ENVIRONMENT_GENERAL")
    assert decision==result["decision"]
    out={"independent_recomputation":"PASS","decision":decision,"gates":gates,
         "raw_fresh_cube_reextractions_exact":72,"saved_model_posterior_checks":4*3*24,
         "saved_null_model_checks":null_checks,"bootstrap_draws_checked":10000,
         "max_logposterior_difference":max_lp_diff,"max_truth_nll_difference":max_nll_diff,
         "ci_bp":ci_bp.tolist(),"ci_mbd":ci_mbd.tolist(),"sealed_data_read":False}
    (OUT/"JTD_E2_INDEPENDENT_RECOMPUTATION.json").write_bytes(
        (json.dumps(out,indent=2,sort_keys=True)+"\n").encode("utf-8"))
    print("JTD_E2_INDEPENDENT_RECOMPUTATION_PASS",decision,flush=True)


if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Independent dual-form ridge and gate recomputation from frozen RPO features."""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.stats import rankdata, spearmanr
from sklearn.metrics import balanced_accuracy_score
from sklearn.preprocessing import StandardScaler

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"evidence/relational_physical_observability_v0"
RIA=ROOT/"evidence/relational_identifiability_a0/RIA_A0_REFERENCE_IDENTIFIABILITY.csv"
FAMILIES=("SOURCE_ONLY","GEOM","SIMPLE_WIND","PHYS")
TARGETS=("CNR","ED")
ALPHAS=(1e-4,1e-3,1e-2,1e-1,1,10,100,1000)

def table(path):
    with open(path,encoding="utf-8",newline="") as f:return list(csv.DictReader(f))

def digest(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):h.update(block)
    return h.hexdigest()

def dual_predict(x,y,train,test,alpha):
    scaler=StandardScaler().fit(x[train])
    a=scaler.transform(x[train]);b=scaler.transform(x[test])
    am=a.mean(axis=0);ym=y[train].mean()
    centered=a-am
    weights=np.linalg.solve(centered@centered.T+alpha*np.eye(len(train)),y[train]-ym)
    return ym+(b-am)@centered.T@weights

def main():
    lock=json.loads((OUT/"RPO_G0_PRE_RUN_LOCK.json").read_text())
    frozen=json.loads((OUT/"RPO_G0_FEATURE_FREEZE.json").read_text())
    result=json.loads((OUT/"RPO_G0_RESULT.json").read_text())
    assert result["decision"]=="RPO_G0_STOP_PHYSICAL_CONTEXT_NOT_PREDICTIVE_BEYOND_BASELINES"
    xs={};bands=None
    for family in FAMILIES:
        file=OUT/f"RPO_G0_{family}_FEATURES.csv"
        assert digest(file)==frozen["feature_sha256"][family]
        rows=[r for r in table(file) if r["panel"]=="CENTRAL"]
        rows.sort(key=lambda r:int(r["pair_index"]))
        assert len(rows)==84
        if bands is None:bands=np.array([int(r["x_band"]) for r in rows])
        names=[k for k in rows[0] if k not in ("panel","pair_index","x_band")]
        xs[family]=np.array([[float(r[k]) for k in names] for r in rows])
    rr={(int(r["pair_index"]),r["protocol"]):r for r in table(RIA)}
    y=np.array([[float(rr[i,"P_E2"][f"D_{t}"])-float(rr[i,"P_G1A"][f"D_{t}"]) for t in TARGETS] for i in range(84)])
    frozen_preds={(int(r["pair_index"]),r["target"]):r for r in table(OUT/"RPO_G0_HELDOUT_PREDICTIONS.csv")}
    diffs=[];alpha_mismatch=[];recomputed=np.zeros((84,2,4))
    selected={(r["target"],r["family"],int(r["heldout_band"])):float(r["alpha"]) for r in table(OUT/"RPO_G0_NESTED_ALPHA.csv")}
    for ki,target in enumerate(TARGETS):
        for fi,family in enumerate(FAMILIES):
            x=xs[family]
            for band in range(4):
                train=np.flatnonzero(bands!=band);test=np.flatnonzero(bands==band)
                losses=[]
                for alpha in ALPHAS:
                    errors=[]
                    for inner in sorted(set(bands[train])):
                        fit=train[bands[train]!=inner];val=train[bands[train]==inner]
                        pred=dual_predict(x,y[:,ki],fit,val,alpha)
                        errors.extend((y[val,ki]-pred)**2)
                    losses.append(float(np.mean(errors)))
                alpha=ALPHAS[int(np.argmin(losses))]
                if alpha!=selected[target,family,band]:alpha_mismatch.append((target,family,band,alpha))
                pp=dual_predict(x,y[:,ki],train,test,alpha)
                recomputed[test,ki,fi]=pp
                for idx,value in zip(test,pp):
                    exact=float(frozen_preds[idx,target][family])
                    diffs.append(abs(value-exact)/max(1,abs(exact)))
    assert not alpha_mismatch and max(diffs)<1e-7
    metrics={}
    for ki,target in enumerate(TARGETS):
        z=y[:,ki];pred=recomputed[:,ki,3]
        rho=float(spearmanr(z,pred).statistic)
        sign={family:float(balanced_accuracy_score(z[np.abs(z)>=1e-10]>0,recomputed[np.abs(z)>=1e-10,ki,fi]>0))
              for fi,family in enumerate(FAMILIES)}
        advantages={}
        for fi,family in enumerate(("GEOM","SIMPLE_WIND"),start=1):
            gain=(z-recomputed[:,ki,fi])**2-(z-pred)**2
            advantages[family]={"mean":float(np.mean(gain)),"positive_bands":int(sum(np.mean(gain[bands==b])>0 for b in range(4)))}
        metrics[target]={"PHYS_spearman":rho,"sign_balanced_accuracy":sign,"advantages":advantages}
        frozen=result["targets"][target]
        assert abs(rho-frozen["PHYS_spearman"])<1e-10
        for family in FAMILIES:assert abs(sign[family]-frozen["sign_balanced_accuracy"][family])<1e-10
        for family in advantages:
            assert advantages[family]["positive_bands"]==frozen["advantages"][family]["positive_bands"]
            assert abs(advantages[family]["mean"]-frozen["advantages"][family]["mean"])/max(1,abs(frozen["advantages"][family]["mean"]))<1e-6
    boot=np.load(OUT/"RPO_G0_BOOTSTRAP_10000.npz")
    draws=boot["pair_draws"]
    assert draws.shape==(10000,84)
    bootstrap_diff=[]
    for ki,target in enumerate(TARGETS):
        for fi,baseline in ((1,"GEOM"),(2,"SIMPLE_WIND")):
            gain=(y[:,ki]-recomputed[:,ki,fi])**2-(y[:,ki]-recomputed[:,ki,3])**2
            values=np.mean(gain[draws],axis=1)
            stored=boot[f"{target}_advantage_{baseline}"]
            bootstrap_diff.append(np.max(np.abs(values-stored)/np.maximum(1,np.abs(stored))))
    assert max(bootstrap_diff)<1e-6
    report={"decision_matches":True,"independent_method":"dual-form ridge with manual inner-band loss aggregation",
            "max_relative_prediction_difference":max(diffs),"max_relative_bootstrap_difference":max(bootstrap_diff),
            "alpha_mismatches":alpha_mismatch,"central_pairs":84,"metrics":metrics,
            "result_sha256":digest(OUT/"RPO_G0_RESULT.json"),"feature_freeze_sha256":digest(OUT/"RPO_G0_FEATURE_FREEZE.json"),
            "ridge_grid_matches_lock":list(ALPHAS)==lock["alpha_grid"]}
    (OUT/"RPO_G0_INDEPENDENT_RECOMPUTATION.json").write_bytes((json.dumps(report,indent=2,sort_keys=True)+"\n").encode())
    print("INDEPENDENT_RPO_PASS",max(diffs),max(bootstrap_diff))

if __name__=="__main__":main()

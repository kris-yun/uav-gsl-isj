#!/usr/bin/env python3
"""Independent implementation of the primary RIA calculations."""
import csv
import json
import hashlib
from pathlib import Path
import numpy as np
from scipy.spatial.distance import cdist, pdist
from scipy.stats import spearmanr, trim_mean

ROOT = Path(__file__).resolve().parents[2]
UP = ROOT / "evidence/source_probe_crossed_audit_v0"
OUT = ROOT / "evidence/relational_identifiability_a0"
FOLDS = ((0, 4, 8, 12), (1, 5, 9, 13), (2, 6, 10, 14), (3, 7, 11, 15))

def rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))

def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for x in iter(lambda: f.read(1 << 20), b""):
            h.update(x)
    return h.hexdigest()

def calc(a, b):
    mean_a, mean_b = a.mean(0), b.mean(0)
    signal = np.dot(mean_a - mean_b, mean_a - mean_b)
    within = (np.mean(np.sum((a - mean_a)**2, axis=1)) +
              np.mean(np.sum((b - mean_b)**2, axis=1))) / 2
    aa, bb = pdist(a).mean(), pdist(b).mean()
    ab = cdist(a, b).mean()
    wdist = (aa + bb) / 2
    return float(signal/(within+1e-12*max(1, within))), float((2*ab-aa-bb)/(wdist+1e-12*max(1,wdist)))

def main():
    pair = [r for r in rows(UP / "SPX_G0_FROZEN_PAIRS.csv") if r["panel"] == "CENTRAL"]
    ref = rows(OUT / "RIA_A0_REFERENCE_IDENTIFIABILITY.csv")
    refkey = {(int(r["pair_index"]), r["protocol"]):r for r in ref}
    diffs = []
    byprotocol = {}
    for protocol in ("P_G1A", "P_E2"):
        bank = np.load(UP / f"SPX_G0_CENTRAL_{protocol}_10x30.npy", mmap_mode="r")
        vals = []
        for r in pair:
            idx = int(r["pair_index"])
            a = bank[int(r["source0_index"])].reshape(16,300)
            b = bank[int(r["source1_index"])].reshape(16,300)
            calc4 = [calc(a[[i for i in range(16) if i not in test]],
                          b[[i for i in range(16) if i not in test]]) for test in FOLDS]
            m = np.mean(calc4, axis=0)
            target = refkey[idx,protocol]
            diffs.extend([abs(m[0]-float(target["D_CNR"])), abs(m[1]-float(target["D_ED"]))])
            vals.append(m)
        byprotocol[protocol] = np.array(vals)
    op = rows(OUT / "RIA_A0_BOUNDED_OPERATIONAL.csv")
    target = [r for r in rows(UP / "SPX_G0_TARGET_METRICS.csv") if r["panel"] == "CENTRAL"]
    grouped = {}
    for r in target:
        grouped.setdefault((int(r["pair_index"]),r["protocol"],r["model"]),[]).append(r)
    operational_diffs=[]
    for r in op:
        i = int(r["pair_index"])
        for protocol in ("P_G1A","P_E2"):
            aa=[]; bb=[]
            for model in ("FULL","BLOCK_PRODUCT","MATCHED_BLOCK_DIAG"):
                block=grouped[i,protocol,model]
                assert len(block)==32
                aa.append(np.mean([float(t["accuracy"]) for t in block]))
                bb.append(np.mean([float(t["brier"]) for t in block]))
            operational_diffs.extend((abs(np.median(aa)-float(r[f"A_{protocol}"])),
                                      abs(-np.median(bb)-float(r[f"B_{protocol}"]))))
    risk_diffs=[]
    for r in rows(OUT/"RIA_A0_ESTIMATOR_RISK.csv"):
        block=grouped[int(r["pair_index"]),r["protocol"],r["model"]]
        z=np.array([float(t["two_class_nll"]) for t in block])
        correct=np.array([float(t["accuracy"]) for t in block])
        wrong=correct<.5
        expected={"mean_nll":z.mean(),"trimmed20_nll":trim_mean(z,.2),
                  "tail_excess":z.mean()-trim_mean(z,.2),
                  "misclassification_rate":wrong.mean(),"q95_nll":np.quantile(z,.95),
                  "max_nll":z.max()}
        if wrong.any():
            expected["mean_nll_given_error"]=z[wrong].mean()
        else:
            assert r["mean_nll_given_error"]==""
        risk_diffs.extend(abs(float(r[k])-float(v)) for k,v in expected.items())
    d=byprotocol["P_E2"]-byprotocol["P_G1A"]
    y=np.array([[float(r["Delta_A"]),float(r["Delta_B"])] for r in op])
    corr={f"{descriptor}__{bounded}":float(spearmanr(d[:,di],y[:,bi]).statistic)
          for di,descriptor in enumerate(("D_CNR","D_ED"))
          for bi,bounded in enumerate(("A","B"))}
    frozen=json.loads((OUT/"RIA_A0_ASSOCIATIONS.json").read_text())["associations"]
    corr_diff=max(abs(v-frozen[k]["spearman"]) for k,v in corr.items())
    result=json.loads((OUT/"RIA_A0_RESULT.json").read_text())
    assert max(diffs)<1e-7 and max(operational_diffs)<1e-12 and max(risk_diffs)<1e-10 and corr_diff<1e-12
    assert all(frozen[k]["bootstrap95"][0]>0 for k in corr)
    assert result["decision"]=="RIA_A0_PHYSICAL_IDENTIFIABILITY_TARGET_SUPPORTED"
    audit={"decision_matches":True,"central_pairs":len(pair),"raw_descriptor_max_abs_difference":max(diffs),
           "bounded_target_level_max_abs_difference":max(operational_diffs),
           "estimator_risk_max_abs_difference":max(risk_diffs),
           "four_association_max_abs_difference":corr_diff,"independent_associations":corr,
           "crossed_input_sha256":{p:digest(UP/f"SPX_G0_CENTRAL_{p}_10x30.npy") for p in ("P_G1A","P_E2")},
           "reference_csv_sha256":digest(OUT/"RIA_A0_REFERENCE_IDENTIFIABILITY.csv"),
           "heldout_target_csv_sha256":digest(UP/"SPX_G0_TARGET_METRICS.csv")}
    (OUT/"RIA_A0_INDEPENDENT_RECOMPUTATION.json").write_text(json.dumps(audit,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("INDEPENDENT_RECOMPUTATION_PASS",max(diffs),max(operational_diffs))

if __name__=="__main__":
    main()

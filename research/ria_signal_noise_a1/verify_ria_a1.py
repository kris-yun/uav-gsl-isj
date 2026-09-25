#!/usr/bin/env python3
"""Independent scipy-distance recomputation of frozen RIA-A1 components."""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial.distance import cdist,pdist
from scipy.stats import rankdata,spearmanr

ROOT=Path(__file__).resolve().parents[2]
SPX=ROOT/"evidence/source_probe_crossed_audit_v0"
RIA=ROOT/"evidence/relational_identifiability_a0"
OUT=ROOT/"evidence/ria_signal_noise_a1"
FOLDS=((0,4,8,12),(1,5,9,13),(2,6,10,14),(3,7,11,15))

def rows(p):
    with open(p,newline="",encoding="utf-8") as f:return list(csv.DictReader(f))

def hashfile(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def calc(a,b):
    mu_a=a.mean(axis=0);mu_b=b.mean(axis=0)
    S=float(np.dot(mu_a-mu_b,mu_a-mu_b))
    W=float((np.sum((a-mu_a)**2,axis=1).mean()+np.sum((b-mu_b)**2,axis=1).mean())/2)
    wa=float(pdist(a).mean());wb=float(pdist(b).mean());B=float(cdist(a,b).mean())
    we=(wa+wb)/2;ed=2*B-wa-wb
    return {"S":S,"W":W,"D_CNR":S/(W+1e-12*max(1,W)),"B":B,"W_a":wa,"W_b":wb,
            "W_E":we,"ED":ed,"D_ED":ed/(we+1e-12*max(1,we))}

def independent_boot(x,y,draws):
    a=rankdata(x[draws],axis=1);b=rankdata(y[draws],axis=1)
    a-=a.mean(axis=1,keepdims=True);b-=b.mean(axis=1,keepdims=True)
    den=np.sqrt(np.sum(a*a,axis=1)*np.sum(b*b,axis=1))
    return np.divide(np.sum(a*b,axis=1),den,out=np.zeros(len(draws)),where=den>0)

def main():
    pairs=[r for r in rows(SPX/"SPX_G0_FROZEN_PAIRS.csv") if r["panel"]=="CENTRAL"]
    ref={(int(r["pair_index"]),r["protocol"],int(r["fold"])):r for r in rows(OUT/"RIA_A1_ENERGY_COMPONENTS.csv")}
    fold={(int(r["pair_index"]),int(r["fold"])):r for r in rows(OUT/"RIA_A1_FOLD_DECOMPOSITION.csv")}
    bank={p:np.load(SPX/f"SPX_G0_CENTRAL_{p}_10x30.npy",mmap_mode="r") for p in ("P_G1A","P_E2")}
    differences=[]
    for pair in pairs:
        i=int(pair["pair_index"]);a=int(pair["source0_index"]);b=int(pair["source1_index"])
        for fi,test in enumerate(FOLDS):
            train=[j for j in range(16) if j not in test]
            val={}
            for p in bank:
                x=bank[p][a,train].reshape(12,300);y=bank[p][b,train].reshape(12,300)
                val[p]=calc(x,y)
                saved=ref[i,p,fi]
                differences.extend(abs(z-float(saved[k])) for k,z in val[p].items())
            g=val["P_G1A"];e=val["P_E2"]
            sig=np.log(e["S"]+1e-12*max(1,e["S"]))-np.log(g["S"]+1e-12*max(1,g["S"]))
            noise=np.log(g["W"]+1e-12*max(1,g["W"]))-np.log(e["W"]+1e-12*max(1,e["W"]))
            derived={"signal":sig,"noise":noise,"total":sig+noise,"Delta_Between":e["B"]-g["B"],
                     "Delta_WithinED":e["W_E"]-g["W_E"],"Delta_EDnum":e["ED"]-g["ED"],
                     "Delta_D_ED":e["D_ED"]-g["D_ED"],"Delta_D_CNR":e["D_CNR"]-g["D_CNR"]}
            differences.extend(abs(z-float(fold[i,fi][k])) for k,z in derived.items())
    assert max(differences)<1e-9
    pairrows=sorted(rows(OUT/"RIA_A1_PAIR_DECOMPOSITION.csv"),key=lambda r:int(r["pair_index"]))
    bounded=sorted(rows(RIA/"RIA_A0_BOUNDED_OPERATIONAL.csv"),key=lambda r:int(r["pair_index"]))
    assoc=json.loads((OUT/"RIA_A1_ASSOCIATIONS.json").read_text())["associations"]
    draws=np.load(OUT/"RIA_A1_BOOTSTRAP_10000.npz")["pair_draws"]
    assert draws.shape==(10000,84)
    corr_diff=[];ci_diff=[]
    for key,summary in assoc.items():
        component,target=key.split("__")
        if component=="minus_Delta_WithinED":
            x=-np.array([float(r["Delta_WithinED"]) for r in pairrows])
        else:
            x=np.array([float(r[component]) for r in pairrows])
        if target in ("Delta_A","Delta_B"):
            y=np.array([float(r[target]) for r in bounded])
        else:
            y=np.array([float(r[target]) for r in pairrows])
        corr_diff.append(abs(float(spearmanr(x,y).statistic)-summary["spearman"]))
        ci_diff.extend(abs(np.quantile(independent_boot(x,y,draws),[.025,.975])-summary["bootstrap95"]))
    share=np.array([float(r["share_signal"]) for r in pairrows])
    result=json.loads((OUT/"RIA_A1_RESULT.json").read_text())
    assert result["decision"]=="RIA_A1_MIXED_SIGNAL_AND_VARIABILITY"
    assert abs(np.median(share)-.5836696979791451)<1e-12
    assert max(corr_diff)<1e-12 and max(ci_diff)<1e-12
    report={"decision_matches":True,"fold_rows":336,"energy_rows":672,"pair_rows":84,
            "max_absolute_fold_difference":max(differences),"max_absolute_correlation_difference":max(corr_diff),
            "max_absolute_bootstrap_ci_difference":max(ci_diff),
            "share_signal_median":float(np.median(share)),"share_signal_gt_half_fraction":float(np.mean(share>.5)),
            "result_sha256":hashfile(OUT/"RIA_A1_RESULT.json"),
            "input_sha256":{p:hashfile(SPX/f"SPX_G0_CENTRAL_{p}_10x30.npy") for p in bank}}
    (OUT/"RIA_A1_INDEPENDENT_RECOMPUTATION.json").write_bytes((json.dumps(report,sort_keys=True,indent=2)+"\n").encode())
    print("RIA_A1_INDEPENDENT_PASS",max(differences),max(corr_diff),max(ci_diff))

if __name__=="__main__":main()

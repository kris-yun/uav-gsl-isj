#!/usr/bin/env python3
"""Frozen RIA-A1 algebraic signal/variability decomposition."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import rankdata, spearmanr

ROOT=Path(__file__).resolve().parents[2]
SPX=ROOT/"evidence/source_probe_crossed_audit_v0"
RIA=ROOT/"evidence/relational_identifiability_a0"
OUT=ROOT/"evidence/ria_signal_noise_a1"
CODE=Path(__file__).resolve()
FOLDS=((0,4,8,12),(1,5,9,13),(2,6,10,14),(3,7,11,15))
PROTOCOLS=("P_G1A","P_E2")
SEED=202609260

def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def loadcsv(p):
    with open(p,newline="",encoding="utf-8") as f:return list(csv.DictReader(f))

def savecsv(p,rows):
    if not rows:raise ValueError("empty output")
    with open(p,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n")
        w.writeheader();w.writerows(rows)

def savejson(p,value):
    p.write_bytes((json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+"\n").encode())

def tensor_files():
    return {p:SPX/f"SPX_G0_CENTRAL_{p}_10x30.npy" for p in PROTOCOLS}

def audit():
    lock=json.loads((SPX/"SPX_G0_PRE_SCORE_LOCK.json").read_text())
    ria_lock=json.loads((RIA/"RIA_A0_PRE_RUN_LOCK.json").read_text())
    assert tuple(tuple(x) for x in ria_lock["folds_heldout"])==FOLDS
    assert sha(SPX/"SPX_G0_FROZEN_PAIRS.csv")==lock["pairs_sha256"]
    for p,file in tensor_files().items():
        assert sha(file)==lock["crossed_tensor_sha256"][f"CENTRAL_{p}"]
        t=np.load(file,mmap_mode="r")
        assert t.shape==(168,16,10,30) and np.isfinite(t).all()
    assert len([x for x in loadcsv(SPX/"SPX_G0_FROZEN_PAIRS.csv") if x["panel"]=="CENTRAL"])==84
    assert json.loads((RIA/"RIA_A0_RESULT.json").read_text())["decision"]=="RIA_A0_PHYSICAL_IDENTIFIABILITY_TARGET_SUPPORTED"
    return {"spx_pairs_sha256":lock["pairs_sha256"],
            "crossed_tensor_sha256":{p:sha(f) for p,f in tensor_files().items()},
            "ria_reference_sha256":sha(RIA/"RIA_A0_REFERENCE_IDENTIFIABILITY.csv"),
            "ria_bounded_sha256":sha(RIA/"RIA_A0_BOUNDED_OPERATIONAL.csv")}

def lock_stage():
    OUT.mkdir(parents=True,exist_ok=True)
    v=audit()
    lock={"branch":"research/ria-signal-noise-decomposition-a1-20260926",
          "code_sha256":sha(CODE),"charter_sha256":sha(ROOT/"research/ria_signal_noise_a1/RIA_A1_CHARTER_20260926.md"),
          "inputs":v,"folds_heldout":FOLDS,"source_pairs":84,"bootstrap_seed":SEED,"bootstrap_draws":10000,
          "epsilon":"For each S,W,W_E separately: 1e-12*max(1,corresponding scale)",
          "sign_ties":"exclude |value|<1e-10", "fold_aggregation":"arithmetic mean across four SPX/RIA folds",
          "diagnostic_priority":"signal dominance, then symmetric within dominance, otherwise mixed"}
    savejson(OUT/"RIA_A1_PRE_RUN_LOCK.json",lock)
    print("A1_PRE_RUN_LOCK",sha(OUT/"RIA_A1_PRE_RUN_LOCK.json"))

def raw_metrics(a,b):
    ma,mb=a.mean(0),b.mean(0)
    signal=float(np.sum((ma-mb)**2))
    within=float((np.mean(np.sum((a-ma)**2,axis=1))+np.mean(np.sum((b-mb)**2,axis=1)))/2)
    aa=np.sqrt(np.maximum(0,np.sum((a[:,None,:]-a[None,:,:])**2,axis=2)))
    bb=np.sqrt(np.maximum(0,np.sum((b[:,None,:]-b[None,:,:])**2,axis=2)))
    ab=np.sqrt(np.maximum(0,np.sum((a[:,None,:]-b[None,:,:])**2,axis=2)))
    n,m=len(a),len(b)
    wa=float((aa.sum()-np.trace(aa))/(n*(n-1)))
    wb=float((bb.sum()-np.trace(bb))/(m*(m-1)))
    B=float(ab.mean());we=(wa+wb)/2
    ed=2*B-wa-wb
    return {"S":signal,"W":within,"D_CNR":signal/(within+1e-12*max(1,within)),
            "B":B,"W_a":wa,"W_b":wb,"W_E":we,"ED":ed,
            "D_ED":ed/(we+1e-12*max(1,we))}

def decompose_stage():
    lock=json.loads((OUT/"RIA_A1_PRE_RUN_LOCK.json").read_text())
    assert sha(CODE)==lock["code_sha256"]
    assert audit()==lock["inputs"]
    tensors={p:np.load(f) for p,f in tensor_files().items()}
    pairs=[r for r in loadcsv(SPX/"SPX_G0_FROZEN_PAIRS.csv") if r["panel"]=="CENTRAL"]
    reference={(int(r["pair_index"]),r["protocol"]):r for r in loadcsv(RIA/"RIA_A0_REFERENCE_IDENTIFIABILITY.csv")}
    folds=[];energy=[];aggregated=[]
    max_upstream=0.;max_log_identity=0.;max_ed_identity=0.
    for pair in pairs:
        i=int(pair["pair_index"]);ai=int(pair["source0_index"]);bi=int(pair["source1_index"])
        local=[]
        for f,test in enumerate(FOLDS):
            train=[j for j in range(16) if j not in test]
            vals={p:raw_metrics(tensors[p][ai,train].reshape(12,300),tensors[p][bi,train].reshape(12,300)) for p in PROTOCOLS}
            for p in PROTOCOLS:
                row={"pair_index":i,"protocol":p,"fold":f,**vals[p]}
                energy.append(row)
            old,new=vals["P_G1A"],vals["P_E2"]
            signal=np.log(new["S"]+1e-12*max(1,new["S"]))-np.log(old["S"]+1e-12*max(1,old["S"]))
            noise=-(np.log(new["W"]+1e-12*max(1,new["W"]))-np.log(old["W"]+1e-12*max(1,old["W"])))
            total=signal+noise
            if old["D_CNR"]>0 and new["D_CNR"]>0:
                max_log_identity=max(max_log_identity,abs(total-(np.log(new["D_CNR"])-np.log(old["D_CNR"]))))
            max_ed_identity=max(max_ed_identity,abs((new["ED"]-old["ED"])-(2*(new["B"]-old["B"])-2*(new["W_E"]-old["W_E"]))))
            local.append({"pair_index":i,"fold":f,"signal":float(signal),"noise":float(noise),"total":float(total),
                          "Delta_Between":new["B"]-old["B"],"Delta_WithinED":new["W_E"]-old["W_E"],
                          "Delta_EDnum":new["ED"]-old["ED"],"Delta_D_ED":new["D_ED"]-old["D_ED"],
                          "Delta_D_CNR":new["D_CNR"]-old["D_CNR"]})
        folds.extend(local)
        for p in PROTOCOLS:
            for key in ("S","W","D_CNR","W_E","ED","D_ED"):
                mean=np.mean([r[key] for r in energy if r["pair_index"]==i and r["protocol"]==p])
                max_upstream=max(max_upstream,abs(mean-float(reference[i,p][key])))
        aggregate={"pair_index":i}
        for key in ("signal","noise","total","Delta_Between","Delta_WithinED","Delta_EDnum","Delta_D_ED","Delta_D_CNR"):
            aggregate[key]=float(np.mean([r[key] for r in local]))
        aggregate["share_signal"]=abs(aggregate["signal"])/(abs(aggregate["signal"])+abs(aggregate["noise"])+1e-12)
        aggregated.append(aggregate)
    if max_upstream>1e-8 or max_log_identity>1e-10 or max_ed_identity>1e-10:
        raise ValueError(f"algebra/RIA verification failed: {max_upstream},{max_log_identity},{max_ed_identity}")
    savecsv(OUT/"RIA_A1_FOLD_DECOMPOSITION.csv",folds)
    savecsv(OUT/"RIA_A1_PAIR_DECOMPOSITION.csv",aggregated)
    savecsv(OUT/"RIA_A1_ENERGY_COMPONENTS.csv",energy)
    savejson(OUT/"RIA_A1_DECOMPOSITION_FREEZE.json",{"fold_rows":len(folds),"pair_rows":len(aggregated),
             "energy_rows":len(energy),"max_abs_RIA_reference_difference":max_upstream,
             "max_abs_CNR_log_identity_error":max_log_identity,"max_abs_ED_identity_error":max_ed_identity,
             "bounded_metrics_imported":False,"sha256":{name:sha(OUT/name) for name in (
                 "RIA_A1_FOLD_DECOMPOSITION.csv","RIA_A1_PAIR_DECOMPOSITION.csv","RIA_A1_ENERGY_COMPONENTS.csv")}})
    print("A1_DECOMPOSITION_FREEZE",max_upstream,max_log_identity,max_ed_identity)

def rho(x,y):
    return float(spearmanr(x,y).statistic)

def bootstrap_rho(x,y,draws):
    a=rankdata(x[draws],axis=1);b=rankdata(y[draws],axis=1)
    a-=a.mean(axis=1,keepdims=True);b-=b.mean(axis=1,keepdims=True)
    denom=np.sqrt(np.sum(a*a,axis=1)*np.sum(b*b,axis=1))
    return np.divide(np.sum(a*b,axis=1),den,out=np.zeros(len(draws)),where=denom>0)

def agreement(x,y):
    use=(np.abs(x)>=1e-10)&(np.abs(y)>=1e-10)
    return {"count":int(np.sum(use)),"fraction":float(np.mean(np.sign(x[use])==np.sign(y[use]))) if use.any() else None}

def diagnose_stage():
    lock=json.loads((OUT/"RIA_A1_PRE_RUN_LOCK.json").read_text())
    assert sha(CODE)==lock["code_sha256"]
    freeze=json.loads((OUT/"RIA_A1_DECOMPOSITION_FREEZE.json").read_text())
    for name,h in freeze["sha256"].items():assert sha(OUT/name)==h
    pairs=loadcsv(OUT/"RIA_A1_PAIR_DECOMPOSITION.csv")
    assert len(pairs)==84
    bounded=sorted(loadcsv(RIA/"RIA_A0_BOUNDED_OPERATIONAL.csv"),key=lambda r:int(r["pair_index"]))
    assert len(bounded)==84
    x={k:np.array([float(r[k]) for r in pairs]) for k in ("signal","noise","total","share_signal","Delta_Between","Delta_WithinED","Delta_EDnum","Delta_D_ED","Delta_D_CNR")}
    x["minus_Delta_WithinED"]=-x["Delta_WithinED"]
    y={k:np.array([float(r[k]) for r in bounded]) for k in ("Delta_A","Delta_B")}
    y.update({"Delta_D_CNR":x["Delta_D_CNR"],"Delta_D_ED":x["Delta_D_ED"]})
    rng=np.random.default_rng(SEED)
    draws=rng.integers(0,84,(10000,84),dtype=np.int32)
    assoc={};samples={}
    combos=[(component,target) for component in ("signal","noise") for target in ("Delta_A","Delta_B","Delta_D_CNR","Delta_D_ED")]
    combos += [(component,target) for component in ("Delta_Between","minus_Delta_WithinED") for target in ("Delta_D_ED","Delta_A","Delta_B")]
    for component,target in combos:
        k=f"{component}__{target}";r=rho(x[component],y[target]);bs=bootstrap_rho(x[component],y[target],draws)
        assoc[k]={"spearman":r,"bootstrap95":np.quantile(bs,[.025,.975]).tolist()}
        samples[k]=bs
    signs={f"{a}__{b}":agreement(x[a],x[b] if b=="total" else y[b])
           for a in ("signal","noise") for b in ("total","Delta_A","Delta_B")}
    shares={"median":float(np.median(x["share_signal"])),"q25":float(np.quantile(x["share_signal"],.25)),
            "q75":float(np.quantile(x["share_signal"],.75)),
            "fraction_gt_0p5":float(np.mean(x["share_signal"]>.5))}
    def primary(component,other,share,edcomponent):
        main=[assoc[f"{component}__{b}"] for b in ("Delta_A","Delta_B")]
        alt=[assoc[f"{other}__{b}"] for b in ("Delta_A","Delta_B")]
        return (all(a["spearman"]>0 and a["bootstrap95"][0]>0 for a in main)
                and all(a["bootstrap95"][0]<=0<=a["bootstrap95"][1] or abs(a["spearman"])<.15 for a in alt)
                and float(np.median(share))>=.65 and float(np.mean(share>.5))>=.70
                and assoc[f"{edcomponent}__Delta_D_ED"]["spearman"]>0)
    signal_pass=primary("signal","noise",x["share_signal"],"Delta_Between")
    noise_share=np.abs(x["noise"])/(np.abs(x["signal"])+np.abs(x["noise"])+1e-12)
    noise_pass=primary("noise","signal",noise_share,"minus_Delta_WithinED")
    decision=("RIA_A1_SIGNAL_SEPARATION_DOMINANT" if signal_pass else
              "RIA_A1_WITHIN_VARIABILITY_DOMINANT" if noise_pass else
              "RIA_A1_MIXED_SIGNAL_AND_VARIABILITY")
    savejson(OUT/"RIA_A1_ASSOCIATIONS.json",{"associations":assoc,"share_signal":shares,
             "share_noise":{"median":float(np.median(noise_share)),"fraction_gt_0p5":float(np.mean(noise_share>.5))},
             "sign_agreements":signs,"signal_gate_pass":bool(signal_pass),"within_gate_pass":bool(noise_pass)})
    np.savez_compressed(OUT/"RIA_A1_BOOTSTRAP_10000.npz",pair_draws=draws,**samples)
    savejson(OUT/"RIA_A1_RESULT.json",{"decision":decision,"central_pairs":84,"new_plume":0,
             "ria_a0_retained":True,"rpo_g0_stop_retained":True,
             "decomposition_freeze_sha256":sha(OUT/"RIA_A1_DECOMPOSITION_FREEZE.json"),
             "associations_sha256":sha(OUT/"RIA_A1_ASSOCIATIONS.json")})
    print("A1_DECISION",decision)

def main():
    ap=argparse.ArgumentParser();ap.add_argument("stage",choices=("lock","decompose","diagnose"))
    args=ap.parse_args()
    {"lock":lock_stage,"decompose":decompose_stage,"diagnose":diagnose_stage}[args.stage]()

if __name__=="__main__":main()

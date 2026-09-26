#!/usr/bin/env python3
"""Score frozen SOLICM-G0 target logits only after all 96 runs finish."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.special import logsumexp,softmax
from sklearn.metrics import f1_score

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"evidence/solicm_v0/g0"
RUNS=Path(r"D:\ZYC\A-gas\_staging\SOLICM_G0_RUNS_20260926")
VARIANTS=("SOURCE_ONLY","PL_ONLY","LCA_NO_ALIGN","LCA_FULL")
DIRECTIONS=("W0_to_W2","W2_to_W0")
SEEDS=(0,1,2)
PAIRS=((0,1),(2,3),(4,5))
CODE=Path(__file__).resolve()

def digest(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def writejson(path,value):
    path.write_bytes((json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+"\n").encode())

def writecsv(path,rows):
    if not rows:raise ValueError("empty table")
    with open(path,"w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n")
        w.writeheader();w.writerows(rows)

def runid(direction,fold,seed,variant):
    return f"{direction}__fold{fold}__seed{seed}__{variant}"

def allruns():
    for direction in DIRECTIONS:
        for fold in range(4):
            for seed in SEEDS:
                for variant in VARIANTS:
                    yield direction,fold,seed,variant,runid(direction,fold,seed,variant)

def audit_runs():
    locksha=digest(OUT/"SOLICM_G0_PRE_RUN_LOCK.json")
    entries=[]
    for direction,fold,seed,variant,name in allruns():
        folder=RUNS/name
        donefile=folder/"COMPLETE.json"
        if not donefile.exists():raise FileNotFoundError(donefile)
        done=json.loads(donefile.read_text())
        config=json.loads((folder/"config.json").read_text())
        assert done["pre_run_lock_sha256"]==locksha and config["pre_run_lock_sha256"]==locksha
        assert config["target_labels_available_to_training"] is False
        assert config["source_count"]==96 and config["target_unlabeled_count"]==72 and config["target_heldout_count"]==24
        assert (config["direction"],config["fold"],config["seed"],config["variant"])==(direction,fold,seed,variant)
        logits=folder/"heldout_logits.npy"
        assert digest(logits)==done["heldout_logits_sha256"]
        arr=np.load(logits,mmap_mode="r")
        assert arr.shape==(24,6) and np.isfinite(arr).all()
        assert digest(folder/"best_checkpoint.pt")==done["checkpoint_sha256"]
        if variant.startswith("LCA_"):
            assert digest(folder/"latent_structure.npz")==done["latent_structure_sha256"]
        entries.append({"runid":name,"direction":direction,"fold":fold,"seed":seed,"variant":variant,
                        "best_epoch":done["best_epoch"],"source_risk":done["source_risk"],
                        "logits_sha256":done["heldout_logits_sha256"],"checkpoint_sha256":done["checkpoint_sha256"],
                        "config_sha256":digest(folder/"config.json"),"history_sha256":digest(folder/"training_history.json"),
                        "latent_structure_sha256":done["latent_structure_sha256"] or ""})
    assert len(entries)==96
    return entries

def lock_stage():
    entries=audit_runs()
    writecsv(OUT/"SOLICM_G0_RUN_MANIFEST.csv",entries)
    lock={"branch":"research/solicm-latent-causal-g0-20260926",
          "scorer_sha256":digest(CODE),"training_lock_sha256":digest(OUT/"SOLICM_G0_PRE_RUN_LOCK.json"),
          "run_manifest_sha256":digest(OUT/"SOLICM_G0_RUN_MANIFEST.csv"),
          "run_count":96,"target_count_per_run":24,"target_source_ids_from_frozen_data_audit":json.loads((OUT/"SOLICM_G0_DATA_AUDIT.json").read_text())["source_ids"],
          "seed_aggregation":"average metrics over seeds at each target realization, then average targets within source/direction",
          "cluster_bootstrap":"12 direction x source units with replacement, 10000 draws, percentile 95% interval",
          "bootstrap_seed":2026092602,"primary_delta_align":"NLL(LCA_NO_ALIGN)-NLL(LCA_FULL)",
          "secondary_delta_PL":"NLL(PL_ONLY)-NLL(LCA_FULL)",
          "Brier":"sum of six squared class-probability errors", "adjacent_pairs":PAIRS,
          "gate_priority":"PASS G0-1..6; HOLD only G0-1..5 pass and G0-6 fails; STOP otherwise"}
    file=OUT/"SOLICM_G0_PRE_SCORE_LOCK.json"
    if file.exists():assert json.loads(file.read_text())==lock
    else:writejson(file,lock)
    print("SOLICM_PRE_SCORE_LOCK",digest(file))

def score_stage():
    lock=json.loads((OUT/"SOLICM_G0_PRE_SCORE_LOCK.json").read_text())
    assert digest(CODE)==lock["scorer_sha256"]
    assert digest(OUT/"SOLICM_G0_RUN_MANIFEST.csv")==lock["run_manifest_sha256"]
    audit_runs()
    # Only this stage reconstructs held-out target source labels from source-major tensor order.
    truth=np.repeat(np.arange(6),4)
    logits_cube=np.empty((2,4,3,4,24,6),dtype=np.float32)
    target_rows=[];run_rows=[];pair_rows=[];latent_rows=[]
    latent_mags=np.zeros((2,4,3,2,2,30,30),dtype=np.float32)
    latent_masks=np.zeros((2,4,3,2,2,30,30),dtype=np.bool_)
    for di,direction in enumerate(DIRECTIONS):
        for fold in range(4):
            for seed in SEEDS:
                for vi,variant in enumerate(VARIANTS):
                    folder=RUNS/runid(direction,fold,seed,variant)
                    logits=np.load(folder/"heldout_logits.npy").astype(np.float64)
                    logits_cube[di,fold,seed,vi]=logits.astype(np.float32)
                    logprob=logits-logsumexp(logits,axis=1,keepdims=True)
                    prob=np.exp(logprob)
                    nll=-logprob[np.arange(24),truth]
                    eye=np.eye(6)[truth]
                    brier=np.sum((prob-eye)**2,axis=1)
                    pred=np.argmax(logits,axis=1)
                    correct=(pred==truth).astype(int)
                    rank=1+np.sum(logits>logits[np.arange(24),truth][:,None],axis=1)
                    entropy=-np.sum(prob*logprob,axis=1)
                    f1=float(f1_score(truth,pred,labels=list(range(6)),average="macro",zero_division=0))
                    run_rows.append({"direction":direction,"fold":fold,"seed":seed,"variant":variant,
                                     "mean_nll":float(nll.mean()),"mean_brier":float(brier.mean()),
                                     "accuracy":float(correct.mean()),"macro_f1":f1,
                                     "top3_accuracy":float(np.mean(rank<=3))})
                    for i in range(24):
                        src=i//4;rep=fold*4+i%4
                        partner=src+1 if src%2==0 else src-1
                        pair_prob=float(prob[i,src]/(prob[i,src]+prob[i,partner]))
                        row={"direction":direction,"fold":fold,"seed":seed,"variant":variant,
                             "source_index":src,"replicate_index":rep,"truth":src,"nll":float(nll[i]),
                             "brier":float(brier[i]),"accuracy":int(correct[i]),"truth_rank":int(rank[i]),
                             "top3":int(rank[i]<=3),"entropy":float(entropy[i]),
                             "partner_index":partner,"truth_vs_partner_log_odds":float(logits[i,src]-logits[i,partner]),
                             "pair_restricted_brier":2*(1-pair_prob)**2,
                             "pair_restricted_accuracy":int(pair_prob>.5)}
                        target_rows.append(row)
                    if variant in ("LCA_NO_ALIGN","LCA_FULL"):
                        z=np.load(folder/"latent_structure.npz")
                        kind=0 if variant=="LCA_NO_ALIGN" else 1
                        for domain_i,domain in enumerate(("source","target_unlabeled")):
                            latent_mags[di,fold,seed,kind,domain_i]=z["src_magnitude" if domain_i==0 else "tgt_magnitude"]
                            latent_masks[di,fold,seed,kind,domain_i]=z["src_mask" if domain_i==0 else "tgt_mask"]
                        latent_rows.append({"direction":direction,"fold":fold,"seed":seed,"variant":variant,
                            "weighted_structure_discrepancy":float(z["weighted_discrepancy"]),
                            "mask_jaccard":float(z["mask_jaccard"]),
                            "learned_threa":float(z["learned_threa"]),"threshold":float(z["threshold"])})
    writecsv(OUT/"SOLICM_G0_TARGET_METRICS.csv",target_rows)
    writecsv(OUT/"SOLICM_G0_RUN_METRICS.csv",run_rows)
    writecsv(OUT/"SOLICM_G0_LATENT_STRUCTURE_AUDIT.csv",latent_rows)
    np.save(OUT/"SOLICM_G0_TARGET_LOGITS.npy",logits_cube,allow_pickle=False)
    np.save(OUT/"SOLICM_G0_TARGET_PROBABILITIES.npy",softmax(logits_cube.astype(np.float64),axis=-1),allow_pickle=False)
    np.savez_compressed(OUT/"SOLICM_G0_LATENT_STRUCTURE_AUDIT.npz",magnitudes=latent_mags,masks=latent_masks)
    # Seed-level target metrics are averaged at fixed direction/source/replicate.
    grouped={}
    for r in target_rows:
        key=(r["direction"],int(r["source_index"]),int(r["replicate_index"]),r["variant"])
        grouped.setdefault(key,[]).append(r)
    per_target={}
    for key,rr in grouped.items():
        assert len(rr)==3
        per_target[key]={metric:float(np.mean([float(r[metric]) for r in rr])) for metric in
                         ("nll","brier","accuracy","top3","entropy","pair_restricted_brier","pair_restricted_accuracy","truth_vs_partner_log_odds")}
    unit_rows=[]
    for direction in DIRECTIONS:
        for source in range(6):
            byvariant={v:{metric:float(np.mean([per_target[direction,source,rep,v][metric] for rep in range(16)]))
                          for metric in ("nll","brier","accuracy","top3","entropy","pair_restricted_brier","pair_restricted_accuracy","truth_vs_partner_log_odds")}
                       for v in VARIANTS}
            row={"direction":direction,"source_index":source,
                 "delta_align":byvariant["LCA_NO_ALIGN"]["nll"]-byvariant["LCA_FULL"]["nll"],
                 "delta_PL":byvariant["PL_ONLY"]["nll"]-byvariant["LCA_FULL"]["nll"]}
            for v in VARIANTS:
                for metric,value in byvariant[v].items():row[f"{v}_{metric}"]=value
            unit_rows.append(row)
    writecsv(OUT/"SOLICM_G0_DIRECTION_SOURCE_SUMMARY.csv",unit_rows)
    seed_rows=[]
    for direction in DIRECTIONS:
        for seed in SEEDS:
            byvariant={v:[r for r in target_rows if r["direction"]==direction and r["seed"]==seed and r["variant"]==v] for v in VARIANTS}
            row={"direction":direction,"seed":seed,
                 "delta_align":float(np.mean([float(r["nll"]) for r in byvariant["LCA_NO_ALIGN"]])-
                                      np.mean([float(r["nll"]) for r in byvariant["LCA_FULL"]]))}
            for v in VARIANTS:
                row[f"{v}_nll"]=float(np.mean([float(r["nll"]) for r in byvariant[v]]))
            seed_rows.append(row)
    writecsv(OUT/"SOLICM_G0_SEED_SUMMARY.csv",seed_rows)
    for direction in DIRECTIONS:
        for vi,variant in enumerate(VARIANTS):
            for pi,(a,b) in enumerate(PAIRS):
                rr=[r for r in target_rows if r["direction"]==direction and r["variant"]==variant and int(r["source_index"]) in (a,b)]
                pair_rows.append({"direction":direction,"variant":variant,"pair_index":pi,
                                  "source0_index":a,"source1_index":b,"target_count_including_seeds":len(rr),
                                  "mean_truth_vs_partner_log_odds":float(np.mean([float(r["truth_vs_partner_log_odds"]) for r in rr])),
                                  "mean_pair_restricted_brier":float(np.mean([float(r["pair_restricted_brier"]) for r in rr])),
                                  "pair_restricted_accuracy":float(np.mean([float(r["pair_restricted_accuracy"]) for r in rr]))})
    writecsv(OUT/"SOLICM_G0_ADJACENT_PAIR_SUMMARY.csv",pair_rows)
    rng=np.random.default_rng(2026092602)
    draws=rng.integers(0,12,(10000,12),dtype=np.int32)
    da=np.array([float(r["delta_align"]) for r in unit_rows]);dp=np.array([float(r["delta_PL"]) for r in unit_rows])
    boot_align=da[draws].mean(axis=1);boot_pl=dp[draws].mean(axis=1)
    np.savez_compressed(OUT/"SOLICM_G0_CLUSTER_BOOTSTRAP_10000.npz",cluster_draws=draws,
                        delta_align=boot_align,delta_PL=boot_pl)
    directions={}
    for direction in DIRECTIONS:
        rr=[r for r in unit_rows if r["direction"]==direction]
        ss=[r for r in seed_rows if r["direction"]==direction]
        directions[direction]={"mean_delta_align":float(np.mean([float(r["delta_align"]) for r in rr])),
             "mean_delta_PL":float(np.mean([float(r["delta_PL"]) for r in rr])),
             "positive_source_units":int(sum(float(r["delta_align"])>0 for r in rr)),
             "mean_brier":{v:float(np.mean([float(r[f"{v}_brier"]) for r in rr])) for v in VARIANTS},
             "accuracy":{v:float(np.mean([float(r[f"{v}_accuracy"]) for r in rr])) for v in VARIANTS},
             "seed_delta_align":[float(r["delta_align"]) for r in ss],
             "seed_full_nll_ratio_to_no_align":[float(r["LCA_FULL_nll"])/float(r["LCA_NO_ALIGN_nll"]) for r in ss]}
    g1=all(v["mean_delta_align"]>0 for v in directions.values())
    ci_align=np.quantile(boot_align,[.025,.975]).tolist()
    ci_pl=np.quantile(boot_pl,[.025,.975]).tolist()
    g2=ci_align[0]>0
    g3=sum(v["positive_source_units"] for v in directions.values())>=8 and all(v["positive_source_units"]>=4 for v in directions.values())
    g4=all(v["mean_delta_PL"]>0 for v in directions.values()) and ci_pl[0]>0
    g5=all(v["mean_brier"]["LCA_FULL"]<v["mean_brier"]["LCA_NO_ALIGN"] and
           v["mean_brier"]["LCA_FULL"]<v["mean_brier"]["PL_ONLY"] and
           v["accuracy"]["LCA_FULL"]>=max(v["accuracy"]["LCA_NO_ALIGN"],v["accuracy"]["PL_ONLY"])-.02
           for v in directions.values())
    g6=all(float(np.median(v["seed_delta_align"]))>0 and max(v["seed_full_nll_ratio_to_no_align"])<=1.10 for v in directions.values())
    gates={"G0_1":bool(g1),"G0_2":bool(g2),"G0_3":bool(g3),"G0_4":bool(g4),"G0_5":bool(g5),"G0_6":bool(g6)}
    decision=("SOLICM_G0_PASS_LATENT_CAUSAL_ALIGNMENT_TRANSFER_SIGNAL" if all(gates.values()) else
              "SOLICM_G0_HOLD_UNSTABLE_NEURAL_TRANSFER_SIGNAL" if all([g1,g2,g3,g4,g5]) else
              "SOLICM_G0_STOP_LATENT_CAUSAL_ALIGNMENT_NOT_SOURCE_USEFUL")
    writejson(OUT/"SOLICM_G0_RESULT.json",{"decision":decision,"gates":gates,"directions":directions,
          "pooled_delta_align":float(da.mean()),"pooled_delta_align_CI95":ci_align,
          "pooled_delta_PL":float(dp.mean()),"pooled_delta_PL_CI95":ci_pl,
          "positive_direction_source_units":int(np.sum(da>0)),"training_runs":96,"new_plume":0,
          "target_labels_unavailable_during_training":True,
          "pre_score_lock_sha256":digest(OUT/"SOLICM_G0_PRE_SCORE_LOCK.json")})
    print("SOLICM_G0_DECISION",decision)

def main():
    ap=argparse.ArgumentParser();ap.add_argument("stage",choices=("lock","score"))
    args=ap.parse_args()
    {"lock":lock_stage,"score":score_stage}[args.stage]()

if __name__=="__main__":main()

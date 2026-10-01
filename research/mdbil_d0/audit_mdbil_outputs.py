"""Independent post-execution contract, aggregation and frozen-gate audit.

No training, alternative split, scorer or scientific gate is introduced.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np


def rows(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cos_prototypes(train, labels, target, target_labels):
    # Separate implementation of the frozen cosine prototype diagnostics.
    centers=np.stack([train[labels==s].mean(axis=0) for s in (0,1)])
    norm=lambda v:v/np.maximum(np.sqrt(np.sum(v*v,axis=1,keepdims=True)),1e-12)
    a=norm(target);b=norm(centers)
    similarity=np.matmul(a,b.T)
    correct=similarity[np.arange(len(target_labels)),target_labels]
    wrong=similarity[np.arange(len(target_labels)),1-target_labels]
    separation=max(1-np.matmul(b[:1],b[1:].T)[0,0],1e-6)
    return float(np.mean(similarity.argmax(axis=1)==target_labels)),float(np.median(correct-wrong)),float(np.median((1-correct)/separation))


def independent_gates(folds):
    val=lambda name:np.array([float(r[name]) for r in folds])
    accuracy=val("invariant_accuracy");margin=val("invariant_margin")
    ratio=val("invariant_ratio");wind=val("invariant_wind_ratio")
    reference=max(float(np.median(val(k+"_accuracy"))) for k in ("raw","static","vanilla"))
    g1=np.median(accuracy)>=.75 and np.sum(accuracy>=.75)>=6 and np.median(margin)>0 and np.sum(margin>0)>=7
    g2=np.median(ratio)<.75 and np.sum(ratio<1)>=6 and np.median(wind)<1 and np.sum(wind<1)>=6
    gain={k:val(k+"_ratio")-ratio for k in ("raw","static","vanilla")}
    wind_gain={k:val(k+"_wind_ratio")-wind for k in ("raw","static","vanilla")}
    g3=np.median(accuracy)>=reference-.125 and all(np.median(gain[k])>0 and np.sum(gain[k]>0)>=6 and np.median(wind_gain[k])>0 for k in gain)
    leakage=val("vanilla_zs_env")-val("invariant_zs_env")
    g4=np.median(val("invariant_zm_env"))>=2/3-1e-12 and np.median(leakage)>=-1e-12 and np.sum(leakage>=-1e-12)>=5
    gates={"G1":bool(g1),"G2":bool(g2),"G3":bool(g3),"G4":bool(g4)}
    decision="MDBIL_D0_NO_STABLE_SOURCE_BLOCK_STOP" if not g1 else "MDBIL_D0_SOURCE_WEATHER_BLOCK_SIGNAL_PASS" if all(gates.values()) else "MDBIL_D0_SOURCE_BLOCK_SIGNAL_HOLD"
    return gates,decision


def audit(root, evidence):
    manifest_path=root/"evidence/cdsi_t01b/pass1/EXACT_64_RUN_MANIFEST.tsv"
    manifest=rows(manifest_path)
    assert len(manifest)==64 and len({r["run_id"] for r in manifest})==64
    assert len({r["master_seed"] for r in manifest})==64
    samples={}
    for r in manifest:
        p=root/"evidence/ocb_r2/mechanism_census_r0/inputs"/(r["run_id"]+".pooled.npy")
        assert sha(p)==r["frozen_tensor_sha256"]
        assert sha(root/r["metadata_file"])==r["metadata_sha256"]
        x=np.load(p,allow_pickle=False)
        assert x.shape==(10,30) and np.isfinite(x).all() and x.min()>=0
        samples[r["run_id"]]=(x>0).astype(np.float32)
    audits=[]
    for passname in ("pass1","pass2"):
        p=evidence/passname
        config=json.loads((p/"MODEL_CONFIG.json").read_text())
        assert config["epochs"]==500 and config["seeds"]==[2026100101,2026100102,2026100103]
        assert config["split"]=="leave-one-context-out per House"
        assert config["cfg"]=={"epochs":500,"lr":.002,"wd":.0001,"temp":.15,"src":1.,"con":.5,"align":.5,"met":.5,"adv":.2,"ind":.05,"rec":.1,"rank":.5,"margin":.2}
        seed=rows(p/"SEED_METRICS.tsv");folds=rows(p/"FOLD_METRICS.tsv")
        assert len(seed)==48 and len(folds)==8
        assert {(r["house"],r["heldout_context"]) for r in folds}=={(r["house"],r["context"]) for r in manifest}
        baseline_max=0.;aggregation_max=0.
        for f in folds:
            house=f["house"];held=f["heldout_context"]
            physical=[r for r in manifest if r["house"]==house]
            mapping={s:i for i,s in enumerate(sorted({r["source_id"] for r in physical}))}
            train=sorted((r for r in physical if r["context"]!=held),key=lambda r:(r["context"],r["source_id"],r["replicate_ordinal"]))
            test=sorted((r for r in physical if r["context"]==held),key=lambda r:(r["source_id"],r["replicate_ordinal"]))
            assert len(train)==24 and len(test)==8
            assert not(set(r["run_id"] for r in train)&set(r["run_id"] for r in test))
            sibling_context={r["context"] for r in train if r["gas_type"]==f["heldout_gas"]}
            assert len(sibling_context)==1
            sibling=[r for r in train if r["context"] in sibling_context]
            assert len(sibling)==8 and all(r["wind_id"]!=f["heldout_wind"] for r in sibling)
            y=np.array([mapping[r["source_id"]] for r in train]);yt=np.array([mapping[r["source_id"]] for r in test]);ys=np.array([mapping[r["source_id"]] for r in sibling])
            x=np.stack([samples[r["run_id"]] for r in train]);xt=np.stack([samples[r["run_id"]] for r in test]);xs=np.stack([samples[r["run_id"]] for r in sibling])
            for name,transform in (("raw",lambda a:a.reshape(len(a),300)),("static",lambda a:a.mean(axis=1))):
                values=cos_prototypes(transform(x),y,transform(xt),yt)
                sw=cos_prototypes(transform(xs),ys,transform(xt),yt)[2]
                for field,value in zip(("accuracy","margin","ratio","wind_ratio"),values+(sw,)):
                    difference=abs(value-float(f[name+"_"+field]));baseline_max=max(baseline_max,difference)
                    assert difference<1e-6,(passname,held,name,field,difference)
            sf=[r for r in seed if r["house"]==house and r["heldout_context"]==held]
            assert len(sf)==6
            for variant,prefix in (("vanilla","vanilla"),("invariant","invariant")):
                group=[r for r in sf if r["variant"]==variant]
                assert sorted(int(r["seed"]) for r in group)==[2026100101,2026100102,2026100103]
                for field in ("accuracy","margin","ratio","wind_ratio","zs_env")+(("zm_env","recon") if variant=="invariant" else ()):
                    value=float(np.median([float(r[field]) for r in group]))
                    difference=abs(value-float(f[prefix+"_"+field]));aggregation_max=max(aggregation_max,difference)
                    assert difference<1e-12
            for short,name in (("v","vanilla"),("raw","raw"),("static","static")):
                assert abs(float(f["ratio_gain_"+short])-(float(f[name+"_ratio"])-float(f["invariant_ratio"])))<1e-12
                assert abs(float(f["wind_gain_"+short])-(float(f[name+"_wind_ratio"])-float(f["invariant_wind_ratio"])))<1e-12
            assert abs(float(f["leak_gain"])-(float(f["vanilla_zs_env"])-float(f["invariant_zs_env"])))<1e-12
        gates,decision=independent_gates(folds)
        official=json.loads((p/"MDBIL_D0_RESULT.json").read_text())
        assert gates=={k:v["pass"] for k,v in official["gates"].items()} and decision==official["decision"]
        audits.append({"pass":passname,"independent_gate_flags":gates,"independent_decision":decision,"baseline_metric_max_abs":baseline_max,"seed_aggregation_max_abs":aggregation_max,"folds":8,"seed_metric_rows":48,"split_and_same_gas_cross_wind_audit":True})
    repeat_files=["INPUT_SHA256.tsv","DATA_CONTRACT.json","MODEL_CONFIG.json","SEED_METRICS.tsv","FOLD_METRICS.tsv","MDBIL_D0_RESULT.json","DECISION.md"]
    repeats=[]
    for filename in repeat_files:
        a=sha(evidence/"pass1"/filename);b=sha(evidence/"pass2"/filename)
        assert a==b,filename
        repeats.append({"file":filename,"sha256":a})
    report={"decision":"MDBIL_D0_INDEPENDENT_OUTPUT_AUDIT_PASS","pass":True,"input_count":64,"pass_audits":audits,"all_seven_key_outputs_byte_identical":True,"repeat_hashes":repeats,
            "scope_limits":["The frozen runner does not export trained weights or latent arrays. This audit independently checks inputs, baseline diagnostics, seed aggregation and gates; it does not independently recompute learned embeddings.","z_s/z_m context decoding is prototype leave-one-out on the 24 training-context samples, not decoding a held-out meteorological class.","A/B xyz differs including z; no pure XY/candidate-ranking/PMFS or causal-identifiability claim follows."]}
    (evidence/"INDEPENDENT_OUTPUT_AUDIT.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,required=True);p.add_argument("--evidence",type=Path,required=True)
    a=p.parse_args();audit(a.root,a.evidence)

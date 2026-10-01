"""Independent descriptor/score/LOHO-boundary/gate audit plus byte repeat.

Primary feature and decision implementations are not imported here.
"""
import argparse
import csv
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np


def digest(path):
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def independent_features(z,key,prior):
    p=z[key+"__p"];c=z[key+"__c"];hit=z[key+"__hit"]
    wind=z[key+"__wind"];xy=z[key+"__xy"];points=z[key+"__source"]
    scores=z[key+"__scores"];owner=z[key+"__owner"]
    u=wind/(np.sqrt((wind**2).sum(1))+1e-12)[:,None]
    gas=c*np.maximum(p-prior,0);miss=c*(1-p)
    def average(v,w):
        return float((v*w).sum()/w.sum()) if w.sum()>0 else 0.
    def quantile(v,w,f):
        if w.sum()==0:return 0.
        pairs=sorted(zip(v,w),key=lambda a:a[0]);total=sum(t[1] for t in pairs);cumulative=0.
        for val,weight in pairs:
            cumulative+=weight
            if cumulative>=f*total:return float(val)
        return float(pairs[-1][0])
    rows=[]
    for k,h in enumerate(hit):
        r=p-h;absolute=abs(r)
        a=((xy-points[k])*u).sum(1)
        b=np.sqrt(((xy-points[k]-a[:,None]*u)**2).sum(1))
        wb=c*absolute;center=average(b,wb)
        denom=float((c*np.maximum(p,h)).sum())
        rows.append([1-(int(np.sum(scores<scores[k]))+.5*int(np.sum(scores==scores[k])))/len(scores),
                     average(absolute,c),quantile(absolute,c,.5),quantile(absolute,c,.9),
                     average(h==0,gas),average(h,miss),1-float((c*np.minimum(p,h)).sum())/denom if denom>0 else 0,
                     float(np.sum(owner==k))/len(owner),average(a<0,gas),math.sqrt(max(0,average((b-center)**2,wb))),
                     abs(float((c*r*a).sum()))/float((c*abs(r*a)).sum()) if (c*abs(r*a)).sum()>0 else 0,
                     max(0,1-float(np.linalg.norm((gas[:,None]*u).sum(0)))/gas.sum()) if gas.sum()>0 else 0,
                     average(h*(a>0),miss)])
    return np.asarray(rows)


def audit(root,out,binary_dir):
    z=np.load(out/"SOURCE_BLIND_FEATURE_DATA.npz",allow_pickle=False)
    ds=json.loads((out/"SOURCE_BLIND_UPDATES.json").read_text())
    models=json.loads((out/"FROZEN_LOHO_MODELS.json").read_text())
    result=json.loads((out/"SITER_V0_RESULT.json").read_text())
    feature_max=0.;score_max=0.;posterior_max=0.
    for d in ds:
        key=d["key"]
        x=independent_features(z,key,d["parameters"]["hitPriorProbability"])
        feature_max=max(feature_max,float(np.max(abs(x-z[key+"__X"]))))
        assert np.max(abs(x-z[key+"__X"]))<1e-10
        factor=1-z[key+"__c"][None,:]*abs(z[key+"__p"][None,:]-z[key+"__hit"])*d["parameters"]["sourceDiscriminationPower"]
        logs=np.log(factor).sum(1)
        score_max=max(score_max,float(np.max(abs(logs-z[key+"__scores"]))))
        assert np.max(abs(logs-z[key+"__scores"]))<1e-10
        scaled=np.exp(logs[z[key+"__owner"]]-logs.max());scaled/=scaled.sum()
        posterior_max=max(posterior_max,float(np.max(abs(scaled-z[key+"__native_posterior"]))))
        assert np.max(abs(scaled-z[key+"__native_posterior"]))<1e-10
    for held,fold in models["folds"].items():
        training=[d for d in ds if d["house"]!=held]
        assert set(fold["training_update_keys"])==set(d["key"] for d in training)
        allx=np.concatenate([z[d["key"]+"__X"] for d in training])
        for name,m in fold["models"].items():
            assert np.array_equal(np.array(m["lo"]),allx.min(0)) and np.array_equal(np.array(m["hi"]),allx.max(0))
            b=np.asarray(m["beta"])
            if name!="signed":
                assert b.min()>=-1e-10 and abs(b.sum()-1)<1e-8
                means={int(k):v for k,v in m["inner_mean_validation_loss"].items()}
                selected=min(k for k,v in means.items() if v<=min(means.values())+1e-12)
                assert selected==m["selected_capacity"]
                for inner in m["inner_folds"]:
                    assert inner["validation_case"] not in inner["training_cases"]
                    assert all(not c.startswith(held) for c in inner["training_cases"])
    independent_rows=[]
    for case in result["cases"]:
        d=next(d for d in ds if d["case"]==case["case"] and d["update"]==5);key=d["key"]
        t=d["timing"];truth=np.array([case["truth_x"],case["truth_y"]],dtype=np.float32)
        origin=np.array([float(t["origin_x"]),float(t["origin_y"])],dtype=np.float32)
        ij=((truth-origin)/np.float32(float(t["cell_size"]))).astype(int)
        rectangle=z[key+"__rectangles"]
        covers=[k for k,r in enumerate(rectangle) if r[0]<=ij[0]<r[0]+r[2] and r[1]<=ij[1]<r[1]+r[3]]
        assert len(covers)==1
        true=covers[0];assert d["candidate_ids"][true]==case["truth_owner"]
        n=z[key+"__scores"];m=models["folds"][d["house"]]["models"]["full"]
        span=np.array(m["hi"])-np.array(m["lo"])
        x=np.minimum(1,np.maximum(0,(z[key+"__X"]-m["lo"])/np.where(span>0,span,1)))*(span>0)
        new=n-x@np.array(m["beta"])
        def rank(s):
            others=np.delete(s,true)
            return 1+np.sum(others>s[true])+.5*np.sum(others==s[true])
        assert rank(n)==case["native_rank"] and rank(new)==case["full_rank"]
        mass=np.exp(new[z[key+"__owner"]]-new.max());mass/=mass.sum()
        stored=np.load(out/"TERMINAL_POSTERIORS.npz",allow_pickle=False)[case["case"]+"__full"]
        assert np.max(abs(mass-stored))<1e-14
        assert abs(float(new[true]-np.delete(new,true).max())-case["full_margin"])<1e-12
        independent_rows.append({"case":case["case"],"rank_verified":True,"posterior_verified":True,"margin_verified":True})
    cases=result["cases"]
    rank_delta=np.array([r["native_rank"]-r["full_rank"] for r in cases]);error_delta=np.array([r["native_error_m"]-r["full_error_m"] for r in cases])
    rank_pass=(rank_delta>0).sum()>=4 and np.median(rank_delta)>0 and (rank_delta>=-10).all()
    old=np.mean([r["native_error_m"] for r in cases]);new=np.mean([r["full_error_m"] for r in cases])
    endpoint_pass=(error_delta>0).sum()>=4 and (old-new)/old>=.05
    safe=not any(r["new_false_confident_collapse"] for r in cases)
    transferable=all(any(r["house"]==h and r["rank_improvement"]>0 and r["endpoint_improvement_m"]>0 for r in cases) for h in ("House01","House02","House03"))
    expected="SITER_V0_CROSS_HOUSE_SIGNAL" if rank_pass and endpoint_pass and safe and transferable else "SITER_V0_HOLD_RANK_ONLY" if rank_pass and not endpoint_pass else "SITER_V0_HOLD_NONTRANSFERABLE" if endpoint_pass and not(rank_pass and safe and transferable) else "SITER_V0_NO_GO_STOP"
    assert expected==result["decision"]
    repeat=out/"repeat_scoring";repeat.mkdir(exist_ok=True)
    for name in ("SOURCE_BLIND_FEATURE_DATA.npz","SOURCE_BLIND_UPDATES.json","FROZEN_LOHO_MODELS.json"):
        shutil.copyfile(out/name,repeat/name)
    subprocess.run([sys.executable,str(Path(__file__).with_name("evaluate_frozen.py")),"--root",str(root),"--out",str(repeat),"--binary-dir",str(binary_dir)],check=True)
    repeated={}
    for name in ("SITER_V0_CANDIDATES.tsv","SITER_V0_CASES.tsv","SITER_V0_ABLATIONS.tsv","SITER_V0_RESULT.json","TERMINAL_POSTERIORS.npz","NATIVE_ENDPOINT_RECOVERY_PARITY.json"):
        a=digest(out/name);b=digest(repeat/name);assert a==b,(name,a,b)
        repeated[name]=a
    report={"pass":True,"independent_feature_max_abs":feature_max,"independent_native_score_max_abs":score_max,"independent_native_posterior_max_abs":posterior_max,
            "all_30_updates_checked":True,"candidate_axis_and_truth_owner_checked":True,"all_folds_training_only_scaling":True,"no_heldout_run_in_inner_training":True,
            "simplex_and_capacity_selection_checked":True,"terminal_rows":independent_rows,"independent_decision":expected,"deterministic_repeat_byte_identical":True,"repeat_hashes":repeated,
            "limitations":["Independent formulas use archived compact cell/hit matrices; raw CSV hash verification was done in preparation.","Endpoint function is shared validated Native C++, not an independent estimate algorithm.","This audit verifies the frozen implementation, not physical validity or untouched generalization."]}
    (out/"INDEPENDENT_SITER_V0_AUDIT.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,required=True);p.add_argument("--out",type=Path,required=True);p.add_argument("--binary-dir",type=Path,required=True)
    a=p.parse_args();audit(a.root,a.out,a.binary_dir)

"""Freeze all LOHO fits before outer evaluation; no test outcomes are read."""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

from prepare_features import read_csv, sha, write_json


def truth_owner(data, metadata, truth):
    t=metadata["timing"]
    # Match Native float coordinate-to-index semantics.
    point=np.asarray(truth,dtype=np.float32)
    origin=np.asarray([float(t["origin_x"]),float(t["origin_y"])],dtype=np.float32)
    cellsize=np.float32(float(t["cell_size"]))
    ij=((point-origin)/cellsize).astype(int)
    row=np.flatnonzero(np.all(data[f'{metadata["key"]}__ij']==ij,axis=1))
    assert len(row)==1, (metadata["key"],truth,ij,"truth not in legal support")
    return int(data[f'{metadata["key"]}__owner'][row[0]])


def labels(root, datasets):
    result={}
    inputs=[]
    for case in sorted(set(d["case"] for d in datasets)):
        path=root/"native"/f"{case}_off_off"/"tnqc_fixed_trajectory_evaluation.json"
        truth=json.loads(path.read_text())["truth"]
        result[case]=truth
        inputs.append({"path":str(path),"sha256":sha(path),"usage":"evaluator/supervision only; never a feature"})
    return result,inputs


def bounds(data, items):
    x=np.concatenate([data[f'{d["key"]}__X'] for d in items])
    return x.min(axis=0),x.max(axis=0)


def transform(x, lo, hi):
    span=hi-lo
    return np.clip((x-lo)/np.where(span>0,span,1),0,1)* (span>0)


def pairs(data, items, truth, lo, hi):
    offsets=[];differences=[];weights=[]
    for d in items:
        key=d["key"]; true=truth_owner(data,d,truth[d["case"]])
        x=transform(data[f"{key}__X"],lo,hi)
        score=data[f"{key}__scores"]
        wrong=np.arange(len(score))!=true
        offsets.append(score[wrong]-score[true])
        differences.append(x[true]-x[wrong])
        weights.append(np.full(wrong.sum(),1/(len(items)*wrong.sum())))
    return np.concatenate(offsets),np.concatenate(differences),np.concatenate(weights)


def loss_gradient(alpha, offset, delta, weight):
    z=offset+delta@alpha
    return float(np.dot(weight,np.logaddexp(0,z))),delta.T@(weight*expit(z))


def solve(offset, delta, weight):
    n=delta.shape[1]
    if n==1:
        a=np.ones(1);loss,_=loss_gradient(a,offset,delta,weight)
        return a,loss,{"success":True,"nit":0}
    opt=minimize(lambda a:loss_gradient(a,offset,delta,weight),np.full(n,1/n),jac=True,
                 method="SLSQP",bounds=[(0,1)]*n,
                 constraints={"type":"eq","fun":lambda a:a.sum()-1,"jac":lambda a:np.ones(n)},
                 options={"ftol":1e-10,"maxiter":500})
    assert opt.success, (opt.message,opt.fun)
    assert opt.x.min()>=-1e-10 and abs(opt.x.sum()-1)<=1e-8
    return opt.x,float(opt.fun),{"success":bool(opt.success),"nit":int(opt.nit)}


def greedy_path(offset,delta,weight,components):
    chosen=[];path={}
    for count in range(1,len(components)+1):
        best=None
        for feature in sorted(set(components)-set(chosen)):
            subset=chosen+[feature]
            alpha,loss,diag=solve(offset,delta[:,subset],weight)
            if best is None or loss<best["loss"]-1e-12:
                best={"subset":subset,"alpha":alpha.tolist(),"loss":loss,"optimizer":diag}
        chosen=best["subset"]
        path[count]=best
    return path


def fit_group(data, train, truth, components):
    ks=sorted(set([1,2,4,len(components)]))
    ks=[k for k in ks if k<=len(components)]
    validation={k:[] for k in ks}
    inner_records=[]
    for case in sorted(set(d["case"] for d in train)):
        a=[d for d in train if d["case"]!=case]
        b=[d for d in train if d["case"]==case]
        lo,hi=bounds(data,a)
        offset,delta,weight=pairs(data,a,truth,lo,hi)
        path=greedy_path(offset,delta,weight,components)
        vo,vd,vw=pairs(data,b,truth,lo,hi)
        losses={}
        for k in ks:
            p=path[k]
            value=loss_gradient(np.array(p["alpha"]),vo,vd[:,p["subset"]],vw)[0]
            losses[str(k)]=value;validation[k].append(value)
        inner_records.append({"validation_case":case,"training_cases":sorted(set(d["case"] for d in a)),"losses":losses})
    means={k:float(np.mean(validation[k])) for k in ks}
    kbest=ks[0]
    for k in ks[1:]:
        if means[k]<means[kbest]-1e-12:
            kbest=k
    lo,hi=bounds(data,train)
    offset,delta,weight=pairs(data,train,truth,lo,hi)
    fit=greedy_path(offset,delta,weight,components)[kbest]
    beta=np.zeros(13);beta[fit["subset"]]=fit["alpha"]
    return {"lo":lo.tolist(),"hi":hi.tolist(),"beta":beta.tolist(),"selected_capacity":kbest,"selected_features":fit["subset"],"training_loss":fit["loss"],"inner_mean_validation_loss":{str(k):v for k,v in means.items()},"inner_folds":inner_records,"optimizer":fit["optimizer"]}


def fit_all(root, out):
    data=np.load(out/"SOURCE_BLIND_FEATURE_DATA.npz",allow_pickle=False)
    datasets=json.loads((out/"SOURCE_BLIND_UPDATES.json").read_text())
    truth,inputs=labels(root,datasets)
    folds={}
    for held in ("House03","House02","House01"):
        train=[d for d in datasets if d["house"]!=held]
        assert len(train)==20
        models={}
        for name,components in (("general",list(range(8))),("flow",list(range(8,13))),("full",list(range(13)))):
            models[name]=fit_group(data,train,truth,components)
            print(held,name,models[name]["selected_capacity"],models[name]["selected_features"],flush=True)
        lo,hi=bounds(data,train)
        offset,delta,weight=pairs(data,train,truth,lo,hi)
        a,loss,diag=solve(offset,np.concatenate([delta,-delta],axis=1),weight)
        models["signed"]={"lo":lo.tolist(),"hi":hi.tolist(),"beta":(a[:13]-a[13:]).tolist(),"simplex_alpha":a.tolist(),"training_loss":loss,"optimizer":diag}
        folds[held]={"held_out_house":held,"training_houses":sorted(set(d["house"] for d in train)),"training_update_keys":[d["key"] for d in train],"models":models}
    result={"feature_data_sha256":sha(out/"SOURCE_BLIND_FEATURE_DATA.npz"),"implementation_sha256":sha(Path(__file__)),"folds":folds,"supervision_files":inputs,"outer_evaluation_executed":False,"all_outer_models_frozen":True}
    write_json(out/"FROZEN_LOHO_MODELS.json",result)
    print("ALL_OUTER_MODELS_FROZEN",sha(out/"FROZEN_LOHO_MODELS.json"),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    a=parser.parse_args()
    fit_all(a.root,a.out)

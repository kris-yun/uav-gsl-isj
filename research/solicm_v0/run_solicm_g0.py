#!/usr/bin/env python3
"""Frozen four-arm LCA transfer experiment on isolated H02 W0/W2 arrays."""
from __future__ import annotations
import argparse
import collections
import copy
import hashlib
import itertools
import json
import os
import random
import sys
from pathlib import Path

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader,TensorDataset

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"evidence/solicm_v0/g0"
VENDOR=ROOT/"research/solicm_v0/vendor/LCA/TSClassif"
RUNS=Path(r"D:\ZYC\A-gas\_staging\SOLICM_G0_RUNS_20260926")
sys.path.insert(0,str(VENDOR))
from configs.data_model_configs import HAR
from configs.LCA_config import get_model_a_parser
from algorithms.algorithms import LCA
from utils import AverageMeter

VARIANTS=("SOURCE_ONLY","PL_ONLY","LCA_NO_ALIGN","LCA_FULL")
DIRECTIONS=((0,1,"W0_to_W2"),(1,0,"W2_to_W0"))
FOLDS=((0,1,2,3),(4,5,6,7),(8,9,10,11),(12,13,14,15))
SEEDS=(0,1,2)
EPOCHS=40
BATCH=32

def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def savejson(path,value):
    path.write_bytes((json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+"\n").encode())

def model_configs(variant):
    data=HAR();data.sequence_len=10;data.input_channels=30;data.num_classes=6
    args=get_model_a_parser().parse_args([])
    if variant in ("SOURCE_ONLY","PL_ONLY"):
        args.No_prior=True
        args.z_kl_weight=0.0;args.rec_weight=0.0;args.sparsity_weight=0.0;args.structure_weight=0.0
    elif variant=="LCA_NO_ALIGN":
        args.structure_weight=0.0
    elif variant!="LCA_FULL":raise ValueError(variant)
    return data,args

def pre_run_lock():
    audit=json.loads((OUT/"SOLICM_G0_DATA_AUDIT.json").read_text())
    upstream=json.loads((OUT/"SOLICM_G0_UPSTREAM_CODE_MANIFEST.json").read_text())
    assert audit["decision"]=="SOLICM_G0_DATA_READY"
    configs={}
    for variant in VARIANTS:
        data,args=model_configs(variant)
        configs[variant]={"input_shape":[10,30],"num_classes":6,"data_config":{
            "kernel_size":data.kernel_size,"stride":data.stride,"dropout":data.dropout,
            "mid_channels":data.mid_channels,"final_out_channels":data.final_out_channels,
            "features_len":data.features_len},"lca_config":vars(args)}
    lock={"branch":"research/solicm-latent-causal-g0-20260926",
          "charter_sha256":sha(ROOT/"research/solicm_v0/SOLICM_G0_CHARTER_20260926.md"),
          "adapter_sha256":sha(ROOT/"research/solicm_v0/prepare_solicm_g0.py"),
          "training_code_sha256":sha(Path(__file__).resolve()),
          "isolated_input_sha256":audit["isolated_bank_sha256"],
          "upstream_commit":upstream["commit"],"upstream_code_manifest_sha256":sha(OUT/"SOLICM_G0_UPSTREAM_CODE_MANIFEST.json"),
          "model_configs":configs,"directions":[name for _,_,name in DIRECTIONS],
          "folds_heldout":FOLDS,"seeds":SEEDS,"epochs":EPOCHS,"batch_size":BATCH,
          "optimizer":"official LCA Adam lr=0.001 weight_decay=1e-4",
          "source_scaling":"channel-wise mean/std of all labeled SOURCE sequences and time points; std=1 only when exact zero; target unseen",
          "target_unlabeled_loader":"72 sequences; batch32 shuffle/drop_last true; official zip(source,cycle(target)) schedule",
          "selection":"minimum deterministic SOURCE-only CrossEntropyLoss on the 96 source training samples at epochs 10/20/30/40; no target labels",
          "pseudo_label":"official epoch>30, confidence>0.99, loss multiplier 0.5",
          "official_implementation_notes":["classifier outputs softmax before CrossEntropyLoss",
                "get_features returns z_std as third latent tuple element in pinned TSClassif code"],
          "latent_audit":"descriptive mean abs transition Jacobian per-domain on source/all target-unlabeled arrays at best checkpoint; learned threa applied as soft_quantile on signed Jacobian; no gate",
          "bootstrap_seed":2026092602,"bootstrap_clusters":12,"bootstrap_draws":10000,
          "training_has_no_target_label_or_target_metric_path":True,
          "device":str(torch.device("cuda" if torch.cuda.is_available() else "cpu")),
          "torch_version":torch.__version__,"numpy_version":np.__version__}
    file=OUT/"SOLICM_G0_PRE_RUN_LOCK.json"
    if file.exists():assert json.loads(file.read_text())==lock
    else:savejson(file,lock)
    print("SOLICM_PRE_RUN_LOCK",sha(file))

def load_bank():
    lock=json.loads((OUT/"SOLICM_G0_PRE_RUN_LOCK.json").read_text())
    assert sha(Path(__file__).resolve())==lock["training_code_sha256"]
    path=OUT/"SOLICM_G0_H02_W0_W2_16x10x30.npy"
    assert sha(path)==lock["isolated_input_sha256"]
    bank=np.load(path,allow_pickle=False)
    assert bank.shape==(2,6,16,10,30)
    return bank

def set_seed(seed):
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark=False
    torch.backends.cudnn.deterministic=True
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(4)

def source_scaled_arrays(bank,src,tgt,fold):
    sx=bank[src].reshape(96,10,30).astype(np.float64)
    mean=sx.mean(axis=(0,1));std=sx.std(axis=(0,1))
    std[std==0]=1.0
    train_index=[r for r in range(16) if r not in FOLDS[fold]]
    tx=bank[tgt][:,train_index].reshape(72,10,30).astype(np.float64)
    hx=bank[tgt][:,list(FOLDS[fold])].reshape(24,10,30).astype(np.float64)
    sx=((sx-mean)/std).astype(np.float32)
    tx=((tx-mean)/std).astype(np.float32)
    hx=((hx-mean)/std).astype(np.float32)
    # Only the SOURCE domain receives class labels. Target tensors carry no labels.
    sy=np.repeat(np.arange(6,dtype=np.int64),16)
    return sx,sy,tx,hx,mean,std

def source_risk(model,sx,sy,device):
    model.eval();losses=[]
    with torch.no_grad():
        for i in range(0,96,BATCH):
            x=torch.from_numpy(sx[i:i+BATCH].transpose(0,2,1).copy()).to(device)
            y=torch.from_numpy(sy[i:i+BATCH]).to(device)
            losses.append(F.cross_entropy(model.inference(x),y,reduction="sum").item())
    model.train()
    return float(sum(losses)/96)

def source_only_epoch(model,src_loader,device):
    model.train();meter=collections.defaultdict(AverageMeter)
    for x,y in src_loader:
        x=x.to(device);y=y.to(device)
        _,_,prediction=model.get_features(x)
        loss=F.cross_entropy(prediction,y)
        model.optimizer.zero_grad();loss.backward();model.optimizer.step()
        meter["Src_cls_loss"].update(loss.item(),len(y))
    return meter

def export_logits(model,hx,device):
    model.eval();logits=[]
    with torch.no_grad():
        for i in range(0,24,BATCH):
            x=torch.from_numpy(hx[i:i+BATCH].transpose(0,2,1).copy()).to(device)
            z_mean,_=model.z_net(x.permute(0,2,1))
            hidden=model.feature_extractor(z_mean.permute(0,2,1))
            raw=model.classifier.logits[0](hidden)
            official=model.inference(x)
            if not torch.allclose(torch.softmax(raw,dim=-1),official,atol=1e-6,rtol=1e-6):
                raise ValueError("official inference/logit mismatch")
            logits.append(raw.detach().cpu().numpy())
    return np.concatenate(logits,axis=0)

def latent_jacobians(model,x,device):
    model.eval();jac=[];threshold=[]
    for i in range(0,len(x),16):
        batch=torch.from_numpy(x[i:i+16].transpose(0,2,1).copy()).to(device)
        with torch.no_grad():
            _,z_std=model.z_net(batch.permute(0,2,1))
            _,_,hist=model.transition_prior_fix.forward(z_std)
            mat=torch.cat([j[:,0,:30].detach() for j in hist],dim=1)
            jac.append(mat.cpu().numpy())
            threshold.append(float(model.soft_quantile(mat.flatten(),model.threa).detach().cpu()))
    all_jac=np.concatenate(jac,axis=0)
    signed=all_jac.mean(axis=0).reshape(30,30)
    mag=np.abs(all_jac).mean(axis=0).reshape(30,30)
    thr=float(np.mean(threshold))
    return mag,signed,thr

def train_one(direction,fold,seed,variant):
    if variant not in VARIANTS or direction not in (0,1) or fold not in range(4) or seed not in SEEDS:
        raise ValueError("outside frozen run grid")
    bank=load_bank()
    src,tgt,name=DIRECTIONS[direction]
    set_seed(seed)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    sx,sy,tx,hx,mean,std=source_scaled_arrays(bank,src,tgt,fold)
    data,args=model_configs(variant)
    model=LCA(args,data,{"num_epochs":EPOCHS},device).to(device)
    source_tensor=torch.from_numpy(sx.transpose(0,2,1).copy())
    source_loader=DataLoader(TensorDataset(source_tensor,torch.from_numpy(sy)),batch_size=BATCH,shuffle=True,drop_last=True)
    target_tensor=torch.from_numpy(tx.transpose(0,2,1).copy())
    target_loader=DataLoader(TensorDataset(target_tensor,torch.zeros(len(tx),dtype=torch.long)),batch_size=BATCH,shuffle=True,drop_last=True)
    runid=f"{name}__fold{fold}__seed{seed}__{variant}"
    final=RUNS/runid
    if not final.resolve().is_relative_to(RUNS.resolve()):
        raise ValueError("run path escaped staging directory")
    if (final/"COMPLETE.json").exists():
        done=json.loads((final/"COMPLETE.json").read_text())
        assert done["pre_run_lock_sha256"]==sha(OUT/"SOLICM_G0_PRE_RUN_LOCK.json")
        assert sha(final/"heldout_logits.npy")==done["heldout_logits_sha256"]
        print("SKIP_COMPLETED",runid,flush=True)
        return
    if final.exists():raise FileExistsError(f"partial run directory: {final}")
    temp=RUNS/(runid+".inprogress")
    if not temp.resolve().is_relative_to(RUNS.resolve()):
        raise ValueError("temporary run path escaped staging directory")
    if temp.exists():raise FileExistsError(f"partial run directory: {temp}")
    temp.mkdir(parents=True)
    config={"direction":name,"source_domain":src,"target_domain":tgt,"fold":fold,"heldout_indices":FOLDS[fold],
            "seed":seed,"variant":variant,"epochs":EPOCHS,"batch_size":BATCH,"source_count":96,
            "target_unlabeled_count":72,"target_heldout_count":24,
            "source_scaler_mean":mean.tolist(),"source_scaler_std":std.tolist(),
            "pre_run_lock_sha256":sha(OUT/"SOLICM_G0_PRE_RUN_LOCK.json"),
            "target_labels_available_to_training":False,"model_config":vars(args)}
    savejson(temp/"config.json",config)
    best=float("inf");best_state=None;best_epoch=None;history=[]
    for epoch in range(1,EPOCHS+1):
        if variant=="SOURCE_ONLY":meter=source_only_epoch(model,source_loader,device)
        else:
            model.train();meter=collections.defaultdict(AverageMeter)
            model.training_epoch(source_loader,target_loader,meter,epoch)
        record={"epoch":epoch,"training_source_class_loss":float(meter["Src_cls_loss"].avg)}
        if epoch%10==0:
            risk=source_risk(model,sx,sy,device)
            record["checkpoint_source_only_risk"]=risk
            if risk<best:
                best=risk;best_epoch=epoch;best_state=copy.deepcopy({k:v.detach().cpu() for k,v in model.state_dict().items()})
        history.append(record)
        if epoch%10==0:print("EPOCH",runid,epoch,"source_risk",record["checkpoint_source_only_risk"],flush=True)
    assert best_state is not None
    torch.save({"state_dict":best_state,"best_epoch":best_epoch,"source_risk":best},temp/"best_checkpoint.pt")
    model.load_state_dict(best_state);model.to(device)
    logits=export_logits(model,hx,device)
    if logits.shape!=(24,6) or not np.isfinite(logits).all():raise ValueError("invalid heldout logits")
    np.save(temp/"heldout_logits.npy",logits,allow_pickle=False)
    savejson(temp/"training_history.json",{"best_epoch":best_epoch,"best_source_only_risk":best,"epochs":history})
    if variant in ("LCA_NO_ALIGN","LCA_FULL"):
        src_mag,src_signed,src_thr=latent_jacobians(model,sx,device)
        tgt_mag,tgt_signed,tgt_thr=latent_jacobians(model,tx,device)
        threshold=(src_thr+tgt_thr)/2
        src_mask=src_signed>threshold;tgt_mask=tgt_signed>threshold
        overlap=np.logical_and(src_mask,tgt_mask).sum();union=np.logical_or(src_mask,tgt_mask).sum()
        np.savez_compressed(temp/"latent_structure.npz",src_magnitude=src_mag,tgt_magnitude=tgt_mag,
             src_signed=src_signed,tgt_signed=tgt_signed,src_mask=src_mask,tgt_mask=tgt_mask,
             learned_threa=float(model.threa.detach().cpu()),threshold=threshold,
             weighted_discrepancy=float(np.mean(np.abs(src_mag-tgt_mag))),
             mask_jaccard=float(overlap/union) if union else 1.0)
    done={"runid":runid,"best_epoch":best_epoch,"source_risk":best,
          "pre_run_lock_sha256":sha(OUT/"SOLICM_G0_PRE_RUN_LOCK.json"),
          "heldout_logits_sha256":sha(temp/"heldout_logits.npy"),
          "checkpoint_sha256":sha(temp/"best_checkpoint.pt"),
          "latent_structure_sha256":sha(temp/"latent_structure.npz") if (temp/"latent_structure.npz").exists() else None}
    savejson(temp/"COMPLETE.json",done)
    temp.rename(final)
    print("RUN_COMPLETE",runid,best_epoch,flush=True)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("stage",choices=("lock","train_one","train_all"))
    ap.add_argument("--direction",type=int);ap.add_argument("--fold",type=int);ap.add_argument("--seed",type=int)
    ap.add_argument("--variant",choices=VARIANTS)
    args=ap.parse_args()
    if args.stage=="lock":pre_run_lock()
    elif args.stage=="train_one":train_one(args.direction,args.fold,args.seed,args.variant)
    else:
        for d,_,_ in DIRECTIONS:
            for fold in range(4):
                for seed in SEEDS:
                    for variant in VARIANTS:
                        train_one(d,fold,seed,variant)

if __name__=="__main__":main()

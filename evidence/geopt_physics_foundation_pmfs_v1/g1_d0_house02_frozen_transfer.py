#!/usr/bin/env python3
"""M6 G1-D0: cheap House02 frozen-foundation transfer kill test.

Development-only screen using the already-open 2-source x 2-wind x 2-plume
House02 GADEN bank. No new simulation and no PMFS closed loop.

Scientific question:
Does the *official pretrained GeoPT representation* transfer better than the
same architecture with a random frozen backbone under scarce gas supervision?

Frozen design
-------------
- Same 8-layer GeoPT/Transolver architecture in both arms.
- Same 16,961-param source adapter + 257-param scalar gas head.
- Backbone frozen in both arms.
- PRE arm loads every official non-head GeoPT tensor.
- RF arm uses random frozen GeoPT weights.
- Train combinations: S1W1, S2W1, S1W2.
- Held out: S2W2.
- Training target averages both plume realizations and all 10 snapshots.
- Evaluation keeps plume A/B separate.
- Only a deterministic 25% geometry-hash subset contributes to training loss.
- Full free grid remains visible to the attention backbone in both arms.
- No held-out target enters training, normalization, model selection, or
  stopping. Fixed epochs, optimizer, and two training seeds.

This can KILL M6. A positive result is development evidence only and cannot
ADVANCE the paper main innovation without independent multi-candidate rank.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch
from scipy.spatial import cKDTree
from torch import nn
from torch.nn import functional as F


PAIRS_TRAIN=(("S1","W1"),("S2","W1"),("S1","W2"))
PAIR_HOLDOUT=("S2","W2")
TRAIN_SEEDS=(1729,2718)
PLUMES=("A","B")
POOL=3
LABEL_FRAC=0.25
EPOCHS=80
LR=1e-3
WEIGHT_DECAY=1e-5
TAU_REF_S=1.0
SOURCE_SIGMA_WORLD_M=0.30
EXPECTED_CKPT_SHA="c0b1b9c4e5d533dbc249190d3d1fbe8e6b066b36d325cf4377cc0d613c02d1c2"
OFFICIAL_EXCLUDE=("mlp2","ln_3")


def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()


def coarse_centers(n:int,k:int,origin:float,cell_m:float)->np.ndarray:
    out=[]
    for o in range(math.ceil(n/k)):
        a=o*k
        b=min((o+1)*k,n)
        # Mean of fine-cell centres.
        idx=np.arange(a,b,dtype=np.float64)+0.5
        out.append(origin+cell_m*float(idx.mean()))
    return np.asarray(out,dtype=np.float64)


def avg_pool_np(a:np.ndarray,k:int=POOL)->np.ndarray:
    """Pool trailing H,W with ceil_mode."""
    t=torch.from_numpy(a.astype(np.float32,copy=False))
    lead=t.shape[:-2]
    h,w=t.shape[-2:]
    z=t.reshape(-1,1,h,w)
    z=F.avg_pool2d(z,kernel_size=k,stride=k,ceil_mode=True)
    return z[:,0].reshape(*lead,z.shape[-2],z.shape[-1]).numpy()


def max_pool_np(a:np.ndarray,k:int=POOL)->np.ndarray:
    t=torch.from_numpy(a.astype(np.float32,copy=False))
    lead=t.shape[:-2]
    h,w=t.shape[-2:]
    z=t.reshape(-1,1,h,w)
    z=F.max_pool2d(z,kernel_size=k,stride=k,ceil_mode=True)
    return z[:,0].reshape(*lead,z.shape[-2],z.shape[-1]).numpy()


def load_bank(bank:Path,dynamic:Path):
    meta=json.loads((bank/"geometry/context_metadata.json").read_text())
    cell=float(meta["cell_m"])
    env_min=np.asarray(meta["env_min_m"],dtype=np.float64)
    obstacle=np.load(bank/"geometry/obstacle_mask_z0p20.npy",allow_pickle=False)
    if obstacle.shape!=(83,119):
        raise RuntimeError(f"obstacle shape drift {obstacle.shape}")

    # Bank convention: obstacle==0 means free.
    free_fine=(obstacle==0).astype(np.float32)
    # Coarse cell is free only if every fine cell in its pool is free.
    blocked_fine=1.0-free_fine
    free=(1.0-max_pool_np(blocked_fine)).astype(bool)
    h,w=free.shape

    xs=coarse_centers(obstacle.shape[0],POOL,env_min[0],cell)
    ys=coarse_centers(obstacle.shape[1],POOL,env_min[1],cell)
    X,Y=np.meshgrid(xs,ys,indexing="ij")
    if X.shape!=(h,w):
        raise RuntimeError("coarse coordinate shape drift")

    # Source-blind House normalization. Use full cell-domain x width.
    scale=5.0/(obstacle.shape[0]*cell)
    x0=float(env_min[0]+obstacle.shape[0]*cell/2)
    y0=float(env_min[1]+obstacle.shape[1]*cell/2)

    free_xy=np.column_stack([X[free],Y[free]])
    obs_xy=np.column_stack([X[~free],Y[~free]])
    tree=cKDTree(obs_xy)
    dist,idx=tree.query(free_xy,k=1)
    nearest=obs_xy[idx]
    wall_vec=nearest-free_xy  # GeoPT pretraining sign: free -> boundary.
    wall_vec/=np.maximum(dist[:,None],1e-12)

    # y-up embedding: X<-world x, Y<-vertical relative to sensor plane, Z<-world y.
    pos=np.column_stack([
        (free_xy[:,0]-x0)*scale,
        np.zeros(len(free_xy),dtype=np.float64),
        (free_xy[:,1]-y0)*scale,
    ])
    wall_dir=np.column_stack([
        wall_vec[:,0],
        np.zeros(len(wall_vec),dtype=np.float64),
        wall_vec[:,1],
    ])
    geom=np.column_stack([pos,dist*scale,wall_dir])  # 7

    # Dynamic wind: use the mean of the ten cycling physical wind files 1..10.
    fx_by_wind={}
    wind_diag={}
    for wid in ("W1","W2"):
        p=dynamic/f"wind_{wid}_sequence_z0p20.npy"
        a=np.load(p,allow_pickle=False).astype(np.float32)
        if a.shape!=(11,83,119,3):
            raise RuntimeError(f"{wid} wind shape drift {a.shape}")
        # [I,H,W,3] -> [I,3,H,W], pool spatially.
        b=np.transpose(a,(0,3,1,2))
        b=avg_pool_np(b)  # [11,3,h,w]
        mean_w=b[1:11].mean(axis=0) # [3,h,w]
        vec=np.column_stack([
            mean_w[0][free],
            mean_w[2][free],  # temporary order only; remap below
            mean_w[1][free],
        ])
        # Original components are [world x, world y, world z].
        wx=mean_w[0][free].astype(np.float64)
        wy=mean_w[1][free].astype(np.float64)
        wz=mean_w[2][free].astype(np.float64)
        # GeoPT y-up: [world x, world z, world y].
        wgeo=np.column_stack([wx,wz,wy])
        speed=np.linalg.norm(wgeo,axis=1)
        unit=np.zeros_like(wgeo)
        nz=speed>1e-12
        unit[nz]=wgeo[nz]/speed[nz,None]
        step=scale*speed*TAU_REF_S
        dynamics=np.column_stack([unit,step])
        fx=np.column_stack([geom,dynamics])
        if fx.shape[1]!=11:
            raise RuntimeError("fx width drift")
        fx_by_wind[wid]=fx.astype(np.float32)
        wind_diag[wid]={
            "speed_quantiles":np.quantile(speed,[0,.25,.5,.75,.9,.95,1]).tolist(),
            "step_quantiles":np.quantile(step,[0,.25,.5,.75,.9,.95,1]).tolist(),
            "step_gt_2_fraction":float(np.mean(step>2.0)),
        }

    sources={}
    for sid in ("S1","S2"):
        xyz=np.asarray(meta["source_maps"][sid]["xyz_m"],dtype=np.float64)
        sources[sid]=np.asarray([
            (xyz[0]-x0)*scale,
            0.0,  # source and sensor plane are both z=0.2 m in this development bank
            (xyz[1]-y0)*scale,
        ],dtype=np.float32)

    # Targets: pool log1p concentration, then average time.
    targets={}
    for sid in ("S1","S2"):
        for wid in ("W1","W2"):
            targets[(sid,wid)]={}
            for plume in PLUMES:
                p=bank/"realizations"/f"{sid}_{wid}_{plume}"/"concentration.npy"
                a=np.load(p,allow_pickle=False).astype(np.float32)
                if a.shape!=(10,83,119) or not np.isfinite(a).all() or (a<0).any():
                    raise RuntimeError(f"target drift {p} {a.shape}")
                z=avg_pool_np(np.log1p(a)) # [10,h,w]
                y=z.mean(axis=0)[free].astype(np.float32)
                targets[(sid,wid)][plume]=y

    # Geometry-only deterministic hash, same labels for every source/wind.
    ii,jj=np.nonzero(free)
    hv=((ii.astype(np.uint64)*73856093) ^
        (jj.astype(np.uint64)*19349663) ^
        np.uint64(20260924)) % np.uint64(10000)
    selected=(hv < int(LABEL_FRAC*10000))
    if selected.sum()<50:
        raise RuntimeError("too few selected labels")

    return {
        "pos":pos.astype(np.float32),
        "fx":fx_by_wind,
        "sources":sources,
        "targets":targets,
        "selected":selected,
        "free_count":int(free.sum()),
        "coarse_shape":[int(h),int(w)],
        "scale":float(scale),
        "source_sigma_norm":float(SOURCE_SIGMA_WORLD_M*scale),
        "wind_diag":wind_diag,
    }


class SourceInjectionAdapter(nn.Module):
    def __init__(self,hidden_dim=256,adapter_hidden=64):
        super().__init__()
        self.net=nn.Sequential(
            nn.Linear(4,adapter_hidden),
            nn.SiLU(),
            nn.Linear(adapter_hidden,hidden_dim),
        )
        self.gate=nn.Parameter(torch.zeros(()))

    def forward(self,pos,source_xyz,sigma_s):
        if source_xyz.ndim==2:
            source_xyz=source_xyz[:,None,:]
        delta=pos-source_xyz
        d2=(delta*delta).sum(dim=-1,keepdim=True)
        q=torch.exp(-0.5*d2/(sigma_s*sigma_s))
        r=torch.cat([q,q*delta],dim=-1)
        return self.gate*self.net(r)


def instantiate_official(geopt_root:Path,seed:int):
    sys.path.insert(0,str(geopt_root))
    module=importlib.import_module("models.Transolver")
    args=SimpleNamespace(
        fun_dim=11,space_dim=3,n_hidden=256,n_heads=8,n_layers=8,
        mlp_ratio=2,slice_num=32,out_dim=9,dropout=0.0,act="gelu",
        geotype="unstructured",shapelist=None,checkpoint=0,unified_pos=0,
    )
    torch.manual_seed(seed)
    return module.Model(args).cpu()


def load_pretrained_internal(model,checkpoint:Path):
    raw=torch.load(checkpoint,map_location="cpu",weights_only=True)
    st=model.state_dict()
    filt={
        k:v for k,v in raw.items()
        if k in st and st[k].shape==v.shape
        and not any(ex in k for ex in OFFICIAL_EXCLUDE)
    }
    missing=[
        k for k in st
        if not any(ex in k for ex in OFFICIAL_EXCLUDE) and k not in filt
    ]
    if missing:
        raise RuntimeError(f"pretrained internal mismatch: {missing[:10]}")
    st.update(filt)
    model.load_state_dict(st,strict=True)
    return len(filt),sum(int(v.numel()) for v in filt.values())


class FrozenFoundationGas(nn.Module):
    """Frozen GeoPT internal dynamics + trainable source adapter/scalar head."""
    def __init__(self,geopt):
        super().__init__()
        self.geopt=geopt
        for p in self.geopt.parameters():
            p.requires_grad_(False)
        self.source_adapter=SourceInjectionAdapter(256,64)
        self.gas_head=nn.Linear(256,1)

    def hidden(self,pos,fx,source_xyz,sigma_s):
        h=self.geopt.preprocess(torch.cat([pos,fx],dim=-1))
        h=h+self.geopt.placeholder[None,None,:]
        h=h+self.source_adapter(pos,source_xyz,sigma_s)
        for block in self.geopt.blocks[:-1]:
            h=block(h)
        # Use all internal layers of final block but deliberately bypass its
        # pretraining task head (ln_3/mlp2), matching official fine-tune filter.
        b=self.geopt.blocks[-1]
        h=b.Attn(b.ln_1(h))+h
        h=b.mlp(b.ln_2(h))+h
        return h

    def forward(self,pos,fx,source_xyz,sigma_s):
        return self.gas_head(self.hidden(pos,fx,source_xyz,sigma_s))[...,0]

    def trainable_parameters(self):
        return list(self.source_adapter.parameters())+list(self.gas_head.parameters())


def make_batches(data,pairs):
    pos=torch.from_numpy(data["pos"])[None].expand(len(pairs),-1,-1).contiguous()
    fx=torch.stack([torch.from_numpy(data["fx"][w]) for _,w in pairs],dim=0)
    src=torch.stack([torch.from_numpy(data["sources"][s]) for s,_ in pairs],dim=0)
    return pos,fx,src


def train_arm(arm,seed,data,geopt_root,checkpoint):
    geopt=instantiate_official(geopt_root,seed)
    loaded=None
    if arm=="pretrained":
        loaded=load_pretrained_internal(geopt,checkpoint)
    elif arm!="random_frozen":
        raise ValueError(arm)

    # Reset adapter/head from the same seed stream independent of backbone arm.
    torch.manual_seed(seed+100000)
    model=FrozenFoundationGas(geopt)
    model.train()

    pos,fx,src=make_batches(data,PAIRS_TRAIN)
    # Average A/B targets; time was already averaged in load_bank.
    ys=[]
    for pair in PAIRS_TRAIN:
        y=0.5*(data["targets"][pair]["A"]+data["targets"][pair]["B"])
        ys.append(torch.from_numpy(y))
    y=torch.stack(ys,dim=0)
    sel=torch.from_numpy(data["selected"])

    opt=torch.optim.AdamW(
        model.trainable_parameters(),lr=LR,weight_decay=WEIGHT_DECAY)
    losses=[]
    t0=time.perf_counter()
    for _ in range(EPOCHS):
        pred=model(pos,fx,src,data["source_sigma_norm"])
        loss=((pred[:,sel]-y[:,sel])**2).mean()
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        losses.append(float(loss.detach()))
    elapsed=time.perf_counter()-t0

    model.eval()
    return model,{
        "loss_first":losses[0],
        "loss_last":losses[-1],
        "training_seconds":elapsed,
        "pretrained_loaded":loaded,
        "adapter_params":sum(p.numel() for p in model.source_adapter.parameters()),
        "head_params":sum(p.numel() for p in model.gas_head.parameters()),
    }


def mse(a,b):
    return float(np.mean((a-b)**2))


def evaluate(model,data):
    pair_inputs=(("S2","W2"),("S1","W2"))
    pos,fx,src=make_batches(data,pair_inputs)
    with torch.no_grad():
        pred=model(pos,fx,src,data["source_sigma_norm"]).cpu().numpy()
    p_true=pred[0]
    p_wrong=pred[1]
    out={}
    for plume in PLUMES:
        y=data["targets"][PAIR_HOLDOUT][plume]
        mt=mse(p_true,y)
        mw=mse(p_wrong,y)
        out[plume]={
            "true_candidate_mse":mt,
            "wrong_S1_candidate_mse":mw,
            "source_margin_wrong_minus_true":mw-mt,
            "truth_rank_2_candidates":1 if mt<mw else (2 if mt>mw else 1.5),
        }
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--geopt-root",type=Path,required=True)
    ap.add_argument("--checkpoint",type=Path,required=True)
    ap.add_argument("--bank",type=Path,required=True)
    ap.add_argument("--dynamic-wind",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()

    torch.set_num_threads(4)
    torch.use_deterministic_algorithms(True)
    digest=sha256(args.checkpoint)
    if digest!=EXPECTED_CKPT_SHA:
        raise RuntimeError(f"checkpoint hash mismatch {digest}")

    data=load_bank(args.bank,args.dynamic_wind)
    result={
        "mode":"M6_G1_D0_HOUSE02_FROZEN_TRANSFER_25PCT",
        "development_only":True,
        "checkpoint_sha256":digest,
        "pool_factor":POOL,
        "coarse_shape":data["coarse_shape"],
        "free_tokens":data["free_count"],
        "label_fraction":LABEL_FRAC,
        "selected_label_tokens":int(data["selected"].sum()),
        "epochs":EPOCHS,
        "lr":LR,
        "weight_decay":WEIGHT_DECAY,
        "tau_ref_s":TAU_REF_S,
        "source_sigma_world_m":SOURCE_SIGMA_WORLD_M,
        "source_sigma_normalized":data["source_sigma_norm"],
        "geometry_scale":data["scale"],
        "wind_diag":data["wind_diag"],
        "train_pairs":[f"{s}_{w}" for s,w in PAIRS_TRAIN],
        "holdout_pair":"S2_W2",
        "arms":{},
        "paired":{},
    }

    models={}
    for seed in TRAIN_SEEDS:
        sk=str(seed)
        result["arms"][sk]={}
        for arm in ("pretrained","random_frozen"):
            model,train_info=train_arm(
                arm,seed,data,args.geopt_root,args.checkpoint)
            ev=evaluate(model,data)
            result["arms"][sk][arm]={
                "train":train_info,
                "holdout":ev,
            }

    all_field=True
    all_margin=True
    all_rank=True
    paired=[]
    for seed in TRAIN_SEEDS:
        sk=str(seed)
        result["paired"][sk]={}
        for plume in PLUMES:
            p=result["arms"][sk]["pretrained"]["holdout"][plume]
            r=result["arms"][sk]["random_frozen"]["holdout"][plume]
            ratio=p["true_candidate_mse"]/r["true_candidate_mse"] if r["true_candidate_mse"]>0 else float("inf")
            margin_gain=p["source_margin_wrong_minus_true"]-r["source_margin_wrong_minus_true"]
            row={
                "pretrained_to_random_field_mse_ratio":ratio,
                "pretrained_field_improves_ge_10pct":ratio<=0.90,
                "source_margin_gain_pre_minus_random":margin_gain,
                "pretrained_margin_better":margin_gain>0,
                "pretrained_truth_rank":p["truth_rank_2_candidates"],
                "random_truth_rank":r["truth_rank_2_candidates"],
            }
            result["paired"][sk][plume]=row
            paired.append(row)
            all_field &= row["pretrained_field_improves_ge_10pct"]
            all_margin &= row["pretrained_margin_better"]
            all_rank &= (row["pretrained_truth_rank"]==1)

    if all_field and all_margin and all_rank:
        decision="G1_D0_PRETRAINING_SIGNAL_SURVIVES"
    else:
        decision="G1_D0_NO_GO_PRETRAINING_TRANSFER"

    result["summary"]={
        "all_4_pretrained_field_improve_ge_10pct":bool(all_field),
        "all_4_pretrained_source_margin_better":bool(all_margin),
        "all_4_pretrained_truth_rank_1_of_2":bool(all_rank),
        "mean_field_mse_ratio":float(np.mean([x["pretrained_to_random_field_mse_ratio"] for x in paired])),
        "mean_source_margin_gain":float(np.mean([x["source_margin_gain_pre_minus_random"] for x in paired])),
        "decision":decision,
        "interpretation":"development kill only; 2-candidate rank is a floor and cannot ADVANCE M6",
    }

    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=True)+"\n")
    print(json.dumps(result,indent=2,allow_nan=True))


if __name__=="__main__":
    main()

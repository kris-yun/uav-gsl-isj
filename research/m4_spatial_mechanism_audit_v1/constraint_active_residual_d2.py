#!/usr/bin/env python3
"""D2 cheap mechanism screen: tiny source-blind constraint-active residual.

House02 is development-only and already opened. Frozen M4-v3 checkpoints are
never updated. Two equal-capacity 64-parameter residual models are trained on
S1W1/S2W1/S1W2 only:

  GATED: correction is allowed only in source-blind constraint-active regions
         (near wall OR top-25% strain OR top-25% |Wz|).
  GLOBAL: identical model/features/optimizer, but correction may act everywhere.

The purpose is not to establish a final method. It asks whether the missing
wind-response geometry is specifically concentrated in physically identified
constraint-active regions, rather than being generic residual-fitting capacity.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import torch
from scipy.ndimage import distance_transform_edt
from torch import nn
from torch.nn import functional as F

TRAIN_PAIRS=(("S1","W1"),("S2","W1"),("S1","W2"))
EVAL_PAIRS=(("S2","W2"),("S2","W1"),("S1","W2"))
BASE_SEEDS=(1729,2718)
PLUME_SEEDS=("A","B")
CORRECTOR_SEED=6061
EPOCHS=100
LR=5e-3
MAX_CORRECTION_RATIO=0.50

BASE_COS={
  1729:{"A":0.3505734245283621,"B":0.3832453097348595},
  2718:{"A":0.3406864424162008,"B":0.3697538958716866},
}
BASE_MSE={
  1729:{"A":0.28387215733528137,"B":0.29915934801101685},
  2718:{"A":0.2931515574455261,"B":0.3083305060863495},
}


def load_py(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(m)
    return m


def raw_winds3(dynamic:Path):
    out={}
    for wid in ("W1","W2"):
        a=np.load(dynamic/f"wind_{wid}_sequence_z0p20.npy",allow_pickle=False).astype(np.float32)
        if a.shape!=(11,83,119,3):
            raise ValueError(f"unexpected {wid} wind shape {a.shape}")
        t=torch.from_numpy(a).permute(0,3,1,2)
        out[wid]=F.avg_pool2d(t,2,ceil_mode=True)
    return out


def record_wind3(d0,mm,winds3,pairs):
    max_steps=int(round(max(d0.TARGET_TIMES_S)/d0.PHYSICS_DT_S))
    ids=mm.gaden_wind_index_schedule(
        max_steps,d0.PHYSICS_DT_S,d0.WIND_DT_S,11,d0.LOOP_FROM,d0.LOOP_TO)
    rec_steps=d0.record_steps()
    items=[]
    for _,wid in pairs:
        seq=[]
        for step in rec_steps:
            seq.append(winds3[wid][ids[step-1]])
        items.append(torch.stack(seq,dim=0))
    return torch.stack(items,dim=0) # [B,T,3,H,W]


def wall_near_mask(free:torch.Tensor):
    f=(free[0,0].cpu().numpy()>0.5)
    p=np.pad(f.astype(np.uint8),1,mode="constant",constant_values=0)
    d=distance_transform_edt(p)[1:-1,1:-1]
    near=(d<=1.0) & f
    return torch.from_numpy(near)


def strain_mag(w:torch.Tensor,cell_m:float):
    # w [B,T,3,H,W]
    u=w[:,:,0].double()
    v=w[:,:,1].double()
    du_dr,du_dc=torch.gradient(u,spacing=(cell_m,cell_m),dim=(-2,-1))
    dv_dr,dv_dc=torch.gradient(v,spacing=(cell_m,cell_m),dim=(-2,-1))
    s11=du_dr
    s22=dv_dc
    s12=0.5*(du_dc+dv_dr)
    return torch.sqrt(s11*s11+s22*s22+2.0*s12*s12).float()


def top_fraction_mask(x:torch.Tensor,free:torch.Tensor,frac:float=0.25):
    # x [B,T,H,W]
    f=(free[0,0]>0.5)
    out=torch.zeros_like(x,dtype=torch.bool)
    for b in range(x.shape[0]):
        for t in range(x.shape[1]):
            vals=x[b,t][f]
            q=torch.quantile(vals,1.0-frac)
            out[b,t]=x[b,t]>=q
    return out


def build_features_and_gate(coarse_log,wind3,free,cell_m):
    # coarse_log [B,T,1,H,W], wind3 [B,T,3,H,W]
    strain=strain_mag(wind3,cell_m)
    speed=torch.linalg.vector_norm(wind3[:,:,:2],dim=2)
    wzabs=wind3[:,:,2].abs()
    wall=wall_near_mask(free)[None,None].expand(
        coarse_log.shape[0],coarse_log.shape[1],-1,-1)
    smask=top_fraction_mask(strain,free,0.25)
    zmask=top_fraction_mask(wzabs,free,0.25)
    gate=(wall|smask|zmask) & (free[0,0]>0.5)[None,None]
    wallf=wall.float()
    feat=torch.cat((
        coarse_log,
        wind3,
        speed[:,:,None],
        strain[:,:,None],
        wallf[:,:,None],
    ),dim=2)  # 1 + 3 + 1 + 1 + 1 = 7
    return feat,gate[:, :, None].float()


class TinySpatialResidual(nn.Module):
    """Exactly 64 parameters: Conv2d(7->1,k=3) including bias."""
    def __init__(self):
        super().__init__()
        self.conv=nn.Conv2d(7,1,3,padding=1,bias=True)
        nn.init.zeros_(self.conv.weight)
        nn.init.zeros_(self.conv.bias)

    def forward(self,features):
        b,t,c,h,w=features.shape
        raw=self.conv(features.reshape(b*t,c,h,w))
        return raw.reshape(b,t,1,h,w)


def apply_corrector(model,coarse_log,features,gate,free,mode):
    raw=model(features)
    correction=0.5*torch.tanh(raw)
    if mode=="gated":
        correction=correction*gate
    elif mode!="global":
        raise ValueError(mode)
    correction=correction*free[:,None]
    corrected=(coarse_log+correction).clamp_min(0.0)*free[:,None]
    return corrected,correction


def predict_base(d0,mm,model,sources,winds2,pairs,free):
    sb=torch.cat([sources[s] for s,_ in pairs],dim=0)
    sch=d0.build_batch_schedule(mm,winds2,pairs,torch.device("cpu"))
    with torch.no_grad():
        p=d0.evolve_to_records(model,sb,sch,free,use_checkpoint=False)
    return torch.log1p(p.clamp_min(0))


def free_flat(x,free):
    m=(free[0,0]>0.5)
    return x[:,:,0][:,:,m].reshape(-1).double()


def delta_metrics(p,y,free):
    pf=free_flat(p,free); yf=free_flat(y,free)
    pn=float(torch.linalg.vector_norm(pf)); yn=float(torch.linalg.vector_norm(yf))
    if pn<=0 or yn<=0:
        cos=float("nan")
    else:
        cos=float(torch.dot(pf,yf)/(torch.linalg.vector_norm(pf)*torch.linalg.vector_norm(yf)))
    return {"pred_norm":pn,"true_norm":yn,
            "amplitude_ratio":pn/yn if yn>0 else float("nan"),
            "cosine":cos}


def mse(pred,y,free):
    f=free[:,None]
    return float((((pred-y)**2)*f).sum()/(f.sum()*pred.shape[1]))


def train_one(mode,features,gate,coarse,targets,free):
    torch.manual_seed(CORRECTOR_SEED)
    model=TinySpatialResidual()
    opt=torch.optim.Adam(model.parameters(),lr=LR)
    f=free[:,None]
    losses=[]
    for _ in range(EPOCHS):
        corrected,corr=apply_corrector(model,coarse,features,gate,free,mode)
        # targets [B,2,T,1,H,W]
        diff=(corrected[:,None]-targets)**2
        data=(diff*f[None]).sum()/(f.sum()*diff.shape[0]*diff.shape[1]*diff.shape[2])
        reg=0.01*((corr*corr)*f).sum()/(f.sum()*corr.shape[0]*corr.shape[1])
        loss=data+reg
        opt.zero_grad(set_to_none=True); loss.backward(); opt.step()
        losses.append(float(loss.detach()))
    return model,losses


def evaluate_variant(name,model,eval_base,eval_feat,eval_gate,truth,free):
    all_rows=[]
    fits={}
    cos_gains=[]
    mse_wins=0
    gate_all=True
    correction_ratios=[]
    for seed in BASE_SEEDS:
        coarse=eval_base[seed]
        feat=eval_feat
        gate=eval_gate
        with torch.no_grad():
            corrected,corr=apply_corrector(model,coarse,feat,gate,free,name)
        ratio=float(torch.linalg.vector_norm(free_flat(corr,free))/
                    torch.linalg.vector_norm(free_flat(coarse,free)).clamp_min(1e-30))
        correction_ratios.append(ratio)
        sr={}
        for ps in PLUME_SEEDS:
            y22=truth[("S2","W2")][ps]
            y21=truth[("S2","W1")][ps]
            y12=truth[("S1","W2")][ps]
            wm=delta_metrics(corrected[0:1]-corrected[1:2],y22-y21,free)
            sm=delta_metrics(corrected[0:1]-corrected[2:3],y22-y12,free)
            fmse=mse(corrected[0:1],y22,free)
            cg=wm["cosine"]-BASE_COS[seed][ps]
            cos_gains.append(cg)
            if fmse<BASE_MSE[seed][ps]:
                mse_wins+=1
            gates={
              "wind_cosine_gt_0p5":wm["cosine"]>0.5,
              "wind_amplitude_0p5_1p5":0.5<=wm["amplitude_ratio"]<=1.5,
              "source_amplitude_gt_0p5":sm["amplitude_ratio"]>0.5,
            }
            gate_all &= all(gates.values())
            row={"field_mse":fmse,"base_mse":BASE_MSE[seed][ps],
                 "wind_delta":wm,"source_delta":sm,
                 "wind_cosine_gain_vs_base":cg,"gates":gates}
            sr[ps]=row
            all_rows.append(row)
        fits[str(seed)]=sr

    mean_gain=float(np.mean(cos_gains))
    summary={
      "all_four_physical_gates_pass":bool(gate_all),
      "mean_wind_cosine_gain":mean_gain,
      "mean_gain_ge_0p10":mean_gain>=0.10,
      "field_mse_wins_vs_base":mse_wins,
      "correction_norm_ratios":correction_ratios,
      "auxiliary_not_dominant":max(correction_ratios)<=MAX_CORRECTION_RATIO,
    }
    summary["pass"]=bool(
        gate_all and mean_gain>=0.10 and mse_wins>=3 and
        max(correction_ratios)<=MAX_CORRECTION_RATIO
    )
    return {"fits":fits,"summary":summary}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",type=Path,required=True)
    ap.add_argument("--dynamic-wind",type=Path,required=True)
    ap.add_argument("--d0-out",type=Path,required=True)
    ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args()

    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(4)

    root=args.repo_root
    cr=root/"research/causal_compositional_plume_world_model_v1"
    bank=root/"evidence/causal_compositional_plume_world_model_v1/c0_5_real_gaden_bank"
    d0=load_py(cr/"m4_v3_d0_house02.py","d0")
    mm=load_py(cr/"m4_v3_interventional_evolution.py","mm")
    sources,free=d0.load_static_context(bank)
    winds2,_=d0.load_dynamic_winds(args.dynamic_wind)
    winds3=raw_winds3(args.dynamic_wind)
    manifest=json.loads((args.d0_out/"train_manifest.json").read_text())
    cell_m=float(manifest["effective_cell_m"])

    # Frozen base predictions.
    train_base=[]
    eval_base={}
    for seed in BASE_SEEDS:
        key=f"m4v3_seed{seed}"
        cp=args.d0_out/f"{key}.pt"
        if d0.sha256(cp)!=manifest["fits"][key]["checkpoint_sha256"]:
            raise RuntimeError("checkpoint hash mismatch "+key)
        model=mm.InterventionalEvolutionPropagator(
            cell_m=cell_m,internal_dt_s=manifest["physics_dt_s"])
        model.load_state_dict(torch.load(cp,map_location="cpu",weights_only=True))
        model.eval()
        train_base.append(predict_base(d0,mm,model,sources,winds2,TRAIN_PAIRS,free))
        eval_base[seed]=predict_base(d0,mm,model,sources,winds2,EVAL_PAIRS,free)

    # Same target bank for both base seeds. Training never reads S2W2.
    tgs=[]
    for sid,wid in TRAIN_PAIRS:
        tgs.append(torch.stack([d0.target(bank,sid,wid,p) for p in PLUME_SEEDS],0))
    tgs=torch.stack(tgs,0) # [3,2,T,1,H,W]
    targets=torch.cat((tgs,tgs),0)
    coarse=torch.cat(train_base,0)

    train_w3=record_wind3(d0,mm,winds3,TRAIN_PAIRS)
    train_w3=torch.cat((train_w3,train_w3),0)
    train_feat,train_gate=build_features_and_gate(coarse,train_w3,free,cell_m)

    args.output_dir.mkdir(parents=True,exist_ok=False)
    models={}
    losses={}
    for mode in ("gated","global"):
        m,ls=train_one(mode,train_feat,train_gate,coarse,targets,free)
        models[mode]=m
        losses[mode]=ls
        torch.save(m.state_dict(),args.output_dir/f"{mode}_corrector.pt")

    # Holdout is opened only after both correctors are frozen.
    truth={}
    for pair in EVAL_PAIRS:
        truth[pair]={p:d0.target(bank,*pair,p)[None] for p in PLUME_SEEDS}

    eval_w3=record_wind3(d0,mm,winds3,EVAL_PAIRS)
    # physical feature/gate is identical across base seeds because it is source-blind.
    example=eval_base[BASE_SEEDS[0]]
    eval_feat,eval_gate=build_features_and_gate(example,eval_w3,free,cell_m)

    result={
      "mode":"M4_CONSTRAINT_ACTIVE_RESIDUAL_D2",
      "base_checkpoints":list(BASE_SEEDS),
      "corrector_parameters":64,
      "corrector_seed":CORRECTOR_SEED,
      "epochs":EPOCHS,"lr":LR,
      "training_pairs":["S1_W1","S2_W1","S1_W2"],
      "heldout_pair":"S2_W2",
      "physical_gate":"wall<=1 downsampled cell OR top25% strain OR top25% |Wz|",
      "models":{},
    }
    for mode in ("gated","global"):
        ev=evaluate_variant(mode,models[mode],eval_base,eval_feat,eval_gate,truth,free)
        ev["loss_first"]=losses[mode][0]
        ev["loss_last"]=losses[mode][-1]
        result["models"][mode]=ev

    gp=result["models"]["gated"]["summary"]["pass"]
    wp=result["models"]["global"]["summary"]["pass"]
    if gp and not wp:
        decision="CONSTRAINT_LOCAL_RESIDUAL_SIGNAL"
    elif gp and wp:
        decision="GENERIC_RESIDUAL_FIT_NOT_MECHANISM_SPECIFIC"
    elif (not gp) and wp:
        decision="GENERIC_ONLY_NO_CONSTRAINT_MECHANISM"
    else:
        decision="CONSTRAINT_LOCAL_RESIDUAL_NO_GO"
    result["decision"]=decision

    (args.output_dir/"d2_result.json").write_text(json.dumps(result,indent=2,allow_nan=True)+"\n")
    print(json.dumps(result,indent=2,allow_nan=True))


if __name__=="__main__":
    main()

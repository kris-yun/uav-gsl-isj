#!/usr/bin/env python3
"""D1 development screen: tiny causal memory closure on frozen M4-v3.

House02 is development-only and already opened. This script does not change
M4-v3. It freezes the two M4-v3 checkpoints and trains ONE shared, source-blind
memory closure on S1W1/S2W1/S1W2 only, then evaluates S2W2.

Goal:
Can a very small history-conditioned correction repair the wrong wind-response
geometry without replacing the coarse characteristic transport?
"""
from __future__ import annotations

import argparse, importlib.util, json, math
from pathlib import Path
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

TRAIN_PAIRS=(("S1","W1"),("S2","W1"),("S1","W2"))
EVAL_PAIRS=(("S2","W2"),("S2","W1"),("S1","W2"))
PLUME_SEEDS=("A","B")
BASE_SEEDS=(1729,2718)
CLOSURE_SEED=4242
EPOCHS=80
LR=5e-3

BASE_D0_COS={
  1729:{"A":0.3505734245283621,"B":0.3832453097348595},
  2718:{"A":0.3406864424162008,"B":0.3697538958716866},
}
BASE_D0_MSE={
  1729:{"A":0.28387215733528137,"B":0.29915934801101685},
  2718:{"A":0.2931515574455261,"B":0.3083305060863495},
}

def load_py(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

class TinyCausalMemoryClosure(nn.Module):
    """55-parameter source-blind local memory correction.

    Inputs per snapshot:
      current coarse log field,
      first temporal difference,
      second temporal difference,
      current wind u, v, speed.

    It never receives source ID, source coordinates or target truth.
    """
    def __init__(self):
        super().__init__()
        self.conv=nn.Conv2d(6,1,3,padding=1,bias=True)
        nn.init.zeros_(self.conv.weight)
        nn.init.zeros_(self.conv.bias)

    def forward(self, coarse_log, wind_now, free_mask):
        # coarse_log [B,T,1,H,W], wind_now [B,T,2,H,W]
        prev=torch.cat((coarse_log[:,0:1],coarse_log[:,:-1]),dim=1)
        prev2=torch.cat((coarse_log[:,0:1],coarse_log[:,0:1],coarse_log[:,:-2]),dim=1)
        d1=coarse_log-prev
        d2=prev-prev2
        speed=torch.linalg.vector_norm(wind_now,dim=2,keepdim=True)
        x=torch.cat((coarse_log,d1,d2,wind_now,speed),dim=2)
        b,t,c,h,w=x.shape
        raw=self.conv(x.reshape(b*t,c,h,w)).reshape(b,t,1,h,w)
        # Bounded correction: the auxiliary cannot arbitrarily replace the base.
        correction=0.5*torch.tanh(raw)
        corrected=(coarse_log+correction).clamp_min(0.0)
        corrected=corrected*free_mask[:,None]
        correction=correction*free_mask[:,None]
        return corrected,correction

def record_wind_fields(d0,mm,winds,pairs,device):
    steps=d0.record_steps()
    ids=mm.gaden_wind_index_schedule(
        steps[-1],d0.PHYSICS_DT_S,d0.WIND_DT_S,11,d0.LOOP_FROM,d0.LOOP_TO)
    out=[]
    for _,wid in pairs:
        seq=winds[wid]
        snapshots=[]
        for s in steps:
            snapshots.append(seq[ids[s-1]])
        out.append(torch.stack(snapshots,dim=0))
    # [B,T,2,H,W]
    return torch.stack(out,dim=0).to(device)

def predict_base(d0,mm,model,sources,winds,pairs,free,device):
    sb=torch.cat([sources[s] for s,_ in pairs],dim=0).to(device)
    sch=d0.build_batch_schedule(mm,winds,pairs,device)
    with torch.no_grad():
        p=d0.evolve_to_records(model,sb,sch,free,use_checkpoint=False)
        plog=torch.log1p(p.clamp_min(0))
    wn=record_wind_fields(d0,mm,winds,pairs,device)
    return plog,wn

def free_flat(x,free):
    mask=free[0,0]>0.5
    return x[:,:,0][:,:,mask].reshape(-1).double()

def delta_metrics(p,y,free):
    pf=free_flat(p,free); yf=free_flat(y,free)
    pn=float(torch.linalg.vector_norm(pf)); yn=float(torch.linalg.vector_norm(yf))
    cos=float(torch.dot(pf,yf)/(torch.linalg.vector_norm(pf)*torch.linalg.vector_norm(yf))) if pn>0 and yn>0 else float("nan")
    return {"pred_norm":pn,"true_norm":yn,
            "amplitude_ratio":pn/yn if yn>0 else float("nan"),
            "cosine":cos}

def centroid(field,free):
    a=field[0,:,0].clamp_min(0).double()*free[0,0].double()[None]
    rr,cc=torch.meshgrid(torch.arange(a.shape[-2],dtype=torch.double),
                         torch.arange(a.shape[-1],dtype=torch.double),indexing="ij")
    pts=[]
    for z in a:
        mass=z.sum()
        if float(mass)<=1e-12: pts.append((float("nan"),float("nan")))
        else: pts.append((float((z*rr).sum()/mass),float((z*cc).sum()/mass)))
    return np.asarray(pts)

def centroid_shift(a,b,free):
    d=centroid(b,free)-centroid(a,free)
    good=np.isfinite(d).all(axis=1)
    v=d[good].mean(axis=0)
    return {"vector":v.tolist(),"norm":float(np.linalg.norm(v))}

def mse(pred,y,free):
    f=free[:,None]
    return float((((pred-y)**2)*f).sum()/(f.sum()*pred.shape[1]))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",type=Path,required=True)
    ap.add_argument("--dynamic-wind",type=Path,required=True)
    ap.add_argument("--d0-out",type=Path,required=True)
    ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args()

    torch.use_deterministic_algorithms(True); torch.set_num_threads(4)
    root=args.repo_root
    cr=root/"research/causal_compositional_plume_world_model_v1"
    bank=root/"evidence/causal_compositional_plume_world_model_v1/c0_5_real_gaden_bank"
    d0=load_py(cr/"m4_v3_d0_house02.py","d0")
    mm=load_py(cr/"m4_v3_interventional_evolution.py","mm")
    manifest=json.loads((args.d0_out/"train_manifest.json").read_text())
    sources,free=d0.load_static_context(bank)
    winds,_=d0.load_dynamic_winds(args.dynamic_wind)
    device=torch.device("cpu"); free=free.to(device)

    # Build frozen base predictions for both checkpoint seeds.
    train_base=[]; train_wind=[]
    eval_base={}; eval_wind={}
    for seed in BASE_SEEDS:
        key=f"m4v3_seed{seed}"
        cp=args.d0_out/f"{key}.pt"
        if d0.sha256(cp)!=manifest["fits"][key]["checkpoint_sha256"]:
            raise RuntimeError("checkpoint hash mismatch "+key)
        model=mm.InterventionalEvolutionPropagator(
            cell_m=manifest["effective_cell_m"],
            internal_dt_s=manifest["physics_dt_s"])
        model.load_state_dict(torch.load(cp,map_location="cpu",weights_only=True))
        model.eval()
        p,w=predict_base(d0,mm,model,sources,winds,TRAIN_PAIRS,free,device)
        train_base.append(p); train_wind.append(w)
        pe,we=predict_base(d0,mm,model,sources,winds,EVAL_PAIRS,free,device)
        eval_base[seed]=pe; eval_wind[seed]=we

    # One shared closure sees both frozen base seeds during development.
    train_base=torch.cat(train_base,dim=0)  # [6,T,1,H,W]
    train_wind=torch.cat(train_wind,dim=0)

    # deterministic target = A/B mean, duplicated for both base seeds.
    tgt=[]
    for sid,wid in TRAIN_PAIRS:
        a=d0.target(bank,sid,wid,"A")
        b=d0.target(bank,sid,wid,"B")
        tgt.append(0.5*(a+b))
    tgt=torch.stack(tgt,dim=0)
    tgt=torch.cat((tgt,tgt),dim=0).to(device)

    torch.manual_seed(CLOSURE_SEED)
    closure=TinyCausalMemoryClosure().to(device)
    opt=torch.optim.Adam(closure.parameters(),lr=LR)
    losses=[]
    mask=free.expand(train_base.shape[0],-1,-1,-1)
    for ep in range(EPOCHS):
        corrected,corr=closure(train_base,train_wind,mask)
        diff=(corrected-tgt)**2
        data=(diff*mask[:,None]).sum()/(mask.sum()*diff.shape[1])
        # fixed, predeclared weak regularizer against replacing the base field.
        reg=0.01*((corr*corr)*mask[:,None]).sum()/(mask.sum()*corr.shape[1])
        loss=data+reg
        opt.zero_grad(set_to_none=True); loss.backward(); opt.step()
        losses.append(float(loss.detach()))
    args.output_dir.mkdir(parents=True,exist_ok=False)
    cp=args.output_dir/"memory_closure.pt"
    torch.save(closure.state_dict(),cp)

    result={
      "mode":"M4_V3_MEMORY_CLOSURE_D1_DEVELOPMENT",
      "training_pairs":["S1_W1","S2_W1","S1_W2"],
      "holdout":"S2_W2",
      "base_seeds":list(BASE_SEEDS),
      "closure_seed":CLOSURE_SEED,
      "closure_parameters":sum(p.numel() for p in closure.parameters()),
      "epochs":EPOCHS,"lr":LR,
      "loss_first":losses[0],"loss_last":losses[-1],
      "fits":{},"summary":{}
    }

    all_wind=True; cosine_gains=[]; mse_wins=0; no_big_mse_regression=True
    correction_ratios=[]
    for seed in BASE_SEEDS:
        base=eval_base[seed]; w=eval_wind[seed]
        mask3=free.expand(base.shape[0],-1,-1,-1)
        with torch.no_grad():
            corr,cfield=closure(base,w,mask3)
        # eval batch: 0 S2W2, 1 S2W1, 2 S1W2
        dw=corr[0:1]-corr[1:2]
        ds=corr[0:1]-corr[2:3]
        seedres={}
        correction_ratios.append(float(torch.linalg.vector_norm(free_flat(cfield,free))/
                                       torch.linalg.vector_norm(free_flat(base,free)).clamp_min(1e-30)))
        for ps in PLUME_SEEDS:
            y22=d0.target(bank,"S2","W2",ps)[None]
            y21=d0.target(bank,"S2","W1",ps)[None]
            y12=d0.target(bank,"S1","W2",ps)[None]
            wm=delta_metrics(dw,y22-y21,free)
            sm=delta_metrics(ds,y22-y12,free)
            field_mse=mse(corr[0:1],y22,free)
            base_mse=BASE_D0_MSE[seed][ps]
            cos_gain=wm["cosine"]-BASE_D0_COS[seed][ps]
            cosine_gains.append(cos_gain)
            if field_mse < base_mse: mse_wins += 1
            if field_mse > 1.10*base_mse: no_big_mse_regression=False
            gates={
              "wind_cosine_gt_0p5":wm["cosine"]>0.5,
              "wind_amplitude_0p5_1p5":0.5<=wm["amplitude_ratio"]<=1.5,
              "source_amplitude_gt_0p5":sm["amplitude_ratio"]>0.5,
            }
            all_wind &= all(gates.values())
            seedres[ps]={
              "field_mse":field_mse,"base_m4v3_mse":base_mse,
              "wind_delta":wm,"source_delta":sm,
              "wind_cosine_gain_vs_base":cos_gain,
              "true_centroid_shift":centroid_shift(y21,y22,free),
              "corrected_centroid_shift":centroid_shift(corr[1:2],corr[0:1],free),
              "gates":gates
            }
        result["fits"][f"base_seed{seed}"]=seedres

    mean_gain=float(np.mean(cosine_gains))
    result["summary"]={
      "all_four_physical_gates_pass":all_wind,
      "mean_wind_cosine_gain":mean_gain,
      "wind_cosine_gain_gate":mean_gain>=0.10,
      "field_mse_wins_vs_base":mse_wins,
      "no_gt10pct_field_mse_regression":no_big_mse_regression,
      "correction_norm_ratios":correction_ratios,
      "auxiliary_not_dominant":max(correction_ratios)<=0.5,
    }
    passed=(all_wind and mean_gain>=0.10 and mse_wins>=3 and
            no_big_mse_regression and max(correction_ratios)<=0.5)
    result["summary"]["decision"]="D1_MEMORY_AUX_SURVIVES" if passed else "D1_MEMORY_AUX_NO_GO"
    (args.output_dir/"d1_result.json").write_text(json.dumps(result,indent=2,allow_nan=True)+"\n")
    print(json.dumps(result,indent=2,allow_nan=True))

if __name__=="__main__":
    main()

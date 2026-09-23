#!/usr/bin/env python3
"""M4-v3 D0 development trainer/evaluator.

House02 is development-only and already opened. Training is hard-separated from
S2-W2: train mode never loads either S2_W2 concentration target. Evaluate mode
requires hashed checkpoints produced by train mode before opening the holdout.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import torch
from torch.nn import functional as F
from torch.utils.checkpoint import checkpoint

TRAIN_PAIRS = (("S1","W1"), ("S2","W1"), ("S1","W2"))
HOLDOUT_PAIR = ("S2","W2")
PLUME_SEEDS = ("A","B")
TRAIN_SEEDS = (1729,2718)
TARGET_TIMES_S = (50,75,100,125,150,175,200,225,250,275)
PHYSICS_DT_S = 0.1
WIND_DT_S = 1.0
LOOP_FROM = 1
LOOP_TO = 10
EPOCHS = 20
LR = 1e-2
MONO_MSE = {
    1729: {"A":0.442161500453949, "B":0.4313753545284271},
    2718: {"A":0.31033462285995483, "B":0.2978709042072296},
}

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def load_module(path:Path):
    spec=importlib.util.spec_from_file_location("m4v3_model",path)
    m=importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(m)
    return m

def load_static_context(bank:Path):
    g=bank/"geometry"
    src={}
    for sid in ("S1","S2"):
        a=np.load(g/f"source_map_{sid}.npy",allow_pickle=False).astype(np.float32)
        src[sid]=torch.from_numpy(a)[None,None]
    mask=np.load(g/"obstacle_mask_z0p20.npy",allow_pickle=False)
    mask=torch.from_numpy((mask==0).astype(np.float32))[None,None]
    src={k:F.max_pool2d(v,2,ceil_mode=True) for k,v in src.items()}
    free=1.0-F.max_pool2d(1.0-mask,2,ceil_mode=True)
    return src,free

def load_dynamic_winds(dynamic:Path):
    out={}
    for wid in ("W1","W2"):
        p=dynamic/f"wind_{wid}_sequence_z0p20.npy"
        a=np.load(p,allow_pickle=False).astype(np.float32)
        if a.shape!=(11,83,119,3) or not np.isfinite(a).all():
            raise ValueError(f"dynamic wind contract drift {wid}: {a.shape}")
        t=torch.from_numpy(a).permute(0,3,1,2)[:,:2]
        out[wid]=F.avg_pool2d(t,2,ceil_mode=True)
    manifest=json.loads((dynamic/"wind_sequence_manifest.json").read_text())
    if not manifest["iteration1_matches_existing_contract"]["pass"]:
        raise ValueError("dynamic wind iteration-1 anchor failed")
    return out,manifest

def target(bank:Path,sid:str,wid:str,ps:str):
    p=bank/"realizations"/f"{sid}_{wid}_{ps}"/"concentration.npy"
    a=np.load(p,allow_pickle=False)
    if a.shape!=(10,83,119) or not np.isfinite(a).all() or (a<0).any():
        raise ValueError(f"target drift {p}")
    y=torch.from_numpy(np.log1p(a).astype(np.float32))[:,None]
    return F.avg_pool2d(y,2,ceil_mode=True)

def build_batch_schedule(module,winds:dict,pairs,device):
    max_steps=int(round(max(TARGET_TIMES_S)/PHYSICS_DT_S))
    ids=module.gaden_wind_index_schedule(
        max_steps,PHYSICS_DT_S,WIND_DT_S,11,LOOP_FROM,LOOP_TO)
    items=[]
    idx=torch.as_tensor(ids,dtype=torch.long)
    for _,wid in pairs:
        items.append(winds[wid][idx])
    # list [T,2,H,W] -> [T,B,2,H,W]
    return torch.stack(items,dim=1).to(device)

def record_steps():
    return [int(round(t/PHYSICS_DT_S)) for t in TARGET_TIMES_S]

def evolve_to_records(model,source_batch,wind_schedule,free_mask,use_checkpoint=True):
    steps=record_steps()
    state=torch.zeros_like(source_batch)
    outputs=[]
    start=0
    mask=free_mask.expand(source_batch.shape[0],-1,-1,-1)
    def segment(s,src,w,msk):
        z=s
        for i in range(w.shape[0]):
            z=model.step(z,src,w[i],msk)
        return z
    for end in steps:
        w=wind_schedule[start:end]
        if use_checkpoint and model.training:
            state=checkpoint(segment,state,source_batch,w,mask,use_reentrant=False)
        else:
            state=segment(state,source_batch,w,mask)
        outputs.append(state)
        start=end
    # [B,T,1,H,W]
    return torch.stack(outputs,dim=1)

def free_mse(pred_log,y,free):
    f=free[:,None]
    return float((((pred_log-y)**2)*f).sum()/f.sum()/pred_log.shape[1])

def flatten_free(x,free):
    m=(free[0,0]>0.5)
    return x[:,:,0][:,:,m].reshape(-1).double()

def delta_metrics(p,y,free):
    pf=flatten_free(p,free); yf=flatten_free(y,free)
    pn=float(torch.linalg.vector_norm(pf)); yn=float(torch.linalg.vector_norm(yf))
    cos=float(torch.dot(pf,yf)/(torch.linalg.vector_norm(pf)*torch.linalg.vector_norm(yf))) if pn>0 and yn>0 else float("nan")
    return {"pred_norm":pn,"true_norm":yn,
            "amplitude_ratio":pn/yn if yn>0 else float("nan"),
            "cosine":cos}

def centroid(field,free):
    # field [1,T,1,H,W], nonnegative diagnostic field
    a=field[0,:,0].clamp_min(0).double()*free[0,0].double()[None]
    rr,cc=torch.meshgrid(torch.arange(a.shape[-2],dtype=torch.double,device=a.device),
                         torch.arange(a.shape[-1],dtype=torch.double,device=a.device),indexing="ij")
    pts=[]
    for z in a:
        mass=z.sum()
        if float(mass)<=1e-12: pts.append((float("nan"),float("nan")))
        else: pts.append((float((z*rr).sum()/mass),float((z*cc).sum()/mass)))
    return np.asarray(pts)

def centroid_shift(a,b,free):
    d=centroid(b,free)-centroid(a,free)
    good=np.isfinite(d).all(axis=1)
    if not good.any(): return {"vector":[float("nan"),float("nan")],"norm":float("nan")}
    v=d[good].mean(axis=0)
    return {"vector":v.tolist(),"norm":float(np.linalg.norm(v))}

def checkpoint_hash_ok(out:Path,manifest,key):
    p=out/f"{key}.pt"
    digest=sha256(p)
    if digest!=manifest["fits"][key]["checkpoint_sha256"]:
        raise ValueError(f"checkpoint hash drift {key}")
    return p

def train(args):
    module=load_module(args.model_script)
    sources,free=load_static_context(args.bank)
    winds,wmanifest=load_dynamic_winds(args.dynamic_wind)
    device=torch.device(args.device)
    source_batch=torch.cat([sources[s] for s,_ in TRAIN_PAIRS],dim=0).to(device)
    free=free.to(device)
    schedule=build_batch_schedule(module,winds,TRAIN_PAIRS,device)
    # Training target read list intentionally excludes S2_W2.
    target_bank=[]
    for sid,wid in TRAIN_PAIRS:
        target_bank.append(torch.stack([target(args.bank,sid,wid,ps) for ps in PLUME_SEEDS],dim=0))
    targets=torch.stack(target_bank,dim=0).to(device) # [B,2,T,1,H,W]

    args.out.mkdir(parents=True,exist_ok=False)
    result={
      "mode":"train",
      "holdout_unopened":["S2_W2_A","S2_W2_B"],
      "train_pairs":[f"{s}_{w}" for s,w in TRAIN_PAIRS],
      "plume_seeds":PLUME_SEEDS,
      "train_seeds":TRAIN_SEEDS,
      "epochs":EPOCHS,"lr":LR,
      "physics_dt_s":PHYSICS_DT_S,
      "effective_cell_m":0.2,
      "target_times_s":TARGET_TIMES_S,
      "wind_manifest_sha256":sha256(args.dynamic_wind/"wind_sequence_manifest.json"),
      "fits":{}
    }
    for seed in TRAIN_SEEDS:
        torch.manual_seed(seed)
        model=module.InterventionalEvolutionPropagator(cell_m=0.2,internal_dt_s=PHYSICS_DT_S).to(device)
        with torch.no_grad():
            model.transport.closure.logits.weight.normal_(0.0,0.01)
            model.transport.closure.logits.bias[:] = torch.tensor([4.,0.,0.,0.,0.],device=device)
            model.transport.closure.logits.bias.add_(0.01*torch.randn_like(model.transport.closure.logits.bias))
            model.transport.loss_raw.fill_(-8.0)
            model.source_strength_raw.fill_(0.0)
        opt=torch.optim.Adam(model.parameters(),lr=LR,weight_decay=0.0)
        losses=[]
        for epoch in range(EPOCHS):
            model.train()
            pred=evolve_to_records(model,source_batch,schedule,free,use_checkpoint=True)
            plog=torch.log1p(pred.clamp_min(0))[:,None] # [B,1,T,1,H,W]
            f=free[None,None] # [1,1,1,1,H,W]
            diff=(plog-targets)**2
            loss=(diff*f).sum()/(f.sum()*diff.shape[0]*diff.shape[1]*diff.shape[2])
            opt.zero_grad(set_to_none=True); loss.backward(); opt.step()
            losses.append(float(loss.detach().cpu()))
            print(f"seed={seed} epoch={epoch+1}/{EPOCHS} loss={losses[-1]:.8g}",flush=True)
        cp=args.out/f"m4v3_seed{seed}.pt"
        torch.save(model.state_dict(),cp)
        result["fits"][f"m4v3_seed{seed}"]={
            "loss_first":losses[0],"loss_last":losses[-1],
            "checkpoint_sha256":sha256(cp)}
    (args.out/"train_manifest.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))

def evaluate(args):
    module=load_module(args.model_script)
    sources,free=load_static_context(args.bank)
    winds,_=load_dynamic_winds(args.dynamic_wind)
    device=torch.device(args.device); free=free.to(device)
    manifest=json.loads((args.out/"train_manifest.json").read_text())
    if manifest.get("holdout_unopened")!=["S2_W2_A","S2_W2_B"]:
        raise ValueError("training manifest holdout contract drift")

    eval_pairs=(("S2","W2"),("S2","W1"),("S1","W2"))
    source_batch=torch.cat([sources[s] for s,_ in eval_pairs],dim=0).to(device)
    schedule=build_batch_schedule(module,winds,eval_pairs,device)

    # Validate every frozen checkpoint hash before opening either S2-W2 target.
    validated={}
    for seed in TRAIN_SEEDS:
        key=f"m4v3_seed{seed}"
        validated[seed]=checkpoint_hash_ok(args.out,manifest,key)

    # Holdout is first opened only after all checkpoint hashes have passed.
    true={}
    for sid,wid in eval_pairs:
        true[(sid,wid)]={ps:target(args.bank,sid,wid,ps).to(device)[None] for ps in PLUME_SEEDS}

    results={"mode":"evaluate","fits":{},"decision":None}
    all_pass=True
    for seed in TRAIN_SEEDS:
        key=f"m4v3_seed{seed}"
        cp=validated[seed]
        model=module.InterventionalEvolutionPropagator(cell_m=0.2,internal_dt_s=PHYSICS_DT_S).to(device)
        model.load_state_dict(torch.load(cp,map_location=device,weights_only=True)); model.eval()
        with torch.no_grad():
            p=evolve_to_records(model,source_batch,schedule,free,use_checkpoint=False)
            plog=torch.log1p(p.clamp_min(0))
            # batch: 0=S2W2,1=S2W1,2=S1W2
            full_dw=plog[0:1]-plog[1:2]
            full_ds=plog[0:1]-plog[2:3]
            full_dw_norm=float(torch.linalg.vector_norm(flatten_free(full_dw,free)))

            model.transport.characteristic_scale=0.0
            pa=evolve_to_records(model,source_batch,schedule,free,use_checkpoint=False)
            palog=torch.log1p(pa.clamp_min(0))
            abl_dw=palog[0:1]-palog[1:2]
            abl_norm=float(torch.linalg.vector_norm(flatten_free(abl_dw,free)))
            model.transport.characteristic_scale=1.0

            # Exact source superposition on W2 final-time schedule.
            max_steps=record_steps()[-1]
            s_w2=build_batch_schedule(module,winds,(("S1","W2"),),device)
            sup=module.superposition_error(
                model,sources["S1"].to(device),sources["S2"].to(device),
                s_w2,free)

        seed_result={"checkpoint_sha256":sha256(cp),
                     "characteristic_ablation_wind_norm_ratio":abl_norm/full_dw_norm if full_dw_norm>0 else float("inf"),
                     "superposition_max_abs_error":sup,
                     "plumes":{}}
        seed_pass=(seed_result["characteristic_ablation_wind_norm_ratio"]<=0.5 and sup<1e-5)
        for ps in PLUME_SEEDS:
            y22=true[("S2","W2")][ps]; y21=true[("S2","W1")][ps]; y12=true[("S1","W2")][ps]
            true_dw=y22-y21; true_ds=y22-y12
            wm=delta_metrics(full_dw,true_dw,free)
            sm=delta_metrics(full_ds,true_ds,free)
            true_ws=wm["true_norm"]/sm["true_norm"] if sm["true_norm"]>0 else float("nan")
            pred_ws=wm["pred_norm"]/sm["pred_norm"] if sm["pred_norm"]>0 else float("nan")
            rws=pred_ws/true_ws if true_ws>0 else float("nan")
            tc=centroid_shift(y21,y22,free)
            pc=centroid_shift(plog[1:2],plog[0:1],free)
            cent_ratio=pc["norm"]/tc["norm"] if tc["norm"]>0 else float("nan")
            mse=free_mse(plog[0:1],y22,free)
            gates={
              "wind_amplitude": 0.5<=wm["amplitude_ratio"]<=1.5,
              "wind_cosine": wm["cosine"]>0.5,
              "centroid_ratio": cent_ratio>0.5,
              "relative_wind_source": rws>0.5,
              "source_amplitude": sm["amplitude_ratio"]>0.5,
              "beats_frozen_monolithic_mse": mse<MONO_MSE[seed][ps],
            }
            plume_pass=all(gates.values())
            seed_pass=seed_pass and plume_pass
            seed_result["plumes"][ps]={
              "field_mse":mse,"monolithic_reference_mse":MONO_MSE[seed][ps],
              "wind_delta":wm,"source_delta":sm,
              "true_wind_to_source":true_ws,"pred_wind_to_source":pred_ws,
              "relative_wind_to_source":rws,
              "true_centroid_shift":tc,"pred_centroid_shift":pc,
              "centroid_shift_magnitude_ratio":cent_ratio,
              "gates":gates,"pass":plume_pass,
            }
        seed_result["pass"]=seed_pass
        results["fits"][key]=seed_result
        all_pass=all_pass and seed_pass

    results["decision"]="D0_PASS_FREEZE_BEFORE_NEW_CONFIRMATION" if all_pass else "D0_FAIL_STOP_M4_V3"
    (args.out/"d0_result.json").write_text(json.dumps(results,indent=2,allow_nan=True)+"\n")
    print(json.dumps(results,indent=2,allow_nan=True))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("mode",choices=("train","evaluate"))
    ap.add_argument("--bank",type=Path,required=True)
    ap.add_argument("--dynamic-wind",type=Path,required=True)
    ap.add_argument("--model-script",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--device",default="cuda" if torch.cuda.is_available() else "cpu")
    args=ap.parse_args()
    if args.mode=="train": train(args)
    else: evaluate(args)

if __name__=="__main__": main()

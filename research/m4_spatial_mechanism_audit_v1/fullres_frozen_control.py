#!/usr/bin/env python3
"""Frozen M4-v3 full-resolution anti-aliasing control.

No training and no parameter changes. Loads the frozen 0.2 m M4-v3 checkpoints,
reuses their learned closure/source/sink parameters, but evaluates the same
transport equations on the original 0.1 m House02 XY grid and raw XY winds.

Purpose: test whether 2x spatial pooling alone explains the failed W1->W2
response geometry. Cosine is primary because source-amplitude calibration may
change with discretization.
"""
from __future__ import annotations
import argparse, importlib.util, json
from pathlib import Path
import numpy as np
import torch

SEEDS=(1729,2718); PLUMES=("A","B")
DT=.1; TIMES=(50,75,100,125,150,175,200,225,250,275)
PAIRS=(("S2","W2"),("S2","W1"))

def load_py(p,n):
    s=importlib.util.spec_from_file_location(n,p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def raw_context(bank):
    g=bank/"geometry"
    src={}
    for sid in ("S1","S2"):
        a=np.load(g/f"source_map_{sid}.npy",allow_pickle=False).astype(np.float32)
        src[sid]=torch.from_numpy(a)[None,None]
    obs=np.load(g/"obstacle_mask_z0p20.npy",allow_pickle=False)
    free=torch.from_numpy((obs==0).astype(np.float32))[None,None]
    return src,free

def raw_winds(dynamic):
    out={}
    for wid in ("W1","W2"):
        a=np.load(dynamic/f"wind_{wid}_sequence_z0p20.npy",allow_pickle=False).astype(np.float32)
        out[wid]=torch.from_numpy(a).permute(0,3,1,2)[:,:2]
    return out

def raw_target(bank,s,w,ps):
    a=np.load(bank/"realizations"/f"{s}_{w}_{ps}"/"concentration.npy",allow_pickle=False)
    return torch.from_numpy(np.log1p(a).astype(np.float32))[:,None]

def schedule(mm,winds,pairs):
    max_steps=int(round(max(TIMES)/DT))
    ids=mm.gaden_wind_index_schedule(max_steps,DT,1.0,11,1,10)
    idx=torch.as_tensor(ids,dtype=torch.long)
    return torch.stack([winds[w][idx] for _,w in pairs],dim=1)

def evolve(model,source,wind,free):
    state=torch.zeros_like(source); mask=free.expand(source.shape[0],-1,-1,-1)
    outs=[]; start=0
    for t in TIMES:
        end=int(round(t/DT))
        for i in range(start,end):
            state=model.step(state,source,wind[i],mask)
        outs.append(state)
        start=end
    return torch.stack(outs,1)

def flat(x,free):
    m=free[0,0]>0.5
    return x[:,:,0][:,:,m].reshape(-1).double()

def metrics(p,y,free):
    a=flat(p,free); b=flat(y,free)
    na=torch.linalg.vector_norm(a); nb=torch.linalg.vector_norm(b)
    return {
      "pred_norm":float(na),"true_norm":float(nb),
      "amplitude_ratio":float(na/nb) if float(nb)>0 else float("nan"),
      "cosine":float(torch.dot(a,b)/(na*nb)) if float(na)>0 and float(nb)>0 else float("nan")
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",type=Path,required=True)
    ap.add_argument("--dynamic-wind",type=Path,required=True)
    ap.add_argument("--d0-out",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    torch.use_deterministic_algorithms(True); torch.set_num_threads(4)
    root=a.repo_root
    cr=root/"research/causal_compositional_plume_world_model_v1"
    bank=root/"evidence/causal_compositional_plume_world_model_v1/c0_5_real_gaden_bank"
    mm=load_py(cr/"m4_v3_interventional_evolution.py","mm")
    src,free=raw_context(bank); winds=raw_winds(a.dynamic_wind)
    sch=schedule(mm,winds,PAIRS)
    sb=torch.cat([src[s] for s,_ in PAIRS],0)
    man=json.loads((a.d0_out/"train_manifest.json").read_text())
    result={"mode":"FROZEN_M4_FULLRES_0P1M_CONTROL","refit":False,"fits":{}}
    for seed in SEEDS:
        cp=a.d0_out/f"m4v3_seed{seed}.pt"
        model=mm.InterventionalEvolutionPropagator(cell_m=.1,internal_dt_s=.1)
        model.load_state_dict(torch.load(cp,map_location="cpu",weights_only=True)); model.eval()
        with torch.no_grad():
            pred=evolve(model,sb,sch,free)
            plog=torch.log1p(pred.clamp_min(0))
        dp=plog[0:1]-plog[1:2]
        rr={}
        for ps in PLUMES:
            dy=raw_target(bank,"S2","W2",ps)[None]-raw_target(bank,"S2","W1",ps)[None]
            rr[ps]={"wind_delta":metrics(dp,dy,free)}
        result["fits"][str(seed)]=rr
    cos=[result["fits"][str(s)][p]["wind_delta"]["cosine"] for s in SEEDS for p in PLUMES]
    result["summary"]={
      "cosines":cos,
      "all_cosine_gt_0p5":all(x>.5 for x in cos),
      "mean_cosine":float(np.mean(cos)),
      "decision":"POOLING_ALIAS_EXPLAINS_FAILURE" if all(x>.5 for x in cos) else "POOLING_ALONE_NOT_SUFFICIENT"
    }
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__": main()

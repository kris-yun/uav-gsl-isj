#!/usr/bin/env python3
"""Minimal cross-combination memory/stochasticity probe for MZ-PBD.

NO neural training. The only fitted quantities are global scalar AR coefficients
for residual dynamics, learned on S1W1/S2W1/S1W2 and evaluated on S2W2.

Question 1: does a second residual-history lag improve held-out residual
prediction beyond a one-lag Markov predictor?

Question 2: under identical source/wind forcing, is plume-realization
variability large enough to justify a stochastic orthogonal component?
"""
from __future__ import annotations
import argparse, importlib.util, json
from pathlib import Path
import numpy as np
import torch

TRAIN_PAIRS=(("S1","W1"),("S2","W1"),("S1","W2"))
HOLDOUT=("S2","W2")
ALL_PAIRS=TRAIN_PAIRS+(HOLDOUT,)
TRAIN_SEEDS=(1729,2718)
MEMORY_GAIN_GATE=0.05
STOCHASTIC_ENERGY_GATE=0.05

def load_py(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def flat(x,free):
    mask=free[0,0]>0.5
    return x[:,0][:,mask].double()  # [T,N]

def fit_ar1(train_series):
    xs=[]; ys=[]
    for r in train_series:
        xs.append(r[:-1].reshape(-1))
        ys.append(r[1:].reshape(-1))
    x=torch.cat(xs); y=torch.cat(ys)
    return float(torch.dot(x,y)/torch.dot(x,x).clamp_min(1e-30))

def fit_ar2(train_series):
    x1=[]; x2=[]; ys=[]
    for r in train_series:
        x1.append(r[1:-1].reshape(-1))
        x2.append(r[:-2].reshape(-1))
        ys.append(r[2:].reshape(-1))
    a=torch.stack((torch.cat(x1),torch.cat(x2)),dim=1)
    y=torch.cat(ys)
    sol=torch.linalg.lstsq(a,y[:,None]).solution[:,0]
    return float(sol[0]),float(sol[1])

def score_ar1(r,a):
    y=r[1:]; p=a*r[:-1]
    return float(((p-y)**2).mean())

def score_ar2(r,a,b):
    y=r[2:]; p=a*r[1:-1]+b*r[:-2]
    return float(((p-y)**2).mean())

def stochastic_ratio(A,B,free):
    A=flat(A,free); B=flat(B,free)
    mean=0.5*(A+B)
    half=0.5*(A-B)
    # relative realization-specific energy against total (mean + halfdiff)
    em=float((mean*mean).sum()); es=float((half*half).sum())
    return es/(em+es+1e-30)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",type=Path,required=True)
    ap.add_argument("--dynamic-wind",type=Path,required=True)
    ap.add_argument("--d0-out",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()

    root=args.repo_root
    cr=root/"research/causal_compositional_plume_world_model_v1"
    bank=root/"evidence/causal_compositional_plume_world_model_v1/c0_5_real_gaden_bank"
    d0=load_py(cr/"m4_v3_d0_house02.py","d0")
    mm=load_py(cr/"m4_v3_interventional_evolution.py","mm")
    torch.use_deterministic_algorithms(True); torch.set_num_threads(4)

    sources,free=d0.load_static_context(bank)
    winds,_=d0.load_dynamic_winds(args.dynamic_wind)
    manifest=json.loads((args.d0_out/"train_manifest.json").read_text())
    source_batch=torch.cat([sources[s] for s,_ in ALL_PAIRS],dim=0)
    schedule=d0.build_batch_schedule(mm,winds,ALL_PAIRS,torch.device("cpu"))

    truth={}
    for pair in ALL_PAIRS:
        truth[pair]={ps:d0.target(bank,*pair,ps) for ps in ("A","B")}

    out={"mode":"MZ_PBD_MINIMAL_MEMORY_PROBE","training":"scalar_AR_only",
         "memory_gain_gate":MEMORY_GAIN_GATE,
         "stochastic_energy_gate":STOCHASTIC_ENERGY_GATE,
         "fits":{}}
    gains=[]; stochastic=[]
    for seed in TRAIN_SEEDS:
        key=f"m4v3_seed{seed}"
        cp=args.d0_out/f"{key}.pt"
        if d0.sha256(cp)!=manifest["fits"][key]["checkpoint_sha256"]:
            raise RuntimeError("checkpoint hash mismatch "+key)
        model=mm.InterventionalEvolutionPropagator(
            cell_m=manifest["effective_cell_m"],
            internal_dt_s=manifest["physics_dt_s"])
        model.load_state_dict(torch.load(cp,map_location="cpu",weights_only=True))
        model.eval()
        with torch.no_grad():
            pred=d0.evolve_to_records(model,source_batch,schedule,free,use_checkpoint=False)
            plog=torch.log1p(pred.clamp_min(0))[:,:,0]  # [B,T,H,W]

        shared={}
        for i,pair in enumerate(ALL_PAIRS):
            pp=plog[i][:,None]
            rA=truth[pair]["A"]-pp
            rB=truth[pair]["B"]-pp
            shared[pair]=flat(0.5*(rA+rB),free)
            stochastic.append(stochastic_ratio(truth[pair]["A"],truth[pair]["B"],free))

        train=[shared[p] for p in TRAIN_PAIRS]
        a1=fit_ar1(train)
        a2,b2=fit_ar2(train)
        h=shared[HOLDOUT]
        # Align comparison to times 2..T-1 so AR1/AR2 score the exact same samples.
        y=h[2:]
        p1=a1*h[1:-1]
        p2=a2*h[1:-1]+b2*h[:-2]
        mse1=float(((p1-y)**2).mean())
        mse2=float(((p2-y)**2).mean())
        gain=(mse1-mse2)/mse1 if mse1>0 else float("nan")
        gains.append(gain)
        out["fits"][key]={
            "ar1_coefficient":a1,
            "ar2_coefficients":[a2,b2],
            "holdout_ar1_mse":mse1,
            "holdout_ar2_mse":mse2,
            "relative_memory_gain":gain,
            "memory_gate_pass":bool(np.isfinite(gain) and gain>=MEMORY_GAIN_GATE),
        }

    med_stoch=float(np.median(stochastic))
    out["summary"]={
        "memory_gains":gains,
        "memory_both_seeds_pass":all(np.isfinite(g) and g>=MEMORY_GAIN_GATE for g in gains),
        "median_realization_specific_energy_fraction":med_stoch,
        "stochastic_gate_pass":med_stoch>=STOCHASTIC_ENERGY_GATE,
    }
    if not out["summary"]["memory_both_seeds_pass"]:
        decision="STOP_MZ_MEMORY_AS_MAIN"
    elif not out["summary"]["stochastic_gate_pass"]:
        decision="MEMORY_SURVIVES_STOCHASTIC_AUX_NOT_YET_JUSTIFIED"
    else:
        decision="MZ_MEMORY_AND_STOCHASTICITY_SURVIVE_MINIMAL_SCREEN"
    out["summary"]["decision"]=decision
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,indent=2,allow_nan=True)+"\n")
    print(json.dumps(out,indent=2,allow_nan=True))

if __name__=="__main__":
    main()

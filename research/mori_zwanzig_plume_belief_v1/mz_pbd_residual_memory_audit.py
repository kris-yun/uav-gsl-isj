#!/usr/bin/env python3
"""Source-blind residual-memory audit for MZ-PBD screening.

NO TRAINING. House02 is development-only and already opened.

Purpose:
1) decompose frozen M4-v3 residuals from the two plume realizations into
   a shared/model-form component and a realization-specific component;
2) test whether the shared residual has temporal ordering/memory beyond a
   shuffled-time null;
3) quantify whether realization-specific variability is material.

This audit can kill the MZ-PBD screening hypothesis. It cannot establish a
scientific ADVANCE claim.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import torch


PAIRS=(("S1","W1"),("S2","W1"),("S1","W2"),("S2","W2"))
TRAIN_SEEDS=(1729,2718)
PERMUTATIONS=5000
PERM_SEED=20260923


def load_py(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(m)
    return m


def flatten_time_free(x:torch.Tensor,free:torch.Tensor)->torch.Tensor:
    # x [T,1,H,W] -> [T,N]
    mask=free[0,0]>0.5
    return x[:,0][:,mask].double()


def cosine_rows(a:torch.Tensor,b:torch.Tensor)->torch.Tensor:
    an=torch.linalg.vector_norm(a,dim=1)
    bn=torch.linalg.vector_norm(b,dim=1)
    dot=(a*b).sum(dim=1)
    return dot/(an*bn).clamp_min(1e-30)


def adjacent_order_test(seq:torch.Tensor,nperm:int=PERMUTATIONS):
    # seq [T,N]. Statistic = mean cosine between adjacent temporal residuals.
    if seq.shape[0] < 4:
        raise ValueError("need >=4 time points")
    obs=float(cosine_rows(seq[:-1],seq[1:]).mean())
    rng=np.random.default_rng(PERM_SEED)
    vals=np.empty(nperm,dtype=np.float64)
    arr=seq.cpu()
    for i in range(nperm):
        order=rng.permutation(arr.shape[0])
        z=arr[torch.as_tensor(order)]
        vals[i]=float(cosine_rows(z[:-1],z[1:]).mean())
    p=float((1.0+np.sum(vals>=obs))/(1.0+nperm))
    return {
        "adjacent_mean_cosine":obs,
        "shuffle_mean":float(vals.mean()),
        "shuffle_std":float(vals.std(ddof=1)),
        "one_sided_p":p,
        "permutations":nperm,
    }


def gradient_energy_ratio(field:torch.Tensor,free:torch.Tensor)->float:
    # field [T,1,H,W]. Zero differences crossing obstacles.
    x=field[:,0].double()
    m=(free[0,0]>0.5)
    dx=x[:,1:,:]-x[:,:-1,:]
    dy=x[:,:,1:]-x[:,:,:-1]
    mx=(m[1:,:]&m[:-1,:])[None]
    my=(m[:,1:]&m[:,:-1])[None]
    ge=(dx.pow(2)*mx).sum()+(dy.pow(2)*my).sum()
    e=(x.pow(2)*m[None]).sum()
    return float(ge/e.clamp_min(1e-30))


def norm_free(field:torch.Tensor,free:torch.Tensor)->float:
    return float(torch.linalg.vector_norm(flatten_time_free(field,free)))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",type=Path,required=True)
    ap.add_argument("--dynamic-wind",type=Path,required=True)
    ap.add_argument("--d0-out",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()

    root=args.repo_root
    research=root/"research/causal_compositional_plume_world_model_v1"
    bank=root/"evidence/causal_compositional_plume_world_model_v1/c0_5_real_gaden_bank"
    model_path=research/"m4_v3_interventional_evolution.py"
    d0_path=research/"m4_v3_d0_house02.py"

    d0=load_py(d0_path,"m4v3_d0")
    modelmod=load_py(model_path,"m4v3_model")

    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(4)
    sources,free=d0.load_static_context(bank)
    winds,wmanifest=d0.load_dynamic_winds(args.dynamic_wind)
    free=free.cpu()

    # Load all targets only because House02 is already development-open.
    truth={}
    for sid,wid in PAIRS:
        truth[(sid,wid)]={}
        for ps in ("A","B"):
            truth[(sid,wid)][ps]=d0.target(bank,sid,wid,ps).cpu()

    source_batch=torch.cat([sources[s] for s,_ in PAIRS],dim=0)
    schedule=d0.build_batch_schedule(modelmod,winds,PAIRS,torch.device("cpu"))
    manifest=json.loads((args.d0_out/"train_manifest.json").read_text())

    result={
        "status":"MZ_PBD_SCREENING_ONLY",
        "house":"House02",
        "training":False,
        "pairs":[f"{s}_{w}" for s,w in PAIRS],
        "permutations":PERMUTATIONS,
        "wind_manifest_sha256":manifest["wind_manifest_sha256"],
        "fits":{},
        "summary":{},
    }

    memory_support_count=0
    total_tests=0
    stochastic_fracs=[]

    for seed in TRAIN_SEEDS:
        key=f"m4v3_seed{seed}"
        cp=args.d0_out/f"{key}.pt"
        if d0.sha256(cp)!=manifest["fits"][key]["checkpoint_sha256"]:
            raise RuntimeError(f"checkpoint hash mismatch {key}")
        model=modelmod.InterventionalEvolutionPropagator(
            cell_m=manifest["effective_cell_m"],
            internal_dt_s=manifest["physics_dt_s"],
        )
        model.load_state_dict(torch.load(cp,map_location="cpu",weights_only=True))
        model.eval()
        with torch.no_grad():
            pred=d0.evolve_to_records(
                model,source_batch,schedule,free,use_checkpoint=False
            )
            pred_log=torch.log1p(pred.clamp_min(0))[:, :, 0] # [B,T,H,W]

        fit={}
        for bi,(sid,wid) in enumerate(PAIRS):
            p=pred_log[bi][:,None]
            rA=truth[(sid,wid)]["A"]-p
            rB=truth[(sid,wid)]["B"]-p
            shared=0.5*(rA+rB)
            stochastic=0.5*(rA-rB)

            ns=norm_free(shared,free)
            nn=norm_free(stochastic,free)
            denom=ns*ns+nn*nn
            frac=(nn*nn/denom) if denom>0 else float("nan")
            stochastic_fracs.append(frac)

            mem=adjacent_order_test(flatten_time_free(shared,free))
            memory_supported=(
                mem["adjacent_mean_cosine"]>0.0 and mem["one_sided_p"]<0.05
            )
            memory_support_count += int(memory_supported)
            total_tests += 1

            fit[f"{sid}_{wid}"]={
                "shared_bias_norm":ns,
                "realization_specific_halfdiff_norm":nn,
                "stochastic_energy_fraction":frac,
                "shared_gradient_energy_ratio":gradient_energy_ratio(shared,free),
                "stochastic_gradient_energy_ratio":gradient_energy_ratio(stochastic,free),
                "shared_temporal_order_test":mem,
                "memory_supported_by_shuffle_test":memory_supported,
            }
        result["fits"][key]=fit

    result["summary"]={
        "memory_supported_tests":memory_support_count,
        "memory_total_tests":total_tests,
        "median_stochastic_energy_fraction":float(np.median(stochastic_fracs)),
        "max_stochastic_energy_fraction":float(np.max(stochastic_fracs)),
        "memory_screen":"SURVIVES" if memory_support_count>=total_tests//2+1 else "NO_SUPPORT",
        "stochastic_screen":"SURVIVES" if float(np.median(stochastic_fracs))>=0.10 else "WEAK",
        "decision":None,
    }
    if result["summary"]["memory_screen"]=="NO_SUPPORT":
        decision="STOP_MZ_MEMORY_LINE"
    elif result["summary"]["stochastic_screen"]=="WEAK":
        decision="MEMORY_ONLY_CANDIDATE_STOCHASTIC_AUX_NOT_JUSTIFIED"
    else:
        decision="MZ_PBD_SURVIVES_SCREEN_BUILD_D1_ONLY"
    result["summary"]["decision"]=decision

    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=True)+"\n")
    print(json.dumps(result,indent=2,allow_nan=True))


if __name__=="__main__":
    main()

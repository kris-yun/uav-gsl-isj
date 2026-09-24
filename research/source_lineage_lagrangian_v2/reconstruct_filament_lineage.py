#!/usr/bin/env python3
"""Recover persistent filament lineage IDs from exported GADEN snapshots.

Frozen House02 generator contract:
- sim_dt = 0.1 s
- num_filaments_sec = 7
- source emission is the GADEN RunningSimulation releaseAccumulator rule
- every emitted filament is moved/grown once in its birth simulation step
- sigma growth is deterministic and path-independent

Thus sigma identifies age-in-steps and:
    birth_step = snapshot_sim_step - age_steps + 1

The legacy ROS parameters variable_rate / filament_stop_steps were passed on the
command line but are not consumed by the frozen generator implementation.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np


def load_npz(path:Path):
    z=np.load(path,allow_pickle=False)
    required={"filaments","offsets","simulation_steps","times_s"}
    if not required<=set(z.files):
        raise ValueError(f"{path}: missing {sorted(required-set(z.files))}")
    return (z["filaments"].astype(np.float32),
            z["offsets"].astype(np.int64),
            z["simulation_steps"].astype(np.int64),
            z["times_s"].astype(np.float64))


def theoretical_sigma(max_age:int,initial:float,gamma:float,dt:float):
    s=np.float32(initial)
    g=np.float32(gamma); d=np.float32(dt)
    out=np.empty(max_age+1,dtype=np.float32)
    out[0]=s
    for age in range(1,max_age+1):
        s=np.float32(s + np.float32(g/(np.float32(2.0)*s))*d)
        out[age]=s
    return out


def emission_counts(max_step:int,rate:float,dt:float):
    """Exact float32 releaseAccumulator schedule."""
    r=np.float32(rate); d=np.float32(dt); acc=np.float32(0.0)
    out=np.zeros(max_step+1,dtype=np.int16)
    per=np.float32(r*d)
    for step in range(max_step+1):
        acc=np.float32(acc+per)
        n=int(np.floor(acc))
        out[step]=n
        acc=np.float32(acc-n)
    return out


def nearest_ages(sigmas:np.ndarray,lookup:np.ndarray,tol:float):
    # lookup is monotone. Search nearest of left/right neighbors.
    x=sigmas.astype(np.float32)
    idx=np.searchsorted(lookup,x,side="left")
    hi=np.clip(idx,1,len(lookup)-1)
    lo=hi-1
    elo=np.abs(x-lookup[lo]); ehi=np.abs(x-lookup[hi])
    use_hi=ehi<elo
    age=np.where(use_hi,hi,lo).astype(np.int64)
    err=np.minimum(elo,ehi)
    if np.max(err,initial=0.0)>tol:
        j=int(np.argmax(err))
        raise RuntimeError(
            f"sigma->age mismatch: max error {float(err[j]):.6g} > {tol}; "
            f"sigma={float(x[j]):.7g}, nearest={float(lookup[age[j]]):.7g}")
    if np.any(age<1):
        raise RuntimeError("found age 0, but saved filaments have already undergone one growth step")
    return age,err


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("filament_npz",type=Path)
    ap.add_argument("output_npz",type=Path)
    ap.add_argument("--sim-dt",type=float,default=0.1)
    ap.add_argument("--emission-rate",type=float,default=7.0)
    ap.add_argument("--initial-sigma",type=float,default=10.0)
    ap.add_argument("--growth-gamma",type=float,default=15.0)
    ap.add_argument("--sigma-tol",type=float,default=2e-4)
    args=ap.parse_args()

    fil,off,sim_steps,times=load_npz(args.filament_npz)
    max_step=int(sim_steps.max())
    sigma_lut=theoretical_sigma(max_step+2,args.initial_sigma,args.growth_gamma,args.sim_dt)
    age,age_err=nearest_ages(fil[:,3],sigma_lut,args.sigma_tol)
    births_allowed=emission_counts(max_step,args.emission_rate,args.sim_dt)

    lineage=np.empty(len(fil),dtype=np.int64)
    duplicate_snapshots=0
    invalid_births=0
    shared_counts=[]
    progression_errors=0

    for k,step in enumerate(sim_steps):
        s,e=int(off[k]),int(off[k+1])
        lineage[s:e]=int(step)-age[s:e]+1
        ids=lineage[s:e]
        if len(np.unique(ids))!=len(ids):
            duplicate_snapshots+=1
        bad=(ids<0) | (ids>max_step)
        if np.any(~bad):
            valid=ids[~bad]
            bad_emit=births_allowed[valid] < 1
            invalid_births += int(np.sum(bad_emit))
        invalid_births += int(np.sum(bad))

        if k:
            ps,pe=int(off[k-1]),int(off[k])
            prev_ids=lineage[ps:pe]
            common,ia,ib=np.intersect1d(prev_ids,ids,return_indices=True)
            shared_counts.append(int(len(common)))
            if len(common):
                prev_age=age[ps:pe][ia]
                cur_age=age[s:e][ib]
                expected_delta=int(step-sim_steps[k-1])
                progression_errors += int(np.sum((cur_age-prev_age)!=expected_delta))

    if duplicate_snapshots:
        raise RuntimeError(f"duplicate lineage IDs in {duplicate_snapshots} snapshots")
    if invalid_births:
        raise RuntimeError(f"{invalid_births} filament IDs map to impossible emission steps")
    if progression_errors:
        raise RuntimeError(f"{progression_errors} shared lineages violate exact sigma-age progression")

    args.output_npz.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(args.output_npz,lineage_id=lineage,age_steps=age,
                        sigma_lookup=sigma_lut,simulation_steps=sim_steps)
    manifest={
      "format":"gaden_filament_lineage_v2",
      "source":str(args.filament_npz),
      "sim_dt_s":args.sim_dt,"emission_rate_hz":args.emission_rate,
      "emission_rule":"float32 releaseAccumulator",
      "initial_sigma":args.initial_sigma,"growth_gamma":args.growth_gamma,
      "sigma_tolerance":args.sigma_tol,
      "max_sigma_age_error":float(np.max(age_err,initial=0.0)),
      "snapshots":int(len(sim_steps)),
      "filaments_total":int(len(fil)),
      "duplicate_lineage_snapshots":int(duplicate_snapshots),
      "invalid_birth_assignments":int(invalid_births),
      "progression_errors":int(progression_errors),
      "adjacent_shared_lineage_min":int(min(shared_counts)) if shared_counts else 0,
      "adjacent_shared_lineage_median":float(np.median(shared_counts)) if shared_counts else 0.0,
      "generator_contract_note":"variable_rate and filament_stop_steps are ignored by the frozen ROS2 wrapper; RunningSimulation receives constant numFilaments_sec=7",
      "decision":"LINEAGE_RECONSTRUCTION_PASS"
    }
    args.output_npz.with_suffix(".json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps(manifest,indent=2))


if __name__=="__main__":
    main()

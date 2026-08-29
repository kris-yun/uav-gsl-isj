#!/usr/bin/env python3
"""Historical H01/H02/H03 held-out-House PF-SNRE evaluator.

Primary point estimator for BOTH Classic PMFS and PF-SNRE is the frozen native
PMFS ExpectedValue(sourceProbability,0.05) semantics: highest-probability 5% of
free grid cells, then probability-weighted coordinate mean. The formal final
closed-loop evaluator remains native C++; this script is the deterministic
reference mirror for offline qualification.

No training or checkpoint selection occurs here. Historical truth is read only
by this evaluation program.
"""
from __future__ import annotations
import argparse, csv, json, time
from pathlib import Path
import numpy as np
import torch

import materialize_v4_truthblind_contexts as m4
from pf_snre_final_core import HouseDataset, ConditionedMomentSetDirectNRE, direct_posterior, sha256
from evaluate_pf_snre_reserved_sweep import score_candidates
from pf_snre_spatial_eval import load_carrier_cells, expand_region_mass_to_cells, spatial_energy_score, precompute_distance_matrix
from pf_snre_pmfs_metric import localization_error_top_fraction

HOUSE_LONG={"H01":"House01","H02":"House02","H03":"House03"}


def _truth(path: Path, house: str):
    out={}
    with path.open(newline="",encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["house"] in (house,HOUSE_LONG[house]):
                seed=int(r["seed"])
                xy=np.asarray([float(r["x"]),float(r["y"])],dtype=np.float64)
                if seed in out: raise ValueError(f"duplicate truth {house} seed{seed}")
                out[seed]=xy
    if set(out)!=set(range(10)): raise ValueError(f"{house}: truth CSV must contain seeds0..9 exactly")
    return out


def _observed_blocks(path: Path, house: str):
    out={s:[] for s in range(10)}
    with path.open(newline="",encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["house"] not in (house,HOUSE_LONG[house]): continue
            seed=int(r["seed"])
            if seed not in out: continue
            idx=np.asarray([int(v) for v in r["sample_row_indices"].split(";")],dtype=np.int64)
            y=np.asarray([float(v) for v in r["measured_ppm"].split(";")],dtype=np.float32)
            if idx.shape!=(10,) or y.shape!=(10,): raise ValueError("observed block must have 10 indices/measurements")
            out[seed].append((int(r["block_id"]),idx,y))
    for s,rows in out.items():
        rows.sort(key=lambda z:z[0])
        if [r[0] for r in rows]!=list(range(1,len(rows)+1)): raise ValueError(f"{house} seed{s}: incomplete observed blocks")
    return out


def _load_native_posterior(runtime_root: Path, update: int, cells: np.ndarray):
    name=f"native_shadow_source_posterior_update_{update:04d}.csv"
    matches=list(runtime_root.rglob(name))
    if len(matches)!=1:
        raise ValueError(f"expected exactly one {name} under {runtime_root}, found {len(matches)}")
    rows=[]
    with matches[0].open(newline="",encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            rows.append((float(r["x"]),float(r["y"]),float(r["source_probability"])))
    if len(rows)!=len(cells): raise ValueError("native PMFS free-cell count mismatch")
    pos=np.asarray([[r[0],r[1]] for r in rows],dtype=np.float64)
    prob=np.asarray([r[2] for r in rows],dtype=np.float64)
    if np.any(prob<0) or not np.all(np.isfinite(prob)) or prob.sum()<=0: raise ValueError("invalid native PMFS posterior")
    # Reorder native CSV to exact final carrier/free-cell order by coordinate.
    mapped=np.empty(len(cells),dtype=np.float64); used=set()
    for i,xy in enumerate(cells):
        d=np.linalg.norm(pos-xy[None,:],axis=1); k=int(np.argmin(d))
        if d[k]>1e-8 or k in used: raise ValueError("native PMFS/free-cell coordinate mismatch")
        mapped[i]=prob[k]; used.add(k)
    mapped/=mapped.sum()
    return mapped, matches[0]


def _model(path: Path, house: str):
    ck=torch.load(path,map_location="cpu",weights_only=False)
    if ck.get("heldout_house")!=house or ck.get("seed")!=3301 or ck.get("architecture")!="conditioned_moment_set_direct_nre_v2_exact_topology":
        raise ValueError("checkpoint is not primary seed3301 frozen LOHO model")
    m=ConditionedMomentSetDirectNRE(int(ck["candidate_dim"]),int(ck["block_context_dim"]),int(ck["hidden"]))
    m.load_state_dict(ck["model_state"]); m.eval(); return m,ck


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--house",choices=("H01","H02","H03"),required=True)
    ap.add_argument("--measured",type=Path,required=True)
    ap.add_argument("--carriers",type=Path,required=True)
    ap.add_argument("--blocks",type=Path,required=True)
    ap.add_argument("--archive-root",type=Path,required=True)
    ap.add_argument("--observed-block-manifest",type=Path,required=True)
    ap.add_argument("--truth-csv",type=Path,required=True)
    ap.add_argument("--checkpoint",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args(); args.out.mkdir(parents=True,exist_ok=True); started=time.monotonic()
    data=HouseDataset.load(args.house,args.measured,args.carriers,args.blocks)
    model,ck=_model(args.checkpoint,args.house)
    truth=_truth(args.truth_csv,args.house); observed=_observed_blocks(args.observed_block_manifest,args.house)
    ids,_,q0,cells,ptr=load_carrier_cells(args.carriers); q0cell=expand_region_mass_to_cells(q0,ptr); dmat=precompute_distance_matrix(cells)
    cell_ids=np.asarray([f"{x:.12g},{y:.12g}" for x,y in cells])
    rows=[]; native_files=[]
    for seed in range(10):
        run=m4._discover_run(args.archive_root,HOUSE_LONG[args.house],seed)
        for update in range(1,6):
            visible=data.blocks.visible(seed,update)
            if len(observed[seed])<visible: raise ValueError(f"{args.house} seed{seed}: observed blocks shorter than canonical prefix")
            # Assert canonical block IDs are exactly the observed row indices used to form D.
            oi=np.stack([r[1] for r in observed[seed][:visible]])
            ci=data.blocks.sample_indices[seed,:visible]
            if not np.array_equal(oi,ci): raise ValueError(f"{args.house} seed{seed}: canonical/observed block index mismatch")
            y=np.stack([r[2] for r in observed[seed][:visible]])
            # score_candidates expects a full timeline and selects canonical idx.
            full=np.zeros(data.measured.shape[-1],dtype=np.float32)
            flat_i=ci.reshape(-1); flat_y=y.reshape(-1)
            full[flat_i]=flat_y
            logits=score_candidates(model,data,full,seed,visible)
            post=direct_posterior(q0,logits); cellp=expand_region_mass_to_cells(post,ptr)
            native,native_path=_load_native_posterior(run.runtime_root,update,cells); native_files.append(str(native_path))
            pf_err,pf_meta=localization_error_top_fraction(cellp,cells,truth[seed],0.05,cell_ids)
            pmfs_err,pmfs_meta=localization_error_top_fraction(native,cells,truth[seed],0.05,cell_ids)
            q0_err,_=localization_error_top_fraction(q0cell,cells,truth[seed],0.05,cell_ids)
            rows.append({
                "house":args.house,"seed":seed,"source_update":update,"visible_blocks":visible,
                "pf_expectedvalue05_error_m":pf_err,"pmfs_expectedvalue05_error_m":pmfs_err,"q0_expectedvalue05_error_m":q0_err,
                "pf_spatial_energy_score":spatial_energy_score(cellp,cells,truth[seed],dmat),
                "pmfs_spatial_energy_score":spatial_energy_score(native,cells,truth[seed],dmat),
                "pf_max_carrier_mass":float(post.max()),"pf_max_cell_mass":float(cellp.max()),
                "pf_top05_selected_cells":pf_meta["selected_cells"],"pmfs_top05_selected_cells":pmfs_meta["selected_cells"],
            })
    def mean(k): return float(np.mean([r[k] for r in rows]))
    by_seed={str(s):{
        "pf":float(np.mean([r["pf_expectedvalue05_error_m"] for r in rows if r["seed"]==s])),
        "pmfs":float(np.mean([r["pmfs_expectedvalue05_error_m"] for r in rows if r["seed"]==s]))}
        for s in range(10)}
    summary={
        "contract":"PF_SNRE_HISTORICAL_LOHO_V1","house":args.house,"cases":len(rows),
        "primary_metric":"native_PMFS_ExpectedValue_sourceProbability_0.05_top_cell_fraction",
        "mean_pf_error_m":mean("pf_expectedvalue05_error_m"),"mean_pmfs_error_m":mean("pmfs_expectedvalue05_error_m"),
        "relative_improvement_vs_pmfs":(mean("pmfs_expectedvalue05_error_m")-mean("pf_expectedvalue05_error_m"))/mean("pmfs_expectedvalue05_error_m"),
        "paired_cases_improved":int(sum(r["pf_expectedvalue05_error_m"]<r["pmfs_expectedvalue05_error_m"] for r in rows)),
        "by_seed":by_seed,"checkpoint_sha256":sha256(args.checkpoint),"checkpoint_step":int(ck["step"]),
        "native_posterior_files":native_files,"wall_time_s":time.monotonic()-started,
    }
    with (args.out/"historical_cases.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    (args.out/"historical_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("PF_SNRE_HISTORICAL_LOHO_COMPLETE "+json.dumps(summary,sort_keys=True))

if __name__=="__main__": main()

#!/usr/bin/env python3
"""Simulation-based calibration panel for frozen held-out-House PF-SNRE.

Sources are a deterministic 64-point systematic q0 panel, nuisance members are
all four frozen reserved members, trajectories are the same two SHA-selected
held-out schedules, and all five source-update prefixes are scored. No
historical localization outcome is used.
"""
from __future__ import annotations
import argparse,csv,json,time
from pathlib import Path
import numpy as np
import torch

from pf_snre_final_core import HouseDataset,ConditionedMomentSetDirectNRE,direct_posterior,sha256
from evaluate_pf_snre_reserved_sweep import score_candidates
from pf_snre_spatial_eval import (load_carrier_cells,expand_region_mass_to_cells,hpd_cell_mask,
    systematic_q0_sources,mass_within_radius)


def _model(path:Path,house:str):
    ck=torch.load(path,map_location="cpu",weights_only=False)
    if ck.get("heldout_house")!=house or ck.get("seed")!=3301 or ck.get("architecture")!="conditioned_moment_set_direct_nre_v2_exact_topology":
        raise ValueError("not primary seed3301 LOHO checkpoint")
    m=ConditionedMomentSetDirectNRE(int(ck["candidate_dim"]),int(ck["block_context_dim"]),int(ck["hidden"]))
    m.load_state_dict(ck["model_state"]);m.eval();return m


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--house",choices=("H01","H02","H03"),required=True)
    ap.add_argument("--carriers",type=Path,required=True);ap.add_argument("--measured-train8",type=Path,required=True)
    ap.add_argument("--measured-reserved4",type=Path,required=True);ap.add_argument("--reserved-source-xy",type=Path,required=True)
    ap.add_argument("--blocks",type=Path,required=True);ap.add_argument("--checkpoint",type=Path,required=True);ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True);started=time.monotonic()
    data=HouseDataset.load(a.house,a.measured_train8,a.carriers,a.blocks);obs=np.load(a.measured_reserved4,mmap_mode="r");truth=np.load(a.reserved_source_xy,mmap_mode="r")
    if obs.shape!=(data.source_count,4,data.trajectory_count,data.measured.shape[-1]) or truth.shape!=(data.source_count,4,data.trajectory_count,2):raise ValueError("reserved calibration array shape mismatch")
    model=_model(a.checkpoint,a.house);ids,_,q0,cells,ptr=load_carrier_cells(a.carriers);sources=systematic_q0_sources(q0,ids,64)
    order=np.argsort(data.blocks.trajectory_sha.astype(str),kind="stable");trajectories=np.asarray([order[0],order[-1]],dtype=np.int64)
    for t in trajectories:
        if np.count_nonzero(data.blocks.update_visible_blocks[t])!=5:raise ValueError("calibration requires exactly five canonical updates")
    rows=[]
    for source in sources:
      for member in range(4):
       for trajectory in trajectories:
        y=np.asarray(obs[source,member,trajectory],dtype=np.float32)
        for update in range(1,6):
            visible=data.blocks.visible(int(trajectory),update);logits=score_candidates(model,data,y,int(trajectory),visible);post=direct_posterior(q0,logits);cellp=expand_region_mass_to_cells(post,ptr)
            true=np.asarray(truth[source,member,trajectory],dtype=np.float64);source_cells=cells[ptr[source]:ptr[source+1]];hit=np.flatnonzero(np.linalg.norm(source_cells-true[None,:],axis=1)<=1e-8)
            if len(hit)!=1:raise ValueError("calibration truth not exact free-cell center")
            true_cell=ptr[source]+int(hit[0]);h50=hpd_cell_mask(cellp,.5);h90=hpd_cell_mask(cellp,.9)
            idx=data.blocks.sample_indices[int(trajectory),:visible];block_mean=np.mean(y[idx],axis=1);hit_blocks=int(np.sum(block_mean>0.1));info="NO_HIT" if hit_blocks==0 else "AT_LEAST_ONE_HIT"
            # Density/evidence rank is independent of q0 area; posterior rank is secondary.
            ordlog=np.lexsort((ids.astype(str),-logits));rank=int(np.flatnonzero(ordlog==int(source))[0])+1
            rows.append({"house":a.house,"source_id":str(ids[source]),"reserved_member":member,"trajectory_sha":str(data.blocks.trajectory_sha[trajectory]),"update":update,"visible_blocks":visible,
                "hit_blocks":hit_blocks,"hit_fraction":hit_blocks/visible,"information_regime":info,"hpd50_contains_truth":bool(h50[true_cell]),"hpd90_contains_truth":bool(h90[true_cell]),
                "false_confident":bool((not h90[true_cell]) and float(post.max())>=0.5),"max_carrier_mass":float(post.max()),"max_cell_mass":float(cellp.max()),
                "mass_1m":mass_within_radius(cellp,cells,true,1.0),"mass_2m":mass_within_radius(cellp,cells,true,2.0),"density_rank":rank,"normalized_density_rank":(rank-1)/(len(ids)-1)})
    def summarize(rr):
        return {"cases":len(rr),"coverage50":float(np.mean([r["hpd50_contains_truth"] for r in rr])),"coverage90":float(np.mean([r["hpd90_contains_truth"] for r in rr])),
            "false_confident_count":int(sum(r["false_confident"] for r in rr)),"false_confident_fraction":float(np.mean([r["false_confident"] for r in rr])),
            "mean_max_carrier_mass":float(np.mean([r["max_carrier_mass"] for r in rr])),"median_normalized_density_rank":float(np.median([r["normalized_density_rank"] for r in rr]))}
    by_update={str(u):summarize([r for r in rows if r["update"]==u]) for u in range(1,6)}
    by_info={k:summarize([r for r in rows if r["information_regime"]==k]) for k in ("NO_HIT","AT_LEAST_ONE_HIT") if any(r["information_regime"]==k for r in rows)}
    hist=np.histogram([r["normalized_density_rank"] for r in rows],bins=np.linspace(0,1,11))[0].tolist()
    summary={"contract":"PF_SNRE_Q0_CALIBRATION_V1","house":a.house,"sources":64,"reserved_members":4,"trajectories":2,"updates":5,
        "source_selection":"deterministic_systematic_q0","overall":summarize(rows),"by_update":by_update,"by_information_regime":by_info,
        "normalized_density_rank_histogram_10_bins":hist,"pmfs_false_confidence_comparator":"NOT_DEFINED_FOR_SYNTHETIC_RESERVED_PANEL",
        "checkpoint_sha256":sha256(a.checkpoint),"wall_time_s":time.monotonic()-started}
    with (a.out/"calibration_cases.csv").open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (a.out/"calibration_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("PF_SNRE_Q0_CALIBRATION_COMPLETE "+json.dumps(summary,sort_keys=True))
if __name__=="__main__":main()

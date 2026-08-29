#!/usr/bin/env python3
"""Final PF-SNRE held-out-House 32-source qualification sweep.

Adds the two missing preregistered controls to the original evaluator:
1) the already-frozen nonlearned physical-concentration energy-score selector;
2) 199 deterministic source-label permutations with a paired aggregate-rank test.

The nonlearned comparator is NOT converted into a pseudo-posterior and has no
new temperature. Its point estimate is the exact free-cell mean (carrier
centroid) of the source selected by the frozen energy score.
"""
from __future__ import annotations
import argparse,csv,json,time
from pathlib import Path
import numpy as np
import torch

from pf_snre_final_core import HouseDataset,ConditionedMomentSetDirectNRE,direct_posterior,sha256
from evaluate_pf_snre_reserved_sweep import score_candidates
from pf_snre_spatial_eval import (load_carrier_cells,expand_region_mass_to_cells,posterior_mean_xy,
    spatial_energy_score,hpd_cell_mask,mass_within_radius,density_rank,deterministic_kcenter,precompute_distance_matrix)
from pf_dei_runlevel_energy_reference import source_energy_scores
from materialize_pf_snre_final_dataset import TRAIN_SEEDS,RESERVED_SEEDS

DELAY_STEPS=2
PERMUTATIONS=199
PERMUTATION_SEED=2026082901


def _resolve(base:Path,v:str)->Path:
    p=Path(v); return p if p.is_absolute() else (base/p).resolve()


def _bank_for_trajectory(manifest:Path,house:str,trajectory:int):
    spec=json.loads(manifest.read_text(encoding="utf-8"))
    if spec.get("contract")!="PF_SNRE_MATERIALIZATION_INPUT_V1": raise ValueError("wrong materialization input contract")
    hs=spec["houses"][house]; rows={int(r["trajectory_index"]):r for r in hs["banks"]}
    if set(rows)!=set(range(30)): raise ValueError("physical bank manifest does not cover trajectories0..29")
    return _resolve(manifest.parent,rows[trajectory]["path"])


def _physical_visible(bank:Path,source:int,reserved_member:int,sample_indices):
    with np.load(bank,allow_pickle=False) as d:
        seeds=np.asarray(d["transport_seed"],dtype=np.int64); index={int(v):i for i,v in enumerate(seeds.tolist())}
        if not set(TRAIN_SEEDS+RESERVED_SEEDS).issubset(index): raise ValueError("bank lacks frozen transport members")
        x=np.asarray(d["candidate_physical_ppm"],dtype=np.float64)
        train=np.asarray([index[s] for s in TRAIN_SEEDS]); r=index[RESERVED_SEEDS[reserved_member]]
        flat=np.asarray(sample_indices,dtype=np.int64).reshape(-1)
        pred=np.zeros((x.shape[0],len(train),len(flat)),dtype=np.float64)
        obs=np.zeros(len(flat),dtype=np.float64)
        valid=flat>=DELAY_STEPS
        causal=flat[valid]-DELAY_STEPS
        pred[:,:,valid]=x[:,train][:,:,causal]
        obs[valid]=x[source,r,causal]
    return obs,pred


def _model(path:Path,house:str):
    ck=torch.load(path,map_location="cpu",weights_only=False)
    if ck.get("heldout_house")!=house or ck.get("seed")!=3301 or ck.get("architecture")!="conditioned_moment_set_direct_nre_v2_exact_topology":
        raise ValueError("not primary seed3301 LOHO checkpoint")
    m=ConditionedMomentSetDirectNRE(int(ck["candidate_dim"]),int(ck["block_context_dim"]),int(ck["hidden"]))
    m.load_state_dict(ck["model_state"]); m.eval(); return m


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--house",choices=("H01","H02","H03"),required=True)
    ap.add_argument("--carriers",type=Path,required=True); ap.add_argument("--measured-train8",type=Path,required=True)
    ap.add_argument("--measured-reserved4",type=Path,required=True); ap.add_argument("--reserved-source-xy",type=Path,required=True)
    ap.add_argument("--blocks",type=Path,required=True); ap.add_argument("--physical-bank-manifest",type=Path,required=True)
    ap.add_argument("--checkpoint",type=Path,required=True); ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=True); started=time.monotonic()
    data=HouseDataset.load(a.house,a.measured_train8,a.carriers,a.blocks); obs=np.load(a.measured_reserved4,mmap_mode="r"); truth=np.load(a.reserved_source_xy,mmap_mode="r")
    if obs.shape!=(data.source_count,4,data.trajectory_count,data.measured.shape[-1]): raise ValueError("reserved measured shape mismatch")
    if truth.shape!=(data.source_count,4,data.trajectory_count,2): raise ValueError("reserved truth shape mismatch")
    model=_model(a.checkpoint,a.house)
    ids,centroids,q0,cells,ptr=load_carrier_cells(a.carriers); selected=deterministic_kcenter(centroids,ids,32)
    order=np.argsort(data.blocks.trajectory_sha.astype(str),kind="stable"); trajectories=np.asarray([order[0],order[-1]],dtype=np.int64)
    for t in trajectories:
        if np.count_nonzero(data.blocks.update_visible_blocks[t])!=5: raise ValueError("reserved qualification requires exactly five canonical updates")
    id_order=np.argsort(ids,kind="stable"); physics_perm=np.empty(len(ids),dtype=np.int64); physics_perm[id_order]=np.roll(id_order,1)
    if np.any(physics_perm==np.arange(len(ids))): raise RuntimeError("physics derangement has fixed point")
    rng=np.random.default_rng(PERMUTATION_SEED); perms=np.stack([rng.permutation(len(ids)) for _ in range(PERMUTATIONS)])
    dmat=precompute_distance_matrix(cells); q0cell=expand_region_mass_to_cells(q0,ptr); q0point=posterior_mean_xy(q0cell,cells)
    null_rank_sum=np.zeros(PERMUTATIONS,dtype=np.float64); observed_rank_sum=0.0; rank_cases=0; rows=[]
    bank_cache={int(t):_bank_for_trajectory(a.physical_bank_manifest,a.house,int(t)) for t in trajectories}
    for source in selected:
      for member in range(4):
       for trajectory in trajectories:
        bank=bank_cache[int(trajectory)]
        for update in range(1,6):
            visible=data.blocks.visible(int(trajectory),update); y=np.asarray(obs[source,member,trajectory],dtype=np.float32)
            logits=score_candidates(model,data,y,int(trajectory),visible); post=direct_posterior(q0,logits); cellp=expand_region_mass_to_cells(post,ptr)
            no_logits=score_candidates(model,data,y,int(trajectory),visible,physics_source_map=physics_perm); no=direct_posterior(q0,no_logits); nocell=expand_region_mass_to_cells(no,ptr)
            true=np.asarray(truth[source,member,trajectory],dtype=np.float64); point=posterior_mean_xy(cellp,cells); nopoint=posterior_mean_xy(nocell,cells)
            h90=hpd_cell_mask(cellp,.9); source_cells=cells[ptr[source]:ptr[source+1]]; hit=np.flatnonzero(np.linalg.norm(source_cells-true[None,:],axis=1)<=1e-8)
            if len(hit)!=1: raise ValueError("reserved generating XY is not exact carrier free cell")
            true_cell=ptr[source]+int(hit[0])
            # Frozen physical comparator on the causal physical inputs that generated M[k].
            phys_obs,phys_pred=_physical_visible(bank,int(source),member,data.blocks.sample_indices[int(trajectory),:visible])
            es=source_energy_scores(phys_obs,phys_pred); comp_source=int(np.lexsort((ids.astype(str),es))[0]); comp_point=centroids[comp_source]
            order_log=np.lexsort((ids.astype(str),-logits)); inv=np.empty(len(ids),dtype=np.int64); inv[order_log]=np.arange(1,len(ids)+1)
            nr=(float(inv[source])-1.0)/(len(ids)-1.0); observed_rank_sum+=nr
            null_rank_sum+=(inv[perms[:,source]].astype(np.float64)-1.0)/(len(ids)-1.0); rank_cases+=1
            rows.append({"house":a.house,"source_id":str(ids[source]),"reserved_member":member,"trajectory_sha":str(data.blocks.trajectory_sha[trajectory]),
                "update":update,"visible_blocks":visible,"pf_error_m":float(np.linalg.norm(point-true)),"q0_error_m":float(np.linalg.norm(q0point-true)),
                "nonlearned_physics_error_m":float(np.linalg.norm(comp_point-true)),"nonlearned_selected_source_id":str(ids[comp_source]),
                "no_physics_error_m":float(np.linalg.norm(nopoint-true)),"pf_energy_score":spatial_energy_score(cellp,cells,true,dmat),
                "q0_energy_score":spatial_energy_score(q0cell,cells,true,dmat),"mass_1m":mass_within_radius(cellp,cells,true,1.0),"mass_2m":mass_within_radius(cellp,cells,true,2.0),
                "density_rank":int(inv[source]),"normalized_density_rank":nr,"posterior_carrier_rank":density_rank(np.log(post),int(source),ids),
                "hpd90_contains_truth":bool(h90[true_cell]),"max_carrier_mass":float(post.max()),"max_cell_mass":float(cellp.max())})
    def mean(k):return float(np.mean([r[k] for r in rows]))
    obs_stat=observed_rank_sum/rank_cases; null_stats=null_rank_sum/rank_cases
    p=(1+int(np.sum(null_stats<=obs_stat)))/(PERMUTATIONS+1)
    summary={"contract":"PF_SNRE_RESERVED_SOURCE_SWEEP_V2","house":a.house,"cases":len(rows),"sources":32,"reserved_members":4,"trajectories":2,"updates":5,
        "selected_source_ids":[str(ids[i]) for i in selected],"trajectory_sha":[str(data.blocks.trajectory_sha[i]) for i in trajectories],
        "mean_pf_error_m":mean("pf_error_m"),"mean_q0_error_m":mean("q0_error_m"),"mean_nonlearned_physics_error_m":mean("nonlearned_physics_error_m"),"mean_no_physics_error_m":mean("no_physics_error_m"),
        "relative_improvement_vs_q0":(mean("q0_error_m")-mean("pf_error_m"))/mean("q0_error_m"),
        "relative_improvement_vs_nonlearned":(mean("nonlearned_physics_error_m")-mean("pf_error_m"))/mean("nonlearned_physics_error_m"),
        "relative_improvement_no_physics_vs_q0":(mean("q0_error_m")-mean("no_physics_error_m"))/mean("q0_error_m"),
        "median_normalized_density_rank":float(np.median([r["normalized_density_rank"] for r in rows])),"mean_normalized_density_rank":obs_stat,
        "source_label_permutation_test":{"permutations":PERMUTATIONS,"seed":PERMUTATION_SEED,"statistic":"mean_normalized_density_rank_lower_better","observed":obs_stat,"null_mean":float(null_stats.mean()),"p_one_sided":p},
        "hpd90_coverage":float(np.mean([r["hpd90_contains_truth"] for r in rows])),"checkpoint_sha256":sha256(a.checkpoint),"wall_time_s":time.monotonic()-started}
    with (a.out/"source_sweep_cases.csv").open("w",newline="",encoding="utf-8") as f: w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (a.out/"source_sweep_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("PF_SNRE_RESERVED_SOURCE_SWEEP_V2_COMPLETE "+json.dumps(summary,sort_keys=True))
if __name__=="__main__":main()

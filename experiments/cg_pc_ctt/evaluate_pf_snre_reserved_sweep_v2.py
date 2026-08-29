#!/usr/bin/env python3
"""Final PF-SNRE held-out-House 32-source qualification sweep.

Controls are frozen before scoring:
1) the existing nonlearned physical-concentration energy-score selector;
2) 199 deterministic source-label permutations;
3) a deterministic source->physics derangement leakage diagnostic.

The nonlearned comparator is never converted to a posterior and receives no
new temperature. Its point estimate is the free-cell mean of its selected
carrier. Physical comparator arrays are cached/vectorized so qualification does
not repeatedly decompress multi-megabyte NPZ banks.
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
from materialize_pf_snre_final_dataset import TRAIN_SEEDS,RESERVED_SEEDS

DELAY_STEPS=2
PERMUTATIONS=199
PERMUTATION_SEED=2026082901


def _resolve(base:Path,v:str)->Path:
    p=Path(v); return p if p.is_absolute() else (base/p).resolve()

def _bank_for_trajectory(manifest:Path,house:str,trajectory:int):
    spec=json.loads(manifest.read_text(encoding="utf-8"))
    if spec.get("contract")!="PF_SNRE_MATERIALIZATION_INPUT_V1": raise ValueError("wrong materialization input contract")
    rows={int(r["trajectory_index"]):r for r in spec["houses"][house]["banks"]}
    if set(rows)!=set(range(30)): raise ValueError("physical bank manifest does not cover trajectories0..29")
    return _resolve(manifest.parent,rows[trajectory]["path"])

class PhysicalComparatorCache:
    """Exact equal-weight frozen energy score, vectorized over sources/members."""
    def __init__(self, bank_paths:dict[int,Path]):
        self.full={};self.train_index={};self.reserved_index={};self.pred={}
        for trajectory,path in bank_paths.items():
            with np.load(path,allow_pickle=False) as d:
                seeds=np.asarray(d["transport_seed"],dtype=np.int64); index={int(v):i for i,v in enumerate(seeds.tolist())}
                if not set(TRAIN_SEEDS+RESERVED_SEEDS).issubset(index):raise ValueError("bank lacks frozen transport members")
                self.full[trajectory]=np.asarray(d["candidate_physical_ppm"],dtype=np.float64)
                self.train_index[trajectory]=np.asarray([index[s] for s in TRAIN_SEEDS],dtype=np.int64)
                self.reserved_index[trajectory]=np.asarray([index[s] for s in RESERVED_SEEDS],dtype=np.int64)
    def _prepared(self,trajectory:int,visible:int,sample_indices):
        key=(trajectory,visible)
        if key in self.pred:return self.pred[key]
        x=self.full[trajectory];flat=np.asarray(sample_indices,dtype=np.int64).reshape(-1);valid=flat>=DELAY_STEPS;causal=flat[valid]-DELAY_STEPS
        pred=np.zeros((x.shape[0],len(TRAIN_SEEDS),len(flat)),dtype=np.float64)
        pred[:,:,valid]=x[:,self.train_index[trajectory]][:,:,causal]
        L=float(len(flat));x2=np.sum(pred*pred,axis=2)/L
        gram=np.einsum("sml,snl->smn",pred,pred,optimize=True)/L
        dist2=np.maximum(x2[:,:,None]+x2[:,None,:]-2.0*gram,0.0)
        second=.5*np.sqrt(dist2).mean(axis=(1,2))
        pack=(pred,x2,second,flat,valid,causal);self.pred[key]=pack;return pack
    def scores(self,source:int,member:int,trajectory:int,visible:int,sample_indices):
        pred,x2,second,flat,valid,causal=self._prepared(trajectory,visible,sample_indices)
        x=self.full[trajectory];y=np.zeros(len(flat),dtype=np.float64);y[valid]=x[source,self.reserved_index[trajectory][member],causal]
        L=float(len(y));y2=float(np.dot(y,y)/L);cross=np.einsum("sml,l->sm",pred,y,optimize=True)/L
        first=np.sqrt(np.maximum(x2+y2-2.0*cross,0.0)).mean(axis=1)
        return first-second

def _model(path:Path,house:str):
    ck=torch.load(path,map_location="cpu",weights_only=False)
    if ck.get("heldout_house")!=house or ck.get("seed")!=3301 or ck.get("architecture")!="conditioned_moment_set_direct_nre_v2_exact_topology":raise ValueError("not primary seed3301 LOHO checkpoint")
    m=ConditionedMomentSetDirectNRE(int(ck["candidate_dim"]),int(ck["block_context_dim"]),int(ck["hidden"]));m.load_state_dict(ck["model_state"]);m.eval();return m

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--house",choices=("H01","H02","H03"),required=True);ap.add_argument("--carriers",type=Path,required=True);ap.add_argument("--measured-train8",type=Path,required=True);ap.add_argument("--measured-reserved4",type=Path,required=True);ap.add_argument("--reserved-source-xy",type=Path,required=True);ap.add_argument("--blocks",type=Path,required=True);ap.add_argument("--physical-bank-manifest",type=Path,required=True);ap.add_argument("--checkpoint",type=Path,required=True);ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True);started=time.monotonic();data=HouseDataset.load(a.house,a.measured_train8,a.carriers,a.blocks);obs=np.load(a.measured_reserved4,mmap_mode="r");truth=np.load(a.reserved_source_xy,mmap_mode="r")
    if obs.shape!=(data.source_count,4,data.trajectory_count,data.measured.shape[-1]) or truth.shape!=(data.source_count,4,data.trajectory_count,2):raise ValueError("reserved qualification array shape mismatch")
    model=_model(a.checkpoint,a.house);ids,centroids,q0,cells,ptr=load_carrier_cells(a.carriers);selected=deterministic_kcenter(centroids,ids,32);order=np.argsort(data.blocks.trajectory_sha.astype(str),kind="stable");trajectories=np.asarray([order[0],order[-1]],dtype=np.int64)
    for t in trajectories:
        if np.count_nonzero(data.blocks.update_visible_blocks[t])!=5:raise ValueError("reserved qualification requires exactly five canonical updates")
    id_order=np.argsort(ids,kind="stable");physics_perm=np.empty(len(ids),dtype=np.int64);physics_perm[id_order]=np.roll(id_order,1)
    if np.any(physics_perm==np.arange(len(ids))):raise RuntimeError("physics derangement has fixed point")
    rng=np.random.default_rng(PERMUTATION_SEED);perms=np.stack([rng.permutation(len(ids)) for _ in range(PERMUTATIONS)])
    dmat=precompute_distance_matrix(cells);q0cell=expand_region_mass_to_cells(q0,ptr);q0point=posterior_mean_xy(q0cell,cells);null_rank_sum=np.zeros(PERMUTATIONS);observed_rank_sum=0.;rank_cases=0;rows=[]
    bank_paths={int(t):_bank_for_trajectory(a.physical_bank_manifest,a.house,int(t)) for t in trajectories};comparator=PhysicalComparatorCache(bank_paths)
    for source in selected:
      for member in range(4):
       for trajectory in trajectories:
        for update in range(1,6):
            visible=data.blocks.visible(int(trajectory),update);y=np.asarray(obs[source,member,trajectory],dtype=np.float32);logits=score_candidates(model,data,y,int(trajectory),visible);post=direct_posterior(q0,logits);cellp=expand_region_mass_to_cells(post,ptr)
            no_logits=score_candidates(model,data,y,int(trajectory),visible,physics_source_map=physics_perm);no=direct_posterior(q0,no_logits);nocell=expand_region_mass_to_cells(no,ptr);true=np.asarray(truth[source,member,trajectory],dtype=np.float64);point=posterior_mean_xy(cellp,cells);nopoint=posterior_mean_xy(nocell,cells);h90=hpd_cell_mask(cellp,.9)
            source_cells=cells[ptr[source]:ptr[source+1]];hit=np.flatnonzero(np.linalg.norm(source_cells-true[None,:],axis=1)<=1e-8)
            if len(hit)!=1:raise ValueError("reserved generating XY is not exact carrier free cell")
            true_cell=ptr[source]+int(hit[0]);es=comparator.scores(int(source),member,int(trajectory),visible,data.blocks.sample_indices[int(trajectory),:visible]);comp_source=int(np.lexsort((ids.astype(str),es))[0]);comp_point=centroids[comp_source]
            order_log=np.lexsort((ids.astype(str),-logits));inv=np.empty(len(ids),dtype=np.int64);inv[order_log]=np.arange(1,len(ids)+1);nr=(float(inv[source])-1.)/(len(ids)-1.);observed_rank_sum+=nr;null_rank_sum+=(inv[perms[:,source]].astype(float)-1.)/(len(ids)-1.);rank_cases+=1
            rows.append({"house":a.house,"source_id":str(ids[source]),"reserved_member":member,"trajectory_sha":str(data.blocks.trajectory_sha[trajectory]),"update":update,"visible_blocks":visible,"pf_error_m":float(np.linalg.norm(point-true)),"q0_error_m":float(np.linalg.norm(q0point-true)),"nonlearned_physics_error_m":float(np.linalg.norm(comp_point-true)),"nonlearned_selected_source_id":str(ids[comp_source]),"no_physics_error_m":float(np.linalg.norm(nopoint-true)),"pf_energy_score":spatial_energy_score(cellp,cells,true,dmat),"q0_energy_score":spatial_energy_score(q0cell,cells,true,dmat),"mass_1m":mass_within_radius(cellp,cells,true,1.),"mass_2m":mass_within_radius(cellp,cells,true,2.),"density_rank":int(inv[source]),"normalized_density_rank":nr,"posterior_carrier_rank":density_rank(np.log(post),int(source),ids),"hpd90_contains_truth":bool(h90[true_cell]),"max_carrier_mass":float(post.max()),"max_cell_mass":float(cellp.max())})
    def mean(k):return float(np.mean([r[k] for r in rows]))
    obs_stat=observed_rank_sum/rank_cases;null_stats=null_rank_sum/rank_cases;p=(1+int(np.sum(null_stats<=obs_stat)))/(PERMUTATIONS+1)
    summary={"contract":"PF_SNRE_RESERVED_SOURCE_SWEEP_V2","house":a.house,"cases":len(rows),"sources":32,"reserved_members":4,"trajectories":2,"updates":5,"selected_source_ids":[str(ids[i]) for i in selected],"trajectory_sha":[str(data.blocks.trajectory_sha[i]) for i in trajectories],"mean_pf_error_m":mean("pf_error_m"),"mean_q0_error_m":mean("q0_error_m"),"mean_nonlearned_physics_error_m":mean("nonlearned_physics_error_m"),"mean_no_physics_error_m":mean("no_physics_error_m"),"relative_improvement_vs_q0":(mean("q0_error_m")-mean("pf_error_m"))/mean("q0_error_m"),"relative_improvement_vs_nonlearned":(mean("nonlearned_physics_error_m")-mean("pf_error_m"))/mean("nonlearned_physics_error_m"),"relative_improvement_no_physics_vs_q0":(mean("q0_error_m")-mean("no_physics_error_m"))/mean("q0_error_m"),"median_normalized_density_rank":float(np.median([r["normalized_density_rank"] for r in rows])),"mean_normalized_density_rank":obs_stat,"source_label_permutation_test":{"permutations":PERMUTATIONS,"seed":PERMUTATION_SEED,"statistic":"mean_normalized_density_rank_lower_better","observed":obs_stat,"null_mean":float(null_stats.mean()),"null_statistics":null_stats.tolist(),"p_one_sided":p},"hpd90_coverage":float(np.mean([r["hpd90_contains_truth"] for r in rows])),"nonlearned_comparator":"frozen_pf_dei_runlevel_equal_weight_physical_energy_score_on_causal_sensor_inputs","checkpoint_sha256":sha256(a.checkpoint),"wall_time_s":time.monotonic()-started}
    with (a.out/"source_sweep_cases.csv").open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (a.out/"source_sweep_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8");print("PF_SNRE_RESERVED_SOURCE_SWEEP_V2_COMPLETE "+json.dumps({k:v for k,v in summary.items() if k!="source_label_permutation_test"},sort_keys=True))
if __name__=="__main__":main()

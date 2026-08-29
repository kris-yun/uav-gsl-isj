#!/usr/bin/env python3
"""Train direct physics-conditioned Set-NRE v2 on frozen H01 bank.

Key correction versus residual v1:
- source proposal is fixed uniform over carriers and independent of observation;
- negative candidate is an independent uniform draw from the same proposal;
- no historical PMFS posterior is used by the model or sampler;
- historical H01 trajectories 0..9 are fully excluded from training;
- train trajectories 10..24, validation 25..29;
- strict leave-one-member-out prevents exact physical self-match.
"""
from __future__ import annotations
import argparse, csv, json, math, random, time
from pathlib import Path
import numpy as np
import torch
from torch.nn import functional as F
from pf_dei_direct_set_nre_v2 import (
    ConditionedDeepSetDirectNRE, block_context, build_block_layout,
    candidate_features, log_measurement, sha256,
)

SEED=3201
TRAIN_TRAJECTORIES=tuple(range(10,25))
VALIDATION_TRAJECTORIES=tuple(range(25,30))
HISTORICAL_HOLDOUT_TRAJECTORIES=tuple(range(10))
SOURCE_COUNT=210

class BatchFactory:
    def __init__(self, measured_path: Path, schedule_path: Path, carriers_path: Path):
        self.measured=np.load(measured_path,mmap_mode="r")
        schedule=np.load(schedule_path,allow_pickle=False)
        self.lengths=schedule["lengths"].astype(int)
        self.layouts=[build_block_layout(schedule["x"][i],schedule["y"][i],schedule["stop_start"][i],int(self.lengths[i])) for i in range(30)]
        self.carriers=json.loads(carriers_path.read_text(encoding="utf-8"))
        if self.measured.shape[:3]!=(SOURCE_COUNT,8,30) or len(self.carriers)!=SOURCE_COUNT:
            raise ValueError("training dataset identity mismatch")
        self.carrier_xy=np.asarray([[c["centroid_x"],c["centroid_y"]] for c in self.carriers],dtype=np.float64)
        self.xy_center=0.5*(self.carrier_xy.min(axis=0)+self.carrier_xy.max(axis=0))
        self.xy_scale=np.maximum(self.carrier_xy.max(axis=0)-self.carrier_xy.min(axis=0),1e-6)

    def sample_specs(self,pair_count:int,trajectories:tuple[int,...],rng:np.random.Generator):
        specs=[]
        for _ in range(pair_count):
            trajectory=int(trajectories[int(rng.integers(0,len(trajectories)))])
            layout=self.layouts[trajectory]
            update=int(layout.available_updates[int(rng.integers(0,len(layout.available_updates)))])
            source=int(rng.integers(0,SOURCE_COUNT))
            negative=int(rng.integers(0,SOURCE_COUNT))
            heldout=int(rng.integers(0,8))
            specs.append((trajectory,update,source,negative,heldout))
        return specs

    def make_batch(self,specs):
        max_blocks=max(self.layouts[t].visible_blocks(u) for t,u,*_ in specs)
        examples=2*len(specs)
        obs_out=np.zeros((examples,max_blocks,10),dtype=np.float32)
        pred_out=np.zeros((examples,max_blocks,7,10),dtype=np.float32)
        ctx_out=np.zeros((examples,max_blocks,6),dtype=np.float32)
        cand_out=np.zeros((examples,5),dtype=np.float32)
        block_mask=np.zeros((examples,max_blocks),dtype=np.bool_)
        member_mask=np.ones((examples,7),dtype=np.bool_)
        labels=np.zeros(examples,dtype=np.float32)
        for pair,(trajectory,update,source,negative,heldout) in enumerate(specs):
            layout=self.layouts[trajectory]; visible=layout.visible_blocks(update); indices=layout.sample_indices[:visible]
            observation=log_measurement(self.measured[source,heldout,trajectory][indices])
            members=np.asarray([m for m in range(8) if m!=heldout],dtype=np.int64)
            if heldout in members: raise RuntimeError("LOMO failure")
            for offset,(candidate,label) in enumerate(((source,1.0),(negative,0.0))):
                e=2*pair+offset
                pred=self.measured[candidate,members,trajectory][:,indices]
                pred=np.transpose(pred,(1,0,2))
                obs_out[e,:visible]=observation
                pred_out[e,:visible]=log_measurement(pred)
                ctx_out[e,:visible]=block_context(layout,visible,self.carriers[candidate],self.xy_center,self.xy_scale)
                cand_out[e]=candidate_features(self.carriers[candidate],self.xy_center,self.xy_scale)
                block_mask[e,:visible]=True; labels[e]=label
        return tuple(torch.from_numpy(x) for x in (obs_out,pred_out,ctx_out,cand_out,block_mask,member_mask,labels))

def evaluate_bce(model,factory,specs,device,chunk_pairs=16):
    model.eval(); loss_sum=0.0; count=0
    with torch.no_grad():
        for start in range(0,len(specs),chunk_pairs):
            batch=factory.make_batch(specs[start:start+chunk_pairs])
            obs,pred,ctx,cand,bmask,mmask,label=[x.to(device) for x in batch]
            logits=model(obs,pred,ctx,cand,bmask,mmask)
            loss_sum+=float(F.binary_cross_entropy_with_logits(logits,label,reduction="sum")); count+=int(label.numel())
    return loss_sum/count

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--dataset-root",type=Path,required=True); ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--steps",type=int,default=12000); ap.add_argument("--pairs-per-batch",type=int,default=8); ap.add_argument("--validation-pairs",type=int,default=256); ap.add_argument("--validation-every",type=int,default=250)
    args=ap.parse_args(); args.out.mkdir(parents=True,exist_ok=True)
    if not (1<=args.steps<=12000): raise ValueError("steps must be 1..12000")
    random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED); torch.use_deterministic_algorithms(True); torch.set_num_threads(min(4,max(1,torch.get_num_threads())))
    device=torch.device("cpu")
    factory=BatchFactory(args.dataset_root/"H01_measured_train.npy",args.dataset_root/"H01_schedule_train.npz",args.dataset_root/"H01_carriers.json")
    train_rng=np.random.default_rng(SEED); val_rng=np.random.default_rng(SEED+1)
    validation_specs=factory.sample_specs(args.validation_pairs,VALIDATION_TRAJECTORIES,val_rng)
    model=ConditionedDeepSetDirectNRE().to(device); opt=torch.optim.AdamW(model.parameters(),lr=3e-4,weight_decay=1e-4)
    best=math.inf; best_step=0; ckpt=args.out/"best_validation_bce_seed3201.pt"; rows=[]; started=time.monotonic(); source_counts=np.zeros(SOURCE_COUNT,dtype=np.int64)
    initial=evaluate_bce(model,factory,validation_specs,device); print(f"DIRECT_SET_NRE_INITIAL_VALIDATION_BCE={initial:.9f}",flush=True)
    for step in range(1,args.steps+1):
        specs=factory.sample_specs(args.pairs_per_batch,TRAIN_TRAJECTORIES,train_rng)
        for _,_,source,_,_ in specs: source_counts[source]+=1
        obs,pred,ctx,cand,bmask,mmask,label=[x.to(device) for x in factory.make_batch(specs)]
        opt.zero_grad(set_to_none=True); logits=model(obs,pred,ctx,cand,bmask,mmask); loss=F.binary_cross_entropy_with_logits(logits,label); loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(),5.0); opt.step()
        if step==1 or step%args.validation_every==0 or step==args.steps:
            vbce=evaluate_bce(model,factory,validation_specs,device); row={"step":step,"training_bce":float(loss.detach()),"validation_bce":vbce,"elapsed_s":time.monotonic()-started}; rows.append(row); print("DIRECT_SET_NRE_PROGRESS "+json.dumps(row,sort_keys=True),flush=True)
            if vbce<best:
                best=vbce; best_step=step
                torch.save({"model_state":model.state_dict(),"seed":SEED,"step":step,"validation_bce":vbce,"architecture":"candidate_conditioned_deep_set_direct_nre_v2","candidate_dim":5,"block_context_dim":6,"hidden":32},ckpt)
    with (args.out/"training_log.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    summary={
        "contract":"PF_DEI_DIRECT_SET_NRE_V2_TRAINING",
        "seed":SEED,"steps_completed":args.steps,"maximum_steps":12000,"pairs_per_batch":args.pairs_per_batch,
        "source_proposal":"uniform_over_210_carriers_independent_of_observation",
        "negative_proposal":"independent_uniform_over_210_carriers",
        "pmfs_posterior_used_by_model":False,"pmfs_posterior_used_by_sampler":False,
        "strict_leave_one_member_out":True,"historical_holdout_trajectories":list(HISTORICAL_HOLDOUT_TRAJECTORIES),
        "training_trajectories":list(TRAIN_TRAJECTORIES),"validation_trajectories":list(VALIDATION_TRAJECTORIES),
        "initial_validation_bce":initial,"best_validation_bce":best,"best_step":best_step,
        "positive_source_exposure_min":int(source_counts.min()),"positive_source_exposure_median":float(np.median(source_counts)),"positive_source_exposure_max":int(source_counts.max()),
        "checkpoint_selection":"minimum simulated validation BCE only","checkpoint_sha256":sha256(ckpt),"gaden_runs":0,"wall_time_s":time.monotonic()-started,
    }
    (args.out/"training_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("PF_DEI_DIRECT_SET_NRE_V2_TRAINING_COMPLETE "+json.dumps(summary,sort_keys=True),flush=True)
if __name__=="__main__": main()

#!/usr/bin/env python3
"""One-shot H01 seeds0..9 x five-update evaluation for direct Set-NRE v2."""
from __future__ import annotations
import argparse,csv,json,time
from pathlib import Path
import numpy as np
import torch
from pf_dei_direct_set_nre_v2 import (
    ConditionedDeepSetDirectNRE,block_context,build_block_layout,candidate_features,
    direct_posterior,log_measurement,sha256,
)
TRUE_CARRIER_EVAL_ONLY="quadtree_22_16_2_2"

def stable_rank_desc(values,ids,target):
    order=np.lexsort((ids.astype(str),-np.asarray(values,dtype=np.float64))); return int(np.flatnonzero(order==target)[0])+1

def norm_rank(rank,n=210): return float(rank-1)/float(n-1)

def load_observed_blocks(path:Path):
    out={seed:[] for seed in range(10)}
    with path.open(newline="",encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["house"]!="House01" or int(row["seed"]) not in out: continue
            out[int(row["seed"])].append({"block_id":int(row["block_id"]),"indices":np.asarray([int(v) for v in row["sample_row_indices"].split(";")],dtype=np.int64),"measured":np.asarray([float(v) for v in row["measured_ppm"].split(";")],dtype=np.float32)})
    for seed,rows in out.items():
        rows.sort(key=lambda r:r["block_id"])
        if [r["block_id"] for r in rows]!=list(range(1,len(rows)+1)): raise ValueError(f"seed{seed}: observed blocks incomplete")
    return out

def summarize(rows):
    base=np.asarray([r["pmfs_true_rank"] for r in rows]); direct=np.asarray([r["direct_true_rank"] for r in rows]); bn=np.asarray([r["pmfs_normalized_rank"] for r in rows]); dn=np.asarray([r["direct_normalized_rank"] for r in rows]); be=np.asarray([r["pmfs_expected_error_m"] for r in rows]); de=np.asarray([r["direct_expected_error_m"] for r in rows])
    return {"cases":len(rows),"pmfs_top1":int(np.sum(base<=1)),"pmfs_top5":int(np.sum(base<=5)),"pmfs_top10":int(np.sum(base<=10)),"direct_top1":int(np.sum(direct<=1)),"direct_top5":int(np.sum(direct<=5)),"direct_top10":int(np.sum(direct<=10)),"pmfs_median_normalized_rank":float(np.median(bn)),"direct_median_normalized_rank":float(np.median(dn)),"pmfs_mean_normalized_rank":float(np.mean(bn)),"direct_mean_normalized_rank":float(np.mean(dn)),"rank_improved":int(np.sum(direct<base)),"rank_tied":int(np.sum(direct==base)),"rank_worsened":int(np.sum(direct>base)),"pmfs_mean_expected_error_m":float(np.mean(be)),"direct_mean_expected_error_m":float(np.mean(de)),"relative_expected_error_improvement":float((np.mean(be)-np.mean(de))/np.mean(be))}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--dataset-root",type=Path,required=True); ap.add_argument("--pmfs-posteriors",type=Path,required=True); ap.add_argument("--observed-block-manifest",type=Path,required=True); ap.add_argument("--checkpoint",type=Path,required=True); ap.add_argument("--training-summary",type=Path,required=True); ap.add_argument("--out",type=Path,required=True); args=ap.parse_args(); args.out.mkdir(parents=True,exist_ok=True); started=time.monotonic()
    training=json.loads(args.training_summary.read_text(encoding="utf-8"))
    if training["contract"]!="PF_DEI_DIRECT_SET_NRE_V2_TRAINING" or training["checkpoint_selection"]!="minimum simulated validation BCE only": raise ValueError("wrong training contract")
    if training["checkpoint_sha256"]!=sha256(args.checkpoint): raise ValueError("checkpoint hash mismatch")
    ck=torch.load(args.checkpoint,map_location="cpu",weights_only=False); model=ConditionedDeepSetDirectNRE(candidate_dim=int(ck["candidate_dim"]),block_context_dim=int(ck["block_context_dim"]),hidden=int(ck["hidden"])); model.load_state_dict(ck["model_state"]); model.eval()
    measured=np.load(args.dataset_root/"H01_measured_train.npy",mmap_mode="r"); schedule=np.load(args.dataset_root/"H01_schedule_train.npz",allow_pickle=False); carriers=json.loads((args.dataset_root/"H01_carriers.json").read_text(encoding="utf-8")); frozen=np.load(args.pmfs_posteriors,allow_pickle=False); q_matrix=np.asarray(frozen["posterior"],dtype=np.float64); ids=np.asarray(frozen["carrier_id"]).astype(str); carrier_ids=np.asarray([c["carrier_id"] for c in carriers]).astype(str)
    if not np.array_equal(ids,carrier_ids) or q_matrix.shape!=(10,5,210): raise ValueError("carrier/posterior identity mismatch")
    true_hit=np.flatnonzero(ids==TRUE_CARRIER_EVAL_ONLY)
    if len(true_hit)!=1: raise ValueError("truth carrier missing")
    true_idx=int(true_hit[0]); xy=np.asarray([[c["centroid_x"],c["centroid_y"]] for c in carriers],dtype=np.float64); true_xy=xy[true_idx]; xy_center=0.5*(xy.min(axis=0)+xy.max(axis=0)); xy_scale=np.maximum(xy.max(axis=0)-xy.min(axis=0),1e-6); q0=np.asarray([float(c["prior_mass"]) for c in carriers],dtype=np.float64); q0/=q0.sum(); observed=load_observed_blocks(args.observed_block_manifest)
    layouts=[build_block_layout(schedule["x"][seed],schedule["y"][seed],schedule["stop_start"][seed],int(schedule["lengths"][seed])) for seed in range(10)]
    rows=[]; all_logits=[]
    with torch.no_grad():
        for seed in range(10):
            layout=layouts[seed]; manifest_indices=np.stack([r["indices"] for r in observed[seed]])
            if len(manifest_indices)<128: raise ValueError(f"seed{seed}: fewer than five prefixes")
            for update in range(1,6):
                visible=layout.visible_blocks(update); obs_np=log_measurement(np.stack([r["measured"] for r in observed[seed][:visible]])); logits=np.empty(210,dtype=np.float64); indices=manifest_indices[:visible]
                for start in range(0,210,30):
                    candidates=np.arange(start,min(start+30,210)); count=len(candidates); pred=measured[candidates,:,seed][:,:,indices]; pred=np.transpose(pred,(0,2,1,3)); obs_batch=np.repeat(obs_np[None,:,:],count,axis=0); ctx=np.stack([block_context(layout,visible,carriers[int(c)],xy_center,xy_scale) for c in candidates]); cand=np.stack([candidate_features(carriers[int(c)],xy_center,xy_scale) for c in candidates]); bmask=np.ones((count,visible),dtype=np.bool_); mmask=np.ones((count,8),dtype=np.bool_); tensors=[torch.from_numpy(a) for a in (obs_batch.astype(np.float32),log_measurement(pred),ctx.astype(np.float32),cand.astype(np.float32),bmask,mmask)]; logits[start:start+count]=model(*tensors).numpy()
                direct=direct_posterior(q0,logits); pmfs=q_matrix[seed,update-1]; pmfs_rank=stable_rank_desc(pmfs,ids,true_idx); direct_rank=stable_rank_desc(direct,ids,true_idx); pmfs_xy=np.sum(pmfs[:,None]*xy,axis=0); direct_xy=np.sum(direct[:,None]*xy,axis=0)
                rows.append({"seed":seed,"source_update_id":update,"visible_blocks":visible,"pmfs_true_rank":pmfs_rank,"pmfs_normalized_rank":norm_rank(pmfs_rank),"pmfs_truth_mass":float(pmfs[true_idx]),"direct_true_rank":direct_rank,"direct_normalized_rank":norm_rank(direct_rank),"direct_truth_mass":float(direct[true_idx]),"pmfs_expected_error_m":float(np.linalg.norm(pmfs_xy-true_xy)),"direct_expected_error_m":float(np.linalg.norm(direct_xy-true_xy)),"log_likelihood_ratio_true":float(logits[true_idx]),"logit_min":float(np.min(logits)),"logit_max":float(np.max(logits)),"true_carrier_evaluation_only":TRUE_CARRIER_EVAL_ONLY,"truth_available_during_scoring":False}); all_logits.append(logits)
    overall=summarize(rows); by_update={str(u):summarize([r for r in rows if r["source_update_id"]==u]) for u in range(1,6)}; result={"contract":"PF_DEI_DIRECT_SET_NRE_V2_H01_HISTORICAL_HOLDOUT_EVAL","scientific_status":"H01_DEVELOPMENT_TRAJECTORIES_0_9_HELD_OUT_FROM_NEURAL_TRAINING","checkpoint_step":int(ck["step"]),"checkpoint_validation_bce":float(ck["validation_bce"]),"checkpoint_sha256":sha256(args.checkpoint),"model_uses_pmfs_posterior":False,"posterior_reference":"geometry_prior_q0","overall":overall,"by_source_update":by_update,"cases":rows,"gaden_runs":0,"wall_time_s":time.monotonic()-started}
    np.save(args.out/"historical_direct_logits.npy",np.asarray(all_logits,dtype=np.float32));
    with (args.out/"historical_cases.csv").open("w",newline="",encoding="utf-8") as f: w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    (args.out/"historical_evaluation.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print("PF_DEI_DIRECT_SET_NRE_V2_EVAL_COMPLETE "+json.dumps({"overall":overall,"by_source_update":by_update,"wall_time_s":result["wall_time_s"]},sort_keys=True))
if __name__=="__main__": main()

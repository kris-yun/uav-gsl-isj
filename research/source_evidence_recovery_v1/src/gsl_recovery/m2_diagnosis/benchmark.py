"""Same-replay finite-budget proposal benchmark on development histories.

python -m gsl_recovery.m2_diagnosis.benchmark --manifest PATH --model PATH \
    --diagnosis PATH --out artifacts/diagnosis_budget_benchmark

All proposals target the same Bprime full suffix replay. Source-blind here
changes the diagnostic reference, never the replay likelihood. Normalized
finite-MC posteriors are biased; agreement is measured against exact inference.
"""
from __future__ import annotations
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import time
import numpy as np
from gsl_recovery.io import read_json,write_json,sha256
from gsl_recovery.data.qualification import audit_manifest,load_episode
from gsl_recovery.m1_generator import JointObservationGenerator
from gsl_recovery.m2_replay import ReplayEngine
from gsl_recovery.pipeline import default_mechanisms,inference_version
from gsl_recovery.types import Mechanism
from .network import DifferentialDiagnoser,diagnostic_pairs


class _CountingGenerator:
    def __init__(self,model):
        self.model=model;self.likelihood_calls=0;self.scored_observations=0;self.reference_trajectories=0
    def log_prob(self,history,source,mechanism):
        self.likelihood_calls+=1;self.scored_observations+=len(history)
        return self.model.log_prob(history,source,mechanism)
    def sample_future(self,history,actions,source,mechanism,rng):
        self.reference_trajectories+=1
        return self.model.sample_future(history,actions,source,mechanism,rng)


class _Proposal:
    def __init__(self,network=None,source_blind=False):
        self.network=network;self.source_blind=source_blind
    def propose(self,history,sources,generator,mechanisms,rng,**kwargs):
        if self.network is None:
            return np.full((len(sources),len(mechanisms)),1/len(mechanisms))
        # Force only the diagnostic reference mode. The caller always invokes
        # infer_budgeted(...,variant='Bprime'), retaining full history replay.
        kwargs["source_blind"]=self.source_blind
        return self.network.propose(history,sources,generator,mechanisms,rng,**kwargs)


def _fit_source_blind(manifest_path,manifest,model,mechanisms,seed,maxiter,out):
    actuals=[];references=[];labels=[];used=[];rng=np.random.default_rng(seed)
    catalogue=[asdict(m) for m in mechanisms]
    for entry in manifest["episodes"]:
        path=manifest_path.parent/entry["path"]
        raw=read_json(path)
        if raw["metadata"]["split"]!="train":continue
        record,history=load_episode(path,for_training=True)
        mechanism=asdict(Mechanism(**record.get("mechanism",{})))
        if mechanism not in catalogue:
            raise ValueError("Training mechanism outside frozen catalogue")
        label=catalogue.index(mechanism)
        # Exactly the training candidate panel used by train-diagnosis; the
        # only change is averaging references before the shared encoder.
        panel=np.asarray(record["candidates"],float)[:3]
        a,b=diagnostic_pairs(history,panel,model,mechanisms[0],rng,draws=2,source_blind=True)
        actuals.extend(a);references.extend(b);labels.extend([label]*len(a));used.append(entry["path"])
    if not used:raise ValueError("No qualified training labels for source-blind classifier")
    network=DifferentialDiagnoser(len(mechanisms),seed=seed).bind_catalog(mechanisms)
    started=time.perf_counter()
    fit=network.fit(np.asarray(actuals),np.asarray(references),np.asarray(labels),max_iter=maxiter)
    network.save(out/"source_blind_diagnosis.npz")
    receipt={**fit,"wall_seconds":time.perf_counter()-started,"training_episodes":used,
             "split":"train","development_labels_used":False,"frozen_test_used":False,
             "same_training_candidate_panel":"first 3 candidates as train-diagnosis",
             "source_blind_reference":True,"seed":seed,"maxiter":maxiter}
    write_json(out/"source_blind_training_receipt.json",receipt)
    return network


def run(manifest_path,model_path,diagnosis_path,out,episodes=4,repeats=5,
        budgets=(2,4,8),seed=2718,reference_draws=4,epsilon=.1,diagnosis_maxiter=150):
    manifest_path=Path(manifest_path);model_path=Path(model_path);diagnosis_path=Path(diagnosis_path)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    input_paths={"manifest_sha256":manifest_path,"generator_sha256":model_path,
                 "source_aware_checkpoint_sha256":diagnosis_path}
    input_hashes={key:sha256(path) for key,path in input_paths.items()}
    if episodes<1 or repeats<1 or min(budgets)<1:
        raise ValueError("Positive episodes/repeats/budgets required")
    audit=audit_manifest(manifest_path,for_training=True)
    if audit["status"]!="PASS":raise ValueError("DATA_QUALIFICATION_FAILED")
    manifest=read_json(manifest_path);model=JointObservationGenerator.load(model_path)
    aware=DifferentialDiagnoser.load(diagnosis_path);mechanisms=default_mechanisms()
    # Verify exact catalogue identity before any development computation.
    aware.bind_catalog(mechanisms)
    blind=_fit_source_blind(manifest_path,manifest,model,mechanisms,seed,diagnosis_maxiter,out)
    proposals={"uniform":_Proposal(),"source_blind":_Proposal(blind,True),
               "source_aware":_Proposal(aware,False)}
    selected=[]
    for entry in manifest["episodes"]:
        raw=read_json(manifest_path.parent/entry["path"])
        if raw["metadata"]["split"]=="development":selected.append(entry)
    selected=selected[:episodes]
    if len(selected)!=episodes:raise ValueError("Not enough development episodes")
    rows=[];exact_receipts=[];start=time.perf_counter()
    for episode_index,entry in enumerate(selected):
        record,history=load_episode(manifest_path.parent/entry["path"])
        sources=np.asarray(record["candidates"],float)
        version=inference_version(model,mechanisms,sources)
        counted=_CountingGenerator(model)
        exact_engine=ReplayEngine(counted,sources,mechanisms,mechanism_prior=[.8,.1,.1],model_version=version)
        t=time.perf_counter();exact=exact_engine.infer(history,"Bprime");elapsed=time.perf_counter()-t
        exact_receipts.append({"episode":entry["path"],"posterior":exact.source_posterior,
                               "likelihood_calls":counted.likelihood_calls,
                               "scored_observations":counted.scored_observations,"wall_seconds":elapsed})
        # Source truth is not used for proposal construction or approximation
        # error. Brier-distance here is squared distance to exact posterior.
        for budget in budgets:
            for repeat in range(repeats):
                mc_seed=seed+100000+episode_index*10000+budget*100+repeat
                for name,proposal in proposals.items():
                    counted=_CountingGenerator(model)
                    engine=ReplayEngine(counted,sources,mechanisms,mechanism_prior=[.8,.1,.1],model_version=version)
                    t=time.perf_counter()
                    result=engine.infer_budgeted(history,proposal,np.random.default_rng(mc_seed),
                         draws=budget,reference_draws=reference_draws,epsilon=epsilon,variant="Bprime")
                    elapsed=time.perf_counter()-t
                    error=result["source_posterior"]-exact.source_posterior
                    rows.append({"episode":entry["path"],"proposal":name,"R":budget,"repeat":repeat,
                        "seed":mc_seed,"replay_variant":"Bprime","l1_to_exact":float(np.abs(error).sum()),
                        "brier_distance_to_exact":float(error@error),
                        "likelihood_evaluations":result["likelihood_evaluations"],
                        "actual_log_prob_calls":counted.likelihood_calls,
                        "scored_observations":counted.scored_observations,
                        "reference_trajectories":counted.reference_trajectories,
                        "wall_seconds":elapsed,"posterior":result["source_posterior"],
                        "proposal_probabilities":result["proposal"],
                        "sampled_mechanisms":result["sampled_mechanisms"]})
    summary=[]
    for budget in budgets:
        for name in proposals:
            group=[r for r in rows if r["R"]==budget and r["proposal"]==name]
            summary.append({"R":budget,"proposal":name,"runs":len(group),
                **{key+"_mean":float(np.mean([r[key] for r in group])) for key in
                   ("l1_to_exact","brier_distance_to_exact","likelihood_evaluations",
                    "reference_trajectories","wall_seconds")},
                "l1_to_exact_max":float(max(r["l1_to_exact"] for r in group))})
    if any(sha256(path)!=input_hashes[key] for key,path in input_paths.items()):
        raise RuntimeError("INPUT_CHANGED_DURING_BENCHMARK: rerun on frozen manifest/model/checkpoint")
    receipt={"status":"COMPLETE_DEVELOPMENT_BUDGET_BENCHMARK","rows":len(rows),"episodes":len(selected),
        "repeats":repeats,"budgets":list(budgets),"seed":seed,"reference_draws":reference_draws,
        "epsilon":epsilon,**input_hashes,"model_version":model.version,
        "wall_seconds":time.perf_counter()-start,"summary":summary,"frozen_test_used":False,
        "target":"same Bprime full-history source-mechanism posterior for every proposal",
        "bias":"unnormalized evidence is unbiased under assumptions; finite-MC normalized posterior is biased",
        "brier_definition":"sum_s (estimated_p_s - exact_p_s)^2; approximation error, not label Brier score",
        "scope":"controlled development benchmark only; no diagnosis superiority or physical localization claim",
        "randomness":"same initial MC seed per episode/R/repeat; reference generation consumes additional draws"}
    write_json(out/"runs.json",rows);write_json(out/"exact_reference.json",exact_receipts)
    write_json(out/"receipt.json",receipt)
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ("manifest","model","diagnosis","out"):parser.add_argument("--"+key,required=True)
    parser.add_argument("--episodes",type=int,default=4);parser.add_argument("--repeats",type=int,default=5)
    parser.add_argument("--budgets",type=int,nargs="+",default=[2,4,8]);parser.add_argument("--seed",type=int,default=2718)
    parser.add_argument("--reference-draws",type=int,default=4);parser.add_argument("--epsilon",type=float,default=.1)
    parser.add_argument("--diagnosis-maxiter",type=int,default=150)
    args=parser.parse_args()
    result=run(args.manifest,args.model,args.diagnosis,args.out,args.episodes,args.repeats,args.budgets,
               args.seed,args.reference_draws,args.epsilon,args.diagnosis_maxiter)
    print(json.dumps(result,indent=2,ensure_ascii=False))


if __name__=="__main__":main()

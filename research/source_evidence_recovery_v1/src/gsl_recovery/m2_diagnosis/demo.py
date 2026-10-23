"""Executable controlled diagnosis training and budgeted-replay receipt.

Run: python -m gsl_recovery.m2_diagnosis.demo --out artifacts/m2_diagnosis
This is an algorithm/interface test, not House/PMFS performance evidence.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
from gsl_recovery.types import Action,Mechanism
from gsl_recovery.m1_teacher import ControlledPlumeBackend
from gsl_recovery.m2_replay import ReplayEngine
from .network import DifferentialDiagnoser,diagnostic_pairs


def run(out,seed=733,episodes=72):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(seed);backend=ControlledPlumeBackend()
    sources=np.array([[.5,.5],[1.5,.5],[.5,1.5],[1.5,1.5]])
    mechanisms=[Mechanism(),Mechanism("wind_bias",4,None,.9),
                Mechanism("sensor_offset",4,None,1.2)]
    actions=[Action(float(.3+(i%4)*.5),float(.3+(i//4)*.4),time=i) for i in range(16)]
    actuals=[];references=[];labels=[]
    for n in range(episodes):
        source=sources[n%len(sources)];label=n%len(mechanisms)
        history=backend.simulate_episode(source,actions,mechanisms[label],rng)
        # Nominal wrong-source references are explicit negative examples.
        reference_source=sources[(n+1)%len(sources)] if label==0 and n%2==0 else source
        actual,reference=diagnostic_pairs(history,[reference_source],backend,mechanisms[0],rng,draws=3)
        actuals.append(actual[0]);references.append(reference[0]);labels.append(label)
    actuals=np.asarray(actuals);references=np.asarray(references);labels=np.asarray(labels)
    diagnosis=DifferentialDiagnoser(len(mechanisms),hidden=16,seed=seed)
    diagnosis.bind_catalog(mechanisms)
    fit=diagnosis.fit(actuals,references,labels,max_iter=500,l2=.005)
    diagnosis.save(out/"diagnosis.npz")
    np.savez(out/"training_pairs.npz",observed=actuals,reference=references,labels=labels)
    history=backend.simulate_episode(sources[3],actions,mechanisms[1],np.random.default_rng(seed+1000))
    engine=ReplayEngine(backend,sources,mechanisms,mechanism_prior=[.8,.1,.1])
    exact=engine.infer(history)
    budgeted=engine.infer_budgeted(history,diagnosis,np.random.default_rng(seed+2000),
                                  draws=2,reference_draws=4,epsilon=.2)
    receipt={"status":"PASS_CONTROLLED_TRAIN_AND_USE", "seed":seed,"training_episodes":episodes,
             "heldout_rng_seed":seed+1000,"fit":fit,
             "training_accuracy":float(np.mean(diagnosis.predict_proba(actuals,references).argmax(1)==labels)),
             "exact_source_posterior":exact.source_posterior.tolist(),
             "budgeted_source_posterior":budgeted["source_posterior"].tolist(),
             "proposal":budgeted["proposal"].tolist(),"sampled_mechanisms":budgeted["sampled_mechanisms"],
             "likelihood_evaluations":budgeted["likelihood_evaluations"],
             "full_enumeration_evaluations":budgeted["full_enumeration_evaluations"],
             "reference_trajectories":budgeted["reference_trajectories"],
             "posterior_l1_to_exact":float(np.abs(exact.source_posterior-budgeted["source_posterior"]).sum()),
             "claim_scope":"Controlled synthetic trainability and pi/q replay integration; no localization improvement claim"}
    (out/"receipt.json").write_text(json.dumps(receipt,indent=2,ensure_ascii=False),encoding="utf-8")
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",default="artifacts/m2_diagnosis")
    parser.add_argument("--seed",type=int,default=733)
    parser.add_argument("--episodes",type=int,default=72)
    args=parser.parse_args()
    print(json.dumps(run(args.out,args.seed,args.episodes),indent=2,ensure_ascii=False))


if __name__=="__main__":
    main()

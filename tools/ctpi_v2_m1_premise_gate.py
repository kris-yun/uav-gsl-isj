#!/usr/bin/env python3
"""Cheap falsification gate for the first precise M1 proposal; no House runs."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments/cg_pc_ctt"))
from ctpi_v2_m1_premise_reference import ordinary_bayes, candidate_m1, SharedNuisanceM1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    contract_path = ROOT / "docs/CTPI_V2_M1_PREMISE_GATE_CONTRACT.json"
    contract = json.loads(contract_path.read_text())
    tol = contract["numeric_tolerance"]
    errors = []
    for nsource in (2, 3, 7):
        for nuisance in (1, 2, 5):
            for blocks in (1, 4, 13):
                grid = np.arange(nsource * nuisance * blocks).reshape(nsource,nuisance,blocks)
                prediction = 2 + np.sin(grid*.31) + .2*np.cos(grid*.13)
                y = 2 + .8*np.sin(np.arange(blocks)*.71)
                ps, pu = np.arange(1,nsource+1), np.arange(1,nuisance+1)
                a = ordinary_bayes(prediction,y,ps,pu,.4)
                b = candidate_m1(prediction,y,ps,pu,.4)
                errors.append(float(np.max(np.abs(a-b))))
    assert max(errors) < tol

    # At every matched nuisance, the source contrast is nonzero, but the
    # marginal response distributions are exactly the same after swapping.
    prediction = np.asarray([[[0.,0.], [1.,1.]], [[1.,1.], [0.,0.]]])
    y = np.asarray([0.,0.])
    ambiguous = candidate_m1(prediction,y,[1,1],[1,1],.1)
    baseline = ordinary_bayes(prediction,y,[1,1],[1,1],.1)
    matched_contrast = float(np.min(np.linalg.norm(prediction[0]-prediction[1],axis=1)))
    assert np.max(np.abs(ambiguous-.5)) < tol and matched_contrast > 0
    # A source-independent, observed wind cue changes nuisance weights; this
    # is EXTRA observed information, not an estimator-only causal advantage.
    anchored = candidate_m1(prediction,y,[1,1],[.9,.1],.1)
    anchored_baseline = ordinary_bayes(prediction,y,[1,1],[.9,.1],.1)
    assert np.max(np.abs(anchored-[.9,.1]))<tol
    assert np.max(np.abs(anchored-anchored_baseline))<tol

    # Preserve each nuisance trajectory through blocks. Incorrectly multiplying
    # fresh mixtures per block can manufacture compatibility with a source.
    persistent = np.asarray([[[0.,1.],[1.,0.]], [[.2,.2],[.2,.2]]])
    correct = candidate_m1(persistent,y,[1,1],[1,1],.1)
    per_block = np.ones(2)
    for i in range(2):
        per_block *= np.exp(-.5*((persistent[:,:,i]-y[i])/.1)**2).mean(axis=1)
    per_block /= per_block.sum()
    assert correct[1]>.99 and per_block[0]>.9

    profile_a = np.asarray([1.,2.,1.])
    profile_b = 2*profile_a
    scaled_error = float(np.max(np.abs(2*profile_a-1*profile_b)))
    assert scaled_error == 0
    # Relabel member trajectories and their weights together.
    permuted = candidate_m1(prediction[:,::-1,:],y,[1,1],[.1,.9],.1)
    assert np.max(np.abs(permuted-anchored))<tol
    model = SharedNuisanceM1([1,1],[1,1],.1)
    model.update(0,prediction[:,:,0],0.)
    rejected = 0
    for invalid in (0,-1,2):
        try:
            model.update(invalid,prediction[:,:,0],0.)
        except ValueError:
            rejected += 1
    assert rejected == 3
    result = {
        "verdict": "M1_SHARED_NUISANCE_CAUSAL_CONTRIBUTION_NOT_ESTABLISHED",
        "gate": "NO_GO_TO_HOUSE_FOR_THIS_FORMULATION",
        "implementation_checks_pass": True,
        "deterministic_fixture_count": len(errors),
        "max_candidate_vs_ordinary_bayes_difference": max(errors),
        "ambiguity_probe": {"candidate_posterior": ambiguous.tolist(), "baseline_posterior": baseline.tolist(),
                            "minimum_matched_nuisance_source_contrast": matched_contrast},
        "independent_wind_cue_probe": {"candidate_posterior": anchored.tolist(), "baseline_posterior": anchored_baseline.tolist()},
        "persistent_nuisance_probe": {"correct_posterior": correct.tolist(), "incorrect_independent_block_mixture": per_block.tolist()},
        "source_strength_overlap_max_abs": scaled_error,
        "rejected_invalid_block_ids": rejected,
        "interpretation": "Reject only the claim that shared nuisance marginalization itself is a new causal estimator. This is neither a real-world localization failure nor rejection of all causal inference methods.",
        "missing_for_new_claim": ["A concrete estimator step not equivalent to the same-input baseline",
                                  "An identifiable source contrast justified by available observations and structural assumptions",
                                  "Independent model qualification, then task benefit"],
        "house_runs_launched": 0,
        "input_hashes": {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                         (contract_path,ROOT/"experiments/cg_pc_ctt/ctpi_v2_m1_premise_reference.py",Path(__file__).resolve())}
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

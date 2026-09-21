#!/usr/bin/env python3
"""Exact finite examples and linear-algebra checks, NOT PMFS or physical GSL.
Run: python src/exact_identifiability_tests.py --out results/exact_tests.json
No performance or originality claim. numpy is the only nonstandard dependency.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np


def entropy(p: np.ndarray) -> float:
    a = np.asarray(p, dtype=float)
    a = a[a > 0]
    return float(-(a * np.log2(a)).sum())


def marginal(b: np.ndarray, groups: np.ndarray) -> np.ndarray:
    return np.bincount(groups, weights=b, minlength=int(groups.max()) + 1)


def outcomes(b: np.ndarray, likelihood: np.ndarray):
    # likelihood[state, outcome]
    if not np.allclose(likelihood.sum(axis=1), 1):
        raise ValueError('Each likelihood row must sum to one')
    for i in range(likelihood.shape[1]):
        w = b * likelihood[:, i]
        py = float(w.sum())
        if py > 1e-15:
            yield py, w / py


def info(b: np.ndarray, likelihood: np.ndarray, groups: np.ndarray) -> float:
    return entropy(marginal(b, groups)) - sum(
        p * entropy(marginal(post, groups)) for p, post in outcomes(b, likelihood)
    )


def risk(b: np.ndarray, source: np.ndarray) -> float:
    # Binary/discrete source classification 0-1 Bayes error; NOT native top-5%.
    return float(1 - marginal(b, source).max())


def finite_policy_tests():
    # Four worlds: (S,N) = (0,0),(0,1),(1,0),(1,1).
    s = np.array([0, 0, 1, 1]); n = np.array([0, 1, 0, 1]); b = np.full(4, .25)
    noisy_s = np.array([[.75, .25] if si == 0 else [.25, .75] for si in s])
    actions = {'calibrate_nuisance': np.eye(2)[n],
               'confounded_probe': np.eye(2)[s ^ n],
               'direct_noisy_source': noisy_s}

    def optimal(belief: np.ndarray, horizon: int):
        if horizon == 0:
            return risk(belief, s), None
        scores = {name: sum(p * optimal(post, horizon-1)[0]
                           for p, post in outcomes(belief, L))
                  for name, L in actions.items()}
        chosen = min(scores, key=scores.get)
        return scores[chosen], chosen

    def greedy(belief: np.ndarray, horizon: int):
        if horizon == 0:
            return risk(belief, s), None
        chosen = max(actions, key=lambda k: info(belief, actions[k], s))
        value = sum(p * greedy(post, horizon-1)[0]
                    for p, post in outcomes(belief, actions[chosen]))
        return value, chosen

    one = {name: info(b, L, s) for name, L in actions.items()}
    opt, first = optimal(b, 2); g, gfirst = greedy(b, 2)
    assert abs(opt) < 1e-12 and abs(g - .25) < 1e-12
    assert first in ('calibrate_nuisance', 'confounded_probe')

    # Different one-step example: observing 2 nuisance bits beats noisy source
    # in JOINT entropy but loses under source classification loss.
    ss = np.repeat(np.arange(2), 4); nn = np.tile(np.arange(4), 2)
    bb = np.full(8, 1/8)
    L_n = np.eye(4)[nn]
    L_s = np.array([[.9, .1] if si == 0 else [.1, .9] for si in ss])
    one_step = {}
    for name, L in {'nuisance_only_2bits': L_n, 'source_noisy_10pct': L_s}.items():
        one_step[name] = dict(source_mi_bits=info(bb,L,ss),
            joint_mi_bits=info(bb,L,np.arange(8)),
            expected_source_error=sum(p*risk(post,ss) for p,post in outcomes(bb,L)))

    return dict(scope='Exact discrete toy; independent source/nuisance prior; equal unit costs; not gas physics or PMFS',
                one_step_source_mi_bits=one,
                greedy_source_mi_horizon2=dict(first_action=gfirst,exact_error=g),
                optimal_terminal_risk_horizon2=dict(first_action=first,exact_error=opt),
                joint_vs_source_one_step=one_step)


def efficient_information(Js: np.ndarray, Jn: np.ndarray):
    # Inputs are already noise-whitened. Orthogonal residual, no added prior.
    P = Jn @ np.linalg.pinv(Jn)
    residual = Js - P @ Js
    return residual.T @ residual


def information_tests():
    # y_1=s+n+e_1, y_2=s-n+e_2. Independent noise, variance 1.
    first = efficient_information(np.array([[1.]]), np.array([[1.]]))
    second = efficient_information(np.array([[1.]]), np.array([[-1.]]))
    combined = efficient_information(np.array([[1.],[1.]]), np.array([[1.],[-1.]]))
    assert abs(first.item()) < 1e-12 and abs(second.item()) < 1e-12
    assert abs(combined.item()-2) < 1e-12
    rng = np.random.default_rng(20260921)
    max_profile_error=0.; max_schur_error=0.; max_span_info=0.
    for _ in range(1000):
        Js = rng.normal(size=(12,2)); Jn = rng.normal(size=(12,3)); delta = rng.normal(size=2)
        F = efficient_information(Js,Jn)
        beta = np.linalg.lstsq(Jn, -Js@delta, rcond=None)[0]
        profile = float(np.linalg.norm(Js@delta+Jn@beta)**2)
        max_profile_error=max(max_profile_error,abs(profile-float(delta@F@delta)))
        schur=Js.T@Js-Js.T@Jn@np.linalg.inv(Jn.T@Jn)@Jn.T@Js
        max_schur_error=max(max_schur_error,float(np.max(np.abs(F-schur))))
        collapsed=efficient_information(Jn@rng.normal(size=(3,2)),Jn)
        max_span_info=max(max_span_info,float(np.max(np.abs(collapsed))))
    return dict(noise_variance=1.,first_probe_information=float(first.item()),
        second_probe_information=float(second.item()),
        joint_two_probe_information=float(combined.item()),
        random_trials=1000,max_profile_identity_error=max_profile_error,
        max_schur_identity_error=max_schur_error,
        max_information_when_source_in_nuisance_span=max_span_info)


def coherence_test():
    # Source A gives [theta,theta], B gives [theta,-theta], theta in {1,2}.
    # Each candidate must retain the SAME theta across the observation block.
    x=np.array([1.,-1.]); bank_A=np.array([[1.,1.],[2.,2.]])
    bank_B=np.array([[1.,-1.],[2.,-2.]])
    coherent_A=float(np.min(np.sum((bank_A-x)**2,axis=1)))
    coherent_B=float(np.min(np.sum((bank_B-x)**2,axis=1)))
    # Additional textbook counterexample to independent per-cell refitting:
    # one source predicts [theta,theta], theta in {-1,+1}; observed [1,-1].
    bank=np.array([[-1.,-1.],[1.,1.]])
    coherent=float(np.min(np.sum((bank-x)**2,axis=1)))
    per_cell=float(np.sum(np.min((bank-x)**2,axis=0)))
    assert coherent==4. and per_cell==0.
    return dict(observed=x.tolist(),coherent_A_sse=coherent_A,coherent_B_sse=coherent_B,
                counterexample_coherent_sse=coherent,counterexample_independent_per_cell_sse=per_cell,
                explanation='min_theta sum != sum min_theta; per-cell nuisance switching fits a nonexistent world')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=Path('results/exact_tests.json'))
    args=parser.parse_args()
    result=dict(scope='NEW exact mathematical sanity tests; NOT a new House/GADEN/native PMFS performance run',
        finite_policy=finite_policy_tests(),local_information=information_tests(),
        nuisance_coherence=coherence_test())
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2,ensure_ascii=False))

if __name__=='__main__':
    main()

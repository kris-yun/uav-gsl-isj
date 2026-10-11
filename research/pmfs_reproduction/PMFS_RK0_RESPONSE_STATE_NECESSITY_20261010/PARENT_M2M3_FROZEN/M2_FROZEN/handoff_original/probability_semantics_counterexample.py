#!/usr/bin/env python3
"""Formula-level counterexample; NOT a B4 replay or a new GADEN simulation.

Single receptor, iid Bernoulli detections, exact candidate frequencies.
Uses the local PMFS binary-filter update at zero spatial offset and its
single-cell similarity score. The prior and discrimination power match B4;
0.6f / 0.1f are represented as binary32 constants, then used in real-valued
formula evaluation. This is NOT a bitwise C++ floating-point emulator.

No original files are modified. No labels/data from B4 enter the synthetic
sample. Exact binomial averaging avoids Monte Carlo seed selection.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, struct
from pathlib import Path


def f32(x: float) -> float:
    return struct.unpack('f', struct.pack('f', x))[0]


def logit(p: float) -> float:
    if not 0 < p < 1:
        raise ValueError('Probability must lie strictly between zero and one.')
    return math.log(p) - math.log1p(-p)


def sigmoid(x: float) -> float:
    if x >= 0:
        e = math.exp(-x)
        return 1 / (1 + e)
    e = math.exp(x)
    return e / (1 + e)


def run(outdir: Path) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    p0, p_hit, p_miss, discrimination = .3, f32(.6), f32(.1), .4
    l0 = logit(p0)
    a, b = logit(p_hit)-l0, logit(p_miss)-l0
    rcrit = -b/(a-b)
    r, wrong_q = .6, .9
    rows = []
    for n in [5, 10, 20, 50, 100, 200, 1000]:
        ks = list(range(n+1))
        logw = [math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1)
                +k*math.log(r)+(n-k)*math.log1p(-r) for k in ks]
        mx = max(logw)
        weights = [math.exp(w-mx) for w in logw]
        norm = math.fsum(weights)
        weights = [w/norm for w in weights]
        map_wrong = raw_wrong = map_mean = expected_native_gap = 0.
        expected_raw_gap = 0.
        for k,w in zip(ks, weights):
            p = sigmoid(l0+k*a+(n-k)*b)
            # Confidence=1: any common positive confidence has identical ranking.
            st = 1-discrimination*abs(p-r)
            sw = 1-discrimination*abs(p-wrong_q)
            raw_gap = k*math.log(r/wrong_q)+(n-k)*math.log((1-r)/(1-wrong_q))
            map_wrong += w*(sw>st)
            raw_wrong += w*(raw_gap<0)
            map_mean += w*p
            expected_native_gap += w*(math.log(st)-math.log(sw))
            expected_raw_gap += w*raw_gap
        kl = r*math.log(r/wrong_q)+(1-r)*math.log((1-r)/(1-wrong_q))
        assert math.isclose(expected_raw_gap,n*kl,rel_tol=2e-12,abs_tol=2e-12)
        k = int(round(r*n))
        p = sigmoid(l0+k*a+(n-k)*b)
        rows.append(dict(n=n,true_hit_rate=r,wrong_candidate_rate=wrong_q,
            mean_measured_map_probability=map_mean,
            exact_probability_map_similarity_selects_wrong=map_wrong,
            exact_probability_raw_bernoulli_selects_wrong=raw_wrong,
            expected_log_score_true_minus_wrong=expected_native_gap,
            expected_raw_log_likelihood_true_minus_wrong=expected_raw_gap,
            example_hits=k, example_map_probability=p,
            example_native_true_score=1-discrimination*abs(p-r),
            example_native_wrong_score=1-discrimination*abs(p-wrong_q),
            example_raw_likelihood_ratio_true_over_wrong=math.exp(k*math.log(r/wrong_q)+(n-k)*math.log((1-r)/(1-wrong_q)))))
    with (outdir/'probability_semantics_counterexample.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    result=dict(status='FORMULA_LEVEL_COUNTEREXAMPLE_VERIFIED_NOT_B4_CAUSE',
        assumptions=['one receptor','iid Bernoulli detections','exact candidate hit frequencies',
                     'same positive confidence for candidates','zero spatial propagation offset',
                     'finite initial log odds','no 2D/3D or forward Monte Carlo error'],
        constants=dict(prior=p0,hit_inverse_value=p_hit,miss_inverse_value=p_miss,
                       discrimination_power=discrimination),
        hit_log_odds_increment=a,miss_log_odds_increment=b,critical_hit_frequency=rcrit,
        limit='p_map -> 1 almost surely when r>critical, ->0 when r<critical. No convergence claim at equality.',
        nonclaims=['Not a native C++ bitwise replay','Not an observed B4 localization improvement',
                   'Not proof that this alone causes B4','Not a novel algorithm or a cross-dataset result',
                   'Does not refute a binary filter for a genuinely static binary latent variable'],
        rows=rows)
    (outdir/'probability_semantics_counterexample.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--out',type=Path,default=Path('.'))
    result=run(p.parse_args().out)
    print(json.dumps({k:result[k] for k in ('status','critical_hit_frequency','rows')},indent=2))

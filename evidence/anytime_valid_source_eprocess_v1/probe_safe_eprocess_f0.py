#!/usr/bin/env python3
from __future__ import annotations
import math
import numpy as np

EPS = 1e-12

def clip01(x: float) -> float:
    return float(min(1.0-EPS, max(EPS, x)))

def robust_e_factor(y: int, q: float, lo: float, hi: float) -> float:
    if not (0 <= lo <= hi <= 1):
        raise ValueError('invalid interval')
    if y not in (0,1):
        raise ValueError('y must be binary')
    q = clip01(q)
    pstar = clip01(min(hi, max(lo, q)))
    return q/pstar if y == 1 else (1-q)/(1-pstar)

def expected_factor(p: float, q: float, lo: float, hi: float) -> float:
    return p*robust_e_factor(1,q,lo,hi)+(1-p)*robust_e_factor(0,q,lo,hi)

def bern_kl(q: float, p: float) -> float:
    q,p=clip01(q),clip01(p)
    return q*math.log(q/p)+(1-q)*math.log((1-q)/(1-p))

def expected_log_factor_under_q(q: float, lo: float, hi: float) -> float:
    pstar=clip01(min(hi,max(lo,q)))
    return q*math.log(robust_e_factor(1,q,lo,hi))+(1-q)*math.log(robust_e_factor(0,q,lo,hi))

def algebra_grid_test() -> tuple[float,int]:
    mx=0.0; bad=0
    for lo in np.linspace(0.02,0.80,9):
        for hi in np.linspace(lo+0.02,0.98,9):
            for q in np.linspace(0.01,0.99,31):
                for p in np.linspace(lo,hi,51):
                    e=expected_factor(float(p),float(q),float(lo),float(hi))
                    mx=max(mx,e)
                    if e>1+1e-10:
                        bad+=1
    return mx,bad

def kl_identity_test() -> float:
    err=0.0
    for lo in np.linspace(0.05,0.75,8):
        for hi in np.linspace(lo+0.05,0.95,8):
            for q in np.linspace(0.01,0.99,25):
                pstar=min(hi,max(lo,q))
                lhs=expected_log_factor_under_q(float(q),float(lo),float(hi))
                rhs=bern_kl(float(q),float(pstar))
                err=max(err,abs(lhs-rhs))
    return err

def adaptive_optional_stopping_mc(seed=20260923, n=200_000, horizon=100, alpha=0.05):
    rng=np.random.default_rng(seed)
    p_true=0.40
    lo,hi=0.30,0.50
    E=np.ones(n,dtype=float)
    crossed=np.zeros(n,dtype=bool)
    last=np.zeros(n,dtype=np.int8)
    threshold=1/alpha
    for t in range(horizon):
        q=np.where(last==1,0.85,0.15)
        y=(rng.random(n)<p_true).astype(np.int8)
        pstar=np.clip(q,lo,hi)
        fac=np.where(y==1,q/pstar,(1-q)/(1-pstar))
        E*=fac
        crossed |= E>=threshold
        last=y
    return float(crossed.mean()), float(E.mean())

def zero_growth_inside_null_test() -> float:
    worst=0.0
    for q in np.linspace(0.2,0.8,31):
        lo=max(0.0,q-0.1); hi=min(1.0,q+0.1)
        worst=max(worst,abs(expected_log_factor_under_q(float(q),lo,hi)))
    return worst

if __name__=='__main__':
    mx,bad=algebra_grid_test()
    kl_err=kl_identity_test()
    cross,meanE=adaptive_optional_stopping_mc()
    zero=zero_growth_inside_null_test()

    assert bad==0
    assert mx<=1+1e-10
    assert kl_err<1e-11
    assert zero<1e-11
    assert cross<=0.05 + 0.003

    print('SAFE-F0: PASS')
    print(f'max_null_expected_factor={mx:.12f}')
    print(f'violations={bad}')
    print(f'max_KL_identity_error={kl_err:.3e}')
    print(f'max_zero_growth_inside_null={zero:.3e}')
    print(f'adaptive_crossing_rate_alpha0.05={cross:.6f}')
    print(f'final_mean_eprocess={meanE:.6e}')

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V40: six auditable linear/Gaussian theory checks; NOT native S2 performance.
Usage: python V40_TESTS.py (requires numpy). All RNG is frozen.
"""
import numpy as np


def info(J, N, cov):
    eig, U = np.linalg.eigh(cov)
    assert eig.min() > 1e-10
    W12 = (U * eig**(-.5)) @ U.T
    A = W12 @ N
    P = np.eye(cov.shape[0]) - A @ np.linalg.pinv(A)
    return J.T @ W12 @ P @ W12 @ J


def main():
    rng = np.random.default_rng(20261028)
    m = 8
    Z = rng.normal(size=(m,m))
    cov = Z @ Z.T + 0.5*np.eye(m)
    J = rng.normal(size=(m,2))
    N = rng.normal(size=(m,3))
    P = info(J,N,cov)
    W = np.linalg.inv(cov)
    schur = J.T@W@J-(J.T@W@N)@np.linalg.pinv(N.T@W@N)@(N.T@W@J)
    assert np.allclose(P,schur,atol=1e-10)
    assert np.linalg.eigvalsh(P).min() >= -1e-10
    print("T1 PASS: nuisance projection equals Schur complement")

    # V39 two-way fixed effects are the special case of T1.
    effects = np.zeros((6,5))
    for i in range(3):
        for t in range(2):
            row=i*2+t
            effects[row,t]=1
            effects[row,2+i]=1
    D = np.array([[6.6666666667,0],
                  [-3.3333333333,5.7735026919],
                  [-3.3333333334,-5.7735026919]])
    Jxy=np.zeros((6,2))
    for i in range(3): Jxy[i*2+1]=D[i]
    I=info(Jxy,effects,np.eye(6)*.08**2)
    assert np.allclose(I,D.T@D/(2*.08**2),atol=1e-7)
    print("T2 PASS: V39 double difference is a special projected Fisher case")

    # Completely free positive release coefficients can fully absorb a
    # nearby change in horizontal source, even though fixed q yields rank 2.
    q=np.full(8,.8)
    A=rng.normal(size=(8,8))*.01
    B=rng.normal(size=(8,8))*.01
    K=np.eye(8)
    Js=np.column_stack((A@q,B@q))
    assert np.linalg.matrix_rank(Js)==2
    Ifree=info(Js,K,np.eye(8)*.02**2)
    assert np.linalg.norm(Ifree)<1e-9
    Knew=K+.1*A+.1*B
    qnew=np.linalg.solve(Knew,K@q)
    assert qnew.min()>0 and np.allclose(Knew@qnew,K@q,atol=1e-12)
    print("T3 PASS: unconstrained release history can remove all source rank")

    # Model uncertainty triangle-bound conditional on a VALIDATED common metric.
    m0=np.array([0.,0.,0.]);m1=np.array([1.4,0.,0.])
    eps0,eps1=.2,.3
    cert=max(0,np.linalg.norm(m0-m1)-eps0-eps1)
    assert abs(cert-.9)<1e-12
    for _ in range(2000):
        d0=rng.normal(size=3);d0/=np.linalg.norm(d0);d0*=rng.uniform(0,eps0)
        d1=rng.normal(size=3);d1/=np.linalg.norm(d1);d1*=rng.uniform(0,eps1)
        assert np.linalg.norm(m0+d0-m1-d1)+1e-12>=cert
    print("T4 PASS: validated model error yields a conservative margin")

    # Positive local XY Fisher does not guarantee unique GLOBAL source.
    s0=np.array([.23,1.3]);s1=s0+np.array([2*np.pi,0.])
    def mu(s):return np.array([np.cos(s[0]),np.sin(s[0]),s[1]])
    Jloc=np.array([[-np.sin(s0[0]),0],[np.cos(s0[0]),0],[0,1.]])
    assert np.linalg.matrix_rank(Jloc)==2
    assert np.linalg.norm(mu(s0)-mu(s1))<1e-12
    print("T5 PASS: full local rank with a global source alias")

    # Actual concentration is delayed and first-order filtered in S2.
    rho=np.exp(-1.)
    delay=2.+rho/(1.-rho)
    assert np.isclose(delay,2.5819767068693265)
    print("T6 PASS: mean causal sensor age %.6fs; at 2m/s %.6fm" %
          (delay,2*delay))
    print("PASS 6/6: no claim of native S2 contact or localization improvement")


if __name__=="__main__":
    main()

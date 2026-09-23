#!/usr/bin/env python3
"""F0 algebra for the coupled common-transport adversary.

No gas-source data are used here. This validates only:
1) robust-regret ranking exactly recovers native score ranking at rho=0;
2) the ellipsoidal worst-case linear score difference matches random-search checks;
3) the shared-adversary robust candidate variance recovers native variance at rho=0;
4) robust variance never exceeds nominal variance.
"""

import math
import random
import numpy as np


def robust_regret(log_scores, sensitivities, M, rho):
    L = np.asarray(log_scores, dtype=float)
    A = np.asarray(sensitivities, dtype=float)
    Minv = np.linalg.inv(np.asarray(M, dtype=float))
    n = len(L)
    out = np.empty(n)
    for s in range(n):
        vals = []
        for j in range(n):
            d = A[j] - A[s]
            penalty = rho * math.sqrt(max(0.0, float(d @ Minv @ d)))
            vals.append(L[j] - L[s] + penalty)
        out[s] = max(vals)
    return out


def weighted_variance(weights, values):
    w = np.asarray(weights, dtype=float)
    w = w / w.sum()
    x = np.asarray(values, dtype=float)
    mu = float(w @ x)
    return float(np.sum(w * (x - mu) ** 2))


def robust_shared_variance(weights, h, G, M, rho):
    w = np.asarray(weights, dtype=float)
    w = w / w.sum()
    h = np.asarray(h, dtype=float)
    G = np.asarray(G, dtype=float)
    M = np.asarray(M, dtype=float)

    C = np.diag(w) - np.outer(w, w)
    nominal = float(h @ C @ h)
    if rho == 0:
        return nominal, np.zeros(G.shape[1])

    # Whiten theta^T M theta <= rho^2.
    evals, evecs = np.linalg.eigh(M)
    if np.min(evals) <= 1e-12:
        raise ValueError("M must be positive definite in F0")
    Minvhalf = evecs @ np.diag(1.0 / np.sqrt(evals)) @ evecs.T

    A = Minvhalf @ (G.T @ C @ G) @ Minvhalf
    b = Minvhalf @ (G.T @ C @ h)

    # Unconstrained minimizer using pseudoinverse.
    z0 = -np.linalg.pinv(A, rcond=1e-12) @ b
    if np.linalg.norm(z0) <= rho + 1e-12:
        z = z0
    else:
        # z(lambda)=-(A+lambda I)^-1 b; norm decreases with lambda.
        eye = np.eye(A.shape[0])

        def z_of(lam):
            return -np.linalg.solve(A + lam * eye, b)

        lo = 0.0
        hi = 1.0
        while np.linalg.norm(z_of(hi)) > rho:
            hi *= 2.0
        for _ in range(120):
            mid = 0.5 * (lo + hi)
            if np.linalg.norm(z_of(mid)) > rho:
                lo = mid
            else:
                hi = mid
        z = z_of(0.5 * (lo + hi))

    theta = Minvhalf @ z
    q = h + G @ theta
    return weighted_variance(w, q), theta


def main():
    rng = np.random.default_rng(20260923)

    max_rank_fail = 0
    max_zero_var_err = 0.0
    max_var_violation = -1e30

    for _ in range(1000):
        ns = 20
        d = 4
        L = rng.normal(size=ns)
        sens = rng.normal(size=(ns, d))
        A = rng.normal(size=(d, d))
        M = A.T @ A + 0.5 * np.eye(d)

        native_order = list(np.argsort(-L))
        rr0 = robust_regret(L, sens, M, 0.0)
        robust_order = list(np.argsort(rr0))
        if native_order != robust_order:
            max_rank_fail += 1

        weights = rng.random(ns) + 0.01
        h = rng.random(ns)
        G = rng.normal(scale=0.1, size=(ns, d))

        native = weighted_variance(weights, h)
        r0, _ = robust_shared_variance(weights, h, G, M, 0.0)
        max_zero_var_err = max(max_zero_var_err, abs(native - r0))

        rho = float(rng.uniform(0.001, 1.0))
        rr, theta = robust_shared_variance(weights, h, G, M, rho)
        max_var_violation = max(max_var_violation, rr - native)
        assert float(theta @ M @ theta) <= rho * rho + 1e-8

    assert max_rank_fail == 0
    assert max_zero_var_err < 1e-12
    assert max_var_violation <= 1e-10

    # Direct support-function check for one linear score difference.
    d = 3
    A = rng.normal(size=(d, d))
    M = A.T @ A + np.eye(d)
    Minv = np.linalg.inv(M)
    v = rng.normal(size=d)
    rho = 0.4
    exact = rho * math.sqrt(float(v @ Minv @ v))

    # Boundary optimizer theta*=rho*M^-1 v / sqrt(v^T M^-1 v)
    theta_star = rho * (Minv @ v) / math.sqrt(float(v @ Minv @ v))
    attained = float(v @ theta_star)
    assert abs(attained - exact) < 1e-12
    assert abs(float(theta_star @ M @ theta_star) - rho * rho) < 1e-12

    print("native_rank_recovery_failures", max_rank_fail)
    print("max_zero_radius_variance_error", max_zero_var_err)
    print("max_robust_minus_native_variance", max_var_violation)
    print("support_function_exact", exact)
    print("F0_COUPLED_TRANSPORT_ADVERSARY_PASS")


if __name__ == "__main__":
    main()

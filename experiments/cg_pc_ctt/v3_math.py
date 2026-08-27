#!/usr/bin/env python3
"""Shared mathematics for CG-PC-CTT V3 observation-conditioned source resolution.

This module is research-only. It does not modify frozen Gate V2.

Core design:
  * candidate IDs are quotiented to unique physical source coordinates;
  * member nuisance is represented by the full pair-difference covariance;
  * all source contrasts use the Moore-Penrose inverse of that covariance,
    avoiding artificial information gain from duplicated/rotated feature encodings;
  * local source identifiability is a 2-D property of physical (x,y) coordinates;
  * optional assimilation gain maps local information into source-uncertainty shrinkage.

No outcome-fitted threshold is defined here.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, product
import math
import numpy as np
from scipy.spatial import Delaunay

EPS_COORD_DECIMALS = 7
P_SIGNFLIP_MAX = 0.01


@dataclass(frozen=True)
class NuisanceMetric:
    covariance: np.ndarray
    precision: np.ndarray
    eigenvalues: np.ndarray
    numerical_rank: int
    tolerance: float


def coordinate_quotient(phi: np.ndarray, xy: np.ndarray, decimals: int = EPS_COORD_DECIMALS):
    """Merge candidate IDs representing the same physical source coordinate.

    phi: [S,M,D]
    xy:  [S,2]

    Returns qphi[Sq,M,D], qxy[Sq,2], groups(list[list[int]]), max_member_field_drift.
    """
    phi = np.asarray(phi, dtype=np.float64)
    xy = np.asarray(xy, dtype=np.float64)
    if phi.ndim != 3:
        raise ValueError(f"phi must be [S,M,D], got {phi.shape}")
    if xy.shape != (phi.shape[0], 2):
        raise ValueError("candidate_xy shape mismatch")

    keyed = {}
    order = []
    for i, (x, y) in enumerate(xy):
        key = (round(float(x), decimals), round(float(y), decimals))
        if key not in keyed:
            keyed[key] = []
            order.append(key)
        keyed[key].append(i)

    groups = [keyed[k] for k in order]
    qxy = np.asarray(order, dtype=np.float64)
    qphi = np.stack([phi[np.asarray(g, dtype=int)].mean(axis=0) for g in groups], axis=0)

    drift = 0.0
    for g in groups:
        if len(g) > 1:
            ref = phi[g[0]]
            for j in g[1:]:
                drift = max(drift, float(np.max(np.abs(ref - phi[j]))))
    return qphi, qxy, groups, drift


def pair_difference_covariance(phi: np.ndarray) -> np.ndarray:
    """Full within-source member nuisance covariance from pair differences.

    Sigma_tr = mean_{s,m<n} 0.5 (phi_sm-phi_sn)(phi_sm-phi_sn)^T.

    The pair-difference form avoids estimating the candidate mean before
    nuisance estimation and is invariant to candidate translation.
    """
    x = np.asarray(phi, dtype=np.float64)
    if x.ndim != 3:
        raise ValueError(f"phi must be [S,M,D], got {x.shape}")
    S, M, D = x.shape
    if M < 2:
        raise ValueError("need >=2 transport members")

    cov = np.zeros((D, D), dtype=np.float64)
    n = 0
    for m in range(M):
        for h in range(m + 1, M):
            d = x[:, m, :] - x[:, h, :]
            cov += 0.5 * (d.T @ d)
            n += S
    cov /= float(max(n, 1))
    return 0.5 * (cov + cov.T)


def psd_pseudoinverse(cov: np.ndarray) -> NuisanceMetric:
    """Numerical Moore-Penrose inverse for a PSD covariance.

    The tolerance is numerical only, not outcome tuned:
      tol = max(D,1) * eps_machine * max(lambda_max, 1) * 100.

    Exact duplicate feature embeddings therefore do not create extra
    Mahalanobis information; they only add covariance null directions.
    """
    cov = np.asarray(cov, dtype=np.float64)
    if cov.ndim != 2 or cov.shape[0] != cov.shape[1]:
        raise ValueError("covariance must be square")
    cov = 0.5 * (cov + cov.T)
    val, vec = np.linalg.eigh(cov)
    lmax = max(float(np.max(val)), 0.0)
    tol = max(cov.shape[0], 1) * np.finfo(np.float64).eps * max(lmax, 1.0) * 100.0
    keep = val > tol
    inv = np.zeros_like(val)
    inv[keep] = 1.0 / val[keep]
    precision = (vec * inv[None, :]) @ vec.T
    precision = 0.5 * (precision + precision.T)
    return NuisanceMetric(cov, precision, val, int(np.sum(keep)), float(tol))


def nuisance_metric(phi: np.ndarray) -> NuisanceMetric:
    return psd_pseudoinverse(pair_difference_covariance(phi))


def delaunay_neighbors(xy: np.ndarray):
    xy = np.asarray(xy, dtype=np.float64)
    if xy.ndim != 2 or xy.shape[1] != 2 or len(xy) < 3:
        raise ValueError("need >=3 2-D physical source coordinates")
    tri = Delaunay(xy)
    nb = [set() for _ in range(len(xy))]
    edges = set()
    for simplex in tri.simplices:
        for i, j in combinations(map(int, simplex), 2):
            a, b = min(i, j), max(i, j)
            edges.add((a, b))
            nb[a].add(b)
            nb[b].add(a)
    return [np.asarray(sorted(v), dtype=int) for v in nb], sorted(edges)


def local_geometry_stats(xy: np.ndarray, i: int, neighbours: np.ndarray):
    DX = np.asarray(xy, dtype=np.float64)[neighbours] - np.asarray(xy, dtype=np.float64)[i]
    rank = int(np.linalg.matrix_rank(DX))
    if rank < 1:
        cond = math.inf
    else:
        s = np.linalg.svd(DX, compute_uv=False)
        positive = s[s > np.finfo(np.float64).eps * max(DX.shape) * max(float(s[0]), 1.0)]
        cond = math.inf if len(positive) < 2 else float(positive[0] / positive[-1])
    return DX, rank, cond


def member_local_jacobians(phi: np.ndarray, xy: np.ndarray, i: int, neighbours: np.ndarray):
    """Fit local member-specific response Jacobians.

    Returns B[M,2,D], where B_m = J_m^T and
      Delta phi ~= Delta x @ B_m.
    """
    x = np.asarray(phi, dtype=np.float64)
    xy = np.asarray(xy, dtype=np.float64)
    DX, rank, cond = local_geometry_stats(xy, i, neighbours)
    if rank < 2:
        return np.zeros((x.shape[1], 2, x.shape[2])), rank, cond
    pinv = np.linalg.pinv(DX)
    B = []
    for m in range(x.shape[1]):
        DZ = x[neighbours, m, :] - x[i, m, :]
        B.append(pinv @ DZ)
    return np.asarray(B), rank, cond


def cross_member_tangent_information(B: np.ndarray, precision: np.ndarray):
    """Cross-member 2x2 source information.

    F = avg_{m!=n} B_m Sigma_tr^+ B_n^T.

    Same-member squares are excluded, preserving the replicated-source logic
    of Gate V2 while aligning the source dimension with physical (x,y).
    """
    B = np.asarray(B, dtype=np.float64)
    P = np.asarray(precision, dtype=np.float64)
    if B.ndim != 3 or B.shape[1] != 2:
        raise ValueError("B must be [M,2,D]")
    if P.shape != (B.shape[2], B.shape[2]):
        raise ValueError("precision shape mismatch")
    M = B.shape[0]
    if M < 2:
        raise ValueError("need >=2 members")
    F = np.zeros((2, 2), dtype=np.float64)
    for m in range(M):
        for n in range(M):
            if m != n:
                F += B[m] @ P @ B[n].T
    F /= float(M * (M - 1))
    return 0.5 * (F + F.T)


def tangent_information_for_source(phi: np.ndarray, xy: np.ndarray, i: int,
                                   neighbours: np.ndarray, metric: NuisanceMetric):
    B, rank, cond = member_local_jacobians(phi, xy, i, neighbours)
    F = cross_member_tangent_information(B, metric.precision)
    ev = np.linalg.eigvalsh(F)[::-1]
    lmax, lmin = map(float, ev)
    gamma = math.sqrt(max(lmin, 0.0) / max(lmax, np.finfo(float).tiny)) if lmax > 0 else 0.0
    return {
        "F": F,
        "lambda_max": lmax,
        "lambda_min": lmin,
        "gamma_xy": float(gamma),
        "geometry_rank": rank,
        "geometry_condition": cond,
    }


def pair_cross_stat(phi: np.ndarray, i: int, j: int, metric: NuisanceMetric,
                    exact_signflip: bool = True):
    """Replicated source-pair separation under full nuisance precision."""
    x = np.asarray(phi, dtype=np.float64)
    M = x.shape[1]
    d = x[i] - x[j]
    P = metric.precision

    def cross_for(signs):
        z = d * np.asarray(signs, dtype=np.float64)[:, None]
        total = z.sum(axis=0)
        self_term = sum(float(v @ P @ v) for v in z)
        return (float(total @ P @ total) - self_term) / float(M * (M - 1))

    obs = cross_for(np.ones(M))
    p = None
    patterns = None
    if exact_signflip:
        if M > 16:
            raise ValueError("exact sign-flip limited to M<=16")
        patterns = [(1.0,) + tail for tail in product((-1.0, 1.0), repeat=M - 1)]
        null = np.asarray([cross_for(s) for s in patterns], dtype=np.float64)
        p = float(np.mean(null >= obs - 1e-12))

    loo = []
    for r in range(M):
        dd = np.delete(d, r, axis=0)
        mm = M - 1
        total = dd.sum(axis=0)
        self_term = sum(float(v @ P @ v) for v in dd)
        loo.append((float(total @ P @ total) - self_term) / float(mm * (mm - 1)))

    return {
        "pair_cross_strength": float(obs),
        "pair_alpha_cf": float(math.sqrt(max(obs, 0.0))),
        "pair_p_signflip": p,
        "pair_null_patterns": None if patterns is None else len(patterns),
        "loo_min_cross_strength": float(min(loo)),
        "resolved_proto": bool(obs > 0 and (p is None or p <= P_SIGNFLIP_MAX) and min(loo) > 0),
    }


def _sqrt_psd(A: np.ndarray):
    A = 0.5 * (np.asarray(A, dtype=np.float64) + np.asarray(A, dtype=np.float64).T)
    val, vec = np.linalg.eigh(A)
    val = np.maximum(val, 0.0)
    return (vec * np.sqrt(val)[None, :]) @ vec.T


def assimilation_resolution_gain(F: np.ndarray, prior_cov: np.ndarray):
    """ACI/data-assimilation-inspired local uncertainty-reduction diagnostic.

    For a local Gaussian source displacement prior P- and information F:
      P+ = (P-^{-1} + F)^{-1}

    Dimensionless directional information is eig(P-^{1/2} F P-^{1/2}).
    Total Gaussian information gain is 0.5*log det(I + P-^{1/2} F P-^{1/2}).

    This is a diagnostic, not a release threshold.
    """
    F = 0.5 * (np.asarray(F, dtype=np.float64) + np.asarray(F, dtype=np.float64).T)
    P0 = 0.5 * (np.asarray(prior_cov, dtype=np.float64) + np.asarray(prior_cov, dtype=np.float64).T)
    if F.shape != (2, 2) or P0.shape != (2, 2):
        raise ValueError("F and prior_cov must be 2x2")
    Psqrt = _sqrt_psd(P0)
    G = 0.5 * (Psqrt @ F @ Psqrt + (Psqrt @ F @ Psqrt).T)
    kappa = np.linalg.eigvalsh(G)[::-1]
    kappa_pos = np.maximum(kappa, 0.0)
    gain = 0.5 * float(np.sum(np.log1p(kappa_pos)))
    shrink = 1.0 / (1.0 + kappa_pos)
    return {
        "dimensionless_information_eigenvalues": kappa.tolist(),
        "information_gain_nats_positive_part": gain,
        "posterior_variance_shrink_factors_positive_part": shrink.tolist(),
    }

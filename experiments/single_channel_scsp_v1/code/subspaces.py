"""M3: freeze source-contrast and mismatch subspaces; report overlap."""

from __future__ import annotations

import numpy as np


def whiten(D, conf, sigma2=0.16):
    """Whiten by observation covariance: S^{1/2} D, S=diag(conf)/sigma2."""
    w = np.sqrt(np.maximum(conf, 1e-12) / sigma2)
    return D * w[:, None].T if D.ndim == 2 else D * w


def source_contrast_basis(fu, conf_threshold=1e-9):
    """Prior-weighted source contrast D (C x N_keep), whitened."""
    from arms import assignment_from_rects

    g = fu.maps
    assign = assignment_from_rects(fu.candidates, fu.grid_x, fu.grid_y)
    C = g.shape[0]
    pi_cand = np.zeros(C)
    for c in range(C):
        mask = assign == c
        if mask.any():
            pi_cand[c] = fu.prior[mask].sum()
    pi_cand /= pi_cand.sum()
    gbar = pi_cand @ g
    d = g - gbar
    keep = fu.measured_conf > conf_threshold
    D = d[:, keep]
    D = whiten(D, fu.measured_conf[keep])
    return D, keep


def mismatch_basis(atoms, keep, energy_threshold=0.95):
    """Atoms (J x N) -> whitened columns on keep cells, frozen rank by energy."""
    A = atoms[:, keep]
    u, s, vh = np.linalg.svd(A, full_matrices=False)
    cum = np.cumsum(s**2) / np.sum(s**2)
    r = int(np.searchsorted(cum, energy_threshold) + 1)
    r = min(r, A.shape[0], A.shape[1])
    return (vh[:r].T * s[:r]), r, cum


def overlap(D, B):
    """rho = |Q_D^T Q_B|_F^2 / min(rank D, rank B); principal angles."""
    qd, _ = np.linalg.qr(D.T)
    qb, _ = np.linalg.qr(B)
    k = min(qd.shape[1], qb.shape[1])
    if k == 0:
        return 0.0, []
    sv = np.linalg.svd(qd.T @ qb, compute_uv=False)
    angles = np.arccos(np.clip(sv, -1, 1))
    rho = float(np.sum(sv**2)) / k
    return rho, angles


def decompose(B, D):
    """B = B_parallelS + B_perpS (columns orthogonal to span(D))."""
    qd, _ = np.linalg.qr(D.T)
    Bpar = qd @ (qd.T @ B)
    Bperp = B - Bpar
    return Bpar, Bperp

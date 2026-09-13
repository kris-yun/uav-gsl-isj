"""Metric-consistent, rank-revealing source/mismatch subspaces.

The legacy GW-MAIN code whitened source contrasts but not nuisance atoms and
used a full QR basis for a rank-deficient, prior-centred source matrix.  This
module implements the stated covariance geometry without changing the frozen
posterior rule.
"""

from __future__ import annotations

import numpy as np


def whitening_vector(conf: np.ndarray, sigma2: float = 0.16) -> np.ndarray:
    return np.sqrt(np.maximum(np.asarray(conf, dtype=float), 1e-12) / sigma2)


def orthonormal_basis(matrix: np.ndarray) -> tuple[np.ndarray, int]:
    """Return a rank-revealing column-space basis using the LAPACK tolerance."""
    matrix = np.asarray(matrix, dtype=float)
    if matrix.ndim != 2:
        raise ValueError("matrix must be two-dimensional")
    if not matrix.size:
        return np.zeros((matrix.shape[0], 0), dtype=float), 0
    u, s, _ = np.linalg.svd(matrix, full_matrices=False)
    if not s.size or s[0] == 0:
        return np.zeros((matrix.shape[0], 0), dtype=float), 0
    tol = max(matrix.shape) * np.finfo(float).eps * s[0]
    rank = int(np.sum(s > tol))
    return u[:, :rank], rank


def source_contrast_geometry(fu, conf_threshold: float = 1e-9):
    """Return D_w (N_keep x C), its basis/rank, keep mask and W diagonal."""
    from arms import assignment_from_rects

    keep = fu.measured_conf > conf_threshold
    assignment = assignment_from_rects(fu.candidates, fu.grid_x, fu.grid_y)
    candidate_mass = np.array([
        fu.prior[assignment == c].sum() for c in range(len(fu.candidates))
    ], dtype=float)
    candidate_mass /= candidate_mass.sum()
    gbar = candidate_mass @ fu.maps
    d = (fu.maps - gbar)[:, keep].T
    w = whitening_vector(fu.measured_conf[keep])
    d_w = w[:, None] * d
    q_d, rank_d = orthonormal_basis(d_w)
    return d_w, q_d, rank_d, keep, w


def mismatch_geometry(atoms: np.ndarray, keep: np.ndarray, w: np.ndarray,
                      energy_threshold: float = 0.95):
    """Low-rank nuisance basis in whitened and measurement coordinates."""
    a_w = np.asarray(atoms, dtype=float)[:, keep] * w[None, :]
    _, singular, vh = np.linalg.svd(a_w, full_matrices=False)
    if not singular.size or np.sum(singular ** 2) == 0:
        empty = np.zeros((int(np.sum(keep)), 0), dtype=float)
        return empty, empty, 0, np.array([], dtype=float)
    cumulative = np.cumsum(singular ** 2) / np.sum(singular ** 2)
    rank = int(np.searchsorted(cumulative, energy_threshold) + 1)
    rank = min(rank, a_w.shape[0], a_w.shape[1])
    b_w = vh[:rank].T * singular[:rank]
    b_measurement = b_w / w[:, None]
    return b_w, b_measurement, rank, cumulative


def overlap_and_source_safe_projection(q_d: np.ndarray, b_w: np.ndarray,
                                       w: np.ndarray):
    """Project nuisance components away from source span in the W metric."""
    q_b, rank_b = orthonormal_basis(b_w)
    rank_d = q_d.shape[1]
    if rank_d == 0 or rank_b == 0:
        rho = 0.0
    else:
        rho = float(np.sum((q_d.T @ q_b) ** 2) / min(rank_d, rank_b))
    b_perp_w = b_w - q_d @ (q_d.T @ b_w)
    b_perp_measurement = b_perp_w / w[:, None]
    orthogonality = float(np.max(np.abs(q_d.T @ b_perp_w))) if b_perp_w.size else 0.0
    return rho, b_perp_w, b_perp_measurement, orthogonality, rank_b


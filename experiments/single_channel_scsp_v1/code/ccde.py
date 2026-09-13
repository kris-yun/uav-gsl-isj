"""CCDE-PMFS: Candidate-Conditioned Deprojection Evidence.

Inspired by constrained component separation / foreground deprojection in CMB
analysis. For each candidate source s, construct a different minimum-variance
linear filter that:
  1) has unit response to the candidate source-contrast template h_s;
  2) has zero response to source-conditioned nuisance perturbation templates;
  3) minimizes variance under the frozen observation covariance.

No truth is used by inference.
"""
from __future__ import annotations
import math
import numpy as np

SIGMA2 = 0.16
CONF_EPS = 1e-9

def assignment_from_rects(candidates, grid_x, grid_y):
    n = grid_x * grid_y
    a = np.full(n, -1, dtype=np.int64)
    for i, c in enumerate(candidates):
        if not c["valid"]:
            continue
        ox, oy = c["origin"]; sx, sy = c["size"]
        for x in range(ox, ox + sx):
            for y in range(oy, oy + sy):
                a[y * grid_x + x] = i
    if np.any(a < 0):
        # outside candidate support is never used in candidate evidence
        pass
    return a

def load_physical_atoms(path, n_candidates, n_cells):
    arr = np.fromfile(path, dtype="<f4").astype(np.float64)
    expect = n_candidates * 4 * n_cells
    if arr.size != expect:
        raise ValueError(f"atom size mismatch: {arr.size} != {expect}")
    return arr.reshape(n_candidates, 4, n_cells)

def candidate_prior_mass(fu, assignment):
    C = len(fu.candidates)
    p = np.array([fu.prior[assignment == c].sum() for c in range(C)], dtype=float)
    if p.sum() <= 0:
        raise ValueError("zero candidate prior mass")
    return p / p.sum()

def ccde_log_evidence(fu, atoms, modes=(0,1,2,3), include_constant=False):
    keep = fu.measured_conf > CONF_EPS
    conf = np.maximum(fu.measured_conf[keep], CONF_EPS)
    cinv = conf / SIGMA2

    maps = fu.maps[:, keep]
    C = maps.shape[0]
    assignment = assignment_from_rects(fu.candidates, fu.grid_x, fu.grid_y)
    pi = candidate_prior_mass(fu, assignment)
    gbar = pi @ maps
    x = fu.measured_prob[keep] - gbar
    A = atoms[:, :, keep]

    logev = np.full(C, -np.inf)
    diagnostics = []
    for c in range(C):
        h = maps[c] - gbar
        cols = [h]
        for j in modes:
            cols.append(A[c, j])
        if include_constant:
            cols.append(np.ones_like(h))
        M = np.column_stack(cols)

        gram = M.T @ (cinv[:, None] * M)
        gram_inv = np.linalg.pinv(gram, rcond=1e-10)
        e1 = np.zeros(M.shape[1]); e1[0] = 1.0

        # Minimum-variance constrained filter.
        w = cinv * (M @ (gram_inv @ e1))
        source_response = float(w @ h)
        if abs(source_response) < 1e-10:
            diagnostics.append({"candidate": c, "degenerate": True})
            continue
        w = w / source_response

        nuisance_leak = [float(w @ A[c, j]) for j in modes]
        ahat = float(w @ x)
        var = float(np.sum((w*w) * (SIGMA2 / conf)))
        z = ahat / math.sqrt(max(var, 1e-15))

        # One-sided GLRT for a nonnegative target amplitude.
        logev[c] = 0.5 * max(z, 0.0)**2
        diagnostics.append({
            "candidate": c,
            "unit_response": float(w @ h),
            "max_abs_nuisance_leak": max([abs(v) for v in nuisance_leak], default=0.0),
            "ahat": ahat,
            "variance": var,
            "z": z,
            "degenerate": False,
        })
    return logev, diagnostics

def matched_source_log_evidence(fu):
    """Ablation: same candidate-conditioned matched-source filter with no nuisance constraints."""
    C = len(fu.candidates)
    dummy = np.zeros((C,4,fu.n_cells), dtype=float)
    return ccde_log_evidence(fu, dummy, modes=())[0]

def posterior_from_candidate_logev(fu, logev, prior):
    a = assignment_from_rects(fu.candidates, fu.grid_x, fu.grid_y)
    logp = np.full_like(prior, -np.inf, dtype=float)
    valid = fu.occupancy & (a >= 0)
    logp[valid] = np.log(np.maximum(prior[valid], 1e-300)) + logev[a[valid]]
    m = np.max(logp[valid])
    p = np.zeros_like(prior, dtype=float)
    p[valid] = np.exp(logp[valid] - m)
    p /= p.sum()
    return p

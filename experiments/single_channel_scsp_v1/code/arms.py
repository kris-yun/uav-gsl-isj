"""A0–A4 fixed-support arms in log space.

Frozen observation-model contract (no truth leakage, no H01/H03 tuning):
  * Gaussian observation model on confidence-weighted cells:
      log L(s) = -0.5 (y-g_s)^T S (y-g_s),  S = diag(conf)/sigma2
  * sigma2 = 0.16 (sigma=0.4) — frozen config-derived constant.
  * A1 inflates S by factor kappa=4 (covariance inflation only).
  * A2 scalar block-glitch: additive offset b~N(0,tau2), tau=0.3 (frozen scalar
    glitch baseline, no re-tuning; consistent with G0 freeze).
  * A3 unstructured mismatch: b~N(0,lam2 I) in span(B), lam=0.5 (frozen).
  * A4 source-protected: only B_perpS is used, attribution alpha = 1-rho.
"""

from __future__ import annotations

import numpy as np

SIGMA2 = 0.16
KAPPA_A1 = 4.0
TAU_A2 = 0.3
LAM = 0.5
CONF_EPS = 1e-9


def weights(conf: np.ndarray) -> np.ndarray:
    return np.maximum(conf, CONF_EPS)


def log_evidence_quad(s, g_s, y, S):
    """-0.5 (y-g_s)^T S (y-g_s) (constant log-det dropped: same S across s)."""
    r = y - g_s
    return -0.5 * float(r @ (S * r))


def log_evidence_scalar_glitch(s, g_s, y, S, tau2=TAU_A2**2):
    """A2: y = g_s + b*1 + e, b~N(0,tau2). Woodbury."""
    r = y - g_s
    denom = 1.0 / tau2 + float(np.sum(S))
    quad = float(r @ (S * r)) - (float(np.sum(S * r)) ** 2) / denom
    # log det term (constant across s): log|S^{-1} + tau2 11^T|
    logdet = float(np.sum(np.log(1.0 / S))) + np.log(denom) + np.log(tau2)
    return -0.5 * quad - 0.5 * logdet


def log_evidence_structured(s, g_s, y, S, B, lam2=LAM**2):
    """A3/A4: y = g_s + B b + e, b~N(0,lam2 I). Woodbury on rank-r basis."""
    r = y - g_s
    # cov = S^{-1} + lam2 B B^T ; inverse via Woodbury:
    # (S^{-1} + lam2 BB^T)^{-1} = S - S B (lam2^{-1} I + B^T S B)^{-1} B^T S
    SB = S[:, None] * B  # (N, r) S*B (S diagonal)
    H = B.T @ SB  # (r, r)
    M = np.linalg.inv(H + np.eye(H.shape[0]) / lam2)
    quad = float(r @ (S * r)) - float((SB.T @ r) @ M @ (SB.T @ r))
    # log det: log|S^{-1} + lam2 BB^T| = -log|S| + log|I + lam2 B^T S B|
    logdet = -float(np.sum(np.log(S))) + float(
        np.linalg.slogdet(np.eye(H.shape[0]) + lam2 * H)[1]
    )
    return -0.5 * quad - 0.5 * logdet


def posterior_from_logev(log_ev: np.ndarray, prior: np.ndarray, assignment: np.ndarray) -> np.ndarray:
    """Per-cell posterior: prior(cell) * exp(log_ev[candidate(cell)]), normalized."""
    logp = log_ev[assignment] + np.log(np.maximum(prior, 1e-300))
    m = logp.max()
    p = np.exp(logp - m)
    return p / p.sum()


def assignment_from_rects(candidates, grid_x, grid_y):
    n = grid_x * grid_y
    a = np.full(n, -1, dtype=np.int64)
    for i, c in enumerate(candidates):
        if not c["valid"]:
            continue
        ox, oy = c["origin"]
        sx, sy = c["size"]
        for x in range(ox, ox + sx):
            for y in range(oy, oy + sy):
                a[y * grid_x + x] = i
    return a


def run_arms(y, conf, prior, maps, assignment, keep, official_posterior=None,
             internal_official=None, B_full=None, B_perp=None, rho=0.0):
    """Compute the five arms' per-candidate log evidence + posterior.

    maps: (C, N); y/conf/prior: (N,); assignment: (N,) candidate id per cell;
    keep: (N,) bool confidence mask; B_perp: (N_keep, r) or None.
    Returns dict arm -> dict(log_ev, posterior, abstained).
    """
    C, N = maps.shape
    yk = y[keep]
    mk = maps[:, keep]
    Sk = weights(conf[keep]) / SIGMA2
    out = {}
    # A0 native (recomputed from maps is the parity target; here the Gaussian
    # reference for the same support is provided as A0g for comparability; the
    # official native posterior is loaded separately).
    if internal_official is not None and official_posterior is not None:
        log_ev_native = np.array([
            float(np.log(max(np.mean(official_posterior[assignment == c]), 1e-300)))
            if (assignment == c).any() else -np.inf
            for c in range(C)
        ])
        out["A0_native"] = {
            "log_ev": log_ev_native,
            "posterior": official_posterior if official_posterior is not None else prior,
            "abstained": False,
        }
    else:
        out["A0_native"] = {
            "log_ev": None,
            "posterior": official_posterior if official_posterior is not None else prior,
            "abstained": False,
        }
    log_ev_a0 = np.array([log_evidence_quad(i, mk[i], yk, Sk) for i in range(C)])
    out["A0_gauss"] = {
        "log_ev": log_ev_a0,
        "posterior": posterior_from_logev(log_ev_a0, prior, assignment),
        "abstained": False,
    }
    log_ev_a1 = log_ev_a0 / KAPPA_A1
    out["A1_cov_inflate"] = {
        "log_ev": log_ev_a1,
        "posterior": posterior_from_logev(log_ev_a1, prior, assignment),
        "abstained": False,
    }
    log_ev_a2 = np.array(
        [log_evidence_scalar_glitch(i, mk[i], yk, Sk) for i in range(C)]
    )
    out["A2_block_glitch"] = {
        "log_ev": log_ev_a2,
        "posterior": posterior_from_logev(log_ev_a2, prior, assignment),
        "abstained": False,
    }
    if B_full is None or B_full.shape[1] == 0 or rho >= 1.0 - 1e-12:
        # source/mismatch not identifiable -> A4 abstains (keeps prior)
        for arm, Bmat in (("A3_structured", B_full), ("A4_protected", B_perp)):
            if Bmat is None or Bmat.shape[1] == 0:
                out[arm] = {
                    "log_ev": log_ev_a0,
                    "posterior": prior.copy(),
                    "abstained": True,
                }
            else:
                log_ev = np.array(
                    [log_evidence_structured(i, mk[i], yk, Sk, Bmat) for i in range(C)]
                )
                out[arm] = {
                    "log_ev": log_ev,
                    "posterior": posterior_from_logev(log_ev, prior, assignment),
                    "abstained": False,
                }
        return out
    # A3: full mismatch basis (unprotected — glitch may absorb source contrast)
    log_ev_a3 = np.array(
        [log_evidence_structured(i, mk[i], yk, Sk, B_full) for i in range(C)]
    )
    out["A3_structured"] = {
        "log_ev": log_ev_a3,
        "posterior": posterior_from_logev(log_ev_a3, prior, assignment),
        "abstained": False,
    }
    # A4: source-protected — structured evidence on B_perp only, then
    # attribution-weighted handling of the overlap fraction.
    alpha = 1.0 - rho
    log_ev_a4 = np.array(
        [log_evidence_structured(i, mk[i], yk, Sk, B_perp) for i in range(C)]
    )
    # Primary formulation (mechanism reading of "rho->0 uses remaining source
    # evidence normally"): evidence-level blend of protected structured
    # evidence with the native Gaussian evidence.
    log_ev_a4e = alpha * log_ev_a4 + (1.0 - alpha) * log_ev_a0
    p4e = posterior_from_logev(log_ev_a4e, prior, assignment)
    out["A4_protected_evidence"] = {
        "log_ev": log_ev_a4e,
        "posterior": p4e,
        "abstained": False,
        "alpha": alpha,
        "rho": rho,
    }
    # Alternative: posterior-level blend with the prior (safety/dilution).
    p_structured = posterior_from_logev(log_ev_a4, prior, assignment)
    p4 = alpha * p_structured + (1.0 - alpha) * prior
    out["A4_protected"] = {
        "log_ev": log_ev_a4,
        "posterior": p4,
        "abstained": False,
        "alpha": alpha,
        "rho": rho,
    }
    return out

#!/usr/bin/env python3
"""Completeness/identifiability gate for CG-PC-CTT.

Input per decision context:
    phi[s, m, d]
where s indexes candidate sources, m transport members, and d response features.

The gate deliberately avoids inverting a high-dimensional dxd covariance.
It projects transport residuals into the low-dimensional source-contrast
subspace first (dimension <= S-1), estimates transport covariance there,
then whitens source contrasts.

Outputs:
    gamma = sigma_min / sigma_max   (relative conditioning)
    alpha = sigma_min               (absolute weakest whitened source strength)
    beta  = minimum pairwise whitened candidate separation (diagnostic)
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional
import numpy as np


@dataclass(frozen=True)
class GateConfig:
    gamma_min: float = 0.05
    alpha_min: float = 1.0
    beta_min: Optional[float] = None
    ridge_rel: float = 1e-3
    eig_floor: float = 1e-9

    def validate(self) -> None:
        if self.gamma_min < 0:
            raise ValueError("gamma_min must be >= 0")
        if self.alpha_min < 0:
            raise ValueError("alpha_min must be >= 0")
        if self.beta_min is not None and self.beta_min < 0:
            raise ValueError("beta_min must be >= 0")
        if self.ridge_rel < 0:
            raise ValueError("ridge_rel must be >= 0")
        if self.eig_floor <= 0:
            raise ValueError("eig_floor must be > 0")


@dataclass(frozen=True)
class GateResult:
    gamma: float
    alpha: float
    beta: float
    sigma_max: float
    sigma_min: float
    numerical_rank: int
    target_rank: int
    accepted: bool
    reason: str
    ridge: float

    def to_dict(self):
        return asdict(self)


def _as_finite_3d(phi: np.ndarray) -> np.ndarray:
    x = np.asarray(phi, dtype=np.float64)
    if x.ndim != 3:
        raise ValueError(f"phi must have shape [S,M,D], got {x.shape}")
    s, m, d = x.shape
    if s < 2 or m < 2 or d < 1:
        raise ValueError(f"need S>=2, M>=2, D>=1, got {x.shape}")
    if not np.all(np.isfinite(x)):
        raise ValueError("phi contains NaN or Inf")
    return x


def compute_gate(phi: np.ndarray, cfg: GateConfig = GateConfig()) -> GateResult:
    cfg.validate()
    x = _as_finite_3d(phi)
    S, M, D = x.shape
    target_rank = min(S - 1, D)

    # Candidate means and centered source contrasts.
    mu = x.mean(axis=1)                      # [S,D]
    B = mu - mu.mean(axis=0, keepdims=True)  # [S,D]

    # Source-contrast basis. We only need dimensions that source differences occupy.
    _, svals_raw, vt = np.linalg.svd(B, full_matrices=False)
    if len(svals_raw) == 0 or svals_raw[0] <= cfg.eig_floor:
        return GateResult(
            gamma=0.0, alpha=0.0, beta=0.0, sigma_max=0.0, sigma_min=0.0,
            numerical_rank=0, target_rank=target_rank, accepted=False,
            reason="NO_SOURCE_CONTRAST", ridge=cfg.eig_floor
        )
    Q = vt[:target_rank].T  # [D,r]

    # Transport-member residuals, pooled over candidate sources.
    resid = x - mu[:, None, :]              # [S,M,D]
    R = resid.reshape(S * M, D) @ Q          # [S*M,r]

    # Low-rank transport covariance. Ridge is scale-relative and deterministic.
    denom = max(R.shape[0] - 1, 1)
    C = (R.T @ R) / denom
    scale = float(np.trace(C) / max(target_rank, 1))
    ridge = max(cfg.eig_floor, cfg.ridge_rel * max(scale, cfg.eig_floor))
    C_reg = C + ridge * np.eye(target_rank)

    # Symmetric inverse square root.
    evals, evecs = np.linalg.eigh(C_reg)
    evals = np.maximum(evals, cfg.eig_floor)
    C_inv_sqrt = (evecs * (1.0 / np.sqrt(evals))) @ evecs.T

    B_low = B @ Q                            # [S,r]
    B_white = B_low @ C_inv_sqrt             # [S,r]
    sw = np.linalg.svd(B_white, compute_uv=False)
    sigma_max = float(sw[0]) if len(sw) else 0.0
    sigma_min = float(sw[target_rank - 1]) if len(sw) >= target_rank else 0.0
    numerical_rank = int(np.sum(sw > max(cfg.eig_floor, sigma_max * 1e-8)))
    gamma = float(sigma_min / sigma_max) if sigma_max > cfg.eig_floor else 0.0
    alpha = sigma_min

    # Pairwise hard-negative diagnostic in whitened source space.
    beta = np.inf
    for i in range(S):
        for j in range(i + 1, S):
            beta = min(beta, float(np.linalg.norm(B_white[i] - B_white[j])))
    if not np.isfinite(beta):
        beta = 0.0

    reasons = []
    if numerical_rank < target_rank:
        reasons.append("RANK")
    if gamma < cfg.gamma_min:
        reasons.append("GAMMA")
    if alpha < cfg.alpha_min:
        reasons.append("ALPHA")
    if cfg.beta_min is not None and beta < cfg.beta_min:
        reasons.append("BETA")

    accepted = not reasons
    return GateResult(
        gamma=gamma,
        alpha=alpha,
        beta=beta,
        sigma_max=sigma_max,
        sigma_min=sigma_min,
        numerical_rank=numerical_rank,
        target_rank=target_rank,
        accepted=accepted,
        reason="PASS" if accepted else "+".join(reasons),
        ridge=ridge,
    )


def no_update_posterior(previous_q: np.ndarray) -> np.ndarray:
    """Exact ABSTAIN contract: rejected gate cannot sharpen or move posterior."""
    q = np.asarray(previous_q, dtype=np.float64)
    if q.ndim != 1 or q.size < 2 or np.any(q < 0) or not np.all(np.isfinite(q)):
        raise ValueError("previous_q must be a finite nonnegative 1-D probability vector")
    z = q.sum()
    if z <= 0:
        raise ValueError("previous_q must have positive mass")
    return (q / z).copy()

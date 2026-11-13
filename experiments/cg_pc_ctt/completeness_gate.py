#!/usr/bin/env python3
"""CG-PC-CTT V2 replicated-completeness gate.

Why V1 is invalid
-----------------
V1 formed a full-member candidate mean and whitened it by transport-member
residual covariance. With only M=8 members, the source mean contains finite-M
noise O(M^-1/2). Under a true source-null this can still produce rank 3 and a
raw alpha around one. Raising alpha_min would only hide the bias.

V2 statistic
------------
Assume, ONLY in inferential mode,
    phi[s,m,d] = mu[s,d] + eps[s,m,d]
where transport members m are independent/exchangeable realizations around a
stable candidate response mu. We never square a noisy sample mean. Instead we
build a cross-member U-statistic whose nuisance-noise cross terms have zero
expectation.

1) Estimate per-feature member-noise scale without using a source mean:
   v[d] = mean_{s,m<n} (phi[s,m,d]-phi[s,n,d])^2 / 2.
2) Whiten each feature by sqrt(v[d]+ridge).
3) Center candidates separately inside every member, C_m = P_S Phi_m W.
4) Stable source operator in feature space:
       K = sum_{m!=n} C_m^T C_n / (M(M-1)S)
     = ((sum_m C_m)^T(sum_m C_m)-sum_m C_m^T C_m)/(M(M-1)S).
   E[K] is the stable between-source contrast Gram under exchangeable member
   noise; unlike V1 it contains no same-member mean-noise square.
5) Let lambda_1 >= ... be eigenvalues of symmetric K. For rank_k=3:
       alpha_cf = sqrt(max(lambda_3,0))
       gamma_cf = sqrt(max(lambda_3,0)/max(lambda_1,eps)).
6) Exact member sign-flip test: multiply the whole source-contrast matrix C_m
   by +/-1. Fix the first sign +1 (global sign is redundant), enumerate all
   2^(M-1) patterns for M<=16, and test lambda_3. With M=8 the minimum exact
   p-value is 1/128 = 0.0078125, so p_max=0.01 is pre-registered.

Important semantics
-------------------
The sign-flip p-value is inferential only if M1 transport members are genuinely
exchangeable/random realizations and the member deviations are sign-symmetric
under the no-stable-source-contrast null. If the eight members are a fixed
nuisance/quadrature design, this code returns inferential_valid=False and MUST
NOT release a source update. Fixed-design members require a separate robust-set
qualification; do not relabel them as random samples.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from itertools import product
import numpy as np


@dataclass(frozen=True)
class GateConfig:
    gamma_min: float = 0.05
    p_max: float = 0.01
    rank_k: int = 3
    ridge_rel: float = 1e-3
    eig_floor: float = 1e-9
    exact_signflip_max_members: int = 16
    member_semantics: str = "UNDECLARED"

    def validate(self) -> None:
        if self.gamma_min < 0:
            raise ValueError("gamma_min must be >= 0")
        if not (0 < self.p_max < 1):
            raise ValueError("p_max must be in (0,1)")
        if self.rank_k < 1:
            raise ValueError("rank_k must be >=1")
        if self.ridge_rel < 0 or self.eig_floor <= 0:
            raise ValueError("invalid regularization")
        if self.member_semantics not in {
            "exchangeable_realizations", "fixed_nuisance_design", "UNDECLARED"
        }:
            raise ValueError("invalid member_semantics")


@dataclass(frozen=True)
class GateResult:
    alpha_cf: float
    gamma_cf: float
    lambda_1: float
    lambda_k: float
    p_signflip: float
    null_patterns: int
    target_rank: int
    n_members: int
    accepted: bool
    inferential_valid: bool
    reason: str
    ridge: float
    member_semantics: str

    def to_dict(self):
        return asdict(self)


def _finite_phi(phi: np.ndarray) -> np.ndarray:
    x = np.asarray(phi, dtype=np.float64)
    if x.ndim != 3:
        raise ValueError(f"phi must be [S,M,D], got {x.shape}")
    S, M, D = x.shape
    if S < 4 or M < 4 or D < 3:
        raise ValueError(f"V2 requires S>=4,M>=4,D>=3; got {x.shape}")
    if not np.all(np.isfinite(x)):
        raise ValueError("phi contains NaN/Inf")
    return x


def _member_noise_scale(x: np.ndarray, cfg: GateConfig):
    """Pair-difference estimate of per-feature member noise variance."""
    S, M, D = x.shape
    ss = np.zeros(D, dtype=np.float64)
    n = 0
    for m in range(M):
        for h in range(m + 1, M):
            diff = x[:, m, :] - x[:, h, :]
            ss += np.sum(0.5 * diff * diff, axis=0)
            n += S
    v = ss / max(n, 1)
    scale = float(np.mean(v))
    ridge = max(cfg.eig_floor, cfg.ridge_rel * max(scale, cfg.eig_floor))
    return v, ridge


def _centered_whitened_members(x: np.ndarray, cfg: GateConfig):
    v, ridge = _member_noise_scale(x, cfg)
    w = 1.0 / np.sqrt(v + ridge)
    # [M,S,D]
    C = np.transpose(x, (1, 0, 2)) * w[None, None, :]
    C = C - C.mean(axis=1, keepdims=True)
    return C, ridge


def _operator_from_signs(C: np.ndarray, signs: np.ndarray):
    """Cross-member stable source operator K in feature space."""
    M, S, D = C.shape
    Cs = C * signs[:, None, None]
    total = Cs.sum(axis=0)  # [S,D]
    # sign^2=1, so self term is unchanged by sign flipping.
    self_term = np.zeros((D, D), dtype=np.float64)
    for m in range(M):
        self_term += C[m].T @ C[m]
    K = (total.T @ total - self_term) / float(M * (M - 1) * S)
    return 0.5 * (K + K.T)


def _eig_stats(C: np.ndarray, signs: np.ndarray, rank_k: int, eps: float):
    K = _operator_from_signs(C, signs)
    ev = np.linalg.eigvalsh(K)[::-1]
    lambda_1 = float(ev[0])
    lambda_k = float(ev[rank_k - 1])
    pos_k = max(lambda_k, 0.0)
    alpha_cf = float(np.sqrt(pos_k))
    gamma_cf = float(np.sqrt(pos_k / max(lambda_1, eps)))
    return lambda_1, lambda_k, alpha_cf, gamma_cf


def _exact_signflip_p(C: np.ndarray, observed_lambda_k: float, cfg: GateConfig):
    M = C.shape[0]
    if M > cfg.exact_signflip_max_members:
        raise ValueError(
            f"M={M} exceeds exact sign-flip limit {cfg.exact_signflip_max_members}; "
            "V2 forbids silently switching to a Monte-Carlo p-value"
        )
    # Global sign is redundant for pair products; fix member 0 to +1.
    null = []
    for tail in product((-1.0, 1.0), repeat=M - 1):
        signs = np.asarray((1.0,) + tail, dtype=np.float64)
        _, lk, _, _ = _eig_stats(C, signs, cfg.rank_k, cfg.eig_floor)
        null.append(lk)
    null = np.asarray(null, dtype=np.float64)
    # Exact randomization p-value; identity pattern is present in null.
    p = float(np.mean(null >= observed_lambda_k - 1e-12))
    return p, int(null.size)


def compute_gate(phi: np.ndarray, cfg: GateConfig = GateConfig()) -> GateResult:
    cfg.validate()
    x = _finite_phi(phi)
    S, M, D = x.shape
    target_rank = min(cfg.rank_k, S - 1, D)
    if target_rank != cfg.rank_k:
        return GateResult(
            0.0, 0.0, 0.0, 0.0, 1.0, 0, target_rank, M,
            False, False, "INSUFFICIENT_SOURCE_DIMENSION", cfg.eig_floor,
            cfg.member_semantics,
        )

    C, ridge = _centered_whitened_members(x, cfg)
    identity = np.ones(M, dtype=np.float64)
    l1, lk, alpha_cf, gamma_cf = _eig_stats(
        C, identity, cfg.rank_k, cfg.eig_floor
    )
    p_signflip, null_patterns = _exact_signflip_p(C, lk, cfg)

    inferential_valid = cfg.member_semantics == "exchangeable_realizations"
    reasons = []
    if cfg.member_semantics == "UNDECLARED":
        reasons.append("MEMBER_SEMANTICS_UNDECLARED")
    elif not inferential_valid:
        reasons.append("FIXED_DESIGN_REQUIRES_ROBUST_SET_PROTOCOL")
    if lk <= 0:
        reasons.append("NONPOSITIVE_REPLICATED_RANK_K")
    if gamma_cf < cfg.gamma_min:
        reasons.append("GAMMA_CF")
    if p_signflip > cfg.p_max:
        reasons.append("SIGNFLIP_NULL")

    accepted = not reasons
    return GateResult(
        alpha_cf, gamma_cf, l1, lk, p_signflip, null_patterns,
        target_rank, M, accepted, inferential_valid,
        "PASS" if accepted else "+".join(reasons), ridge,
        cfg.member_semantics,
    )


def no_update_posterior(previous_q: np.ndarray) -> np.ndarray:
    """Exact ABSTAIN contract: rejected evidence cannot alter q."""
    q = np.asarray(previous_q, dtype=np.float64)
    if q.ndim != 1 or q.size < 2 or np.any(q < 0) or not np.all(np.isfinite(q)):
        raise ValueError("invalid posterior")
    z = q.sum()
    if z <= 0:
        raise ValueError("posterior must have positive mass")
    return (q / z).copy()

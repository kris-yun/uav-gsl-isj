"""Normalized route-law scoring shared by M2 and M1.

The M2 route law exposes a mean and scale for each future sensor step.  This
module turns those heads into an explicitly normalized *innovation* law before
M1 consumes it.  It is not an independent per-step product: consecutive valid
steps use a declared AR(1) residual, while an invalid frame contributes no
factor and resets the local innovation chain.  A valid zero remains an
ordinary observation.
"""
from __future__ import annotations

import math
from typing import Sequence

import torch

from .conditional_evidence import ConditionalEvidence, estimate_conditional_evidence


def _check_rho(rho: float) -> float:
    rho = float(rho)
    if not math.isfinite(rho) or not -1.0 < rho < 1.0:
        raise ValueError("PICR_ROUTE_RHO")
    return rho


def innovation_loglik(values: torch.Tensor, mean: torch.Tensor, scale: torch.Tensor,
                      valid: torch.Tensor, rho: float = 0.0) -> torch.Tensor:
    """Return one normalized joint log score for one route observation block."""
    rho = _check_rho(rho)
    for x, name in ((values, "VALUES"), (mean, "MEAN"), (scale, "SCALE")):
        if x.ndim != 1 or not torch.isfinite(x).all():
            raise ValueError("PICR_ROUTE_" + name)
    if values.shape != mean.shape or values.shape != scale.shape:
        raise ValueError("PICR_ROUTE_SHAPE")
    if valid.ndim != 1 or valid.shape != values.shape or valid.dtype is not torch.bool:
        raise ValueError("PICR_ROUTE_VALID")
    if torch.any(scale <= 0):
        raise ValueError("PICR_ROUTE_SCALE")
    if not bool(valid.any()):
        # No valid observation is a neutral factor, not a fabricated zero gas.
        return values.new_zeros(())
    log2pi = math.log(2.0 * math.pi)
    total = values.new_zeros(())
    previous = None
    for i in range(values.numel()):
        if not bool(valid[i]):
            previous = None
            continue
        if previous is None:
            residual = values[i] - mean[i]
            sigma = scale[i]
        else:
            residual = (values[i] - mean[i]) - rho * (values[previous] - mean[previous])
            sigma = scale[i]
        total = total - 0.5 * (log2pi + 2.0 * torch.log(sigma) + (residual / sigma) ** 2)
        previous = i
    return total


def score_route_laws(candidate_laws, context_laws, observed_logppm: Sequence[float],
                     valid: Sequence[bool] | torch.Tensor, *, rho: float = 0.0,
                     prior_logprob: torch.Tensor | None = None,
                     candidate_valid: torch.Tensor | None = None) -> ConditionalEvidence:
    """Score one candidate/context pair and return the M1 conditional posterior.

    ``context_laws`` must be produced by the same route-law implementation with
    source response masked, one law per candidate.  It is deliberately supplied as a separate law so
    an audit can bind both manifests and reject a hidden candidate shortcut.
    """
    values = torch.as_tensor(observed_logppm, dtype=torch.float32)
    valid_t = torch.as_tensor(valid, dtype=torch.bool)
    if values.ndim != 1:
        raise ValueError("PICR_ROUTE_OBSERVATION_SHAPE")
    if len(candidate_laws) != len(context_laws) or not candidate_laws:
        raise ValueError("PICR_ROUTE_CANDIDATE_COUNT")
    def law_tensors(law):
        mean = torch.as_tensor(law.logppm_mean, dtype=values.dtype)
        scale = torch.as_tensor(law.logppm_scale, dtype=values.dtype)
        if mean.shape != values.shape or scale.shape != values.shape:
            raise ValueError("PICR_ROUTE_LAW_HORIZON")
        return mean, scale
    source_scores = []
    context_scores = []
    for candidate_law, context_law in zip(candidate_laws, context_laws):
        candidate_mean, candidate_scale = law_tensors(candidate_law)
        context_mean, context_scale = law_tensors(context_law)
        source_scores.append(innovation_loglik(values, candidate_mean, candidate_scale, valid_t, rho))
        context_scores.append(innovation_loglik(values, context_mean, context_scale, valid_t, rho))
    source_loglik = torch.stack(source_scores)
    context_loglik = torch.stack(context_scores)
    return estimate_conditional_evidence(
        source_loglik, context_loglik,
        prior_logprob=prior_logprob,
        candidate_valid=candidate_valid,
        observation_valid=bool(valid_t.any()),
    )

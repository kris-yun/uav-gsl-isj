"""PICR conditional-incremental evidence estimator.

This is the smallest executable M1 mechanism candidate. It estimates source
evidence as a likelihood ratio against a candidate-conditioned, gas-free
context law. The context law can encode pose/geometry/wind/sensor nuisance but
must not inspect gas, source truth, future frames or a deployment bank.

Unlike the frozen PICR encoder, this module does not learn a posterior directly.
It is intentionally a pure, auditable score transform so an offline gate can
test the estimand and destructive controls before a neural implementation.
"""
from __future__ import annotations

from dataclasses import dataclass
import torch


@dataclass(frozen=True)
class ConditionalEvidence:
    log_ratio: torch.Tensor
    posterior: torch.Tensor
    valid: torch.Tensor


def _check_vector(value: torch.Tensor, name: str) -> None:
    if value.ndim != 1 or value.numel() < 1 or not torch.isfinite(value).all():
        raise ValueError("PICR_CIE_" + name)


def estimate_conditional_evidence(
    source_loglik: torch.Tensor,
    context_loglik: torch.Tensor,
    prior_logprob: torch.Tensor | None = None,
    candidate_valid: torch.Tensor | None = None,
    observation_valid: bool = True,
) -> ConditionalEvidence:
    """Compute `log p(Y|S=s,N) - log p(Y|N)` as candidate residual evidence.

    `source_loglik` is a candidate-specific log score from the shared causal
    observation law. `context_loglik` is produced by the same law with the
    source/gas response masked, retaining only nuisance context. Subtracting it
    removes candidate-only context preference. A common context constant would
    cancel in ordinary Bayes; a candidate-varying context term is precisely the
    shortcut this estimator guards against, making the distinction testable.

    If no valid observation exists, no evidence is accumulated and the prior is
    returned. This is distinct from a valid zero gas measurement, which must be
    scored by the observation law and therefore passes `observation_valid=True`.
    """
    _check_vector(source_loglik, "SOURCE_SHAPE")
    _check_vector(context_loglik, "CONTEXT_SHAPE")
    if source_loglik.shape != context_loglik.shape:
        raise ValueError("PICR_CIE_LIKELIHOOD_SHAPE")
    count = source_loglik.numel()
    if candidate_valid is None:
        candidate_valid = torch.ones(count, dtype=torch.bool, device=source_loglik.device)
    if candidate_valid.shape != (count,) or candidate_valid.dtype is not torch.bool:
        raise ValueError("PICR_CIE_CANDIDATE_MASK")
    if not bool(candidate_valid.any()):
        raise ValueError("PICR_CIE_NO_VALID_CANDIDATE")
    if prior_logprob is None:
        prior_logprob = torch.zeros_like(source_loglik)
    _check_vector(prior_logprob, "PRIOR_SHAPE")
    if prior_logprob.shape != (count,):
        raise ValueError("PICR_CIE_PRIOR_SHAPE")
    if not torch.isfinite(prior_logprob).all():
        raise ValueError("PICR_CIE_PRIOR_NONFINITE")
    valid = torch.tensor(bool(observation_valid), dtype=torch.bool, device=source_loglik.device)
    ratio = source_loglik - context_loglik if bool(valid) else torch.zeros_like(source_loglik)
    ratio = torch.where(candidate_valid, ratio, torch.full_like(ratio, -torch.inf))
    logits = prior_logprob + ratio
    logits = torch.where(candidate_valid, logits, torch.full_like(logits, -torch.inf))
    posterior = torch.softmax(logits, dim=0)
    if not torch.isfinite(posterior).all() or not torch.isclose(
        posterior.sum(), torch.ones((), device=posterior.device), atol=1e-6
    ):
        raise ValueError("PICR_CIE_POSTERIOR_NUMERIC")
    return ConditionalEvidence(ratio, posterior, valid)


def nuisance_permutation_invariance(
    source_loglik: torch.Tensor,
    context_loglik: torch.Tensor,
    nuisance_permutation: torch.Tensor,
) -> torch.Tensor:
    """Diagnostic: residual source evidence after a nuisance-only permutation.

    The caller must construct the permuted context law without changing source
    candidate order. This function only checks the score residual and cannot
    certify the intervention itself.
    """
    if nuisance_permutation.ndim != 1 or nuisance_permutation.dtype is not torch.long:
        raise ValueError("PICR_CIE_PERMUTATION_SHAPE")
    if nuisance_permutation.numel() != source_loglik.numel():
        raise ValueError("PICR_CIE_PERMUTATION_LENGTH")
    return estimate_conditional_evidence(
        source_loglik, context_loglik[nuisance_permutation],
        observation_valid=True,
    ).posterior

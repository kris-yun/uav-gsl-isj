"""Source-conditional, same-information projection of a finite teacher bank.

The bank is a *training* object.  It must not contain the held-out episode's
future wind, and a plume state generated at one source is not an exogenous
world that may be reused at every candidate source.  Each atom is a normalized
causal joint observation model.  This module never treats an averaged
log-likelihood as a mixture likelihood.

``derivative_valid`` is an explicit qualification flag, not an autodiff test.
Autodiff through a sampled hard branch can silently return the wrong physical
derivative.  Such a bank may use endpoint contrasts, but cannot request scores
or a source-path integral until a valid boundary/weak derivative is supplied.

Known identities used here: finite Bayesian filtering, the log-sum-exp mixture
identity, Fisher's identity, and the fundamental theorem for line integrals.
Their source-conditional composition is a research operator; these identities
are not claimed to be newly invented.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Sequence

import numpy as np
import torch


class ProjectionQualificationError(RuntimeError):
    """A derivative or conditional distribution lacks required qualification."""


@dataclass
class EvidenceProjection:
    log_prob: torch.Tensor
    score: torch.Tensor | None
    history_weights: torch.Tensor
    full_weights: torch.Tensor
    history_ess: torch.Tensor
    full_ess: torch.Tensor
    status: str

    def as_record(self) -> dict[str, Any]:
        def number(value: torch.Tensor) -> float:
            return float(value.detach().cpu())

        return {
            "log_prob": number(self.log_prob),
            "score": None if self.score is None else self.score.detach().cpu().tolist(),
            "history_weights": self.history_weights.detach().cpu().tolist(),
            "full_weights": self.full_weights.detach().cpu().tolist(),
            "history_ess": number(self.history_ess),
            "full_ess": number(self.full_ess),
            "status": self.status,
            "scope": "finite_training_bank; not a native-physics certificate",
        }


@dataclass
class LineIntegralResult:
    integral: torch.Tensor
    endpoint: torch.Tensor
    defect: torch.Tensor
    min_ess: torch.Tensor
    order: int
    status: str

    def as_record(self) -> dict[str, Any]:
        return {
            "integral": float(self.integral.detach().cpu()),
            "endpoint": float(self.endpoint.detach().cpu()),
            "quadrature_defect": float(self.defect.detach().cpu()),
            "min_ess": float(self.min_ess.detach().cpu()),
            "quadrature_order": self.order,
            "status": self.status,
            "scope": "numeric consistency under declared regularity; not ranking proof",
        }


class ConditionalEvidenceProjector:
    """Project a privileged teacher to legal local history, then differentiate.

    Parameters
    ----------
    atom_log_prob:
        ``(history, source_tensor, mechanism) -> Tensor[K]``.  Its k-th value is
        log p_k(history | source, mechanism), conditional on the actions stored
        in the history.  A fixed atom has causal consistency across prefixes.
    log_prior:
        ``source_tensor -> Tensor[K]``.  Normalized log prior or unnormalized
        log prior weights.  Log-softmax normalization preserves its source
        derivative.  The prior must not depend on the realized future.
    derivative_valid:
        Explicit caller assertion of a smooth, fixed-support bank or a correct
        custom weak derivative.  Defaults to False, which blocks score methods.
    min_ess:
        A diagnostic threshold for finite-bank concentration.  ESS is not a
        posterior calibration bound and a high ESS cannot certify correctness.
    domain_validator:
        Optional source-domain check.  A line integral checks endpoints and
        quadrature nodes; this is not a proof that its entire path is legal.

    ``pair_endpoint(H, Y, a, b)`` returns log p(Y|H,b)-log p(Y|H,a).
    The line integral has exactly this orientation, a -> b.
    """

    def __init__(
        self,
        atom_log_prob: Callable[[Sequence[Any], torch.Tensor, Any], torch.Tensor],
        log_prior: Callable[[torch.Tensor], torch.Tensor],
        *,
        derivative_valid: bool = False,
        min_ess: float = 1.0,
        domain_validator: Callable[[torch.Tensor], bool] | None = None,
    ) -> None:
        if min_ess < 1.0:
            raise ValueError("min_ess must be at least one")
        self.atom_log_prob = atom_log_prob
        self.log_prior = log_prior
        self.derivative_valid = bool(derivative_valid)
        self.min_ess = float(min_ess)
        self.domain_validator = domain_validator

    def _source(self, source: Any, *, gradient: bool = False) -> torch.Tensor:
        if isinstance(source, torch.Tensor):
            result = source
            if not result.is_floating_point():
                result = result.to(torch.float64)
        else:
            result = torch.as_tensor(source, dtype=torch.float64)
        if result.ndim != 1 or result.numel() < 1:
            raise ValueError("source must be a nonempty coordinate vector")
        if not bool(torch.isfinite(result).all()):
            raise ValueError("source must have finite coordinates")
        if self.domain_validator is not None and not bool(self.domain_validator(result)):
            raise ProjectionQualificationError("BLOCKED: source/path node is outside the qualified domain")
        if gradient and not result.requires_grad:
            result = result.detach().clone().requires_grad_(True)
        return result

    @staticmethod
    def _valid_log_vector(value: torch.Tensor, name: str) -> None:
        if value.ndim != 1 or value.numel() < 1:
            raise ValueError(f"{name} must be a nonempty vector")
        if bool(torch.isnan(value).any()) or bool(torch.isposinf(value).any()):
            raise ValueError(f"{name} contains NaN or positive infinity")

    def _prior(self, source: torch.Tensor) -> torch.Tensor:
        raw = self.log_prior(source)
        if not isinstance(raw, torch.Tensor):
            raw = torch.as_tensor(raw, dtype=source.dtype, device=source.device)
        else:
            raw = raw.to(dtype=source.dtype, device=source.device)
        self._valid_log_vector(raw, "log_prior")
        if not bool(torch.isfinite(raw).any()):
            raise ProjectionQualificationError("BLOCKED: prior has no positive-mass atom")
        # This is differentiable also for a source-dependent latent prior.
        return torch.log_softmax(raw, dim=0)

    def _atom_values(
        self,
        history: Sequence[Any],
        source: torch.Tensor,
        mechanism: Any,
        prior: torch.Tensor,
    ) -> torch.Tensor:
        if len(history) == 0:
            return torch.zeros_like(prior)
        value = self.atom_log_prob(history, source, mechanism)
        if not isinstance(value, torch.Tensor):
            value = torch.as_tensor(value, dtype=source.dtype, device=source.device)
        else:
            value = value.to(dtype=source.dtype, device=source.device)
        self._valid_log_vector(value, "atom_log_prob")
        if value.shape != prior.shape:
            raise ValueError("atom bank size and prior size disagree")
        return value

    def marginal_log_prob(self, history: Sequence[Any], source: Any, mechanism: Any = None) -> torch.Tensor:
        s = self._source(source)
        prior = self._prior(s)
        atom = self._atom_values(history, s, mechanism, prior)
        return torch.logsumexp(prior + atom, dim=0)

    def posterior_weights(self, history: Sequence[Any], source: Any, mechanism: Any = None) -> torch.Tensor:
        s = self._source(source)
        prior = self._prior(s)
        log_weight = prior + self._atom_values(history, s, mechanism, prior)
        if not bool(torch.isfinite(torch.logsumexp(log_weight, dim=0))):
            raise ProjectionQualificationError("BLOCKED: history has zero support under every atom")
        return torch.softmax(log_weight, dim=0)

    def conditional_log_prob(
        self,
        history: Sequence[Any],
        future: Sequence[Any],
        source: Any,
        mechanism: Any = None,
    ) -> torch.Tensor:
        s = self._source(source)
        prior = self._prior(s)
        lh = torch.logsumexp(prior + self._atom_values(history, s, mechanism, prior), dim=0)
        if not bool(torch.isfinite(lh)):
            raise ProjectionQualificationError("BLOCKED: cannot condition on zero-support history")
        if len(future) == 0:
            return s.sum() * 0.0
        combined = list(history) + list(future)
        lhy = torch.logsumexp(prior + self._atom_values(combined, s, mechanism, prior), dim=0)
        # A zero-probability future is a legitimate value (-inf).  Its score is
        # undefined, and project(with_score=True) will reject it explicitly.
        return lhy - lh

    def project(
        self,
        history: Sequence[Any],
        future: Sequence[Any],
        source: Any,
        mechanism: Any = None,
        *,
        with_score: bool = True,
        create_graph: bool = False,
    ) -> EvidenceProjection:
        if with_score and not self.derivative_valid:
            raise ProjectionQualificationError(
                "BLOCKED: source derivative is not qualified; use endpoint contrasts "
                "or provide a valid smooth/weak boundary derivative"
            )
        s = self._source(source, gradient=with_score)
        prior = self._prior(s)
        joint_h = prior + self._atom_values(history, s, mechanism, prior)
        lh = torch.logsumexp(joint_h, dim=0)
        if not bool(torch.isfinite(lh)):
            raise ProjectionQualificationError("BLOCKED: cannot condition on zero-support history")
        joint_hy = prior + self._atom_values(list(history) + list(future), s, mechanism, prior)
        lhy = torch.logsumexp(joint_hy, dim=0)
        if not bool(torch.isfinite(lhy)):
            raise ProjectionQualificationError("BLOCKED: future has zero support; its source score is undefined")
        bh = torch.softmax(joint_h, dim=0)
        bhy = torch.softmax(joint_hy, dim=0)
        value = lhy - lh + s.sum() * 0.0
        score = None
        if with_score:
            score = torch.autograd.grad(value, s, create_graph=create_graph, retain_graph=True)[0]
            if not bool(torch.isfinite(score).all()):
                raise ProjectionQualificationError(
                    "BLOCKED: non-finite source derivative; check support and boundary qualification"
                )
        eh = 1.0 / bh.square().sum()
        ehy = 1.0 / bhy.square().sum()
        status = "LOW_ESS" if float(torch.minimum(eh, ehy).detach()) < self.min_ess else "OK_FINITE_BANK"
        return EvidenceProjection(value, score, bh, bhy, eh, ehy, status)

    def score(
        self,
        history: Sequence[Any],
        future: Sequence[Any],
        source: Any,
        mechanism: Any = None,
        *,
        create_graph: bool = False,
    ) -> torch.Tensor:
        result = self.project(history, future, source, mechanism, create_graph=create_graph)
        assert result.score is not None  # guaranteed by with_score=True
        return result.score

    def pair_endpoint(
        self,
        history: Sequence[Any],
        future: Sequence[Any],
        source_a: Any,
        source_b: Any,
        mechanism: Any = None,
    ) -> torch.Tensor:
        """Finite candidate contrast log p_b - log p_a; no derivative assumed."""
        a, b = self._source(source_a), self._source(source_b)
        if a.shape != b.shape:
            raise ValueError("source endpoints must have equal dimensions")
        left = self.conditional_log_prob(history, future, a, mechanism)
        right = self.conditional_log_prob(history, future, b, mechanism)
        if not bool(torch.isfinite(left)) or not bool(torch.isfinite(right)):
            raise ProjectionQualificationError("BLOCKED: finite pair contrast requires positive support at both endpoints")
        return right - left

    def line_integral(
        self,
        history: Sequence[Any],
        future: Sequence[Any],
        source_a: Any,
        source_b: Any,
        mechanism: Any = None,
        *,
        order: int = 8,
        tolerance: float = 1e-5,
    ) -> LineIntegralResult:
        """Gauss-Legendre integral of the conditional source score from a to b.

        The reported defect compares the quadrature with the exact *finite
        bank* endpoint contrast.  It does not bound teacher misspecification,
        Monte Carlo bias, or an unobserved discontinuity between the nodes.
        """
        if not self.derivative_valid:
            raise ProjectionQualificationError("BLOCKED: a source path integral needs a qualified derivative")
        if order < 2 or tolerance < 0:
            raise ValueError("order must be >= 2 and tolerance must be nonnegative")
        a, b = self._source(source_a), self._source(source_b)
        if a.shape != b.shape:
            raise ValueError("source endpoints must have equal dimensions")
        delta = b - a
        nodes, weights = np.polynomial.legendre.leggauss(order)
        integral = torch.zeros((), dtype=a.dtype, device=a.device)
        ess_values = []
        for node, weight in zip(nodes, weights):
            alpha = (float(node) + 1.0) / 2.0
            point = (a + alpha * delta).detach().clone().requires_grad_(True)
            result = self.project(history, future, point, mechanism)
            assert result.score is not None
            integral = integral + (float(weight) / 2.0) * torch.dot(result.score, delta)
            ess_values.extend((result.history_ess.detach(), result.full_ess.detach()))
        endpoint = self.pair_endpoint(history, future, a, b, mechanism)
        for point in (a, b):
            result = self.project(history, future, point, mechanism, with_score=False)
            ess_values.extend((result.history_ess.detach(), result.full_ess.detach()))
        defect = torch.abs(integral - endpoint)
        min_ess = torch.stack(ess_values).min()
        flags = []
        if float(defect.detach()) > tolerance:
            flags.append("QUADRATURE_DEFECT")
        if float(min_ess.detach()) < self.min_ess:
            flags.append("LOW_ESS")
        status = "+".join(flags) if flags else "OK_FINITE_BANK"
        return LineIntegralResult(integral, endpoint, defect, min_ess, int(order), status)

"""Fresh-suffix likelihood audit with a shared finite nuisance parameter.

An audit e-value is not a posterior probability or another observation.  This
class never updates a source posterior. Its guarantee is conditional on the
supplied laws being the actual conditional observation laws (or a null family
containing them). Estimates from simulation seeds do not establish that fact.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable

import numpy as np
from scipy.special import logsumexp


CALIBRATION_ASSUMPTIONS = (
    "The true source is included in the fixed legal source set.",
    "One included nuisance index describes the entire audit; it is not reselected at each step.",
    "Every supplied law is a proper conditional law for the same realized past and chosen action.",
    "The law and normalized alternative prediction are frozen before the current outcome is seen.",
    "Raw observations are new, or their increments use the correct conditional dependence law.",
    "Actions and the audit start use only past information; repeat audits require alpha spending.",
    "Estimated-channel validity is model-relative unless external calibration proves family inclusion.",
)


class ImpossibleObservationError(ValueError):
    """The audit suffix has zero likelihood under every installed state."""


@dataclass(frozen=True)
class AuditSnapshot:
    log_e_values: np.ndarray
    max_log_e_values: np.ndarray
    compatible_now: tuple[int, ...]
    not_rejected_since_start: tuple[int, ...]
    event_count: int
    total_cost: float
    action_counts: np.ndarray
    alpha: float
    log_threshold: float
    guarantee_scope: str


class AuditLedger:
    """Test each source against a fixed mixture of all other source states.

    Usage: ``prepare(action)`` *before* taking the measurement, then
    ``update(action, outcome, event_id)``. The source/null likelihood is
    ``max_r prod_t P_t(outcome_t | source, r, actual_past, action_t)``.
    Thus the same nuisance r is shared through the audit. A new ledger starts
    from likelihood one and has no access to the possibly wrong old posterior.

    ``prepare(..., probabilities=P_t)`` supports predictable conditional laws.
    P_t must keep the original [action,source,nuisance,outcome] shape and the
    physical meaning of every nuisance index. The API can freeze arrays; it
    cannot verify their physical calibration or the absence of future leakage.
    """

    def __init__(self, channel, alpha: float = 0.05, alternative_weights=None):
        if not np.isfinite(alpha) or not 0 < alpha < 1:
            raise ValueError("alpha must be strictly between zero and one")
        self.alpha = float(alpha)
        self.log_threshold = float(np.log(1.0 / alpha))
        self._probabilities = self._validate_table(channel.probabilities).copy()
        self.shape = self._probabilities.shape
        a, s, r, _ = self.shape
        self.costs = np.asarray(channel.costs, dtype=float).copy()
        if self.costs.shape != (a,) or not np.isfinite(self.costs).all() or np.any(self.costs <= 0):
            raise ValueError("audit costs must be positive and finite")
        self.source_ids = tuple(channel.source_ids)
        weights = np.ones((s, r)) if alternative_weights is None else np.asarray(alternative_weights, dtype=float)
        if weights.shape != (s, r) or not np.isfinite(weights).all() or np.any(weights <= 0):
            raise ValueError("fixed alternative weights must be positive [source,nuisance]")
        self._log_mixture_weights = np.empty((s, s, r))
        for null in range(s):
            log_w = np.log(weights)
            log_w[null] = -np.inf
            self._log_mixture_weights[null] = log_w - logsumexp(log_w)
        self._log_likelihood = np.zeros((s, r))
        self._log_alt = np.zeros(s)
        self._log_e = np.zeros(s)
        self._max_log_e = np.zeros(s)
        self._pending = None
        self._event_ids: set[Hashable] = set()
        self.events: list[dict] = []
        self.action_counts = np.zeros(a, dtype=int)
        self.total_cost = 0.0
        self.calibration_assumptions = CALIBRATION_ASSUMPTIONS
        self.guarantee_scope = "model-relative; no physical calibration is inferred from a probability table"

    @staticmethod
    def _validate_table(values):
        p = np.asarray(values, dtype=float)
        if p.ndim != 4 or p.shape[0] < 1 or p.shape[1] < 2 or p.shape[2] < 1 or p.shape[3] < 2:
            raise ValueError("conditional probabilities need axes [action,source,nuisance,outcome]")
        if not np.isfinite(p).all() or np.any(p < 0) or not np.allclose(p.sum(-1), 1.0, atol=1e-9, rtol=0):
            raise ValueError("every conditional outcome law must be a probability distribution")
        return p

    @staticmethod
    def _index(value, bound, name):
        if not isinstance(value, (int, np.integer)) or isinstance(value, (bool, np.bool_)) or not 0 <= value < bound:
            raise ValueError(f"{name} index is out of range")
        return int(value)

    @property
    def log_likelihood(self):
        return self._log_likelihood.copy()

    @property
    def log_alt(self):
        return self._log_alt.copy()

    @property
    def log_e_values(self):
        return self._log_e.copy()

    @property
    def max_log_e_values(self):
        return self._max_log_e.copy()

    @property
    def compatible_now(self):
        return tuple(int(i) for i in np.flatnonzero(self._log_e < self.log_threshold))

    @property
    def not_rejected_since_start(self):
        return tuple(int(i) for i in np.flatnonzero(self._max_log_e < self.log_threshold))

    @property
    def pending_action(self):
        return None if self._pending is None else self._pending["action"]

    def prepare(self, action: int, *, probabilities=None, model_version=None) -> np.ndarray:
        """Freeze alternative predictions and selected conditional law now.

        Returns a copy of q[null_source,outcome]. Internal log q is computed
        with logsumexp, so a tiny returned probability does not erase evidence.
        A pending observation must be resolved before another is prepared.
        """
        action = self._index(action, self.shape[0], "action")
        if self._pending is not None:
            raise RuntimeError("the previously prepared action has not been observed")
        table = self._probabilities if probabilities is None else self._validate_table(probabilities)
        if table.shape != self.shape:
            raise ValueError("conditional table shape and nuisance identity must stay fixed")
        selected = table[action].copy()
        with np.errstate(divide="ignore"):
            log_selected = np.log(selected)
        s, _, o = selected.shape
        log_q = np.empty((s, o))
        for null in range(s):
            history = self._log_mixture_weights[null] + self._log_likelihood
            normalizer = logsumexp(history)
            if np.isneginf(normalizer):
                # This fixed alternative mixture already has zero path mass.
                # Any normalized next prediction is valid; its product stays 0.
                log_q[null] = -np.log(o)
            else:
                log_q[null] = logsumexp(history[:, :, None] + log_selected, axis=(0, 1)) - normalizer
        self._pending = {
            "action": action,
            "log_selected": log_selected,
            "log_q": log_q,
            "model_version": model_version,
        }
        return np.exp(log_q).copy()

    def update(self, action: int, outcome: int, event_id: Hashable) -> AuditSnapshot:
        """Enter a fresh observation once, using only the prepared prediction.

        Validation precedes mutation. Duplicate IDs, a missing preparation,
        action mismatches, and a globally impossible suffix leave state intact.
        A posterior update, if desired, must be performed separately once using
        this same raw event; this method never supplies an extra likelihood.
        """
        try:
            hash(event_id)
        except TypeError as exc:
            raise ValueError("event_id must be hashable") from exc
        if event_id in self._event_ids:
            raise ValueError("a raw observation block cannot be counted twice in the audit")
        action = self._index(action, self.shape[0], "action")
        outcome = self._index(outcome, self.shape[-1], "outcome")
        if self._pending is None:
            raise RuntimeError("prepare(action) must freeze predictions before observing the outcome")
        if action != self._pending["action"]:
            raise ValueError("observed action differs from the prepared action")
        new_likelihood = self._log_likelihood + self._pending["log_selected"][:, :, outcome]
        if np.all(np.isneginf(new_likelihood)):
            raise ImpossibleObservationError("the entire observed suffix has zero probability under every installed state")
        new_log_alt = self._log_alt + self._pending["log_q"][:, outcome]
        new_log_e = new_log_alt - np.max(new_likelihood, axis=1)
        event = {
            "event_id": event_id,
            "action": action,
            "outcome": outcome,
            "cost": float(self.costs[action]),
            "model_version": self._pending["model_version"],
            "alternative_log_prediction": self._pending["log_q"][:, outcome].tolist(),
        }
        self._log_likelihood = new_likelihood
        self._log_alt = new_log_alt
        self._log_e = new_log_e
        self._max_log_e = np.maximum(self._max_log_e, new_log_e)
        self._event_ids.add(event_id)
        self.events.append(event)
        self.action_counts[action] += 1
        self.total_cost += float(self.costs[action])
        self._pending = None
        return self.snapshot()

    def snapshot(self) -> AuditSnapshot:
        return AuditSnapshot(
            self._log_e.copy(), self._max_log_e.copy(), self.compatible_now,
            self.not_rejected_since_start, len(self.events), self.total_cost,
            self.action_counts.copy(), self.alpha, self.log_threshold,
            self.guarantee_scope,
        )

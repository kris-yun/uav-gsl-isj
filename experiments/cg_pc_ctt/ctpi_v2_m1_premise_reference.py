"""Exact finite-mixture baseline and first M1 realization for a premise audit.

The proposed shared-nuisance construction is tested against ordinary Bayesian
inversion with IDENTICAL forward responses, priors and observation likelihood.
No claim of novelty is made by naming a simulator source setting an intervention.
Nuisance indexes denote whole persistent trajectories, not fresh per-block draws.
"""
from __future__ import annotations
import numpy as np


def validate(prediction, observation, source_prior, nuisance_prior, sigma):
    p = np.asarray(prediction, dtype=float)
    y = np.asarray(observation, dtype=float)
    ps = np.asarray(source_prior, dtype=float)
    pu = np.asarray(nuisance_prior, dtype=float)
    if p.ndim != 3 or y.shape != (p.shape[2],):
        raise ValueError("expected source x nuisance-trajectory x block")
    if ps.shape != (p.shape[0],) or pu.shape != (p.shape[1],):
        raise ValueError("prior dimension")
    if p.shape[2] == 0 or not all(np.all(np.isfinite(x)) for x in (p, y, ps, pu)):
        raise ValueError("empty or nonfinite")
    if not np.isfinite(sigma) or sigma <= 0 or np.any(ps <= 0) or np.any(pu <= 0):
        raise ValueError("positive scale and priors required")
    return p, y, ps / ps.sum(), pu / pu.sum(), float(sigma)


def ordinary_bayes(prediction, observation, source_prior, nuisance_prior, sigma):
    """Vectorized joint posterior, then sum nuisance out once."""
    p, y, ps, pu, sigma = validate(prediction, observation, source_prior, nuisance_prior, sigma)
    logjoint = (np.log(ps)[:, None] + np.log(pu)[None, :]
                - .5 * np.sum(((p - y) / sigma) ** 2, axis=2))
    joint = np.exp(logjoint - np.max(logjoint))
    joint /= joint.sum()
    return joint.sum(axis=1)


class SharedNuisanceM1:
    """Incremental paired-world implementation; not a new inference principle."""
    def __init__(self, source_prior, nuisance_prior, sigma):
        ps, pu = np.asarray(source_prior, float), np.asarray(nuisance_prior, float)
        if (ps.ndim != 1 or pu.ndim != 1 or not len(ps) or not len(pu)
                or not np.all(np.isfinite(ps)) or not np.all(np.isfinite(pu))
                or np.any(ps <= 0) or np.any(pu <= 0) or not np.isfinite(sigma) or sigma <= 0):
            raise ValueError("invalid prior/scale")
        self.logweights = np.log(ps / ps.sum())[:, None] + np.log(pu / pu.sum())[None, :]
        self.sigma = float(sigma)
        self.last_block = -1

    def update(self, block_id, candidate_predictions, measured):
        if block_id != self.last_block + 1:
            raise ValueError("duplicate, reversed or missing evidence block")
        x = np.asarray(candidate_predictions, float)
        if x.shape != self.logweights.shape or not np.all(np.isfinite(x)) or not np.isfinite(measured):
            raise ValueError("invalid observation block")
        for source in range(x.shape[0]):
            for nuisance in range(x.shape[1]):
                residual = (float(measured) - float(x[source, nuisance])) / self.sigma
                self.logweights[source, nuisance] -= .5 * residual * residual
        self.last_block = block_id

    def posterior(self):
        weights = np.exp(self.logweights - np.max(self.logweights))
        return weights.sum(axis=1) / weights.sum()


def candidate_m1(prediction, observation, source_prior, nuisance_prior, sigma):
    p, y, ps, pu, sigma = validate(prediction, observation, source_prior, nuisance_prior, sigma)
    model = SharedNuisanceM1(ps, pu, sigma)
    for block in range(len(y)):
        model.update(block, p[:, :, block], y[block])
    return model.posterior()

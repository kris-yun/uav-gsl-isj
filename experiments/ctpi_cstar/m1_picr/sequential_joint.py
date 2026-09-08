"""Development M1: persistent source x mechanism posterior, not a novelty claim.

A mechanism index denotes a persistent nuisance hypothesis, not a component
that may be reselected independently after every observation. Predictions are
committed before observations; each positive timestamp is scored exactly once.
No context-ratio correction, source truth, planner, or map interpolation enters
this estimator. Gaussian scales/rho are declared model assumptions, not a
claim that the physical prior has been calibrated on real Houses.
"""
from __future__ import annotations

import math
import numpy as np


def _normalize(logp):
    peak = np.max(logp)
    if not np.isfinite(peak):
        raise ValueError('JOINT_EMPTY_SUPPORT')
    normalizer = peak + np.log(np.exp(logp - peak).sum())
    return logp - normalizer, float(normalizer)


class SequentialJointEvidence:
    def __init__(self, source_prior, mechanism_prior, *, cadence_ns=200_000_000, rho=0.0):
        sp, mp = np.asarray(source_prior, dtype=float), np.asarray(mechanism_prior, dtype=float)
        for p in (sp, mp):
            if p.ndim != 1 or not len(p) or not np.isfinite(p).all() or np.any(p <= 0):
                raise ValueError('JOINT_PRIOR')
        if type(cadence_ns) is not int or cadence_ns <= 0:
            raise ValueError('JOINT_CADENCE')
        if not math.isfinite(rho) or not -1 < rho < 1:
            raise ValueError('JOINT_RHO')
        self.log_joint = np.log(sp / sp.sum())[:, None] + np.log(mp / mp.sum())[None, :]
        self.cadence_ns, self.rho = cadence_ns, rho
        self.last_stamp_ns = 0
        self.observation_count = 0
        self.log_evidence = 0.0
        self._prediction = None
        self._residual = None

    @property
    def source_posterior(self):
        return np.exp(self.log_joint).sum(axis=1)

    def predict(self, stamp_ns, mean, scale):
        if self._prediction is not None:
            raise ValueError('JOINT_UNCONSUMED_PREDICTION')
        if type(stamp_ns) is not int or stamp_ns != self.last_stamp_ns + self.cadence_ns:
            raise ValueError('JOINT_PREDICTION_STAMP')
        mean, scale = np.array(mean, dtype=float, copy=True), np.array(scale, dtype=float, copy=True)
        if (mean.shape != self.log_joint.shape or scale.shape != mean.shape or
                not np.isfinite(mean).all() or not np.isfinite(scale).all() or np.any(scale <= 0)):
            raise ValueError('JOINT_PREDICTION_LAW')
        self._prediction = (stamp_ns, mean, scale)

    def observe(self, stamp_ns, gas_ppm=None, *, valid=True):
        if self._prediction is None or stamp_ns != self._prediction[0]:
            raise ValueError('JOINT_OBSERVATION_WITHOUT_MATCHED_PREDICTION')
        if type(valid) is not bool:
            raise ValueError('JOINT_VALID_MASK')
        _, mean, scale = self._prediction
        # Validate before mutation so rejected data cannot partly advance state.
        if valid:
            if gas_ppm is None or not math.isfinite(float(gas_ppm)) or gas_ppm < 0:
                raise ValueError('JOINT_OBSERVATION_GAS')
            residual = math.log1p(gas_ppm) - mean
            innovation = residual if self._residual is None else residual - self.rho * self._residual
            score = -0.5 * (math.log(2 * math.pi) + 2 * np.log(scale) + (innovation / scale) ** 2)
            updated, increment = _normalize(self.log_joint + score)
            self.log_joint = updated
            self.log_evidence += increment
            self._residual = residual
            self.observation_count += 1
        else:
            # Missing is neutral; a real measured zero follows the valid branch.
            self._residual = None
        self.last_stamp_ns = stamp_ns
        self._prediction = None
        return self.source_posterior

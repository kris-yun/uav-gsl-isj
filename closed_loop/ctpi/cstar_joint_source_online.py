"""Truth-blind M1/M2 development boundary, not yet a PMFS controller hook.

Caller supplies geometry-only candidate support and a physical-law provider.
The candidate/member ordering must remain fixed throughout a session. The
provider sees only the old prefix and commanded next sensing location. A new
wind observation is appended after its gas observation has been scored.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from experiments.ctpi_cstar.m1_picr.sequential_joint import SequentialJointEvidence


@dataclass(frozen=True)
class _FrameSnapshot:
    stamp_ns: int
    pose_xy: tuple[float, float]
    gas_ppm: float
    wind_uv: tuple[float, float]


def _snapshot(frame):
    return _FrameSnapshot(frame.stamp_ns, tuple(frame.pose_xy), float(frame.gas_ppm), tuple(frame.wind_uv))


class JointSourceSession:
    def __init__(self, provider, candidates_xy, bootstrap, *, source_prior=None, rho=0.0):
        self.provider = provider
        points = np.asarray(candidates_xy, dtype=float)
        if points.ndim != 2 or points.shape[1] != 2 or not len(points) or not np.isfinite(points).all():
            raise ValueError('JOINT_CANDIDATES')
        if len(set(map(tuple, points))) != len(points):
            raise ValueError('JOINT_DUPLICATE_CANDIDATES')
        if bootstrap.stamp_ns != 0:
            raise ValueError('JOINT_REAL_BOOTSTRAP_REQUIRED')
        self._check_frame(bootstrap)
        self.candidates = tuple(map(tuple, points))
        self.prefix = [_snapshot(bootstrap)]
        self.state = None
        self.source_prior = np.array(source_prior, dtype=float, copy=True) if source_prior is not None else np.ones(len(points))
        if self.source_prior.shape != (len(points),):
            raise ValueError('JOINT_SOURCE_PRIOR_SHAPE')
        self.rho = rho
        self.next_pose = None
        self.weights = None
        self.cadence_ns = round(provider.config.route_dt * 1e9)

    @staticmethod
    def _check_frame(frame):
        if (type(frame.stamp_ns) is not int or frame.stamp_ns < 0 or
                len(frame.pose_xy) != 2 or len(frame.wind_uv) != 2 or
                not np.isfinite((*frame.pose_xy, *frame.wind_uv, frame.gas_ppm)).all() or frame.gas_ppm < 0):
            raise ValueError('JOINT_FRAME')

    def predict_next(self, pose_xy):
        if self.next_pose is not None:
            raise ValueError('JOINT_PENDING_FRAME')
        pose = tuple(float(v) for v in pose_xy)
        if len(pose) != 2 or not np.isfinite(pose).all():
            raise ValueError('JOINT_NEXT_POSE')
        means, scales, weights = [], [], None
        for point in self.candidates:
            request = type('Request', (), {'source_xy': point, 'route_xy': (pose,)})()
            laws, candidate_weights = self.provider.predict_ensemble(tuple(self.prefix), request)
            candidate_weights = tuple(candidate_weights)
            if weights is not None and weights != candidate_weights:
                raise ValueError('JOINT_SOURCE_DEPENDENT_MECHANISM_PRIOR')
            weights = candidate_weights
            if any(len(l.logppm_mean) != 1 or len(l.logppm_scale) != 1 for l in laws):
                raise ValueError('JOINT_ONE_STEP_REQUIRED')
            means.append([l.logppm_mean[0] for l in laws])
            scales.append([l.logppm_scale[0] for l in laws])
        if self.weights is not None and self.weights != weights:
            raise ValueError('JOINT_MECHANISM_PRIOR_DRIFT')
        state = self.state or SequentialJointEvidence(self.source_prior, weights,
                          cadence_ns=self.cadence_ns, rho=self.rho)
        state.predict(self.prefix[-1].stamp_ns + self.cadence_ns, means, scales)
        self.state, self.weights, self.next_pose = state, weights, pose

    def observe(self, frame):
        self._check_frame(frame)
        if self.next_pose is None or tuple(frame.pose_xy) != self.next_pose:
            raise ValueError('JOINT_REALIZED_POSE_DIFFERS_FROM_PREDICTED_POSE')
        result = self.state.observe(frame.stamp_ns, frame.gas_ppm)
        self.prefix.append(_snapshot(frame))
        self.next_pose = None
        return result

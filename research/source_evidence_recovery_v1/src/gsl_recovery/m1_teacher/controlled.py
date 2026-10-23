"""Controlled stochastic plume surrogate with exact probabilities and teacher.

Not CFD: a causal Gaussian wind process drives an intermittent thresholded
response. A source-dependent routing gate creates a genuine discontinuity in
natural simulator noise. It is intended to verify the algorithm and contracts,
not establish lake/House localization performance.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence
import numpy as np
from scipy.special import ndtr
from gsl_recovery.types import Action, Observation, Mechanism
from .operators import gaussian_lift, gaussian_score_weight, sample_scalar_branch, standard_normal_pdf


@dataclass(frozen=True)
class ControlledConfig:
    wind_mean: tuple = (0.6, 0.1)
    wind_rho: float = 0.65
    wind_sigma: float = 0.45
    response_sigma: float = 0.9
    branch_jump: float = 0.8
    sensor_memory: float = 0.8


@dataclass
class TeacherRecord:
    source: np.ndarray
    history: list
    observation: Observation
    mechanism: Mechanism
    smooth_weight: np.ndarray
    unconstrained_weight: np.ndarray
    boundary_coefficient: np.ndarray
    boundary_plus: float
    boundary_minus: float
    wind_residual: float
    response_residual: float
    unconstrained_wind_residual: float


class ControlledPlumeBackend:
    """Source is passed only to the environment or an explicit hypothesis call."""
    def __init__(self, config=None):
        self.config = config or ControlledConfig()

    @staticmethod
    def _active(mechanism, index):
        return mechanism is not None and mechanism.kind != 'nominal' and mechanism.active(index)

    def wind_mean(self, history, mechanism):
        cfg = self.config
        mean = np.asarray(cfg.wind_mean, float)
        previous = np.asarray(history[-1].wind, float) if history else mean
        value = mean + cfg.wind_rho * (previous - mean)
        if self._active(mechanism, len(history)) and mechanism.kind == 'wind_bias':
            value = value + np.array([mechanism.magnitude, 0.0])
        return value

    def response(self, source, action, wind, previous_y, mechanism, index):
        s = np.asarray(source, float)
        r = np.array([action.x, action.y]) - s - 0.7 * np.asarray(wind)
        mu = 1.5 - 0.9 * r[0] ** 2 - 0.8 * r[1] ** 2
        mu += self.config.sensor_memory * previous_y
        mu -= 0.1 * abs(action.z - 1.0)
        if self._active(mechanism, index) and mechanism.kind == 'sensor_offset':
            mu += mechanism.magnitude
        d_source = np.array([1.8 * r[0], 1.6 * r[1]])
        d_wind = 0.7 * d_source
        return float(mu), d_source, d_wind

    def gate(self, source):
        s = np.asarray(source, float)
        return float(0.5 * (s[0] - 1.5) + 0.2 * (s[1] - 1.5))

    @staticmethod
    def gate_gradient():
        return np.array([0.5, 0.2])

    def survival(self, mechanism, index):
        if self._active(mechanism, index) and mechanism.kind == 'detection_loss':
            if not 0.0 <= mechanism.magnitude < 1.0:
                raise ValueError('detection_loss magnitude must be in [0,1)')
            return 1.0 - mechanism.magnitude
        return 1.0

    def next_probability(self, history, action, wind, source, mechanism=None):
        prev = history[-1].gas if history else 0.0
        mu, _, _ = self.response(source, action, wind, prev, mechanism, len(history))
        b = self.gate(source)
        lo = ndtr(mu / self.config.response_sigma)
        hi = ndtr((mu + self.config.branch_jump) / self.config.response_sigma)
        p = ndtr(b) * lo + (1.0 - ndtr(b)) * hi
        return float(np.clip(p * self.survival(mechanism, len(history)), 1e-12, 1 - 1e-12))

    def next_source_score(self, history, observation, source, mechanism=None):
        prev = history[-1].gas if history else 0.0
        mu, dmu, _ = self.response(source, observation.action, observation.wind,
                                  prev, mechanism, len(history))
        sig, delta = self.config.response_sigma, self.config.branch_jump
        b = self.gate(source)
        lo, hi = ndtr(mu / sig), ndtr((mu + delta) / sig)
        regular = (ndtr(b) * standard_normal_pdf(mu / sig)
                   + (1.0 - ndtr(b)) * standard_normal_pdf((mu + delta) / sig)) / sig * dmu
        boundary = standard_normal_pdf(b) * (lo - hi) * self.gate_gradient()
        survival = self.survival(mechanism, len(history))
        dp = (regular + boundary) * survival
        raw_p = (ndtr(b) * lo + (1.0 - ndtr(b)) * hi) * survival
        if raw_p <= 1e-12 or raw_p >= 1.0 - 1e-12:
            dp = np.zeros(2)
        p = self.next_probability(history, observation.action, observation.wind, source, mechanism)
        return (observation.gas - p) * dp / (p * (1.0 - p))

    def log_prob(self, history, source, mechanism=None):
        value = 0.0
        prefix = []
        sig = self.config.wind_sigma
        for observation in history:
            wind = np.asarray(observation.wind)
            error = (wind - self.wind_mean(prefix, mechanism)) / sig
            value += -0.5 * float(error @ error) - 2.0 * np.log(sig) - np.log(2.0 * np.pi)
            p = self.next_probability(prefix, observation.action, wind, source, mechanism)
            y = observation.gas
            if y not in (0., 1.):
                raise ValueError('controlled backend requires binary hit/miss observations')
            value += y * np.log(p) + (1.0 - y) * np.log1p(-p)
            prefix.append(observation)
        return float(value)

    def source_score(self, history, source, mechanism=None):
        return sum((self.next_source_score(history[:i], o, source, mechanism)
                    for i, o in enumerate(history)), np.zeros(2))

    def step(self, source, history, action, mechanism=None, rng=None, uid=None):
        rng = np.random.default_rng() if rng is None else rng
        xi = rng.standard_normal(4)
        wind = self.wind_mean(history, mechanism) + self.config.wind_sigma * xi[:2]
        prev = history[-1].gas if history else 0.0
        mu, _, _ = self.response(source, action, wind, prev, mechanism, len(history))
        latent = mu + self.config.response_sigma * xi[2]
        latent += self.config.branch_jump * (xi[3] > self.gate(source))
        survived = rng.random() < self.survival(mechanism, len(history))
        y = float(latent > 0 and survived)
        return Observation(uid=uid or f'controlled_{len(history)}', action=action,
                           wind=tuple(map(float, wind)), gas=y)

    def simulate_episode(self, source, actions, mechanism=None, rng=None):
        rng = np.random.default_rng() if rng is None else rng
        history = []
        for action in actions:
            history.append(self.step(source, history, action, mechanism, rng))
        return history

    def sample_future(self, history, actions, source, mechanism=None, rng=None):
        rng = np.random.default_rng() if rng is None else rng
        prefix, output = list(history), []
        for i, action in enumerate(actions):
            obs = self.step(source, prefix, action, mechanism, rng, uid=f'pred_{len(prefix)}')
            prefix.append(obs)
            output.append(obs)
        return output

    def teacher_record(self, source, history, action, mechanism=None, rng=None):
        """A matched sample and IBP weights; all prefix observations are fixed."""
        rng = np.random.default_rng() if rng is None else rng
        mechanism = mechanism or Mechanism()
        source = np.asarray(source, float)
        xi = rng.standard_normal(4)
        wm = self.wind_mean(history, mechanism)
        wind = wm + self.config.wind_sigma * xi[:2]
        prev = history[-1].gas if history else 0.0
        mu, ds, _ = self.response(source, action, wind, prev, mechanism, len(history))
        b = self.gate(source)
        survival = float(rng.random() < self.survival(mechanism, len(history)))
        def output(gate_on):
            return float(mu + self.config.response_sigma * xi[2]
                         + self.config.branch_jump * gate_on > 0.0) * survival
        y = output(float(xi[3] > b))
        observation = Observation(uid=f'teacher_{len(history)}', action=action,
                                  wind=tuple(map(float, wind)), gas=y)
        ju = np.zeros((2, 4)); ju[:, :2] = self.config.wind_sigma * np.eye(2)
        def lift_at(noise, constrained):
            u = wm + self.config.wind_sigma * noise[:2]
            _, tangent, d_wind = self.response(source, action, u, prev, mechanism, len(history))
            jx = np.array([[*(self.config.wind_sigma * d_wind), self.config.response_sigma, 0.0]])
            return gaussian_lift(jx, ju, tangent[None, :], preserve_wind=constrained)
        constrained = lift_at(xi, True)
        unconstrained = lift_at(xi, False)
        if not constrained.feasible:
            raise ValueError('infeasible wind-preserving lift')
        # Constrained gas-coordinate lift is independent of xi_gas, hence div=0.
        smooth = xi @ constrained.lift
        direct = gaussian_score_weight(lambda z: lift_at(z, False).lift, xi)
        boundary = sample_scalar_branch(
            lambda z: z - b, -self.gate_gradient(), lambda z: 1.0,
            lambda z: output(True), lambda z: output(False),
            bracket=(b - 1., b + 1.))
        return TeacherRecord(source, list(history), observation, mechanism, smooth,
                             direct, boundary.coefficient, boundary.plus_value,
                             boundary.minus_value, constrained.wind_residual,
                             constrained.response_residual, unconstrained.wind_residual)


def make_training_episodes(backend, sources, actions, n_episodes=64, seed=0, mechanisms=None):
    """Return mappings consumed by JointObservationGenerator.fit.

    Only caller-provided TRAIN sources/mechanisms are sampled. Split discovery
    and frozen holdout enforcement belong to the data qualification layer.
    """
    rng = np.random.default_rng(seed)
    mechanisms = list(mechanisms or [Mechanism()])
    sources = np.asarray(sources, float)
    result = []
    for i in range(n_episodes):
        source = sources[i % len(sources)].copy()
        mechanism = mechanisms[(i // len(sources)) % len(mechanisms)]
        # Permute whole fixed action schedules, not observations within an episode.
        order = rng.permutation(len(actions))
        schedule = [Action(x=actions[j].x, y=actions[j].y, z=actions[j].z,
                           time=float(k), dwell=actions[j].dwell) for k, j in enumerate(order)]
        observations = backend.simulate_episode(source, schedule, mechanism, rng)
        result.append({'source': source, 'observations': observations, 'mechanism': mechanism,
                       'episode_id': f'train_{seed}_{i}', 'split': 'train'})
    return result

"""Data contracts. No truth, future wind or world-id in deployment inputs."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import numpy as np


@dataclass(frozen=True)
class Reading:
    """One simultaneous 1 Hz gas/wind/pose reading for an N-UAV team.

    gas_ppm is the actual measured *background-subtracted* excess, not an
    instantaneous oracle concentration. The model accounts for physical delay.
    """
    t: float
    pos: np.ndarray            # [N,3] ENU meters
    gas_ppm: np.ndarray        # [N] observed (negative values allowed)
    wind: np.ndarray           # [N,3] environmental Earth-frame wind m/s
    valid: np.ndarray          # [N] sensor validity
    background_ppm: float = 0.0
    sensor_ids: tuple[str, ...] | None = None  # immutable physical instrument identity across time

    def __post_init__(self):
        p, y, w, v = map(np.asarray, (self.pos, self.gas_ppm, self.wind, self.valid))
        if p.ndim != 2 or p.shape[1] != 3 or len(p) < 2:
            raise ValueError('Requires N>=2 xyz team positions')
        if y.shape != (len(p),) or w.shape != p.shape or v.shape != (len(p),):
            raise ValueError('Observation shape mismatch')
        if not (np.isfinite(p).all() and np.isfinite(y).all() and np.isfinite(w).all()):
            raise ValueError('NaN in sensor observation')
        if not np.asarray(v).dtype == bool:
            raise ValueError('valid must be a boolean array')
        if not np.isfinite(self.t): raise ValueError('Invalid observation time')
        if self.sensor_ids is not None:
            if len(self.sensor_ids) != len(p) or len(set(self.sensor_ids)) != len(p):
                raise ValueError('sensor_ids must be unique and cover every UAV')
            if any(not isinstance(i, str) or not i for i in self.sensor_ids):
                raise ValueError('sensor identities must be nonempty strings')


@dataclass(frozen=True)
class Trajectory:
    name: str
    velocity: np.ndarray       # [N,3] constant velocity, 1-second execution step
    family: str                # translation | reconfiguration | mixed | safe
    rationale: str


@dataclass
class Configuration:
    q_values: tuple = (.5, 1.0, 2.0, 4.0)
    q_prior: tuple = (.25, .25, .25, .25)
    sensor_sigma: float = .02
    hit_threshold: float = .06
    dt_action: float = 1.0
    horizon_steps: int = 3
    speed_xy_max: float = 1.75
    speed_z_max: float = 1.0
    distance_max_per_uav: float = 54.0
    min_separation: float = 4.0
    max_candidates_scored: int = 8
    source_fd_eps_m: float = 1.0
    project_height_nuisance: bool = True
    source_height_eps_m: float = 1.0
    source_pair_count: int = 12
    forecast_error_bound: Optional[float] = None    # independently validated whitened error bound
    model_error_calibrated: bool = False  # requires certificate_id to be operational
    model_error_certificate_id: Optional[str] = None  # immutable externally validated ID
    sensor_lag_s: float = 2.0
    sensor_tau_s: float = 1.0
    min_effective_gas_for_shape: float = .06
    strict_model_gate: bool = False                 # no certificate -> safe cover, no claimed disambiguation
    evidence_rank_threshold: float = 1e-6
    gain_min: float = 1e-6
    profile_margin_scale: float = 1e-2
    eig_regularizer: float = 1e-4
    mode: str = 'bio'

    def __post_init__(self):
        if len(self.q_values) != len(self.q_prior) or min(self.q_values) <= 0:
            raise ValueError('Need shared positive q-support')
        if any(q < 0 for q in self.q_prior) or abs(sum(self.q_prior)-1) > 1e-9:
            raise ValueError('q prior must sum to 1')
        if self.sensor_sigma <= 0 or self.horizon_steps < 1 or self.dt_action <= 0:
            raise ValueError('Invalid time/noise settings')
        if self.forecast_error_bound is not None and self.forecast_error_bound < 0:
            raise ValueError('Invalid model error bound')

        valid_modes = {'bio','bio_noidentity','bio_noflow','bio_nogap','ordinary_coverage',
                       'ordinary_eig','ordinary_projected','ordinary_eig_full','ordinary_projected_full'}
        if self.mode not in valid_modes:
            raise ValueError('Unknown policy mode: '+self.mode)
        if self.sensor_lag_s < 0 or self.sensor_tau_s < 0:
            raise ValueError('invalid sensor time specification')
        if self.model_error_calibrated and (self.forecast_error_bound is None or
               not self.model_error_certificate_id):
            raise ValueError('Model reliability certificate requires error bound and external ID')
        if self.max_candidates_scored < 1:
            raise ValueError('Must score at least one action')

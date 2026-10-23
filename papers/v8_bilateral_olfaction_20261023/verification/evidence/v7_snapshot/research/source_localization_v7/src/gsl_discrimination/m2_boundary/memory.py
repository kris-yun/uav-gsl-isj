"""Causal direction memories and an engineering uncertainty tube.

The memory update follows Siliciano et al., Nature (2026),
doi:10.1038/s41586-026-10827-7.  The tube and its uncertainty bookkeeping
are engineering additions; neither is a source likelihood.  Distances use
one caller-declared coordinate unit throughout, and all times are seconds.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np


def _vector(value, name: str) -> np.ndarray:
    arr = np.asarray(value, dtype=float)
    if arr.shape != (2,) or not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} must be a finite length-2 vector")
    return arr.copy()


def _psd(value, name: str) -> np.ndarray:
    arr = np.asarray(value, dtype=float)
    if arr.shape != (2, 2) or not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} must be a finite 2x2 covariance")
    if not np.allclose(arr, arr.T, atol=1e-12, rtol=1e-10):
        raise ValueError(f"{name} must be symmetric")
    if np.linalg.eigvalsh(arr).min() < -1e-12:
        raise ValueError(f"{name} must be positive semidefinite")
    return arr.copy()


@dataclass(frozen=True)
class BoundaryEvent:
    """An already confirmed crossing supplied by a causal odor detector.

    crossing_time_s is the sensor-aligned *sample* time, not a frame index.
    The detector is responsible for uninterrupted pre/post odor occupancy;
    M2 checks their durations and that confirmation does not use future time.
    Known sensor/tube latency must be corrected before constructing an event.
    """

    kind: Literal["entry", "exit"]
    crossing_time_s: float
    prior_stable_duration_s: float
    post_stable_duration_s: float


@dataclass(frozen=True)
class LocalWind:
    """Measured air velocity (points DOWNWIND), with acquisition time."""

    velocity_xy: np.ndarray
    timestamp_s: float


@dataclass(frozen=True)
class BoundaryMemoryConfig:
    """All temporal and motion scales must be supplied for the target sensor.

    entry_only is a no-wind engineering adaptation.  wind_gated adds the
    original two-memory/upwind-gate structure, not the paper's full velocity
    controller or negative-binomial state-duration model.
    """

    mode: Literal["entry_only", "wind_gated"]
    entry_decay: float
    entry_gain: float
    min_pre_s: float
    min_post_s: float
    direction_window_s: float
    max_observation_gap_s: float
    max_memory_age_s: float
    min_speed: float
    max_speed: float
    timing_validated: bool
    exit_decay: float | None = None
    exit_gain: float | None = None
    initial_upwind_gain: float | None = None
    initial_crosswind_gain: float = 0.0
    exit_min_upwind_cos: float = 0.5
    max_wind_age_s: float = 0.0
    direction_noise_variance: float = 0.0

    def __post_init__(self):
        if self.mode not in ("entry_only", "wind_gated"):
            raise ValueError("mode must be entry_only or wind_gated")
        if self.timing_validated is not True:
            raise ValueError("dynamic memory requires validated sensor time alignment")
        positive = ("entry_gain", "min_pre_s", "min_post_s", "direction_window_s",
                    "max_observation_gap_s", "max_memory_age_s", "max_speed")
        for name in positive:
            val = getattr(self, name)
            if not np.isfinite(val) or val <= 0:
                raise ValueError(f"{name} must be finite and positive")
        if not np.isfinite(self.entry_decay) or not 0 <= self.entry_decay < 1:
            raise ValueError("entry_decay must be in [0, 1)")
        if not np.isfinite(self.min_speed) or not 0 <= self.min_speed < self.max_speed:
            raise ValueError("require 0 <= min_speed < max_speed")
        if self.direction_window_s > self.min_pre_s + self.min_post_s + 1e-12:
            raise ValueError("direction window exceeds qualified crossing history")
        for name in ("max_wind_age_s", "direction_noise_variance"):
            val = getattr(self, name)
            if not np.isfinite(val) or val < 0:
                raise ValueError(f"{name} must be finite and nonnegative")
        if not np.isfinite(self.exit_min_upwind_cos) or not -1 <= self.exit_min_upwind_cos <= 1:
            raise ValueError("exit_min_upwind_cos must be in [-1, 1]")
        if not np.isfinite(self.initial_crosswind_gain):
            raise ValueError("initial_crosswind_gain must be finite")
        if self.mode == "wind_gated":
            if self.exit_decay is None or not np.isfinite(self.exit_decay) or not 0 <= self.exit_decay < 1:
                raise ValueError("wind_gated requires exit_decay in [0, 1)")
            for name in ("exit_gain", "initial_upwind_gain"):
                val = getattr(self, name)
                if val is None or not np.isfinite(val) or val <= 0:
                    raise ValueError(f"wind_gated requires positive {name}")


@dataclass(frozen=True)
class MemorySnapshot:
    entry_vector: np.ndarray
    exit_vector: np.ndarray
    entry_covariance: np.ndarray
    entry_count: int
    exit_count: int
    last_observation_s: float | None
    last_entry_confirmation_s: float | None
    last_entry_sample_s: float | None


@dataclass(frozen=True)
class MemoryUpdate:
    event_used: bool
    reason: str
    snapshot: MemorySnapshot


@dataclass(frozen=True)
class ReturnTube:
    """A relative ray tube from the current robot location, not a boundary map.

    multiplier is a design conservatism parameter, not a calibrated coverage
    quantile.  Only action centers are constrained; probe endpoints may straddle
    the tube and must satisfy the separate geometry constraints.
    """

    origin_xy: np.ndarray
    direction_xy: np.ndarray
    length: float
    base_radius: float
    position_covariance: np.ndarray
    direction_covariance: np.ndarray
    multiplier: float = 1.0

    def __post_init__(self):
        origin = _vector(self.origin_xy, "origin_xy")
        direction = _vector(self.direction_xy, "direction_xy")
        norm = np.linalg.norm(direction)
        if norm < 1e-12:
            raise ValueError("return direction is undefined")
        for name in ("length", "base_radius", "multiplier"):
            val = getattr(self, name)
            if not np.isfinite(val) or val < 0 or (name == "length" and val == 0):
                raise ValueError(f"invalid {name}")
        object.__setattr__(self, "origin_xy", origin)
        object.__setattr__(self, "direction_xy", direction / norm)
        object.__setattr__(self, "position_covariance", _psd(self.position_covariance, "position_covariance"))
        object.__setattr__(self, "direction_covariance", _psd(self.direction_covariance, "direction_covariance"))

    def radius(self, along_distance) -> np.ndarray:
        distance = np.asarray(along_distance, dtype=float)
        if not np.all(np.isfinite(distance)):
            raise ValueError("along_distance must be finite")
        normal = np.array([-self.direction_xy[1], self.direction_xy[0]])
        v0 = normal @ self.position_covariance @ normal
        v1 = normal @ self.direction_covariance @ normal
        return self.base_radius + self.multiplier * np.sqrt(np.maximum(0.0, v0 + distance ** 2 * v1))

    def contains(self, points_xy) -> np.ndarray:
        points = np.asarray(points_xy, dtype=float)
        if points.shape[-1:] != (2,) or not np.all(np.isfinite(points)):
            raise ValueError("points_xy must end in 2 finite coordinates")
        relative = points - self.origin_xy
        along = relative @ self.direction_xy
        normal = np.array([-self.direction_xy[1], self.direction_xy[0]])
        across = np.abs(relative @ normal)
        return (along >= -1e-12) & (along <= self.length + 1e-12) & (across <= self.radius(along) + 1e-12)


class CausalBoundaryMemory:
    """Event-only direction memory. There is intentionally no source input.

    heading_rad is the odometric travel heading of the segment ending at this
    observation, not aircraft yaw.  Segment speed comes from positions and true
    elapsed seconds.  A crossing direction averages observed velocity over the
    configured qualified window, entirely at/before confirmation time.
    """

    def __init__(self, config: BoundaryMemoryConfig):
        self.config = config
        self.reset()

    def reset(self) -> None:
        """Start a new qualified stream after a gap; old direction is discarded."""
        self._samples: list[tuple[float, np.ndarray, float]] = []
        self._entry = np.zeros(2)
        self._exit = np.zeros(2)
        self._entry_cov = np.zeros((2, 2))
        self._entry_count = 0
        self._exit_count = 0
        self._last_entry_s = None
        self._last_entry_confirmation_s = None
        self._last_crossing_s = None

    def snapshot(self) -> MemorySnapshot:
        return MemorySnapshot(self._entry.copy(), self._exit.copy(), self._entry_cov.copy(),
                              self._entry_count, self._exit_count,
                              self._samples[-1][0] if self._samples else None,
                              self._last_entry_confirmation_s, self._last_entry_s)

    def _upwind(self, wind: LocalWind | None, now: float) -> np.ndarray:
        if wind is None:
            raise ValueError("current local wind is required for this wind_gated update")
        ts = float(wind.timestamp_s)
        if not np.isfinite(ts) or ts > now + 1e-12:
            raise ValueError("wind acquisition timestamp must not be in the future")
        if now - ts > self.config.max_wind_age_s + 1e-12:
            raise ValueError("local wind is too old")
        flow = _vector(wind.velocity_xy, "wind velocity_xy")
        if np.linalg.norm(flow) < 1e-12:
            raise ValueError("zero wind cannot define upwind")
        return -flow / np.linalg.norm(flow)

    def _crossing_direction(self, samples, event: BoundaryEvent, now: float):
        cfg = self.config
        if event.kind not in ("entry", "exit"):
            raise ValueError("event kind must be entry or exit")
        vals = (event.crossing_time_s, event.prior_stable_duration_s, event.post_stable_duration_s)
        if not np.all(np.isfinite(vals)):
            raise ValueError("event times must be finite real seconds")
        if event.crossing_time_s < 0 or event.crossing_time_s > now + 1e-12:
            raise ValueError("crossing must have an observed, nonfuture sample time")
        if self._last_crossing_s is not None and event.crossing_time_s <= self._last_crossing_s:
            raise ValueError("crossing events must be new and ordered")
        if event.prior_stable_duration_s + 1e-12 < cfg.min_pre_s:
            raise ValueError("crossing has insufficient qualified pre-event duration")
        if event.post_stable_duration_s + 1e-12 < cfg.min_post_s:
            raise ValueError("crossing has insufficient qualified post-event duration")
        if event.crossing_time_s + event.post_stable_duration_s > now + 1e-12:
            raise ValueError("event confirmation would require future observations")
        end = event.crossing_time_s + cfg.min_post_s
        start = end - cfg.direction_window_s
        if now - end > cfg.max_memory_age_s + 1e-12:
            raise ValueError("crossing direction is already too old at confirmation")
        if not samples or samples[0][0] > start + 1e-12 or samples[-1][0] < end - 1e-12:
            raise ValueError("observed trajectory does not cover the crossing direction window")
        velocities, durations = [], []
        for (ta, xa, _), (tb, xb, heading) in zip(samples[:-1], samples[1:]):
            overlap = min(tb, end) - max(ta, start)
            if overlap <= 0:
                continue
            speed = np.linalg.norm(xb - xa) / (tb - ta)
            velocities.append(speed * np.array([np.cos(heading), np.sin(heading)]))
            durations.append(overlap)
        duration = np.sum(durations)
        if duration < cfg.direction_window_s - 1e-9:
            raise ValueError("incomplete causal direction window")
        velocity = np.average(velocities, axis=0, weights=durations)
        speed = np.linalg.norm(velocity)
        if speed <= max(cfg.min_speed, 1e-12):
            raise ValueError("stationary or cancelling motion does not define an entry direction")
        direction = velocity / speed
        scatter = np.zeros((2, 2))
        for vel, weight in zip(velocities, durations):
            norm = np.linalg.norm(vel)
            if norm > 1e-12:
                residual = vel / norm - direction
                scatter += weight / duration * np.outer(residual, residual)
        scatter += cfg.direction_noise_variance * np.eye(2)
        return direction, scatter

    def update(self, *, timestamp_s: float, position_xy, heading_rad: float,
               event: BoundaryEvent | None = None, local_wind: LocalWind | None = None) -> MemoryUpdate:
        """Validate, then atomically accept an observation and possible event."""
        now = float(timestamp_s)
        heading = float(heading_rad)
        if not np.isfinite(now) or now < 0 or not np.isfinite(heading):
            raise ValueError("timestamp_s and travel heading must be finite; time must be nonnegative")
        position = _vector(position_xy, "position_xy")
        cfg = self.config
        if self._samples:
            dt = now - self._samples[-1][0]
            if dt <= 0:
                raise ValueError("observation timestamps must strictly increase")
            if dt > cfg.max_observation_gap_s + 1e-12:
                raise ValueError("observation gap exceeds dynamic-memory qualification")
            if np.linalg.norm(position - self._samples[-1][1]) / dt > cfg.max_speed + 1e-12:
                raise ValueError("observed displacement violates the configured motion bound")
        upwind = self._upwind(local_wind, now) if local_wind is not None else None
        if cfg.mode == "wind_gated" and (not self._samples or (event is not None and event.kind == "exit")):
            upwind = self._upwind(local_wind, now)
        samples = self._samples + [(now, position, heading)]
        direction, scatter = (None, None) if event is None else self._crossing_direction(samples, event, now)

        # No mutation precedes this point: a rejected clock/wind/event is retryable.
        if not self._samples and cfg.mode == "wind_gated":
            crosswind = np.array([upwind[1], -upwind[0]])
            self._exit = cfg.initial_upwind_gain * upwind + cfg.initial_crosswind_gain * crosswind
        used, reason = False, "no_crossing"
        if event is not None:
            self._last_crossing_s = event.crossing_time_s
            if event.kind == "entry":
                if self._entry_count and np.linalg.norm(self._entry) > 1e-12:
                    residual = direction - self._entry / np.linalg.norm(self._entry)
                    scatter = scatter + np.outer(residual, residual)
                self._entry_cov = cfg.entry_decay ** 2 * self._entry_cov + cfg.entry_gain ** 2 * scatter
                self._entry = cfg.entry_decay * self._entry + cfg.entry_gain * direction
                self._entry_count += 1
                # Sensor-aligned evidence ages while confirmation is delayed.
                self._last_entry_s = event.crossing_time_s + cfg.min_post_s
                self._last_entry_confirmation_s = now
                used, reason = True, "entry_memory_updated"
            elif cfg.mode == "entry_only":
                reason = "exit_ignored_in_entry_only_mode"
            elif direction @ upwind < cfg.exit_min_upwind_cos:
                reason = "exit_rejected_by_upwind_gate"
            else:
                self._exit = cfg.exit_decay * self._exit + cfg.exit_gain * direction
                self._exit_count += 1
                used, reason = True, "exit_memory_updated"
        self._samples = samples
        # Retain enough past motion for sensor-aligned delayed confirmation.
        horizon = cfg.max_memory_age_s + cfg.direction_window_s + cfg.min_pre_s
        while len(self._samples) > 2 and self._samples[1][0] < now - horizon:
            self._samples.pop(0)
        return MemoryUpdate(used, reason, self.snapshot())

    def make_return_tube(self, *, timestamp_s: float, current_position_xy, length: float,
                         base_radius: float, position_covariance, drift_variance_rate: float,
                         sensor_delay_uncertainty_s: float, multiplier: float = 1.0) -> ReturnTube:
        now = float(timestamp_s)
        if not np.isfinite(now) or not self._samples or now < self._samples[-1][0] - 1e-12:
            raise ValueError("tube time must be at or after the latest real observation")
        if self._last_entry_s is None:
            raise ValueError("no qualified entry memory exists")
        age = now - self._last_entry_s
        if age > self.config.max_memory_age_s:
            raise ValueError("entry direction memory has expired")
        if now - self._samples[-1][0] > self.config.max_observation_gap_s + 1e-12:
            raise ValueError("current motion observations are too stale for a return tube")
        current_position = _vector(current_position_xy, "current_position_xy")
        elapsed = now - self._samples[-1][0]
        if np.linalg.norm(current_position - self._samples[-1][1]) > self.config.max_speed * elapsed + 1e-9:
            raise ValueError("current position is inconsistent with the observed motion bound")
        for value in (drift_variance_rate, sensor_delay_uncertainty_s):
            if not np.isfinite(value) or value < 0:
                raise ValueError("tube drift and latency uncertainty must be nonnegative")
        norm = np.linalg.norm(self._entry)
        if norm < 1e-12:
            raise ValueError("entry directions cancel; no return direction is identifiable")
        direction = self._entry / norm
        jacobian = (np.eye(2) - np.outer(direction, direction)) / norm
        direction_covariance = jacobian @ self._entry_cov @ jacobian.T
        position_covariance = _psd(position_covariance, "position_covariance")
        added = drift_variance_rate * age + (self.config.max_speed * sensor_delay_uncertainty_s) ** 2
        position_covariance += added * np.eye(2)
        return ReturnTube(current_position, direction, length, base_radius,
                          position_covariance, direction_covariance, multiplier)

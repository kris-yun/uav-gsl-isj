"""Deterministic, causal physical prior for the online CPO boundary.

This is deliberately a *prior*, not a trained CPO and not a source estimator.
For each source hypothesis it advances a declared finite-volume plume with the
past-only local wind, applies the declared FOPDT sensor, and converts the
predicted concentration to a first-encounter hazard.  The implementation is
kept small and mirrors the contracts in ``CTPIOnlineCoreV2.hpp``: free-cell
faces are no-flux, the update is positivity preserving, and the source rate,
grid, cadence, and hazard scale are explicit configuration rather than hidden
constants.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

try:  # package import when used from a test/module
    from ..common.trace_io import Episode  # type: ignore
except ImportError:  # pragma: no cover - only for direct script execution
    Episode = object  # type: ignore

try:
    from cstar_reference import CPORouteLaw
except ImportError:  # pragma: no cover
    from experiments.ctpi_cstar.cstar_reference import CPORouteLaw


@dataclass(frozen=True)
class PhysicalPriorConfig:
    nx: int
    ny: int
    dx: float
    diffusion: float
    free: tuple[bool, ...]
    origin_xy: tuple[float, float] = (0.0, 0.0)
    field_dt: float = 0.5
    route_dt: float = 0.2
    source_rate_per_field_second: float = 1.0
    source_rate_values: tuple[float, ...] = (0.5, 1.0, 2.0)
    sensor_tau: float = 1.2
    sensor_dead: float = 0.4
    hazard_scale: float = 0.2

    def validate(self) -> None:
        if type(self.nx) is not int or type(self.ny) is not int or self.nx < 1 or self.ny < 1:
            raise ValueError("CSTAR_M2_PRIOR_GRID")
        if len(self.free) != self.nx * self.ny or not any(self.free):
            raise ValueError("CSTAR_M2_PRIOR_FREE_MASK")
        for value, code in ((self.dx, "DX"), (self.diffusion, "DIFFUSION"),
                            (self.field_dt, "FIELD_DT"), (self.route_dt, "ROUTE_DT"),
                            (self.source_rate_per_field_second, "SOURCE_RATE"),
                            (self.sensor_tau, "SENSOR_TAU"), (self.sensor_dead, "SENSOR_DEAD"),
                            (self.hazard_scale, "HAZARD_SCALE")):
            if not math.isfinite(float(value)) or (value <= 0 and code not in {"DIFFUSION", "SENSOR_DEAD"}):
                raise ValueError("CSTAR_M2_PRIOR_" + code)
        if self.diffusion < 0 or self.sensor_dead < 0 or self.hazard_scale <= 0:
            raise ValueError("CSTAR_M2_PRIOR_PARAMETER_RANGE")
        if (not self.source_rate_values or
                any(not math.isfinite(float(v)) or float(v) <= 0 for v in self.source_rate_values)):
            raise ValueError("CSTAR_M2_PRIOR_SOURCE_RATE_ENSEMBLE")


def _cell(config: PhysicalPriorConfig, xy: tuple[float, float]) -> int:
    x = int(round((float(xy[0]) - config.origin_xy[0]) / config.dx))
    y = int(round((float(xy[1]) - config.origin_xy[1]) / config.dx))
    if x < 0 or x >= config.nx or y < 0 or y >= config.ny:
        raise ValueError("CSTAR_M2_PRIOR_POINT_OUTSIDE_GRID")
    idx = x + y * config.nx
    if not config.free[idx]:
        raise ValueError("CSTAR_M2_PRIOR_POINT_IN_SOLID")
    return idx


def _advance(field: list[float], config: PhysicalPriorConfig, wind: tuple[float, float],
             source: int | None, source_rate: float | None = None,
             duration: float | None = None) -> None:
    """Advance one native field interval using the C++ V2 finite-volume law."""
    n = config.nx * config.ny
    if len(field) != n:
        raise ValueError("CSTAR_M2_PRIOR_FIELD_SIZE")
    if any((not math.isfinite(v) or v < 0) for v in field):
        raise ValueError("CSTAR_M2_PRIOR_FIELD_INVALID")
    u, v = map(float, wind)
    if not math.isfinite(u) or not math.isfinite(v):
        raise ValueError("CSTAR_M2_PRIOR_WIND_INVALID")
    diffusion_rate = config.diffusion / (config.dx * config.dx)
    faces: list[tuple[int, int, bool]] = []
    outgoing = [0.0] * n
    for y in range(config.ny):
        for x in range(config.nx):
            a = x + y * config.nx
            if not config.free[a]:
                if abs(field[a]) > 0:
                    raise ValueError("CSTAR_M2_PRIOR_SOLID_MASS")
                continue
            if x + 1 < config.nx and config.free[a + 1]:
                b = a + 1
                rate = u / config.dx
                faces.append((a, b, True))
                outgoing[a] += max(rate, 0.0) + diffusion_rate
                outgoing[b] += max(-rate, 0.0) + diffusion_rate
            if y + 1 < config.ny and config.free[a + config.nx]:
                b = a + config.nx
                rate = v / config.dx
                faces.append((a, b, False))
                outgoing[a] += max(rate, 0.0) + diffusion_rate
                outgoing[b] += max(-rate, 0.0) + diffusion_rate
    duration = config.field_dt if duration is None else float(duration)
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("CSTAR_M2_PRIOR_DURATION")
    max_rate = max(outgoing, default=0.0)
    steps = max(1, int(math.ceil(duration * max_rate)))
    if steps > 1_000_000:
        raise ValueError("CSTAR_M2_PRIOR_SUBSTEP_LIMIT")
    dt = duration / steps
    rates = [(u / config.dx if horizontal else v / config.dx) for _, _, horizontal in faces]
    for _ in range(steps):
        nxt = [(max(1.0 - dt * out, 0.0) * c) for out, c in zip(outgoing, field)]
        for (a, b, _), rate in zip(faces, rates):
            nxt[b] += dt * (max(rate, 0.0) + diffusion_rate) * field[a]
            nxt[a] += dt * (max(-rate, 0.0) + diffusion_rate) * field[b]
        if source is not None:
            rate = config.source_rate_per_field_second if source_rate is None else source_rate
            nxt[source] += rate * dt
        field[:] = nxt
    if any((not math.isfinite(v) or v < -1e-12) for v in field):
        raise ValueError("CSTAR_M2_PRIOR_NUMERIC_STATE")


class _Fopdt:
    def __init__(self, tau: float, dead: float):
        self.tau, self.dead = tau, dead
        self.time = 0.0
        self.state = 0.0
        self.history: list[tuple[float, float]] = [(0.0, 0.0)]

    def step(self, value: float, dt: float) -> float:
        self.time += dt
        self.history.append((self.time, value))
        query = self.time - self.dead
        delayed = 0.0
        if query > 0.0:
            while len(self.history) > 2 and self.history[1][0] < query:
                self.history.pop(0)
            if query >= self.history[-1][0]:
                delayed = self.history[-1][1]
            else:
                for (a, x), (b, y) in zip(self.history, self.history[1:]):
                    if query <= b:
                        delayed = x + (query - a) / (b - a) * (y - x)
                        break
        alpha = math.exp(-dt / self.tau)
        self.state = alpha * self.state + (1.0 - alpha) * delayed
        return max(0.0, min(1e6, self.state))


class PhysicalCPOProvider:
    """Route-law provider using only a past prefix and explicit hypotheses."""

    def __init__(self, config: PhysicalPriorConfig, *, initial_field: Sequence[float] | None = None):
        config.validate()
        n = config.nx * config.ny
        self.config = config
        self.initial_field = tuple(float(v) for v in (initial_field if initial_field is not None else [0.0] * n))
        if len(self.initial_field) != n or any((not math.isfinite(v) or v < 0) for v in self.initial_field):
            raise ValueError("CSTAR_M2_PRIOR_INITIAL_FIELD")

    def predict(self, prefix, request):
        if not prefix:
            raise ValueError("CSTAR_M2_PRIOR_EMPTY_PREFIX")
        route = tuple(request.route_xy)
        if not route:
            raise ValueError("CSTAR_M2_PRIOR_EMPTY_ROUTE")
        laws, weights = self.predict_ensemble(prefix, request)
        return _moment_match(laws, weights)

    def predict_ensemble(self, prefix, request):
        """Return source-strength components and fixed prior weights.

        The nuisance ensemble is part of the model contract, not a
        post-outcome calibration knob. M1 can marginalize these components in
        log space; the ordinary online route-law surface remains available via
        :meth:`predict` for consumers that require one moment-matched law.
        """
        if not prefix:
            raise ValueError("CSTAR_M2_PRIOR_EMPTY_PREFIX")
        source = _cell(self.config, tuple(request.source_xy))
        route_cells = [_cell(self.config, tuple(point)) for point in request.route_xy]
        weights = tuple(1.0 / len(self.config.source_rate_values)
                        for _ in self.config.source_rate_values)
        laws = tuple(self._predict_cells(prefix, route_cells, source, rate)
                     for rate in self.config.source_rate_values)
        return laws, weights

    def predict_context(self, prefix, route_xy):
        """Source/gas-masked law used as M1's context denominator."""
        if not prefix:
            raise ValueError("CSTAR_M2_PRIOR_EMPTY_PREFIX")
        route_cells = [_cell(self.config, tuple(point)) for point in route_xy]
        return self._predict_cells(prefix, route_cells, None)

    def _predict_cells(self, prefix, route_cells, source, source_rate=None):
        field, sensor = self._replay_prefix(prefix, source, source_rate)
        # The latest wind is the only admissible wind for the next route step.
        wind = tuple(float(v) for v in prefix[-1].wind_uv)
        hazards: list[float] = []
        means: list[float] = []
        scales: list[float] = []
        for cell in route_cells:
            # Sensor blocks arrive at route_dt; field_dt remains the native
            # environment metadata and is not silently used as a 2.5x clock.
            _advance(field, self.config, wind, source, source_rate=source_rate,
                     duration=self.config.route_dt)
            measured = sensor.step(field[cell], self.config.route_dt)
            means.append(math.log1p(measured))
            scales.append(max(1e-6, 1.0 / math.sqrt(1.0 + measured)))
            hazards.append(1.0 - math.exp(-self.config.hazard_scale * measured))
        return CPORouteLaw.from_hazards(hazards, means, scales)

    def _replay_prefix(self, prefix, source, source_rate):
        """Reconstruct candidate plume/sensor state from past frames only."""
        field = list(self.initial_field)
        sensor = _Fopdt(self.config.sensor_tau, self.config.sensor_dead)
        # t=0 is bootstrap.  Every later frame is predicted with the wind
        # available at the preceding stamp, then sampled at its current pose.
        for previous, current in zip(prefix, prefix[1:]):
            pose = getattr(current, "pose_xy", None)
            if pose is None:
                raise ValueError("CSTAR_M2_PRIOR_PREFIX_POSE_REQUIRED")
            if source is not None:
                source_cell = source
            else:
                source_cell = None
            _advance(field, self.config, tuple(previous.wind_uv), source_cell,
                     source_rate=source_rate, duration=self.config.route_dt)
            sensor.step(field[_cell(self.config, tuple(pose))], self.config.route_dt)
        return field, sensor


def _moment_match(laws, weights):
    """Moment-match nuisance components for the scalar online law surface."""
    if len(laws) != len(weights) or not laws:
        raise ValueError("CSTAR_M2_PRIOR_ENSEMBLE_SHAPE")
    z = float(sum(weights))
    if not math.isfinite(z) or z <= 0:
        raise ValueError("CSTAR_M2_PRIOR_ENSEMBLE_WEIGHTS")
    w = [float(v) / z for v in weights]
    horizon = len(laws[0].logppm_mean)
    if any(len(l.logppm_mean) != horizon for l in laws):
        raise ValueError("CSTAR_M2_PRIOR_ENSEMBLE_HORIZON")
    first = [sum(w[k] * laws[k].first_hit_prob[i] for k in range(len(laws)))
             for i in range(horizon + 1)]
    cdf = [sum(first[:i + 1]) for i in range(horizon)]
    means = [sum(w[k] * laws[k].logppm_mean[i] for k in range(len(laws)))
             for i in range(horizon)]
    scales = []
    for i, mean in enumerate(means):
        variance = sum(w[k] * (laws[k].logppm_scale[i] ** 2 +
                               (laws[k].logppm_mean[i] - mean) ** 2)
                       for k in range(len(laws)))
        scales.append(math.sqrt(max(1e-12, variance)))
    return CPORouteLaw(tuple(first), tuple(cdf), cdf[-1], tuple(means), tuple(scales))

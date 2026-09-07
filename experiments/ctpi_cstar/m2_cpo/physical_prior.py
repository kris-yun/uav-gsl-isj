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
from functools import lru_cache
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
    amplitude_min: float = 1.0e-3
    amplitude_max: float = 1.0e6
    transport_time_scale: float = 1.0
    condition_noise_free_sensor: bool = False
    transport_backend: str = 'reference'

    def validate(self) -> None:
        if self.transport_backend not in ('reference','numpy'):
            raise ValueError('CSTAR_M2_PRIOR_BACKEND')
        if type(self.nx) is not int or type(self.ny) is not int or self.nx < 1 or self.ny < 1:
            raise ValueError("CSTAR_M2_PRIOR_GRID")
        if len(self.free) != self.nx * self.ny or not any(self.free):
            raise ValueError("CSTAR_M2_PRIOR_FREE_MASK")
        for value, code in ((self.dx, "DX"), (self.diffusion, "DIFFUSION"),
                            (self.field_dt, "FIELD_DT"), (self.route_dt, "ROUTE_DT"),
                            (self.source_rate_per_field_second, "SOURCE_RATE"),
                            (self.sensor_tau, "SENSOR_TAU"), (self.sensor_dead, "SENSOR_DEAD"),
                            (self.hazard_scale, "HAZARD_SCALE"),
                            (self.amplitude_min, "AMPLITUDE_MIN"),
                            (self.amplitude_max, "AMPLITUDE_MAX"),
                            (self.transport_time_scale, "TRANSPORT_TIME_SCALE")):
            if not math.isfinite(float(value)) or (value <= 0 and code not in {"DIFFUSION", "SENSOR_DEAD"}):
                raise ValueError("CSTAR_M2_PRIOR_" + code)
        if self.diffusion < 0 or self.sensor_dead < 0 or self.hazard_scale <= 0:
            raise ValueError("CSTAR_M2_PRIOR_PARAMETER_RANGE")
        if self.amplitude_min <= 0 or self.amplitude_max < self.amplitude_min:
            raise ValueError("CSTAR_M2_PRIOR_AMPLITUDE_RANGE")
        if (not self.source_rate_values or
                any(not math.isfinite(float(v)) or float(v) <= 0 for v in self.source_rate_values)):
            raise ValueError("CSTAR_M2_PRIOR_SOURCE_RATE_ENSEMBLE")


def _cell(config: PhysicalPriorConfig, xy: tuple[float, float]) -> int:
    # ROS YAML origin is the lower corner, not the centre of cell zero.
    x = math.floor((float(xy[0]) - config.origin_xy[0]) / config.dx)
    y = math.floor((float(xy[1]) - config.origin_xy[1]) / config.dx)
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
    if config.transport_backend == 'numpy':
        return _advance_numpy(field,config,wind,source,source_rate,duration)
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


@lru_cache(maxsize=8)
def _numpy_faces(nx,ny,free):
    import numpy as np
    mask=np.asarray(free,dtype=bool).reshape(ny,nx)
    grid=np.arange(nx*ny).reshape(ny,nx)
    horizontal=mask[:,:-1]&mask[:,1:]
    vertical=mask[:-1,:]&mask[1:,:]
    a=np.concatenate((grid[:,:-1][horizontal],grid[:-1,:][vertical]))
    b=np.concatenate((grid[:,1:][horizontal],grid[1:,:][vertical]))
    return a,b,int(horizontal.sum()),mask.flatten()


def _advance_numpy(field,config,wind,source,source_rate,duration):
    """Same edge fluxes/CFL substeps as the scalar reference, batched in NumPy."""
    import numpy as np
    c=np.asarray(field,dtype=np.float64)
    n=config.nx*config.ny
    if c.shape!=(n,): raise ValueError('CSTAR_M2_PRIOR_FIELD_SIZE')
    if not np.isfinite(c).all() or (c<0).any(): raise ValueError('CSTAR_M2_PRIOR_FIELD_INVALID')
    u,v=map(float,wind)
    if not math.isfinite(u) or not math.isfinite(v): raise ValueError('CSTAR_M2_PRIOR_WIND_INVALID')
    a,b,nh,free=_numpy_faces(config.nx,config.ny,config.free)
    if (c[~free]!=0).any(): raise ValueError('CSTAR_M2_PRIOR_SOLID_MASS')
    rates=np.empty(len(a)); rates[:nh]=u/config.dx; rates[nh:]=v/config.dx
    forward=np.maximum(rates,0)+config.diffusion/config.dx**2
    reverse=np.maximum(-rates,0)+config.diffusion/config.dx**2
    outgoing=np.bincount(a,weights=forward,minlength=n)+np.bincount(b,weights=reverse,minlength=n)
    duration=config.field_dt if duration is None else float(duration)
    if not math.isfinite(duration) or duration<=0: raise ValueError('CSTAR_M2_PRIOR_DURATION')
    steps=max(1,math.ceil(duration*float(outgoing.max())))
    if steps>1_000_000: raise ValueError('CSTAR_M2_PRIOR_SUBSTEP_LIMIT')
    dt=duration/steps
    retention=np.maximum(1-dt*outgoing,0)
    for _ in range(steps):
        nxt=retention*c
        nxt+=np.bincount(b,weights=dt*forward*c[a],minlength=n)
        nxt+=np.bincount(a,weights=dt*reverse*c[b],minlength=n)
        if source is not None:
            nxt[source]+=(config.source_rate_per_field_second if source_rate is None else source_rate)*dt
        c=nxt
    if not np.isfinite(c).all() or (c < -1e-12).any(): raise ValueError('CSTAR_M2_PRIOR_NUMERIC_STATE')
    field[:]=c.tolist()


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

    def predict_assimilated(self, prefix, request):
        """Predict one source-conditioned law after causal prefix assimilation.

        The unit-rate plume is replayed only through the last observed frame.
        A non-negative multiplicative source-strength state is then estimated
        by ridge projection of measured gas onto that unit response.  The
        resulting state is carried through the *future route*; no future gas,
        route outcome, source truth, or bank is consulted.  This is the
        explicit ``amplitude_state`` nuisance path in the M1/M2 interface and
        is intentionally separate from the fixed-weight rate ensemble.
        """
        if not prefix:
            raise ValueError("CSTAR_M2_PRIOR_EMPTY_PREFIX")
        route = tuple(request.route_xy)
        if not route:
            raise ValueError("CSTAR_M2_PRIOR_EMPTY_ROUTE")
        source = _cell(self.config, tuple(request.source_xy))
        route_cells = [_cell(self.config, tuple(point)) for point in route]
        return self._predict_cells(
            prefix, route_cells, source, source_rate=None,
            assimilate_amplitude=True,
        )

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
        return self._predict_cells(prefix, route_cells, None, condition_sensor=False)

    def _predict_cells(self, prefix, route_cells, source, source_rate=None,
                       assimilate_amplitude=False, condition_sensor=True):
        if assimilate_amplitude:
            field, sensor, prefix_response = self._replay_prefix(
                prefix, source, 1.0, record_response=True)
            amplitude = self._estimate_amplitude(prefix, prefix_response)
            field = [amplitude * value for value in field]
            sensor.state *= amplitude
            sensor.history = [(t, amplitude * value) for t, value in sensor.history]
            source_rate = amplitude
        else:
            field, sensor = self._replay_prefix(prefix, source, source_rate)
        if self.config.condition_noise_free_sensor and condition_sensor:
            # In the explicitly noise-free, unit-gain FOPDT contract, measured
            # output is the sensor state. Carry it at the decision boundary;
            # a misfit source plume must not reset an observed state to zero.
            # The unobserved delay queue remains the model prediction.
            measured_state = float(prefix[-1].gas_ppm)
            if not math.isfinite(measured_state) or not 0 <= measured_state < 1e6:
                raise ValueError('CSTAR_M2_SENSOR_STATE_UNOBSERVABLE_OR_SATURATED')
            sensor.state = measured_state
        # The latest wind is the only admissible wind for the next route step.
        wind = tuple(float(v) for v in prefix[-1].wind_uv)
        hazards: list[float] = []
        means: list[float] = []
        scales: list[float] = []
        for cell in route_cells:
            # Sensor and field clocks differ in seeded GADEN replay. The
            # explicit scale is bound to the environment, not fitted to gas.
            _advance(field, self.config, wind, source, source_rate=source_rate,
                     duration=self.config.route_dt * self.config.transport_time_scale)
            measured = sensor.step(field[cell], self.config.route_dt)
            means.append(math.log1p(measured))
            scales.append(max(1e-6, 1.0 / math.sqrt(1.0 + measured)))
            hazards.append(1.0 - math.exp(-self.config.hazard_scale * measured))
        return CPORouteLaw.from_hazards(hazards, means, scales)

    def _replay_prefix(self, prefix, source, source_rate, record_response=False):
        """Reconstruct candidate plume/sensor state from past frames only."""
        stamps = [getattr(frame,'stamp_ns',None) for frame in prefix]
        if any(stamp is not None for stamp in stamps):
            if stamps[0] != 0 or any(stamp is None for stamp in stamps):
                raise ValueError('CSTAR_M2_PRIOR_MISSING_BOOTSTRAP_STATE')
            dt_ns=round(self.config.route_dt*1e9)
            if any(b-a != dt_ns for a,b in zip(stamps,stamps[1:])):
                raise ValueError('CSTAR_M2_PRIOR_PREFIX_CADENCE')
        field = list(self.initial_field)
        sensor = _Fopdt(self.config.sensor_tau, self.config.sensor_dead)
        responses: list[float] = []
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
                     source_rate=source_rate,
                     duration=self.config.route_dt * self.config.transport_time_scale)
            responses.append(sensor.step(
                field[_cell(self.config, tuple(pose))], self.config.route_dt
            ))
        if record_response:
            return field, sensor, responses
        return field, sensor

    def _estimate_amplitude(self, prefix, unit_response: Sequence[float]) -> float:
        """Estimate a positive release-strength multiplier from past gas only."""
        observed = [max(0.0, float(frame.gas_ppm)) for frame in prefix[1:]]
        if len(observed) != len(unit_response):
            raise ValueError("CSTAR_M2_PRIOR_AMPLITUDE_ALIGNMENT")
        energy = sum(float(value) * float(value) for value in unit_response)
        cross = sum(float(a) * float(b) for a, b in zip(unit_response, observed))
        # A tiny fixed ridge is a numerical guard, not an outcome-tuned fit.
        estimate = max(0.0, cross) / (energy + 1.0e-12)
        if energy <= 1.0e-12:
            estimate = 1.0
        return min(self.config.amplitude_max,
                   max(self.config.amplitude_min, estimate))


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

#!/usr/bin/env python3
"""Truth-blind inverse of the frozen PF-DEI native sensor for mechanism diagnostics.

This is NOT a generic sensor inverse and is not a source-localization likelihood.
It is valid only when the source-proven sensor contract satisfies:

- deterministic dynamic sensor (noise = drift = 0),
- known non-zero gain and baseline,
- no saturation at the analysed samples,
- tau_rise == tau_recovery == tau,
- regular sample cadence dt,
- dead_time / dt is an integer.

For the frozen development configuration:
    dt = 0.2 s, dead_time = 0.4 s, tau = 1.2 s,
    gain = 1, baseline = 0, initial state/input = 0.

The native source manifest states
    z[k] = exp(-dt/tau) z[k-1] + (1-exp(-dt/tau)) u_delayed[k]
and uses causal piecewise-linear sampled-input delay history.  With an integer
2-sample delay, u_delayed[k] equals physical input C[k-2] on the sample grid.
Thus the physical sample is algebraically recoverable from measured ppm.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Optional

import numpy as np


@dataclass(frozen=True)
class FrozenSensorInverseConfig:
    tau_s: float = 1.2
    dead_time_s: float = 0.4
    gain: float = 1.0
    baseline: float = 0.0
    initial_state_ppm: float = 0.0
    initial_input_ppm: float = 0.0
    noise_std_ppm: float = 0.0
    drift_rate_ppm_s: float = 0.0
    saturation_min_ppm: float = 0.0
    saturation_max_ppm: float = 1.0e6
    regularity_atol_s: float = 1.0e-9


@dataclass(frozen=True)
class InverseResult:
    physical_ppm: np.ndarray
    physical_time_s: np.ndarray
    delayed_input_ppm: np.ndarray
    sample_dt_s: float
    delay_steps: int
    alpha: float
    first_recoverable_input_index: int
    last_recoverable_input_index: int


def _as_1d_finite(name: str, values) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64)
    if arr.ndim != 1 or arr.size < 3 or not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} must be a finite 1-D array with >=3 values")
    return arr


def invert_frozen_sensor(
    sample_time_s,
    measured_ppm,
    config: FrozenSensorInverseConfig = FrozenSensorInverseConfig(),
) -> InverseResult:
    """Recover sample-grid physical concentration from measured ppm.

    The returned `physical_ppm`/`physical_time_s` omit the final `delay_steps`
    physical inputs because no future measured samples exist to observe them.
    No extrapolation is permitted.
    """
    t = _as_1d_finite("sample_time_s", sample_time_s)
    m = _as_1d_finite("measured_ppm", measured_ppm)
    if t.shape != m.shape:
        raise ValueError("time and measured arrays must have identical shape")
    if not np.all(np.diff(t) > 0.0):
        raise ValueError("sample timestamps must be strictly increasing")

    if config.noise_std_ppm != 0.0 or config.drift_rate_ppm_s != 0.0:
        raise ValueError("exact inverse requires frozen zero-noise/zero-drift sensor")
    if not (config.gain > 0.0 and math.isfinite(config.gain)):
        raise ValueError("gain must be finite and positive")
    if not (config.tau_s > 0.0 and math.isfinite(config.tau_s)):
        raise ValueError("tau must be finite and positive")

    dts = np.diff(t)
    dt = float(np.median(dts))
    if not np.allclose(dts, dt, rtol=0.0, atol=config.regularity_atol_s):
        raise ValueError("exact diagnostic inverse requires regular cadence")

    ratio = config.dead_time_s / dt
    delay_steps = int(round(ratio))
    if delay_steps < 0 or not math.isclose(ratio, delay_steps, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError("dead_time/dt must be an integer for this frozen inverse")

    # If clipping is active, the map is not one-to-one.  Exact boundary values
    # are rejected conservatively rather than guessed through.
    if np.any(m <= config.saturation_min_ppm) and config.saturation_min_ppm != 0.0:
        raise ValueError("lower saturation may make inverse non-identifiable")
    if np.any(m >= config.saturation_max_ppm):
        raise ValueError("upper saturation makes inverse non-identifiable")

    z = (m - config.baseline) / config.gain
    alpha = math.exp(-dt / config.tau_s)
    one_minus_alpha = 1.0 - alpha
    if not (one_minus_alpha > 0.0):
        raise ValueError("invalid alpha")

    delayed = np.empty_like(z)
    previous_state = float(config.initial_state_ppm)
    for k in range(z.size):
        delayed[k] = (z[k] - alpha * previous_state) / one_minus_alpha
        previous_state = z[k]

    # For the first `delay_steps`, the delayed input belongs to the declared
    # pre-run history.  From k=delay_steps onward it maps to C[k-delay_steps].
    n_recoverable = z.size - delay_steps
    if n_recoverable <= 0:
        raise ValueError("trace shorter than sensor dead time")
    physical = delayed[delay_steps:].copy()
    physical_time = t[:n_recoverable].copy()

    return InverseResult(
        physical_ppm=physical,
        physical_time_s=physical_time,
        delayed_input_ppm=delayed,
        sample_dt_s=dt,
        delay_steps=delay_steps,
        alpha=alpha,
        first_recoverable_input_index=0,
        last_recoverable_input_index=n_recoverable - 1,
    )


def forward_frozen_sensor(
    physical_ppm,
    config: FrozenSensorInverseConfig = FrozenSensorInverseConfig(),
    sample_dt_s: float = 0.2,
) -> np.ndarray:
    """Minimal sample-grid forward equation for selftest/parity diagnostics.

    It intentionally implements only the frozen symmetric, integer-delay,
    zero-noise case.  Normative production forward simulation remains the
    source-proven native sensor implementation.
    """
    u = _as_1d_finite("physical_ppm", physical_ppm)
    ratio = config.dead_time_s / sample_dt_s
    delay_steps = int(round(ratio))
    if not math.isclose(ratio, delay_steps, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError("dead_time/dt must be integer")
    alpha = math.exp(-sample_dt_s / config.tau_s)

    pre = np.full(delay_steps, float(config.initial_input_ppm), dtype=np.float64)
    delayed = np.concatenate([pre, u])
    out = np.empty(delayed.size, dtype=np.float64)
    state = float(config.initial_state_ppm)
    for k, value in enumerate(delayed):
        state = alpha * state + (1.0 - alpha) * float(value)
        out[k] = config.baseline + config.gain * state
    return out


def inverse_quantization_bound_ppm(
    decimal_places: int,
    alpha: float,
    gain: float = 1.0,
) -> float:
    """Worst-case physical-input error from decimal serialization only."""
    if decimal_places < 0 or not (0.0 <= alpha < 1.0) or not (gain > 0.0):
        raise ValueError("invalid quantization-bound arguments")
    half_quantum = 0.5 * 10.0 ** (-decimal_places)
    return half_quantum * (1.0 + alpha) / ((1.0 - alpha) * gain)


def ideal_block_decision(
    physical_ppm,
    sample_indices,
    threshold_ppm: float,
) -> tuple[float, bool]:
    values = np.asarray(physical_ppm, dtype=np.float64)[np.asarray(sample_indices, dtype=np.int64)]
    if values.size == 0 or not np.all(np.isfinite(values)):
        raise ValueError("invalid ideal block samples")
    mean = float(values.mean(dtype=np.float64))
    return mean, bool(mean > threshold_ppm)

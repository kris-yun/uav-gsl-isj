#!/usr/bin/env python3
"""Frozen run-persistent PF-DEI V3 sensor forward operator."""

from __future__ import annotations

from collections import deque
import hashlib
import json
import math

import numpy as np


AUTHORITATIVE_SENSOR_SOURCE_SHA256 = "423042f94315a35ca83aa929d42a32633d94ea819b8e15639e26039073c549bc"
SENSOR_SEED = 20260828
SENSOR_CONFIG = {
    "mode": "asymmetric",
    "gain": 1.0,
    "baseline": 0.0,
    "tau_rise_s": 1.2,
    "tau_recovery_s": 1.2,
    "dead_time_s": 0.4,
    "noise_std_ppm": 0.0,
    "drift_rate_ppm_s": 0.0,
    "saturation_min_ppm": 0.0,
    "saturation_max_ppm": 1.0e6,
    "initial_state_ppm": 0.0,
    "initial_input_ppm": 0.0,
}


def parameter_manifest() -> dict:
    return {
        "model_version": "mcos-sensor-v1",
        "seed": SENSOR_SEED,
        "state_transition": (
            "z[k]=exp(-dt/tau_branch)*z[k-1]+"
            "(1-exp(-dt/tau_branch))*u_delayed[k]"
        ),
        "delay_interpolation": "causal piecewise-linear sampled-input history",
        "noise_location": "additive after dynamic state, before saturation",
        "config": dict(SENSOR_CONFIG),
    }


def parameter_sha256() -> str:
    blob = json.dumps(parameter_manifest(), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()


def forward_sensor(physical_ppm: np.ndarray, dt_s: float = 0.2) -> np.ndarray:
    physical = np.asarray(physical_ppm, dtype=np.float64)
    if physical.ndim != 1 or not np.isfinite(physical).all() or (physical < 0).any():
        raise ValueError("PF_DEI_V3_SENSOR_INVALID_PHYSICAL_INPUT")
    if not math.isfinite(dt_s) or dt_s <= 0.0:
        raise ValueError("PF_DEI_V3_SENSOR_INVALID_DT")
    cfg = SENSOR_CONFIG
    history = deque([(0.0, float(cfg["initial_input_ppm"]))])
    time_s = 0.0
    state = float(cfg["initial_state_ppm"])
    output = np.empty_like(physical, dtype=np.float64)

    def delayed_input(query_time_s: float) -> float:
        if query_time_s <= 0.0:
            return float(cfg["initial_input_ppm"])
        if query_time_s >= history[-1][0]:
            return history[-1][1]
        previous_time, previous_value = history[0]
        for next_time, next_value in list(history)[1:]:
            if query_time_s <= next_time:
                width = next_time - previous_time
                if width <= 0.0:
                    return next_value
                weight = (query_time_s - previous_time) / width
                return previous_value + weight * (next_value - previous_value)
            previous_time, previous_value = next_time, next_value
        return history[-1][1]

    for index, value in enumerate(physical):
        time_s += dt_s
        history.append((time_s, float(value)))
        delayed = delayed_input(time_s - float(cfg["dead_time_s"]))
        target = (
            float(cfg["gain"]) * delayed + float(cfg["baseline"])
            + float(cfg["drift_rate_ppm_s"]) * time_s
        )
        tau = float(cfg["tau_rise_s"] if target >= state else cfg["tau_recovery_s"])
        if tau <= 0.0:
            state = target
        else:
            alpha = math.exp(-dt_s / tau)
            state = alpha * state + (1.0 - alpha) * target
        output[index] = np.clip(state, float(cfg["saturation_min_ppm"]), float(cfg["saturation_max_ppm"]))
    return output


def forward_sensor_batch(physical_ppm: np.ndarray, dt_s: float = 0.2) -> np.ndarray:
    """Vectorized independent run-persistent states for equal-length traces."""
    physical = np.asarray(physical_ppm, dtype=np.float64)
    if physical.ndim != 2 or not np.isfinite(physical).all() or (physical < 0).any():
        raise ValueError("PF_DEI_V3_SENSOR_INVALID_PHYSICAL_BATCH")
    if not math.isfinite(dt_s) or dt_s <= 0.0:
        raise ValueError("PF_DEI_V3_SENSOR_INVALID_DT")
    delay_steps = float(SENSOR_CONFIG["dead_time_s"]) / dt_s
    if abs(delay_steps - round(delay_steps)) > 1e-12:
        raise ValueError("PF_DEI_V3_SENSOR_BATCH_REQUIRES_INTEGER_DELAY")
    delay = int(round(delay_steps))
    state = np.full(physical.shape[0], float(SENSOR_CONFIG["initial_state_ppm"]), dtype=np.float64)
    output = np.empty_like(physical, dtype=np.float64)
    alpha = math.exp(-dt_s / float(SENSOR_CONFIG["tau_rise_s"]))
    initial = float(SENSOR_CONFIG["initial_input_ppm"])
    for index in range(physical.shape[1]):
        target = physical[:, index - delay] if index >= delay else initial
        state = alpha * state + (1.0 - alpha) * target
        output[:, index] = np.clip(
            state,
            float(SENSOR_CONFIG["saturation_min_ppm"]),
            float(SENSOR_CONFIG["saturation_max_ppm"]),
        )
    return output

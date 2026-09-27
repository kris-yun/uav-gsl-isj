"""Auditable gas-sensor dynamics for authorized VGR/ROS 2 simulation.

The primary paper model is a symmetric first-order-plus-dead-time (FOPDT)
sensor.  Asymmetric rise/recovery and mismatch profiles are explicit stress
tests, not hidden tuning.  The state transition is exact for a zero-order-held
input over each simulation interval.

This module is intentionally ROS-independent so its dynamics can be verified
before deployment into the ``vgr_bridge`` package.
"""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, replace
import math
from typing import Deque

import numpy as np


MODEL_VERSION = "mcos-sensor-v1"


@dataclass(frozen=True)
class SensorConfig:
    mode: str = "fopdt"
    gain: float = 1.0
    baseline: float = 0.0
    tau_rise_s: float = 1.2
    tau_recovery_s: float = 1.2
    dead_time_s: float = 0.4
    noise_std_ppm: float = 0.0
    drift_rate_ppm_s: float = 0.0
    saturation_min_ppm: float = 0.0
    saturation_max_ppm: float = 1.0e6
    initial_state_ppm: float = 0.0
    initial_input_ppm: float = 0.0

    @staticmethod
    def profile(mode: str) -> "SensorConfig":
        normalized = mode.strip().lower()
        profiles = {
            "ideal": SensorConfig(
                mode="ideal",
                tau_rise_s=0.0,
                tau_recovery_s=0.0,
                dead_time_s=0.0,
            ),
            "fopdt": SensorConfig(mode="fopdt"),
            "dynamic": SensorConfig(
                mode="asymmetric",
                tau_rise_s=1.2,
                tau_recovery_s=4.0,
                dead_time_s=0.4,
                noise_std_ppm=0.002,
            ),
            "asymmetric": SensorConfig(
                mode="asymmetric",
                tau_rise_s=1.2,
                tau_recovery_s=4.0,
                dead_time_s=0.4,
            ),
            "mismatch": SensorConfig(
                mode="mismatch",
                gain=0.92,
                baseline=0.015,
                tau_rise_s=0.8,
                tau_recovery_s=5.0,
                dead_time_s=0.6,
                noise_std_ppm=0.005,
                drift_rate_ppm_s=2.0e-4,
            ),
        }
        if normalized not in profiles:
            raise ValueError(
                f"unknown sensor mode {mode!r}; expected one of {sorted(profiles)}"
            )
        return profiles[normalized]

    def validate(self) -> None:
        if self.mode not in {"ideal", "fopdt", "asymmetric", "mismatch"}:
            raise ValueError(f"unsupported normalized sensor mode {self.mode!r}")
        if self.gain < 0.0:
            raise ValueError("gain must be nonnegative")
        if self.tau_rise_s < 0.0 or self.tau_recovery_s < 0.0:
            raise ValueError("time constants must be nonnegative")
        if self.dead_time_s < 0.0:
            raise ValueError("dead time must be nonnegative")
        if self.noise_std_ppm < 0.0:
            raise ValueError("noise standard deviation must be nonnegative")
        if self.saturation_max_ppm <= self.saturation_min_ppm:
            raise ValueError("saturation_max_ppm must exceed saturation_min_ppm")


class SensorModel:
    """Causal FOPDT/asymmetric sensor with deterministic seeded noise."""

    def __init__(self, mode: str = "fopdt", seed: int = 0, **overrides: float):
        config = SensorConfig.profile(mode)
        if overrides:
            unknown = set(overrides) - set(asdict(config))
            if unknown:
                raise TypeError(f"unknown SensorConfig fields: {sorted(unknown)}")
            config = replace(config, **overrides)
        if config.mode == "ideal":
            # ``ideal`` is a negative control: launch-wide dynamic defaults must
            # not silently leave a dead time or a response pole active.
            config = replace(
                config,
                tau_rise_s=0.0,
                tau_recovery_s=0.0,
                dead_time_s=0.0,
            )
        config.validate()
        self.cfg = config
        self.seed = int(seed)
        self.rng = np.random.default_rng(self.seed)
        self.reset()

    def reset(self) -> None:
        self.time_s = 0.0
        self.state_ppm = float(self.cfg.initial_state_ppm)
        self._input_history: Deque[tuple[float, float]] = deque()
        self._input_history.append((0.0, float(self.cfg.initial_input_ppm)))

    def _delayed_input(self, query_time_s: float) -> float:
        if query_time_s <= 0.0:
            return float(self.cfg.initial_input_ppm)
        history = self._input_history
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

    def process(self, true_gas_ppm: float, dt_s: float) -> float:
        if not math.isfinite(true_gas_ppm):
            raise ValueError("true_gas_ppm must be finite")
        if not math.isfinite(dt_s) or dt_s <= 0.0:
            raise ValueError("dt_s must be finite and positive")

        self.time_s += float(dt_s)
        self._input_history.append((self.time_s, float(true_gas_ppm)))
        delayed = self._delayed_input(self.time_s - self.cfg.dead_time_s)
        target = (
            self.cfg.gain * delayed
            + self.cfg.baseline
            + self.cfg.drift_rate_ppm_s * self.time_s
        )

        if self.cfg.mode == "ideal":
            self.state_ppm = target
        else:
            tau = (
                self.cfg.tau_rise_s
                if target >= self.state_ppm
                else self.cfg.tau_recovery_s
            )
            if tau <= 0.0:
                self.state_ppm = target
            else:
                alpha = math.exp(-dt_s / tau)
                self.state_ppm = alpha * self.state_ppm + (1.0 - alpha) * target

        measurement = self.state_ppm
        if self.cfg.noise_std_ppm > 0.0:
            measurement += float(self.rng.normal(0.0, self.cfg.noise_std_ppm))
        return float(
            np.clip(
                measurement,
                self.cfg.saturation_min_ppm,
                self.cfg.saturation_max_ppm,
            )
        )

    def manifest(self) -> dict[str, object]:
        return {
            "model_version": MODEL_VERSION,
            "seed": self.seed,
            "state_transition": (
                "z[k]=exp(-dt/tau_branch)*z[k-1]+"
                "(1-exp(-dt/tau_branch))*u_delayed[k]"
            ),
            "delay_interpolation": "causal piecewise-linear sampled-input history",
            "noise_location": "additive after dynamic state, before saturation",
            "config": asdict(self.cfg),
        }

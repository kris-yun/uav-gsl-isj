"""Deterministic fixed-altitude motion primitives for MCOS G4 smoke tests.

Profiles are relative, source-truth-free, and analytically differentiated.
Translation/rotation into a House map and collision rejection remain the ROS
bridge's responsibility.  No altitude component is generated here.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


@dataclass(frozen=True)
class MotionLimits:
    max_speed_m_s: float = 0.7
    max_acceleration_m_s2: float = 0.5
    max_jerk_m_s3: float = 0.5


@dataclass(frozen=True)
class MotionProfile:
    name: str
    time_s: np.ndarray
    position_xy_m: np.ndarray
    velocity_xy_m_s: np.ndarray
    acceleration_xy_m_s2: np.ndarray
    jerk_xy_m_s3: np.ndarray

    def envelope(self) -> dict[str, float]:
        return {
            "max_speed_m_s": float(np.max(np.linalg.norm(self.velocity_xy_m_s, axis=1))),
            "max_acceleration_m_s2": float(
                np.max(np.linalg.norm(self.acceleration_xy_m_s2, axis=1))
            ),
            "max_jerk_m_s3": float(np.max(np.linalg.norm(self.jerk_xy_m_s3, axis=1))),
        }

    def satisfies(self, limits: MotionLimits, tolerance: float = 1e-12) -> bool:
        envelope = self.envelope()
        return bool(
            envelope["max_speed_m_s"] <= limits.max_speed_m_s + tolerance
            and envelope["max_acceleration_m_s2"]
            <= limits.max_acceleration_m_s2 + tolerance
            and envelope["max_jerk_m_s3"] <= limits.max_jerk_m_s3 + tolerance
        )


def _rotate_and_translate(
    position: np.ndarray,
    velocity: np.ndarray,
    acceleration: np.ndarray,
    jerk: np.ndarray,
    start_xy_m: tuple[float, float],
    heading_rad: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    cosine, sine = math.cos(heading_rad), math.sin(heading_rad)
    rotation = np.array([[cosine, -sine], [sine, cosine]])
    return (
        position @ rotation.T + np.asarray(start_xy_m),
        velocity @ rotation.T,
        acceleration @ rotation.T,
        jerk @ rotation.T,
    )


def generate_profile(
    name: str,
    *,
    duration_s: float = 8.0,
    dt_s: float = 0.2,
    start_xy_m: tuple[float, float] = (0.0, 0.0),
    heading_rad: float = 0.0,
) -> MotionProfile:
    if duration_s <= 0.0 or dt_s <= 0.0:
        raise ValueError("duration and dt must be positive")
    steps = int(round(duration_s / dt_s))
    if not math.isclose(steps * dt_s, duration_s, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError("duration must be an integer multiple of dt")
    time = np.arange(steps + 1, dtype=float) * dt_s
    normalized = name.strip().lower()

    if normalized == "straight":
        speed = 0.50
        position = np.column_stack((speed * time, np.zeros_like(time)))
        velocity = np.column_stack((np.full_like(time, speed), np.zeros_like(time)))
        acceleration = np.zeros_like(position)
        jerk = np.zeros_like(position)
    elif normalized == "turn":
        speed, angular_rate = 0.50, 0.25
        angle = angular_rate * time
        radius = speed / angular_rate
        position = np.column_stack((radius * np.sin(angle), radius * (1.0 - np.cos(angle))))
        velocity = np.column_stack((speed * np.cos(angle), speed * np.sin(angle)))
        acceleration = np.column_stack((
            -speed * angular_rate * np.sin(angle),
            speed * angular_rate * np.cos(angle),
        ))
        jerk = np.column_stack((
            -speed * angular_rate**2 * np.cos(angle),
            -speed * angular_rate**2 * np.sin(angle),
        ))
    elif normalized == "harmonic":
        base_speed, amplitude, omega = 0.45, 0.20, 1.10
        phase = omega * time
        position = np.column_stack((base_speed * time, amplitude * np.sin(phase)))
        velocity = np.column_stack((
            np.full_like(time, base_speed), amplitude * omega * np.cos(phase)
        ))
        acceleration = np.column_stack((
            np.zeros_like(time), -amplitude * omega**2 * np.sin(phase)
        ))
        jerk = np.column_stack((
            np.zeros_like(time), -amplitude * omega**3 * np.cos(phase)
        ))
    elif normalized == "chirp":
        base_speed, amplitude = 0.45, 0.12
        omega_start, omega_end = 0.40, 1.20
        chirp_rate = (omega_end - omega_start) / duration_s
        omega = omega_start + chirp_rate * time
        phase = omega_start * time + 0.5 * chirp_rate * time**2
        position = np.column_stack((base_speed * time, amplitude * np.sin(phase)))
        velocity = np.column_stack((
            np.full_like(time, base_speed), amplitude * np.cos(phase) * omega
        ))
        acceleration = np.column_stack((
            np.zeros_like(time),
            amplitude * (-np.sin(phase) * omega**2 + np.cos(phase) * chirp_rate),
        ))
        jerk = np.column_stack((
            np.zeros_like(time),
            amplitude * (
                -np.cos(phase) * omega**3
                - 3.0 * np.sin(phase) * omega * chirp_rate
            ),
        ))
    elif normalized == "multisine":
        base_speed = 0.45
        amplitudes = np.array([0.12, 0.06])
        frequencies = np.array([0.50, 1.10])
        phases = time[:, None] * frequencies[None, :] + np.array([0.0, 0.7])
        transverse_position = np.sin(phases) @ amplitudes
        transverse_velocity = np.cos(phases) @ (amplitudes * frequencies)
        transverse_acceleration = -np.sin(phases) @ (amplitudes * frequencies**2)
        transverse_jerk = -np.cos(phases) @ (amplitudes * frequencies**3)
        position = np.column_stack((base_speed * time, transverse_position))
        velocity = np.column_stack((np.full_like(time, base_speed), transverse_velocity))
        acceleration = np.column_stack((np.zeros_like(time), transverse_acceleration))
        jerk = np.column_stack((np.zeros_like(time), transverse_jerk))
    elif normalized == "reversal":
        amplitude, omega = 0.50, 0.80
        phase = omega * time
        position = np.column_stack((amplitude * np.sin(phase), np.zeros_like(time)))
        velocity = np.column_stack((amplitude * omega * np.cos(phase), np.zeros_like(time)))
        acceleration = np.column_stack((
            -amplitude * omega**2 * np.sin(phase), np.zeros_like(time)
        ))
        jerk = np.column_stack((
            -amplitude * omega**3 * np.cos(phase), np.zeros_like(time)
        ))
    else:
        raise ValueError(
            "unknown profile; expected straight, turn, harmonic, chirp, "
            "multisine, or reversal"
        )

    position, velocity, acceleration, jerk = _rotate_and_translate(
        position, velocity, acceleration, jerk, start_xy_m, heading_rad
    )
    return MotionProfile(
        name=normalized,
        time_s=time,
        position_xy_m=position,
        velocity_xy_m_s=velocity,
        acceleration_xy_m_s2=acceleration,
        jerk_xy_m_s3=jerk,
    )

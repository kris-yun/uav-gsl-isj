"""CSTAR local stamped wind convention.

Runtime semantics are intentionally minimal and independent of GMRF:
- message frame must be ``map``;
- ``wind_direction`` is the DOWNWIND direction already published by VGR;
- speed is m/s;
- return local vector (u, v) = speed*(cos(theta), sin(theta));
- never add pi and never infer the observation position from a later TF lookup.

The observation position is the stamped robot pose joined by StampedIngress at
the same timestamp.  This module does not estimate a global wind field.
"""
from __future__ import annotations

import math

DIRECTION_CONVENTION = "downwind_vector_uv"
FRAME = "map"
UNITS = "m/s"


def decode_local_downwind(frame_id: str, wind_speed: float,
                          wind_direction: float) -> tuple[float, float]:
    if frame_id != FRAME:
        raise ValueError(f"CSTAR_WIND_FRAME:{frame_id}")
    speed = float(wind_speed)
    theta = float(wind_direction)
    if not math.isfinite(speed) or speed < 0 or not math.isfinite(theta):
        raise ValueError("CSTAR_WIND_NONFINITE_OR_NEGATIVE")
    u = speed * math.cos(theta)
    v = speed * math.sin(theta)
    if not math.isfinite(u) or not math.isfinite(v):
        raise ValueError("CSTAR_WIND_VECTOR_NONFINITE")
    return u, v

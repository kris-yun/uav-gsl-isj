"""Explicit map-position/downwind encoding for the GMRF service path.

This is NOT a wind estimator, delivery acknowledgement, deduplicator, or freshness
guarantee. Feed only unique frames from StampedIngress. Disable GMRF's native
anemometer subscription before forwarding these requests, or evidence duplicates.
"""
import math


def gmrf_request_values(stamp_ns, pose_xy, downwind_uv):
    if (type(stamp_ns) is not int or stamp_ns <= 0
            or stamp_ns % 200_000_000):
        # VGR's t=0 wind is an initialization placeholder, not a measurement.
        raise ValueError("V2_GMRF_UNOBSERVED_OR_OFF_CADENCE_WIND")
    xy, uv = tuple(pose_xy), tuple(downwind_uv)
    if len(xy) != 2 or len(uv) != 2:
        raise ValueError("V2_GMRF_VECTOR_SHAPE")
    x, y, u, v = map(float, (*xy, *uv))
    if not all(math.isfinite(z) for z in (x, y, u, v)):
        raise ValueError("V2_GMRF_NONFINITE_OBSERVATION")
    speed = math.hypot(u, v)
    if not math.isfinite(speed):
        raise ValueError("V2_GMRF_SPEED_OVERFLOW")
    return {
        "observation_stamp_ns": stamp_ns,  # audit sidecar; srv has NO stamp
        "frame": "map", "direction_convention": "downwind",
        "request": {
            "wind_speed": [speed], "wind_direction": [math.atan2(v, u)],
            "x_pos": [x], "y_pos": [y],
            # Current backend ignores these arrays and hard-codes these values.
            # Echo its behavior; neither value is a calibrated V2 error model.
            "var_speed": [.001], "var_direction": [.0001],
        },
        "variance_status": "BACKEND_FIXED_UNCALIBRATED",
        "delivery_status": "NOT_SUBMITTED",
    }

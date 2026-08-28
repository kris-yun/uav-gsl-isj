#!/usr/bin/env python3
from __future__ import annotations

import math
import numpy as np

from pf_dei_inverse_sensor_reference import (
    FrozenSensorInverseConfig,
    forward_frozen_sensor,
    invert_frozen_sensor,
    inverse_quantization_bound_ppm,
)


def main() -> int:
    cfg = FrozenSensorInverseConfig()
    dt = 0.2
    t = np.arange(50, dtype=np.float64) * dt

    # Closure evidence-style plume sequence: repeated plateaus and zero suffixes.
    physical = np.asarray(
        [0, 0, 0, 7.270297050476074, 7.270297050476074,
         21.296451568603516, 21.296451568603516, 21.296451568603516,
         12.486902236938477, 12.486902236938477,
         0, 0, 0, 0, 0,
         3, 3, 0, 0, 8,
         8, 8, 1, 1, 0,
         0, 0, 0, 5, 5,
         5, 0, 0, 0, 2,
         2, 2, 0, 0, 0,
         0, 4, 4, 0, 0,
         0, 0, 0, 0, 0],
        dtype=np.float64,
    )

    # forward_frozen_sensor emits the delayed tail too.  The first 50 measured
    # samples correspond to the 50-sample observed run interval.
    measured_full = forward_frozen_sensor(physical, cfg, sample_dt_s=dt)
    measured = measured_full[: physical.size]

    inv = invert_frozen_sensor(t, measured, cfg)
    n = inv.physical_ppm.size
    if n != physical.size - 2:
        raise AssertionError((n, physical.size))
    max_abs = float(np.max(np.abs(inv.physical_ppm - physical[:n])))
    if max_abs > 1e-12:
        raise AssertionError(f"inverse mismatch {max_abs}")

    expected_alpha = math.exp(-dt / 1.2)
    if abs(inv.alpha - expected_alpha) > 1e-15 or inv.delay_steps != 2:
        raise AssertionError("frozen timing mismatch")

    bound = inverse_quantization_bound_ppm(6, inv.alpha)
    if not (6.0e-6 < bound < 6.1e-6):
        raise AssertionError(f"unexpected serialization bound {bound}")

    # A high previous state followed by zero current physical input must retain
    # a non-zero native measured suffix; this makes the locality test live.
    if not (physical[10] == 0.0 and measured[10] > 0.1):
        raise AssertionError("sensor-memory fixture is not live")

    # Reject non-regular cadence rather than silently using an approximate inverse.
    bad_t = t.copy()
    bad_t[20:] += 1e-4
    try:
        invert_frozen_sensor(bad_t, measured, cfg)
    except ValueError:
        pass
    else:
        raise AssertionError("irregular cadence was not rejected")

    print("PF_DEI_INVERSE_SENSOR_REFERENCE_SELFTEST PASS")
    print(f"max_abs_physical_recovery_ppm={max_abs:.17g}")
    print(f"six_decimal_inverse_error_bound_ppm={bound:.17g}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

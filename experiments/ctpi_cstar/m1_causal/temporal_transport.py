"""Causal, prefix-only temporal transport provider for M1.

The provider shares only the deterministic finite-volume primitive with the
existing physical code.  It does not use CPO route prediction, first-hit laws,
posterior state, gas measurements, source labels, or future wind.  Its output
is the raw candidate exposure trace consumed by M1's sensor likelihood.
"""
from __future__ import annotations

import math
from typing import Sequence

from m2_cpo.physical_prior import PhysicalPriorConfig, _advance, _cell


def replay_candidate_exposure(prefix: Sequence[object], *, config: PhysicalPriorConfig,
                              source_xy: tuple[float, float], source_rate: float = 1.0) -> tuple[float, ...]:
    """Advance one candidate plume through a causal frame prefix.

    ``prefix[0]`` is an explicit t=0 zero-state bootstrap.  Each later frame
    is sampled at its pose after advancing from the preceding wind.  The
    returned sequence has one exposure value per non-bootstrap frame.
    """
    config.validate()
    if len(prefix) < 2 or not math.isfinite(source_rate) or source_rate <= 0:
        raise ValueError("M1_CAUSAL_TRANSPORT_INPUT")
    stamps = [int(getattr(frame, "stamp_ns")) for frame in prefix]
    dt_ns = round(config.route_dt * 1.0e9)
    if stamps[0] != 0 or any(right - left != dt_ns for left, right in zip(stamps, stamps[1:])):
        raise ValueError("M1_CAUSAL_TRANSPORT_CLOCK")
    source = _cell(config, source_xy)
    field = [0.0] * (config.nx * config.ny)
    exposure: list[float] = []
    for previous, current in zip(prefix, prefix[1:]):
        wind = tuple(float(value) for value in getattr(previous, "wind_uv"))
        pose = tuple(float(value) for value in getattr(current, "pose_xy"))
        _advance(field, config, wind, source, source_rate=source_rate,
                 duration=config.route_dt * config.transport_time_scale)
        value = float(field[_cell(config, pose)])
        if not math.isfinite(value) or value < 0:
            raise ValueError("M1_CAUSAL_TRANSPORT_OUTPUT")
        exposure.append(value)
    return tuple(exposure)

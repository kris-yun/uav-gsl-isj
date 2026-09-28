"""Bind PMFS block values to distinct VGR sensor publications.

PMFS stamps callbacks with its current /clock, which may lag one VGR
publication and may repeat despite distinct physical sensor messages. The
VGR sensor trace records the publication step/time. This audit does not edit
either log or alter the event average used by PMFS and the network.
"""
from __future__ import annotations

from functools import lru_cache
import math


def verify_distinct_vgr_samples(samples: list[dict], sensor_trace: list[dict],
                                start: float, end: float, xy: tuple[float, float]) -> dict:
    if len(samples) != 10:
        raise RuntimeError('expected ten PMFS gas callbacks')
    # A PMFS callback may see a /clock tick 0.2 s behind the VGR publication.
    nearby = [row for row in sensor_trace
              if start - .6 <= float(row['t_sim_s']) <= end + .6 and
              math.hypot(float(row['x']) - xy[0], float(row['y']) - xy[1]) <= .02]
    if len(nearby) < 10:
        raise RuntimeError('fewer than ten VGR publications near PMFS window')
    sample_values = [float(r['measured_gas_ppm']) for r in samples]
    callback_times = [float(r['sim_time']) for r in samples]
    sensor_values = [float(r['measured_gas_ppm']) for r in nearby]
    sensor_times = [float(r['t_sim_s']) for r in nearby]

    @lru_cache(None)
    def solve(i: int, begin: int):
        if i == 10:
            return (0., ())
        best = None
        for j in range(begin, len(nearby) - (10 - i) + 1):
            tolerance = 2e-5 + 5e-6 * max(1., abs(sample_values[i]))
            if (abs(sample_values[i] - sensor_values[j]) > tolerance or
                    abs(callback_times[i] - sensor_times[j]) > .6):
                continue
            suffix = solve(i + 1, j + 1)
            if suffix is None:
                continue
            cost = abs(callback_times[i] - sensor_times[j]) + suffix[0]
            candidate = (cost, (j,) + suffix[1])
            if best is None or candidate < best:
                best = candidate
        return best

    match = solve(0, 0)
    if match is None:
        raise RuntimeError('PMFS callbacks cannot map to ten distinct ordered VGR publications')
    times = [sensor_times[j] for j in match[1]]
    if any(b <= a for a, b in zip(times, times[1:])):
        raise RuntimeError('VGR publication times are not strictly increasing')
    return {'vgr_start_s': times[0], 'vgr_end_s': times[-1],
            'max_clock_lag_s': max(abs(a - b) for a, b in zip(callback_times, times)),
            'clock_collision_count': sum(b <= a for a, b in zip(callback_times, callback_times[1:]))}

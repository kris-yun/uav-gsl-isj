#!/usr/bin/env python3
"""Invoke the frozen support-extension route builder at a 5 m aperture."""

from __future__ import annotations

import math
import sys

import build_house02_global_dual_route as geometry
import build_support_extension_routes as base


SEPARATION = 5.0


def exact_baseline_is_free(occupancy, x, y, angle_deg):
    radians = math.radians(angle_deg)
    direction = (math.cos(radians), math.sin(radians), 0.0)
    center = (float(x), float(y), float(base.ALTITUDE))
    minus = tuple(center[index] - direction[index] * (SEPARATION / 2.0) for index in range(3))
    plus = tuple(center[index] + direction[index] * (SEPARATION / 2.0) for index in range(3))
    count = max(3, int(math.ceil(SEPARATION / 0.025)) + 1)
    return all(occupancy.query(tuple(minus[index] + fraction * (plus[index] - minus[index]) for index in range(3)))[0] == 0 for fraction in [index / (count - 1) for index in range(count)])


def main():
    base.SEPARATION = SEPARATION
    base.exact_baseline_is_free = exact_baseline_is_free
    base.main()


if __name__ == "__main__":
    main()

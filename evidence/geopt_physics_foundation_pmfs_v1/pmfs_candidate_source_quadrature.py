#!/usr/bin/env python3
"""Deterministic 2x2 Gauss-Legendre source quadrature for PMFS quadtree candidates."""

from __future__ import annotations

import math
from typing import List, Tuple


def gauss2_interval(a: float, b: float) -> Tuple[float, float]:
    if b < a:
        raise ValueError("interval must satisfy b >= a")
    if b == a:
        return (a, a)
    mid = 0.5 * (a + b)
    half = 0.5 * (b - a)
    t = 1.0 / math.sqrt(3.0)
    return (mid - half * t, mid + half * t)


def candidate_quadrature(
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    z: float,
) -> List[Tuple[float, float, float, float]]:
    xs = gauss2_interval(x_min, x_max)
    ys = gauss2_interval(y_min, y_max)
    pts = []
    for x in xs:
        for y in ys:
            pts.append((x, y, z, 0.25))
    return pts


def _self_test():
    pts = candidate_quadrature(-1.0, 1.0, -2.0, 2.0, 0.2)
    assert len(pts) == 4
    assert abs(sum(p[3] for p in pts) - 1.0) < 1e-12

    # Symmetry: weighted mean is rectangle center.
    mx = sum(x*w for x,y,z,w in pts)
    my = sum(y*w for x,y,z,w in pts)
    assert abs(mx) < 1e-12
    assert abs(my) < 1e-12

    # Tensor Gauss-2 integrates quadratics exactly in each dimension.
    ex2 = sum((x*x)*w for x,y,z,w in pts)
    ey2 = sum((y*y)*w for x,y,z,w in pts)
    # Uniform rectangle expectations: E[x^2]=1/3, E[y^2]=4/3.
    assert abs(ex2 - 1.0/3.0) < 1e-12
    assert abs(ey2 - 4.0/3.0) < 1e-12


if __name__ == "__main__":
    _self_test()
    print("PMFS quadtree source quadrature F0: PASS")

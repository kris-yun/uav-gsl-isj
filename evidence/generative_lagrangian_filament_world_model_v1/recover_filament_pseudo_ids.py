#!/usr/bin/env python3
"""Specification/reference code for GADEN filament pseudo-ID recovery.

This script intentionally leaves binary iteration-file loading to the installed
GADEN PlaybackSimulation/core API. The identity logic is independent of file
compression.

Required per saved frame:
    simulation_step
    list of filaments with (x,y,z,sigma)

For the frozen project generator:
    dt=0.1
    gamma=15.0
    initial_sigma=10.0
    release_rate=7 / s
"""

from __future__ import annotations

import math


def sigma_table(initial_sigma: float, gamma: float, dt: float, max_age_steps: int):
    vals = [float(initial_sigma)]
    s = float(initial_sigma)
    for _ in range(max_age_steps):
        s = s + gamma / (2.0 * s) * dt
        vals.append(s)
    return vals


def infer_age_steps(
    sigma: float,
    table,
    *,
    atol: float = 2e-5,
):
    best = min(range(len(table)), key=lambda i: abs(table[i] - sigma))
    err = abs(table[best] - sigma)
    if err > atol:
        raise ValueError(
            f"sigma={sigma:.9g} does not match deterministic age table; "
            f"nearest age={best}, error={err:.3g}"
        )
    return best


def pseudo_id(
    current_simulation_step: int,
    sigma: float,
    table,
):
    age = infer_age_steps(sigma, table)
    return current_simulation_step - age


def release_schedule(rate_hz: float, dt: float, num_steps: int):
    """Replicate GADEN releaseAccumulator logic."""
    acc = 0.0
    out = []
    per_step = rate_hz * dt
    for step in range(num_steps):
        acc += per_step
        births = math.floor(acc)
        acc -= births
        out.append(births)
    return out


def self_test():
    sched = release_schedule(7.0, 0.1, 100)
    assert max(sched) <= 1, max(sched)

    tab = sigma_table(10.0, 15.0, 0.1, 10000)
    for age in (0, 1, 5, 50, 500):
        got = infer_age_steps(tab[age], tab)
        assert got == age

    print("pseudo-ID algebra self-test: PASS")
    print(f"max births/step at 7Hz, dt=0.1: {max(sched)}")


if __name__ == "__main__":
    self_test()

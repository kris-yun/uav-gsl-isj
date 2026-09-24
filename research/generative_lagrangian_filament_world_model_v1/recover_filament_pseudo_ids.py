#!/usr/bin/env python3
"""GADEN filament pseudo-ID recovery utilities.

Scientific contract
-------------------
For the frozen 2026-09-22 generator:
    deltaTime=0.1 s
    saveDeltaTime=0.5 s
    filamentGrowthGamma=15.0 cm^2/s
    filamentInitialSigma=10.0 cm
    numFilaments_sec=7

GADEN executes:
    AddFilaments -> MoveFilaments (including sigma growth) -> SaveResults

Therefore a filament born at simulation step b has already undergone one
sigma update when it is first visible. If its sigma corresponds to
age_updates growth updates in a frame saved at current simulation step k,

    birth_step = k - age_updates + 1.

The iteration file number is NOT the simulation step. This module reconstructs
the exact save-step schedule with float32 arithmetic matching GADEN.
"""

from __future__ import annotations

import math
import struct


def f32(x: float) -> float:
    """Round to IEEE-754 float32, matching GADEN's float state."""
    return struct.unpack("<f", struct.pack("<f", float(x)))[0]


def sigma_table(
    initial_sigma: float,
    gamma: float,
    dt: float,
    max_age_updates: int,
):
    """Return sigma after 0..max_age_updates growth updates."""
    s = f32(initial_sigma)
    g = f32(gamma)
    dt = f32(dt)
    vals = [s]
    for _ in range(max_age_updates):
        denom = f32(f32(2.0) * s)
        inc = f32(f32(g / denom) * dt)
        s = f32(s + inc)
        vals.append(s)
    return vals


def infer_age_updates(
    sigma: float,
    table,
    *,
    atol: float = 5e-5,
):
    """Infer number of completed sigma-growth updates."""
    sigma = f32(sigma)
    best = min(range(len(table)), key=lambda i: abs(table[i] - sigma))
    err = abs(table[best] - sigma)
    if err > atol:
        raise ValueError(
            f"sigma={sigma:.9g} does not match deterministic age table; "
            f"nearest updates={best}, error={err:.3g}"
        )
    return best


def pseudo_birth_step(
    current_simulation_step: int,
    sigma: float,
    table,
):
    age_updates = infer_age_updates(sigma, table)
    if age_updates < 1:
        raise ValueError(
            "active saved filament cannot have zero sigma updates because "
            "GADEN moves/grows it before SaveResults"
        )
    return current_simulation_step - age_updates + 1


def release_schedule(rate_hz: float, dt: float, num_steps: int):
    """Replicate GADEN releaseAccumulator logic with float32 state."""
    acc = f32(0.0)
    per_step = f32(f32(rate_hz) * f32(dt))
    out = []
    for _ in range(num_steps):
        acc = f32(acc + per_step)
        births = math.floor(acc)
        acc = f32(acc - births)
        out.append(births)
    return out


def save_step_schedule(
    sim_time: float,
    dt: float,
    save_dt: float,
):
    """Map result-file index to (simulation step, float32 currentTime)."""
    current_time = f32(0.0)
    last_save = f32(-3.4028234663852886e38)  # -FLT_MAX
    dt = f32(dt)
    save_dt = f32(save_dt)

    out = []
    step = 0
    while current_time < float(sim_time):
        if current_time > f32(last_save + save_dt):
            out.append((step, current_time))
            last_save = current_time
        current_time = f32(current_time + dt)
        step += 1
    return out


def self_test():
    sched = release_schedule(7.0, 0.1, 10000)
    assert max(sched) <= 1, max(sched)

    # Exact frozen save schedule reproduces all six provenance manifests.
    saves = save_step_schedule(1000.0, 0.1, 0.5)
    assert len(saves) == 1803, len(saves)
    assert saves[0][0] == 0
    assert saves[1][0] == 6
    assert saves[-1][0] == 9996

    tab = sigma_table(10.0, 15.0, 0.1, 10050)
    for age_updates in (1, 2, 5, 50, 500, 5000):
        got = infer_age_updates(tab[age_updates], tab)
        assert got == age_updates

    # Born at b, after n updates it is visible at step k=b+n-1.
    for birth_step, age_updates in ((1, 1), (1, 5), (17, 100), (2500, 700)):
        current_step = birth_step + age_updates - 1
        got = pseudo_birth_step(current_step, tab[age_updates], tab)
        assert got == birth_step, (birth_step, age_updates, got)

    print("pseudo-ID algebra self-test: PASS")
    print(f"max births/step at 7Hz, dt=0.1: {max(sched)}")
    print(f"1000s save frames at dt=0.1/save_dt=0.5: {len(saves)}")
    print(f"last saved simulation step: {saves[-1][0]}")
    print(f"last saved currentTime(float32): {saves[-1][1]:.9f}")


if __name__ == "__main__":
    self_test()

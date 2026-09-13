"""MOX rise/recovery + dead-time observation perturbation (frozen contract).

The MOX nuisance acts on the observation operator. For a fixed candidate map
g_s we define the MOX-distorted prediction:
    MOX(g; tau) = g * (1 - exp(-g / tau))      (rise/saturation)
and the atom is MOX(g; tau+) - MOX(g; tau-), same underlying map -> CRN holds.
Dead-time is represented by a conservative saturation floor.
Magnitudes frozen: tau_nominal = 0.5, delta = 0.2*tau_nominal.
"""

from __future__ import annotations

import numpy as np

TAU_NOM = 0.5
TAU_DELTA = 0.1


def mox_atoms(maps: np.ndarray) -> np.ndarray:
    """(C, N) -> (C, N) atoms MOX(tau+)-MOX(tau-)."""
    tau_p = TAU_NOM + TAU_DELTA
    tau_m = TAU_NOM - TAU_DELTA
    mp = maps * (1.0 - np.exp(-maps / tau_p))
    mm = maps * (1.0 - np.exp(-maps / tau_m))
    return mp - mm

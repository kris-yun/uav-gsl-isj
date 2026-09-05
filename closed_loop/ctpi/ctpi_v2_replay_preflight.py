"""Pure scheduling preflight; never change a seed or launch a simulator.

Mirrors the verified legacy seeded_time_replay formula. A wrap is a requirement
for physical seam evidence, NOT proof of a concentration discontinuity. Passing
this narrow check does not validate native frame duration or a transport model.
"""
import math


def audit_replay(max_iteration: int, seed: int, dt_s: float, horizon_s: float):
    if type(max_iteration) is not int or max_iteration < 2 or type(seed) is not int:
        raise ValueError("invalid replay identity")
    if not all(math.isfinite(x) and x > 0 for x in (dt_s, horizon_s)):
        raise ValueError("invalid replay clock")
    steps = round(horizon_s / dt_s)
    if steps < 1 or abs(steps * dt_s - horizon_s) > 1e-9:
        raise ValueError("horizon must be an integral number of steps")
    usable = max_iteration - 1
    offset = (7919 * (seed + 1)) % usable
    first_wrap_step = usable - offset
    wraps = list(range(first_wrap_step, steps + 1, usable))
    return {
        "max_iteration": max_iteration, "seed": seed, "dt_s": dt_s,
        "horizon_s": horizon_s, "offset": offset,
        "first_observed_iteration": (offset + 1) % usable,
        "last_observed_iteration": (offset + steps) % usable,
        "wraps": [{"step": step, "time_s": round(step * dt_s, 9),
                   "previous_iteration": usable - 1, "iteration": 0} for step in wraps],
        "status": "REPLAY_SEAM_PHYSICAL_CONTINUITY_UNQUALIFIED" if wraps else "NO_INDEX_WRAP_ONLY",
        "continuous_transport_qualified": False,
        "remaining_evidence": ["Native field-frame interval matches simulated elapsed time",
                               "Every crossed replay seam has a physically supported transition"] if wraps else [
                                   "Native field-frame interval matches simulated elapsed time"],
    }

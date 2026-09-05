"""Conditional ROS1 release operator, NOT an inferred House source prior.

Tracks nominal fractional carry even when the actual random release is zero.
One latent rate/carry path must persist across observations of the same source.
Rate, initial carry and PRNG-residue probabilities have no hidden defaults.
This does not establish PRNG independence, historical generator identity,
source identifiability, or a concentration-per-filament conversion.
"""
import math
from fractions import Fraction


def nominal_step(carry, rate_per_native_second, native_dt):
    """Binary64 recurrence of the pinned ROS1 nominal counter; pure/transactional."""
    carry, rate, dt = map(float, (carry, rate_per_native_second, native_dt))
    if not all(math.isfinite(x) for x in (carry, rate, dt)):
        raise ValueError("nonfinite release input")
    if not 0 <= carry < 1 or rate < 0 or dt <= 0:
        raise ValueError("invalid carry/rate/native time")
    accumulated = carry + rate * dt
    if not math.isfinite(accumulated) or accumulated >= 2**31:
        raise ValueError("release count exceeds ROS1 int domain")
    cap = math.floor(accumulated)
    return cap, accumulated - cap


def release_count(cap, residue):
    """Map an explicitly supplied rand()%100 residue using positive C++ round."""
    if type(cap) is not int or not 0 <= cap < 2**31:
        raise ValueError("invalid nominal count")
    if type(residue) is not int or not 0 <= residue < 100:
        raise ValueError("residue must be an integer in [0, 100)")
    value = (float(residue) / 100.0) * cap
    # Avoid Python's ties-to-even round. No random stream is generated here.
    return math.floor(value) + int(value - math.floor(value) >= .5)


def conditional_count_law(cap, residue_probabilities):
    """Exact mass aggregation GIVEN an explicit residue law, not an iid claim.

    A sequence model must supply probabilities conditional on its own history.
    Uniform residues are a test assumption, not an assertion about C rand().
    """
    weights = tuple(Fraction(w) for w in residue_probabilities)
    if len(weights) != 100 or min(weights) < 0 or sum(weights) != 1:
        raise ValueError("supply 100 nonnegative probabilities summing exactly to 1")
    result = {}
    for residue, weight in enumerate(weights):
        count = release_count(cap, residue)
        if weight:
            result[count] = result.get(count, Fraction(0)) + weight
    return result

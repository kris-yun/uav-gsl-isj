"""Pure CPU reference contracts for CSTAR (2026-09-06).

This file is intentionally independent of ROS, source truth and any predictive bank.
It freezes the exact probability algebra shared by the future M2 CPO provider and
M3 PHS planner before either is connected to closed loop.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence


def _finite_nonnegative(values: Sequence[float], name: str) -> list[float]:
    out = [float(v) for v in values]
    if not out or any((not math.isfinite(v) or v < 0.0) for v in out):
        raise ValueError(f"CSTAR_INVALID_{name}")
    return out


def normalize_probability(values: Sequence[float]) -> list[float]:
    out = _finite_nonnegative(values, "PROBABILITY")
    total = math.fsum(out)
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("CSTAR_EMPTY_PROBABILITY")
    result = [v / total for v in out]
    if abs(math.fsum(result) - 1.0) > 1e-12:
        raise ValueError("CSTAR_PROBABILITY_NORMALIZATION")
    return result


def hazards_to_first_passage(hazards: Sequence[float]) -> list[float]:
    """Convert conditional encounter hazards to P(T=1..H, T>H).

    h_j = P(T=j | T>=j, causal state, source, do(route)).
    No independence claim beyond this sequential conditional factorization is made.
    """
    hs = [float(h) for h in hazards]
    if not hs or any((not math.isfinite(h) or h < 0.0 or h > 1.0) for h in hs):
        raise ValueError("CSTAR_INVALID_HAZARD")
    survive = 1.0
    law: list[float] = []
    for h in hs:
        law.append(survive * h)
        survive *= 1.0 - h
    law.append(survive)
    if any(p < -1e-14 or not math.isfinite(p) for p in law):
        raise ValueError("CSTAR_FIRST_PASSAGE_NUMERIC")
    return normalize_probability([max(0.0, p) for p in law])


def first_passage_to_encounter_cdf(first_passage: Sequence[float]) -> list[float]:
    """Return F_h=P(T<=h), excluding the terminal no-hit category.

    This is a first-passage CDF. The scalar final value is the route committor:
    probability of reaching the encounter set before the route/horizon terminates.
    """
    law = normalize_probability(first_passage)
    if len(law) < 2:
        raise ValueError("CSTAR_FIRST_PASSAGE_NEEDS_HORIZON")
    result: list[float] = []
    cumulative = 0.0
    for p in law[:-1]:
        cumulative += p
        result.append(cumulative)
    if any(result[i] > result[i + 1] + 1e-14 for i in range(len(result) - 1)):
        raise ValueError("CSTAR_ENCOUNTER_CDF_NONMONOTONE")
    return result


def route_committor(first_passage: Sequence[float]) -> float:
    cdf = first_passage_to_encounter_cdf(first_passage)
    return cdf[-1]


def bhattacharyya_coefficient(p: Sequence[float], q: Sequence[float]) -> float:
    """BC(P,Q) in [0,1] for equal categorical supports."""
    pp = normalize_probability(p)
    qq = normalize_probability(q)
    if len(pp) != len(qq):
        raise ValueError("CSTAR_LAW_SUPPORT_MISMATCH")
    bc = math.fsum(math.sqrt(a * b) for a, b in zip(pp, qq))
    if bc < -1e-12 or bc > 1.0 + 1e-12 or not math.isfinite(bc):
        raise ValueError("CSTAR_BHATTACHARYYA_RANGE")
    return min(1.0, max(0.0, bc))


@dataclass(frozen=True)
class RouteResolution:
    route_index: int
    resolution: float
    normalized_confusion: float
    pair_weight_sum: float


def prospective_resolution_scores(
    posterior: Sequence[float],
    route_laws: Sequence[Sequence[Sequence[float]]],
) -> list[RouteResolution]:
    """PHS reference score.

    route_laws[source][route][outcome]. The outcome support must be identical
    across every source and route. For each route:

      B(tau) = sum_{i<j} sqrt(pi_i*pi_j) BC(P_i^tau,P_j^tau)
      Resolution = 1 - B/Z, Z=sum_{i<j} sqrt(pi_i*pi_j).

    The function contains no travel or exploitation weight. Geometry/feasibility
    belongs outside this pure information calculation.
    """
    pi = normalize_probability(posterior)
    source_count = len(pi)
    if source_count < 2 or len(route_laws) != source_count:
        raise ValueError("CSTAR_SOURCE_SHAPE")
    route_count = len(route_laws[0])
    if route_count < 1 or any(len(s) != route_count for s in route_laws):
        raise ValueError("CSTAR_ROUTE_SHAPE")

    support = None
    normalized: list[list[list[float]]] = []
    for source in route_laws:
        row: list[list[float]] = []
        for law in source:
            nl = normalize_probability(law)
            support = len(nl) if support is None else support
            if len(nl) != support:
                raise ValueError("CSTAR_LAW_SUPPORT_MISMATCH")
            row.append(nl)
        normalized.append(row)

    pair_weights: list[tuple[int, int, float]] = []
    for i in range(source_count):
        for j in range(i + 1, source_count):
            w = math.sqrt(pi[i] * pi[j])
            if w > 0.0:
                pair_weights.append((i, j, w))
    z = math.fsum(w for _, _, w in pair_weights)
    if not math.isfinite(z) or z <= 0.0:
        return [RouteResolution(r, 0.0, 0.0, 0.0) for r in range(route_count)]

    result: list[RouteResolution] = []
    for r in range(route_count):
        confusion = 0.0
        for i, j, w in pair_weights:
            confusion += w * bhattacharyya_coefficient(
                normalized[i][r], normalized[j][r]
            )
        normalized_confusion = confusion / z
        resolution = 1.0 - normalized_confusion
        if (
            resolution < -1e-12
            or resolution > 1.0 + 1e-12
            or not math.isfinite(resolution)
        ):
            raise ValueError("CSTAR_RESOLUTION_RANGE")
        result.append(
            RouteResolution(
                route_index=r,
                resolution=min(1.0, max(0.0, resolution)),
                normalized_confusion=min(1.0, max(0.0, normalized_confusion)),
                pair_weight_sum=z,
            )
        )
    return result


def select_route(
    posterior: Sequence[float],
    route_laws: Sequence[Sequence[Sequence[float]]],
    travel_distance: Sequence[float],
) -> RouteResolution:
    """Choose max resolution; distance then index are deterministic tie-breaks."""
    scores = prospective_resolution_scores(posterior, route_laws)
    distances = [float(d) for d in travel_distance]
    if len(distances) != len(scores) or any(
        (not math.isfinite(d) or d < 0.0) for d in distances
    ):
        raise ValueError("CSTAR_TRAVEL_SHAPE_OR_VALUE")
    return min(
        scores,
        key=lambda item: (
            -item.resolution, distances[item.route_index], item.route_index
        ),
    )


@dataclass(frozen=True)
class CPORouteLaw:
    """Minimal versioned M2->M3 contract for one source and one future route."""

    first_hit_prob: tuple[float, ...]
    encounter_cdf: tuple[float, ...]
    route_committor: float
    logppm_mean: tuple[float, ...]
    logppm_scale: tuple[float, ...]

    @staticmethod
    def from_hazards(
        hazards: Sequence[float],
        logppm_mean: Sequence[float],
        logppm_scale: Sequence[float],
    ) -> "CPORouteLaw":
        law = hazards_to_first_passage(hazards)
        cdf = first_passage_to_encounter_cdf(law)
        q_route = cdf[-1]
        mu = [float(v) for v in logppm_mean]
        scale = [float(v) for v in logppm_scale]
        if len(mu) != len(cdf) or len(scale) != len(cdf):
            raise ValueError("CSTAR_MARK_HORIZON")
        if any(not math.isfinite(v) for v in mu):
            raise ValueError("CSTAR_MARK_MEAN")
        if any((not math.isfinite(v) or v <= 0.0) for v in scale):
            raise ValueError("CSTAR_MARK_SCALE")
        return CPORouteLaw(
            tuple(law), tuple(cdf), q_route, tuple(mu), tuple(scale)
        )

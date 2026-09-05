"""CSTAR M3 PHS research reference.

This module adds the source-region marginalization that the legacy CTPI planner
lacked, then delegates the exact source-confusion algebra to cstar_reference.
It is pure CPU research code: no ROS, truth or predictive bank access.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from cstar_reference import normalize_probability, select_route, prospective_resolution_scores


def marginalize_region_laws(
    placement_laws: Sequence[Sequence[Sequence[Sequence[float]]]],
    placement_weights: Sequence[Sequence[float]],
) -> list[list[list[float]]]:
    """Mix physical-placement laws within each region source hypothesis.

    placement_laws[region][placement][route][outcome].
    placement_weights[region][placement] is a frozen geometry-only quadrature.

    Returns region_laws[region][route][outcome]. No posterior or source truth is
    used in the within-region mixture.
    """
    region_count = len(placement_laws)
    if region_count < 2 or len(placement_weights) != region_count:
        raise ValueError("CSTAR_PHS_REGION_SHAPE")

    result: list[list[list[float]]] = []
    route_count = None
    outcome_count = None
    for r in range(region_count):
        placements = placement_laws[r]
        weights = normalize_probability(placement_weights[r])
        if not placements or len(placements) != len(weights):
            raise ValueError("CSTAR_PHS_PLACEMENT_SHAPE")
        route_count = len(placements[0]) if route_count is None else route_count
        if route_count < 1 or any(len(p) != route_count for p in placements):
            raise ValueError("CSTAR_PHS_ROUTE_SHAPE")

        region_routes: list[list[float]] = []
        for route in range(route_count):
            normalized_placements = [normalize_probability(p[route]) for p in placements]
            if outcome_count is None:
                outcome_count = len(normalized_placements[0])
            if any(len(law) != outcome_count for law in normalized_placements):
                raise ValueError("CSTAR_PHS_OUTCOME_SUPPORT")
            mixed = [0.0] * outcome_count
            for w, law in zip(weights, normalized_placements):
                for k, prob in enumerate(law):
                    mixed[k] += w * prob
            region_routes.append(normalize_probability(mixed))
        result.append(region_routes)
    return result


@dataclass(frozen=True)
class PHSDecision:
    selected_route: int
    resolution: float
    normalized_confusion: float
    region_route_laws: tuple


def decide_from_region_placements(
    posterior_region_mass: Sequence[float],
    placement_laws: Sequence[Sequence[Sequence[Sequence[float]]]],
    placement_weights: Sequence[Sequence[float]],
    travel_distance: Sequence[float],
) -> PHSDecision:
    region_laws = marginalize_region_laws(placement_laws, placement_weights)
    chosen = select_route(posterior_region_mass, region_laws, travel_distance)
    return PHSDecision(
        selected_route=chosen.route_index,
        resolution=chosen.resolution,
        normalized_confusion=chosen.normalized_confusion,
        region_route_laws=tuple(
            tuple(tuple(law) for law in routes) for routes in region_laws
        ),
    )


def score_region_routes(
    posterior_region_mass: Sequence[float],
    placement_laws: Sequence[Sequence[Sequence[Sequence[float]]]],
    placement_weights: Sequence[Sequence[float]],
):
    region_laws = marginalize_region_laws(placement_laws, placement_weights)
    return prospective_resolution_scores(posterior_region_mass, region_laws)

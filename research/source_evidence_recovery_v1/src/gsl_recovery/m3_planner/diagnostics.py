"""Read-only decomposition of model-conditional counterevidence power.

Every layer solves the existing risk-constrained LP with the SAME alpha,
source hypotheses, action block and generator samples. Relaxations are for
diagnosis only: they neither replace the deployed test nor spend or reset its
risk budget. In particular, a low diagnostic power is not a statement about
physical identifiability of the real gas source.
"""
from __future__ import annotations

import numpy as np

from ..m3_codebook.channel import CorruptionChannel
from .planner import solve_robust_test


LAYER_ORDER = (
    "nominal_clean",
    "all_mechanisms_clean",
    "all_mechanisms_corruption",
    "all_mechanisms_corruption_tv",
)


def _index(value, size, label):
    try:
        parsed = int(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError(f"{label} must be an integer index") from exc
    if parsed != value or not 0 <= parsed < size:
        raise ValueError(f"{label} must be an integer index in [0, {size})")
    return parsed


def _tv_witness(probabilities, radii, null_source, challengers, alpha):
    """Pairwise necessary bounds, including a finite-TV intersection witness.

    A level-alpha test has power at most alpha + TV(P,Q) against any one
    null/alternative pair. TV balls reduce their minimum distance to
    max(0, TV(P,Q)-r_P-r_Q). A corruption channel contains its clean identity
    action, so this remains a (possibly loose) upper bound for our robust
    problem. It is conditional on the supplied model ambiguity sets.
    """
    records = []
    for source in challengers:
        for null_mechanism in range(probabilities.shape[1]):
            for alt_mechanism in range(probabilities.shape[1]):
                distance = float(0.5 * np.abs(
                    probabilities[null_source, null_mechanism]
                    - probabilities[source, alt_mechanism]).sum())
                nr = float(radii[null_source, null_mechanism])
                ar = float(radii[source, alt_mechanism])
                residual = max(0.0, distance - nr - ar)
                records.append({
                    "null_source": null_source,
                    "null_mechanism": null_mechanism,
                    "alternative_source": source,
                    "alternative_mechanism": alt_mechanism,
                    "clean_tv_distance": distance,
                    "null_tv_radius": nr,
                    "alternative_tv_radius": ar,
                    "tv_ball_minimum_distance": residual,
                    "tv_balls_intersect": bool(distance <= nr + ar + 1e-12),
                    "clean_pair_power_upper_bound": min(1.0, alpha + distance),
                    "tv_pair_power_upper_bound": min(1.0, alpha + residual),
                })
    return {
        "closest_clean_pair": min(records, key=lambda r: r["clean_tv_distance"]),
        "closest_tv_ambiguity_pair": min(records, key=lambda r: r["tv_ball_minimum_distance"]),
        "scope": "necessary_pairwise_model_bound_not_physical_identifiability",
    }


def diagnose_counterevidence_layers(codebook, null_source, challenge_indices, *,
                                   channel=None, alpha=0.05, nominal_mechanism=0,
                                   power_tolerance=1e-12):
    """Return a JSON-serializable four-layer diagnostic for one frozen book.

    ``nominal_mechanism`` is the preregistered nominal column, not a column
    selected for high power after observing the results. The two nominal/all
    clean layers use no extra contamination and zero TV radii; the third uses
    the declared contamination channel; the fourth also uses the book's
    original TV radii. Ordinary joint plume randomness remains in every law.

    Pass the same alpha that the planner used (normally
    ``planner.risk.next_alpha()`` before reservation). No alpha, draws, TV
    radius, mechanism list or contamination budget is changed in place.
    Returned fallback is for this block; planner-wide fallback additionally
    requires no eligible block to provide certified gain. ``power_tolerance``
    applies to cost-normalized gain, matching the planner's 1e-12 threshold.
    """
    p = np.asarray(codebook.probabilities, dtype=float)
    if p.ndim != 3 or min(p.shape) < 1:
        raise ValueError("Expected nonempty [source, mechanism, word] codebook")
    if (np.any(~np.isfinite(p)) or np.any(p < 0)
            or not np.allclose(p.sum(axis=-1), 1.0, atol=1e-9)):
        raise ValueError("Invalid codebook probability laws")
    if p.shape[-1] != 2 ** len(codebook.actions):
        raise ValueError("Codebook word support and action block disagree")
    radii = np.asarray(codebook.tv_radius, dtype=float)
    if (radii.shape != p.shape[:2] or np.any(~np.isfinite(radii))
            or np.any(radii < 0) or np.any(radii > 1)):
        raise ValueError("Invalid codebook TV radii")
    if not np.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError("alpha must lie in (0,1)")
    if not np.isfinite(power_tolerance) or power_tolerance < 0:
        raise ValueError("power_tolerance must be finite and nonnegative")
    if not np.isfinite(codebook.cost) or codebook.cost <= 0:
        raise ValueError("Action cost must be finite and positive")
    h = _index(null_source, p.shape[0], "null_source")
    nominal = _index(nominal_mechanism, p.shape[1], "nominal_mechanism")
    challengers = [_index(s, p.shape[0], "challenge source") for s in challenge_indices]
    if not challengers or h in challengers or len(set(challengers)) != len(challengers):
        raise ValueError("Challenge sources must be distinct, nonempty, and exclude the null")
    channel = CorruptionChannel() if channel is None else channel
    clean_channel = CorruptionChannel()
    configurations = (
        (LAYER_ORDER[0], p[h, nominal][None, :], p[challengers, nominal],
         clean_channel, 0.0, 0.0),
        (LAYER_ORDER[1], p[h], p[challengers].reshape(-1, p.shape[-1]),
         clean_channel, 0.0, 0.0),
        (LAYER_ORDER[2], p[h], p[challengers].reshape(-1, p.shape[-1]),
         channel, 0.0, 0.0),
        (LAYER_ORDER[3], p[h], p[challengers].reshape(-1, p.shape[-1]),
         channel, radii[h], radii[challengers].ravel()),
    )
    layers = {}
    for name, nulls, alternatives, error_channel, nr, ar in configurations:
        test = solve_robust_test(
            nulls, alternatives, channel=error_channel, alpha=float(alpha),
            null_radius=nr, alternative_radius=ar,
            model_version=str(codebook.model_version),
        )
        # `power` is the optimized conservative LP objective. The independent
        # finite-TV recomputation may certify a higher power for that solution.
        # Both are reported: do not silently equate them under nonzero TV.
        excess = float(test.alternative_power_bound - alpha)
        layers[name] = {
            "alpha": float(alpha),
            "null_hypotheses": int(len(nulls)),
            "alternative_hypotheses": int(len(alternatives)),
            "lp_power": float(test.power),
            "power_bound": float(test.alternative_power_bound),
            "null_risk_bound": float(test.null_risk_bound),
            "risk_slack": float(alpha - test.null_risk_bound),
            "power_excess_over_alpha": excess,
            "cost_adjusted_gain": max(0.0, excess) / float(codebook.cost),
            "has_certified_gain": bool(max(0.0, excess) / float(codebook.cost) > power_tolerance),
            "null_tv_radius_max": float(np.max(nr)),
            "alternative_tv_radius_max": float(np.max(ar)),
            "corruption": {
                "max_flips": int(error_channel.max_flips),
                "max_erasures": int(error_channel.max_erasures),
                "max_burst": int(error_channel.max_burst),
            },
            "solver_status": test.status,
        }
    full = layers[LAYER_ORDER[-1]]
    fallback = not full["has_certified_gain"]
    reasons = (
        "nominal_model_response_overlap",
        "declared_mechanism_ambiguity",
        "declared_corruption_budget",
        "tv_uncertainty_or_conservative_tv_lp",
    )
    bottleneck = {
        "cause": "none_for_this_block",
        "layer": LAYER_ORDER[-1],
        "power_bound": full["power_bound"],
        "alpha": float(alpha),
        "power_excess_over_alpha": full["power_excess_over_alpha"],
    }
    if fallback:
        for name, cause in zip(LAYER_ORDER, reasons):
            if not layers[name]["has_certified_gain"]:
                bottleneck = {
                    "cause": cause,
                    "layer": name,
                    "power_bound": layers[name]["power_bound"],
                    "alpha": float(alpha),
                    "power_excess_over_alpha": layers[name]["power_excess_over_alpha"],
                    "interpretation": "first_relaxed_layer_without_a_certified_gain_for_this_model",
                }
                break
    lp_losses = {
        "adding_mechanisms": layers[LAYER_ORDER[0]]["lp_power"] - layers[LAYER_ORDER[1]]["lp_power"],
        "adding_corruption": layers[LAYER_ORDER[1]]["lp_power"] - layers[LAYER_ORDER[2]]["lp_power"],
        "adding_tv_uncertainty": layers[LAYER_ORDER[2]]["lp_power"] - layers[LAYER_ORDER[3]]["lp_power"],
    }
    return {
        "status": "COMPLETED_MODEL_CONDITIONAL_DIAGNOSTIC",
        "scope": "one_frozen_generator_codebook_not_physical_identifiability",
        "model_version": str(codebook.model_version),
        "null_source": h,
        "challenge_indices": challengers,
        "nominal_mechanism": nominal,
        "alpha": float(alpha),
        "cost_normalized_gain_tolerance": float(power_tolerance),
        "length": int(codebook.length),
        "word_alphabet_size": int(p.shape[-1]),
        "draws": int(codebook.draws),
        "exact_codebook": bool(codebook.exact),
        "confidence_failure_probability": float(codebook.confidence_failure_probability),
        "tv_radius_min": float(radii.min()),
        "tv_radius_max": float(radii.max()),
        "layer_order": list(LAYER_ORDER),
        "layers": layers,
        "lp_power_losses": lp_losses,
        "nested_lp_power_within_numerical_tolerance": bool(min(lp_losses.values()) >= -2e-7),
        "fallback_for_this_block": fallback,
        "bottleneck": bottleneck,
        "pairwise_necessary_bounds": _tv_witness(p, radii, h, challengers, float(alpha)),
        "risk_budget_spent": 0.0,
        "action_taken": False,
        "limitations": [
            "Relaxed-layer tests are diagnostic and must not replace the committed robust test.",
            "A layer's failure does not prove physical source non-identifiability.",
            "MC bounds describe sampling inside the generator, not physical model discrepancy.",
            "The nonzero-TV LP uses a conservative range-times-radius constraint; exact recomputed power is a certificate for its chosen test, not a globally optimal exact-TV power.",
            "No adaptive sampling or new confidence allocation is performed.",
        ],
    }

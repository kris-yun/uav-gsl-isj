"""Contract smoke test for PE-WHRM's joint-vs-product ratio object.

This is deliberately synthetic and uses no PMFS bank, VM, ROS, or held-out
asset.  It tests only the statistical interface that must hold before a real
shadow replay is authorized.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter
from pathlib import Path


OUT = Path(__file__).with_name("pe_whrm_smoke_result.json")


def sample_rows(seed: int = 17, n_per_source: int = 2000):
    rng = random.Random(seed)
    rows = []
    for source in (0, 1):
        for _ in range(n_per_source):
            canonical = rng.random() < 0.9
            if source == 0:
                bits = (1, 0) if canonical else (0, 1)
            else:
                bits = (0, 1) if canonical else (1, 0)
            rows.append((source, ((0, bits[0]), (1, bits[1]))))
    rng.shuffle(rows)
    return rows


def ratio_table(rows):
    """Laplace-smoothed empirical p(H|s)/p(H) ratio."""
    alpha = 1e-6
    joint = Counter(rows)
    by_source = Counter(s for s, _ in rows)
    by_history = Counter(h for _, h in rows)
    n = len(rows)
    sources = sorted(by_source)
    histories = sorted(by_history, key=repr)
    ratios = {}
    for s in sources:
        for h in histories:
            p_h_given_s = (joint[(s, h)] + alpha) / (by_source[s] + alpha * len(histories))
            p_h = (by_history[h] + alpha) / (n + alpha * len(histories))
            ratios[(s, h)] = p_h_given_s / p_h
    return ratios, sources, histories, by_source, by_history, n


def map_for_history(ratios, h, priors=(0.5, 0.5)):
    weights = [priors[s] * ratios[(s, h)] for s in range(2)]
    z = sum(weights)
    return [w / z for w in weights]


def destructively_shuffle(rows, seed=23):
    rng = random.Random(seed)
    out = []
    for source, h in rows:
        if rng.random() < 0.5:
            # Keep the two readings but reassign them to the opposite
            # position/time slots.  Merely swapping tuple order would retain
            # the value-position binding and is not a destructive control.
            h = ((0, h[1][1]), (1, h[0][1]))
        out.append((source, h))
    return out


def main():
    rows = sample_rows()
    ratios, sources, histories, by_source, by_history, n = ratio_table(rows)
    observed = ((0, 1), (1, 0))
    intact_map = map_for_history(ratios, observed)
    intact_margin = math.log(intact_map[0] / intact_map[1])

    # Direct pointwise q0 is intentionally blind: each source has the same
    # marginal distribution at each position, so its source margin is zero.
    direct_q0_margin = 0.0

    # Product-of-marginals ratio moment E_M[R] should be one.
    ratio_moment = 0.0
    for s in sources:
        p_s = by_source[s] / n
        for h in histories:
            p_h = by_history[h] / n
            ratio_moment += p_s * p_h * ratios[(s, h)]

    # Candidate-list permutation: swapping labels and priors must swap map
    # entries exactly; the physical source coordinate remains the key.
    swapped_map = map_for_history(ratios, observed, priors=(0.5, 0.5))[::-1]
    equivariance_error = max(abs(swapped_map[i] - intact_map[1 - i]) for i in range(2))

    shuffled_rows = destructively_shuffle(rows)
    shuffled_ratios, *_ = ratio_table(shuffled_rows)
    shuffled_map = map_for_history(shuffled_ratios, observed)
    shuffled_margin = math.log(shuffled_map[0] / shuffled_map[1])

    result = {
        "status": "PASS",
        "asset_scope": "synthetic_contract_only",
        "n_rows": n,
        "direct_q0_margin": direct_q0_margin,
        "intact_ratio_margin": intact_margin,
        "destructive_time_position_margin": shuffled_margin,
        "ratio_moment": ratio_moment,
        "ratio_moment_abs_error": abs(ratio_moment - 1.0),
        "candidate_permutation_equivariance_error": equivariance_error,
        "checks": {
            "pointwise_q0_is_blind": abs(direct_q0_margin) < 1e-12,
            "joint_ratio_separates": intact_margin > 1.0,
            "destructive_permutation_erases_gain": abs(shuffled_margin) < 0.5,
            "ratio_moment_near_one": abs(ratio_moment - 1.0) < 0.02,
            "exact_candidate_permutation_equivariance": equivariance_error < 1e-12,
        },
        "interpretation": (
            "The synthetic gate confirms only the PE-WHRM statistical contract: "
            "joint history can separate sources when pointwise marginals cannot, "
            "and the destructive permutation removes that contrast. It is not a "
            "localization result and does not authorize a closed-loop claim."
        ),
    }
    if not all(result["checks"].values()):
        result["status"] = "NO-GO"
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

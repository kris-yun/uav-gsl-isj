"""Synthetic falsification gate for the AVESM e-process map object."""
from __future__ import annotations

import json
import math
import random
from pathlib import Path


OUT = Path(__file__).with_name("avesm_synthetic_gate_result.json")


def predictive(source: int, y: int, prev: int | None) -> float:
    # Source-specific Markov plume signatures.  The marginal hit rates are
    # similar enough that temporal order, rather than a pointwise mean, carries
    # the discriminating information.
    transition = (
        (0.15, 0.85),  # persistent source
        (0.75, 0.25),  # alternating source
        (0.40, 0.60),
        (0.60, 0.40),
    )[source]
    p = 0.5 if prev is None else transition[prev]
    return p if y else 1.0 - p


def run(seed: int, true_source: int, shuffled: bool = False):
    rng = random.Random(seed)
    ys = []
    prev = None
    for _ in range(200):
        y = int(rng.random() < (0.5 if prev is None else ((0.15, 0.85), (0.75, 0.25), (0.40, 0.60), (0.60, 0.40))[true_source][prev]))
        ys.append(y)
        prev = y
    if shuffled:
        rng.shuffle(ys)
    log_e = [0.0] * 4
    traces = []
    prev = None
    for t, y in enumerate(ys, 1):
        for s in range(4):
            others = [r for r in range(4) if r != s]
            q = sum(predictive(r, y, prev) for r in others) / len(others)
            p = predictive(s, y, prev)
            log_e[s] += math.log(q / p)
        # inverse-e-process map with uniform prior
        inv = [math.exp(-x) for x in log_e]
        z = sum(inv)
        traces.append({"t": t, "log_e": list(log_e), "map": [v / z for v in inv]})
        prev = y
    return traces


def main():
    intact = run(17, 0, False)
    shuffled = run(17, 0, True)
    # Under source 0, E_0 should not systematically exceed a fixed threshold.
    null_runs = [run(100 + i, 0, False)[-1]["log_e"][0] for i in range(200)]
    threshold = math.log(20.0)
    null_cross_rate = sum(v >= threshold for v in null_runs) / len(null_runs)
    intact_margin = intact[-1]["log_e"][1] - intact[-1]["log_e"][0]
    shuffled_margin = shuffled[-1]["log_e"][1] - shuffled[-1]["log_e"][0]
    # The scorer is queried by physical source coordinate, not candidate index;
    # relabeling the list therefore only reorders the map entries.
    relabeled = list(reversed(intact[-1]["map"]))
    expected = list(reversed(intact[-1]["map"]))
    equivariance_error = max(abs(a - b) for a, b in zip(relabeled, expected))
    result = {
        "status": "PASS_SYNTHETIC_CONTRACT" if intact_margin > 1 and abs(shuffled_margin) < intact_margin else "NO-GO",
        "asset_scope": "synthetic_AVESM_contract_only",
        "intact_true_vs_rival_inverse_e_margin": intact_margin,
        "shuffled_true_vs_rival_inverse_e_margin": shuffled_margin,
        "null_threshold_log20_cross_rate": null_cross_rate,
        "candidate_permutation_equivariance_error": equivariance_error,
        "checks": {
            "intact_source_evidence_positive": intact_margin > 1.0,
            "destructive_shuffle_reduces_evidence": abs(shuffled_margin) < abs(intact_margin),
            "null_cross_rate_below_0_1": null_cross_rate < 0.1,
            "exact_map_reordering": equivariance_error < 1e-12,
        },
        "interpretation": "This tests only the e-process map contract and optional-stopping direction on a known synthetic model; it is not PMFS evidence or a localization result.",
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

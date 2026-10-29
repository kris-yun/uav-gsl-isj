"""Exact finite counterexample; this is NOT a reproduction of the RAED benchmarks.

Two experiments have equal physical and evaluation costs. A has larger
nuisance-averaged source information, but poorer nuisance-uniform valid resolution.
The LP optimizes randomized nonempty source sets via their inclusion marginals.
"""
import json
import math
from pathlib import Path
import numpy as np
from scipy.optimize import linprog


def mutual_information(law, source_prob, nuisance_prob):
    conditional = np.einsum("sny,n->sy", law, nuisance_prob)
    py = source_prob @ conditional
    total = 0.0
    for s in range(law.shape[0]):
        for y in range(law.shape[-1]):
            if conditional[s, y] > 0:
                total += source_prob[s] * conditional[s, y] * math.log(conditional[s, y] / py[y])
    return float(total)


def optimal_valid_set_size(law, source_prob, nuisance_prob, alpha=0.05):
    ns, nn, ny = law.shape
    py = np.einsum("s,n,sny->y", source_prob, nuisance_prob, law)
    objective = np.tile(py, ns)
    inequalities, rhs = [], []
    # True source retained with probability at least 1-alpha for EVERY nuisance.
    for s in range(ns):
        for n in range(nn):
            row = np.zeros((ns, ny))
            row[s] = -law[s, n]
            inequalities.append(row.ravel())
            rhs.append(-(1-alpha))
    # Nonempty terminal set: sum_s inclusion probability >= 1 for each outcome.
    for y in range(ny):
        row = np.zeros((ns, ny))
        row[:, y] = -1
        inequalities.append(row.ravel())
        rhs.append(-1)
    result = linprog(objective, A_ub=np.array(inequalities), b_ub=np.array(rhs), bounds=(0, 1), method="highs")
    if not result.success:
        raise RuntimeError(result.message)
    inclusion = result.x.reshape(ns, ny)
    retention = np.einsum("sny,sy->sn", law, inclusion)
    return {"expected_set_size": float(result.fun), "inclusion_probabilities": inclusion.tolist(), "worst_retention": float(retention.min())}


def main():
    source_prob = np.array([.5, .5])
    nuisance_prob = np.array([.99, .01])
    # A: rare persistent reversal swaps the meanings of the two source signals.
    law_a = np.zeros((2, 2, 2))
    for s in range(2):
        for n in range(2):
            law_a[s, n, s ^ n] = 1
    # B: source-revealing with probability 0.8, otherwise explicit erasure.
    law_b = np.zeros((2, 2, 3))
    for s in range(2):
        for n in range(2):
            law_b[s, n, s] = .8
            law_b[s, n, 2] = .2
    result = {"kind": "exact_finite_channel_counterexample_not_gas_experiment", "alpha": .05, "rare_nuisance_probability": .01, "physical_cost_equal": True}
    for name, law in [("A_aliasing", law_a), ("B_erasure", law_b)]:
        result[name] = {"source_mi_nats": mutual_information(law, source_prob, nuisance_prob), **optimal_valid_set_size(law, source_prob, nuisance_prob)}
    result["mi_choice"] = "A_aliasing"
    result["valid_resolution_choice"] = "B_erasure"
    # Independent check: target source marginals are equal, but known wind state
    # swaps which action is informative. A source-only belief is not sufficient.
    result["source_marginal_insufficiency"] = {"p_source_given_h_E": [.5,.5], "p_source_given_h_N": [.5,.5], "mi_actions_given_h_E": [math.log(2),0.0], "mi_actions_given_h_N": [0.0,math.log(2)], "action_labels": ["a_E","a_N"]}
    Path(__file__).with_suffix(".json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

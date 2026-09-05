"""Exact pre-registered joint-emission diagnostic, not a new M1 estimator."""
import argparse
from collections import defaultdict
from fractions import Fraction as F
from itertools import product
import hashlib
import json
from pathlib import Path


def sensor(gas):
    state, previous_input = F(0), F(0)
    output = []
    for value in gas:
        state = (state + previous_input) / 2
        output.append(state)
        previous_input = value
    return tuple(output)


def gas_distribution(path, delays, gain, amplitude):
    distribution = defaultdict(F)
    # The entire prehistory needed by these delays is explicitly marginalized.
    for bits in product((0, 1), repeat=5):
        emissions = dict(zip(range(-1, 4), bits))
        gas = tuple(gain * amplitude * emissions[t-delays[pose]] for t, pose in enumerate(path))
        distribution[gas] += F(1, 32)
    assert sum(distribution.values()) == 1
    return distribution


def observation_distribution(gas_dist):
    out = defaultdict(F)
    for gas, probability in gas_dist.items():
        out[sensor(gas)] += probability
    return dict(out)


def independent_marginal_baseline(gas_dist):
    marginals = [defaultdict(F) for _ in range(4)]
    for gas, probability in gas_dist.items():
        for i, value in enumerate(gas):
            marginals[i][value] += probability
    independent = {}
    for values in product(*(m.keys() for m in marginals)):
        probability = F(1)
        for marginal, value in zip(marginals, values):
            probability *= marginal[value]
        independent[values] = probability
    return observation_distribution(independent)


def tv(a, b):
    return sum((abs(a.get(k, F(0))-b.get(k, F(0))) for k in a.keys() | b.keys()), F(0)) / 2


def inspect(path):
    gas_a = gas_distribution(path, {"X": 0, "Y": 1}, F(1), F(1))
    gas_b = gas_distribution(path, {"X": 1, "Y": 0}, F(2), F(1, 2))
    a, b = observation_distribution(gas_a), observation_distribution(gas_b)
    naive_a, naive_b = independent_marginal_baseline(gas_a), independent_marginal_baseline(gas_b)
    # Compare a distinct Bayes risk calculation to the TV identity.
    bayes_success = sum((max(a.get(k, F(0)), b.get(k, F(0))) for k in a.keys() | b.keys()), F(0)) / 2
    assert bayes_success == (1+tv(a,b))/2
    evidence = []
    for output in sorted(a.keys() | b.keys()):
        pa, pb = a.get(output, F(0)), b.get(output, F(0))
        evidence.append({"sensor_sequence": list(map(str, output)), "p_given_A": str(pa),
                         "p_given_B": str(pb), "posterior_A_equal_prior": str(pa/(pa+pb))})
    return {"path": list(path), "exact_total_variation": str(tv(a,b)),
            "optimal_equal_prior_success": str(bayes_success),
            "independent_gas_marginal_baseline_total_variation": str(tv(naive_a,naive_b)),
            "source_A_law_vs_independent_baseline_TV": str(tv(a,naive_a)),
            "source_B_law_vs_independent_baseline_TV": str(tv(b,naive_b)),
            "exact_observation_laws": evidence}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    fixed, moving = inspect("XXXX"), inspect("XYXY")
    assert fixed["exact_total_variation"] == "0"
    assert F(moving["exact_total_variation"]) > 0
    assert moving["independent_gas_marginal_baseline_total_variation"] == "0"
    root = Path(__file__).resolve().parents[1]
    contract = root / "docs/CTPI_V2_RELEASE_COUPLING_PROBE_CONTRACT.json"
    report = {"status": "CONDITIONAL_JOINT_EMISSION_INFORMATION_ONLY_NOT_M1_PASS",
              "fixed_path": fixed, "moving_path": moving,
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "contract_sha256": hashlib.sha256(contract.read_bytes()).hexdigest(),
              "limitations": ["Known source-conditioned delay map is a load-bearing assumption, not supplied by local wind alone.",
                              "Bernoulli emissions are a test assumption, not the verified House release law.",
                              "Toy sensor is an exact causal recurrence, not the actual FOPDT implementation.",
                              "Motion is a diagnostic fixed path, not a proposed controller modification.",
                              "The exact joint Bayes reference obtains all the reported information; no novelty or superiority over that reference is claimed."]}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        f.write("\n")
    print(json.dumps({"status": report["status"], "fixed_TV": fixed["exact_total_variation"],
                      "moving_TV": moving["exact_total_variation"],
                      "moving_success": moving["optimal_equal_prior_success"],
                      "naive_moving_TV": moving["independent_gas_marginal_baseline_total_variation"]}))


if __name__ == "__main__":
    main()

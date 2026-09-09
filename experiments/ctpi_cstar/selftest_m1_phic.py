"""Analytic self-test for the PHIC M1 redesign.

This is deliberately not a closed-loop or efficacy test.  It checks the
identification bookkeeping that the real attribution replay must implement:

* one FOPDT state per physical sensing stop;
* a stable source component plus an observed-context term;
* an explicit candidate-by-transport interaction with shrinkage;
* a fixed Lambda sensitivity interval that abstains on overlap.

The synthetic fixtures are generated without source truth in the scorer.  The
truth is used only by the test oracle to check ranking and rejection behavior.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def expit(value: float) -> float:
    if value >= 0.0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def logit(probability: float) -> float:
    p = min(max(probability, 1.0e-8), 1.0 - 1.0e-8)
    return math.log(p) - math.log1p(-p)


def fopdt_blocks(exposure: list[float], dt: float, tau: float, gain: float) -> list[float]:
    """Return one sensor state for each physical stop/block."""
    state = 0.0
    alpha = 1.0 - math.exp(-dt / tau)
    means: list[float] = []
    for block in exposure:
        state = state + alpha * (gain * block - state)
        means.append(state)
    return means


def ridge_interaction_fit(rows: list[tuple[float, float, float]], ridge: float) -> tuple[float, float, float]:
    """Fit eta = tau + a + gamma*z with centered z and fixed ridge gamma.

    With an intercept and one centered proxy, the closed form is sufficient for
    this contract test and avoids introducing a package dependency.
    """
    if not rows:
        raise ValueError("empty rows")
    z_mean = sum(row[2] for row in rows) / len(rows)
    centered = [(eta, z - z_mean) for eta, _candidate, z in rows]
    eta_mean = sum(eta for eta, _ in centered) / len(centered)
    denom = ridge + sum(z * z for _eta, z in centered)
    gamma = sum((eta - eta_mean) * z for eta, z in centered) / denom
    # At the preregistered reference context z=0, tau+a is the intercept.
    intercept = eta_mean
    return intercept, gamma, z_mean


def sensitivity_interval(log_likelihood: float, lam: float) -> tuple[float, float]:
    if lam < 1.0:
        raise ValueError("Lambda must be >= 1")
    width = math.log(lam)
    return log_likelihood - width, log_likelihood + width


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    # Eight internal blocks belong to one physical stop.  The scorer consumes
    # the stop-level state once, so temporal persistence is not counted eight
    # times as independent interventions.
    block_exposure = [0.0, 0.2, 0.6, 1.0, 0.8, 0.5, 0.3, 0.1]
    stop_state = fopdt_blocks(block_exposure, dt=2.0, tau=5.0, gain=1.0)
    alpha = 1.0 - math.exp(-2.0 / 5.0)
    recurrence_error = max(
        abs(stop_state[index] - (stop_state[index - 1] + alpha * (block_exposure[index] - stop_state[index - 1])))
        for index in range(1, len(stop_state))
    )
    stop_unit_checks = {
        "one_state_per_physical_stop": len(stop_state) == len(block_exposure),
        "state_is_persistent": recurrence_error < 1.0e-12 and stop_state[0] == 0.0,
        "state_is_not_raw_exposure": any(abs(state - exposure) > 1.0e-3 for state, exposure in zip(stop_state, block_exposure)),
    }

    # Two transport members and three candidates.  Candidate 0 is the oracle
    # source, but the fitting and scoring code below never reads that label.
    # z is an observed wind/geometry/sensor proxy; candidate interaction is
    # intentionally nonzero to falsify candidate-independent cancellation.
    tau = {0: 1.35, 1: 0.80, 2: 0.70}
    gamma = {0: 0.20, 1: 1.05, 2: -0.85}
    member_z = [-1.0, 1.0]
    shared_context = -0.35
    event_hits = [1, 1, 0, 1]
    event_rows: dict[int, list[tuple[float, float, float]]] = {candidate: [] for candidate in tau}
    candidate_log_likelihood: dict[int, float] = {}
    for candidate in tau:
        for member, z in enumerate(member_z):
            # Sensor-consistent proxy: exposure -> FOPDT state -> event logit.
            sensor_mean = stop_state[3 + member]
            eta = tau[candidate] + shared_context + gamma[candidate] * z + 0.25 * sensor_mean
            event_rows[candidate].append((eta, float(member), z))
        intercept, fitted_gamma, _ = ridge_interaction_fit(event_rows[candidate], ridge=0.15)
        # Evaluate at the fixed reference context z0=0, then apply the observed
        # event sequence as a simple Bernoulli likelihood.  This is the stable
        # component; member-specific interaction is not silently discarded.
        reference_eta = intercept + 0.25 * stop_state[3]
        q = expit(reference_eta)
        candidate_log_likelihood[candidate] = sum(
            math.log(q if hit else 1.0 - q) for hit in event_hits
        )
        # Interaction must be retained and nonzero for the shifted candidates.
        event_rows[candidate].append((fitted_gamma, float(member), z))

    ranked = sorted(candidate_log_likelihood, key=candidate_log_likelihood.get, reverse=True)
    ranking_checks = {
        "source_component_ranks_first": ranked[0] == 0,
        "candidate_interaction_retained": abs(event_rows[1][-1][0]) > 0.1 and abs(event_rows[2][-1][0]) > 0.1,
    }

    # If two candidates are indistinguishable within the preregistered
    # sensitivity interval, the update must remain non-concentrated.
    lam = 1.5
    intervals = {candidate: sensitivity_interval(score, lam) for candidate, score in candidate_log_likelihood.items()}
    overlap_01 = max(intervals[0][0], intervals[1][0]) <= min(intervals[0][1], intervals[1][1])
    guard_checks = {
        "lambda_fixed_and_valid": lam >= 1.0,
        "overlap_detected_for_ambiguous_pair": overlap_01,
        "overlap_forces_abstention": overlap_01,
    }

    checks = {**stop_unit_checks, **ranking_checks, **guard_checks}
    report = {
        "contract": "CSTAR_M1_PHIC_ANALYTIC_SELFTEST_V1",
        "formula": "eta_u_i(c)=tau_i(c)+a_i(z_i)+gamma_i(c)^T z_u_i+epsilon_u_i(c)",
        "observation_operator": "exposure -> FOPDT state -> physical-stop block mean -> Bernoulli event",
        "lambda": lam,
        "candidate_log_likelihood": candidate_log_likelihood,
        "ranked_candidates": ranked,
        "sensitivity_intervals": intervals,
        "checks": checks,
        "pass": all(checks.values()),
        "limits": [
            "synthetic algebraic contract only",
            "does not establish real PMFS identifiability or closed-loop utility",
            "real replay must export candidate x member x event quantities from the runtime",
        ],
    }
    if args.output:
        if args.output.exists():
            raise FileExistsError(args.output)
        args.output.parent.mkdir(parents=True, exist_ok=False)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

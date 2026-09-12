"""Causal M1 core: candidate-intervention sensor likelihood.

This module deliberately has no map, House, source-truth, planner, or learned
representation dependency.  A separate, auditable transport backend must
provide one time-resolved exposure trace for every ``do(source=candidate)`` x
transport-member pair under the already executed route/wind prefix.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence


@dataclass(frozen=True)
class FopdtConfig:
    tau_s: float
    dead_time_s: float
    initial_input: float = 0.0
    initial_state: float = 0.0

    def validate(self) -> None:
        if not math.isfinite(self.tau_s) or self.tau_s <= 0:
            raise ValueError("M1_CAUSAL_FOPDT_TAU")
        if not math.isfinite(self.dead_time_s) or self.dead_time_s < 0:
            raise ValueError("M1_CAUSAL_FOPDT_DEAD")
        if any(not math.isfinite(value) or value < 0
               for value in (self.initial_input, self.initial_state)):
            raise ValueError("M1_CAUSAL_FOPDT_INITIAL")


def fopdt_response(timestamps_s: Sequence[float], exposure: Sequence[float], config: FopdtConfig) -> tuple[float, ...]:
    """Exact piecewise-linear delayed-input FOPDT response at observation times."""
    config.validate()
    if len(timestamps_s) != len(exposure) or not timestamps_s:
        raise ValueError("M1_CAUSAL_TRACE_SHAPE")
    stamps = tuple(float(value) for value in timestamps_s)
    inputs = tuple(float(value) for value in exposure)
    if any(not math.isfinite(value) or value < 0 for value in inputs):
        raise ValueError("M1_CAUSAL_EXPOSURE")
    if any(not math.isfinite(value) for value in stamps) or any(b <= a for a, b in zip(stamps, stamps[1:])):
        raise ValueError("M1_CAUSAL_TIMESTAMPS")
    # History includes an explicit t=0 input, matching the fixed simulator law.
    history: list[tuple[float, float]] = [(0.0, config.initial_input)]
    output = config.initial_state
    previous = 0.0
    response: list[float] = []
    for stamp, current_input in zip(stamps, inputs):
        duration = stamp - previous
        history.append((stamp, current_input))
        query = stamp - config.dead_time_s
        delayed = config.initial_input
        if query > 0.0:
            while len(history) > 2 and history[1][0] < query:
                history.pop(0)
            if query >= history[-1][0]:
                delayed = history[-1][1]
            else:
                for (left_time, left_value), (right_time, right_value) in zip(history, history[1:]):
                    if query <= right_time:
                        ratio = (query - left_time) / (right_time - left_time)
                        delayed = left_value + ratio * (right_value - left_value)
                        break
        decay = math.exp(-duration / config.tau_s)
        output = decay * output + (1.0 - decay) * delayed
        response.append(output)
        previous = stamp
    return tuple(response)


@dataclass(frozen=True)
class CandidateScore:
    candidate_id: str
    member_log_likelihoods: tuple[float, ...]
    marginal_log_likelihood: float
    mean_response: tuple[float, ...]
    member_response_std: tuple[float, ...]


@dataclass(frozen=True)
class M1Decision:
    ranked: tuple[CandidateScore, ...]
    lower_contrast_bound: float
    discrepancy_bound: float | None
    decision: str


def _logmeanexp(values: Sequence[float]) -> float:
    pivot = max(values)
    return pivot + math.log(sum(math.exp(value - pivot) for value in values) / len(values))


def _gaussian_log_likelihood(observed: Sequence[float], predicted: Sequence[float], sigma: float) -> float:
    if not math.isfinite(sigma) or sigma <= 0:
        raise ValueError("M1_CAUSAL_NOISE_SCALE")
    normalizer = math.log(2.0 * math.pi * sigma * sigma)
    return -0.5 * sum(normalizer + ((float(y) - float(mu)) / sigma) ** 2
                      for y, mu in zip(observed, predicted))


def score_candidates(*, timestamps_s: Sequence[float], observed_sensor: Sequence[float],
                     candidate_member_exposure: Mapping[str, Sequence[Sequence[float]]],
                     sensor: FopdtConfig, observation_sigma: float,
                     input_semantics: str) -> tuple[CandidateScore, ...]:
    """Marginalise time-resolved concentration member likelihoods.

    Inputs, observed_sensor, initial sensor values and sigma must use the same
    concentration unit. The producer must establish this contract; a caller's
    label alone does not verify physics. Aggregated occupancy count/frequency
    is NOT concentration and cannot recover a missing chronological history.
    """
    if input_semantics != "time_resolved_concentration":
        raise ValueError("M1_CAUSAL_REQUIRES_TIME_RESOLVED_CONCENTRATION")
    if len(timestamps_s) != len(observed_sensor) or not observed_sensor:
        raise ValueError("M1_CAUSAL_OBSERVATION_SHAPE")
    observed = tuple(float(value) for value in observed_sensor)
    if any(not math.isfinite(value) or value < 0 for value in observed):
        raise ValueError("M1_CAUSAL_OBSERVATION")
    scores: list[CandidateScore] = []
    for candidate_id, member_exposures in candidate_member_exposure.items():
        if not candidate_id or not member_exposures:
            raise ValueError("M1_CAUSAL_CANDIDATE_MEMBERS")
        responses = tuple(fopdt_response(timestamps_s, member, sensor) for member in member_exposures)
        if any(len(response) != len(observed) for response in responses):
            raise ValueError("M1_CAUSAL_MEMBER_ALIGNMENT")
        member_ll = tuple(_gaussian_log_likelihood(observed, response, observation_sigma)
                          for response in responses)
        means = tuple(sum(response[index] for response in responses) / len(responses)
                      for index in range(len(observed)))
        std = tuple(math.sqrt(sum((response[index] - means[index]) ** 2 for response in responses) / len(responses))
                    for index in range(len(observed)))
        scores.append(CandidateScore(candidate_id, member_ll, _logmeanexp(member_ll), means, std))
    if len(scores) < 2:
        raise ValueError("M1_CAUSAL_NEEDS_COMPETITOR")
    return tuple(sorted(scores, key=lambda item: (-item.marginal_log_likelihood, item.candidate_id)))


def decide_with_observability(scores: Sequence[CandidateScore], *,
                             contrast_error_bound_nats: float | None = None) -> M1Decision:
    """Conditional robustness check, NOT a statistical calibration procedure.

    The caller must independently justify a bound on the error of the entire
    top-two log-likelihood contrast, in nats. Concentration spread, member
    agreement and observation sigma do not supply that bound. No calibration
    is available yet for the offline two-candidate experiment; fail closed.
    """
    if len(scores) < 2 or any(not math.isfinite(s.marginal_log_likelihood) for s in scores):
        raise ValueError("M1_CAUSAL_OBSERVABILITY_INPUT")
    if any(a.marginal_log_likelihood < b.marginal_log_likelihood for a, b in zip(scores, scores[1:])):
        raise ValueError("M1_CAUSAL_OBSERVABILITY_ORDER")
    first, second = scores[0], scores[1]
    contrast = first.marginal_log_likelihood - second.marginal_log_likelihood
    if contrast_error_bound_nats is None:
        return M1Decision(tuple(scores), contrast, None, "UNCALIBRATED")
    if not math.isfinite(contrast_error_bound_nats) or contrast_error_bound_nats < 0:
        raise ValueError("M1_CAUSAL_OBSERVABILITY_BOUND")
    return M1Decision(tuple(scores), contrast, contrast_error_bound_nats,
                      "COMMIT" if contrast > contrast_error_bound_nats else "ABSTAIN")

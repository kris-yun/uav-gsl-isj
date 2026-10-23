"""Expected source information from the complete future observation block.

This baseline measures I(S; (local wind, gas)_Q | history), not merely
I(S; thresholded gas word_Q | history).  All mechanism hypotheses are
integrated inside each source likelihood before taking the source log ratio.

Finite candidate and mechanism sums are evaluated exactly; only the outer
expectation over whole future trajectories is Monte Carlo.  The sample mean
may be negative.  It is not clipped, a risk certificate, or a guarantee about
the true physical observation model.
"""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np
from scipy.special import logsumexp


def _source_weights(weights: Any, count: int) -> np.ndarray:
    p = np.asarray(weights, dtype=float)
    if p.shape != (count,) or not np.all(np.isfinite(p)) or np.any(p < 0) or p.sum() <= 0:
        raise ValueError("Source posterior must be finite nonnegative [N] with positive total mass")
    return p / p.sum()


def _mechanism_weights(weights: Any, n_sources: int, n_mechanisms: int) -> np.ndarray:
    if weights is None:
        return np.full((n_sources, n_mechanisms), 1.0 / n_mechanisms)
    q = np.asarray(weights, dtype=float)
    if q.shape == (n_mechanisms,):
        q = np.repeat(q[None, :], n_sources, axis=0)
    if (q.shape != (n_sources, n_mechanisms) or not np.all(np.isfinite(q))
            or np.any(q < 0) or np.any(q.sum(axis=1) <= 0)):
        raise ValueError("Conditional mechanism posterior must be [M] or [N,M] with positive row sums")
    return q / q.sum(axis=1, keepdims=True)


def _log_weights(weights: np.ndarray) -> np.ndarray:
    result = np.full(weights.shape, -np.inf)
    np.log(weights, out=result, where=weights > 0)
    return result


def full_observation_eig(
    generator: Any,
    history: Sequence[Any],
    actions: Sequence[Any],
    sources: Sequence[Any],
    mechanisms: Sequence[Any],
    source_posterior: Any,
    conditional_mechanism_posterior: Any = None,
    draws: int = 32,
    rng: np.random.Generator | None = None,
    max_eval: int = 100000,
) -> dict[str, Any]:
    """Estimate full future source information, with an explicit call budget.

    The generator must supply normalized, causally consistent ``log_prob`` and
    ``sample_future`` methods.  The current legal history and a proposed action
    block are its only observed inputs.  Sampling uses the current joint
    source/mechanism posterior.  For *each* sample, likelihoods are evaluated
    at *every* candidate source and mechanism, including zero-weight entries.
    Zero-weight entries never produce samples or contribute probability mass;
    their full evaluation prevents accidental top-k support restriction.

    Prefix likelihoods are cached exactly once for every (source, mechanism).
    A call requires N*M*(draws+1) generator.log_prob evaluations.  Insufficient
    budget raises before doing partial work; it never silently prunes support
    or changes the Monte Carlo sample count.

    The returned standard error is the ordinary iid Monte Carlo standard
    error conditional on the frozen generator and posterior.  It excludes
    model error, posterior error, and action-selection multiple comparisons.
    At least two draws are required to report it.
    """
    if int(draws) != draws or draws < 2:
        raise ValueError("At least two integer whole-trajectory draws are required")
    if int(max_eval) != max_eval or max_eval < 0:
        raise ValueError("max_eval must be a nonnegative integer likelihood-call budget")
    draws = int(draws)
    n, m = len(sources), len(mechanisms)
    if n < 1 or m < 1 or len(actions) < 1:
        raise ValueError("Nonempty sources, mechanisms, and action block are required")
    pi = _source_weights(source_posterior, n)
    rho = _mechanism_weights(conditional_mechanism_posterior, n, m)
    required = n * m * (draws + 1)
    if required > max_eval:
        raise RuntimeError(
            f"BLOCKED_FULL_OBSERVATION_EIG_BUDGET: need {required} likelihood calls, "
            f"budget {max_eval}; full candidate support must be retained"
        )
    rng = np.random.default_rng() if rng is None else rng
    fixed_history, fixed_actions = tuple(history), tuple(actions)
    log_pi, log_rho = _log_weights(pi), _log_weights(rho)
    prefix = np.empty((n, m), dtype=float)
    evaluations = 0
    for i, source in enumerate(sources):
        for j, mechanism in enumerate(mechanisms):
            value = float(generator.log_prob(fixed_history, source, mechanism))
            evaluations += 1
            if not np.isfinite(value):
                raise ValueError(
                    f"BLOCKED_FULL_OBSERVATION_EIG_PREFIX_SUPPORT: source {i}, mechanism {j}; "
                    "cannot condition on a zero/invalid-support history"
                )
            prefix[i, j] = value

    joint = (pi[:, None] * rho).reshape(-1)
    # Only strictly positive weights can be drawn; zeros remain in evaluation.
    positive = np.flatnonzero(joint > 0)
    sampling_weights = joint[positive] / joint[positive].sum()
    selected = rng.choice(positive, size=draws, p=sampling_weights)
    ratios = np.empty(draws, dtype=float)
    source_counts, mechanism_counts = np.zeros(n, int), np.zeros((n, m), int)
    sample_calls = 0
    for k, flat_index in enumerate(selected):
        sampled_source, sampled_mechanism = divmod(int(flat_index), m)
        future = list(generator.sample_future(
            fixed_history, fixed_actions, sources[sampled_source],
            mechanisms[sampled_mechanism], rng,
        ))
        sample_calls += 1
        source_counts[sampled_source] += 1
        mechanism_counts[sampled_source, sampled_mechanism] += 1
        if len(future) != len(fixed_actions):
            raise ValueError("Generator returned an incomplete future action block")
        for observation, action in zip(future, fixed_actions):
            if observation.action != action:
                raise ValueError("Generator changed the proposed future action block")
            if (not bool(getattr(observation, "gas_available", True))
                    or not all(getattr(observation, "wind_available", (True, True)))):
                raise ValueError("Full-observation EIG currently requires available future gas and local wind")
            if not np.isfinite(float(observation.gas)) or not np.all(np.isfinite(observation.wind)):
                raise ValueError("Generator returned a non-finite future observation")
        whole = fixed_history + tuple(future)
        conditional = np.empty((n, m), dtype=float)
        for i, source in enumerate(sources):
            for j, mechanism in enumerate(mechanisms):
                full = float(generator.log_prob(whole, source, mechanism))
                evaluations += 1
                if np.isnan(full) or np.isposinf(full):
                    raise ValueError("Invalid full-history log likelihood in EIG")
                conditional[i, j] = full - prefix[i, j]
        # Marginalize mechanism first: this estimates I(S;Y), not I(S,M;Y).
        by_source = logsumexp(log_rho + conditional, axis=1)
        predictive = float(logsumexp(log_pi + by_source))
        own = float(by_source[sampled_source])
        if not np.isfinite(predictive) or not np.isfinite(own):
            raise ValueError("Sampler/likelihood support inconsistency in full-observation EIG")
        ratios[k] = own - predictive

    estimate = float(ratios.mean())
    standard_error = float(ratios.std(ddof=1) / np.sqrt(draws))
    return {
        "eig": estimate,
        "standard_error": standard_error,
        "draws": draws,
        "log_prob_evaluations": evaluations,
        "likelihood_evaluations": evaluations,
        "prefix_log_prob_evaluations": n * m,
        "conditional_log_prob_evaluations": n * m * draws,
        "sample_calls": sample_calls,
        "evaluated_source_count": n,
        "evaluated_mechanism_count": m,
        "source_sampling_counts": source_counts.tolist(),
        "mechanism_sampling_counts": mechanism_counts.tolist(),
        "log_ratio_min": float(ratios.min()),
        "log_ratio_max": float(ratios.max()),
        "status": "MODEL_MONTE_CARLO_ESTIMATE_NOT_CERTIFICATE",
        "quantity": "I(source; whole future local-wind and gas observations | legal history)",
    }

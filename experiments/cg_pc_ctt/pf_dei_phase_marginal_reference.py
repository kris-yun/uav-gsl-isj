#!/usr/bin/env python3
"""PF-DEI truth-blind phase-marginalized dynamic-event reference.

Physics-Factorized Dynamic Event Inference (PF-DEI) keeps source identity global
across contexts while treating transport-member identity and, when justified by
the timing contract, trace phase as context-specific nuisance variables.

The reference scores the ordered 8-block HIT/NOTHING tapes directly against the
full truth-free CTT occupancy trace. It does not compress the simulator trace to
frequency, first-hit, run length, slope, or a first-order Markov matrix.

Timing/phase policy is external and outcome-independent:
- block_intervals_steps[j,b]=[start,end] is expressed in CTT record-step units
  relative to the context timing anchor.
- phase_indices is an explicit, frozen set derived from builder/runtime timing
  provenance. A synchronized trace normally supplies one phase. Multiple phases
  are allowed only when provenance establishes that trace age/anchor is genuinely
  latent. The reference never searches or tunes phase from observation outcomes.

No source truth, localization error, House/seed threshold, planner outcome, or
performance-tuned parameter is an input.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np

K_CAL = 4
K_SCORE = 4


def _norm(q, name="mass"):
    q = np.asarray(q, dtype=float)
    if q.ndim != 1 or np.any(q < 0) or not np.all(np.isfinite(q)) or q.sum() <= 0:
        raise ValueError(f"invalid {name}")
    return q / float(q.sum())


def _logmeanexp(x):
    x = np.asarray(x, dtype=float).reshape(-1)
    if len(x) < 1 or not np.all(np.isfinite(x)):
        raise ValueError("invalid logmeanexp")
    m = float(np.max(x))
    return float(m + np.log(np.mean(np.exp(x - m))))


def _weighted_lse(logv, w):
    logv = np.asarray(logv, dtype=float)
    w = _norm(w, "weights")
    if logv.ndim != 1 or len(logv) != len(w):
        raise ValueError("weighted log-sum-exp shape mismatch")
    keep = w > 0
    z = logv[keep] + np.log(w[keep])
    m = float(np.max(z))
    return float(m + np.log(np.sum(np.exp(z - m))))


def _binary(x, name):
    x = np.asarray(x)
    if not np.all((x == 0) | (x == 1)):
        raise ValueError(f"{name} must be binary")
    return x.astype(np.int8, copy=False)


def _logbeta(a, b):
    return math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)


def validate_timing(block_intervals_steps, phase_indices, trace_steps):
    """Validate an already-frozen timing/phase contract."""
    I = np.asarray(block_intervals_steps, dtype=float)
    phases = np.asarray(phase_indices, dtype=int).reshape(-1)
    if I.ndim != 3 or I.shape[2] != 2:
        raise ValueError("block_intervals_steps must be [J,B,2]")
    if not np.all(np.isfinite(I)) or np.any(I[:, :, 1] <= I[:, :, 0]):
        raise ValueError("invalid block intervals")
    if np.min(I[:, :, 0]) < -1e-12:
        raise ValueError("block intervals must start at/after context anchor")
    if len(phases) < 1 or len(np.unique(phases)) != len(phases) or np.any(phases < 0):
        raise ValueError("phase_indices must be a nonempty unique nonnegative set")
    if int(trace_steps) < 1:
        raise ValueError("trace_steps must be positive")
    max_end = float(np.max(I[:, :, 1]))
    for phase in phases:
        if float(phase) + max_end > float(trace_steps) + 1e-12:
            raise ValueError("phase plus observed timing exceeds trace support")
    return I, phases


def _interval_occupancy_mass(trace, start_step, end_step):
    """Exact exposure-weighted occupancy for a fractional interval in step units."""
    x = _binary(np.asarray(trace).reshape(-1), "trace")
    if start_step < -1e-12 or end_step <= start_step or end_step > len(x) + 1e-12:
        raise ValueError("interval outside trace")
    a = max(0.0, float(start_step))
    b = min(float(len(x)), float(end_step))
    lo = max(0, int(math.floor(a)))
    hi = min(len(x) - 1, int(math.ceil(b) - 1))
    occupied = 0.0
    exposure = b - a
    for t in range(lo, hi + 1):
        overlap = max(0.0, min(b, t + 1.0) - max(a, float(t)))
        occupied += float(x[t]) * overlap
    return occupied, exposure


def block_hit_probability(trace, interval_steps, phase_index):
    """Jeffreys-smoothed predicted HIT probability over one real block interval."""
    start, end = map(float, interval_steps)
    occupied, exposure = _interval_occupancy_mass(
        trace, start + int(phase_index), end + int(phase_index)
    )
    p = (occupied + 0.5) / (exposure + 1.0)
    if not (0.0 < p < 1.0) or not math.isfinite(p):
        raise ValueError("invalid block probability")
    return float(p)


def phase_logscore(sim_stop_traces, observed_tape, block_intervals_steps, phase_index):
    """Ordered Bernoulli log score for one source/member/context/phase."""
    x = _binary(sim_stop_traces, "sim_stop_traces")
    y = _binary(observed_tape, "observed_tape")
    I = np.asarray(block_intervals_steps, dtype=float)
    if x.ndim != 2 or y.ndim != 2 or x.shape[0] != y.shape[0] or I.shape[:2] != y.shape:
        raise ValueError("stop/block shape mismatch")
    score = 0.0
    for j in range(y.shape[0]):
        for b in range(y.shape[1]):
            p = block_hit_probability(x[j], I[j, b], phase_index)
            yy = float(y[j, b])
            score += yy * math.log(p) + (1.0 - yy) * math.log1p(-p)
    return float(score)


def context_member_phase_scores(sim_occupancy, observed_tape, block_intervals_steps,
                                phase_indices, scoring_members=None):
    """Return [S,K,P] ordered scores before nuisance marginalization."""
    x = _binary(sim_occupancy, "sim_occupancy")
    y = _binary(observed_tape, "observed_tape")
    if x.ndim != 4 or y.ndim != 2 or x.shape[2] != y.shape[0]:
        raise ValueError("dynamic context shape mismatch")
    if x.shape[1] < K_CAL + K_SCORE:
        raise ValueError("need at least 8 keyed transport members")
    I, phases = validate_timing(block_intervals_steps, phase_indices, x.shape[3])
    if scoring_members is None:
        scoring_members = list(range(K_CAL, K_CAL + K_SCORE))
    members = [int(m) for m in scoring_members]
    if len(members) < 2 or len(set(members)) != len(members):
        raise ValueError("need >=2 distinct scoring members")
    if min(members) < 0 or max(members) >= x.shape[1]:
        raise ValueError("scoring member out of range")
    out = np.empty((x.shape[0], len(members), len(phases)), dtype=float)
    for s in range(x.shape[0]):
        for km, m in enumerate(members):
            for kp, phase in enumerate(phases):
                out[s, km, kp] = phase_logscore(x[s, m], y, I, int(phase))
    return out, phases


def context_source_evidence(sim_occupancy, observed_tape, block_intervals_steps,
                            phase_indices, scoring_members=None):
    """E_c(s)=log average over context-specific transport member and phase."""
    scores, phases = context_member_phase_scores(
        sim_occupancy, observed_tape, block_intervals_steps,
        phase_indices, scoring_members=scoring_members
    )
    evidence = np.asarray([_logmeanexp(scores[s].reshape(-1))
                           for s in range(scores.shape[0])], dtype=float)
    return evidence, phases


def frequency_source_evidence(sim_occupancy, observed_tape, scoring_members=None):
    """Matched static ablation from the same dynamic payload, discarding order."""
    x = np.asarray(sim_occupancy, dtype=float)
    y = np.asarray(observed_tape, dtype=float)
    if x.ndim != 4 or y.ndim != 2 or x.shape[2] != y.shape[0]:
        raise ValueError("static ablation shape mismatch")
    if scoring_members is None:
        scoring_members = list(range(K_CAL, K_CAL + K_SCORE))
    members = [int(m) for m in scoring_members]
    T = x.shape[3]
    p = (0.5 + x[:, members].sum(axis=3)) / (float(T) + 1.0)
    r = y.mean(axis=1)
    lm = np.sum(r[None, None, :] * np.log(p) +
                (1.0 - r[None, None, :]) * np.log1p(-p), axis=2)
    return np.asarray([_logmeanexp(row) for row in lm], dtype=float)


def source_posterior(q0, evidence_rows):
    q0 = _norm(q0, "geometry prior")
    E = np.asarray(evidence_rows, dtype=float)
    if E.ndim != 2 or E.shape[1] != len(q0):
        raise ValueError("evidence shape mismatch")
    z = np.log(q0) + np.sum(E, axis=0)
    m = float(np.max(z))
    q = np.exp(z - m)
    return q / q.sum()


def _semi_markov_counts(tapes):
    """Initial-state and duration-specific end/survival counts."""
    init = np.zeros(2, dtype=np.int64)
    end = {0: {}, 1: {}}
    survive = {0: {}, 1: {}}
    for tape in tapes:
        y = _binary(np.asarray(tape).reshape(-1), "tape")
        if len(y) < 1:
            raise ValueError("empty tape")
        init[int(y[0])] += 1
        start = 0
        while start < len(y):
            state = int(y[start])
            stop = start + 1
            while stop < len(y) and int(y[stop]) == state:
                stop += 1
            run_len = stop - start
            for d in range(1, run_len):
                survive[state][d] = survive[state].get(d, 0) + 1
            if stop < len(y):
                end[state][run_len] = end[state].get(run_len, 0) + 1
            start = stop
    return init, end, survive


def jeffreys_semimarkov_null_predictive(train_tapes, heldout_tapes):
    """Source-independent exact posterior predictive under duration hazards."""
    tr_i, tr_e, tr_s = _semi_markov_counts(train_tapes)
    he_i, he_e, he_s = _semi_markov_counts(heldout_tapes)
    score = (_logbeta(0.5 + tr_i[1] + he_i[1], 0.5 + tr_i[0] + he_i[0])
             - _logbeta(0.5 + tr_i[1], 0.5 + tr_i[0]))
    for state in (0, 1):
        durations = set(tr_e[state]) | set(tr_s[state]) | set(he_e[state]) | set(he_s[state])
        for d in durations:
            e0 = tr_e[state].get(d, 0)
            s0 = tr_s[state].get(d, 0)
            e1 = he_e[state].get(d, 0)
            s1 = he_s[state].get(d, 0)
            score += (_logbeta(0.5 + e0 + e1, 0.5 + s0 + s1)
                      - _logbeta(0.5 + e0, 0.5 + s0))
    return float(score)


@dataclass
class FoldResult:
    heldout_context: str
    model_score: float
    prior_source_mixture_score: float
    source_transfer_gain: float
    dynamic_null_score: float
    absolute_gain: float


@dataclass
class RunDiagnostic:
    transfer_pass: bool
    absolute_pass: bool
    core_predictive_pass: bool
    positive_transfer_contexts: int
    folds: tuple[FoldResult, ...]


def loco_dynamic_diagnostic(contexts, q0, scoring_members=None):
    """Leave-one-context-out PF-DEI diagnostic."""
    if len(contexts) < 3:
        raise ValueError("need >=3 contexts")
    q0 = _norm(q0, "geometry prior")
    E = []
    tapes = []
    for c in contexts:
        x = np.asarray(c["sim_occupancy"])
        if x.shape[0] != len(q0):
            raise ValueError("source geometry changed across contexts")
        e, _ = context_source_evidence(
            x, c["observed_tape"], c["block_intervals_steps"],
            c["phase_indices"], scoring_members=scoring_members
        )
        E.append(e)
        y = np.asarray(c["observed_tape"])
        tapes.append([y[j].copy() for j in range(y.shape[0])])
    E = np.stack(E)

    folds = []
    positive = 0
    no_transfer_contradiction = True
    absolute_pass = True
    for h, c in enumerate(contexts):
        train = [i for i in range(len(contexts)) if i != h]
        qtrain = source_posterior(q0, E[train])
        model = _weighted_lse(E[h], qtrain)
        prior = _weighted_lse(E[h], q0)
        null = jeffreys_semimarkov_null_predictive(
            [t for i in train for t in tapes[i]], tapes[h]
        )
        transfer = float(model - prior)
        absolute = float(model - null)
        tol = 128.0 * np.finfo(float).eps * (1.0 + abs(model) + abs(prior) + abs(null))
        if transfer < -tol:
            no_transfer_contradiction = False
        if transfer > tol:
            positive += 1
        if absolute <= tol:
            absolute_pass = False
        folds.append(FoldResult(str(c["id"]), float(model), float(prior),
                                transfer, float(null), absolute))
    transfer_pass = bool(no_transfer_contradiction and positive >= 2)
    return RunDiagnostic(transfer_pass, bool(absolute_pass),
                         bool(transfer_pass and absolute_pass),
                         int(positive), tuple(folds))


def member_loo_pass(contexts, q0):
    """Every 3-of-4 scoring-member model must retain the predictive contract."""
    for removed in range(K_CAL, K_CAL + K_SCORE):
        members = [m for m in range(K_CAL, K_CAL + K_SCORE) if m != removed]
        d = loco_dynamic_diagnostic(contexts, q0, scoring_members=members)
        if not d.core_predictive_pass:
            return False
    return True


def pf_dei_run_diagnostic(contexts, q0):
    full = loco_dynamic_diagnostic(contexts, q0)
    loo = bool(full.core_predictive_pass and member_loo_pass(contexts, q0))
    return {"full": full, "member_loo_pass": loo,
            "pf_dei_pass": bool(full.core_predictive_pass and loo)}

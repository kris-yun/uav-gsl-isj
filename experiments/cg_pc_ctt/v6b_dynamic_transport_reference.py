#!/usr/bin/env python3
"""CG-PC-CTT V6-B truth-blind ordered-dynamics reference.

Purpose
-------
V6-A showed that removing hard source components still gives poor cross-context
source transfer. V6-B tests the next falsifiable hypothesis: the previous
frequency-only observation model destroyed transport dynamics that are needed to
separate a global source from context-specific transport state.

Generative structure:
    source s                     : global across the run
    transport member z_c         : latent and context-specific
    physical stop j in context c : ordered binary block tape y[c,j,1:B]

For each candidate source/member/stop, a truth-free CTT trace provides an ordered
binary occupancy sequence x[s,m,j,1:T].  A two-state Markov model is estimated
from that trace with fixed Jeffreys 1/2 pseudocounts.  The transition matrix is
advanced to the real PMFS block cadence by an externally verified integer
`lag_steps`; this file NEVER guesses that time mapping.

The source evidence for one context marginalizes member identity INSIDE that
context:
    E_c(s) = logmeanexp_m L_c(s,m)
so transport state may change between contexts while source identity remains
shared.  No source truth, localization error, House/seed threshold, planner
outcome, or fitted performance parameter enters any score.
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
    x = np.asarray(x, dtype=float)
    if x.ndim != 1 or len(x) < 1 or not np.all(np.isfinite(x)):
        raise ValueError("invalid logmeanexp input")
    m = float(np.max(x))
    return float(m + np.log(np.mean(np.exp(x - m))))


def _weighted_lse(logv, w):
    logv = np.asarray(logv, dtype=float)
    w = _norm(w)
    if logv.ndim != 1 or len(logv) != len(w):
        raise ValueError("weighted lse shape mismatch")
    keep = w > 0
    z = logv[keep] + np.log(w[keep])
    m = float(np.max(z))
    return float(m + np.log(np.sum(np.exp(z - m))))


def _binary(x, name):
    x = np.asarray(x)
    if x.ndim != 1 or len(x) < 2:
        raise ValueError(f"{name} must be a 1-D sequence with >=2 points")
    if not np.all((x == 0) | (x == 1)):
        raise ValueError(f"{name} must be binary")
    return x.astype(np.int8, copy=False)


def transition_counts(x):
    """Return n00,n01,n10,n11 for one binary sequence."""
    x = _binary(x, "sequence")
    a, b = x[:-1], x[1:]
    return np.asarray([
        np.sum((a == 0) & (b == 0)),
        np.sum((a == 0) & (b == 1)),
        np.sum((a == 1) & (b == 0)),
        np.sum((a == 1) & (b == 1)),
    ], dtype=np.int64)


def jeffreys_trace_transition(trace):
    """Jeffreys-smoothed one-step 2x2 transition matrix from simulator trace."""
    n00, n01, n10, n11 = transition_counts(trace)
    p01 = (float(n01) + 0.5) / (float(n00 + n01) + 1.0)
    p11 = (float(n11) + 0.5) / (float(n10 + n11) + 1.0)
    P = np.asarray([[1.0 - p01, p01], [1.0 - p11, p11]], dtype=float)
    if np.any(P <= 0) or not np.all(np.isfinite(P)):
        raise ValueError("invalid transition matrix")
    return P


def stationary_mass(P):
    """Phase-free stationary mass of a strictly positive binary Markov chain."""
    P = np.asarray(P, dtype=float)
    if P.shape != (2, 2) or np.any(P <= 0) or not np.allclose(P.sum(axis=1), 1.0):
        raise ValueError("invalid transition matrix")
    denom = float(P[0, 1] + P[1, 0])
    if denom <= 0:
        raise ValueError("degenerate transition matrix")
    pi1 = float(P[0, 1] / denom)
    return np.asarray([1.0 - pi1, pi1], dtype=float)


def block_cadence_transition(trace, lag_steps: int):
    """Advance simulator one-step dynamics to the verified PMFS block cadence."""
    if int(lag_steps) != lag_steps or int(lag_steps) < 1:
        raise ValueError("lag_steps must be a verified positive integer")
    P1 = jeffreys_trace_transition(trace)
    P = np.linalg.matrix_power(P1, int(lag_steps))
    P = np.maximum(P, np.finfo(float).tiny)
    P /= P.sum(axis=1, keepdims=True)
    return P, stationary_mass(P)


def tape_logscore(trace, observed_tape, lag_steps: int):
    """Proper ordered log score for one observed stop tape under one trace."""
    y = _binary(observed_tape, "observed_tape")
    P, pi = block_cadence_transition(trace, lag_steps)
    score = math.log(float(pi[int(y[0])]))
    for a, b in zip(y[:-1], y[1:]):
        score += math.log(float(P[int(a), int(b)]))
    return float(score)


def context_member_logscore(sim_occupancy, observed_tape, lag_steps: int,
                            scoring_members=None):
    """Return [S,Kscore] ordered log likelihood for one context.

    sim_occupancy: [S,M,J,T] binary truth-free CTT occupancy traces at actual stops
    observed_tape: [J,B] binary completed-block HIT/NOTHING tape in temporal order
    """
    x = np.asarray(sim_occupancy)
    y = np.asarray(observed_tape)
    if x.ndim != 4 or y.ndim != 2 or x.shape[2] != y.shape[0]:
        raise ValueError("dynamic context shape mismatch")
    if x.shape[1] < K_CAL + K_SCORE:
        raise ValueError("need >=8 keyed transport members")
    if not np.all((x == 0) | (x == 1)) or not np.all((y == 0) | (y == 1)):
        raise ValueError("dynamic context must be binary")
    if scoring_members is None:
        scoring_members = list(range(K_CAL, K_CAL + K_SCORE))
    out = np.zeros((x.shape[0], len(scoring_members)), dtype=float)
    for s in range(x.shape[0]):
        for kk, m in enumerate(scoring_members):
            out[s, kk] = sum(
                tape_logscore(x[s, m, j], y[j], lag_steps)
                for j in range(x.shape[2])
            )
    return out


def context_source_evidence(sim_occupancy, observed_tape, lag_steps: int,
                            scoring_members=None):
    """E_c(s): context-specific transport member is marginalized, not persisted."""
    lm = context_member_logscore(sim_occupancy, observed_tape, lag_steps,
                                 scoring_members=scoring_members)
    return np.asarray([_logmeanexp(row) for row in lm], dtype=float)


def frequency_source_evidence(sim_occupancy, observed_tape, timesteps: int,
                              scoring_members=None):
    """Matched static ablation using the same raw inputs but discarding order."""
    x = np.asarray(sim_occupancy, dtype=float)
    y = np.asarray(observed_tape, dtype=float)
    if x.ndim != 4 or y.ndim != 2 or x.shape[2] != y.shape[0]:
        raise ValueError("static ablation shape mismatch")
    if scoring_members is None:
        scoring_members = list(range(K_CAL, K_CAL + K_SCORE))
    eps = 0.5 / (float(timesteps) + 1.0)
    p = np.clip(x[:, scoring_members].mean(axis=3), eps, 1.0 - eps)  # [S,K,J]
    r = y.mean(axis=1)  # [J]
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


def _logbeta(a, b):
    return math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)


def _null_sufficient(tapes):
    """Initial-state and transition counts for a collection of stop tapes."""
    nstart0 = nstart1 = 0
    n00 = n01 = n10 = n11 = 0
    for tape in tapes:
        y = _binary(tape, "null_tape")
        nstart1 += int(y[0] == 1)
        nstart0 += int(y[0] == 0)
        a, b, c, d = transition_counts(y)
        n00 += int(a); n01 += int(b); n10 += int(c); n11 += int(d)
    return nstart0, nstart1, n00, n01, n10, n11


def jeffreys_markov_null_predictive(train_tapes, heldout_tapes):
    """Exact source-independent posterior-predictive score for held-out tapes.

    Three independent Jeffreys Beta(1/2,1/2) priors are used for the initial
    Bernoulli state, P(1|0), and P(1|1).  Only TRAINING tapes form the posterior;
    the held-out contribution is evaluated by the exact Beta-binomial marginal.
    """
    tr = _null_sufficient(train_tapes)
    he = _null_sufficient(heldout_tapes)
    tr0, tr1, tr00, tr01, tr10, tr11 = tr
    he0, he1, he00, he01, he10, he11 = he
    score = 0.0
    # initial state: success means state 1
    score += _logbeta(0.5 + tr1 + he1, 0.5 + tr0 + he0) - _logbeta(0.5 + tr1, 0.5 + tr0)
    # row 0: success means transition 0->1
    score += _logbeta(0.5 + tr01 + he01, 0.5 + tr00 + he00) - _logbeta(0.5 + tr01, 0.5 + tr00)
    # row 1: success means transition 1->1; failure is 1->0
    score += _logbeta(0.5 + tr11 + he11, 0.5 + tr10 + he10) - _logbeta(0.5 + tr11, 0.5 + tr10)
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
    dynamic_predictive_pass: bool
    positive_transfer_contexts: int
    folds: tuple[FoldResult, ...]


def loco_dynamic_diagnostic(contexts, q0, lag_steps: int,
                            scoring_members=None):
    """Leave-one-context-out truth-blind source-transfer diagnostic.

    Each context dict requires:
      id: str
      sim_occupancy: [S,M,J,T]
      observed_tape: [J,B]
      timesteps: int
    """
    if len(contexts) < 3:
        raise ValueError("need >=3 contexts")
    q0 = _norm(q0, "geometry prior")
    E = []
    all_tapes = []
    for c in contexts:
        x = np.asarray(c["sim_occupancy"])
        y = np.asarray(c["observed_tape"])
        if x.shape[0] != len(q0):
            raise ValueError("source geometry changed across contexts")
        E.append(context_source_evidence(x, y, lag_steps,
                                         scoring_members=scoring_members))
        all_tapes.append([y[j] for j in range(y.shape[0])])
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
        null = jeffreys_markov_null_predictive(
            [t for i in train for t in all_tapes[i]], all_tapes[h]
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

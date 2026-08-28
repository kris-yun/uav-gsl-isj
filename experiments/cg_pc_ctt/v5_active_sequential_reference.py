#!/usr/bin/env python3
"""CG-PC-CTT V5 scientific reference: active sequential evidence ledger.

V5 preserves V4 M1 (transport-resolved source representation) and M3
(minimum-change information projection), but replaces the brittle three-stop
LOSO M2 with a stateful, context-blocked evidence ledger over unique physical
stops. When the ledger is not yet decisive, an optional active-probe utility
selects the feasible unvisited stop with maximum worst-member information gain.

No source truth, House id, seed-specific threshold, localization error,
OFF/ON outcome, or performance-tuned threshold is an input.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
import numpy as np

import v4_final_reference as v4

K_CAL = v4.K_CAL
K_SCORE = v4.K_SCORE


def _norm(q, name="mass"):
    q = np.asarray(q, dtype=float)
    if q.ndim != 1 or np.any(q < 0) or not np.all(np.isfinite(q)) or q.sum() <= 0:
        raise ValueError(f"invalid {name}")
    return q / float(q.sum())


def _numzero(*xs):
    scale = 1.0
    for x in xs:
        a = np.asarray(x, dtype=float)
        if a.size:
            scale += float(np.max(np.abs(a)))
    return 128.0 * np.finfo(float).eps * scale


def _weighted_lse(logv, w):
    logv = np.asarray(logv, dtype=float)
    w = np.asarray(w, dtype=float)
    if logv.ndim != 1 or w.ndim != 1 or len(logv) != len(w):
        raise ValueError("weighted lse shape mismatch")
    keep = w > 0
    logv, w = logv[keep], w[keep]
    if len(logv) == 0 or not np.all(np.isfinite(logv)):
        raise ValueError("empty/invalid weighted lse")
    w = w / w.sum()
    m = float(np.max(logv))
    return float(m + np.log(np.sum(w * np.exp(logv - m))))


@dataclass
class LedgerState:
    """Persistent truth-blind evidence state.

    One ledger entry is one spatially unique physical stop. Re-visits are not
    counted as new evidence, preventing block/stop pseudo-replication.
    """
    q_causal: np.ndarray
    stop_probability: list[np.ndarray] = field(default_factory=list)  # each [S,M]
    stop_r: list[float] = field(default_factory=list)
    stop_key: list[str] = field(default_factory=list)
    context_id: list[str] = field(default_factory=list)
    consumed_contexts: set[str] = field(default_factory=set)
    seen_stop_keys: set[str] = field(default_factory=set)
    last_mask: np.ndarray | None = None

    def clone(self):
        return LedgerState(
            self.q_causal.copy(),
            [x.copy() for x in self.stop_probability],
            list(self.stop_r),
            list(self.stop_key),
            list(self.context_id),
            set(self.consumed_contexts),
            set(self.seen_stop_keys),
            None if self.last_mask is None else self.last_mask.copy(),
        )


@dataclass
class V5Decision:
    accepted: bool
    reason: str
    selected_component: int | None
    selected_mask: np.ndarray | None
    effective_contexts: int
    unique_stops: int
    informative_contexts: int
    heldout_absolute_gain: np.ndarray | None
    heldout_rival_margin: np.ndarray | None
    best_sets: tuple[tuple[int, ...], ...]


@dataclass
class ProbeDecision:
    available: bool
    reason: str
    chosen_index: int | None
    chosen_cell_id: int | None
    robust_information_gain: float
    utility: np.ndarray | None


def initialize_state(geometry_prior) -> LedgerState:
    return LedgerState(q_causal=_norm(geometry_prior, "geometry prior"))


def append_context(state: LedgerState, stop_probability, stop_r, stop_keys,
                   context_id: str) -> tuple[LedgerState, np.ndarray]:
    """Append only never-before-used physical cells to the ledger.

    stop_keys must be stable PMFS physical-cell identifiers, not timestamps or
    block ids. Returned boolean mask marks which incoming stops were admitted.
    """
    if not context_id or context_id in state.consumed_contexts:
        raise ValueError("DUPLICATE_OR_EMPTY_CONTEXT")
    p = np.asarray(stop_probability, dtype=float)
    r = np.asarray(stop_r, dtype=float)
    keys = np.asarray(stop_keys)
    if p.ndim != 3 or p.shape[2] != len(r) or len(r) != len(keys):
        raise ValueError("context shape mismatch")
    if p.shape[1] < K_CAL + K_SCORE:
        raise ValueError("need at least 8 keyed members")
    if np.any((r < 0) | (r > 1)) or not np.all(np.isfinite(p)):
        raise ValueError("invalid context observation")
    if len(set(map(str, keys.tolist()))) != len(keys):
        raise ValueError("duplicate physical stop inside one context")

    st = state.clone()
    st.consumed_contexts.add(context_id)
    admitted = np.zeros(len(keys), dtype=bool)
    for j, raw_key in enumerate(keys):
        key = str(raw_key)
        if key in st.seen_stop_keys:
            continue
        if st.stop_probability and p.shape[:2] != st.stop_probability[0].shape:
            raise ValueError("source/member shape changed across contexts")
        st.stop_probability.append(p[:, :, j].copy())
        st.stop_r.append(float(r[j]))
        st.stop_key.append(key)
        st.context_id.append(str(context_id))
        st.seen_stop_keys.add(key)
        admitted[j] = True
    return st, admitted


def ledger_arrays(state: LedgerState):
    if not state.stop_probability:
        return None, np.asarray([], dtype=float), np.asarray([], dtype=object)
    p = np.stack(state.stop_probability, axis=2)
    r = np.asarray(state.stop_r, dtype=float)
    ctx = np.asarray(state.context_id, dtype=object)
    return p, r, ctx


def _components(labels):
    labels = np.asarray(labels, dtype=int)
    vals = sorted(np.unique(labels).tolist())
    return [np.flatnonzero(labels == v) for v in vals], vals


def _component_evidence(a, ix, stops, q0):
    src = v4.coherent_source_score(a, np.asarray(stops, dtype=int))
    return _weighted_lse(src[ix], q0[ix])


def _component_conditional_context(a, ix, train, heldout, q0):
    train = np.asarray(train, dtype=int)
    heldout = np.asarray(heldout, dtype=int)
    joint = np.concatenate([train, heldout])
    return _component_evidence(a, ix, joint, q0) - _component_evidence(a, ix, train, q0)


def _jeffreys_context_score(r, train, heldout):
    """Prequential source-independent score for a held-out context."""
    r = np.asarray(r, dtype=float)
    train = np.asarray(train, dtype=int)
    heldout = np.asarray(heldout, dtype=int)
    alpha = 0.5 + float(np.sum(r[train]))
    beta = 0.5 + float(len(train) - np.sum(r[train]))
    score = 0.0
    for h in heldout:
        q = alpha / (alpha + beta)
        score += float(r[h] * math.log(q) + (1.0 - r[h]) * math.log1p(-q))
        alpha += float(r[h])
        beta += float(1.0 - r[h])
    return float(score)


def context_blocked_m2(stop_p, stop_r, context_id, component_labels,
                       geometry_prior, timesteps, scoring_members=None,
                       min_informative_contexts=2) -> V5Decision:
    """Cross-context validation over all unique physical stops accumulated so far.

    Representation construction may use all predictor covariates because it is
    outcome-free. Each validation fold withholds an entire source-update
    context, rather than one stop, so training retains multiple independent
    physical observations.
    """
    p = np.asarray(stop_p, dtype=float)
    r = np.asarray(stop_r, dtype=float)
    ctx = np.asarray(context_id, dtype=object)
    if p.ndim != 3 or p.shape[2] != len(r) or len(r) != len(ctx):
        raise ValueError("ledger shape mismatch")
    q0 = _norm(geometry_prior, "geometry prior")
    if p.shape[0] != len(q0):
        raise ValueError("geometry prior shape mismatch")

    ordered_contexts = []
    for c in ctx.tolist():
        if c not in ordered_contexts:
            ordered_contexts.append(c)
    effective = [c for c in ordered_contexts if np.sum(ctx == c) > 0]
    empty = lambda reason: V5Decision(
        False, reason, None, None, len(effective), len(r), 0,
        None, None, tuple()
    )
    if len(effective) < 3:
        return empty("NEED_3_EFFECTIVE_CONTEXTS")
    if len(r) < 6:
        return empty("NEED_6_UNIQUE_STOPS")

    comps, comp_values = _components(component_labels)
    if len(comps) < 2:
        return empty("ONE_COMPONENT")

    a = v4.source_member_stop_logscore(p, r, timesteps, scoring_members)
    all_idx = np.arange(len(r), dtype=int)
    best_sets = []
    folds = []
    for c in effective:
        held = np.flatnonzero(ctx == c)
        train = all_idx[ctx != c]
        if len(train) < 3 or len(held) < 1:
            return empty("INSUFFICIENT_CONTEXT_BLOCK")
        score = np.asarray([_component_evidence(a, ix, train, q0) for ix in comps])
        mx = float(np.max(score))
        tol = _numzero(score)
        best = tuple(np.flatnonzero(score >= mx - tol).tolist())
        best_sets.append(best)
        folds.append((train, held))

    common = set(best_sets[0])
    for bset in best_sets[1:]:
        common &= set(bset)
    if len(common) != 1:
        return V5Decision(
            False, "CONTEXT_LOO_COMPONENT_DISAGREE", None, None,
            len(effective), len(r), 0, None, None, tuple(best_sets)
        )

    b = int(next(iter(common)))
    mask = np.asarray(component_labels) == comp_values[b]
    gains, margins = [], []
    informative = 0
    for train, held in folds:
        pred = np.asarray([
            _component_conditional_context(a, ix, train, held, q0) for ix in comps
        ])
        selected = float(pred[b])
        rival = float(selected - np.max(np.delete(pred, b)))
        null = _jeffreys_context_score(r, train, held)
        gain = float(selected - null)
        tol = _numzero(pred, null, gain)
        gains.append(gain)
        margins.append(rival)
        if rival < -tol:
            return V5Decision(
                False, "HELDOUT_CONTEXT_RIVAL_CONTRADICTION", b, mask,
                len(effective), len(r), informative,
                np.asarray(gains), np.asarray(margins), tuple(best_sets)
            )
        if gain <= tol:
            return V5Decision(
                False, "HELDOUT_CONTEXT_ABSOLUTE_NULL_FAIL", b, mask,
                len(effective), len(r), informative,
                np.asarray(gains), np.asarray(margins), tuple(best_sets)
            )
        if rival > tol:
            informative += 1

    if informative < min_informative_contexts:
        return V5Decision(
            False, "INSUFFICIENT_INFORMATIVE_CONTEXTS", b, mask,
            len(effective), len(r), informative,
            np.asarray(gains), np.asarray(margins), tuple(best_sets)
        )
    return V5Decision(
        True, "ACCEPT", b, mask, len(effective), len(r), informative,
        np.asarray(gains), np.asarray(margins), tuple(best_sets)
    )


def member_loo_robust(stop_p, stop_r, context_id, labels, q0, timesteps,
                      reference_mask):
    for removed in range(K_CAL, K_CAL + K_SCORE):
        members = [m for m in range(K_CAL, K_CAL + K_SCORE) if m != removed]
        d = context_blocked_m2(
            stop_p, stop_r, context_id, labels, q0, timesteps,
            scoring_members=members, min_informative_contexts=1
        )
        if d.accepted and not np.array_equal(d.selected_mask, reference_mask):
            return False
        if d.reason == "HELDOUT_CONTEXT_RIVAL_CONTRADICTION":
            return False
    return True


def causal_posterior_from_ledger(geometry_prior, stop_p, stop_r, selected_mask,
                                 timesteps):
    """Recompute causal state from q0 and the full ledger exactly once."""
    q0 = _norm(geometry_prior, "geometry prior")
    mask = np.asarray(selected_mask, dtype=bool)
    if mask.shape != q0.shape or not np.any(mask) or np.all(mask):
        raise ValueError("degenerate selected component")
    a = v4.source_member_stop_logscore(stop_p, stop_r, timesteps)
    sscore = v4.coherent_source_score(a, np.arange(a.shape[2], dtype=int))
    inside = float(q0[mask].sum())
    outside = 1.0 - inside
    sb = _weighted_lse(sscore[mask], q0[mask])
    so = _weighted_lse(sscore[~mask], q0[~mask])
    logodds = math.log(inside) - math.log(outside) + (sb - so)
    if logodds >= 0:
        post = 1.0 / (1.0 + math.exp(-min(logodds, 700.0)))
    else:
        z = math.exp(max(logodds, -700.0))
        post = z / (1.0 + z)
    out = np.zeros_like(q0)
    out[mask] = q0[mask] / inside * post
    out[~mask] = q0[~mask] / outside * (1.0 - post)
    return out / out.sum(), float(sb - so)


def apply_context(stop_p, stop_r, stop_keys, context_id, rectangles, q0,
                  native_post, timesteps, state: LedgerState):
    """Normative passive V5 path for one source-update context."""
    st, admitted = append_context(state, stop_p, stop_r, stop_keys, context_id)
    p, r, ctx = ledger_arrays(st)
    if p is None:
        d = V5Decision(False, "EMPTY_LEDGER", None, None, 0, 0, 0,
                       None, None, tuple())
        return _norm(native_post), st, d, False, None, None, None, admitted
    build = v4.build_components(p, rectangles, timesteps)
    d = context_blocked_m2(p, r, ctx, build.labels, q0, timesteps)
    if not d.accepted:
        return _norm(native_post), st, d, False, None, None, build, admitted
    if not member_loo_robust(p, r, ctx, build.labels, q0, timesteps, d.selected_mask):
        d.accepted = False
        d.reason = "SCORING_MEMBER_LOO_FAIL"
        return _norm(native_post), st, d, False, None, None, build, admitted
    st.q_causal, _ = causal_posterior_from_ledger(
        q0, p, r, d.selected_mask, timesteps
    )
    st.last_mask = d.selected_mask.copy()
    alpha = float(st.q_causal[d.selected_mask].sum())
    out, active, beta = v4.information_projection(
        native_post, d.selected_mask, alpha, q0
    )
    return out, st, d, active, alpha, beta, build, admitted


def _entropy_bernoulli(p):
    p = np.asarray(p, dtype=float)
    eps = np.finfo(float).eps
    p = np.clip(p, eps, 1.0 - eps)
    return -(p * np.log(p) + (1.0 - p) * np.log1p(-p))


def robust_probe_utility(candidate_probability, component_labels, source_weight,
                         candidate_cell_ids, feasible, visited):
    """Worst-scoring-member expected information gain for active measurement.

    candidate_probability: [S,M,X] predictive hit probabilities at candidate
      physical cells, computed before observing the next outcome.
    feasible: planner-feasible candidate mask; V5 never enlarges the native
      motion horizon.
    visited: physical-cell mask already used in the evidence ledger.

    The objective is parameter-free: maximize the minimum information gain
    across scoring members. Ties are resolved by the stable physical cell id.
    """
    p = np.asarray(candidate_probability, dtype=float)
    labels = np.asarray(component_labels, dtype=int)
    sw = _norm(source_weight, "source weight")
    cell = np.asarray(candidate_cell_ids)
    feasible = np.asarray(feasible, dtype=bool)
    visited = np.asarray(visited, dtype=bool)
    if p.ndim != 3 or p.shape[0] != len(labels) or p.shape[0] != len(sw):
        raise ValueError("probe shape mismatch")
    if p.shape[1] < K_CAL + K_SCORE:
        raise ValueError("need eight keyed members")
    X = p.shape[2]
    if len(cell) != X or len(feasible) != X or len(visited) != X:
        raise ValueError("candidate mask shape mismatch")
    if np.any((p < 0) | (p > 1)) or not np.all(np.isfinite(p)):
        raise ValueError("invalid candidate probability")

    comps, _ = _components(labels)
    if len(comps) < 2:
        return ProbeDecision(False, "ONE_COMPONENT", None, None, 0.0, None)

    comp_w = np.asarray([sw[ix].sum() for ix in comps], dtype=float)
    keep = comp_w > 0
    comps = [ix for ix, k in zip(comps, keep) if k]
    comp_w = comp_w[keep]
    comp_w /= comp_w.sum()
    if len(comps) < 2:
        return ProbeDecision(False, "ONE_WEIGHTED_COMPONENT", None, None, 0.0, None)

    member_ig = []
    for m in range(K_CAL, K_CAL + K_SCORE):
        cp = []
        for ix in comps:
            w = sw[ix]
            cp.append(np.sum(w[:, None] * p[ix, m, :], axis=0) / np.sum(w))
        cp = np.asarray(cp)
        mix = np.sum(comp_w[:, None] * cp, axis=0)
        ig = _entropy_bernoulli(mix) - np.sum(
            comp_w[:, None] * _entropy_bernoulli(cp), axis=0
        )
        member_ig.append(ig)
    utility = np.min(np.asarray(member_ig), axis=0)
    allowed = feasible & ~visited
    if not np.any(allowed):
        return ProbeDecision(False, "NO_FEASIBLE_UNVISITED_STOP", None, None, 0.0, utility)

    maxu = float(np.max(utility[allowed]))
    tol = _numzero(utility, maxu)
    if maxu <= tol:
        return ProbeDecision(False, "NO_POSITIVE_ROBUST_INFORMATION_GAIN", None, None, maxu, utility)
    idx = np.flatnonzero(allowed & (utility >= maxu - tol))
    chosen = int(idx[np.argmin(cell[idx].astype(np.int64))])
    return ProbeDecision(
        True, "PROBE", chosen, int(cell[chosen]), float(utility[chosen]), utility
    )

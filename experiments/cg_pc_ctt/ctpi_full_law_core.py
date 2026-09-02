#!/usr/bin/env python3
"""CTPI V0.3 full-law reference core.

This module implements the ResearchStudio/IdeaSpark revision of CTPI:

M1 CREL  : retain the complete empirical route-encounter law P_s(K).
M2 CDIG  : characterize source identifiability from the full count law rather
           than its mean projection.  It exposes both Cramer/CDF separation
           and the exact empirical replacement radius (total-variation units).
M3 APRS  : compare a candidate predictive law with the observed route-hit count
           using the Ranked Probability Score (RPS), a strictly proper score,
           and retain the *full* member-deletion robustness surface instead of
           selecting a fixed robustness threshold.

No truth, source-specific tuning, smoothing constant, bandwidth, temperature,
or fixed deletion level enters the mathematical core.
"""
from __future__ import annotations

import argparse
import functools
import itertools
from dataclasses import dataclass

import numpy as np


def route_member_counts(events: np.ndarray) -> np.ndarray:
    """[source,member,visible_stop] binary events -> [source,member] counts."""
    e = np.asarray(events)
    if e.ndim != 3 or e.shape[1] < 1 or e.shape[2] < 1:
        raise ValueError("CTPI_EVENT_SHAPE")
    if e.dtype != np.bool_:
        if not np.all((e == 0) | (e == 1)):
            raise ValueError("CTPI_EVENT_BINARY")
        e = e.astype(np.bool_)
    return np.sum(e, axis=2, dtype=np.int64)


def count_histograms(counts: np.ndarray, stop_count: int) -> np.ndarray:
    """Integer empirical histograms [source,K=0..N], each row sums to M."""
    k = np.asarray(counts, dtype=np.int64)
    if k.ndim != 2 or k.shape[1] < 1 or stop_count < 1:
        raise ValueError("CTPI_HIST_INPUT")
    if np.any(k < 0) or np.any(k > stop_count):
        raise ValueError("CTPI_HIST_RANGE")
    out = np.zeros((k.shape[0], stop_count + 1), dtype=np.int16)
    rows = np.repeat(np.arange(k.shape[0], dtype=np.int64), k.shape[1])
    np.add.at(out, (rows, k.ravel()), 1)
    return out


def cumulative_histograms(hist: np.ndarray) -> np.ndarray:
    """CDF numerators at thresholds 0..N-1; the final CDF value 1 is omitted."""
    h = np.asarray(hist, dtype=np.int64)
    if h.ndim != 2 or h.shape[1] < 2 or np.any(h < 0):
        raise ValueError("CTPI_CDF_INPUT")
    return np.cumsum(h, axis=1, dtype=np.int64)[:, :-1]


def f00_mean_projection_numerator(counts: np.ndarray) -> np.ndarray:
    """The source-dependent part of F00 mean projection: total member hits.

    With N visible stops and M members, frozen F00 uses
      qbar_s = [sum_m K_sm + 0.5*N] / [N*(M+1)].
    Hence two sources with the same returned integer are exactly indistinguish-
    able to the F00 *physical likelihood* for every observed hit count H.
    """
    k = np.asarray(counts, dtype=np.int64)
    if k.ndim != 2:
        raise ValueError("CTPI_F00_MEAN_INPUT")
    return np.sum(k, axis=1, dtype=np.int64)


def f00_qbar(counts: np.ndarray, stop_count: int) -> np.ndarray:
    k = np.asarray(counts, dtype=np.int64)
    if k.ndim != 2 or stop_count < 1:
        raise ValueError("CTPI_F00_QBAR_INPUT")
    m = k.shape[1]
    return (f00_mean_projection_numerator(k).astype(np.float64) + 0.5 * stop_count) / (
        float(stop_count) * float(m + 1)
    )


def cramer_energy_units(hist: np.ndarray) -> np.ndarray:
    """Pairwise integer CDF-squared separation.

    If C_s(k) is the empirical cumulative *count* (not probability), return
      G_ij = sum_{k=0}^{N-1} [C_i(k)-C_j(k)]^2.
    The normalized squared Cramer distance is G_ij/M^2.

    G=0 iff the empirical count laws are identical.  This is the same CDF
    geometry that appears in the RPS strict-propriety regret identity.
    """
    c = cumulative_histograms(hist).astype(np.int32)
    diff = c[:, None, :] - c[None, :, :]
    out = np.sum(diff * diff, axis=2, dtype=np.int64)
    np.fill_diagonal(out, 0)
    return out


def transport_replacement_radius(hist: np.ndarray) -> np.ndarray:
    """Exact empirical total-variation radius in member-replacement units.

      R^T_ij = 1/2 * sum_k |n_i(k)-n_j(k)|
             = M - sum_k min(n_i(k),n_j(k)).

    It equals the number of member outcomes outside the two histograms' maximal
    common overlap; equivalently, the minimum number of member outcomes that
    must be changed in ONE empirical law to transform it into the other.  It is
    an integer in [0,M], symmetric, label-invariant and threshold-free.
    """
    h = np.asarray(hist, dtype=np.int64)
    if h.ndim != 2 or np.any(h < 0):
        raise ValueError("CTPI_TV_INPUT")
    if not np.all(np.sum(h, axis=1) == np.sum(h[0])):
        raise ValueError("CTPI_TV_MEMBER_COUNT")
    l1 = np.sum(np.abs(h[:, None, :] - h[None, :, :]), axis=2, dtype=np.int64)
    if np.any(l1 % 2):
        raise RuntimeError("CTPI_TV_PARITY")
    out = (l1 // 2).astype(np.int16)
    np.fill_diagonal(out, 0)
    return out


def mean_alias_distinct_pairs(counts: np.ndarray, cramer_units: np.ndarray) -> np.ndarray:
    """Pairs tied by F00 mean projection but separated by the full law."""
    total = f00_mean_projection_numerator(counts)
    g = np.asarray(cramer_units, dtype=np.int64)
    if g.shape != (len(total), len(total)):
        raise ValueError("CTPI_ALIAS_SHAPE")
    out = (total[:, None] == total[None, :]) & (g > 0)
    np.fill_diagonal(out, False)
    return out


def rps_numerator(sample_counts: np.ndarray, observed_hit_count: int, stop_count: int) -> int:
    """Exact integer numerator of discrete Ranked Probability Score.

    For r retained ensemble members and empirical CDF numerator C(k),
      RPS = sum_{k=0}^{N-1} (C(k)/r - 1[H<=k])^2
          = A/r^2,
    where A is the returned non-negative integer.
    """
    x = np.asarray(sample_counts, dtype=np.int64)
    if x.ndim != 1 or x.size < 1 or stop_count < 1:
        raise ValueError("CTPI_RPS_INPUT")
    if observed_hit_count < 0 or observed_hit_count > stop_count:
        raise ValueError("CTPI_RPS_OBS_RANGE")
    if np.any(x < 0) or np.any(x > stop_count):
        raise ValueError("CTPI_RPS_COUNT_RANGE")
    hist = np.bincount(x, minlength=stop_count + 1)
    cum = np.cumsum(hist, dtype=np.int64)[:-1]
    r = int(x.size)
    target = (np.arange(stop_count, dtype=np.int64) >= int(observed_hit_count)).astype(np.int64)
    delta = cum - r * target
    return int(np.sum(delta * delta, dtype=np.int64))


def rps_value(sample_counts: np.ndarray, observed_hit_count: int, stop_count: int) -> float:
    x = np.asarray(sample_counts)
    return float(rps_numerator(x, observed_hit_count, stop_count) / float(x.size * x.size))


def _rps_hist_bound_one(hist_row: np.ndarray, observed_hit_count: int, retained: int,
                        *, maximize: bool) -> int:
    """Exact min/max RPS numerator over all retained sub-multisets of one law.

    Dynamic programming is over count bins, not member identities.  State z is
    how many members have been retained up to the current K threshold; the RPS
    cost contributed at threshold k is (z-r*1[H<=k])^2.  The terminal K=N bin
    has no RPS threshold term and only supplies the remaining retained members.
    """
    h = np.asarray(hist_row, dtype=np.int64)
    if h.ndim != 1 or h.size < 2 or np.any(h < 0):
        raise ValueError("CTPI_RPS_DP_HIST")
    m = int(np.sum(h))
    n = h.size - 1
    r = int(retained)
    if not 1 <= r <= m or not 0 <= observed_hit_count <= n:
        raise ValueError("CTPI_RPS_DP_RANGE")
    bad = -10**18 if maximize else 10**18
    dp = np.full(r + 1, bad, dtype=np.int64)
    dp[0] = 0
    for k in range(n):
        nxt = np.full(r + 1, bad, dtype=np.int64)
        target = r if observed_hit_count <= k else 0
        cap = min(int(h[k]), r)
        for z in range(r + 1):
            base = int(dp[z])
            if base == bad:
                continue
            for take in range(min(cap, r - z) + 1):
                z2 = z + take
                value = base + (z2 - target) ** 2
                if maximize:
                    if value > nxt[z2]: nxt[z2] = value
                else:
                    if value < nxt[z2]: nxt[z2] = value
        dp = nxt
    # K=N contributes no CDF term.  It only needs to supply enough retained mass.
    best = bad
    last_cap = int(h[n])
    for z in range(r + 1):
        if 0 <= r - z <= last_cap and int(dp[z]) != bad:
            if maximize:
                best = max(best, int(dp[z]))
            else:
                best = min(best, int(dp[z]))
    if best == bad:
        raise RuntimeError("CTPI_RPS_DP_NO_FEASIBLE")
    return int(best)


def rps_deletion_bounds(counts: np.ndarray, observed_hit_count: int, stop_count: int) -> tuple[np.ndarray, np.ndarray]:
    """Exact RPS numerator envelopes for every deletion level via histogram DP."""
    k = np.asarray(counts, dtype=np.int64)
    if k.ndim != 2 or k.shape[1] < 1:
        raise ValueError("CTPI_RPS_BOUNDS_SHAPE")
    hist = count_histograms(k, stop_count)
    s, m = k.shape
    lo = np.empty((s, m), dtype=np.int64)
    hi = np.empty((s, m), dtype=np.int64)
    for q in range(m):
        retained = m - q
        for i in range(s):
            lo[i, q] = _rps_hist_bound_one(hist[i], observed_hit_count, retained, maximize=False)
            hi[i, q] = _rps_hist_bound_one(hist[i], observed_hit_count, retained, maximize=True)
    return lo, hi


def _rps_deletion_bounds_exhaustive(counts: np.ndarray, observed_hit_count: int, stop_count: int) -> tuple[np.ndarray, np.ndarray]:
    """Slow member-identity enumeration used only to validate the DP."""
    k = np.asarray(counts, dtype=np.int64)
    s, m = k.shape
    lo = np.empty((s, m), dtype=np.int64); hi = np.empty((s, m), dtype=np.int64)
    for q in range(m):
        retained = m-q
        subsets = tuple(itertools.combinations(range(m), retained))
        for i in range(s):
            vals=[rps_numerator(k[i,list(idx)], observed_hit_count, stop_count) for idx in subsets]
            lo[i,q]=min(vals); hi[i,q]=max(vals)
    return lo,hi

def observation_rps_robustness_depth(counts: np.ndarray, observed_hit_count: int, stop_count: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Directed robust proper-score preference depth.

    At deletion q, source a is unambiguously better than b iff the WORST RPS of
    a is strictly lower than the BEST RPS of b, over all q-member deletions
    from each source ensemble.  Depth R means this held at every q=0..R-1.
    No fixed deletion q is selected.
    """
    lo, hi = rps_deletion_bounds(counts, observed_hit_count, stop_count)
    s, m = lo.shape
    out = np.zeros((s, s), dtype=np.int8)
    alive = ~np.eye(s, dtype=np.bool_)
    for q in range(m):
        current = hi[:, q][:, None] < lo[:, q][None, :]
        alive &= current
        out[alive] = q + 1
        if not np.any(alive):
            break
    np.fill_diagonal(out, 0)
    return out, lo, hi


def survivor_surface(transport_radius: np.ndarray, observation_depth: np.ndarray, member_count: int) -> np.ndarray:
    """2-D parameter-free robustness surface [rT,rO,source].

    For intrinsic levels rT,rO=1..M, source b is eliminated if some source a
    has transport replacement radius >=rT AND observation RPS robustness depth
    >=rO.  No scalarization between the physical and observational axes occurs.
    """
    t = np.asarray(transport_radius, dtype=np.int64)
    o = np.asarray(observation_depth, dtype=np.int64)
    if t.shape != o.shape or t.ndim != 2 or t.shape[0] != t.shape[1]:
        raise ValueError("CTPI_SURFACE_SHAPE")
    if np.any(t < 0) or np.any(t > member_count) or np.any(o < 0) or np.any(o > member_count):
        raise ValueError("CTPI_SURFACE_RANGE")
    s = t.shape[0]
    out = np.zeros((member_count, member_count, s), dtype=np.bool_)
    for rt in range(1, member_count + 1):
        tmask = t >= rt
        for ro in range(1, member_count + 1):
            relation = tmask & (o >= ro)
            out[rt - 1, ro - 1] = ~np.any(relation, axis=0)
    return out


def surface_persistence(surface: np.ndarray) -> np.ndarray:
    """Fraction of intrinsic (rT,rO) cells at which each source survives.

    This is a descriptive support score, not a calibrated posterior.
    """
    x = np.asarray(surface, dtype=np.bool_)
    if x.ndim != 3 or x.shape[0] < 1 or x.shape[1] < 1:
        raise ValueError("CTPI_PERSISTENCE_SHAPE")
    return np.mean(x, axis=(0, 1), dtype=np.float64)


def persistence_mass(persistence: np.ndarray, prior_mass: np.ndarray) -> np.ndarray:
    p = np.asarray(persistence, dtype=np.float64)
    q = np.asarray(prior_mass, dtype=np.float64)
    if p.shape != q.shape or p.ndim != 1 or np.any(p < 0) or np.any(q < 0):
        raise ValueError("CTPI_PERSISTENCE_MASS_INPUT")
    raw = p * q
    total = float(np.sum(raw))
    if not np.isfinite(total) or total <= 0:
        raise ValueError("CTPI_PERSISTENCE_MASS_ZERO")
    return raw / total


def surface_area(surface: np.ndarray, prior_mass: np.ndarray) -> np.ndarray:
    """q0 mass of each [rT,rO] survivor set."""
    x = np.asarray(surface, dtype=np.bool_)
    q = np.asarray(prior_mass, dtype=np.float64)
    if x.ndim != 3 or q.ndim != 1 or x.shape[2] != q.size or np.any(q < 0):
        raise ValueError("CTPI_SURFACE_AREA_INPUT")
    q = q / float(np.sum(q))
    return np.tensordot(x.astype(np.float64), q, axes=([2], [0]))


def integrated_excess_identification(surface: np.ndarray, prior_mass: np.ndarray, source_index: int) -> float:
    """Mean source inclusion minus survivor-area mass over the intrinsic grid."""
    x = np.asarray(surface, dtype=np.bool_)
    if not 0 <= source_index < x.shape[2]:
        raise ValueError("CTPI_J_SOURCE")
    area = surface_area(x, prior_mass)
    incl = x[:, :, source_index].astype(np.float64)
    return float(np.mean(incl - area))


def cyclic_reassignment_indices(source_count: int, shift: int) -> np.ndarray:
    if source_count < 2 or not 1 <= shift < source_count:
        raise ValueError("CTPI_CYCLIC_SHIFT")
    return (np.arange(source_count, dtype=np.int64) + int(shift)) % source_count


def reassign_source_distributions(counts: np.ndarray, shift: int) -> np.ndarray:
    k = np.asarray(counts, dtype=np.int64)
    if k.ndim != 2:
        raise ValueError("CTPI_REASSIGN_SHAPE")
    return k[cyclic_reassignment_indices(k.shape[0], shift)].copy()


def transport_break_strength(radius: np.ndarray, shift: int, member_count: int) -> float:
    """Mean normalized physical distribution separation broken by reassignment."""
    r = np.asarray(radius, dtype=np.int64)
    if r.ndim != 2 or r.shape[0] != r.shape[1]:
        raise ValueError("CTPI_BREAK_SHAPE")
    pi = cyclic_reassignment_indices(r.shape[0], shift)
    vals = r[np.arange(r.shape[0]), pi].astype(np.float64)
    return float(np.mean(vals) / float(member_count))


def expected_rps_regret(true_counts: np.ndarray, forecast_counts: np.ndarray, stop_count: int) -> float:
    """Empirical expectation E_{H~P}[RPS(Q,H)-RPS(P,H)]."""
    p = np.asarray(true_counts, dtype=np.int64)
    q = np.asarray(forecast_counts, dtype=np.int64)
    if p.ndim != 1 or q.ndim != 1:
        raise ValueError("CTPI_EXPECTED_RPS_INPUT")
    return float(np.mean([rps_value(q, int(h), stop_count) - rps_value(p, int(h), stop_count) for h in p]))


def cramer_regret_identity(true_counts: np.ndarray, forecast_counts: np.ndarray, stop_count: int) -> float:
    """Theoretical RPS regret from squared CDF distance."""
    p = np.asarray(true_counts, dtype=np.int64)
    q = np.asarray(forecast_counts, dtype=np.int64)
    hp = np.bincount(p, minlength=stop_count + 1)
    hq = np.bincount(q, minlength=stop_count + 1)
    fp = np.cumsum(hp)[:-1] / float(len(p))
    fq = np.cumsum(hq)[:-1] / float(len(q))
    return float(np.sum((fp - fq) ** 2))


@dataclass(frozen=True)
class FullLawCTPIResult:
    counts: np.ndarray
    hist: np.ndarray
    cramer_units: np.ndarray
    transport_radius: np.ndarray
    mean_alias_distinct: np.ndarray
    observation_depth: np.ndarray
    rps_min_num: np.ndarray
    rps_max_num: np.ndarray
    surface: np.ndarray
    persistence: np.ndarray


def evaluate(events: np.ndarray, observed_hit_count: int) -> FullLawCTPIResult:
    e = np.asarray(events)
    if e.ndim != 3:
        raise ValueError("CTPI_EVAL_EVENT_SHAPE")
    n = int(e.shape[2])
    counts = route_member_counts(e)
    hist = count_histograms(counts, n)
    g = cramer_energy_units(hist)
    r = transport_replacement_radius(hist)
    alias = mean_alias_distinct_pairs(counts, g)
    obs, lo, hi = observation_rps_robustness_depth(counts, observed_hit_count, n)
    surface = survivor_surface(r, obs, counts.shape[1])
    persistence = surface_persistence(surface)
    return FullLawCTPIResult(counts, hist, g, r, alias, obs, lo, hi, surface, persistence)


def selftest(iterations: int = 4000) -> None:
    rng = np.random.default_rng(20260902)

    # ResearchStudio load-bearing strict-expressivity counterexample:
    # same F00 mean projection, different full transport laws.
    a = np.asarray([0, 0, 0, 0, 4, 4, 4, 4], dtype=np.int64)
    b = np.asarray([2, 2, 2, 2, 2, 2, 2, 2], dtype=np.int64)
    pair = np.stack([a, b])
    hist = count_histograms(pair, 4)
    g = cramer_energy_units(hist)
    tv = transport_replacement_radius(hist)
    assert f00_mean_projection_numerator(pair)[0] == f00_mean_projection_numerator(pair)[1]
    assert f00_qbar(pair, 4)[0] == f00_qbar(pair, 4)[1]
    assert g[0, 1] > 0 and tv[0, 1] > 0
    # Strict propriety: expected RPS uniquely favors the true full law.
    regret = expected_rps_regret(a, b, 4)
    identity = cramer_regret_identity(a, b, 4)
    assert regret > 0.0
    assert abs(regret - identity) < 1e-12

    # Exact RPS integer numerator against floating representation.
    for m in range(1, 9):
        for _ in range(100):
            n = int(rng.integers(1, 16))
            x = rng.integers(0, n + 1, size=m)
            h = int(rng.integers(0, n + 1))
            num = rps_numerator(x, h, n)
            assert num >= 0
            # direct CDF implementation
            hh = np.bincount(x, minlength=n + 1)
            F = np.cumsum(hh)[:-1] / float(m)
            y = (np.arange(n) >= h).astype(float)
            direct = float(np.sum((F - y) ** 2))
            assert abs(direct - num / float(m * m)) < 1e-12

    # Histogram DP equals exhaustive member-subset enumeration.
    for m in range(1, 7):
        for _ in range(80):
            n = int(rng.integers(1, 9))
            kk = rng.integers(0, n + 1, size=(3, m))
            hh = int(rng.integers(0, n + 1))
            lo1, hi1 = rps_deletion_bounds(kk, hh, n)
            lo2, hi2 = _rps_deletion_bounds_exhaustive(kk, hh, n)
            assert np.array_equal(lo1, lo2)
            assert np.array_equal(hi1, hi2)

    for _ in range(iterations):
        sources = int(rng.integers(3, 14))
        members = int(rng.integers(3, 9))
        stops = int(rng.integers(1, 16))
        prob = rng.uniform(0.05, 0.95, size=(sources, 1, 1))
        events = rng.random((sources, members, stops)) < prob
        h = int(rng.integers(0, stops + 1))
        out = evaluate(events, h)

        assert out.hist.shape == (sources, stops + 1)
        assert np.all(out.hist.sum(axis=1) == members)
        assert out.cramer_units.shape == (sources, sources)
        assert out.transport_radius.shape == (sources, sources)
        assert np.all(out.cramer_units >= 0)
        assert np.all((out.transport_radius >= 0) & (out.transport_radius <= members))
        assert np.array_equal(out.transport_radius, out.transport_radius.T)
        assert np.array_equal(out.cramer_units, out.cramer_units.T)
        assert np.array_equal(out.cramer_units == 0, out.transport_radius == 0)
        assert out.observation_depth.shape == (sources, sources)
        assert np.all((out.observation_depth >= 0) & (out.observation_depth <= members))
        assert out.surface.shape == (members, members, sources)
        assert np.all((out.persistence >= 0.0) & (out.persistence <= 1.0))
        # Stronger robustness requirements can only grow the survivor set.
        assert np.all(out.surface[:-1, :, :] <= out.surface[1:, :, :])
        assert np.all(out.surface[:, :-1, :] <= out.surface[:, 1:, :])

        # Member-label invariance independently per source.
        perm = events.copy()
        for s in range(sources):
            perm[s] = perm[s, rng.permutation(members)]
        op = evaluate(perm, h)
        assert np.array_equal(out.hist, op.hist)
        assert np.array_equal(out.cramer_units, op.cramer_units)
        assert np.array_equal(out.transport_radius, op.transport_radius)
        assert np.array_equal(out.observation_depth, op.observation_depth)
        assert np.array_equal(out.surface, op.surface)

        # Count-only stop/time permutation invariance.
        ot = evaluate(events[:, :, ::-1], h)
        assert np.array_equal(out.counts, ot.counts)
        assert np.array_equal(out.surface, ot.surface)

        # Candidate permutation equivariance.
        p = rng.permutation(sources); inv = np.argsort(p)
        os = evaluate(events[p], h)
        assert np.array_equal(out.cramer_units, os.cramer_units[np.ix_(inv, inv)])
        assert np.array_equal(out.transport_radius, os.transport_radius[np.ix_(inv, inv)])
        assert np.array_equal(out.observation_depth, os.observation_depth[np.ix_(inv, inv)])
        assert np.array_equal(out.surface, os.surface[:, :, inv])

        # R_T is exactly the number of members outside the multiset overlap.
        overlap = np.sum(np.minimum(out.hist[:, None, :], out.hist[None, :, :]), axis=2)
        assert np.array_equal(out.transport_radius.astype(np.int64), members - overlap)

        # F00 mean aliases are exactly tied in qbar, but full-law alias means G>0.
        alias = out.mean_alias_distinct
        if np.any(alias):
            qb = f00_qbar(out.counts, stops)
            ii, jj = np.where(alias)
            assert np.all(qb[ii] == qb[jj])
            assert np.all(out.cramer_units[ii, jj] > 0)

        # Source reassignment is a physical-label permutation of the complete laws.
        if sources > 2:
            shift = int(rng.integers(1, sources))
            pi = cyclic_reassignment_indices(sources, shift)
            rr = reassign_source_distributions(out.counts, shift)
            hr = count_histograms(rr, stops)
            assert np.array_equal(cramer_energy_units(hr), out.cramer_units[np.ix_(pi, pi)])
            assert np.array_equal(transport_replacement_radius(hr), out.transport_radius[np.ix_(pi, pi)])
            br = transport_break_strength(out.transport_radius, shift, members)
            assert 0.0 <= br <= 1.0

        # J is bounded.
        q0 = rng.random(sources); q0 /= q0.sum()
        j = integrated_excess_identification(out.surface, q0, int(rng.integers(0, sources)))
        assert -1.0 <= j <= 1.0

    print(f"CTPI_FULL_LAW_SELFTEST=PASS iterations={iterations}")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--iterations", type=int, default=4000)
    args = p.parse_args()
    if args.selftest:
        selftest(args.iterations)
        return 0
    p.error("reference core currently exposes --selftest only")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

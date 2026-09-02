#!/usr/bin/env python3
"""CTPI M2 source-intervention predictive-law calibration reference.

This module calibrates the forward probability object actually consumed by M3:

    P(Y_next | do(S=s), action=a, physical context)

A calibration/confirmation record is generated in a simulator world whose source
`s` was deliberately set by the experimental protocol.  The controlled source
is therefore an input/intervention of the forward-model experiment, not a hidden
localization truth available to the runtime estimator or planner.

No M1 posterior, localization error, source rank, planner reward, or future
counterfactual outcome enters the fit.
"""
from __future__ import annotations

import math
from typing import Any, Sequence

import numpy as np


MEMBER_COUNT = 8
JEFFREYS_ALPHA = 0.5
PAIR_TOL = 1.0e-12
NLL_CLIP = 1.0e-12
VARIATION_TOL = 1.0e-6


def _counts_1d(value: np.ndarray) -> np.ndarray:
    k = np.asarray(value)
    if k.ndim != 1 or not np.issubdtype(k.dtype, np.integer):
        raise ValueError("CTPI_M2_INTERVENTION_COUNT_SHAPE")
    if np.any(k < 0) or np.any(k > MEMBER_COUNT):
        raise ValueError("CTPI_M2_INTERVENTION_COUNT_RANGE")
    return k.astype(np.int64, copy=False)


def _events_1d(value: np.ndarray, n: int) -> np.ndarray:
    y = np.asarray(value, dtype=np.float64)
    if y.shape != (n,) or not np.all((y == 0.0) | (y == 1.0)):
        raise ValueError("CTPI_M2_INTERVENTION_EVENT")
    return y


def baseline_probability(member_hit_count: np.ndarray) -> np.ndarray:
    """Frozen finite-eight-member Jeffreys predictive probability."""
    k = _counts_1d(member_hit_count)
    return (k.astype(np.float64) + JEFFREYS_ALPHA) / (MEMBER_COUNT + 1.0)


def _pav(values: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """Deterministic increasing weighted PAV; equality remains unpooled."""
    y = np.asarray(values, dtype=np.float64)
    w = np.asarray(weights, dtype=np.float64)
    if y.shape != (MEMBER_COUNT + 1,) or w.shape != y.shape:
        raise ValueError("CTPI_M2_INTERVENTION_PAV_SHAPE")
    if np.any(w <= 0.0) or not np.isfinite(y).all() or not np.isfinite(w).all():
        raise ValueError("CTPI_M2_INTERVENTION_PAV_INPUT")
    blocks: list[list[float | int]] = []
    for index, (mean, weight) in enumerate(zip(y, w)):
        blocks.append([index, index, float(weight), float(mean) * float(weight)])
        while len(blocks) >= 2:
            left, right = blocks[-2], blocks[-1]
            left_mean = float(left[3]) / float(left[2])
            right_mean = float(right[3]) / float(right[2])
            if left_mean <= right_mean:
                break
            blocks[-2:] = [[
                int(left[0]), int(right[1]),
                float(left[2]) + float(right[2]),
                float(left[3]) + float(right[3]),
            ]]
    out = np.empty_like(y)
    for start, end, weight, weighted_sum in blocks:
        out[int(start):int(end) + 1] = float(weighted_sum) / float(weight)
    if np.any(np.diff(out) < -PAIR_TOL):
        raise RuntimeError("CTPI_M2_INTERVENTION_PAV_MONOTONICITY")
    return out


def fit_source_intervention_table(
    member_hit_count: np.ndarray,
    observed_event: np.ndarray,
) -> dict[str, Any]:
    """Fit one global source-conditioned reliability table on CAL records.

    Every input row is a real forward-model intervention record: `K` and `Y`
    refer to the same deliberately controlled source and action.  This avoids
    posterior-smearing across counterfactual sources.
    """
    k = _counts_1d(member_hit_count)
    y = _events_1d(observed_event, len(k))
    count = np.bincount(k, minlength=MEMBER_COUNT + 1).astype(np.float64)
    hit = np.bincount(k, weights=y, minlength=MEMBER_COUNT + 1).astype(np.float64)
    preliminary = (hit + JEFFREYS_ALPHA) / (count + 2.0 * JEFFREYS_ALPHA)
    pav_weight = count + 2.0 * JEFFREYS_ALPHA
    table = _pav(preliminary, pav_weight)
    if np.any(table <= 0.0) or np.any(table >= 1.0) or not np.isfinite(table).all():
        raise RuntimeError("CTPI_M2_INTERVENTION_TABLE")
    return {
        "contract": "CTPI_M2_SOURCE_INTERVENTION_ISOTONIC_V1",
        "member_count": MEMBER_COUNT,
        "jeffreys_alpha": JEFFREYS_ALPHA,
        "record_count": int(len(k)),
        "count_by_k": count.tolist(),
        "hit_by_k": hit.tolist(),
        "preliminary_rate": preliminary.tolist(),
        "pav_weight": pav_weight.tolist(),
        "table": table.tolist(),
        "m1_posterior_access": False,
        "localization_truth_access": False,
        "controlled_source_is_forward_intervention": True,
    }


def calibrated_probability(
    member_hit_count: np.ndarray,
    table: Sequence[float],
) -> np.ndarray:
    """Map any source/action member-hit-count tensor to calibrated probability."""
    k = np.asarray(member_hit_count)
    mapping = np.asarray(table, dtype=np.float64)
    if mapping.shape != (MEMBER_COUNT + 1,) or np.any(np.diff(mapping) < -PAIR_TOL):
        raise ValueError("CTPI_M2_INTERVENTION_MAPPING")
    if np.any(mapping <= 0.0) or np.any(mapping >= 1.0) or not np.isfinite(mapping).all():
        raise ValueError("CTPI_M2_INTERVENTION_MAPPING_RANGE")
    if not np.issubdtype(k.dtype, np.integer) or np.any(k < 0) or np.any(k > MEMBER_COUNT):
        raise ValueError("CTPI_M2_INTERVENTION_CALIBRATED_COUNT")
    return mapping[k]


def _loss(probability: np.ndarray, observed: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    p = np.asarray(probability, dtype=np.float64)
    y = np.asarray(observed, dtype=np.float64)
    if p.shape != y.shape or p.ndim != 1:
        raise ValueError("CTPI_M2_INTERVENTION_LOSS_SHAPE")
    clipped = np.clip(p, NLL_CLIP, 1.0 - NLL_CLIP)
    nll = -(y * np.log(clipped) + (1.0 - y) * np.log1p(-clipped))
    return nll, (p - y) ** 2


def _ece(probability: np.ndarray, observed: np.ndarray) -> float:
    p = np.asarray(probability, dtype=np.float64)
    y = np.asarray(observed, dtype=np.float64)
    bins = np.minimum((p * 5.0).astype(np.int64), 4)
    total = int(len(p))
    if total == 0:
        raise ValueError("CTPI_M2_INTERVENTION_ECE_EMPTY")
    value = 0.0
    for b in range(5):
        mask = bins == b
        n = int(np.count_nonzero(mask))
        if n:
            value += n / total * abs(float(np.mean(p[mask])) - float(np.mean(y[mask])))
    return float(value)


def _sign_p(wins: int, losses: int) -> float:
    n = int(wins + losses)
    if n == 0:
        return 1.0
    return float(sum(math.comb(n, k) for k in range(int(wins), n + 1)) / (2 ** n))


def _paired(left: np.ndarray, right: np.ndarray) -> dict[str, Any]:
    wins = int(np.count_nonzero(right < left - PAIR_TOL))
    losses = int(np.count_nonzero(right > left + PAIR_TOL))
    return {
        "pairs": int(len(left)),
        "wins": wins,
        "losses": losses,
        "ties": int(len(left) - wins - losses),
        "one_sided_exact_sign_p": _sign_p(wins, losses),
        "baseline_mean": float(np.mean(left)),
        "m2_mean": float(np.mean(right)),
    }


def evaluate_source_intervention_gate(
    member_hit_count: np.ndarray,
    observed_event: np.ndarray,
    tape_id: Sequence[str],
    house: Sequence[str],
    controlled_source_id: Sequence[str],
    action_id: Sequence[str],
    table: Sequence[float],
) -> dict[str, Any]:
    """One-shot CONFIRM Gate on the source-conditioned forward law itself."""
    k = _counts_1d(member_hit_count)
    y = _events_1d(observed_event, len(k))
    tapes = np.asarray(tape_id, dtype=str)
    houses = np.asarray(house, dtype=str)
    sources = np.asarray(controlled_source_id, dtype=str)
    actions = np.asarray(action_id, dtype=str)
    for name, value in {
        "tape": tapes, "house": houses, "source": sources, "action": actions,
    }.items():
        if value.shape != y.shape or np.any(value == ""):
            raise ValueError(f"CTPI_M2_INTERVENTION_METADATA:{name}")

    base = baseline_probability(k)
    m2 = calibrated_probability(k, table)
    base_nll, base_brier = _loss(base, y)
    m2_nll, m2_brier = _loss(m2, y)

    unique_tapes = sorted(set(tapes.tolist()))
    tape_house: list[str] = []
    bn: list[float] = []; mn: list[float] = []
    bb: list[float] = []; mb: list[float] = []
    for name in unique_tapes:
        mask = tapes == name
        if int(np.count_nonzero(mask)) != 15:
            raise ValueError("CTPI_M2_INTERVENTION_TAPE_EVENT_COUNT")
        hh = sorted(set(houses[mask].tolist()))
        ss = sorted(set(sources[mask].tolist()))
        if len(hh) != 1 or len(ss) != 1:
            raise ValueError("CTPI_M2_INTERVENTION_TAPE_IDENTITY")
        if len(set(actions[mask].tolist())) != 15:
            raise ValueError("CTPI_M2_INTERVENTION_ACTION_IDENTITY")
        tape_house.append(hh[0])
        bn.append(float(np.mean(base_nll[mask])))
        mn.append(float(np.mean(m2_nll[mask])))
        bb.append(float(np.mean(base_brier[mask])))
        mb.append(float(np.mean(m2_brier[mask])))

    bn_a = np.asarray(bn); mn_a = np.asarray(mn)
    bb_a = np.asarray(bb); mb_a = np.asarray(mb)
    nll_pair = _paired(bn_a, mn_a)
    brier_pair = _paired(bb_a, mb_a)

    by_house: dict[str, Any] = {}
    stable_reverse: list[str] = []
    for hh in ("H01", "H02", "H03"):
        mask = np.asarray([v == hh for v in tape_house], dtype=np.bool_)
        if int(np.count_nonzero(mask)) != 10:
            raise ValueError(f"CTPI_M2_INTERVENTION_CONFIRM_TAPES:{hh}")
        hn = _paired(bn_a[mask], mn_a[mask])
        hb = _paired(bb_a[mask], mb_a[mask])
        reverse = bool(
            float(np.mean(mn_a[mask])) > float(np.mean(bn_a[mask])) and
            float(np.mean(mb_a[mask])) > float(np.mean(bb_a[mask])) and
            hn["losses"] >= 8 and hb["losses"] >= 8
        )
        if reverse:
            stable_reverse.append(hh)
        by_house[hh] = {
            "paired_tape_nll": hn,
            "paired_tape_brier": hb,
            "stable_reverse_both": reverse,
        }

    mapping = np.asarray(table, dtype=np.float64)
    distinct = 1 + int(np.count_nonzero(np.diff(mapping) > VARIATION_TOL))
    count_coverage = sorted(set(int(v) for v in k.tolist()))
    criteria = {
        "direct_source_conditioned_nll_lower": bool(np.mean(m2_nll) < np.mean(base_nll)),
        "direct_source_conditioned_brier_lower": bool(np.mean(m2_brier) < np.mean(base_brier)),
        "paired_sign_support": bool(
            nll_pair["one_sided_exact_sign_p"] <= 0.05 or
            brier_pair["one_sided_exact_sign_p"] <= 0.05
        ),
        "ece_not_worse": bool(_ece(m2, y) <= _ece(base, y) + PAIR_TOL),
        "no_stable_reverse_house": not stable_reverse,
        "at_least_three_table_values": distinct >= 3,
        "at_least_three_observed_k_levels": len(count_coverage) >= 3,
        "finite_interior_probability": bool(
            np.isfinite(m2).all() and np.all((m2 > 0.0) & (m2 < 1.0))
        ),
    }
    passed = all(criteria.values())
    return {
        "contract": "CTPI_M2_SOURCE_INTERVENTION_CONFIRM_GATE_V1",
        "controlled_source_is_forward_intervention": True,
        "m1_posterior_argument_present": False,
        "events": int(len(y)),
        "tapes": int(len(unique_tapes)),
        "k_coverage": count_coverage,
        "baseline": {
            "nll": float(np.mean(base_nll)),
            "brier": float(np.mean(base_brier)),
            "ece_5bin": _ece(base, y),
        },
        "m2": {
            "nll": float(np.mean(m2_nll)),
            "brier": float(np.mean(m2_brier)),
            "ece_5bin": _ece(m2, y),
        },
        "paired_tape_nll": nll_pair,
        "paired_tape_brier": brier_pair,
        "by_house": by_house,
        "stable_reverse_houses": stable_reverse,
        "distinct_table_values": distinct,
        "criteria": criteria,
        "pass": passed,
        "verdict": (
            "CTPI_M2_SOURCE_CONDITIONED_PREDICTIVE_GATE_PASS"
            if passed else "CTPI_M2_SOURCE_CONDITIONED_PREDICTIVE_GATE_NO_GO"
        ),
    }


def selftest() -> None:
    # CAL: outcomes are attached to their own controlled-source records; no
    # posterior weighting or hidden source label is needed.
    k = np.tile(np.arange(9, dtype=np.int64), 20)
    probability = np.asarray([0.03, 0.08, 0.15, 0.27, 0.43, 0.60, 0.74, 0.86, 0.96])
    # Deterministic fixture fixed from record index and k; no future value is
    # used to construct any predictor input.
    u = ((np.arange(len(k)) * 37 + 11) % 101) / 101.0
    y = (u < probability[k]).astype(np.int8)
    fit = fit_source_intervention_table(k, y)
    table = np.asarray(fit["table"], dtype=np.float64)
    assert np.all(np.diff(table) >= -PAIR_TOL)
    assert fit["m1_posterior_access"] is False

    # Mechanical metadata/gate smoke with 30 tapes x 15 events.  Use a fixed
    # non-degenerate monotone mapping to test Gate plumbing rather than claim a
    # scientific PASS from this synthetic fixture.
    events = 30 * 15
    kk = np.tile(np.arange(15, dtype=np.int64) % 9, 30)
    pp = probability[kk]
    uu = ((np.arange(events) * 29 + 7) % 103) / 103.0
    yy = (uu < pp).astype(np.int8)
    houses = np.repeat(np.asarray(["H01", "H02", "H03"]), 10 * 15)
    tapes = np.asarray([
        f"{h}_src{i:02d}" for h in ("H01", "H02", "H03")
        for i in range(10) for _ in range(15)
    ])
    sources = np.asarray([
        f"controlled_{h}_{i:02d}" for h in ("H01", "H02", "H03")
        for i in range(10) for _ in range(15)
    ])
    actions = np.asarray([
        f"{h}_{i:02d}_a{j:02d}" for h in ("H01", "H02", "H03")
        for i in range(10) for j in range(15)
    ])
    report = evaluate_source_intervention_gate(
        kk, yy, tapes, houses, sources, actions, probability
    )
    assert report["m1_posterior_argument_present"] is False
    assert report["controlled_source_is_forward_intervention"] is True
    assert len(report["k_coverage"]) == 9
    print("CTPI_M2_SOURCE_INTERVENTION_CORE_SELFTEST=PASS")


if __name__ == "__main__":
    selftest()

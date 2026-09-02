#!/usr/bin/env python3
"""Truth-blind CTPI M2 future-event calibration and confirmatory Gate."""
from __future__ import annotations

import math
from typing import Any, Sequence

import numpy as np


MEMBER_COUNT = 8
JEFFREYS_ALPHA = 0.5
PAIR_TOL = 1.0e-12
VARIATION_TOL = 1.0e-6
NLL_CLIP = 1.0e-12


def _posterior(value: np.ndarray) -> np.ndarray:
    q = np.asarray(value, dtype=np.float64)
    if q.ndim != 2 or q.shape[1] < 2 or np.any(q < 0.0) or not np.isfinite(q).all():
        raise ValueError("CTPI_M2_POSTERIOR")
    total = np.sum(q, axis=1)
    if np.any(total <= 0.0):
        raise ValueError("CTPI_M2_POSTERIOR_MASS")
    return q / total[:, None]


def _counts(value: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    k = np.asarray(value)
    if k.shape != shape or not np.issubdtype(k.dtype, np.integer):
        raise ValueError("CTPI_M2_MEMBER_COUNTS")
    if np.any(k < 0) or np.any(k > MEMBER_COUNT):
        raise ValueError("CTPI_M2_MEMBER_COUNT_RANGE")
    return k.astype(np.int64, copy=False)


def baseline_source_probability(member_hit_count: np.ndarray) -> np.ndarray:
    k = np.asarray(member_hit_count)
    if not np.issubdtype(k.dtype, np.integer) or np.any(k < 0) or np.any(k > MEMBER_COUNT):
        raise ValueError("CTPI_M2_BASELINE_COUNT")
    return (k.astype(np.float64) + JEFFREYS_ALPHA) / (MEMBER_COUNT + 1.0)


def _pav(values: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """Deterministic weighted increasing PAV; equality remains unpooled."""
    y = np.asarray(values, dtype=np.float64)
    w = np.asarray(weights, dtype=np.float64)
    if y.shape != (MEMBER_COUNT + 1,) or w.shape != y.shape or np.any(w <= 0.0):
        raise ValueError("CTPI_M2_PAV_INPUT")
    blocks: list[list[float | int]] = []
    for index, (mean, weight) in enumerate(zip(y, w)):
        blocks.append([index, index, float(weight), float(mean) * float(weight)])
        while len(blocks) >= 2:
            left, right = blocks[-2], blocks[-1]
            if float(left[3]) / float(left[2]) <= float(right[3]) / float(right[2]):
                break
            blocks[-2:] = [[int(left[0]), int(right[1]),
                            float(left[2]) + float(right[2]),
                            float(left[3]) + float(right[3])]]
    result = np.empty_like(y)
    for start, end, weight, weighted_sum in blocks:
        result[int(start):int(end) + 1] = float(weighted_sum) / float(weight)
    if np.any(np.diff(result) < -PAIR_TOL):
        raise RuntimeError("CTPI_M2_PAV_MONOTONICITY")
    return result


def fit_calibration_table(
    pre_event_posterior: np.ndarray,
    member_hit_count: np.ndarray,
    observed_event: np.ndarray,
) -> dict[str, Any]:
    """Fit the single preregistered global table without a truth-source label."""
    posterior = _posterior(pre_event_posterior)
    counts = _counts(member_hit_count, posterior.shape)
    observed = np.asarray(observed_event, dtype=np.float64)
    if observed.shape != (posterior.shape[0],) or not np.all((observed == 0.0) | (observed == 1.0)):
        raise ValueError("CTPI_M2_OBSERVED_EVENT")

    weight = np.zeros(MEMBER_COUNT + 1, dtype=np.float64)
    success = np.zeros_like(weight)
    for k in range(MEMBER_COUNT + 1):
        latent_weight = posterior * (counts == k)
        weight[k] = float(np.sum(latent_weight))
        success[k] = float(np.sum(latent_weight * observed[:, None]))
    preliminary = (success + JEFFREYS_ALPHA) / (weight + 2.0 * JEFFREYS_ALPHA)
    pav_weight = weight + 2.0 * JEFFREYS_ALPHA
    table = _pav(preliminary, pav_weight)
    if np.any(table <= 0.0) or np.any(table >= 1.0) or not np.isfinite(table).all():
        raise RuntimeError("CTPI_M2_CALIBRATION_TABLE")
    return {
        "contract": "CTPI_M2_GLOBAL_WEIGHTED_ISOTONIC_V1",
        "member_count": MEMBER_COUNT,
        "jeffreys_alpha": JEFFREYS_ALPHA,
        "fractional_weight": weight.tolist(),
        "fractional_success": success.tolist(),
        "preliminary_rate": preliminary.tolist(),
        "pav_weight": pav_weight.tolist(),
        "table": table.tolist(),
        "cal_transition_count": int(posterior.shape[0]),
        "source_truth_access": False,
    }


def calibrated_source_probability(member_hit_count: np.ndarray, table: Sequence[float]) -> np.ndarray:
    k = np.asarray(member_hit_count)
    mapping = np.asarray(table, dtype=np.float64)
    if mapping.shape != (MEMBER_COUNT + 1,) or np.any(np.diff(mapping) < -PAIR_TOL):
        raise ValueError("CTPI_M2_CALIBRATION_MAPPING")
    if np.any(mapping <= 0.0) or np.any(mapping >= 1.0) or not np.isfinite(mapping).all():
        raise ValueError("CTPI_M2_CALIBRATION_PROBABILITY")
    if not np.issubdtype(k.dtype, np.integer) or np.any(k < 0) or np.any(k > MEMBER_COUNT):
        raise ValueError("CTPI_M2_CALIBRATED_COUNT")
    return mapping[k]


def mixture_probability(posterior: np.ndarray, source_probability: np.ndarray) -> np.ndarray:
    q = _posterior(posterior)
    p = np.asarray(source_probability, dtype=np.float64)
    if p.shape != q.shape or np.any(p <= 0.0) or np.any(p >= 1.0) or not np.isfinite(p).all():
        raise ValueError("CTPI_M2_SOURCE_PROBABILITY")
    return np.sum(q * p, axis=1)


def _loss(probability: np.ndarray, observed: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    p = np.asarray(probability, dtype=np.float64)
    y = np.asarray(observed, dtype=np.float64)
    if p.shape != y.shape or p.ndim != 1 or not np.all((y == 0.0) | (y == 1.0)):
        raise ValueError("CTPI_M2_LOSS_INPUT")
    clipped = np.clip(p, NLL_CLIP, 1.0 - NLL_CLIP)
    nll = -(y * np.log(clipped) + (1.0 - y) * np.log1p(-clipped))
    return nll, (p - y) ** 2


def _ece(probability: np.ndarray, observed: np.ndarray) -> float:
    p = np.asarray(probability, dtype=np.float64)
    y = np.asarray(observed, dtype=np.float64)
    bins = np.minimum((p * 5.0).astype(np.int64), 4)
    total = len(p)
    return float(sum(
        np.count_nonzero(bins == b) / total *
        abs(float(np.mean(p[bins == b])) - float(np.mean(y[bins == b])))
        for b in range(5) if np.any(bins == b)
    ))


def _sign_p(wins: int, losses: int) -> float:
    n = int(wins + losses)
    if n == 0:
        return 1.0
    return float(sum(math.comb(n, k) for k in range(int(wins), n + 1)) / (2 ** n))


def _paired(left: np.ndarray, right: np.ndarray) -> dict[str, Any]:
    wins = int(np.count_nonzero(right < left - PAIR_TOL))
    losses = int(np.count_nonzero(right > left + PAIR_TOL))
    return {"pairs": int(len(left)), "wins": wins, "losses": losses,
            "ties": int(len(left) - wins - losses),
            "one_sided_exact_sign_p": _sign_p(wins, losses),
            "baseline_mean": float(np.mean(left)), "m2_mean": float(np.mean(right))}


def evaluate_confirmatory_gate(
    pre_event_posterior: np.ndarray,
    member_hit_count: np.ndarray,
    observed_event: np.ndarray,
    tape_id: Sequence[str],
    house: Sequence[str],
    table: Sequence[float],
) -> dict[str, Any]:
    """Evaluate the frozen one-shot Gate; no true-source argument exists."""
    posterior = _posterior(pre_event_posterior)
    counts = _counts(member_hit_count, posterior.shape)
    observed = np.asarray(observed_event, dtype=np.float64)
    tapes = np.asarray(tape_id, dtype=str)
    houses = np.asarray(house, dtype=str)
    if observed.shape != (len(posterior),) or tapes.shape != observed.shape or houses.shape != observed.shape:
        raise ValueError("CTPI_M2_CONFIRM_METADATA")
    baseline_source = baseline_source_probability(counts)
    m2_source = calibrated_source_probability(counts, table)
    baseline = mixture_probability(posterior, baseline_source)
    m2 = mixture_probability(posterior, m2_source)
    base_nll, base_brier = _loss(baseline, observed)
    m2_nll, m2_brier = _loss(m2, observed)

    unique_tapes = sorted(set(tapes.tolist()))
    tape_house: list[str] = []
    tape_base_nll: list[float] = []; tape_m2_nll: list[float] = []
    tape_base_brier: list[float] = []; tape_m2_brier: list[float] = []
    for name in unique_tapes:
        mask = tapes == name
        if int(np.count_nonzero(mask)) != 15:
            raise ValueError("CTPI_M2_TAPE_TRANSITION_COUNT")
        hh = sorted(set(houses[mask].tolist()))
        if len(hh) != 1:
            raise ValueError("CTPI_M2_TAPE_HOUSE")
        tape_house.append(hh[0])
        tape_base_nll.append(float(np.mean(base_nll[mask])))
        tape_m2_nll.append(float(np.mean(m2_nll[mask])))
        tape_base_brier.append(float(np.mean(base_brier[mask])))
        tape_m2_brier.append(float(np.mean(m2_brier[mask])))
    bn = np.asarray(tape_base_nll); mn = np.asarray(tape_m2_nll)
    bb = np.asarray(tape_base_brier); mb = np.asarray(tape_m2_brier)
    nll_pair = _paired(bn, mn); brier_pair = _paired(bb, mb)

    by_house: dict[str, Any] = {}
    stable_reverse: list[str] = []
    source_variation_house: dict[str, bool] = {}
    action_variation_house: dict[str, bool] = {}
    house_names = sorted(set(houses.tolist()))
    if house_names != ["H01", "H02", "H03"]:
        raise ValueError("CTPI_M2_CONFIRM_HOUSES")
    for hh in house_names:
        tape_mask = np.asarray([value == hh for value in tape_house], dtype=np.bool_)
        if int(np.count_nonzero(tape_mask)) != 10:
            raise ValueError("CTPI_M2_CONFIRM_TAPES_PER_HOUSE")
        event_mask = houses == hh
        hn = _paired(bn[tape_mask], mn[tape_mask])
        hb = _paired(bb[tape_mask], mb[tape_mask])
        reverse = bool(mn[tape_mask].mean() > bn[tape_mask].mean() and
                       mb[tape_mask].mean() > bb[tape_mask].mean() and
                       hn["losses"] >= 8 and hb["losses"] >= 8)
        if reverse:
            stable_reverse.append(hh)
        source_variation_house[hh] = bool(np.any(np.ptp(m2_source[event_mask], axis=1) > VARIATION_TOL))
        # Visited next-stop contexts act as the action axis.  This does not
        # make a counterfactual task claim; M3 later supplies that separate Gate.
        action_variation_house[hh] = bool(np.any(np.ptp(m2_source[event_mask], axis=0) > VARIATION_TOL))
        by_house[hh] = {"paired_tape_nll": hn, "paired_tape_brier": hb,
                        "stable_reverse_both": reverse,
                        "source_variation": source_variation_house[hh],
                        "visited_action_variation": action_variation_house[hh]}

    mapping = np.asarray(table, dtype=np.float64)
    distinct = 1 + int(np.count_nonzero(np.diff(mapping) > VARIATION_TOL))
    criteria = {
        "pooled_nll_strictly_lower": bool(np.mean(m2_nll) < np.mean(base_nll)),
        "pooled_brier_strictly_lower": bool(np.mean(m2_brier) < np.mean(base_brier)),
        "paired_sign_support": bool(nll_pair["one_sided_exact_sign_p"] <= 0.05 or
                                    brier_pair["one_sided_exact_sign_p"] <= 0.05),
        "ece_not_worse": bool(_ece(m2, observed) <= _ece(baseline, observed) + PAIR_TOL),
        "no_stable_reverse_house": not stable_reverse,
        "finite_interior_probability": bool(np.isfinite(m2_source).all() and
                                             np.all((m2_source > 0.0) & (m2_source < 1.0))),
        "at_least_three_table_values": distinct >= 3,
        "source_variation_every_house": all(source_variation_house.values()),
        "visited_action_variation_every_house": all(action_variation_house.values()),
    }
    passed = all(criteria.values())
    return {
        "contract": "CTPI_M2_CONFIRMATORY_GATE_V1",
        "truth_source_argument_present": False,
        "events": int(len(observed)), "tapes": len(unique_tapes),
        "baseline": {"nll": float(np.mean(base_nll)), "brier": float(np.mean(base_brier)),
                     "ece_5bin": _ece(baseline, observed)},
        "m2": {"nll": float(np.mean(m2_nll)), "brier": float(np.mean(m2_brier)),
               "ece_5bin": _ece(m2, observed)},
        "paired_tape_nll": nll_pair, "paired_tape_brier": brier_pair,
        "by_house": by_house, "stable_reverse_houses": stable_reverse,
        "distinct_table_values": distinct, "criteria": criteria, "pass": passed,
        "verdict": "CTPI_M2_PREDICTIVE_GATE_PASS" if passed else "CTPI_M2_PREDICTIVE_GATE_NO_GO",
    }

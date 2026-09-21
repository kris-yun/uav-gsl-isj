#!/usr/bin/env python3
"""Dependence-calibrated composite source evidence for fixed-trajectory replay.

GCSI V1 treats PMFS per-cell source compatibility as a composite score rather
than an iid likelihood.  It preserves the native best candidate, but calibrates
how strongly alternatives are rejected using paired spatial-block score
differences.

No source truth is used by the scoring functions in this file.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Mapping, Sequence, Tuple


@dataclass(frozen=True)
class BlockCalibration:
    valid: bool
    block_count: int
    mean_difference: float
    block_sd: float
    robust_z: float
    log_relative_weight: float


def native_cell_log_components(alignment, power: float) -> Dict[int, float]:
    """Exact PMFS per-cell log components used by the native replay."""
    out: Dict[int, float] = {}
    for idx, (measured, confidence, simulated) in alignment.items():
        p = 1.0 - confidence * abs(measured - simulated) * power
        if not (p > 0.0 and math.isfinite(p)):
            raise ValueError(f"invalid native cell likelihood {p}")
        out[idx] = math.log(p)
    return out


def physical_block_id(cell, block_size_m: float,
                      origin_x: float, origin_y: float) -> Tuple[int, int]:
    if not (block_size_m > 0.0 and math.isfinite(block_size_m)):
        raise ValueError("block_size_m must be positive and finite")
    return (
        math.floor((cell.x - origin_x) / block_size_m + 1e-12),
        math.floor((cell.y - origin_y) / block_size_m + 1e-12),
    )


def paired_block_differences(
        cells,
        best_components: Mapping[int, float],
        candidate_components: Mapping[int, float],
        block_size_m: float,
        origin_x: float,
        origin_y: float) -> Dict[Tuple[int, int], float]:
    """Mean paired log-score difference per physical block.

    Positive values favor the native best candidate.  Averaging inside a
    physical block prevents the number of computational cells in that block
    from being interpreted as the number of independent observations.
    """
    sums: Dict[Tuple[int, int], float] = {}
    counts: Dict[Tuple[int, int], int] = {}
    for idx in sorted(set(best_components).intersection(candidate_components)):
        if idx not in cells:
            continue
        value = best_components[idx] - candidate_components[idx]
        if not math.isfinite(value):
            continue
        bid = physical_block_id(
            cells[idx], block_size_m, origin_x, origin_y)
        sums[bid] = sums.get(bid, 0.0) + value
        counts[bid] = counts.get(bid, 0) + 1
    return {bid: sums[bid] / counts[bid] for bid in sums}


def sandwich_pair_calibration(
        cells,
        best_components: Mapping[int, float],
        candidate_components: Mapping[int, float],
        block_size_m: float,
        origin_x: float,
        origin_y: float,
        min_blocks: int = 4,
        z_cap: float = 8.0) -> BlockCalibration:
    """Truth-blind scalar Godambe/sandwich proxy for one candidate pair.

    The block means are treated as dependence-reduced paired score units.
    z = mean(block difference) / SE(block difference).

    The native best candidate is never penalized.  An alternative is penalized
    only when the block-level evidence says the best is better.  The Gaussian
    score-test mapping log w = -z^2/2 is deliberately simple and contains no
    fitted source-truth parameter.
    """
    blocks = paired_block_differences(
        cells, best_components, candidate_components,
        block_size_m, origin_x, origin_y)
    values = list(blocks.values())
    n = len(values)
    if n < min_blocks:
        return BlockCalibration(False, n, 0.0, math.inf, 0.0, 0.0)

    mean = sum(values) / n
    var = sum((x - mean) ** 2 for x in values) / max(1, n - 1)
    sd = math.sqrt(max(var, 0.0))

    if sd <= 1e-15:
        z = z_cap if mean > 0.0 else 0.0
    else:
        z = mean / (sd / math.sqrt(n))
        z = max(0.0, min(z_cap, z))

    return BlockCalibration(
        True, n, mean, sd, z, -0.5 * z * z)


def global_block_temperature(cells, block_size_m: float,
                             origin_x: float, origin_y: float) -> float:
    """Simple scalar-temperature control: physical block count / cell count."""
    if not cells:
        return 1.0
    blocks = {
        physical_block_id(c, block_size_m, origin_x, origin_y)
        for c in cells.values()
    }
    return min(1.0, len(blocks) / len(cells))


def calibrated_candidate_scores(
        cells,
        alignments,
        active_candidate_ids: Sequence[str],
        power: float,
        block_size_m: float,
        origin_x: float,
        origin_y: float):
    """Return native, scalar-temperature and GCSI scores.

    The native best candidate is chosen without truth and remains the GCSI MAP
    candidate because its relative GCSI score is fixed at zero and all other
    relative scores are non-positive.
    """
    components = {
        cid: native_cell_log_components(alignments[cid], power)
        for cid in active_candidate_ids
    }
    native = {cid: sum(components[cid].values()) for cid in active_candidate_ids}
    best = max(active_candidate_ids, key=lambda cid: (native[cid], cid))

    temperature = global_block_temperature(
        cells, block_size_m, origin_x, origin_y)
    tempered = {cid: temperature * native[cid] for cid in active_candidate_ids}

    gcsi = {}
    diagnostics = {}
    for cid in active_candidate_ids:
        if cid == best:
            gcsi[cid] = 0.0
            diagnostics[cid] = {
                "is_native_best": True,
                "valid": True,
                "block_count": None,
                "mean_difference": 0.0,
                "block_sd": 0.0,
                "robust_z": 0.0,
                "log_relative_weight": 0.0,
            }
            continue
        cal = sandwich_pair_calibration(
            cells, components[best], components[cid],
            block_size_m, origin_x, origin_y)
        gcsi[cid] = cal.log_relative_weight
        diagnostics[cid] = {
            "is_native_best": False,
            "valid": cal.valid,
            "block_count": cal.block_count,
            "mean_difference": cal.mean_difference,
            "block_sd": cal.block_sd,
            "robust_z": cal.robust_z,
            "log_relative_weight": cal.log_relative_weight,
        }

    return {
        "native_best_candidate": best,
        "native_scores": native,
        "scalar_temperature": temperature,
        "tempered_scores": tempered,
        "gcsi_scores": gcsi,
        "candidate_diagnostics": diagnostics,
    }

#!/usr/bin/env python3
"""Synthetic invariance tests for GCSI V1."""
from __future__ import annotations

from dataclasses import dataclass

from gcsi_composite import (
    global_block_temperature,
    sandwich_pair_calibration,
)


@dataclass(frozen=True)
class Cell:
    x: float
    y: float


def make_cells(subdivide=False):
    cells = {}
    best = {}
    alt = {}
    idx = 0
    # Four physical 1m blocks. Each block has a reproducible paired score gap.
    block_gap = [0.8, 1.0, 1.2, 1.0]
    for bx, gap in enumerate(block_gap):
        if not subdivide:
            cells[idx] = Cell(bx + 0.25, 0.25)
            best[idx] = gap
            alt[idx] = 0.0
            idx += 1
        else:
            # Four subcells inside the same physical block, all carrying the
            # same physical score contribution. The block mean must be unchanged.
            for dx, dy in ((.125,.125),(.625,.125),(.125,.625),(.625,.625)):
                cells[idx] = Cell(bx + dx, dy)
                best[idx] = gap
                alt[idx] = 0.0
                idx += 1
    return cells, best, alt


def main():
    c1, b1, a1 = make_cells(False)
    c4, b4, a4 = make_cells(True)

    z1 = sandwich_pair_calibration(
        c1, b1, a1, 1.0, 0.0, 0.0, min_blocks=4)
    z4 = sandwich_pair_calibration(
        c4, b4, a4, 1.0, 0.0, 0.0, min_blocks=4)

    assert z1.valid and z4.valid
    assert abs(z1.robust_z - z4.robust_z) < 1e-12
    assert abs(z1.log_relative_weight - z4.log_relative_weight) < 1e-12

    # The naive cell count changes 4x, while the physical block temperature
    # changes accordingly rather than treating those cells as independent.
    t1 = global_block_temperature(c1, 1.0, 0.0, 0.0)
    t4 = global_block_temperature(c4, 1.0, 0.0, 0.0)
    assert abs(t1 - 1.0) < 1e-12
    assert abs(t4 - 0.25) < 1e-12

    print("PASS: GCSI physical-block calibration is invariant to uniform subcell refinement")


if __name__ == "__main__":
    main()

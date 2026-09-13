#!/usr/bin/env python3
"""Regression checks for GADEN-compatible coordinate-to-cell conversion."""

from __future__ import annotations

import tempfile
from pathlib import Path

from audit_occupancy_native_parity import CustomOccupancy


def main():
    fixture = """#env_min(m) -1 -1 -1
#env_max(m) 1 1 1
#num_cells 2 2 2
#cell_size(m) 1
0 1
2 0
;
1 0
0 2
;
"""
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "OccupancyGrid3D.csv"
        path.write_text(fixture, encoding="utf-8")
        occupancy = CustomOccupancy(path)
        assert occupancy.query((-1.1, -1.1, -1.1))[1] == (0, 0, 0)
        assert occupancy.query((-2.1, -2.1, -2.1))[1] == (-1, -1, -1)
        assert occupancy.query((-0.5, -0.5, -0.5)) == (0, (0, 0, 0))
        assert occupancy.query((0.5, -0.5, -0.5)) == (2, (1, 0, 0))
    print("DUAL_UAV_OCCUPANCY_INDEXING_SELFTEST_PASS")


if __name__ == "__main__":
    main()

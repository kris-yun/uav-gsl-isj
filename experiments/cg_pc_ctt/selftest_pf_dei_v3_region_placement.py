#!/usr/bin/env python3
from pf_dei_v3_region_placement import select_placement


def main() -> int:
    cells = [
        {"grid_i": 0, "grid_j": 0, "x": 0.0, "y": 0.0, "heights": (0.1, 0.2, 0.3, 0.4)},
        {"grid_i": 0, "grid_j": 1, "x": 0.0, "y": 1.0, "heights": (0.5,)},
    ]
    assert select_placement(cells, 0.01)["pmfs_grid_j"] == 0
    assert select_placement(cells, 0.49)["pmfs_grid_j"] == 0
    assert select_placement(cells, 0.51)["pmfs_grid_j"] == 1
    assert select_placement(cells, 0.99)["pmfs_grid_j"] == 1
    assert select_placement(cells, 1 / 16)["z"] == 0.1
    assert select_placement(cells, 7 / 16)["z"] == 0.4
    assert select_placement(cells, 9 / 16)["z"] == 0.5
    permuted = [cells[1], cells[0]]
    permuted.sort(key=lambda c: (c["grid_i"], c["grid_j"]))
    assert select_placement(permuted, 9 / 16) == select_placement(cells, 9 / 16)
    print("PF_DEI_V3_REGION_PLACEMENT_SELFTEST PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

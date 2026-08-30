#!/usr/bin/env python3
"""Pure tooling regressions for the CTRE historical shadow adapter."""

from ctre_h01_historical_source_update_shadow import carrier_id_for_cell


def main() -> int:
    width, height = 29, 38
    assert carrier_id_for_cell(1 + width, width, height) == "quadtree_0_0_2_2"
    assert carrier_id_for_cell(28 + 26 * width, width, height) == "quadtree_28_26_1_2"
    assert carrier_id_for_cell(28 + 37 * width, width, height) == "quadtree_28_36_1_2"
    assert carrier_id_for_cell(27 + 37 * width, width, height) == "quadtree_26_36_2_2"
    print("CTRE_HISTORICAL_SHADOW_TOOLING_SELFTEST=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

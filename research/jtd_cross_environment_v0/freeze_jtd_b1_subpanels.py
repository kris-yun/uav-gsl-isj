#!/usr/bin/env python3
"""Pre-result, outcome-blind B1 reference-subpanel index lock."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

FOLDS = ((0, 4, 8, 12), (1, 5, 9, 13), (2, 6, 10, 14), (3, 7, 11, 15))
DEPTHS = (3, 4, 6, 8, 10, 12)
CYCLIC_ORDER = (0, 3, 6, 9, 1, 4, 7, 10, 2, 5, 8, 11)
STARTS = (0, 4, 8)


def build() -> dict:
    result = {"contract": "JTD-B1 reference subpanels, replicate-index-only",
              "index_base": 0,
              "fold_targets": [list(fold) for fold in FOLDS],
              "depths": list(DEPTHS),
              "cyclic_master_order_in_sorted_12_references": list(CYCLIC_ORDER),
              "cyclic_starts": list(STARTS),
              "panels": []}
    for fi, targets in enumerate(FOLDS):
        available = [rep for rep in range(16) if rep not in targets]
        assert len(available) == 12
        for depth in DEPTHS:
            count = 1 if depth == 12 else 3
            exposure = {rep: 0 for rep in available}
            for panel in range(count):
                if depth == 12:
                    selected = available.copy()
                else:
                    start = STARTS[panel]
                    selected = sorted(available[CYCLIC_ORDER[(start+i) % 12]] for i in range(depth))
                assert len(selected) == depth and len(set(selected)) == depth
                assert all(rep in available for rep in selected)
                for rep in selected:
                    exposure[rep] += 1
                result["panels"].append({"fold": fi, "depth": depth, "subpanel": panel,
                                          "targets_zero_based": list(targets),
                                          "references_zero_based": selected})
            if depth < 12:
                assert max(exposure.values()) - min(exposure.values()) <= 1
    assert len(result["panels"]) == 4 * (3*5 + 1)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit("refuse overwrite of B1 subpanel lock")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes((json.dumps(build(), indent=2, sort_keys=True) + "\n").encode("utf-8"))
    print(args.out)


if __name__ == "__main__":
    main()

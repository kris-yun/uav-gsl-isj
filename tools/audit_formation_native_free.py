#!/usr/bin/env python3
"""Native GADEN endpoint audit plus parity-qualified corridor audit."""

from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
from pathlib import Path

import numpy as np

from audit_occupancy_native_parity import CustomOccupancy


def read(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--occupancy", type=Path, required=True)
    parser.add_argument("--center", type=Path, required=True)
    parser.add_argument("--plus", type=Path, required=True)
    parser.add_argument("--minus", type=Path, required=True)
    parser.add_argument("--native-helper", type=Path, required=True)
    parser.add_argument("--out-csv", type=Path, required=True)
    parser.add_argument("--out-summary", type=Path, required=True)
    args = parser.parse_args()
    occupancy = CustomOccupancy(args.occupancy)
    groups = {"CENTER": read(args.center), "PLUS": read(args.plus), "MINUS": read(args.minus)}
    points = []
    for group, rows in groups.items():
        for index, row in enumerate(rows):
            points.append((group, index, float(row["x"]), float(row["y"]), float(row["z"])))
    payload = "".join(f"{x:.17g} {y:.17g} {z:.17g}\n" for _, _, x, y, z in points)
    process = subprocess.run([str(args.native_helper), str(args.occupancy)], input=payload, text=True, capture_output=True, check=True)
    output = process.stdout.splitlines()
    if len(output) != len(points):
        raise RuntimeError(f"native outputs {len(output)} != inputs {len(points)}")
    audit_rows = []
    nonfree = []
    for point, line in zip(points, output):
        group, index, x, y, z = point
        tokens = line.split()
        native_state = int(tokens[1])
        native_index = tuple(map(int, tokens[2:5]))
        custom_state, custom_index = occupancy.query((x, y, z))
        audit_rows.append((group, index, x, y, z, native_state, *native_index, custom_state, *custom_index))
        if native_state != 0 or custom_state != native_state or custom_index != native_index:
            nonfree.append(audit_rows[-1])
    plus = groups["PLUS"]
    minus = groups["MINUS"]
    if len(plus) != len(minus):
        raise RuntimeError("plus/minus row count mismatch")
    separation_errors = 0
    corridor_failures = 0
    corridor_failure_details = []
    for pair_index, (first, second) in enumerate(zip(plus, minus)):
        p = np.asarray([float(first["x"]), float(first["y"]), float(first["z"])])
        m = np.asarray([float(second["x"]), float(second["y"]), float(second["z"])])
        distance = float(np.linalg.norm(p - m))
        if abs(distance - 2.0) > 1e-6:
            separation_errors += 1
        count = max(3, int(math.ceil(distance / 0.025)) + 1)
        first_blocked = None
        for sample_index, fraction in enumerate(np.linspace(0.0, 1.0, count)):
            point = m + fraction * (p - m)
            state, cell_index = occupancy.query(point)
            if state != 0:
                first_blocked = {
                    "pair_row": pair_index,
                    "wind_id": first.get("wind_id", ""),
                    "step": int(first.get("step", pair_index + 1)),
                    "baseline_angle_deg": float(first.get("baseline_angle_deg", "nan")),
                    "corridor_sample": sample_index,
                    "fraction": float(fraction),
                    "point_xyz": [float(value) for value in point],
                    "cell_index": list(cell_index),
                    "state": state,
                }
                break
        if first_blocked is not None:
            corridor_failures += 1
            corridor_failure_details.append(first_blocked)
    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.out_csv.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("group", "row", "x", "y", "z", "native_state", "native_ix", "native_iy", "native_iz", "custom_state", "custom_ix", "custom_iy", "custom_iz"))
        writer.writerows(audit_rows)
    summary = {
        "schema": "HOUSE02_DUAL_FORMATION_NATIVE_VALIDATION_V1",
        "native_api": "gaden::Environment::at/coordsToIndices",
        "endpoint_sample_count": len(points),
        "native_or_parity_failures": len(nonfree),
        "plus_minus_pairs": len(plus),
        "separation_errors": separation_errors,
        "corridor_failures": corridor_failures,
        "corridor_failure_details": corridor_failure_details,
        "all_center_endpoint_corridor_checks_pass": not nonfree and not separation_errors and not corridor_failures,
        "status": "PASS" if not nonfree and not separation_errors and not corridor_failures else "FAIL",
    }
    args.out_summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()

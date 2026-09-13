#!/usr/bin/env python3
"""Compare the custom House02 parser with GADEN Environment::at exactly."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np


class CustomOccupancy:
    def __init__(self, path: Path):
        raw = path.read_bytes()
        lines = raw.decode("utf-8").splitlines()
        metadata = {}
        for line in lines[:4]:
            key, *values = line.split()
            metadata[key.split("(")[0]] = values
        self.minimum = np.asarray(list(map(float, metadata["#env_min"])), dtype=np.float32)
        self.maximum = np.asarray(list(map(float, metadata["#env_max"])), dtype=np.float32)
        self.dimensions = tuple(map(int, metadata["#num_cells"]))
        self.cell = np.float32(float(metadata["#cell_size"][0]))
        layers, rows = [], []
        for line in lines[4:]:
            if not line.strip():
                continue
            if line.strip() == ";":
                layers.append(rows)
                rows = []
            else:
                rows.append(list(map(int, line.split())))
        if rows:
            layers.append(rows)
        self.cells = np.asarray(layers, dtype=np.uint8).transpose(0, 2, 1)
        expected = (self.dimensions[2], self.dimensions[1], self.dimensions[0])
        if self.cells.shape != expected:
            raise ValueError(f"unexpected occupancy shape {self.cells.shape}, expected {expected}")
        self.sha256 = hashlib.sha256(raw).hexdigest()

    def query(self, point):
        scaled = (np.asarray(point, dtype=np.float32) - self.minimum) / self.cell
        # Match gaden::Environment::coordsToIndices exactly: glm::ivec3
        # conversion truncates each float component toward zero.
        index = tuple(int(value) for value in scaled)
        if any(value < 0 or value >= limit for value, limit in zip(index, self.dimensions)):
            return 3, index
        x, y, z = index
        return int(self.cells[z, y, x]), index

    def center(self, flat_index: int):
        nx, ny, _ = self.dimensions
        z, remainder = divmod(flat_index, nx * ny)
        y, x = divmod(remainder, nx)
        return tuple(float(value) for value in self.minimum + (np.asarray([x, y, z], dtype=np.float32) + np.float32(0.5)) * self.cell)


def load_route(path: Path, label: str):
    with path.open(newline="", encoding="utf-8") as stream:
        return [(label, index, (float(row["x"]), float(row["y"]), float(row["z"]))) for index, row in enumerate(csv.DictReader(stream))]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--occupancy", type=Path, required=True)
    parser.add_argument("--route-a", type=Path, required=True)
    parser.add_argument("--route-b", type=Path, required=True)
    parser.add_argument("--native-helper", type=Path, required=True)
    parser.add_argument("--out-csv", type=Path, required=True)
    parser.add_argument("--out-summary", type=Path, required=True)
    args = parser.parse_args()

    occupancy = CustomOccupancy(args.occupancy)
    samples = load_route(args.route_a, "T_diag_A") + load_route(args.route_b, "T_diag_B")
    sources = ((0.0, -1.0, 0.2), (-1.64273, -1.30088, 0.2), (1.35727, -0.10088, 0.2), (2.55727, 1.39912, 0.2))
    samples.extend(("SOURCE_COORDINATE", index, point) for index, point in enumerate(sources))
    total_cells = int(np.prod(occupancy.dimensions))
    deterministic = np.linspace(0, total_cells - 1, 1536, dtype=np.int64)
    samples.extend(("DETERMINISTIC_CELL_CENTER", int(flat), occupancy.center(int(flat))) for flat in deterministic)
    boundary = [
        tuple(float(value) for value in occupancy.minimum),
        tuple(float(value) for value in occupancy.maximum),
        tuple(float(value) for value in occupancy.minimum - occupancy.cell),
        tuple(float(value) for value in occupancy.maximum + occupancy.cell),
    ]
    samples.extend(("BOUNDARY_PROBE", index, point) for index, point in enumerate(boundary))

    payload = "".join(f"{point[0]:.17g} {point[1]:.17g} {point[2]:.17g}\n" for _, _, point in samples)
    process = subprocess.run(
        [str(args.native_helper), str(args.occupancy)],
        input=payload,
        text=True,
        capture_output=True,
        check=True,
    )
    native_lines = process.stdout.splitlines()
    if len(native_lines) != len(samples):
        raise RuntimeError(f"native output count {len(native_lines)} != sample count {len(samples)}")

    rows = []
    route_native_blocked = {"T_diag_A": 0, "T_diag_B": 0}
    disagreements = []
    for sample, native_line in zip(samples, native_lines):
        group, sample_id, point = sample
        tokens = native_line.split()
        if len(tokens) != 5 or tokens[0] != "OK":
            raise RuntimeError(f"invalid native response: {native_line}")
        native_state = int(tokens[1])
        native_index = tuple(map(int, tokens[2:5]))
        custom_state, custom_index = occupancy.query(point)
        agreement = native_state == custom_state and native_index == custom_index
        if group in route_native_blocked and native_state != 0:
            route_native_blocked[group] += 1
        if not agreement:
            disagreements.append({"group": group, "sample_id": sample_id, "point": point, "custom_state": custom_state, "native_state": native_state, "custom_index": custom_index, "native_index": native_index})
        rows.append((group, sample_id, *point, custom_state, native_state, int(agreement), *native_index, *custom_index))

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.out_csv.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("sample_group", "sample_id", "x", "y", "z", "python_custom_state", "native_authoritative_state", "agreement", "native_ix", "native_iy", "native_iz", "python_ix", "python_iy", "python_iz"))
        writer.writerows(rows)
    summary = {
        "schema": "HOUSE02_CUSTOM_NATIVE_OCCUPANCY_PARITY_V1",
        "occupancy_sha256": occupancy.sha256,
        "native_api": "gaden::Environment::ReadFromFile/coordsToIndices/at",
        "state_mapping": {"0": "free", "1": "obstacle", "2": "outlet", "3": "out_of_bounds"},
        "sample_count": len(samples),
        "deterministic_cell_center_count": len(deterministic),
        "disagreement_count": len(disagreements),
        "first_disagreements": disagreements[:20],
        "CUSTOM_OCCUPANCY_NATIVE_PARITY": "PASS" if not disagreements else "FAIL",
        "TDIAG_A_NATIVE_BLOCKED_COUNT": route_native_blocked["T_diag_A"],
        "TDIAG_B_NATIVE_BLOCKED_COUNT": route_native_blocked["T_diag_B"],
        "T_DIAG_A_IS_NOT_A_DEPLOYABLE_NAVIGATION_ROUTE": route_native_blocked["T_diag_A"] > 0,
    }
    args.out_summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()

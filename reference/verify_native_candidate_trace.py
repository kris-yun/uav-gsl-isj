#!/usr/bin/env python3
"""Verify shape, offsets and source-blind provenance of an offline PMFS trace."""

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("trace_dir", type=Path)
    parser.add_argument("parity_csv", type=Path)
    parser.add_argument("manifest_json", type=Path)
    args = parser.parse_args()
    trace_dir = args.trace_dir
    with args.parity_csv.open(newline="") as stream:
        parity = list(csv.DictReader(stream))
    assert parity and all(
        row["source_point_exact"] == row["support_exact"] == row["native_score_exact"] == "1"
        for row in parity
    ), "static parity is incomplete"
    ids = {row["candidate_id"] for row in parity}
    assert len(ids) == len(parity), "duplicate parity candidate"

    steps = defaultdict(list)
    with (trace_dir / "step_summary.csv").open(newline="") as stream:
        for row in csv.DictReader(stream):
            assert row["candidate_id"] in ids
            assert row["source_update_id"] == "1"
            assert math.isclose(float(row["t_internal_s"]), int(row["internal_timestep"]) * 0.2, abs_tol=1e-12)
            for field in ("centroid_x", "centroid_y", "cov_xx", "cov_xy", "cov_yy"):
                assert math.isfinite(float(row[field]))
            steps[row["candidate_id"]].append(row)
    assert set(steps) == ids

    occupancy = defaultdict(list)
    with (trace_dir / "occupied_cells.csv").open(newline="") as stream:
        for row in csv.DictReader(stream):
            candidate = row["candidate_id"]
            timestep = int(row["internal_timestep"])
            cell = int(row["cell_index"])
            assert candidate in ids and row["source_update_id"] == "1"
            assert 1 <= timestep <= 200 and 0 <= cell < 29 * 38
            occupancy[candidate].append((timestep, cell))

    total_positions = total_occupied = 0
    for candidate in sorted(ids):
        rows = steps[candidate]
        assert len(rows) == 200
        assert [int(row["internal_timestep"]) for row in rows] == list(range(1, 201))
        position_offset = occupancy_offset = 0
        counts_by_step = defaultdict(int)
        cells_by_step = defaultdict(set)
        for row in rows:
            active = int(row["active_filament_count"])
            occupied = int(row["hit_cell_count"])
            assert active >= 5 and 0 <= occupied <= active
            assert int(row["position_offset_pairs"]) == position_offset
            assert int(row["position_count"]) == active
            assert int(row["occupancy_offset_pairs"]) == occupancy_offset
            position_offset += active
            occupancy_offset += occupied
        for timestep, cell in occupancy[candidate]:
            counts_by_step[timestep] += 1
            cells_by_step[timestep].add(cell)
        assert len(occupancy[candidate]) == occupancy_offset
        for timestep in range(1, 201):
            assert counts_by_step[timestep] == len(cells_by_step[timestep]), "duplicate occupied cell in a step"
            assert counts_by_step[timestep] == int(rows[timestep - 1]["hit_cell_count"])
        assert (trace_dir / f"{candidate}_positions_xy.f32").stat().st_size == position_offset * 8
        assert (trace_dir / f"{candidate}_transitions.i32").stat().st_size == position_offset * 8
        total_positions += position_offset
        total_occupied += occupancy_offset

    files = sorted(path for path in trace_dir.iterdir() if path.is_file())
    assert len(files) == len(ids) * 2 + 3
    payload = {
        "contract": "STANDALONE_NATIVE_CANDIDATE_TRACE_VERIFIED_V1",
        "candidate_count": len(ids),
        "step_count": len(ids) * 200,
        "filament_position_count": total_positions,
        "unique_occupied_cell_events": total_occupied,
        "parity_csv_sha256": sha256(args.parity_csv),
        "files": {path.name: {"size_bytes": path.stat().st_size, "sha256": sha256(path)} for path in files},
    }
    args.manifest_json.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"TRACE_INTEGRITY_PASS candidates={len(ids)} steps={len(ids) * 200} "
          f"positions={total_positions} occupied={total_occupied}")


if __name__ == "__main__":
    main()

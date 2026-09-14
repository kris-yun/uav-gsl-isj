#!/usr/bin/env python3
"""Independent lineage and FOPDT audit of observability design traces."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
from collections import deque
from pathlib import Path


SOURCES = ("S_truth", "S_k01", "S_k10", "S_k22")
WINDS = ("W_fast", "W_slow")
DT = 0.2


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path, compressed=False):
    opener = gzip.open if compressed else open
    with opener(path, "rt" if compressed else "r", newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


class IndependentFOPDT:
    def __init__(self):
        self.t, self.state = 0.0, 0.0
        self.history = deque([(0.0, 0.0)])

    def process(self, value):
        self.t += DT
        self.history.append((self.t, value))
        query_t = self.t - 0.4
        if query_t <= 0.0:
            delayed = 0.0
        else:
            delayed = self.history[-1][1]
            previous_t, previous_value = self.history[0]
            for next_t, next_value in list(self.history)[1:]:
                if query_t <= next_t:
                    width = next_t - previous_t
                    delayed = next_value if width <= 0 else previous_value + (query_t - previous_t) / width * (next_value - previous_value)
                    break
                previous_t, previous_value = next_t, next_value
        alpha = math.exp(-DT / 1.2)
        self.state = alpha * self.state + (1.0 - alpha) * delayed
        return self.state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--trace-dir", type=Path, required=True)
    parser.add_argument("--query-summary", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    query_summary = json.loads(args.query_summary.read_text(encoding="utf-8"))
    expected_hashes = {(item["route_id"], item["source"], item["wind"]): item["sha256"] for item in query_summary["manifest"]}
    errors, traces = [], []
    max_coordinate_error = 0.0
    max_fopdt_error = 0.0
    for route_path in sorted(args.candidate_root.glob("AO_*/CENTER.csv")):
        route_id = route_path.parent.name
        route = read_csv(route_path)
        for source in SOURCES:
            for wind in WINDS:
                path = args.trace_dir / f"{route_id}__{source}__{wind}.csv.gz"
                rows = read_csv(path, compressed=True)
                sensor = IndependentFOPDT()
                for index, (row, sample) in enumerate(zip(rows, route)):
                    expected_time = index * DT
                    expected_frame = int(math.floor(expected_time / 0.5))
                    if (row["route_id"], row["source_id"], row["wind_id"]) != (route_id, source, wind):
                        errors.append(f"identity:{route_id}:{source}:{wind}:{index}")
                    if int(row["step"]) != index + 1 or int(row["plume_frame_iteration"]) != expected_frame:
                        errors.append(f"time_frame:{route_id}:{source}:{wind}:{index}")
                    for key in ("x", "y", "z"):
                        max_coordinate_error = max(max_coordinate_error, abs(float(row[key]) - float(sample[key])))
                    reproduced = sensor.process(float(row["raw_gas_concentration_ppm"]))
                    max_fopdt_error = max(max_fopdt_error, abs(reproduced - float(row["processed_sensor_output_ppm"])))
                digest = sha256_file(path)
                if len(rows) != 750 or digest != expected_hashes.get((route_id, source, wind)):
                    errors.append(f"cardinality_or_hash:{route_id}:{source}:{wind}")
                traces.append({"route_id": route_id, "source": source, "wind": wind, "rows": len(rows), "sha256": digest})
    unexpected_held = sorted(args.trace_dir.glob("*W_altfast*"))
    result = {
        "schema": "OBSERVABILITY_DESIGN_TRACE_INTEGRITY_AUDIT_V1",
        "trace_count": len(traces), "row_count": sum(item["rows"] for item in traces),
        "maximum_route_coordinate_error": max_coordinate_error,
        "maximum_independent_fopdt_error": max_fopdt_error,
        "held_wind_file_count": len(unexpected_held), "held_wind_read": False,
        "error_count": len(errors), "first_errors": errors[:20], "traces": traces,
        "status": "PASS" if len(traces) == 96 and sum(item["rows"] for item in traces) == 72000 and not errors and not unexpected_held and max_coordinate_error <= 1e-12 and max_fopdt_error <= 1e-12 else "FAIL",
    }
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("trace_count", "row_count", "held_wind_file_count", "error_count", "maximum_independent_fopdt_error", "status")}))


if __name__ == "__main__":
    main()

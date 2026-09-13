#!/usr/bin/env python3
"""Independent same-frame, route-lineage, and FOPDT audit for dual traces."""

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
WINDS = ("W_fast", "W_slow", "W_altfast")
DT = 0.2
FRAME_DT = 0.5


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
        self.t = 0.0
        self.state = 0.0
        self.history = deque([(0.0, 0.0)])

    def process(self, value):
        self.t += DT
        self.history.append((self.t, value))
        query_t = self.t - 0.4
        if query_t <= 0.0:
            delayed = 0.0
        elif query_t >= self.history[-1][0]:
            delayed = self.history[-1][1]
        else:
            delayed = self.history[-1][1]
            previous_t, previous_v = self.history[0]
            for next_t, next_v in list(self.history)[1:]:
                if query_t <= next_t:
                    width = next_t - previous_t
                    delayed = next_v if width <= 0 else previous_v + (query_t - previous_t) / width * (next_v - previous_v)
                    break
                previous_t, previous_v = next_t, next_v
        alpha = math.exp(-DT / 1.2)
        self.state = alpha * self.state + (1.0 - alpha) * delayed
        return self.state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plus-route", type=Path, required=True)
    parser.add_argument("--minus-route", type=Path, required=True)
    parser.add_argument("--trace-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    plus_all = read_csv(args.plus_route)
    minus_all = read_csv(args.minus_route)
    errors = []
    trace_audits = []
    maximum_fopdt_error = 0.0
    maximum_route_coordinate_error = 0.0
    for source in SOURCES:
        for wind in WINDS:
            plus = [row for row in plus_all if row["wind_id"] == wind]
            minus = [row for row in minus_all if row["wind_id"] == wind]
            path = args.trace_dir / f"{source}__{wind}.csv.gz"
            rows = read_csv(path, compressed=True)
            sensors = (IndependentFOPDT(), IndependentFOPDT())
            for index, (row, expected_plus, expected_minus) in enumerate(zip(rows, plus, minus)):
                expected_time = index * DT
                expected_frame = int(math.floor(expected_time / FRAME_DT))
                if row["source_id"] != source or row["wind_id"] != wind:
                    errors.append(f"identity:{source}:{wind}:{index}")
                if int(row["step"]) != index + 1 or abs(float(row["route_time_s"]) - expected_time) > 1e-9:
                    errors.append(f"time:{source}:{wind}:{index}")
                if int(row["plume_frame_iteration"]) != expected_frame or int(row["same_frame"]) != 1:
                    errors.append(f"frame:{source}:{wind}:{index}")
                for observed_key, expected_row, expected_key in (
                    ("x_plus", expected_plus, "x"), ("y_plus", expected_plus, "y"), ("z_plus_position", expected_plus, "z"),
                    ("x_minus", expected_minus, "x"), ("y_minus", expected_minus, "y"), ("z_minus_position", expected_minus, "z"),
                ):
                    maximum_route_coordinate_error = max(maximum_route_coordinate_error, abs(float(row[observed_key]) - float(expected_row[expected_key])))
                reproduced_plus = sensors[0].process(float(row["raw_c_plus_ppm"]))
                reproduced_minus = sensors[1].process(float(row["raw_c_minus_ppm"]))
                maximum_fopdt_error = max(
                    maximum_fopdt_error,
                    abs(reproduced_plus - float(row["processed_z_plus_ppm"])),
                    abs(reproduced_minus - float(row["processed_z_minus_ppm"])),
                )
                if int(row["endpoint_geometry_valid"]) != 1:
                    errors.append(f"geometry:{source}:{wind}:{index}")
            if len(rows) != 750 or len(plus) != 750 or len(minus) != 750:
                errors.append(f"cardinality:{source}:{wind}:{len(rows)}:{len(plus)}:{len(minus)}")
            trace_audits.append({"source": source, "wind": wind, "rows": len(rows), "sha256": sha256_file(path)})
    summary = {
        "schema": "DUAL_UAV_SYNCHRONIZED_TRACE_INDEPENDENT_AUDIT_V1",
        "plus_route_sha256": sha256_file(args.plus_route),
        "minus_route_sha256": sha256_file(args.minus_route),
        "expected_traces": 12, "actual_traces": len(trace_audits),
        "expected_rows": 9000, "actual_rows": sum(item["rows"] for item in trace_audits),
        "maximum_route_coordinate_error": maximum_route_coordinate_error,
        "maximum_independent_fopdt_error": maximum_fopdt_error,
        "error_count": len(errors), "first_errors": errors[:20], "traces": trace_audits,
        "status": "PASS" if len(trace_audits) == 12 and sum(item["rows"] for item in trace_audits) == 9000 and not errors and maximum_route_coordinate_error <= 1e-12 and maximum_fopdt_error <= 1e-12 else "FAIL",
    }
    args.out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()

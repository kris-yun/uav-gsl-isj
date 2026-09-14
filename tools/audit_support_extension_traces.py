#!/usr/bin/env python3
"""Independent integrity audit for the frozen extended endpoint traces."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
from collections import deque
from pathlib import Path

from audit_occupancy_native_parity import CustomOccupancy


SOURCES = ("S_truth", "S_k01", "S_k10", "S_k22")
WINDS = ("W_fast", "W_slow")
DT = 0.2
FRAME_DT = 0.5
N = 1115


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read(path: Path):
    with gzip.open(path, "rt", newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


class FOPDT:
    def __init__(self):
        self.t, self.state = 0.0, 0.0
        self.history = deque([(0.0, 0.0)])

    def process(self, value):
        self.t += DT
        self.history.append((self.t, float(value)))
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--candidate-manifest", type=Path, required=True)
    parser.add_argument("--endpoint-trace-dir", type=Path, required=True)
    parser.add_argument("--endpoint-query-summary", type=Path, required=True)
    parser.add_argument("--occupancy", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.candidate_manifest.read_text(encoding="utf-8"))
    summary = json.loads(args.endpoint_query_summary.read_text(encoding="utf-8"))
    occupancy = CustomOccupancy(args.occupancy)
    expected_hashes = {(item["route_id"], item["source"], item["wind"]): item["sha256"] for item in summary["manifest"]}
    errors = []
    max_midpoint = 0.0
    max_separation = 0.0
    max_coordinate = 0.0
    max_fopdt = 0.0
    endpoint_count = 0
    route_ids = [item["route_id"] for item in manifest["candidates"]]
    for route_id in route_ids:
        route_dir = args.candidate_root / route_id
        center = list(csv.DictReader((route_dir / "CENTER.csv").open(newline="", encoding="utf-8")))
        if len(center) != N:
            errors.append(f"center_rows:{route_id}:{len(center)}")
        for wind in WINDS:
            plus = [row for row in csv.DictReader((route_dir / "PLUS.csv").open(newline="", encoding="utf-8")) if row["wind_id"] == wind]
            minus = [row for row in csv.DictReader((route_dir / "MINUS.csv").open(newline="", encoding="utf-8")) if row["wind_id"] == wind]
            if len(plus) != N or len(minus) != N:
                errors.append(f"endpoint_route_rows:{route_id}:{wind}")
            for index, (c, p, m) in enumerate(zip(center, plus, minus)):
                cx, cy, cz = (float(c[key]) for key in ("x", "y", "z"))
                px, py, pz = (float(p[key]) for key in ("x", "y", "z"))
                mx, my, mz = (float(m[key]) for key in ("x", "y", "z"))
                max_midpoint = max(max_midpoint, abs((px + mx) / 2 - cx), abs((py + my) / 2 - cy), abs((pz + mz) / 2 - cz))
                max_separation = max(max_separation, abs(math.dist((px, py, pz), (mx, my, mz)) - 2.0))
                if occupancy.query((cx, cy, cz))[0] != 0 or occupancy.query((px, py, pz))[0] != 0 or occupancy.query((mx, my, mz))[0] != 0:
                    errors.append(f"occupied_route_point:{route_id}:{wind}:{index}")
                if int(p["step"]) != index + 1 or int(m["step"]) != index + 1 or p["t_sim_s"] != m["t_sim_s"]:
                    errors.append(f"route_timing:{route_id}:{wind}:{index}")

            path = args.endpoint_trace_dir / f"{route_id}__S_truth__{wind}.csv.gz"
            # Trace checks are performed below for all source IDs; this path only avoids a silent empty route.
            if not path.is_file():
                errors.append(f"missing_trace:{path.name}")

        for source in SOURCES:
            for wind in WINDS:
                key = (route_id, source, wind)
                path = args.endpoint_trace_dir / f"{route_id}__{source}__{wind}.csv.gz"
                if not path.is_file():
                    errors.append(f"missing_trace:{path.name}")
                    continue
                rows = read(path)
                endpoint_count += 1
                if len(rows) != N or sha256_file(path) != expected_hashes.get(key):
                    errors.append(f"trace_rows_or_hash:{path.name}")
                sensor_plus, sensor_minus = FOPDT(), FOPDT()
                plus_route = [row for row in csv.DictReader((args.candidate_root / route_id / "PLUS.csv").open(newline="", encoding="utf-8")) if row["wind_id"] == wind]
                minus_route = [row for row in csv.DictReader((args.candidate_root / route_id / "MINUS.csv").open(newline="", encoding="utf-8")) if row["wind_id"] == wind]
                for index, (row, p, m) in enumerate(zip(rows, plus_route, minus_route)):
                    expected_frame = int(math.floor(index * DT / FRAME_DT))
                    if int(row["step"]) != index + 1 or int(row["plume_frame_iteration"]) != expected_frame:
                        errors.append(f"trace_timing:{path.name}:{index}")
                    for trace_key, route_key in (("x_plus", "x"), ("y_plus", "y"), ("z_plus", "z")):
                        max_coordinate = max(max_coordinate, abs(float(row[trace_key]) - float(p[route_key])))
                    for trace_key, route_key in (("x_minus", "x"), ("y_minus", "y"), ("z_minus", "z")):
                        max_coordinate = max(max_coordinate, abs(float(row[trace_key]) - float(m[route_key])))
                    max_fopdt = max(max_fopdt, abs(sensor_plus.process(float(row["raw_c_plus_ppm"])) - float(row["processed_c_plus_ppm"])), abs(sensor_minus.process(float(row["raw_c_minus_ppm"])) - float(row["processed_c_minus_ppm"])))

    actual_names = {path.name for path in args.endpoint_trace_dir.glob("*.csv.gz")}
    expected_names = {f"{route}__{source}__{wind}.csv.gz" for route in route_ids for source in SOURCES for wind in WINDS}
    unexpected = sorted(actual_names - expected_names)
    if unexpected:
        errors.append("unexpected_trace_names")
    result = {
        "schema": "SUPPORT_EXTENSION_TRACE_INTEGRITY_AUDIT_V1",
        "candidate_count": len(route_ids),
        "endpoint_trace_count": endpoint_count,
        "rows_per_trace": N,
        "total_endpoint_rows": endpoint_count * N,
        "query_summary_status": summary.get("status"),
        "forbidden_wind_queried": summary.get("forbidden_wind_queried"),
        "raw_cache_only": summary.get("raw_cache_only"),
        "new_gaden_dataset_generated": summary.get("new_gaden_dataset_generated"),
        "maximum_candidate_midpoint_coordinate_error": max_midpoint,
        "maximum_candidate_separation_error_m": max_separation,
        "maximum_trace_coordinate_error": max_coordinate,
        "maximum_independent_fopdt_error": max_fopdt,
        "unexpected_trace_names": unexpected,
        "held_wind_response_read": False,
        "error_count": len(errors),
        "first_errors": errors[:20],
    }
    result["status"] = "PASS" if (
        endpoint_count == 96 and endpoint_count * N == 107040 and summary.get("status") == "PASS" and
        summary.get("forbidden_wind_queried") is False and summary.get("raw_cache_only") is True and
        summary.get("new_gaden_dataset_generated") is False and not unexpected and not errors and
        max_midpoint <= 1e-12 and max_separation <= 1e-6 and max_coordinate <= 1e-12 and max_fopdt <= 1e-12
    ) else "FAIL"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("endpoint_trace_count", "total_endpoint_rows", "error_count", "status")}))


if __name__ == "__main__":
    main()

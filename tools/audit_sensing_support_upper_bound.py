#!/usr/bin/env python3
"""Independent route-lineage, coordinate, trace, and FOPDT audit for C0--C3."""

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
EXPECTED_SAMPLES = 750


def sha256_file(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path, compressed=False):
    opener = gzip.open if compressed else open
    mode = "rt" if compressed else "r"
    with opener(path, mode, newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


class IndependentFOPDT:
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--candidate-manifest", type=Path, required=True)
    parser.add_argument("--native-audit", type=Path, required=True)
    parser.add_argument("--center-trace-dir", type=Path, required=True)
    parser.add_argument("--center-query-summary", type=Path, required=True)
    parser.add_argument("--endpoint-trace-dir", type=Path, required=True)
    parser.add_argument("--endpoint-query-summary", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.candidate_manifest.read_text(encoding="utf-8"))
    native = json.loads(args.native_audit.read_text(encoding="utf-8"))
    center_summary = json.loads(args.center_query_summary.read_text(encoding="utf-8"))
    endpoint_summary = json.loads(args.endpoint_query_summary.read_text(encoding="utf-8"))
    center_hashes = {(x["route_id"], x["source"], x["wind"]): x["sha256"] for x in center_summary["manifest"]}
    endpoint_hashes = {(x["route_id"], x["source"], x["wind"]): x["sha256"] for x in endpoint_summary["manifest"]}

    errors = []
    candidate_hash_failures = 0
    maximum_midpoint_error = 0.0
    maximum_separation_error = 0.0
    maximum_center_trace_coordinate_error = 0.0
    maximum_endpoint_trace_coordinate_error = 0.0
    maximum_center_fopdt_error = 0.0
    maximum_endpoint_fopdt_error = 0.0
    trace_records = []

    candidate_by_id = {item["route_id"]: item for item in manifest["candidates"]}
    for route_id in sorted(candidate_by_id):
        item = candidate_by_id[route_id]
        route_dir = args.candidate_root / route_id
        for filename, hash_key in (("CENTER.csv", "center_sha256"), ("PLUS.csv", "plus_sha256"), ("MINUS.csv", "minus_sha256")):
            actual = sha256_file(route_dir / filename)
            if actual != item[hash_key]:
                candidate_hash_failures += 1
                errors.append(f"candidate_hash:{route_id}:{filename}")
        center = read_csv(route_dir / "CENTER.csv")
        for wind in WINDS:
            plus = [row for row in read_csv(route_dir / "PLUS.csv") if row["wind_id"] == wind]
            minus = [row for row in read_csv(route_dir / "MINUS.csv") if row["wind_id"] == wind]
            if len(center) != EXPECTED_SAMPLES or len(plus) != EXPECTED_SAMPLES or len(minus) != EXPECTED_SAMPLES:
                errors.append(f"candidate_cardinality:{route_id}:{wind}")
                continue
            for index, (c_row, p_row, m_row) in enumerate(zip(center, plus, minus)):
                c = [float(c_row[key]) for key in ("x", "y", "z")]
                p = [float(p_row[key]) for key in ("x", "y", "z")]
                m = [float(m_row[key]) for key in ("x", "y", "z")]
                midpoint = [(p[axis] + m[axis]) / 2.0 for axis in range(3)]
                maximum_midpoint_error = max(maximum_midpoint_error, *(abs(midpoint[axis] - c[axis]) for axis in range(3)))
                separation = math.sqrt(sum((p[axis] - m[axis]) ** 2 for axis in range(3)))
                maximum_separation_error = max(maximum_separation_error, abs(separation - 2.0))
                if p_row["step"] != m_row["step"] or int(p_row["step"]) != index + 1:
                    errors.append(f"candidate_pair_timing:{route_id}:{wind}:{index}")

        for source in SOURCES:
            for wind in WINDS:
                key = (route_id, source, wind)
                center_path = args.center_trace_dir / f"{route_id}__{source}__{wind}.csv.gz"
                endpoint_path = args.endpoint_trace_dir / f"{route_id}__{source}__{wind}.csv.gz"
                center_rows = read_csv(center_path, compressed=True)
                endpoint_rows = read_csv(endpoint_path, compressed=True)
                if len(center_rows) != EXPECTED_SAMPLES or sha256_file(center_path) != center_hashes.get(key):
                    errors.append(f"center_trace_hash_or_rows:{route_id}:{source}:{wind}")
                if len(endpoint_rows) != EXPECTED_SAMPLES or sha256_file(endpoint_path) != endpoint_hashes.get(key):
                    errors.append(f"endpoint_trace_hash_or_rows:{route_id}:{source}:{wind}")
                sensor_center, sensor_plus, sensor_minus = IndependentFOPDT(), IndependentFOPDT(), IndependentFOPDT()
                center_route = read_csv(args.candidate_root / route_id / "CENTER.csv")
                plus_route = [row for row in read_csv(args.candidate_root / route_id / "PLUS.csv") if row["wind_id"] == wind]
                minus_route = [row for row in read_csv(args.candidate_root / route_id / "MINUS.csv") if row["wind_id"] == wind]
                for index, (c_trace, e_trace, c_route, p_route, m_route) in enumerate(zip(center_rows, endpoint_rows, center_route, plus_route, minus_route)):
                    expected_frame = int(math.floor(index * DT / 0.5))
                    if int(c_trace["step"]) != index + 1 or int(e_trace["step"]) != index + 1 or int(c_trace["plume_frame_iteration"]) != expected_frame or int(e_trace["plume_frame_iteration"]) != expected_frame:
                        errors.append(f"trace_timing:{route_id}:{source}:{wind}:{index}")
                    for axis in ("x", "y", "z"):
                        maximum_center_trace_coordinate_error = max(maximum_center_trace_coordinate_error, abs(float(c_trace[axis]) - float(c_route[axis])))
                    for trace_key, route_key in (("x_plus", "x"), ("y_plus", "y"), ("z_plus", "z")):
                        maximum_endpoint_trace_coordinate_error = max(maximum_endpoint_trace_coordinate_error, abs(float(e_trace[trace_key]) - float(p_route[route_key])))
                    for trace_key, route_key in (("x_minus", "x"), ("y_minus", "y"), ("z_minus", "z")):
                        maximum_endpoint_trace_coordinate_error = max(maximum_endpoint_trace_coordinate_error, abs(float(e_trace[trace_key]) - float(m_route[route_key])))
                    reproduced_center = sensor_center.process(float(c_trace["raw_gas_concentration_ppm"]))
                    reproduced_plus = sensor_plus.process(float(e_trace["raw_c_plus_ppm"]))
                    reproduced_minus = sensor_minus.process(float(e_trace["raw_c_minus_ppm"]))
                    maximum_center_fopdt_error = max(maximum_center_fopdt_error, abs(reproduced_center - float(c_trace["processed_sensor_output_ppm"])))
                    maximum_endpoint_fopdt_error = max(
                        maximum_endpoint_fopdt_error,
                        abs(reproduced_plus - float(e_trace["processed_c_plus_ppm"])),
                        abs(reproduced_minus - float(e_trace["processed_c_minus_ppm"])),
                    )
                trace_records.append({
                    "route_id": route_id, "source": source, "wind": wind,
                    "center_sha256": sha256_file(center_path), "endpoint_sha256": sha256_file(endpoint_path),
                    "rows": len(endpoint_rows),
                })

    expected_trace_names = {
        f"{route_id}__{source}__{wind}.csv.gz"
        for route_id in candidate_by_id for source in SOURCES for wind in WINDS
    }
    actual_endpoint_names = {path.name for path in args.endpoint_trace_dir.glob("*.csv.gz")}
    unexpected_trace_names = sorted(actual_endpoint_names - expected_trace_names)
    if unexpected_trace_names:
        errors.append("unexpected_endpoint_trace_names")

    result = {
        "schema": "SENSING_SUPPORT_TRACE_INTEGRITY_AUDIT_V1",
        "candidate_count": len(candidate_by_id),
        "candidate_hash_failures": candidate_hash_failures,
        "maximum_candidate_midpoint_coordinate_error": maximum_midpoint_error,
        "maximum_candidate_separation_error_m": maximum_separation_error,
        "native_geometry_verification": {
            "mode": "HASH_BOUND_REUSE_OF_PRE_RESPONSE_NATIVE_GADEN_AUDIT_PLUS_INDEPENDENT_COORDINATE_RECOMPUTATION",
            "native_api": native["candidates"][0]["native_api"],
            "native_audit_sha256": sha256_file(args.native_audit),
            "total_endpoint_samples": native["total_endpoint_samples"],
            "total_pairs": native["total_pairs"],
            "native_or_parity_failures": sum(item["native_or_parity_failures"] for item in native["candidates"]),
            "separation_errors": sum(item["separation_errors"] for item in native["candidates"]),
            "corridor_failures": sum(item["corridor_failures"] for item in native["candidates"]),
            "all_pass": native["all_pass"],
        },
        "query_path_verification": {
            "center_query_status": center_summary["status"],
            "endpoint_query_status": endpoint_summary["status"],
            "raw_cache_only": endpoint_summary["raw_cache_only"],
            "new_gaden": endpoint_summary["new_gaden_dataset_generated"],
            "non_design_wind_queried": endpoint_summary["non_design_wind_queried"],
        },
        "center_trace_count": len(trace_records),
        "endpoint_trace_count": len(trace_records),
        "rows_per_trace": EXPECTED_SAMPLES,
        "total_endpoint_rows": sum(item["rows"] for item in trace_records),
        "maximum_center_trace_coordinate_error": maximum_center_trace_coordinate_error,
        "maximum_endpoint_trace_coordinate_error": maximum_endpoint_trace_coordinate_error,
        "maximum_independent_center_fopdt_error": maximum_center_fopdt_error,
        "maximum_independent_endpoint_fopdt_error": maximum_endpoint_fopdt_error,
        "unexpected_endpoint_trace_names": unexpected_trace_names,
        "held_wind_response_read": False,
        "error_count": len(errors),
        "first_errors": errors[:20],
        "traces": trace_records,
    }
    result["status"] = "PASS" if (
        len(trace_records) == 96
        and result["total_endpoint_rows"] == 72000
        and not errors
        and native["all_pass"]
        and maximum_midpoint_error <= 1e-12
        and maximum_separation_error <= 1e-6
        and maximum_center_trace_coordinate_error <= 1e-12
        and maximum_endpoint_trace_coordinate_error <= 1e-12
        and maximum_center_fopdt_error <= 1e-12
        and maximum_endpoint_fopdt_error <= 1e-12
    ) else "FAIL"
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "candidate_hash_failures", "center_trace_count", "endpoint_trace_count", "total_endpoint_rows",
        "maximum_independent_endpoint_fopdt_error", "error_count", "status",
    )}))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Fail-closed G0 audit for the frozen H01 wind-conditioned native bank."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from ctt_h01_wind_bank_io import first_passage, read_physical, read_wind, sensor_forward, sha256_file


EXPECTED_STOPS = (10, 10, 10, 9, 10)
EXPECTED_LENGTHS = (1682, 1682, 1682, 1682, 1682)
AUTHORITATIVE_SENSOR_SHA256 = "423042f94315a35ca83aa929d42a32633d94ea819b8e15639e26039073c549bc"


def read_schedule(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as source:
        return [{"moving": int(row["is_moving"]), "stop": int(row["stop_id"])}
                for row in csv.DictReader(source)]


def stop_indices(schedule: list[dict]) -> list[np.ndarray]:
    result = []
    for stop in sorted({row["stop"] for row in schedule}):
        indices = np.asarray([index for index, row in enumerate(schedule)
                              if row["stop"] == stop and row["moving"] == 0], dtype=np.int64)
        if len(indices) >= 80:
            result.append(indices[:80])
    return result


def exact_sensor_parity(authoritative: Path, streams: list[np.ndarray]) -> tuple[float, bool]:
    if sha256_file(authoritative) != AUTHORITATIVE_SENSOR_SHA256:
        raise ValueError("CTT_H01_AUTHORITATIVE_SENSOR_HASH_FAIL")
    spec = importlib.util.spec_from_file_location("ctt_authoritative_sensor", authoritative)
    if not spec or not spec.loader:
        raise ValueError("CTT_H01_AUTHORITATIVE_SENSOR_IMPORT_FAIL")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    config = {
        "gain": 1.0, "baseline": 0.0, "tau_rise_s": 1.2,
        "tau_recovery_s": 1.2, "dead_time_s": 0.4,
        "noise_std_ppm": 0.0, "drift_rate_ppm_s": 0.0,
        "saturation_min_ppm": 0.0, "saturation_max_ppm": 1.0e6,
        "initial_state_ppm": 0.0, "initial_input_ppm": 0.0,
    }
    maximum = 0.0
    exact = True
    for stream in streams:
        reference = module.SensorModel(mode="dynamic", seed=20260828, **config)
        expected = np.asarray([reference.process(float(value), 0.2) for value in stream])
        actual = sensor_forward(stream)
        maximum = max(maximum, float(np.max(np.abs(actual - expected))))
        exact &= np.array_equal(actual, expected)
    return maximum, exact


def relative_hashes(root: Path) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): sha256_file(path)
            for path in root.glob("context_*/member_*/*.bin")}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bank", type=Path, required=True)
    parser.add_argument("--placement-manifest", type=Path, required=True)
    parser.add_argument("--carrier-manifest", type=Path, required=True)
    parser.add_argument("--context-manifest", type=Path, required=True)
    parser.add_argument("--schedule-root", type=Path, required=True)
    parser.add_argument("--smoke-a", type=Path, required=True)
    parser.add_argument("--smoke-b", type=Path, required=True)
    parser.add_argument("--release-smoke", type=Path, required=True)
    parser.add_argument("--pre-vcpu-reference", type=Path, required=True)
    parser.add_argument("--authoritative-sensor", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"CTT_H01_G0_REFUSE_OVERWRITE:{args.output}")

    summary = json.loads((args.bank / "bank_summary.json").read_text(encoding="utf-8"))
    if summary.get("verdict") != "CTT_H01_WIND_BANK_MATERIALIZATION_PASS":
        raise SystemExit("CTT_H01_G0_BANK_NOT_COMPLETE")
    args.output.mkdir(parents=True)

    placement = json.loads(args.placement_manifest.read_text(encoding="utf-8"))
    placement_rows = [row for row in placement["rows"]
                      if row["house"] == "H01" and row["split"] == "train"]
    placement_ids = {row["carrier_id"] for row in placement_rows}
    placement_members = {int(row["member_id"]) for row in placement_rows}
    with args.carrier_manifest.open(newline="", encoding="utf-8") as source:
        carriers = list(csv.DictReader(source))
    carrier_ids = {row["carrier_id"] for row in carriers}
    carrier_coordinates = {(float(row["x"]), float(row["y"])) for row in carriers}
    carrier_gate = (
        len(placement_rows) == 1680 and len(placement_ids) == 210 and
        placement_members == set(range(8)) and len(carriers) == 210 and
        carrier_ids == placement_ids and len(carrier_coordinates) == 210 and
        [int(row["carrier_index"]) for row in carriers] == list(range(210))
    )

    contexts = json.loads(args.context_manifest.read_text(encoding="utf-8"))["contexts"]
    context_gate = True
    for item in contexts:
        source_hash = sha256_file(item["original_path"])
        context_gate &= source_hash == item["payload_sha256"]
        for slot in range(11):
            context_gate &= sha256_file(Path(item["wind_dir"]) / f"wind_iteration_{slot}") == source_hash

    schedules = [args.schedule_root / "H01" / "reserved" / f"trajectory_seed_{seed}.csv"
                 for seed in range(4001, 4006)]
    schedule_rows = [read_schedule(path) for path in schedules]
    schedule_stops = [stop_indices(rows) for rows in schedule_rows]
    schedule_gate = [len(items) for items in schedule_stops] == list(EXPECTED_STOPS)
    for rows, groups in zip(schedule_rows, schedule_stops):
        for indices in groups:
            schedule_gate &= len(indices) == 80 and len(set(indices.tolist())) == 80
            schedule_gate &= bool(np.all(np.diff(indices) > 0))
            schedule_gate &= all(rows[index]["moving"] == 0 for index in indices)

    coverage_rows = []
    all_streams_valid = True
    for context in range(10):
        wind_streams = read_wind(args.bank / f"context_{context:02d}" / "exact_wind_routes.bin")
        all_streams_valid &= tuple(len(values) for values in wind_streams) == EXPECTED_LENGTHS
        for member in range(8):
            directory = args.bank / f"context_{context:02d}" / f"member_{member:02d}"
            files = sorted(directory.glob("*.bin"))
            ids = {path.stem for path in files}
            valid = len(files) == 210 and ids == carrier_ids
            byte_count = 0
            for path in files:
                streams = read_physical(path)
                byte_count += path.stat().st_size
                valid &= tuple(len(values) for values in streams) == EXPECTED_LENGTHS
            all_streams_valid &= valid
            coverage_rows.append({
                "context": context, "member": member, "file_count": len(files),
                "bytes": byte_count, "exact_carrier_set": int(ids == carrier_ids),
                "stream_valid": int(valid),
            })
    with (args.output / "03_BANK_COVERAGE.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(coverage_rows[0])); writer.writeheader(); writer.writerows(coverage_rows)

    smoke_a = relative_hashes(args.smoke_a)
    smoke_b = relative_hashes(args.smoke_b)
    release = relative_hashes(args.release_smoke)
    pre_relative = args.pre_vcpu_reference.relative_to(
        args.pre_vcpu_reference.parents[2]).as_posix()
    deterministic_gate = (
        smoke_a == smoke_b == release and len(smoke_a) == 2 and
        pre_relative in smoke_a and sha256_file(args.pre_vcpu_reference) == smoke_a[pre_relative]
    )
    smoke_files = sorted(args.smoke_a.glob("context_*/member_*/*.bin"))
    sensor_rows = []
    label_rows = []
    sensor_gate = True
    for path in smoke_files:
        physical_streams = read_physical(path)
        maximum, exact = exact_sensor_parity(args.authoritative_sensor, physical_streams)
        sensor_gate &= exact
        sensor_rows.append({"file": path.relative_to(args.smoke_a).as_posix(),
                            "max_abs_error": maximum, "bitwise_exact": int(exact)})
        for route, (physical, groups) in enumerate(zip(physical_streams, schedule_stops)):
            measured = sensor_forward(physical)
            for stop, indices in enumerate(groups):
                values = measured[indices]
                block_means = values.reshape(8, 10).mean(axis=1)
                label_rows.append({
                    "file": path.relative_to(args.smoke_a).as_posix(),
                    "route_seed": 4001 + route, "stop_index": stop,
                    "first_passage": first_passage(values),
                    "event": int(bool(np.any(values > 0.1))),
                    "native_block_hits": int(np.count_nonzero(block_means > 0.1)),
                    "samples": len(values),
                })
    with (args.output / "04_NATIVE_SENSOR_PARITY.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(sensor_rows[0])); writer.writeheader(); writer.writerows(sensor_rows)

    hashes = relative_hashes(args.bank)
    variation = []
    for context in range(10):
        different = 0
        for carrier_id in sorted(carrier_ids):
            left = hashes[f"context_{context:02d}/member_06/{carrier_id}.bin"]
            right = hashes[f"context_{context:02d}/member_07/{carrier_id}.bin"]
            different += left != right
        variation.append({"context": context, "member_pair": "6_vs_7", "different": different,
                          "total": 210, "fraction": different / 210.0})
    transport_gate = all(row["different"] > 0 for row in variation)
    with (args.output / "05_FIRST_PASSAGE_LABEL_AUDIT.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(label_rows[0])); writer.writeheader(); writer.writerows(label_rows)
    with (args.output / "05_PMFS_BLOCK_SEMANTICS.csv").open("w", newline="", encoding="utf-8") as target:
        fieldnames = ["route_seed", "schedule_samples", "completed_stops", "samples_per_stop",
                      "ordered_unique_nonmoving", "archived_block_reference_available"]
        writer = csv.DictWriter(target, fieldnames=fieldnames); writer.writeheader()
        for seed, rows, groups in zip(range(4001, 4006), schedule_rows, schedule_stops):
            writer.writerow({"route_seed": seed, "schedule_samples": len(rows), "completed_stops": len(groups),
                             "samples_per_stop": 80, "ordered_unique_nonmoving": 1,
                             "archived_block_reference_available": 0})

    contract = {
        "contract": "CTT_H01_WIND_CONDITIONED_NATIVE_BANK_G0_V1",
        "bank_summary_sha256": sha256_file(args.bank / "bank_summary.json"),
        "bank_file_manifest_sha256": sha256_file(args.bank / "FILE_SHA256.tsv"),
        "placement_manifest_sha256": sha256_file(args.placement_manifest),
        "carrier_manifest_sha256": sha256_file(args.carrier_manifest),
        "context_manifest_sha256": sha256_file(args.context_manifest),
        "authoritative_sensor_sha256": sha256_file(args.authoritative_sensor),
        "sensor_state_scope": "run_persistent_per_route",
        "measured_sequence_storage": "losslessly_derived_from_physical_sequence_and_frozen_sensor",
        "dt_s": 0.2, "dead_time_s": 0.4, "tau_s": 1.2,
        "threshold_ppm": 0.1, "samples_per_stop": 80,
        "schedule_sha256": [sha256_file(path) for path in schedules],
        "transport_variation": variation,
        "pre_vcpu_reference_sha256": sha256_file(args.pre_vcpu_reference),
        "pre_vcpu_reference_relative_path": pre_relative,
    }
    (args.output / "02_BANK_CONTRACT.json").write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n")
    (args.output / "02_BANK_FILE_SHA256.tsv").write_bytes((args.bank / "FILE_SHA256.tsv").read_bytes())
    gates = {
        "G0_A_source_query_coverage": carrier_gate and all_streams_valid,
        "G0_B_wind_provenance": context_gate,
        "G0_C_same_seed_determinism": deterministic_gate,
        "G0_C_held_key_variation": transport_gate,
        "G0_D_native_sensor_parity": sensor_gate,
        "G0_E_pmfs_block_semantics": schedule_gate,
    }
    report = {"contract": contract["contract"], "gates": gates,
              "verdict": "CTT_H01_WIND_BANK_G0_PASS" if all(gates.values()) else "STOP_CTT_H01_M1_BANK_INVALID"}
    (args.output / "G0_GATE.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))
    return 0 if all(gates.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())

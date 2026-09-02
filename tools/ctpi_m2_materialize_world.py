#!/usr/bin/env python3
"""Materialize exactly one source-intervention observation world."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import struct
import subprocess
from pathlib import Path
from typing import Any

import numpy as np


CONTRACT = "CTPI_M2_ONE_WORLD_MATERIALIZER_V1"
MAGIC = b"PFV3STR1"
TIME_COUNT = 1500
DT_S = 0.2
STOP_SAMPLES = 80
STOP_COUNT = 15
THRESHOLD_PPM = 0.1
DELAY_SAMPLES = 2
ALPHA = math.exp(-DT_S / 1.2)
EXPECTED_RUNTIME_CONTRACT = "CTPI_M2_GENERATOR_RUNTIME_IDENTITY_V1"
EXPECTED_WORLD_CONTRACT = "CTPI_M2_SOURCE_INTERVENTION_WORLD_MANIFEST_V1"
NATIVE_BINARY = Path("/home/zyc/PF_DEI_V3_STREAM_BUILD/install/bin/pf_dei_v3_native_multistream")
ROUTE_ROOT = Path("/home/zyc/CG_PC_CTT_V3_ORR_MULTI30_20260827")
BANK_ROOT = Path("/mnt/hgfs/workspace/CPIR_M1_FULLGRID_LOOKUP_20260831_R1")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def bank_metadata_fingerprint(root: Path) -> str:
    digest = hashlib.sha256()
    files = sorted(path for path in root.rglob("*") if path.is_file())
    if not files:
        raise RuntimeError("CTPI_WORLD_BANK_EMPTY")
    for path in files:
        stat = path.stat()
        relative = path.relative_to(root).as_posix()
        digest.update(f"{relative}\t{stat.st_size}\t{stat.st_mtime_ns}\n".encode("utf-8"))
    return digest.hexdigest()


def read_single_stream(path: Path) -> np.ndarray:
    with path.open("rb") as source:
        head = source.read(12)
        if len(head) != 12 or head[:8] != MAGIC:
            raise RuntimeError("CTPI_WORLD_BINARY_MAGIC")
        count = struct.unpack_from("<I", head, 8)[0]
        if count != 1:
            raise RuntimeError(f"CTPI_WORLD_STREAM_COUNT:{count}")
        length_raw = source.read(4)
        if len(length_raw) != 4 or struct.unpack("<I", length_raw)[0] != TIME_COUNT:
            raise RuntimeError("CTPI_WORLD_STREAM_LENGTH")
        values = np.fromfile(source, dtype="<f4", count=TIME_COUNT)
        if values.size != TIME_COUNT or source.read(1):
            raise RuntimeError("CTPI_WORLD_BINARY_SIZE")
    if not np.isfinite(values).all() or np.any(values < 0.0):
        raise RuntimeError("CTPI_WORLD_PHYSICAL_VALUES")
    return values.astype(np.float64)


def forward_sensor(physical: np.ndarray) -> np.ndarray:
    value = np.asarray(physical, dtype=np.float64)
    if value.shape != (TIME_COUNT,) or not np.isfinite(value).all() or np.any(value < 0.0):
        raise ValueError("CTPI_WORLD_SENSOR_INPUT")
    delayed = np.concatenate((np.zeros(DELAY_SAMPLES, dtype=np.float64), value))
    measured = np.empty(TIME_COUNT + DELAY_SAMPLES, dtype=np.float64)
    state = 0.0
    for index, target in enumerate(delayed):
        state = ALPHA * state + (1.0 - ALPHA) * float(target)
        measured[index] = state
    return measured


def read_route(path: Path) -> tuple[list[dict[str, str]], list[np.ndarray]]:
    with path.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    if len(rows) != TIME_COUNT:
        raise RuntimeError(f"CTPI_WORLD_ROUTE_LENGTH:{len(rows)}")
    times = np.asarray([float(row["t_sim_s"]) for row in rows])
    expected = np.arange(1, TIME_COUNT + 1, dtype=np.float64) * DT_S
    if np.max(np.abs(times - expected)) > 1.0e-6:
        raise RuntimeError("CTPI_WORLD_ROUTE_TIME_GRID")
    moving = np.asarray([int(row["is_moving"]) for row in rows], dtype=np.int8)
    stops: list[np.ndarray] = []
    start: int | None = None
    for index, value in enumerate(moving):
        if value == 0 and start is None:
            start = index
        elif value != 0 and start is not None:
            if index - start >= STOP_SAMPLES:
                stops.append(np.arange(start, start + STOP_SAMPLES, dtype=np.int64))
            start = None
    if start is not None and TIME_COUNT - start >= STOP_SAMPLES:
        stops.append(np.arange(start, start + STOP_SAMPLES, dtype=np.int64))
    if len(stops) != STOP_COUNT or any(len(stop) != STOP_SAMPLES for stop in stops):
        raise RuntimeError(f"CTPI_WORLD_STOP_CONTRACT:{len(stops)}")
    return rows, stops


def unique_route(house: str, route: int) -> Path:
    house_dir = f"House{house[1:]}"
    matches = sorted((ROUTE_ROOT / house_dir / f"seed{route}" / "off" / "runtime").glob(
        "*/sim_pose_trace.csv"
    ))
    if len(matches) != 1:
        raise RuntimeError(f"CTPI_WORLD_ROUTE_IDENTITY:{house}:{route}:{len(matches)}")
    return matches[0]


def select_world(manifest: dict[str, Any], world_id: str) -> dict[str, Any]:
    records = list(manifest["formal_worlds"]) + [manifest["disposable_smoke_world"]]
    matches = [row for row in records if row["world_id"] == world_id]
    if len(matches) != 1:
        raise RuntimeError(f"CTPI_WORLD_ID:{world_id}:{len(matches)}")
    return matches[0]


def materialize(args: argparse.Namespace) -> dict[str, Any]:
    if args.output.exists():
        raise RuntimeError(f"CTPI_WORLD_REFUSE_STALE_OUTPUT:{args.output}")
    runtime = json.loads(args.runtime_report.read_text(encoding="utf-8"))
    manifest = json.loads(args.world_manifest.read_text(encoding="utf-8"))
    if runtime.get("contract") != EXPECTED_RUNTIME_CONTRACT or not runtime.get("pass"):
        raise RuntimeError("CTPI_WORLD_RUNTIME_NOT_PASS")
    if manifest.get("contract") != EXPECTED_WORLD_CONTRACT or not manifest.get("pass"):
        raise RuntimeError("CTPI_WORLD_MANIFEST_NOT_PASS")
    world = select_world(manifest, args.world_id)
    if world["set"] == "SMOKE":
        if not args.allow_disposable_smoke:
            raise RuntimeError("CTPI_WORLD_SMOKE_NOT_AUTHORIZED")
    else:
        if args.authorization is None:
            raise RuntimeError("CTPI_WORLD_FORMAL_DATASET_LOCKED")
        authorization = json.loads(args.authorization.read_text(encoding="utf-8"))
        if authorization.get("CTPI_M2_SOURCE_INTERVENTION_PREGEN") != "PASS":
            raise RuntimeError("CTPI_WORLD_PREGEN_AUTHORIZATION")
        if world["set"] == "M2_CONFIRM" and authorization.get("M2_CAL_FREEZE") != "PASS":
            raise RuntimeError("CTPI_WORLD_CONFIRM_LOCKED")

    args.output.mkdir(parents=True, exist_ok=False)
    try:
        bank_before = bank_metadata_fingerprint(BANK_ROOT)
        house = str(world["house"])
        route_path = unique_route(house, int(world["route_index"]))
        route_rows, stops = read_route(route_path)
        house_runtime = runtime["houses"][house]
        binary_path = args.output / "physical_world.bin"
        command = [
            str(NATIVE_BINARY), house_runtime["environment"], house_runtime["wind_dir"],
            *(repr(float(value)) for value in world["source_xyz_m"]),
            str(int(world["observation_transport_seed_uint32"])), repr(DT_S),
            str(binary_path), str(route_path),
        ]
        completed = subprocess.run(command, env=os.environ.copy(), text=True,
                                   capture_output=True, check=False)
        if completed.returncode != 0:
            raise RuntimeError("CTPI_WORLD_NATIVE_FAIL:" + completed.stdout + completed.stderr)
        physical = read_single_stream(binary_path)
        measured = forward_sensor(physical)
        events = np.asarray([
            bool(np.max(measured[stop]) > THRESHOLD_PPM) for stop in stops
        ], dtype=np.bool_)
        if measured.shape != (1502,) or events.shape != (15,):
            raise RuntimeError("CTPI_WORLD_OUTPUT_SHAPE")

        physical_path = args.output / "physical_ppm.npy"
        measured_path = args.output / "measured_ppm_1502.npy"
        np.save(physical_path, physical, allow_pickle=False)
        np.save(measured_path, measured, allow_pickle=False)
        events_path = args.output / "stop_events.csv"
        with events_path.open("w", newline="", encoding="utf-8") as target:
            writer = csv.DictWriter(target, fieldnames=(
                "stop_id", "start_index", "end_index", "action_id", "observed_hit",
                "max_measured_ppm",
            ))
            writer.writeheader()
            for stop_id, stop in enumerate(stops, 1):
                writer.writerow({
                    "stop_id": stop_id, "start_index": int(stop[0]),
                    "end_index": int(stop[-1]),
                    "action_id": f"{house}_route{int(world['route_index']):02d}_stop{stop_id:02d}",
                    "observed_hit": int(events[stop_id - 1]),
                    "max_measured_ppm": repr(float(np.max(measured[stop]))),
                })
        tape_path = args.output / "observation_tape.csv"
        with tape_path.open("w", newline="", encoding="utf-8") as target:
            writer = csv.DictWriter(target, fieldnames=("t_sim_s", "step", "measured_gas_ppm"))
            writer.writeheader()
            for index, row in enumerate(route_rows):
                writer.writerow({"t_sim_s": row["t_sim_s"], "step": row["step"],
                                 "measured_gas_ppm": repr(float(measured[index]))})
        sealed_dir = args.output / "sealed"
        sealed_dir.mkdir()
        sealed_path = sealed_dir / "source_intervention.json"
        sealed_payload = {
            "world_id": world["world_id"], "controlled_carrier_id": world["controlled_carrier_id"],
            "source_xyz_m": world["source_xyz_m"],
            "source_xyz_semantics": world["source_xyz_semantics"],
            "reserved_placement_member": world["reserved_placement_member"],
            "reserved_placement_quantile": world["reserved_placement_quantile"],
            "observation_rng_domain": world["observation_rng_domain"],
            "observation_transport_seed_uint32": world["observation_transport_seed_uint32"],
            "runtime_visibility": "SEALED_FROM_LOCALIZATION_AND_PLANNER",
        }
        sealed_path.write_bytes(canonical_bytes(sealed_payload))
        bank_after = bank_metadata_fingerprint(BANK_ROOT)
        if bank_after != bank_before:
            raise RuntimeError("CTPI_WORLD_BANK_METADATA_CHANGED")

        payload_files = [binary_path, physical_path, measured_path, events_path, tape_path, sealed_path]
        payload_hashes = {path.relative_to(args.output).as_posix(): sha256_file(path)
                          for path in payload_files}
        combined = hashlib.sha256()
        for name, digest in sorted(payload_hashes.items()):
            combined.update(f"{name}\t{digest}\n".encode("ascii"))
        audit = {
            "contract": CONTRACT, "world_id": world["world_id"], "set": world["set"],
            "house": house, "route_index": int(world["route_index"]),
            "world_manifest_sha256": sha256_file(args.world_manifest),
            "runtime_report_sha256": sha256_file(args.runtime_report),
            "route_path": str(route_path), "route_sha256": sha256_file(route_path),
            "physical_samples": int(len(physical)), "forward_sensor_samples": int(len(measured)),
            "completed_stop_events": int(len(events)), "hit_count": int(np.count_nonzero(events)),
            "event_rule": "max_measured_first_80_stationary_samples_strict_gt_0.1_ppm",
            "sensor": {"dt_s": DT_S, "dead_time_s": 0.4, "tau_s": 1.2,
                       "gain": 1.0, "baseline": 0.0, "initial_input": 0.0,
                       "initial_state": 0.0, "alpha": ALPHA},
            "one_world_per_native_invocation": True,
            "native_invocation_count": 1,
            "bank_root": str(BANK_ROOT), "bank_metadata_before": bank_before,
            "bank_metadata_after": bank_after, "bank_unchanged": True,
            "payload_sha256": combined.hexdigest(), "file_sha256": payload_hashes,
            "native_stdout": completed.stdout.strip(), "native_stderr": completed.stderr.strip(),
            "source_metadata_visibility": "SEALED_FROM_LOCALIZATION_AND_PLANNER",
            "pass": True, "verdict": "CTPI_M2_WORLD_MATERIALIZATION=PASS",
        }
        (args.output / "WORLD_AUDIT.json").write_bytes(canonical_bytes(audit))
        (args.output / "PASS").write_text("CTPI_M2_WORLD_MATERIALIZATION=PASS\n", encoding="ascii")
        return audit
    except Exception as exc:
        (args.output / "FAIL").write_text(
            f"CTPI_M2_WORLD_MATERIALIZATION=FAIL\n{type(exc).__name__}:{exc}\n",
            encoding="utf-8",
        )
        raise


def selftest() -> None:
    physical = np.zeros(TIME_COUNT, dtype=np.float64)
    physical[10:20] = 1.0
    measured = forward_sensor(physical)
    assert measured.shape == (1502,)
    assert measured[10] == 0.0 and measured[12] > 0.0
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "one.bin"
        with path.open("wb") as target:
            target.write(MAGIC); target.write(struct.pack("<I", 1)); target.write(struct.pack("<I", TIME_COUNT))
            target.write(physical.astype("<f4").tobytes())
        np.testing.assert_allclose(read_single_stream(path), physical)
    print("CTPI_M2_ONE_WORLD_MATERIALIZER_SELFTEST=PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--world-manifest", type=Path)
    parser.add_argument("--runtime-report", type=Path)
    parser.add_argument("--world-id")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--allow-disposable-smoke", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return 0
    if any(value is None for value in (args.world_manifest, args.runtime_report,
                                       args.world_id, args.output)):
        parser.error("materialization arguments are required")
    audit = materialize(args)
    print(audit["verdict"])
    print(f"CTPI_M2_WORLD_PAYLOAD_SHA256={audit['payload_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

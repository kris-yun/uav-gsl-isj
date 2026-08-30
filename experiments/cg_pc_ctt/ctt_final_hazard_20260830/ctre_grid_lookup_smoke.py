#!/usr/bin/env python3
"""Benchmark one native world queried on every H01 free cell for 300 s."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
import subprocess
import tarfile
import time

from ctt_h01_wind_bank_io import read_physical, sha256_file

ROOT = "CG_PC_CTT_V3_ORR_FULL60_PACKAGE_20260827/results/House01"


def load_cells(archive: Path) -> list[dict]:
    member = f"{ROOT}/seed0/off/final_posterior.csv"
    with tarfile.open(archive, "r:gz") as source:
        handle = source.extractfile(member)
        if handle is None:
            raise ValueError("CTRE_GRID_CELL_SOURCE_MISSING")
        rows = list(csv.DictReader(io.StringIO(handle.read().decode("utf-8"))))
    if len(rows) != 626:
        raise ValueError(f"CTRE_GRID_CELL_COUNT:{len(rows)}")
    return rows


def write_schedule(path: Path, cell: dict) -> None:
    fieldnames = ["t_sim_s", "step", "x", "y", "z", "yaw", "is_moving",
                  "seed", "stop_id", "stop_start", "block_boundary"]
    with path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        for step in range(1, 1501):
            writer.writerow({
                "t_sim_s": f"{0.2 * step:.6f}", "step": step,
                "x": cell["x"], "y": cell["y"], "z": "0.300000",
                "yaw": "0.000000", "is_moving": 0, "seed": 0,
                "stop_id": 1, "stop_start": int(step == 1),
                "block_boundary": int(step == 1),
            })


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--native-binary", type=Path, required=True)
    parser.add_argument("--environment", type=Path, required=True)
    parser.add_argument("--wind-dir", type=Path, required=True)
    parser.add_argument("--source-x", type=float, required=True)
    parser.add_argument("--source-y", type=float, required=True)
    parser.add_argument("--source-z", type=float, required=True)
    parser.add_argument("--transport-seed", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"CTRE_GRID_SMOKE_REFUSE_OVERWRITE:{args.output}")
    args.output.mkdir(parents=True)
    cells = load_cells(args.archive)
    schedule_root = args.output / "schedules"
    schedule_root.mkdir()
    schedules = []
    for index, cell in enumerate(cells):
        path = schedule_root / f"cell_{index:04d}.csv"
        write_schedule(path, cell)
        schedules.append(path)
    binary_output = args.output / "one_world_all_cells.bin"
    command = [
        str(args.native_binary), str(args.environment), str(args.wind_dir),
        repr(args.source_x), repr(args.source_y), repr(args.source_z),
        str(args.transport_seed), "0.2", str(binary_output),
        *(str(path) for path in schedules),
    ]
    started = time.monotonic()
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    elapsed = time.monotonic() - started
    if completed.returncode != 0:
        raise RuntimeError("CTRE_GRID_NATIVE_FAIL\n" + completed.stdout + "\n" + completed.stderr)
    streams = read_physical(binary_output)
    if len(streams) != 626 or {len(stream) for stream in streams} != {1500}:
        raise ValueError(f"CTRE_GRID_STREAM_CONTRACT:{len(streams)}:{sorted({len(x) for x in streams})}")
    report = {
        "contract": "CTRE_GRID_LOOKUP_ONE_WORLD_SMOKE_V1",
        "cell_count": len(streams),
        "samples_per_cell": len(streams[0]),
        "total_samples": sum(len(stream) for stream in streams),
        "elapsed_s": elapsed,
        "output_bytes": binary_output.stat().st_size,
        "output_sha256": sha256_file(binary_output),
        "native_binary_sha256": sha256_file(args.native_binary),
        "environment_sha256": sha256_file(args.environment),
        "verdict": "CTRE_GRID_LOOKUP_ONE_WORLD_SMOKE_PASS",
    }
    (args.output / "SUMMARY.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

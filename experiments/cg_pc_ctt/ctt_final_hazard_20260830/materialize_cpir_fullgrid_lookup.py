#!/usr/bin/env python3
"""Materialize a trajectory-independent CPIR source/member/free-cell field bank.

This is an engineering generalization of the already-passed H01 CTRE one-world
smoke.  It changes no forward physics: every subprocess is the frozen native
main_v8 multistream generator with one V3 train placement/transport row.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import time


MAGIC = b"PFV3STR1"
TIME_COUNT = 1500
GENERATION_ENVIRONMENT = {
    "OMP_NUM_THREADS": "4",
    "OMP_DYNAMIC": "FALSE",
    "OMP_SCHEDULE": "static",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_header(path: Path) -> tuple[int, list[int]]:
    with path.open("rb") as source:
        head = source.read(12)
        if len(head) != 12 or head[:8] != MAGIC:
            raise ValueError(f"CPIR_LOOKUP_BAD_MAGIC:{path}")
        count = struct.unpack_from("<I", head, 8)[0]
        raw = source.read(4 * count)
    if len(raw) != 4 * count:
        raise ValueError(f"CPIR_LOOKUP_TRUNCATED_LENGTHS:{path}")
    lengths = list(struct.unpack(f"<{count}I", raw))
    return count, lengths


def validate_world(path: Path, cell_count: int) -> None:
    count, lengths = read_header(path)
    if count != cell_count or set(lengths) != {TIME_COUNT}:
        raise ValueError(f"CPIR_LOOKUP_STREAM_CONTRACT:{path}:{count}")
    expected = 12 + 4 * count + 4 * count * TIME_COUNT
    if path.stat().st_size != expected:
        raise ValueError(f"CPIR_LOOKUP_SIZE_CONTRACT:{path}:{path.stat().st_size}:{expected}")


def load_cells(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    required = {"cell_index", "x", "y"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError("CPIR_LOOKUP_CELL_SCHEMA")
    rows.sort(key=lambda row: int(row["cell_index"]))
    indices = [int(row["cell_index"]) for row in rows]
    if len(set(indices)) != len(indices) or any(index < 0 for index in indices):
        raise ValueError("CPIR_LOOKUP_CELL_INDEX_UNIQUE_NONNEGATIVE")
    return rows


def write_schedule(path: Path, cell: dict[str, str]) -> None:
    fields = ["t_sim_s", "step", "x", "y", "z", "yaw", "is_moving",
              "seed", "stop_id", "stop_start", "block_boundary"]
    with path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        for step in range(1, TIME_COUNT + 1):
            writer.writerow({
                "t_sim_s": f"{0.2 * step:.6f}", "step": step,
                "x": cell["x"], "y": cell["y"], "z": "0.300000",
                "yaw": "0.000000", "is_moving": 0, "seed": 0,
                "stop_id": 1, "stop_start": int(step == 1),
                "block_boundary": int(step == 1),
            })


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--house", choices=("H01", "H02", "H03"), required=True)
    parser.add_argument("--cell-csv", type=Path, required=True)
    parser.add_argument("--placement-manifest", type=Path, required=True)
    parser.add_argument("--native-binary", type=Path, required=True)
    parser.add_argument("--environment", type=Path, required=True)
    parser.add_argument("--wind-dir", type=Path, required=True)
    parser.add_argument("--observation-realization", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    if not 1 <= args.workers <= 12:
        raise SystemExit("CPIR_LOOKUP_WORKERS_1_TO_12")
    for path in (args.cell_csv, args.placement_manifest, args.native_binary,
                 args.environment, args.wind_dir, args.observation_realization):
        if not path.exists():
            raise SystemExit(f"CPIR_LOOKUP_INPUT_MISSING:{path}")

    placement = json.loads(args.placement_manifest.read_text(encoding="utf-8"))
    rows = [row for row in placement["rows"]
            if row["house"] == args.house and row["split"] == "train"]
    rows.sort(key=lambda row: (int(row["member_id"]), row["carrier_id"]))
    if placement.get("contract") != "PF_DEI_V3_REGION_PLACEMENT_V1":
        raise SystemExit("CPIR_LOOKUP_PLACEMENT_CONTRACT")
    carriers = sorted({row["carrier_id"] for row in rows})
    if len(rows) != 8 * len(carriers) or sorted({int(row["member_id"]) for row in rows}) != list(range(8)):
        raise SystemExit("CPIR_LOOKUP_MEMBER_CARRIER_RECTANGLE")

    cells = load_cells(args.cell_csv)
    output = args.output
    if output.exists() and not (output / "IN_PROGRESS").is_file():
        raise SystemExit(f"CPIR_LOOKUP_REFUSE_NONRESUMABLE:{output}")
    output.mkdir(parents=True, exist_ok=True)
    (output / "IN_PROGRESS").write_text("CPIR_FULLGRID_LOOKUP_V1\n", encoding="utf-8")
    schedules = output / "cell_schedules"
    schedules.mkdir(exist_ok=True)
    schedule_paths: list[Path] = []
    for index, cell in enumerate(cells):
        path = schedules / f"cell_{index:04d}.csv"
        if not path.is_file():
            temporary = path.with_suffix(f".tmp.{os.getpid()}")
            write_schedule(temporary, cell)
            os.replace(temporary, path)
        schedule_paths.append(path)
    with (output / "cell_manifest.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=("stream_ordinal", "native_cell_index", "x", "y"))
        writer.writeheader()
        for ordinal, cell in enumerate(cells):
            writer.writerow({"stream_ordinal": ordinal, "native_cell_index": int(cell["cell_index"]),
                             "x": cell["x"], "y": cell["y"]})

    frozen_env = os.environ.copy()
    frozen_env.update(GENERATION_ENVIRONMENT)

    def generate(row: dict) -> str:
        member = int(row["member_id"])
        final = output / "worlds" / f"member_{member:02d}" / f"{row['carrier_id']}.bin"
        if final.is_file():
            validate_world(final, len(cells))
            return "reused"
        final.parent.mkdir(parents=True, exist_ok=True)
        temporary = final.with_suffix(f".tmp.{os.getpid()}")
        command = [
            str(args.native_binary), str(args.environment), str(args.wind_dir),
            repr(float(row["x"])), repr(float(row["y"])), repr(float(row["z"])),
            str(int(row["transport_seed"])), "0.2", str(temporary),
            *(str(path) for path in schedule_paths),
        ]
        try:
            complete = subprocess.run(command, env=frozen_env, text=True,
                                      capture_output=True, check=False)
            if complete.returncode != 0:
                raise RuntimeError("CPIR_LOOKUP_NATIVE_FAIL\n" + complete.stdout + complete.stderr)
            validate_world(temporary, len(cells))
            os.replace(temporary, final)
        finally:
            temporary.unlink(missing_ok=True)
        return "generated"

    started = time.monotonic()
    counts = {"generated": 0, "reused": 0}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(generate, row) for row in rows]
        for index, future in enumerate(concurrent.futures.as_completed(futures), 1):
            counts[future.result()] += 1
            if index % 50 == 0 or index == len(futures):
                print(f"CPIR_LOOKUP_PROGRESS={args.house}:{index}/{len(futures)} {counts}", flush=True)

    files = sorted((output / "worlds").glob("member_*/*.bin"))
    if len(files) != len(rows):
        raise SystemExit(f"CPIR_LOOKUP_FILE_COUNT:{len(files)}:{len(rows)}")
    manifest_rows = []
    total_bytes = 0
    for path in files:
        validate_world(path, len(cells))
        relative = path.relative_to(output).as_posix()
        size = path.stat().st_size
        manifest_rows.append(f"{relative}\t{size}\t{sha256_file(path)}")
        total_bytes += size
    (output / "FILE_SHA256.tsv").write_text("\n".join(manifest_rows) + "\n", encoding="utf-8")
    prediction_keys = sorted({int(row["transport_seed"]) for row in rows})
    summary = {
        "contract": "CPIR_FULLGRID_LOOKUP_V1",
        "house": args.house,
        "carrier_count": len(carriers), "member_count": 8,
        "cell_count": len(cells), "time_count": TIME_COUNT,
        "file_count": len(files), "total_bytes": total_bytes,
        "counts": counts, "elapsed_s": time.monotonic() - started,
        "generation_environment": GENERATION_ENVIRONMENT,
        "prediction_transport_keys": prediction_keys,
        "prediction_rng_domain": "PF_DEI_V3_REGION_PLACEMENT_V1/train",
        "observation_rng_domain": "immutable_external_GADEN_dataset_world",
        "observation_realization": str(args.observation_realization),
        "observation_realization_sha256": sha256_file(args.observation_realization),
        "cell_csv_sha256": sha256_file(args.cell_csv),
        "cell_manifest_sha256": sha256_file(output / "cell_manifest.csv"),
        "placement_manifest_sha256": sha256_file(args.placement_manifest),
        "native_binary_sha256": sha256_file(args.native_binary),
        "environment_sha256": sha256_file(args.environment),
        "wind_iteration_hashes": {
            path.name: sha256_file(path) for path in sorted(args.wind_dir.glob("wind_iteration_*"))
            if path.is_file()
        },
        "verdict": "CPIR_FULLGRID_LOOKUP_PASS",
    }
    (output / "bank_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "IN_PROGRESS").unlink()
    print(json.dumps(summary, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

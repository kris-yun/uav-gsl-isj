#!/usr/bin/env python3
"""Materialize the frozen H01 context-14 full-grid CTRE runtime lookup."""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import time

from ctt_h01_wind_bank_io import read_physical, sha256_file

ROOT = "CG_PC_CTT_V3_ORR_FULL60_PACKAGE_20260827/results/House01"
CONTRACT = "CTRE_H01_CONTEXT14_FULL_GRID_LOOKUP_V1"
CELL_COUNT = 626
TIME_COUNT = 1500


def load_cells(archive: Path) -> list[dict]:
    member = f"{ROOT}/seed0/off/final_posterior.csv"
    with tarfile.open(archive, "r:gz") as source:
        handle = source.extractfile(member)
        if handle is None:
            raise ValueError("CTRE_LOOKUP_CELL_SOURCE_MISSING")
        rows = list(csv.DictReader(io.StringIO(handle.read().decode("utf-8"))))
    if len(rows) != CELL_COUNT:
        raise ValueError(f"CTRE_LOOKUP_CELL_COUNT:{len(rows)}")
    return rows


def write_schedule(path: Path, cell: dict) -> None:
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


def validate(path: Path) -> None:
    streams = read_physical(path)
    if len(streams) != CELL_COUNT or {len(stream) for stream in streams} != {TIME_COUNT}:
        raise ValueError(f"CTRE_LOOKUP_STREAM_CONTRACT:{path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--placement-manifest", type=Path, required=True)
    parser.add_argument("--context-manifest", type=Path, required=True)
    parser.add_argument("--native-binary", type=Path, required=True)
    parser.add_argument("--environment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    if not 1 <= args.workers <= 12:
        raise SystemExit("CTRE_LOOKUP_WORKERS_1_TO_12")
    placement = json.loads(args.placement_manifest.read_text(encoding="utf-8"))
    rows = [row for row in placement["rows"] if row["house"] == "H01" and row["split"] == "train"]
    rows.sort(key=lambda row: (int(row["member_id"]), row["carrier_id"]))
    if placement.get("contract") != "PF_DEI_V3_REGION_PLACEMENT_V1" or len(rows) != 1680:
        raise SystemExit("CTRE_LOOKUP_PLACEMENT_CONTRACT")
    context_payload = json.loads(args.context_manifest.read_text(encoding="utf-8"))
    contexts = [item for item in context_payload["contexts"] if int(item["context"]) == 14]
    if context_payload.get("contract") != "CTT_H01_FRESH_STATIC_WIND_CONTEXTS_V1" or len(contexts) != 1:
        raise SystemExit("CTRE_LOOKUP_CONTEXT_CONTRACT")
    context = contexts[0]
    wind_dir = Path(context["wind_dir"])
    if sha256_file(Path(context["original_path"])) != context["payload_sha256"]:
        raise SystemExit("CTRE_LOOKUP_WIND_HASH")
    output = args.output
    if output.exists() and not (output / "IN_PROGRESS").is_file():
        raise SystemExit(f"CTRE_LOOKUP_REFUSE_NONRESUMABLE:{output}")
    output.mkdir(parents=True, exist_ok=True)
    (output / "IN_PROGRESS").write_text(CONTRACT + "\n", encoding="utf-8")
    schedules = output / "cell_schedules"
    schedules.mkdir(exist_ok=True)
    cells = load_cells(args.archive)
    paths = []
    for index, cell in enumerate(cells):
        path = schedules / f"cell_{index:04d}.csv"
        if not path.is_file():
            temporary = path.with_suffix(f".tmp.{os.getpid()}")
            write_schedule(temporary, cell)
            os.replace(temporary, path)
        paths.append(path)

    def generate(row: dict) -> str:
        member = int(row["member_id"])
        final = output / "worlds" / f"member_{member:02d}" / f"{row['carrier_id']}.bin"
        if final.is_file():
            validate(final)
            return "reused"
        final.parent.mkdir(parents=True, exist_ok=True)
        temporary = final.with_suffix(f".tmp.{os.getpid()}")
        command = [
            str(args.native_binary), str(args.environment), str(wind_dir),
            repr(float(row["x"])), repr(float(row["y"])), repr(float(row["z"])),
            str(int(row["transport_seed"])), "0.2", str(temporary),
            *(str(path) for path in paths),
        ]
        try:
            complete = subprocess.run(command, text=True, capture_output=True, check=False)
            if complete.returncode != 0:
                raise RuntimeError(
                    "CTRE_LOOKUP_NATIVE_FAIL\n" + complete.stdout + "\n" + complete.stderr)
            validate(temporary)
            os.replace(temporary, final)
        finally:
            temporary.unlink(missing_ok=True)
        return "generated"

    started = time.monotonic()
    counts = {"generated": 0, "reused": 0}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(generate, row) for row in rows]
        for index, future in enumerate(concurrent.futures.as_completed(futures), start=1):
            counts[future.result()] += 1
            if index % 100 == 0 or index == len(futures):
                print(f"CTRE_LOOKUP_PROGRESS={index}/{len(futures)} {counts}", flush=True)
    files = sorted((output / "worlds").glob("member_*/*.bin"))
    if len(files) != 1680:
        raise SystemExit(f"CTRE_LOOKUP_FILE_COUNT:{len(files)}")
    manifest = []
    total_bytes = 0
    for path in files:
        relative = path.relative_to(output).as_posix()
        digest = sha256_file(path)
        manifest.append(f"{relative}\t{path.stat().st_size}\t{digest}")
        total_bytes += path.stat().st_size
    (output / "FILE_SHA256.tsv").write_text("\n".join(manifest) + "\n", encoding="utf-8")
    summary = {
        "contract": CONTRACT,
        "context": 14,
        "source_count": 210,
        "member_count": 8,
        "cell_count": CELL_COUNT,
        "time_count": TIME_COUNT,
        "file_count": len(files),
        "total_samples": 210 * 8 * CELL_COUNT * TIME_COUNT,
        "total_bytes": total_bytes,
        "elapsed_s": time.monotonic() - started,
        "counts": counts,
        "archive_sha256": sha256_file(args.archive),
        "placement_manifest_sha256": sha256_file(args.placement_manifest),
        "context_manifest_sha256": sha256_file(args.context_manifest),
        "native_binary_sha256": sha256_file(args.native_binary),
        "environment_sha256": sha256_file(args.environment),
        "verdict": "CTRE_H01_CONTEXT14_FULL_GRID_LOOKUP_PASS",
    }
    (output / "bank_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "IN_PROGRESS").unlink()
    print(json.dumps(summary, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

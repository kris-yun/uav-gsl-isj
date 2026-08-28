#!/usr/bin/env python3
"""Generate the frozen PF-DEI V3 native bank on 30 truth-blind OFF trajectories.

Each native GADEN realization is simulated once and queried at all ten historical
trajectories for its House. Outputs are atomic, resumable binary shards.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

from pf_dei_v3_stream_format import read_multistream


HOUSES = ("H01", "H02", "H03")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def historical_schedule_paths(root: Path, house: str) -> list[Path]:
    return [
        root / f"House{house[-2:]}" / f"seed{seed}" / "off" / "runtime"
        / f"House{house[-2:]}_seed{seed}_off_off" / "sim_pose_trace.csv"
        for seed in range(10)
    ]


def all_schedule_paths(historical_root: Path, maponly_root: Path, house: str, split: str) -> list[Path]:
    paths = historical_schedule_paths(historical_root, house)
    seeds = range(3001, 3021) if split == "train" else range(4001, 4006)
    paths.extend(maponly_root / house / split / f"trajectory_seed_{seed}.csv" for seed in seeds)
    return paths


def schedule_lengths(paths: list[Path]) -> list[int]:
    lengths = []
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(path)
        with path.open(newline="") as source:
            lengths.append(sum(1 for _ in csv.DictReader(source)))
    return lengths


def validate_shard(path: Path, expected_lengths: list[int]) -> None:
    values = read_multistream(path)
    actual = [int(item.size) for item in values]
    if actual != expected_lengths:
        raise ValueError(f"PF_DEI_V3_SHARD_LENGTH_MISMATCH:{path}:{actual}:{expected_lengths}")


def shard_path(root: Path, row: dict) -> Path:
    member = int(row["member_id"])
    return root / row["house"] / row["split"] / f"member_{member:02d}" / f"{row['carrier_id']}.bin"


def generate_one(
    binary: Path,
    row: dict,
    output_root: Path,
    envs: dict[str, Path],
    winds: dict[str, Path],
    schedules: dict[tuple[str, str], list[Path]],
    lengths: dict[tuple[str, str], list[int]],
) -> dict:
    output = shard_path(output_root, row)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.is_file():
        validate_shard(output, lengths[(row["house"], row["split"])])
        return {"status": "reused", "path": str(output)}

    temp = output.with_suffix(f".tmp.{os.getpid()}")
    command = [
        str(binary), str(envs[row["house"]]), str(winds[row["house"]]),
        repr(float(row["x"])), repr(float(row["y"])), repr(float(row["z"])),
        str(int(row["transport_seed"])), "0.2", str(temp),
        *(str(path) for path in schedules[(row["house"], row["split"])]),
    ]
    try:
        completed = subprocess.run(command, check=False, text=True, capture_output=True)
        if completed.returncode != 0:
            raise RuntimeError(
                f"PF_DEI_V3_NATIVE_SHARD_FAILED:{row['house']}:{row['carrier_id']}:"
                f"{row['split']}:{row['member_id']}\n{completed.stdout}\n{completed.stderr}"
            )
        validate_shard(temp, lengths[(row["house"], row["split"])])
        os.replace(temp, output)
    finally:
        temp.unlink(missing_ok=True)
    return {"status": "generated", "path": str(output)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--trajectory-root", type=Path, required=True)
    parser.add_argument("--maponly-root", type=Path, required=True)
    parser.add_argument("--environment-root", type=Path, required=True)
    parser.add_argument("--h02-environment", type=Path, required=True)
    parser.add_argument("--h02-wind", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    if not 1 <= args.workers <= 4:
        raise SystemExit("PF_DEI_V3_WORKERS_MUST_BE_1_TO_4")

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("contract") != "PF_DEI_V3_REGION_PLACEMENT_V1":
        raise SystemExit("PF_DEI_V3_BAD_PLACEMENT_CONTRACT")
    rows = list(manifest["rows"])
    if args.limit is not None:
        rows = rows[: args.limit]

    envs = {
        "H01": args.environment_root / "H01" / "OccupancyGrid3D.csv",
        "H02": args.h02_environment,
        "H03": args.environment_root / "H03" / "OccupancyGrid3D.csv",
    }
    winds = {
        "H01": args.environment_root / "H01" / "wind",
        "H02": args.h02_wind,
        "H03": args.environment_root / "H03" / "wind",
    }
    schedules = {
        (house, split): all_schedule_paths(args.trajectory_root, args.maponly_root, house, split)
        for house in HOUSES for split in ("train", "reserved")
    }
    lengths = {key: schedule_lengths(paths) for key, paths in schedules.items()}
    for path in (*envs.values(), *winds.values(), args.binary):
        if not path.exists():
            raise FileNotFoundError(path)

    args.output_root.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    counts = {"generated": 0, "reused": 0}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [
            pool.submit(
                generate_one, args.binary, row, args.output_root, envs, winds,
                schedules, lengths,
            )
            for row in rows
        ]
        for index, future in enumerate(concurrent.futures.as_completed(futures), start=1):
            result = future.result()
            counts[result["status"]] += 1
            if index % 250 == 0 or index == len(futures):
                elapsed = time.monotonic() - start
                print(
                    f"PF_DEI_V3_BANK_PROGRESS={index}/{len(futures)} "
                    f"generated={counts['generated']} reused={counts['reused']} elapsed_s={elapsed:.1f}",
                    flush=True,
                )

    summary = {
        "contract": "PF_DEI_V3_HISTORICAL_NATIVE_BANK_V1",
        "placement_manifest_sha256": sha256_file(args.manifest),
        "native_multistream_binary_sha256": sha256_file(args.binary),
        "trajectory_schedule_sha256": {
            f"{house}_{split}": [sha256_file(path) for path in schedules[(house, split)]]
            for house in HOUSES for split in ("train", "reserved")
        },
        "trajectory_lengths": {f"{house}_{split}": value for (house, split), value in lengths.items()},
        "row_count": len(rows),
        "generated": counts["generated"],
        "reused": counts["reused"],
        "elapsed_s": time.monotonic() - start,
    }
    summary_path = args.output_root / "bank_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "PF_DEI_V3_HISTORICAL_BANK=PASS "
        f"rows={len(rows)} elapsed_s={summary['elapsed_s']:.1f} "
        f"summary_sha256={sha256_file(summary_path)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

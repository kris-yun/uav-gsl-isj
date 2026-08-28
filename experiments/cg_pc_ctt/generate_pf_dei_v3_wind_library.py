#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
from pathlib import Path

from pf_dei_v3_stream_format import read_wind_multistream


HOUSES = ("H01", "H02", "H03")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def historical_paths(root: Path, house: str) -> list[Path]:
    h = f"House{house[-2:]}"
    return [
        root / h / f"seed{seed}" / "off" / "runtime" / f"{h}_seed{seed}_off_off"
        / "sim_pose_trace.csv"
        for seed in range(10)
    ]


def row_count(path: Path) -> int:
    with path.open(newline="") as source:
        return sum(1 for _ in csv.DictReader(source))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--historical-root", type=Path, required=True)
    parser.add_argument("--maponly-root", type=Path, required=True)
    parser.add_argument("--environment-root", type=Path, required=True)
    parser.add_argument("--h02-environment", type=Path, required=True)
    parser.add_argument("--h02-wind", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
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
    args.output_root.mkdir(parents=True, exist_ok=True)
    summary = {
        "contract": "PF_DEI_V3_NATIVE_WIND_LIBRARY_V1",
        "binary_sha256": sha256_file(args.binary), "houses": {},
    }
    for house in HOUSES:
        paths = historical_paths(args.historical_root, house)
        paths.extend(args.maponly_root / house / "train" / f"trajectory_seed_{seed}.csv" for seed in range(3001, 3021))
        paths.extend(args.maponly_root / house / "reserved" / f"trajectory_seed_{seed}.csv" for seed in range(4001, 4006))
        lengths = [row_count(path) for path in paths]
        output = args.output_root / f"{house}_wind35.bin"
        repeat = args.output_root / f"{house}_wind35.repeat.bin"
        for destination in (output, repeat):
            temp = destination.with_suffix(f".tmp.{os.getpid()}")
            completed = subprocess.run(
                [str(args.binary), str(envs[house]), str(winds[house]), "0.2", str(temp), *(str(path) for path in paths)],
                text=True, capture_output=True, check=False,
            )
            if completed.returncode:
                raise RuntimeError(f"PF_DEI_V3_WIND_GENERATION_FAIL:{house}\n{completed.stdout}\n{completed.stderr}")
            os.replace(temp, destination)
        values = read_wind_multistream(output)
        if [item.shape[0] for item in values] != lengths:
            raise ValueError(f"PF_DEI_V3_WIND_LENGTH_MISMATCH:{house}")
        if output.read_bytes() != repeat.read_bytes():
            raise ValueError(f"PF_DEI_V3_WIND_NONDETERMINISTIC:{house}")
        repeat.unlink()
        summary["houses"][house] = {
            "output": str(output), "sha256": sha256_file(output),
            "trajectory_count": len(paths), "sample_count": sum(lengths),
            "schedule_sha256": [sha256_file(path) for path in paths],
            "schedule_lengths": lengths,
        }
    manifest = args.output_root / "wind_library_manifest.json"
    manifest.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PF_DEI_V3_WIND_LIBRARY=PASS manifest_sha256={sha256_file(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

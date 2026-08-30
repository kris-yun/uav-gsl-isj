#!/usr/bin/env python3
"""TRAIN-only 2-carrier x 2-key x 2-route physical and route-RNG smoke."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

import numpy as np

from ctt_h01_wind_bank_io import first_passage, read_physical, sensor_forward, sha256_file


def run(command: list[str]) -> None:
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode:
        raise RuntimeError("CTT_TINY_SMOKE_COMMAND_FAIL\n" + completed.stdout + completed.stderr)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--placement-manifest", type=Path, required=True)
    parser.add_argument("--native-binary", type=Path, required=True)
    parser.add_argument("--environment", type=Path, required=True)
    parser.add_argument("--wind-dir", type=Path, required=True)
    parser.add_argument("--schedule-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("CTT_TINY_SMOKE_REFUSE_OVERWRITE")
    if os.environ.get("OMP_NUM_THREADS") != "4" or os.environ.get("OMP_DYNAMIC") != "FALSE":
        raise SystemExit("CTT_TINY_SMOKE_OPENMP_CONTRACT_FAIL")
    args.output.mkdir(parents=True)
    payload = json.loads(args.placement_manifest.read_text(encoding="utf-8"))
    rows = [row for row in payload["rows"] if row["house"] == "H01" and row["split"] == "train"]
    carrier_ids = sorted({row["carrier_id"] for row in rows})[:2]
    selected = [row for row in rows if row["carrier_id"] in carrier_ids and int(row["member_id"]) in (0, 1)]
    selected.sort(key=lambda row: (carrier_ids.index(row["carrier_id"]), int(row["member_id"])))
    schedules = [args.schedule_root / "H01" / "reserved" / f"trajectory_seed_{seed}.csv" for seed in (4001, 4002)]
    records = []
    for row in selected:
        target = args.output / f"{row['carrier_id']}_member{int(row['member_id'])}.bin"
        command = [str(args.native_binary), str(args.environment), str(args.wind_dir),
                   repr(float(row["x"])), repr(float(row["y"])), repr(float(row["z"])),
                   str(int(row["transport_seed"])), "0.2", str(target), *(str(path) for path in schedules)]
        run(command)
        streams = read_physical(target)
        if len(streams) != 2 or [len(values) for values in streams] != [1682, 1682]:
            raise ValueError("CTT_TINY_SMOKE_STREAM_CONTRACT_FAIL")
        labels = []
        for physical in streams:
            measured = sensor_forward(physical)
            # Structural first-passage smoke on the first exact 80-sample tape;
            # full schedule semantics remain covered by G0.
            labels.append(first_passage(measured[:80]))
        records.append({"carrier_id": row["carrier_id"], "member": int(row["member_id"]),
                        "transport_seed": int(row["transport_seed"]), "sha256": sha256_file(target),
                        "first_passage_first80": labels})

    # Running the identical physical world with only route 4001 must reproduce
    # the route-4001 stream from the two-route run exactly.
    row = selected[0]
    single = args.output / "route4001_only.bin"
    run([str(args.native_binary), str(args.environment), str(args.wind_dir),
         repr(float(row["x"])), repr(float(row["y"])), repr(float(row["z"])),
         str(int(row["transport_seed"])), "0.2", str(single), str(schedules[0])])
    route_invariant = np.array_equal(read_physical(single)[0], read_physical(args.output / f"{row['carrier_id']}_member0.bin")[0])
    key_diverse = records[0]["sha256"] != records[1]["sha256"]
    rerun = args.output / "deterministic_rerun.bin"
    run([str(args.native_binary), str(args.environment), str(args.wind_dir),
         repr(float(row["x"])), repr(float(row["y"])), repr(float(row["z"])),
         str(int(row["transport_seed"])), "0.2", str(rerun), *(str(path) for path in schedules)])
    deterministic = sha256_file(rerun) == records[0]["sha256"]
    report = {"contract": "CTT_H01_TRAIN_ONLY_TINY_SMOKE_V1", "records": records,
              "route_sampling_rng_invariant": route_invariant,
              "same_key_deterministic": deterministic, "different_train_keys_nonidentical": key_diverse,
              "test_wind_opened": False, "source_rank_read": False,
              "verdict": "CTT_H01_TINY_SMOKE_PASS" if route_invariant and deterministic and key_diverse else "STOP_CTT_H01_TINY_SMOKE_FAIL"}
    (args.output / "TINY_SMOKE_REPORT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(report["verdict"])
    return 0 if report["verdict"].endswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())

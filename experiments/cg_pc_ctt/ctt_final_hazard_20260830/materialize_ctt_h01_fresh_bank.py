#!/usr/bin/env python3
"""Materialize the CTT H01 fresh native-ppm bank for the frozen hazard solver.

Generates 4 fresh wind contexts (10..13) x 210 source carriers x 8 transport
keys = 6720 coherent worlds.  Reuses the production native C++ binaries as the
only writers of physical ppm; this orchestrator is resumable and atomically
publishes each validated shard.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import csv
import json
import os
import subprocess
import time
from pathlib import Path

from ctt_h01_wind_bank_io import read_physical, read_wind, sha256_file


FRESH_CONTEXTS = (10, 11, 12, 13)
FRESH_CONTEXT_CONTRACT = "CTT_H01_FRESH_STATIC_WIND_CONTEXTS_V1"
BANK_CONTRACT = "CTT_H01_FRESH_NATIVE_BANK_V1"


def schedule_length(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as source:
        return sum(1 for _ in csv.DictReader(source))


def validate_stream(path: Path, lengths: list[int]) -> None:
    actual = [int(values.size) for values in read_physical(path)]
    if actual != lengths:
        raise ValueError(f"CTT_H01_STREAM_LENGTH_FAIL:{path}:{actual}:{lengths}")


def validate_wind(path: Path, lengths: list[int]) -> None:
    actual = [int(values.shape[0]) for values in read_wind(path)]
    if actual != lengths:
        raise ValueError(f"CTT_H01_WIND_LENGTH_FAIL:{path}:{actual}:{lengths}")


def run_atomic(command: list[str], temporary: Path, final: Path, validator) -> str:
    if final.is_file():
        validator(final)
        return "reused"
    temporary.parent.mkdir(parents=True, exist_ok=True)
    try:
        completed = subprocess.run(command, text=True, capture_output=True, check=False)
        if completed.returncode != 0:
            raise RuntimeError(
                "CTT_H01_NATIVE_COMMAND_FAIL\nCOMMAND=" + json.dumps(command) +
                "\nSTDOUT=" + completed.stdout + "\nSTDERR=" + completed.stderr)
        validator(temporary)
        os.replace(temporary, final)
    finally:
        temporary.unlink(missing_ok=True)
    return "generated"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--placement-manifest", type=Path, required=True)
    parser.add_argument("--context-manifest", type=Path, required=True)
    parser.add_argument("--native-binary", type=Path, required=True)
    parser.add_argument("--wind-binary", type=Path, required=True)
    parser.add_argument("--environment", type=Path, required=True)
    parser.add_argument("--schedule-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if not 1 <= args.workers <= 12:
        raise SystemExit("CTT_H01_WORKERS_MUST_BE_1_TO_12")

    placements = json.loads(args.placement_manifest.read_text(encoding="utf-8"))
    if placements.get("contract") != "PF_DEI_V3_REGION_PLACEMENT_V1":
        raise SystemExit("CTT_H01_PLACEMENT_CONTRACT_FAIL")
    rows = [row for row in placements["rows"] if row["house"] == "H01" and row["split"] == "train"]
    rows.sort(key=lambda row: (int(row["member_id"]), row["carrier_id"]))
    if len(rows) != 1680 or len({row["carrier_id"] for row in rows}) != 210:
        raise SystemExit(f"CTT_H01_PLACEMENT_COVERAGE_FAIL:{len(rows)}")
    members = {int(row["member_id"]) for row in rows}
    if members != set(range(8)):
        raise SystemExit(f"CTT_H01_PLACEMENT_MEMBER_FAIL:{sorted(members)}")

    context_payload = json.loads(args.context_manifest.read_text(encoding="utf-8"))
    if context_payload.get("contract") != FRESH_CONTEXT_CONTRACT:
        raise SystemExit("CTT_H01_FRESH_WIND_CONTEXT_CONTRACT_FAIL")
    all_contexts = sorted(context_payload["contexts"], key=lambda item: int(item["context"]))
    # PHASE 3 uses only the four confirmatory contexts (10..13); 14,15 are
    # reserved for the later closed-loop development and are not materialized here.
    contexts = [item for item in all_contexts if int(item["context"]) in FRESH_CONTEXTS]
    if [int(item["context"]) for item in contexts] != list(FRESH_CONTEXTS):
        raise SystemExit("CTT_H01_FRESH_WIND_CONTEXT_INDEX_FAIL")
    for item in contexts:
        source = Path(item["original_path"])
        if sha256_file(source) != item["payload_sha256"]:
            raise SystemExit(f"CTT_H01_WIND_HASH_FAIL:{item['context']}")
        for slot in range(11):
            linked = Path(item["wind_dir"]) / f"wind_iteration_{slot}"
            if not linked.is_file() or sha256_file(linked) != item["payload_sha256"]:
                raise SystemExit(f"CTT_H01_WIND_SLOT_FAIL:{item['context']}:{slot}")

    schedules = [args.schedule_root / "H01" / "reserved" / f"trajectory_seed_{seed}.csv"
                 for seed in range(4001, 4006)]
    required = [args.native_binary, args.wind_binary, args.environment, args.placement_manifest,
                args.context_manifest, *schedules]
    for path in required:
        if not path.is_file():
            raise FileNotFoundError(path)
    lengths = [schedule_length(path) for path in schedules]
    output = args.output_root
    if output.exists() and not (output / "IN_PROGRESS").is_file():
        raise SystemExit(f"CTT_H01_REFUSE_NONRESUMABLE_OUTPUT:{output}")
    output.mkdir(parents=True, exist_ok=True)
    (output / "IN_PROGRESS").write_text("fresh_bank\n")

    started = time.monotonic()
    wind_counts = {"generated": 0, "reused": 0}
    for item in contexts:
        context = int(item["context"])
        final = output / f"context_{context:02d}" / "exact_wind_routes.bin"
        temporary = final.with_suffix(f".tmp.{os.getpid()}")
        command = [str(args.wind_binary), str(args.environment), item["wind_dir"], "0.2",
                   str(temporary), *(str(path) for path in schedules)]
        wind_counts[run_atomic(command, temporary, final, lambda p: validate_wind(p, lengths))] += 1

    def generate(item, row):
        context = int(item["context"])
        member = int(row["member_id"])
        final = output / f"context_{context:02d}" / f"member_{member:02d}" / f"{row['carrier_id']}.bin"
        temporary = final.with_suffix(f".tmp.{os.getpid()}")
        command = [
            str(args.native_binary), str(args.environment), item["wind_dir"],
            repr(float(row["x"])), repr(float(row["y"])), repr(float(row["z"])),
            str(int(row["transport_seed"])), "0.2", str(temporary),
            *(str(path) for path in schedules),
        ]
        return run_atomic(command, temporary, final, lambda p: validate_stream(p, lengths))

    tasks = [(item, row) for item in contexts for row in rows]
    counts = {"generated": 0, "reused": 0}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(generate, item, row) for item, row in tasks]
        for index, future in enumerate(concurrent.futures.as_completed(futures), start=1):
            counts[future.result()] += 1
            if index % 500 == 0 or index == len(tasks):
                print(f"CTT_H01_FRESH_BANK_PROGRESS={index}/{len(tasks)} generated={counts['generated']} reused={counts['reused']}", flush=True)

    files = sorted(output.glob("context_*/member_*/*.bin"))
    expected_files = 210 * 4 * 8
    if len(files) != expected_files:
        raise SystemExit(f"CTT_H01_FRESH_BANK_FILE_COUNT_FAIL:{len(files)}:{expected_files}")
    ordered = []
    total_bytes = 0
    for path in files:
        ordered.append(f"{path.relative_to(output).as_posix()}\t{sha256_file(path)}")
        total_bytes += path.stat().st_size
    (output / "FILE_SHA256.tsv").write_text("\n".join(ordered) + "\n", encoding="utf-8")
    summary = {
        "contract": BANK_CONTRACT,
        "scientific_gate_eligible": True,
        "contexts": list(FRESH_CONTEXTS),
        "carrier_count": 210,
        "transport_member_count": 8,
        "route_seeds": list(range(4001, 4006)),
        "file_count": len(files),
        "generated": counts["generated"],
        "reused": counts["reused"],
        "wind": wind_counts,
        "total_bytes": total_bytes,
        "elapsed_s": time.monotonic() - started,
        "native_binary_sha256": sha256_file(args.native_binary),
        "wind_binary_sha256": sha256_file(args.wind_binary),
        "environment_sha256": sha256_file(args.environment),
        "placement_manifest_sha256": sha256_file(args.placement_manifest),
        "context_manifest_sha256": sha256_file(args.context_manifest),
        "schedule_sha256": [sha256_file(path) for path in schedules],
        "verdict": "CTT_H01_FRESH_BANK_MATERIALIZATION_PASS",
    }
    (output / "bank_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "IN_PROGRESS").unlink()
    print(summary["verdict"] + " " + json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

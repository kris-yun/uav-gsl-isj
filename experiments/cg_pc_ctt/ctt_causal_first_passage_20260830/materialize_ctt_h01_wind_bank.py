#!/usr/bin/env python3
"""Materialize the frozen H01 native-ppm wind-conditioned first-passage bank.

The production native C++ binary remains the only writer of physical ppm.
This orchestrator is resumable and atomically publishes each validated shard.
The optional ``--smoke`` mode is infrastructure-only and cannot produce a
scientific gate result.
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


EXPECTED_SPLIT = {
    0: "train", 1: "test", 2: "test", 3: "train", 4: "validation",
    5: "train", 6: "train", 7: "validation", 8: "train", 9: "train",
}

# Generate development contexts before the untouched test contexts.  This is
# an orchestration-only ordering: it neither changes the bank membership nor
# any native simulation input.  It lets the frozen train/validation gates run
# while the two final test contexts are still being materialized, and avoids
# opening test assets during implementation qualification.
FULL_GENERATION_ORDER = (0, 3, 5, 6, 8, 9, 4, 7, 1, 2)


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
                "\nSTDOUT=" + completed.stdout + "\nSTDERR=" + completed.stderr
            )
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
    parser.add_argument("--smoke", action="store_true")
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
    if context_payload.get("contract") != "CTT_H01_NATIVE_STATIC_WIND_CONTEXTS_V1":
        raise SystemExit("CTT_H01_WIND_CONTEXT_CONTRACT_FAIL")
    contexts = sorted(context_payload["contexts"], key=lambda item: int(item["context"]))
    if [int(item["context"]) for item in contexts] != list(range(10)):
        raise SystemExit("CTT_H01_WIND_CONTEXT_INDEX_FAIL")
    for item in contexts:
        index = int(item["context"])
        if item["split"] != EXPECTED_SPLIT[index]:
            raise SystemExit(f"CTT_H01_WIND_SPLIT_FAIL:{index}")
        source = Path(item["original_path"])
        if sha256_file(source) != item["payload_sha256"]:
            raise SystemExit(f"CTT_H01_WIND_HASH_FAIL:{index}")
        for slot in range(11):
            linked = Path(item["wind_dir"]) / f"wind_iteration_{slot}"
            if not linked.is_file() or sha256_file(linked) != item["payload_sha256"]:
                raise SystemExit(f"CTT_H01_WIND_SLOT_FAIL:{index}:{slot}")

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
    (output / "IN_PROGRESS").write_text("infrastructure_smoke\n" if args.smoke else "full_bank\n")

    context_by_index = {int(item["context"]): item for item in contexts}
    selected_contexts = contexts[:1] if args.smoke else [context_by_index[index] for index in FULL_GENERATION_ORDER]
    if args.smoke:
        first_id = rows[0]["carrier_id"]
        selected_rows = [row for row in rows if row["carrier_id"] == first_id and int(row["member_id"]) in (0, 1)]
    else:
        selected_rows = rows

    started = time.monotonic()
    wind_counts = {"generated": 0, "reused": 0}
    for item in selected_contexts:
        context = int(item["context"])
        final = output / f"context_{context:02d}" / "exact_wind_routes.bin"
        temporary = final.with_suffix(f".tmp.{os.getpid()}")
        command = [str(args.wind_binary), str(args.environment), item["wind_dir"], "0.2",
                   str(temporary), *(str(path) for path in schedules)]
        state = run_atomic(command, temporary, final, lambda path: validate_wind(path, lengths))
        wind_counts[state] += 1

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
        return run_atomic(command, temporary, final, lambda path: validate_stream(path, lengths))

    tasks = [(item, row) for item in selected_contexts for row in selected_rows]
    counts = {"generated": 0, "reused": 0}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(generate, item, row) for item, row in tasks]
        for index, future in enumerate(concurrent.futures.as_completed(futures), start=1):
            counts[future.result()] += 1
            if index % 100 == 0 or index == len(tasks):
                print(f"CTT_H01_BANK_PROGRESS={index}/{len(tasks)} generated={counts['generated']} reused={counts['reused']}", flush=True)

    files = sorted(output.glob("context_*/member_*/*.bin"))
    expected_files = 2 if args.smoke else 16800
    if len(files) != expected_files:
        raise SystemExit(f"CTT_H01_BANK_FILE_COUNT_FAIL:{len(files)}:{expected_files}")
    ordered = []
    total_bytes = 0
    for path in files:
        relative = path.relative_to(output).as_posix()
        ordered.append(f"{relative}\t{sha256_file(path)}")
        total_bytes += path.stat().st_size
    (output / "FILE_SHA256.tsv").write_text("\n".join(ordered) + "\n", encoding="utf-8")
    summary = {
        "contract": "CTT_H01_WIND_CONDITIONED_NATIVE_BANK_SMOKE_V1" if args.smoke else "CTT_H01_WIND_CONDITIONED_NATIVE_BANK_V1",
        "scientific_gate_eligible": not args.smoke,
        "contexts": [int(item["context"]) for item in selected_contexts],
        "carrier_count": 1 if args.smoke else 210,
        "transport_member_count": 2 if args.smoke else 8,
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
        "verdict": "CTT_H01_WIND_BANK_SMOKE_PASS" if args.smoke else "CTT_H01_WIND_BANK_MATERIALIZATION_PASS",
    }
    (output / "bank_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "IN_PROGRESS").unlink()
    print(summary["verdict"] + " " + json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

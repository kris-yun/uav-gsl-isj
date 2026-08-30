#!/usr/bin/env python3
"""Fail-closed live monitor for the CTT H01 native bank materialization."""

from __future__ import annotations

import json
import argparse
import os
import shutil
import subprocess
import time
from pathlib import Path

from ctt_h01_wind_bank_io import read_physical, read_wind


EXPECTED_LENGTHS = [1682] * 5
INTERVAL_S = 20
STALL_S = 180


def fail(state: Path, reason: str, detail: dict) -> int:
    payload = {"status": "FAIL", "reason": reason, "time": time.time(), **detail}
    (state / "MONITOR_FAIL.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print("CTT_H01_BANK_MONITOR=FAIL " + json.dumps(payload, sort_keys=True), flush=True)
    return 2


def native_processes(bank: Path) -> list[int]:
    result = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            executable = (entry / "exe").resolve().name
            command = (entry / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace")
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if executable == "pf_dei_v3_native_multistream" and str(bank) in command:
            result.append(int(entry.name))
    return result


def check_process_contract(pids: list[int]) -> tuple[bool, list[dict]]:
    rows = []
    valid = len(pids) <= 3
    for pid in pids:
        try:
            environment = dict(item.split(b"=", 1) for item in
                               Path(f"/proc/{pid}/environ").read_bytes().split(b"\0") if b"=" in item)
            omp = environment.get(b"OMP_NUM_THREADS", b"").decode()
            dynamic = environment.get(b"OMP_DYNAMIC", b"").decode()
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        rows.append({"pid": pid, "omp_num_threads": omp, "omp_dynamic": dynamic})
        valid &= omp == "4" and dynamic == "FALSE"
    return valid, rows


def validate_sample(paths: list[Path]) -> None:
    for path in paths:
        streams = read_physical(path)
        if [len(values) for values in streams] != EXPECTED_LENGTHS:
            raise ValueError(f"stream_lengths:{path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bank", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    args = parser.parse_args()
    bank = args.bank.resolve()
    state = args.state.resolve()
    if state.exists():
        raise SystemExit("CTT_H01_BANK_MONITOR_REFUSE_EXISTING")
    state.mkdir(parents=True)
    previous = -1
    last_change = time.monotonic()
    iteration = 0
    with (state / "monitor.jsonl").open("w", encoding="utf-8", buffering=1) as log:
        while True:
            iteration += 1
            physical = sorted(bank.glob("context_*/member_*/*.bin"), key=lambda path: path.stat().st_mtime_ns)
            winds = sorted(bank.glob("context_*/exact_wind_routes.bin"))
            count = len(physical)
            if count < previous:
                return fail(state, "FILE_COUNT_DECREASED", {"previous": previous, "current": count})
            if count > previous:
                previous = count
                last_change = time.monotonic()
            pids = native_processes(bank)
            process_ok, process_rows = check_process_contract(pids)
            temporary = list(bank.glob("context_*/member_*/*.tmp.*"))
            stale = []
            for path in temporary:
                try:
                    age = time.time() - path.stat().st_mtime
                except FileNotFoundError:
                    # The materializer commits a completed world by atomically
                    # renaming its temporary file; disappearance between glob
                    # and stat is therefore expected, not a stale-file error.
                    continue
                if age > STALL_S:
                    stale.append(str(path))
            usage = shutil.disk_usage("/dev/shm")
            payload = {
                "iteration": iteration, "time": time.time(), "physical_files": count,
                "wind_files": len(winds), "native_processes": process_rows,
                "temporary_files": len(temporary), "stale_temporary": stale,
                "shm_free_bytes": usage.free,
            }
            log.write(json.dumps(payload, sort_keys=True) + "\n")
            if not process_ok:
                return fail(state, "OPENMP_OR_WORKER_CONTRACT_FAIL", payload)
            if stale:
                return fail(state, "STALE_TEMPORARY_FILE", payload)
            if usage.free < 1024 ** 3:
                return fail(state, "SHM_FREE_BELOW_1G", payload)
            try:
                sample = physical[-3:] + physical[:1]
                validate_sample(list(dict.fromkeys(sample)))
                for path in winds:
                    if [len(values) for values in read_wind(path)] != EXPECTED_LENGTHS:
                        raise ValueError(f"wind_lengths:{path}")
            except Exception as error:
                return fail(state, "BINARY_VALIDATION_FAIL", {**payload, "error": repr(error)})

            complete = (bank / "bank_summary.json").is_file() and not (bank / "IN_PROGRESS").exists()
            if complete:
                summary = json.loads((bank / "bank_summary.json").read_text(encoding="utf-8"))
                manifest_lines = (bank / "FILE_SHA256.tsv").read_text(encoding="utf-8").splitlines()
                if not (count == 16800 and len(winds) == 10 and len(manifest_lines) == 16800 and
                        summary.get("verdict") == "CTT_H01_WIND_BANK_MATERIALIZATION_PASS"):
                    return fail(state, "FINAL_BANK_CONTRACT_FAIL", {**payload, "summary": summary,
                                                                     "manifest_lines": len(manifest_lines)})
                final = {"status": "PASS", **payload, "summary": summary,
                         "manifest_lines": len(manifest_lines)}
                (state / "MONITOR_PASS.json").write_text(json.dumps(final, indent=2, sort_keys=True) + "\n")
                print("CTT_H01_BANK_MONITOR=PASS", flush=True)
                return 0
            materializer = subprocess.run(
                ["pgrep", "-f", f"materialize_ctt_h01_wind_bank.py.*{bank.name}"],
                capture_output=True, check=False,
            ).returncode == 0
            if not materializer:
                return fail(state, "MATERIALIZER_EXITED_BEFORE_SUMMARY", payload)
            if time.monotonic() - last_change > STALL_S:
                return fail(state, "PROGRESS_STALLED", payload)
            time.sleep(INTERVAL_S)


if __name__ == "__main__":
    raise SystemExit(main())

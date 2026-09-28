"""Resume the 72 frozen OPEN runs, archiving each raw realization on host C.

Run only after the source-blind manifest, writer time map, and destination disk
have been audited.  A host checksum and tar-member check precede VM cleanup.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parent
HOST_ARCHIVE = Path(r"C:\Users\50176\Desktop\vm数据\BRG_V1_OPEN_CONTINUOUS_20260928")
HOST_RECEIPTS = ROOT / "receipts"
VM = "zyc@192.168.111.128"
KEY = Path.home() / ".ssh" / "id_ed25519_vm"
VM_CODE = "/home/zyc/brg_v1_recovery_20260928"
VM_SCRATCH = "/home/zyc/brg_v1_recovery_scratch_20260928"
ZSTD = Path(r"D:\Anaconda\Library\bin\zstd.exe")
LOCK_SHA = "891a01d580ebc8ddbfa20b4ec2e3e0462cbe54b49232d65c1a36d4982ff4b2fe"


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def command(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, text=True, capture_output=True)
    if check and result.returncode:
        raise RuntimeError(f"command failed {args[0]} ({result.returncode}): {result.stderr[-2000:]} {result.stdout[-1000:]}")
    return result


def ssh(command_text: str, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return command(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8",
                    "-i", str(KEY), VM, command_text], check=check)


def result_json(result: subprocess.CompletedProcess[str]) -> dict:
    return json.loads(result.stdout.strip())


def validate_archive(path: Path, run_id: str) -> int:
    command([str(ZSTD), "-t", str(path)])
    proc = subprocess.Popen([str(ZSTD), "-dc", str(path)], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    assert proc.stdout is not None
    member_result = subprocess.run(["tar", "-tf", "-"], stdin=proc.stdout,
                                   text=True, capture_output=True)
    proc.stdout.close()
    proc.wait()
    assert proc.stderr is not None
    zstd_err = proc.stderr.read()
    if proc.returncode or member_result.returncode:
        raise RuntimeError(f"archive member listing failed: {zstd_err} {member_result.stderr}")
    members = member_result.stdout.splitlines()
    prefix = f"{run_id}/realization/iteration_"
    ids = sorted(int(name[len(prefix):]) for name in members if name.startswith(prefix)
                 and re.fullmatch(r"\d+", name[len(prefix):]))
    if ids != list(range(566)):
        raise RuntimeError(f"native frame member mismatch: {len(ids)}")
    for required in ("RAW_SHA256.tsv", "RUN_METADATA.json", "generation.log"):
        if f"{run_id}/{required}" not in members:
            raise RuntimeError(f"archive missing {required}")
    if sum(f"{run_id}/realization/wind/wind_iteration_{i}" in members
           for i in range(11)) != 11:
        raise RuntimeError("archive missing frozen wind files")
    return len(ids)


def run_one(lock: dict, ordinal: int) -> dict:
    run = lock["runs"][ordinal - 1]
    run_id = run["run_id"]
    if run["ordinal"] != ordinal or not re.fullmatch(r"[A-Za-z0-9_,.\-]+", run_id):
        raise RuntimeError("unsafe run identity")
    path = HOST_ARCHIVE / f"{run_id}.tar.zst"
    receipt_path = HOST_RECEIPTS / f"{ordinal:03d}_{run_id}.json"
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        if receipt["archive_sha256"] != sha(path):
            raise RuntimeError("existing archived run checksum drift")
        return receipt
    remote_dir = f"{VM_SCRATCH}/{run_id}"
    if ssh(f"test -d {remote_dir}", check=False).returncode != 0:
        ready = result_json(ssh(f"bash {VM_CODE}/run_one_vm.sh preflight {ordinal}"))
        if ready["status"] != "PREFLIGHT_PASS":
            raise RuntimeError("frozen run preflight failed")
        started = time.monotonic()
        generated = result_json(ssh(f"bash {VM_CODE}/run_one_vm.sh run-one {ordinal}"))
        if generated["status"] != "RAW_NATIVE_FRAMES_PRESERVED":
            raise RuntimeError("native frame generation failed")
        print(f"[{ordinal}/72] generated 566 frames in {time.monotonic()-started:.1f}s", flush=True)
    remote = result_json(ssh(f"python3 {VM_CODE}/archive_one_vm.py package {ordinal}"))
    if remote["status"] != "VM_ARCHIVE_READY" or remote["run_id"] != run_id:
        raise RuntimeError("VM archive identity mismatch")
    if not path.exists():
        command(["scp", "-q", "-i", str(KEY), f"{VM}:{remote['archive']}", str(path)])
    actual = sha(path)
    if path.stat().st_size != remote["archive_bytes"] or actual != remote["archive_sha256"]:
        raise RuntimeError("host/VM archive byte or checksum mismatch; preserving both copies")
    frames = validate_archive(path, run_id)
    receipt = {"ordinal": ordinal, "run_id": run_id, "house": run["house"],
               "wind": run["wind"], "source_id": run["source_id"],
               "historical_seed": run["historical_seed"], "split": run["split"],
               "archive_path": str(path), "archive_bytes": path.stat().st_size,
               "archive_sha256": actual, "native_frames": frames,
               "raw_inventory_sha256": remote["raw_inventory_sha256"],
               "frozen_manifest_sha256": LOCK_SHA,
               "time_map_sha256": sha(ROOT / "RESULT_TIME_MAP_300S.tsv"),
               "new_gaden_execution": True, "new_independent_realization": False}
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    cleanup = result_json(ssh(f"python3 {VM_CODE}/archive_one_vm.py cleanup {ordinal} {actual}"))
    if cleanup["status"] != "VERIFIED_VM_WORK_COPY_REMOVED":
        raise RuntimeError("verified scratch cleanup did not finish")
    print(f"[{ordinal}/72] archived {path.stat().st_size/1e6:.1f} MB, SHA256 {actual[:12]}", flush=True)
    return receipt


def main() -> None:
    if sha(ROOT / "FROZEN_RUN_MANIFEST.json") != LOCK_SHA:
        raise RuntimeError("frozen run manifest drift")
    lock = json.loads((ROOT / "FROZEN_RUN_MANIFEST.json").read_text())
    if len(lock["runs"]) != 72:
        raise RuntimeError("72-run budget drift")
    if not KEY.is_file() or not ZSTD.is_file() or not (ROOT / "RESULT_TIME_MAP_300S.tsv").is_file():
        raise RuntimeError("missing host key, zstd, or audited frame time map")
    HOST_ARCHIVE.mkdir(parents=True, exist_ok=True)
    HOST_RECEIPTS.mkdir(exist_ok=True)
    if shutil.disk_usage(HOST_ARCHIVE).free < 10_000_000_000:
        raise RuntimeError("host archive free space <10 GB")
    begin = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 72
    if not 1 <= begin <= end <= 72:
        raise RuntimeError("range escapes frozen 72-run budget")
    for ordinal in range(begin, end + 1):
        run_one(lock, ordinal)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Delete only explicitly authorized retired outputs or old ROS log files.

Run on the VM with ``plan`` first. ``execute`` requires the plan digest so a
changed directory cannot be deleted under an earlier inventory. This script
never touches GADEN inputs, original plume data, or ROS2 src/build/install.
"""

import argparse
import hashlib
import json
import os
import shutil
import stat
import sys
from datetime import datetime
from pathlib import Path


CG_ROOT = Path("/home/zyc/CG_PC_CTT_V3_ORR_FULL60_PACKAGE_20260827")
ME_ROOT = Path("/home/zyc/meaci_v12_generalization_20260825_r1")
ROS_LOG_ROOT = Path("/home/zyc/.ros/log")
CG_DIRS = tuple(CG_ROOT / "results" / house for house in ("House01", "House02", "House03"))
ME_DIR_NAMES = (
    "House01_seed418310734_off_off",
    "House01_seed418310734_on_rc_sd_tfei_v12",
    "House02_seed661532441_off_off",
    "House02_seed661532441_on_rc_sd_tfei_v12",
    "House03_seed538848658_off_off",
    "House03_seed538848658_on_rc_sd_tfei_v12",
)
ME_DIRS = tuple(ME_ROOT / name for name in ME_DIR_NAMES)
ROS_CUTOFF = datetime(2026, 9, 27).timestamp()


def check_frozen_decisions() -> None:
    cg = json.loads((CG_ROOT / "results/_batch/MULTISEED_VERDICT.json").read_text())
    me = json.loads((ME_ROOT / "V12_M_HELDOUT_GENERALIZATION_RESULT.json").read_text())
    if cg.get("verdict") != "CG_PC_CTT_MULTI_SEED_NOT_GO":
        raise RuntimeError("CG-PC-CTT frozen decision mismatch")
    if me.get("verdict") != "V12_M_HELDOUT_GENERALIZATION_NO_GO":
        raise RuntimeError("MEACI frozen decision mismatch")


def check_target(path: Path, parent: Path) -> None:
    if path.is_symlink() or not path.exists():
        raise RuntimeError(f"Missing or symlink target: {path}")
    if path.resolve() != path or path.parent.resolve() != parent:
        raise RuntimeError(f"Unexpected resolved path: {path}")
    if path == parent or parent not in path.parents:
        raise RuntimeError(f"Target escapes allowlist parent: {path}")


def describe_tree(path: Path, digest) -> tuple[int, int, int]:
    files = 0
    apparent_bytes = 0
    allocated_bytes = 0
    for current, dirs, names in os.walk(path, topdown=True, followlinks=False):
        dirs.sort()
        for name in sorted(dirs + names):
            child = Path(current) / name
            mode = child.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise RuntimeError(f"Symlink within deletion target: {child}")
            if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                raise RuntimeError(f"Nonregular entry within deletion target: {child}")
            info = child.stat(follow_symlinks=False)
            digest.update(f"{child}\t{info.st_size}\t{info.st_mtime_ns}\n".encode())
            if stat.S_ISREG(mode):
                files += 1
                apparent_bytes += info.st_size
            allocated_bytes += info.st_blocks * 512
    root_info = path.stat()
    digest.update(f"{path}\t{root_info.st_size}\t{root_info.st_mtime_ns}\n".encode())
    allocated_bytes += root_info.st_blocks * 512
    return files, apparent_bytes, allocated_bytes


def inventory(scope: str) -> dict:
    digest = hashlib.sha256()
    entries = []
    if scope == "experiment":
        check_frozen_decisions()
        for path in CG_DIRS:
            check_target(path, CG_ROOT / "results")
        for path in ME_DIRS:
            check_target(path, ME_ROOT)
        for path in CG_DIRS + ME_DIRS:
            files, apparent, allocated = describe_tree(path, digest)
            entries.append({
                "path": str(path), "file_count": files,
                "apparent_bytes": apparent, "allocated_bytes": allocated,
                "reason": "frozen NO-GO per-run derived output",
            })
    elif scope == "ros_log":
        if ROS_LOG_ROOT.is_symlink() or ROS_LOG_ROOT.resolve() != ROS_LOG_ROOT:
            raise RuntimeError("ROS log root is not the exact canonical directory")
        for directory, dirs, names in os.walk(ROS_LOG_ROOT, followlinks=False):
            dirs.sort()
            for name in sorted(names):
                path = Path(directory) / name
                info = path.lstat()
                if not stat.S_ISREG(info.st_mode) or path.suffix != ".log":
                    continue
                if info.st_mtime >= ROS_CUTOFF:
                    continue
                if ROS_LOG_ROOT not in path.parents:
                    raise RuntimeError(f"ROS log path escapes allowlist: {path}")
                digest.update(f"{path}\t{info.st_size}\t{info.st_mtime_ns}\n".encode())
                entries.append({
                    "path": str(path), "file_count": 1,
                    "apparent_bytes": info.st_size,
                    "allocated_bytes": info.st_blocks * 512,
                    "reason": "ROS .log older than 2026-09-27; recent logs retained",
                })
        entries.sort(key=lambda entry: entry["path"])
    else:
        raise RuntimeError(f"Unknown scope {scope}")
    return {
        "scope": scope,
        "manifest_sha256": digest.hexdigest(),
        "target_count": len(entries),
        "file_count": sum(entry["file_count"] for entry in entries),
        "apparent_bytes": sum(entry["apparent_bytes"] for entry in entries),
        "allocated_bytes": sum(entry["allocated_bytes"] for entry in entries),
        "entries": entries,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("plan", "execute"))
    parser.add_argument("scope", choices=("experiment", "ros_log"))
    parser.add_argument("--expect", default="")
    args = parser.parse_args()
    report = inventory(args.scope)
    if args.action == "plan":
        if args.scope == "ros_log":
            report = {key: value for key, value in report.items() if key != "entries"}
        print(json.dumps(report, sort_keys=True))
        return
    if not args.expect or report["manifest_sha256"] != args.expect:
        raise RuntimeError("Plan digest mismatch; no deletion performed")
    print(json.dumps({key: value for key, value in report.items() if key != "entries"}), flush=True)
    for entry in report["entries"]:
        path = Path(entry["path"])
        if args.scope == "experiment":
            shutil.rmtree(path)
        else:
            path.unlink()
        if path.exists():
            raise RuntimeError(f"Deletion failed: {path}")
        print(json.dumps({"deleted": entry}, sort_keys=True), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

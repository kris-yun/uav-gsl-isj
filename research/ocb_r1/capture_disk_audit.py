#!/usr/bin/env python3
"""Read-only OCB-R1 disk inventory; never invokes a simulator or deletes files."""

import argparse
import csv
import datetime as dt
import subprocess
from pathlib import Path


def remote(command: str) -> str:
    result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "zyc@192.168.111.128", command],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def classify(path: str) -> tuple[str, str]:
    if path.startswith((
        "/home/zyc/ros2_ws/src",
        "/home/zyc/ros2_ws/install",
        "/home/zyc/ros2_ws/build",
    )):
        return "KEEP", "Protected ROS2 source/runtime/build"
    if path.startswith("/home/zyc/.ros/log"):
        return "SAFE_LOG", "ROS runtime log; retain recent verification logs"
    if path.startswith("/home/zyc/ros2_ws/log"):
        return "SAFE_LOG", "Colcon log; retain latest build/list provenance"
    if path.startswith("/var/log/journal"):
        return "SAFE_LOG", "Systemd journal; vacuum requires sudo"
    if path.startswith(("/home/zyc/.cache/pip", "/var/cache/apt/archives")):
        return "SAFE_CACHE", "Downloaded package cache"
    if path.startswith("/tmp/"):
        return "UNKNOWN_DO_NOT_TOUCH", "Temporary path requires owner/process check"
    if path.startswith("/home/zyc/.local"):
        return "KEEP", "Installed user Python packages"
    if path.startswith("/home/zyc/uav-gsl-isj"):
        return "KEEP", "Research repository; not a cleanup target"
    if path.startswith("/home/zyc/ros2_ws"):
        return "UNKNOWN_DO_NOT_TOUCH", "ROS2 workspace contents; no cleanup authorization"
    if path.startswith("/home/zyc/"):
        return "MOVABLE_EXPERIMENT_OUTPUT", "Historical output or archive; no verified backup for this action"
    return "UNKNOWN_DO_NOT_TOUCH", "Not on the low-risk cleanup allowlist"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("BEFORE", "AFTER"))
    args = parser.parse_args()
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    rows: list[list[str]] = []

    for line in remote("df -B1 --output=source,size,used,avail,pcent,target / | tail -n +2").splitlines():
        source, size, used, available, percent, target = line.split()
        rows.extend([
            [stamp, args.phase, "filesystem_total", target, size, "KEEP", source],
            [stamp, args.phase, "filesystem_used", target, used, "KEEP", percent],
            [stamp, args.phase, "filesystem_available", target, available, "KEEP", source],
        ])
    for line in remote("df -i / | tail -n +2").splitlines():
        source, total, used, available, percent, target = line.split()
        rows.extend([
            [stamp, args.phase, "inode_total", target, total, "KEEP", source],
            [stamp, args.phase, "inode_used", target, used, "KEEP", percent],
            [stamp, args.phase, "inode_available", target, available, "KEEP", source],
        ])

    roots = "/home/zyc /home/zyc/ros2_ws /var /tmp"
    for line in remote(f"du -x -B1 -d1 {roots} 2>/dev/null || true").splitlines():
        size, path = line.split("\t", 1)
        category, reason = classify(path)
        rows.append([stamp, args.phase, "directory", path, size, category, reason])

    for line in remote(
        "find /home/zyc -xdev -type f -size +100M -printf '%s\\t%p\\n' "
        "2>/dev/null | sort -nr | head -100"
    ).splitlines():
        size, path = line.split("\t", 1)
        category, reason = classify(path)
        rows.append([stamp, args.phase, "large_file", path, size, category, reason])

    for path in (
        "/home/zyc/.cache",
        "/home/zyc/.cache/pip",
        "/home/zyc/.ros/log",
        "/home/zyc/ros2_ws/log",
        "/var/log/journal",
        "/var/cache/apt/archives",
        "/var/tmp",
    ):
        text = remote(f"du -x -B1 -s {path} 2>/dev/null || true").strip()
        if text:
            size = text.split("\t", 1)[0]
            category, reason = classify(path)
            rows.append([stamp, args.phase, "specific_path", path, size, category, reason])

    output = Path("evidence/ocb_r1") / f"DISK_USAGE_{args.phase}.tsv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(("captured_utc", "phase", "item_type", "path", "bytes_or_count", "category", "reason"))
        writer.writerows(rows)
    print(f"{output}: {len(rows)} rows")


if __name__ == "__main__":
    main()

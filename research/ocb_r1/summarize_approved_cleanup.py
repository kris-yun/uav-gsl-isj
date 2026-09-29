#!/usr/bin/env python3
"""Summarize the explicitly approved OCB-R1 cleanup from saved audit records."""

import csv
import datetime as dt
import json
from pathlib import Path


E = Path("evidence/ocb_r1")
R = E / "retired_experiments"
STAMP = dt.datetime.now(dt.timezone.utc).isoformat()


def records(path: Path):
    with path.open(encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def tsv(path: Path, header, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(header)
        writer.writerows(rows)


experiment = list(records(R / "DELETE_EXECUTION_EXPERIMENT.jsonl"))
ros = list(records(E / "ROS_LOG_DELETE_EXECUTION.jsonl"))
assert experiment[0]["target_count"] == 9
assert experiment[0]["file_count"] == 3581
assert len(experiment[1:]) == 9
assert ros[0]["file_count"] == 69625
assert len(ros[1:]) == 69625

before_journal = {}
for line in (E / "JOURNAL_FILES_BEFORE.tsv").read_text(encoding="utf-8-sig").splitlines()[1:]:
    if line.strip():
        size, path = line.split("\t", 1)
        before_journal[path] = int(size)
after_journal = {}
for line in (E / "JOURNAL_FILES_AFTER_APPROVED_CLEANUP.tsv").read_text(encoding="utf-8-sig").splitlines():
    if line.strip():
        size, path = line.split("\t", 1)
        after_journal[path] = int(size)
deleted_journal = {p: b for p, b in before_journal.items() if p not in after_journal}

cleaned = []
retired = []
for row in experiment[1:]:
    item = row["deleted"]
    path = item["path"]
    is_cg = "CG_PC_CTT" in path
    name = "CG-PC-CTT" if is_cg else "MEACI V12"
    decision = "CG_PC_CTT_MULTI_SEED_NOT_GO" if is_cg else "V12_M_HELDOUT_GENERALIZATION_NO_GO"
    branch = "codex/v3-orr-integrated-20260827" if is_cg else "not recorded in frozen VM snapshot"
    commit = "172968b0d18d32e81f7059519f467f7b1ec5b6b6" if is_cg else "not recorded in frozen VM snapshot"
    retained = str(R / ("cg_pc_ctt" if is_cg else "meaci_v12"))
    cleaned.append((STAMP, path, item["allocated_bytes"], "DELETE_DERIVED_INVALID_BASELINE", item["reason"]))
    retired.append((name, path, decision, branch, commit, retained, path, item["allocated_bytes"], "Per-run derived output; final verdict, config, scripts and key hashes retained"))

for row in ros[1:]:
    item = row["deleted"]
    cleaned.append((STAMP, item["path"], item["allocated_bytes"], "SAFE_LOG", "ROS runtime .log predating 2026-09-27; recent logs retained"))
for path, size in sorted(deleted_journal.items()):
    cleaned.append((STAMP, path, size, "SAFE_LOG", "Archived systemd journal removed by vacuum-size=200M"))
cleaned.append((STAMP, "/var/cache/apt/archives", 0, "SAFE_CACHE", "apt clean; cache was approximately 132 KiB; exact path delta not captured"))
cleaned.append((STAMP, "/home/zyc/.cache/pip", 0, "SAFE_CACHE", "pip cache purge removed two HTTP cache entries, approximately 13 KiB"))

tsv(E / "CLEANED_PATHS.tsv", ("deleted_utc", "path", "size_bytes", "category", "reason"), cleaned)
tsv(E / "RETIRED_EXPERIMENT_EVIDENCE.tsv", ("experiment", "original_path", "decision", "branch", "commit", "retained_files", "deleted_path", "deleted_allocated_bytes", "reason"), retired)

print(json.dumps({
    "experiment_dirs": len(experiment) - 1,
    "experiment_allocated_bytes": experiment[0]["allocated_bytes"],
    "ros_logs": len(ros) - 1,
    "ros_allocated_bytes": ros[0]["allocated_bytes"],
    "journal_files": len(deleted_journal),
    "journal_apparent_bytes": sum(deleted_journal.values()),
    "cleaned_rows": len(cleaned),
}, sort_keys=True))

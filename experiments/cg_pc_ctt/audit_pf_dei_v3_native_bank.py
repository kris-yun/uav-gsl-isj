#!/usr/bin/env python3
"""Exhaustive integrity/hash audit of a completed frozen PF-DEI V3 bank."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from pf_dei_v3_stream_format import read_multistream


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative_shard(row: dict) -> Path:
    return (
        Path(row["house"]) / row["split"] / f"member_{int(row['member_id']):02d}"
        / f"{row['carrier_id']}.bin"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--placement-manifest", type=Path, required=True)
    parser.add_argument("--bank-root", type=Path, required=True)
    args = parser.parse_args()
    placement = json.loads(args.placement_manifest.read_text(encoding="utf-8"))
    bank_summary_path = args.bank_root / "bank_summary.json"
    bank_summary = json.loads(bank_summary_path.read_text(encoding="utf-8"))
    if placement.get("contract") != "PF_DEI_V3_REGION_PLACEMENT_V1":
        raise SystemExit("PF_DEI_V3_BANK_AUDIT_BAD_PLACEMENT_CONTRACT")
    if bank_summary.get("contract") != "PF_DEI_V3_HISTORICAL_NATIVE_BANK_V1":
        raise SystemExit("PF_DEI_V3_BANK_AUDIT_BAD_BANK_CONTRACT")
    if bank_summary.get("placement_manifest_sha256") != sha256_file(args.placement_manifest):
        raise SystemExit("PF_DEI_V3_BANK_AUDIT_PLACEMENT_HASH_FAIL")

    expected_rows = list(placement["rows"])
    expected_paths = {relative_shard(row).as_posix() for row in expected_rows}
    if len(expected_paths) != len(expected_rows):
        raise SystemExit("PF_DEI_V3_BANK_AUDIT_DUPLICATE_EXPECTED_SHARD")
    actual_paths = {
        path.relative_to(args.bank_root).as_posix()
        for path in args.bank_root.rglob("*.bin")
    }
    if actual_paths != expected_paths:
        missing = sorted(expected_paths - actual_paths)[:10]
        extra = sorted(actual_paths - expected_paths)[:10]
        raise SystemExit(f"PF_DEI_V3_BANK_AUDIT_FILE_SET_FAIL missing={missing} extra={extra}")
    temporary = sorted(path for path in args.bank_root.rglob("*.tmp.*") if path.is_file())
    if temporary:
        raise SystemExit(f"PF_DEI_V3_BANK_AUDIT_STALE_TEMP_FAIL:{temporary[:5]}")

    rows = []
    for index, row in enumerate(expected_rows, start=1):
        relative = relative_shard(row)
        path = args.bank_root / relative
        streams = read_multistream(path)
        key = f"{row['house']}_{row['split']}"
        expected_lengths = [int(value) for value in bank_summary["trajectory_lengths"][key]]
        actual_lengths = [int(values.size) for values in streams]
        if actual_lengths != expected_lengths:
            raise SystemExit(f"PF_DEI_V3_BANK_AUDIT_LENGTH_FAIL:{relative}")
        rows.append({
            "house": row["house"], "split": row["split"],
            "member_id": int(row["member_id"]), "carrier_id": row["carrier_id"],
            "relative_path": relative.as_posix(), "size_bytes": path.stat().st_size,
            "stream_count": len(streams), "sample_count": sum(actual_lengths),
            "sha256": sha256_file(path),
        })
        if index % 500 == 0 or index == len(expected_rows):
            print(f"PF_DEI_V3_BANK_AUDIT_PROGRESS={index}/{len(expected_rows)}", flush=True)

    manifest_path = args.bank_root / "bank_shard_manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as sink:
        writer = csv.DictWriter(sink, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    summary = {
        "contract": "PF_DEI_V3_NATIVE_BANK_AUDIT_V1",
        "verdict": "PF_DEI_V3_NATIVE_BANK_AUDIT_PASS",
        "shard_count": len(rows),
        "total_size_bytes": sum(int(row["size_bytes"]) for row in rows),
        "total_stream_samples": sum(int(row["sample_count"]) for row in rows),
        "placement_manifest_sha256": sha256_file(args.placement_manifest),
        "bank_summary_sha256": sha256_file(bank_summary_path),
        "bank_shard_manifest_sha256": sha256_file(manifest_path),
        "native_multistream_binary_sha256": bank_summary["native_multistream_binary_sha256"],
    }
    summary_path = args.bank_root / "bank_audit_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(summary["verdict"] + " " + json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

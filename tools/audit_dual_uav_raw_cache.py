#!/usr/bin/env python3
"""Read-only audit for the frozen R3B raw plume caches.

The script never generates, deletes, or rewrites a plume frame.  It verifies
the exact 4-source x 3-wind inventory, required frame range, historical sample
hashes, and writes a complete hash list for frames 0..419.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path


SOURCES = ("S_truth", "S_k01", "S_k10", "S_k22")
WINDS = ("W_fast", "W_slow", "W_altfast")
FRAME_MIN = 0
FRAME_MAX = 419


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_historical_samples(path: Path) -> dict[tuple[str, str, int], str]:
    expected: dict[tuple[str, str, int], str] = {}
    with path.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            for frame, digest in json.loads(row["sample_hashes"]).items():
                expected[(row["source_id"], row["wind_id"], int(frame))] = digest
    return expected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--historical-audit", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-sha256", type=Path, required=True)
    args = parser.parse_args()

    raw_root = args.dataset_root / "raw_cache"
    expected_pairs = {f"{source}__{wind}" for source in SOURCES for wind in WINDS}
    actual_pairs = {path.name for path in raw_root.iterdir() if path.is_dir()}
    historical = load_historical_samples(args.historical_audit)
    pair_rows = []
    complete_hash_rows = []
    sample_mismatches = []

    for pair in sorted(expected_pairs):
        source, wind = pair.split("__", 1)
        folder = raw_root / pair
        found = {}
        if folder.is_dir():
            for path in folder.iterdir():
                match = re.fullmatch(r"iteration_(\d+)", path.name)
                if match and path.is_file():
                    found[int(match.group(1))] = path
        missing = [frame for frame in range(FRAME_MIN, FRAME_MAX + 1) if frame not in found]
        empty = [frame for frame, path in found.items() if FRAME_MIN <= frame <= FRAME_MAX and path.stat().st_size == 0]
        for frame in range(FRAME_MIN, FRAME_MAX + 1):
            if frame not in found:
                continue
            digest = sha256_file(found[frame])
            complete_hash_rows.append((digest, f"raw_cache/{pair}/iteration_{frame}"))
            prior = historical.get((source, wind, frame))
            if prior is not None and prior != digest:
                sample_mismatches.append({
                    "source": source,
                    "wind": wind,
                    "frame": frame,
                    "historical": prior,
                    "current": digest,
                })
        pair_rows.append({
            "source": source,
            "wind": wind,
            "directory": pair,
            "total_frame_files": len(found),
            "min_frame": min(found) if found else None,
            "max_frame": max(found) if found else None,
            "required_missing": missing,
            "required_empty": empty,
            "required_status": "PASS" if not missing and not empty else "FAIL",
        })

    manifest_path = args.dataset_root / "R3B_MANIFEST.json"
    contract_path = args.dataset_root / "R3B_CONTRACT_HASHES.csv"
    overall = (
        actual_pairs == expected_pairs
        and all(row["required_status"] == "PASS" for row in pair_rows)
        and not sample_mismatches
        and manifest_path.is_file()
        and contract_path.is_file()
    )
    result = {
        "schema": "DUAL_UAV_TWO_POINT_RAW_CACHE_AUDIT_V1",
        "mode": "READ_ONLY_REUSE_NO_NEW_GADEN",
        "dataset_root": str(args.dataset_root),
        "expected_sources": list(SOURCES),
        "expected_winds": list(WINDS),
        "expected_pairs": 12,
        "actual_pair_directories": sorted(actual_pairs),
        "missing_pair_directories": sorted(expected_pairs - actual_pairs),
        "unexpected_pair_directories": sorted(actual_pairs - expected_pairs),
        "required_frame_range": [FRAME_MIN, FRAME_MAX],
        "pair_audits": pair_rows,
        "historical_sample_hash_mismatches": sample_mismatches,
        "manifest_sha256": sha256_file(manifest_path) if manifest_path.is_file() else None,
        "contract_hashes_sha256": sha256_file(contract_path) if contract_path.is_file() else None,
        "physical_realizations": 1,
        "stochastic_robustness_claim": False,
        "status": "PASS" if overall else "FAIL",
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    args.out_sha256.write_text(
        "\n".join(f"{digest}  {relative}" for digest, relative in complete_hash_rows) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": result["status"], "pairs": len(pair_rows), "hashes": len(complete_hash_rows)}))


if __name__ == "__main__":
    main()

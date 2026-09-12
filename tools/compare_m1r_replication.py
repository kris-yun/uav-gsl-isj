#!/usr/bin/env python3
"""Compare the single V4.1 instrumented replication with preserved M1R runs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

HOUSES = ("H01", "H02", "H03")


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def digest_records(records: list[dict[str, str]], ignored: set[str]) -> str:
    normalized = [{key: value for key, value in row.items() if key not in ignored} for row in records]
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def sequence_comparison(old: list[dict[str, str]], new: list[dict[str, str]], ignored: set[str]) -> dict:
    old_norm = [{k: v for k, v in row.items() if k not in ignored} for row in old]
    new_norm = [{k: v for k, v in row.items() if k not in ignored} for row in new]
    first_mismatch = next(
        (index for index, pair in enumerate(zip(old_norm, new_norm), 1) if pair[0] != pair[1]),
        None,
    )
    if first_mismatch is None and len(old_norm) != len(new_norm):
        first_mismatch = min(len(old_norm), len(new_norm)) + 1
    return {
        "historical_rows": len(old_norm),
        "replication_rows": len(new_norm),
        "normalized_sha256_historical": digest_records(old, ignored),
        "normalized_sha256_replication": digest_records(new, ignored),
        "exact_sequence_equal": old_norm == new_norm,
        "first_mismatch_row_1_based": first_mismatch,
    }


def compare_house(historical_root: Path, replication_root: Path, house: str) -> dict:
    old_dir = historical_root / f"{house}_seed12_M1R"
    new_dir = replication_root / f"{house}_seed12_M1R"
    old_manifest = json.loads((old_dir / "formal_runtime_manifest.json").read_text(encoding="utf-8"))
    new_manifest = json.loads((new_dir / "formal_runtime_manifest.json").read_text(encoding="utf-8"))
    old_status = json.loads((old_dir / "run_status.json").read_text(encoding="utf-8"))
    new_status = json.loads((new_dir / "run_status.json").read_text(encoding="utf-8"))
    old_source = rows(old_dir / "source_estimate_trace.csv")
    new_source = rows(new_dir / "source_estimate_trace.csv")
    identities = {
        key: {"historical": old_manifest.get(key), "replication": new_manifest.get(key),
              "equal": old_manifest.get(key) == new_manifest.get(key)}
        for key in ("seed", "vgr_bridge_contract_sha256", "realization", "config_id")
    }
    identities["algorithm_sha256"] = {
        "historical": old_manifest.get("algorithm_sha256"),
        "replication": new_manifest.get("algorithm_sha256"),
        "equal": old_manifest.get("algorithm_sha256") == new_manifest.get("algorithm_sha256"),
    }
    result = {
        "house": house,
        "identities": identities,
        "observation_sequence": sequence_comparison(
            rows(old_dir / "sensor_trace.csv"), rows(new_dir / "sensor_trace.csv"), set()
        ),
        "robot_pose_sequence": sequence_comparison(
            rows(old_dir / "sim_pose_trace.csv"), rows(new_dir / "sim_pose_trace.csv"), set()
        ),
        "navigation_event_sequence_without_clock_or_uuid": sequence_comparison(
            rows(old_dir / "navigation_trace.csv"), rows(new_dir / "navigation_trace.csv"),
            {"run_uuid", "sim_time"},
        ),
        "source_update_sequence_without_clock_or_uuid": sequence_comparison(
            old_source, new_source, {"run_uuid", "sim_time"},
        ),
        "update_timestamps_equal": [row["sim_time"] for row in old_source] ==
                                   [row["sim_time"] for row in new_source],
        "final_status": {
            "historical": old_status,
            "replication": new_status,
            "status_equal": old_status.get("status") == new_status.get("status"),
        },
        "final_source_record_without_clock_or_uuid_equal": (
            {k: v for k, v in old_source[-1].items() if k not in {"run_uuid", "sim_time"}} ==
            {k: v for k, v in new_source[-1].items() if k not in {"run_uuid", "sim_time"}}
        ),
    }
    exact_fields = (
        result["observation_sequence"]["exact_sequence_equal"],
        result["robot_pose_sequence"]["exact_sequence_equal"],
        result["navigation_event_sequence_without_clock_or_uuid"]["exact_sequence_equal"],
        result["source_update_sequence_without_clock_or_uuid"]["exact_sequence_equal"],
        result["update_timestamps_equal"],
        identities["algorithm_sha256"]["equal"],
    )
    result["historical_equivalence_proven"] = all(exact_fields)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-root", type=Path, required=True)
    parser.add_argument("--replication-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    comparisons = {house: compare_house(args.historical_root, args.replication_root, house) for house in HOUSES}
    report = {
        "contract": "M1R_V41_HISTORICAL_REPLICATION_COMPARISON",
        "evidence_label": "NEW_INSTRUMENTED_DEVELOPMENT_REPLICATION",
        "historical_equivalence_proven": all(item["historical_equivalence_proven"] for item in comparisons.values()),
        "interpretation_limit": "replication evidence describes the frozen implementation in this new run; it is not historical exact replay",
        "houses": comparisons,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

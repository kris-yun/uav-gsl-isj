#!/usr/bin/env python3
"""Create a read-only descriptive table for the frozen V3-ORR 60-arm run."""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path


def read_audit(path: Path) -> Counter:
    counts: Counter = Counter()
    if not path.exists():
        return counts
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if "released" in row:
                decision = "RELEASE" if str(row["released"]).strip() == "1" else "ABSTAIN"
            else:
                decision = (row.get("decision") or row.get("action") or "UNKNOWN").strip().upper()
            counts[decision] += 1
    return counts


def main() -> None:
    root = Path(sys.argv[1]).resolve()
    out_dir = Path(sys.argv[2]).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for house in ("House01", "House02", "House03"):
        for seed in range(10):
            pair = root / house / f"seed{seed}"
            off = json.loads((pair / "off" / "case_result.json").read_text(encoding="utf-8"))
            on = json.loads((pair / "on" / "case_result.json").read_text(encoding="utf-8"))
            audits = list((pair / "on" / "runtime").rglob("v3_orr_update_audit.csv"))
            audit_counts = read_audit(audits[0]) if len(audits) == 1 else Counter()
            off_error = float(off["primary_error_m"])
            on_error = float(on["primary_error_m"])
            rows.append(
                {
                    "house": house,
                    "seed": seed,
                    "off_error_m": off_error,
                    "on_error_m": on_error,
                    "relative_improvement": (off_error - on_error) / max(off_error, 1e-12),
                    "improved": on_error < off_error,
                    "off_variance_m2": off.get("variance_m2"),
                    "on_variance_m2": on.get("variance_m2"),
                    "off_false_confident_collapse": bool(off.get("false_confident_collapse", False)),
                    "on_false_confident_collapse": bool(on.get("false_confident_collapse", False)),
                    "first_release_s": on.get("first_release_s"),
                    "release_updates": audit_counts.get("RELEASE", 0),
                    "abstain_updates": audit_counts.get("ABSTAIN", 0),
                    "audit_rows": sum(audit_counts.values()),
                    "audit_file_count": len(audits),
                    "off_binary_sha256": off.get("binary_sha256"),
                    "on_binary_sha256": on.get("binary_sha256"),
                }
            )

    fields = list(rows[0])
    with (out_dir / "PAIR_RESULTS_30.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "contract": "V3_ORR_FULL60_DESCRIPTIVE_AUDIT_V1",
        "pairs": len(rows),
        "arms": 2 * len(rows),
        "improved_pairs": sum(bool(row["improved"]) for row in rows),
        "off_false_confident_collapse_count": sum(bool(row["off_false_confident_collapse"]) for row in rows),
        "on_false_confident_collapse_count": sum(bool(row["on_false_confident_collapse"]) for row in rows),
        "pairs_with_any_false_confident_collapse": sum(
            bool(row["off_false_confident_collapse"] or row["on_false_confident_collapse"])
            for row in rows
        ),
        "release_updates": sum(int(row["release_updates"]) for row in rows),
        "abstain_updates": sum(int(row["abstain_updates"]) for row in rows),
        "audit_rows": sum(int(row["audit_rows"]) for row in rows),
        "audit_files": sum(int(row["audit_file_count"]) for row in rows),
        "note": "Descriptive only; the preregistered verdict remains MULTISEED_VERDICT.json.",
    }
    (out_dir / "DESCRIPTIVE_AUDIT.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
